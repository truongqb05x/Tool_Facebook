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
                print(f"[Thread-{flow_type}] Truy cập vào tab Chi tiết cá nhân của profile...")
                driver.get(f"https://www.facebook.com/profile.php?id={uid}&sk=directory_personal_details")
                from selenium.webdriver.support.ui import WebDriverWait
                from selenium.webdriver.support import expected_conditions as EC
                wait_60 = WebDriverWait(driver, 60)
                
                print(f"[Thread-{flow_type}] Đang chờ trang tải...")
                time.sleep(5)
                
                def click_hard(drv, element):
                    from selenium.webdriver.common.action_chains import ActionChains
                    try: drv.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});", element)
                    except: pass
                    time.sleep(0.5)
                    try: element.click(); return True
                    except: pass
                    try: ActionChains(drv).move_to_element(element).click().perform(); return True
                    except: pass
                    try: drv.execute_script("arguments[0].click();", element)
                    except: pass
                    try:
                        drv.execute_script("""
                            var el = arguments[0];
                            for(var i=0; i<8; i++) {
                                if(el) { try { el.click(); } catch(e){} el = el.parentElement; }
                            }
                        """, element)
                        return True
                    except: pass
                    return False
                    
                
                # --- XỬ LÝ QUÊ QUÁN ---
                print(f"[Thread-{flow_type}] Kiểm tra xem tài khoản đã có thông tin Quê quán chưa...")
                # Khi đã có, FB hiện nút aria-label="Chỉnh sửa quê quán"
                xpath_ht_filled = "//*[@aria-label='Chỉnh sửa quê quán' or @aria-label='Edit hometown' or @aria-label='Edit Hometown']"
                if driver.find_elements(By.XPATH, xpath_ht_filled):
                    print(f"[Thread-{flow_type}] BỎ QUA: Tài khoản đã có sẵn thông tin Quê quán rồi!")
                    return
                else:
                    print(f"[Thread-{flow_type}] Đang tìm nút Thêm 'Quê quán'...")
                    xpath_ht = "//*[contains(text(), 'Quê quán') or contains(text(), 'quê quán') or contains(text(), 'Hometown') or contains(text(), 'hometown')]"
                    ht_els = wait_60.until(EC.presence_of_all_elements_located((By.XPATH, xpath_ht)))
                    
                    print(f"[Thread-{flow_type}] Đã thấy mục Quê quán, tiến hành click...")
                    for el in ht_els:
                        click_hard(driver, el)
                        time.sleep(0.5)
                        
                    print(f"[Thread-{flow_type}] Đang chờ ô nhập 'Quê quán' xuất hiện...")
                    xpath_input_ht = "//input[@aria-label='Quê quán' or contains(@aria-label, 'Quê quán') or contains(@aria-label, 'Hometown')]"
                    input_ht_els = wait_60.until(EC.presence_of_all_elements_located((By.XPATH, xpath_input_ht)))
                    
                    active_ht = None
                    for in_el in input_ht_els:
                        if click_hard(driver, in_el):
                            active_ht = in_el
                            break
                        time.sleep(0.5)
                        
                    if active_ht:
                        print(f"[Thread-{flow_type}] Đang nhập chữ vào ô tìm kiếm Quê quán...")
                        target_ht = "Hà Nội"
                        for char in target_ht:
                            try: active_ht.send_keys(char)
                            except: pass
                            time.sleep(random.uniform(0.1, 0.3))
                            
                        print(f"[Thread-{flow_type}] Đang chờ danh sách gợi ý xuất hiện...")
                        xpath_options = "//ul[@role='listbox']//li[@role='option']"
                        options_ht = wait_60.until(EC.presence_of_all_elements_located((By.XPATH, xpath_options)))
                        
                        print(f"[Thread-{flow_type}] Đã tìm thấy {len(options_ht)} gợi ý Quê quán. Chọn ngẫu nhiên...")
                        random_option_ht = random.choice(options_ht)
                        click_hard(driver, random_option_ht)
                        time.sleep(random.uniform(1.0, 2.0))
                        
                        xpath_save = "//*[text()='Lưu' or text()='Save']/ancestor::div[@role='button'] | //*[text()='Lưu' or text()='Save']"
                        save_els_ht = wait_60.until(EC.presence_of_all_elements_located((By.XPATH, xpath_save)))
                        for s_el in save_els_ht:
                            click_hard(driver, s_el)
                            time.sleep(0.5)
                            
                        print(f"[Thread-{flow_type}] Chờ popup chia sẻ Quê quán...")
                        xpath_success = "//*[contains(text(), 'Chia sẻ ngay') or contains(text(), 'Share to Feed') or contains(text(), 'Bảng feed')]"
                        wait_60.until(EC.presence_of_element_located((By.XPATH, xpath_success)))
                        
                        try:
                            xpath_no = "//*[text()='Không' or text()='No']/ancestor::div[@role='button'] | //*[text()='Không' or text()='No']"
                            for n_el in driver.find_elements(By.XPATH, xpath_no):
                                click_hard(driver, n_el)
                        except: pass
                        
                        print(f"[Thread-{flow_type}] Đã hoàn tất 100% quy trình cập nhật Quê quán!")
                        time.sleep(10)
            except Exception as e:
                print(f"[Thread-{flow_type}] Lỗi khi tương tác trang cá nhân: {e}")
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
