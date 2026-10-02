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
            print(f"[Thread-{flow_type}] Chuyển hướng đến trang gợi ý kết bạn...")
            driver.get("https://www.facebook.com/friends/suggestions")
            
            try:
                # Wait thông minh tối đa 60s cho đến khi xuất hiện thông báo hết gợi ý hoặc có nút thêm bạn bè
                WebDriverWait(driver, 60).until(
                    lambda d: "Lời mời và gợi ý kết bạn sẽ hiển thị tại đây." in d.page_source or 
                              "Thêm bạn bè" in d.page_source or 
                              "Add Friend" in d.page_source
                )
            except:
                pass # Hết thời gian chờ 60s
            
            time.sleep(1) # Chờ thêm 1s để DOM ổn định hẳn

            if "Lời mời và gợi ý kết bạn sẽ hiển thị tại đây." in driver.page_source:
                print(f"[Thread-{flow_type}] Không có gợi ý lời mời nào.")
                time.sleep(10)
                print(f"[Thread-{flow_type}] Chuyển hướng đến https://www.facebook.com/lichsungoaitruyen/")
                driver.get("https://www.facebook.com/lichsungoaitruyen/")
                time.sleep(5)
                
                print(f"[Thread-{flow_type}] Bắt đầu lướt tìm khối cảm xúc...")
                found = False
                for _ in range(50): # Cuộn tối đa 50 lần
                    try:
                        # Tìm element có aria-label="Xem ai đã bày tỏ cảm xúc về tin này"
                        el = driver.find_element(By.XPATH, "//*[@aria-label='Xem ai đã bày tỏ cảm xúc về tin này']")
                        # Cuộn element vào giữa màn hình
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", el)
                        time.sleep(2)
                        
                        try:
                            el.click()
                        except:
                            driver.execute_script("arguments[0].click();", el)
                            
                        print(f"[Thread-{flow_type}] Đã click vào khối cảm xúc thành công.")
                        found = True
                        
                        print(f"[Thread-{flow_type}] Đợi modal danh sách người thả cảm xúc...")
                        try:
                            WebDriverWait(driver, 120).until(
                                lambda d: len(d.find_elements(By.XPATH, "//div[@aria-label='Thêm bạn bè']")) > 0
                            )
                            time.sleep(3) # Đợi danh sách load hoàn toàn
                            add_btns = driver.find_elements(By.XPATH, "//div[@aria-modal='true']//div[@aria-label='Thêm bạn bè'] | //div[@aria-label='Thêm bạn bè']")
                            print(f"[Thread-{flow_type}] Tìm thấy {len(add_btns)} nút Thêm bạn bè trong danh sách.")
                            
                            if add_btns:
                                # HƯỚNG DẪN: Nếu muốn click số lượng nhiều (VD: 5 người), 
                                # bạn có thể dùng vòng lặp như sau thay vì chỉ lấy add_btns[0]:
                                # for btn in add_btns[:5]: 
                                btn = add_btns[0]
                                try:
                                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                                    time.sleep(1)
                                    driver.execute_script("arguments[0].click();", btn)
                                    print(f"[Thread-{flow_type}] Đã gửi 1 lời mời kết bạn duy nhất.")
                                    time.sleep(1.5)
                                except Exception as e:
                                    print(f"[Thread-{flow_type}] Lỗi khi click nút Thêm bạn bè: {e}")
                        except Exception as e:
                            print(f"[Thread-{flow_type}] Không tải được modal danh sách sau 120s.")
                            
                        break
                    except Exception:
                        # Cuộn xuống từ từ
                        driver.execute_script("window.scrollBy(0, 400);")
                        time.sleep(1.5)
                        
                if not found:
                    print(f"[Thread-{flow_type}] Không tìm thấy khối cảm xúc trên trang.")
            else:
                print(f"[Thread-{flow_type}] Đã tải trang gợi ý kết bạn.")
                try:
                    sugg_btns = driver.find_elements(By.XPATH, "//div[@aria-label='Thêm bạn bè']")
                    if sugg_btns:
                        print(f"[Thread-{flow_type}] Tìm thấy {len(sugg_btns)} nút Thêm bạn bè ở trang gợi ý.")
                        # HƯỚNG DẪN: Nếu muốn click số lượng nhiều (VD: 5 người), 
                        # bạn có thể dùng vòng lặp như sau thay vì chỉ lấy sugg_btns[0]:
                        # for btn in sugg_btns[:5]: 
                        btn = sugg_btns[0]
                        try:
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                            time.sleep(1)
                            driver.execute_script("arguments[0].click();", btn)
                            print(f"[Thread-{flow_type}] Đã gửi 1 lời mời kết bạn từ trang gợi ý.")
                        except Exception as e:
                            print(f"[Thread-{flow_type}] Lỗi khi click Thêm bạn bè: {e}")
                except Exception as e:
                    pass
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
