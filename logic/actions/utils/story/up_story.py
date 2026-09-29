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
    # Cửa sổ thứ index sẽ nằm cạnh nhau
    return (index * WIN_WIDTH, 0, WIN_WIDTH, WIN_HEIGHT)

def get_profile_path(uid):
    profile_dir = getattr(config, "PROFILE_DIR", "profiles")
    if not os.path.isabs(profile_dir):
        profile_dir = os.path.join(os.getcwd(), profile_dir)
    return os.path.join(profile_dir, uid)

def run_account_flow(cookie_line, window_index):
    flow_type = str(window_index)
    parts = cookie_line.split("|")
    uid = parts[0]
    password = parts[1] if len(parts) > 1 else ""
    cookie_str = "|".join(parts[2:]) if len(parts) > 2 else ""
    
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
        
    proxy_config = None
    proxy_str = None
    kiot_keys = []
    # --- Test cứng Proxy theo yêu cầu ---
    proxy_str = "miennam.vnproxy.com:41773:8K35Fz:4jIe50"
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
                login_els = driver.find_elements(By.NAME, "login") or driver.find_elements(By.ID, "loginbutton") or driver.find_elements(By.XPATH, "//*[text()='Đăng nhập' or text()='Log In']")
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
                    cookie_dict["path"] = "/"
                    cookie_dict["expiry"] = expiry_time
                    driver.add_cookie(cookie_dict)
                except:
                    pass
            driver.refresh()
            time.sleep(8)
            
        def verify_uid(dr, t_uid):
            curr_url = dr.current_url or ""
            if t_uid in curr_url or f"profile.php?id={t_uid}" in curr_url or "/me" in curr_url: return True
            cookies = dr.get_cookies()
            if any(c['name'] == 'c_user' and str(c['value']) == str(t_uid) for c in cookies): return True
            ps = dr.page_source
            if f'\"userID\":\"{t_uid}\"' in ps or f'\"ACCOUNT_ID\":\"{t_uid}\"' in ps: return True
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
                login_with_credentials(driver, uid, password)
                time.sleep(5)
                login_verified = verify_uid(driver, uid)
        
        if login_verified:
            print(f"[Thread-{flow_type}] Xác minh login thành công.")
            try:
                print(f"[Thread-{flow_type}] Đang tìm nút Tạo tin...")
                driver.get("https://www.facebook.com/")
                
                from selenium.webdriver.support.ui import WebDriverWait
                wait_60 = WebDriverWait(driver, 60)
                
                # Chờ nút Tạo tin hiện rõ trên màn hình
                create_story_btn = wait_60.until(EC.visibility_of_element_located((By.XPATH, "//a[contains(@href, '/stories/create')] | //a[@aria-label='Tạo tin' or @aria-label='Create Story']")))
                time.sleep(2) # Cho React nạp xong event
                driver.execute_script("arguments[0].click();", create_story_btn)
                print(f"[Thread-{flow_type}] Đã click vào nút Tạo tin thành công!")
                
                print(f"[Thread-{flow_type}] Chờ tải trang Tạo tin (tối đa 180s)...")
                wait_180 = WebDriverWait(driver, 180)
                wait_180.until(EC.url_contains("/stories/create"))
                
                print(f"[Thread-{flow_type}] Chờ giao diện load xong (tìm thẻ h1 'Tin của bạn')...")
                wait_180.until(EC.presence_of_element_located((By.XPATH, "//h1[text()='Tin của bạn' or text()='Your Story']")))
                
                print(f"[Thread-{flow_type}] Đang tìm nút Loại tin (Ảnh/Chữ)...")
                xpath_photo_story = "//div[@aria-label='Tạo tin có ảnh hoặc video' or contains(@aria-label, 'Photo Story') or contains(@aria-label, 'photo or video')]"
                story_type_btn = wait_180.until(EC.presence_of_element_located((By.XPATH, xpath_photo_story)))
                
                img_path = r"C:\Users\ADMIN\Downloads\814039378_1797285318353320_6152937150203234085_n.jpg"
                
                print(f"[Thread-{flow_type}] Chuẩn bị mở hộp thoại chọn file của hệ điều hành...")
                
                def handle_os_dialog(path):
                    import time
                    try:
                        import pyautogui
                        import pyperclip
                    except ImportError:
                        print(f"[Thread-{flow_type}] THIẾU THƯ VIỆN: Chạy 'pip install pyautogui pyperclip'")
                        return
                    time.sleep(2) # Đợi hộp thoại Open hiện lên
                    
                    # Dùng clipboard + Ctrl V để tránh bộ gõ Unikey làm hỏng đường dẫn (VD: D -> Đ)
                    pyperclip.copy(path)
                    pyautogui.hotkey('ctrl', 'v')
                    time.sleep(1)
                    pyautogui.press('enter')
                    
                import threading
                threading.Thread(target=handle_os_dialog, args=(img_path,), daemon=True).start()
                
                # Bấm vào nút sẽ làm Selenium bị block cho tới khi hộp thoại Open bị đóng
                try:
                    story_type_btn.click()
                except:
                    driver.execute_script("arguments[0].click();", story_type_btn)
                    
                print(f"[Thread-{flow_type}] Đã xử lý xong popup chọn file của OS!")
                
                # Chờ hiển thị UI Editor và nút Thêm nhạc
                print(f"[Thread-{flow_type}] Chờ giao diện chỉnh sửa và tìm nút 'Thêm nhạc'...")
                add_music_btn = wait_180.until(EC.presence_of_element_located((By.XPATH, "//span[contains(text(), 'Thêm nhạc') or contains(text(), 'Add Music')]")))
                time.sleep(2) # Đợi giao diện ổn định sau khi up ảnh
                
                try:
                    add_music_btn.click()
                    print(f"[Thread-{flow_type}] Đã ấn nút 'Thêm nhạc' (Standard)!")
                except:
                    driver.execute_script("arguments[0].click();", add_music_btn)
                    print(f"[Thread-{flow_type}] Đã ấn nút 'Thêm nhạc' (JS Click)!")
                    
                # Tìm popup search nhạc
                print(f"[Thread-{flow_type}] Chờ popup tìm nhạc xuất hiện...")
                search_music_input = wait_180.until(EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Tìm kiếm nhạc' or @placeholder='Search music' or @aria-label='Tìm kiếm nhạc']")))
                print(f"[Thread-{flow_type}] Popup Thêm nhạc đã sẵn sàng!")
                
                # Chờ danh sách bài hát load và chọn random
                print(f"[Thread-{flow_type}] Đang chờ danh sách bài hát load...")
                time.sleep(3) # Chờ API trả về kết quả nhạc
                
                song_rows_xpath = "//div[@data-visualcompletion='ignore-dynamic']/div[@role='button']"
                song_rows = driver.find_elements(By.XPATH, song_rows_xpath)
                
                if song_rows:
                    selected_song = random.choice(song_rows)
                    print(f"[Thread-{flow_type}] Đã tìm thấy {len(song_rows)} bài hát, đang click random...")
                    try:
                        selected_song.click()
                    except:
                        driver.execute_script("arguments[0].click();", selected_song)
                    print(f"[Thread-{flow_type}] Đã chọn nhạc thành công!")
                    
                    # Chờ và ấn nút Xong (Xác nhận nhạc)
                    print(f"[Thread-{flow_type}] Chờ nút 'Xong' để xác nhận nhạc...")
                    try:
                        done_btn = wait_60.until(EC.presence_of_element_located((By.XPATH, "//div[@aria-label='Xong' or @aria-label='Done']")))
                        time.sleep(1)
                        try:
                            done_btn.click()
                        except:
                            driver.execute_script("arguments[0].click();", done_btn)
                        print(f"[Thread-{flow_type}] Đã ấn nút Xong xác nhận nhạc!")
                    except Exception as ex:
                        print(f"[Thread-{flow_type}] Không tìm thấy nút Xong, có thể giao diện không yêu cầu hoặc lỗi: {ex}")
                        
                    # Chờ và ấn nút Chia sẻ lên tin
                    print(f"[Thread-{flow_type}] Chờ nút 'Chia sẻ lên tin'...")
                    try:
                        share_btn = wait_60.until(EC.presence_of_element_located((By.XPATH, "//div[@aria-label='Chia sẻ lên tin' or @aria-label='Share to Story'] | //span[text()='Chia sẻ lên tin' or text()='Share to Story']/ancestor::div[@role='button']")))
                        time.sleep(1)
                        try:
                            share_btn.click()
                        except:
                            driver.execute_script("arguments[0].click();", share_btn)
                        print(f"[Thread-{flow_type}] Đã ấn nút CHIA SẺ LÊN TIN thành công!")
                        
                        print(f"[Thread-{flow_type}] Đang chờ chuyển hướng về trang chủ để xác nhận đăng tin (tối đa 60s)...")
                        try:
                            wait_60.until(lambda d: "/stories/create" not in d.current_url)
                            print(f"[Thread-{flow_type}] [THÀNH CÔNG] Đăng tin hoàn tất, URL đã chuyển hướng về trang chủ!")
                        except:
                            print(f"[Thread-{flow_type}] [LỖI] Đã quá 60s nhưng vẫn kẹt ở trang Tạo tin. Đăng tin thất bại!")
                            
                    except Exception as ex:
                        print(f"[Thread-{flow_type}] Lỗi khi ấn Chia sẻ lên tin: {ex}")

                else:
                    print(f"[Thread-{flow_type}] Không tìm thấy bài hát nào trong danh sách gợi ý!")
            except Exception as e:
                print(f"[Thread-{flow_type}] Lỗi trong quá trình tạo tin: {e}")
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
        "61579448764779|Viqutehu@2567|fr=1TyxyKtMelNYYBsQb.AWeCyjzsQsKm9Vg45bvWQNuwh9rVuugpbVH7Pdi5AVz2eS7sJbs.Bpuxk2..AAA.0.0.BqnlVi.AWf614IxIjbw7464cfGSOVD4bEs; ps_n=1; dpr=2.25; datr=KRm7aVlnR-VpTfv-lVmIDHWo; xs=33:P1qU3cl6ZvGgdA:2:1773869372:-1:-1; ps_l=1; wd=500x569; c_user=61579448764779; sb=5x6Yaq9Isq0O9Lx998sgyolW|EAAAAUaZA8jlABQ0yJ2HwJXDlyLUhYDR1qlHPZAGZB4ZCqMV0AUoStDim0b6zZAN777fPkasZAijuKzzs9Huzwxlw9wg5couGqGWZCegZBh2eZC2x9FrkhRLxFusfTiWuuKmUQNV4KVGGurzZB5cbCmSCWiFttH5KT4xZCO0ZCAaVQbkJb3MzexkbA8r6iBSNNOSvf87ZA3ZAl4CwZDZD"
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
