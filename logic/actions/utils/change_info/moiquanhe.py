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
                    
                
                # --- XỬ LÝ MỐI QUAN HỆ ---
                print(f"[Thread-{flow_type}] Kiểm tra xem tài khoản đã có Tình trạng mối quan hệ chưa...")
                # Khi đã có, FB hiện nút aria-label="Chỉnh sửa mối quan hệ"
                xpath_rel_filled = "//*[@aria-label='Chỉnh sửa mối quan hệ' or @aria-label='Edit relationship' or @aria-label='Edit Relationship']"
                if driver.find_elements(By.XPATH, xpath_rel_filled):
                    print(f"[Thread-{flow_type}] BỎ QUA: Tài khoản đã có sẵn Tình trạng mối quan hệ rồi!")
                    return
                    
                print(f"[Thread-{flow_type}] Đang tìm nút 'Tình trạng mối quan hệ'...")
                xpath_rel_btn = "//*[contains(text(), 'Tình trạng mối quan hệ') or contains(text(), 'Relationship status')]"
                rel_els = wait_60.until(EC.presence_of_all_elements_located((By.XPATH, xpath_rel_btn)))
                
                print(f"[Thread-{flow_type}] Đã thấy mục, tiến hành click...")
                for el in rel_els:
                    click_hard(driver, el)
                    time.sleep(0.5)
                
                print(f"[Thread-{flow_type}] Đang chờ combobox 'Chọn tình trạng mối quan hệ' xuất hiện...")
                xpath_combo = "//*[@aria-label='Chọn tình trạng mối quan hệ của bạn' or @aria-label='Select your relationship status']"
                combo_el = wait_60.until(EC.presence_of_element_located((By.XPATH, xpath_combo)))
                
                print(f"[Thread-{flow_type}] Đã thấy combobox, tiến hành click...")
                click_hard(driver, combo_el)
                time.sleep(random.uniform(1.0, 1.5))
                
                print(f"[Thread-{flow_type}] Đang chờ danh sách tùy chọn xuất hiện...")
                # Các lựa chọn dạng option trong listbox
                xpath_options = "//div[@role='option' or @role='listbox']//span[contains(text(), 'Độc thân') or contains(text(), 'Đang hẹn hò') or contains(text(), 'Tìm hiểu') or contains(text(), 'Single') or contains(text(), 'In a relationship') or contains(text(), \"It's complicated\")]"
                all_options = wait_60.until(EC.presence_of_all_elements_located((By.XPATH, xpath_options)))
                
                print(f"[Thread-{flow_type}] Đã tìm thấy {len(all_options)} tùy chọn. Chọn ngẫu nhiên...")
                chosen = random.choice(all_options)
                print(f"[Thread-{flow_type}] Chọn: {chosen.text}")
                click_hard(driver, chosen)
                time.sleep(random.uniform(1.0, 2.0))
                
                print(f"[Thread-{flow_type}] Đang tìm và ấn nút Lưu...")
                xpath_save = "//*[text()='Lưu' or text()='Save']/ancestor::div[@role='button'] | //*[text()='Lưu' or text()='Save']"
                save_els = wait_60.until(EC.presence_of_all_elements_located((By.XPATH, xpath_save)))
                for s_el in save_els:
                    click_hard(driver, s_el)
                    time.sleep(0.5)
                    
                print(f"[Thread-{flow_type}] Đã hoàn tất 100% quy trình cập nhật Mối quan hệ!")
                time.sleep(3)
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
