import time
import os
import random
import base64
import logging
import threading

# Ẩn các log lỗi ồn ào của seleniumwire (mitmproxy)
logging.getLogger('seleniumwire').setLevel(logging.CRITICAL)

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from utils.driver_utils import create_driver
from config import config

from utils.account_registry import (
    get_assigned_ua, parse_proxy_str
)

# Cấu hình cửa sổ
WIN_WIDTH = 500
WIN_HEIGHT = 700

def get_window_pos(index):
    return (index * WIN_WIDTH, 0, WIN_WIDTH, WIN_HEIGHT)

def get_profile_path(uid):
    profile_dir = getattr(config, "PROFILE_DIR", "profiles")
    if not os.path.isabs(profile_dir):
        profile_dir = os.path.join(os.getcwd(), profile_dir)
    return os.path.join(profile_dir, uid)

def run_account_flow(cookie_line, window_index):
    flow_type = str(window_index)
    parts = cookie_line.split("|")
    uid        = parts[0]
    password   = parts[1].strip() if len(parts) > 1 else ""
    fa2_secret = ""
    cookie_str = ""
    for p in parts[2:]:
        p = p.strip()
        if "c_user=" in p or "sb=" in p or "datr=" in p or ";" in p:
            cookie_str = p
        elif p.isalnum() and len(p) >= 10:
            fa2_secret = p

    print(f"[Thread-{flow_type}] Bắt đầu tài khoản UID: {uid}")

    user_agent = None
    actual_cookies = []
    for c in cookie_str.split(";"):
        c = c.strip()
        if not c: continue
        if "=" in c:
            k, v = c.split("=", 1)
            k = k.strip()
            v = v.strip()
            if k.lower() == "useragent":
                try:
                    user_agent = base64.b64decode(v).decode('utf-8')
                except:
                    user_agent = v
            else:
                actual_cookies.append({"name": k, "value": v})

    if not user_agent:
        import utils.account_registry as ar
        mapping_ua = ar.load_ua_mapping()
        user_agent = get_assigned_ua(uid, mapping_ua)

    proxy_str = "mienbac.vnproxy.com:61369:T2NgwN:nAyfMv"
    proxy_config = parse_proxy_str(proxy_str)
    print(f"[Thread-{flow_type}] Sử dụng Proxy chỉ định: {proxy_str}")

    profile_path = get_profile_path(uid)
    win_pos = get_window_pos(window_index)

    try:
        driver, wait, _ = create_driver(
            user_data_dir=profile_path,
            proxy_config=proxy_config,
            window_pos=win_pos,
            user_agent=user_agent
        )

        driver.get("https://www.facebook.com/")
        print(f"[Thread-{flow_type}] Kiểm tra login...")
        time.sleep(5)

        current_cookies = driver.get_cookies()
        has_c_user = any(c['name'] == 'c_user' and uid in str(c['value']) for c in current_cookies)

        is_logged_in = False
        if has_c_user:
            try:
                login_els = (driver.find_elements(By.NAME, "login")
                             or driver.find_elements(By.ID, "loginbutton")
                             or driver.find_elements(By.XPATH, "//*[text()='Đăng nhập' or text()='Log In']"))
                if not login_els:
                    is_logged_in = True
            except: pass

        if is_logged_in:
            print(f"[Thread-{flow_type}] Đã lưu phiên đăng nhập!")
        else:
            print(f"[Thread-{flow_type}] Nạp cookie mới...")
            expiry_time = int(time.time()) + (365 * 24 * 3600)
            for cookie_dict in actual_cookies:
                try:
                    cookie_dict["domain"] = ".facebook.com"
                    cookie_dict["path"]   = "/"
                    cookie_dict["expiry"] = expiry_time
                    driver.add_cookie(cookie_dict)
                except:
                    pass
            driver.refresh()
            time.sleep(8)

        def verify_uid(dr, t_uid):
            curr_url = dr.current_url or ""
            if t_uid in curr_url or f"profile.php?id={t_uid}" in curr_url or "/me" in curr_url:
                return True
            cookies = dr.get_cookies()
            if any(c['name'] == 'c_user' and str(c['value']) == str(t_uid) for c in cookies):
                return True
            ps = dr.page_source
            if f'"userID":"{t_uid}"' in ps or f'"ACCOUNT_ID":"{t_uid}"' in ps:
                return True
            return False

        login_verified = verify_uid(driver, uid)
        if not login_verified:
            driver.get("https://www.facebook.com/me")
            time.sleep(5)
            login_verified = verify_uid(driver, uid)

        if not login_verified:
            print(f"[Thread-{flow_type}] Cookie lỗi, thử MK...")
            if password:
                from actions.utils.login import login_with_credentials

                # Chạy login trong thread riêng để không bị block khi gặp trang 2FA
                login_done = threading.Event()
                def _do_login():
                    res = login_with_credentials(driver, uid, password, fa2_secret=fa2_secret)
                    if res == "INVALID_REQUEST":
                        print(f"[{uid}] ❌ Lỗi 'Invalid request' 2FA.")
                    login_done.set()
                login_thread = threading.Thread(target=_do_login, daemon=True)
                login_thread.start()
                login_thread.join(35)

                login_verified = verify_uid(driver, uid)

        if login_verified:
            print(f"[Thread-{flow_type}] Xác minh login thành công.")
            
            print(f"[Thread-{flow_type}] Bắt đầu test up story trực tiếp...")
            try:
                print(f"[{uid}] Đang tìm nút Tạo tin...")
                driver.get("https://www.facebook.com/")
                
                wait_60 = WebDriverWait(driver, 60)
                
                # Chờ nút Tạo tin hiện rõ trên màn hình
                create_story_btn = wait_60.until(EC.visibility_of_element_located((By.XPATH, "//a[contains(@href, '/stories/create')] | //a[@aria-label='Tạo tin' or @aria-label='Create Story']")))
                time.sleep(2) # Cho React nạp xong event
                driver.execute_script("arguments[0].click();", create_story_btn)
                print(f"[{uid}] Đã click vào nút Tạo tin thành công!")
                
                print(f"[{uid}] Chờ tải trang Tạo tin (tối đa 180s)...")
                wait_180 = WebDriverWait(driver, 180)
                wait_180.until(EC.url_contains("/stories/create"))
                
                print(f"[{uid}] Chờ giao diện load xong (tìm thẻ h1 'Tin của bạn')...")
                wait_180.until(EC.presence_of_element_located((By.XPATH, "//h1[text()='Tin của bạn' or text()='Your Story']")))
                
                print(f"[{uid}] Đang tìm nút Loại tin (Ảnh/Chữ)...")
                xpath_photo_story = "//div[@aria-label='Tạo tin có ảnh hoặc video' or contains(@aria-label, 'Photo Story')] | //span[text()='Tạo tin có ảnh hoặc video' or text()='Create a Photo Story']/ancestor::div[@role='button'] | //span[text()='Tạo tin có ảnh hoặc video' or text()='Create a Photo Story']"
                story_type_btn = wait_180.until(EC.presence_of_element_located((By.XPATH, xpath_photo_story)))
                
                import os
                image_path = r"C:\Users\ADMIN\Documents\106689-673786365_medium.mp4"
                print(f"[{uid}] Dùng file ảnh/video cố định: {image_path}")
                
                print(f"[{uid}] Tìm thẻ input file để nhét file ngầm (tránh dùng OS Dialog)...")
                try:
                    # Tìm tất cả các thẻ input dạng file
                    file_inputs = wait_60.until(EC.presence_of_all_elements_located((By.XPATH, "//input[@type='file']")))
                    print(f"[{uid}] [DEBUG] Đã tìm thấy {len(file_inputs)} thẻ <input type='file'> trên trang.")
                    
                    if file_inputs:
                        success = False
                        # Đảo ngược danh sách file_inputs để lấy thẻ xuất hiện sau cùng (thường là thẻ thật)
                        file_inputs.reverse()
                        
                        for idx, inp in enumerate(file_inputs):
                            accept_attr = inp.get_attribute("accept") or "Không có"
                            
                            # Tìm đúng thẻ input dùng để up ảnh/video
                            if "image" in accept_attr or "video" in accept_attr or accept_attr == "Không có":
                                print(f"[{uid}] [DEBUG] => Đã tìm thấy thẻ input (từ dưới lên). Tiến hành nạp file...")
                                try:
                                    driver.execute_script("arguments[0].style.display = 'block'; arguments[0].style.opacity = 1;", inp)
                                    
                                    # Selenium send_keys sẽ tự động nạp file
                                    inp.send_keys(image_path)
                                    print(f"[{uid}] [DEBUG] Đã nạp file thành công vào thẻ input!")
                                    
                                    # Bắn nhẹ event change phòng hờ
                                    driver.execute_script("arguments[0].dispatchEvent(new Event('change', { bubbles: true }));", inp)
                                    
                                    success = True
                                    break # Nhét 1 phát ăn luôn, xong thoát vòng lặp
                                except Exception as inner_e:
                                    print(f"[{uid}] [DEBUG] Lỗi khi nạp thẻ: {inner_e}")
                        
                        if success:
                            print(f"[{uid}] [DEBUG] Đã tiêm xong. Chờ 10s để giao diện React nạp và xử lý media...")
                            time.sleep(10)
                        else:
                            print(f"[{uid}] Không thể tiêm file vào bất kỳ thẻ nào.")
                            return
                    else:
                        print(f"[{uid}] Không tìm thấy thẻ input type='file' nào trên trang.")
                        return
                except Exception as e:
                    print(f"[{uid}] Lỗi khi up ảnh/video bằng thẻ input: {e}")
                    return
                
                # --- NẾU LÀ VIDEO THÌ THƯỜNG KHÔNG CẦN / KHÔNG THỂ THÊM NHẠC ---
                is_video = any(image_path.lower().endswith(ext) for ext in ['.mp4', '.mov', '.avi', '.webm', '.mkv'])
                
                if not is_video:
                    print(f"[{uid}] Chờ giao diện chỉnh sửa và tìm nút 'Thêm nhạc' (tối đa 15s)...")
                    try:
                        # Rút ngắn thời gian chờ nút thêm nhạc xuống 15s để không bị kẹt
                        wait_15 = WebDriverWait(driver, 15)
                        add_music_btn = wait_15.until(EC.presence_of_element_located((By.XPATH, "//span[contains(text(), 'Thêm nhạc') or contains(text(), 'Add Music')]")))
                        time.sleep(2)
                        
                        try:
                            add_music_btn.click()
                        except:
                            driver.execute_script("arguments[0].click();", add_music_btn)
                            
                        print(f"[{uid}] Chờ popup tìm nhạc xuất hiện...")
                        search_music_input = wait_15.until(EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Tìm kiếm nhạc' or @placeholder='Search music' or @aria-label='Tìm kiếm nhạc']")))
                        time.sleep(3)
                        
                        song_rows_xpath = "//div[@data-visualcompletion='ignore-dynamic']/div[@role='button']"
                        song_rows = driver.find_elements(By.XPATH, song_rows_xpath)
                        
                        if song_rows:
                            selected_song = random.choice(song_rows)
                            try:
                                selected_song.click()
                            except:
                                driver.execute_script("arguments[0].click();", selected_song)
                            print(f"[{uid}] Đã chọn nhạc thành công!")
                            
                            try:
                                done_btn = wait_15.until(EC.presence_of_element_located((By.XPATH, "//div[@aria-label='Xong' or @aria-label='Done']")))
                                time.sleep(1)
                                try:
                                    done_btn.click()
                                except:
                                    driver.execute_script("arguments[0].click();", done_btn)
                            except Exception:
                                pass
                    except Exception as ex:
                        print(f"[{uid}] Bỏ qua thêm nhạc do không tìm thấy nút hoặc lỗi: {ex}")
                else:
                    print(f"[{uid}] File là Video -> Bỏ qua bước Thêm Nhạc để tránh kẹt UI.")
                    
                print(f"[{uid}] Đang tìm nút 'Chia sẻ lên tin'...")
                try:
                    # Chờ tối đa 30s để nút Chia sẻ hiện ra và có thể click
                    wait_30 = WebDriverWait(driver, 30)
                    share_btn = wait_30.until(EC.element_to_be_clickable((By.XPATH, "//div[@aria-label='Chia sẻ lên tin' or @aria-label='Share to Story'] | //span[text()='Chia sẻ lên tin' or text()='Share to Story']/ancestor::div[@role='button']")))
                    time.sleep(2)
                    try:
                        share_btn.click()
                    except:
                        driver.execute_script("arguments[0].click();", share_btn)
                    print(f"[{uid}] Đã ấn Chia sẻ lên tin thành công!")
                except Exception as ex:
                    print(f"[{uid}] Không tìm thấy hoặc không thể click nút Chia sẻ: {ex}")
                        
            except Exception as e:
                print(f"[{uid}] Lỗi khi up story: {e}")
            
        else:
            print(f"[Thread-{flow_type}] Không thể login, dừng luồng này.")
            return

        print(f"[Thread-{flow_type}] Đã hoàn tất luồng tự động, giữ trình duyệt mở.")
        while True:
            _ = driver.window_handles
            time.sleep(5)

    except Exception as e:
        print(f"[Thread-{flow_type}] Lỗi hoặc trình duyệt đóng: {e}")


def main():
    # --- Dùng cứng Account được chỉ định ---
    lines = [
        "61585946429309|Viqutehu@2567|c_user=61585946429309;datr=qzVWaTiaH3_DbkUsq814ROln;fr=0fOP4AsFOBq6IOUWt.AWcH3rzeaeuibCNyc7O4i5Zuss0FTZviD_JfPLRNSgJhniJ3YkQ.BpVjWr..AAA.0.0.BpVjWw.AWftP_rrajsIjz9JfAZkca7vg6E;ps_l=1;ps_n=1;sb=qzVWaSUO6o3WRychbD4d9uoY;locale=en_US;xs=39%3A0BAB46fc1t_9fg%3A2%3A1767257524%3A-1%3A-1"
    ]

    print(f"[*] Chạy demo trực tiếp với dữ liệu cứng...")

    threads = []
    for i, acc in enumerate(lines):
        t = threading.Thread(target=run_account_flow, args=(acc, i))
        threads.append(t)
        t.start()
        time.sleep(5)

    try:
        for t in threads:
            t.join()
    except KeyboardInterrupt:
        print("\n[*] Dừng chương trình từ bàn phím.")

if __name__ == "__main__":
    main()
