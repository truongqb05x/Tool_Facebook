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
                print(f"[Thread-{flow_type}] Truy cập trực tiếp trang đổi Tên của Account Center...")
                driver.get(f"https://accountscenter.facebook.com/profiles/{uid}/name")
                
                from selenium.webdriver.support.ui import WebDriverWait
                from selenium.webdriver.support import expected_conditions as EC
                wait_60 = WebDriverWait(driver, 60)
                
                print(f"[Thread-{flow_type}] Đã vào trang đổi Tên, kiểm tra điều kiện 60 ngày...")
                
                # Kiểm tra thông báo giới hạn
                xpath_limit = "//*[contains(text(), 'chưa thể đổi tên') or contains(text(), 'You can\\'t change your name') or contains(text(), '60 ngày qua') or contains(text(), '60 days')]"
                try:
                    wait_3 = WebDriverWait(driver, 3)
                    wait_3.until(EC.presence_of_element_located((By.XPATH, xpath_limit)))
                    print(f"[Thread-{flow_type}] LỖI: Tài khoản KHÔNG ĐỦ ĐIỀU KIỆN (Bị kẹt 60 ngày)! Dừng luồng.")
                    return # Thoát hàm run_account_flow luôn vì không thể đổi tên
                except:
                    pass # Nếu không bắt được thông báo trong 3s thì an toàn, đi tiếp
                
                print(f"[Thread-{flow_type}] Chờ giao diện nhập Tên/Họ xuất hiện...")
                xpath_input_ten = "//input[following-sibling::label[text()='Tên' or text()='First name']]"
                xpath_input_ho = "//input[following-sibling::label[text()='Họ' or text()='Last name']]"
                
                input_ten = wait_60.until(EC.presence_of_element_located((By.XPATH, xpath_input_ten)))
                input_ho = wait_60.until(EC.presence_of_element_located((By.XPATH, xpath_input_ho)))
                time.sleep(2)
                
                # Đọc file dữ liệu
                import os, random
                current_dir = os.path.dirname(os.path.abspath(__file__))
                ho_path = os.path.join(current_dir, "resources", "ho.txt")
                ten_path = os.path.join(current_dir, "resources", "ten.txt")
                
                with open(ho_path, 'r', encoding='utf-8') as f:
                    list_ho = [x.strip() for x in f.readlines() if x.strip()]
                with open(ten_path, 'r', encoding='utf-8') as f:
                    list_ten = [x.strip() for x in f.readlines() if x.strip()]
                    
                # Xử lý random
                random_ho = random.choice(list_ho)
                random_ten = random.choice(list_ten)
                
                # 30% chỉ lấy 1 từ đầu cho Họ
                if random.random() < 0.3:
                    random_ho = random_ho.split()[0]
                
                # Hàm gõ như người thật
                def type_like_human(element, text):
                    from selenium.webdriver.common.keys import Keys
                    # Xoá trắng dữ liệu cũ (Ctrl+A -> Backspace)
                    element.send_keys(Keys.CONTROL + "a")
                    time.sleep(0.3)
                    element.send_keys(Keys.BACKSPACE)
                    time.sleep(0.5)
                    
                    # Gõ từng ký tự
                    for char in text:
                        element.send_keys(char)
                        time.sleep(random.uniform(0.05, 0.2))
                        
                print(f"[Thread-{flow_type}] Đang nhập Họ: {random_ho}")
                type_like_human(input_ho, random_ho)
                time.sleep(random.uniform(1, 2))
                
                print(f"[Thread-{flow_type}] Đang nhập Tên: {random_ten}")
                type_like_human(input_ten, random_ten)
                time.sleep(random.uniform(1, 2))
                
                print(f"[Thread-{flow_type}] Đã điền xong Họ và Tên mới!")
                
                # Chờ 3-5s như người thật
                delay_save = random.uniform(3.0, 5.0)
                print(f"[Thread-{flow_type}] Đợi {delay_save:.1f}s trước khi ấn Xem lại thay đổi...")
                time.sleep(delay_save)
                
                print(f"[Thread-{flow_type}] Đang tìm nút 'Xem lại thay đổi'...")
                xpath_review = "//*[contains(text(), 'Xem lại thay đổi') or contains(text(), 'Review change')]"
                review_els = wait_60.until(EC.presence_of_all_elements_located((By.XPATH, xpath_review)))
                
                # Thử click để vượt qua aria-hidden của React
                for rel in review_els:
                    try: rel.click(); break
                    except:
                        try: driver.execute_script("arguments[0].click();", rel); break
                        except:
                            try: driver.execute_script("arguments[0].parentElement.click();", rel); break
                            except: pass
                            
                print(f"[Thread-{flow_type}] Đã click xong nút Xem lại thay đổi!")
                
                print(f"[Thread-{flow_type}] Đợi popup 'Xem trước tên mới' và nút Xong xuất hiện...")
                xpath_done = "//*[text()='Xong' or text()='Done' or contains(text(), 'Done')]"
                done_els = wait_60.until(EC.presence_of_all_elements_located((By.XPATH, xpath_done)))
                time.sleep(2) # Chờ popup load xong
                
                print(f"[Thread-{flow_type}] Đã thấy nút Xong, tiến hành click chốt sổ...")
                for del_btn in done_els:
                    try: del_btn.click(); break
                    except:
                        try: driver.execute_script("arguments[0].click();", del_btn); break
                        except:
                            try: driver.execute_script("arguments[0].parentElement.click();", del_btn); break
                            except: pass
                            
                print(f"[Thread-{flow_type}] Đang chờ trang chuyển hướng để xác nhận hoàn thành (tối đa 60s)...")
                def is_done_redirected(drv):
                    curr = drv.current_url or ""
                    return f"/profiles/{uid}" in curr and "/name" not in curr
                    
                wait_60.until(is_done_redirected)
                print(f"[Thread-{flow_type}] Chúc mừng! Đã đổi Tên hoàn tất và quay về trang Account Center thành công!")
                
            except Exception as ex:
                print(f"[Thread-{flow_type}] Lỗi khi tương tác Account Center: {ex}")
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
