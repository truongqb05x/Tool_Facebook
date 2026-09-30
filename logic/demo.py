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
    proxy_str = "171.249.209.132:31731:8K35Fz:4jIe50"
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
                print(f"[Thread-{flow_type}] Đang truy cập group: https://www.facebook.com/groups/dhsphue")
                driver.get("https://www.facebook.com/groups/dhsphue?sorting_setting=CHRONOLOGICAL")
                time.sleep(8)
                
                # Tìm bài viết từ trên xuống dưới mà không bỏ qua bài đầu
                print(f"[Thread-{flow_type}] Bắt đầu tìm ô comment...")
                box_to_comment = None
                
                for scan_step in range(5):
                    comment_boxes = driver.find_elements(By.XPATH, "//div[@role='textbox' and @contenteditable='true']")
                    for box in comment_boxes:
                        if box.is_displayed():
                            aria_label = box.get_attribute("aria-label") or ""
                            # Bỏ qua ô đăng bài viết mới
                            if "viết gì đó" in aria_label.lower() or "write something" in aria_label.lower():
                                continue
                            box_to_comment = box
                            break
                    
                    if box_to_comment:
                        break
                        
                    # Nếu chưa có ô comment, tìm nút "Bình luận"
                    comment_btns = driver.find_elements(By.XPATH, "//div[@role='button' and (@aria-label='Bình luận' or @aria-label='Comment' or @aria-label='Viết bình luận') and not(@data-scanned='true')]")
                    btn_clicked = False
                    for btn in comment_btns:
                        if btn.is_displayed():
                            try:
                                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                                time.sleep(1)
                                driver.execute_script("arguments[0].setAttribute('data-scanned', 'true')", btn)
                                driver.execute_script("arguments[0].click();", btn)
                                time.sleep(2)
                                btn_clicked = True
                                break
                            except: pass
                    
                    if btn_clicked:
                        # Kiểm tra lại ô comment sau khi click
                        comment_boxes = driver.find_elements(By.XPATH, "//div[@role='textbox' and @contenteditable='true']")
                        for box in comment_boxes:
                            if box.is_displayed():
                                aria_label = box.get_attribute("aria-label") or ""
                                if "viết gì đó" in aria_label.lower() or "write something" in aria_label.lower():
                                    continue
                                box_to_comment = box
                                break
                                
                    if box_to_comment:
                        break
                        
                    # Cuộn nhẹ để tìm bài tiếp theo
                    driver.execute_script("window.scrollBy(0, 400);")
                    time.sleep(2)
                
                if box_to_comment:
                        print(f"[Thread-{flow_type}] Đã tìm thấy ô bình luận, đang lấy link bài viết...")
                        try:
                            # Tìm div bọc cả bài viết (chứa cả ô comment và thẻ a target='_blank' của thời gian đăng bài)
                            post_container = box_to_comment.find_element(By.XPATH, "./ancestor::div[.//a[@role='link' and @target='_blank']][1]")
                            
                            post_links = post_container.find_elements(By.XPATH, ".//a[@role='link' and @target='_blank']")
                            real_post_link = None
                            post_time = "Không xác định"
                            found_link_element = None
                            
                            for link in post_links:
                                try:
                                    # Cố gắng lấy text thời gian từ thẻ cha
                                    try:
                                        parent_text = link.find_element(By.XPATH, "..").text
                                        if parent_text:
                                            post_time = parent_text.split("·")[0].strip()
                                    except:
                                        pass

                                    href = link.get_attribute("href")
                                    if href and ("/posts/" in href or "/permalink/" in href):
                                        real_post_link = href
                                        found_link_element = link
                                        break
                                    
                                    # Hover để Facebook kích hoạt đổi href thật
                                    from selenium.webdriver.common.action_chains import ActionChains
                                    ActionChains(driver).move_to_element(link).perform()
                                    time.sleep(1)
                                    
                                    href_after_hover = link.get_attribute("href")
                                    if href_after_hover and ("/posts/" in href_after_hover or "/permalink/" in href_after_hover):
                                        real_post_link = href_after_hover
                                        found_link_element = link
                                        break
                                except Exception:
                                    pass
                                    
                            if not real_post_link and post_links:
                                # Nếu hover không đổi được link thật, thì lấy luôn href hiện có
                                href = post_links[0].get_attribute("href")
                                if href:
                                    real_post_link = href
                                    found_link_element = post_links[0]
                                    
                            if real_post_link:
                                # Xóa bớt các params không cần thiết nếu nó là link sạch
                                if "/posts/" in real_post_link or "/permalink/" in real_post_link:
                                    real_post_link = real_post_link.split("?")[0]
                                    
                                # Lọc ra ID bài viết
                                import re
                                post_id = ""
                                match = re.search(r'/(?:posts|permalink)/(\d+)', real_post_link)
                                if match:
                                    post_id = match.group(1)
                                else:
                                    # Fallback nếu không khớp regex nhưng vẫn có ID ở cuối
                                    post_id = real_post_link.rstrip("/").split("/")[-1]
                                    
                                print(f"[Thread-{flow_type}] 🕒 THỜI GIAN ĐĂNG: {post_time}")
                                print(f"[Thread-{flow_type}] 🔗 ID BÀI VIẾT: {post_id}")
                                
                                # --- TEST LOGIC: Nhấn trực tiếp vào thẻ <a> ---
                                if found_link_element:
                                    print(f"[Thread-{flow_type}] 🚀 [TEST] Đang click trực tiếp vào thẻ <a> (thời gian bài viết) để mở modal...")
                                    try:
                                        # Hủy bỏ thuộc tính target="_blank" để ngăn mở tab mới
                                        driver.execute_script("arguments[0].removeAttribute('target');", found_link_element)
                                        # Dùng JS click để mở modal
                                        script = "arguments[0].dispatchEvent(new MouseEvent('click', {view: window, bubbles: true, cancelable: true}));"
                                        driver.execute_script(script, found_link_element)
                                        time.sleep(6) # Đợi modal tải
                                    except Exception as e_click:
                                        print(f"[Thread-{flow_type}] ❌ Lỗi khi click link: {e_click}")
                                    
                                    print(f"[Thread-{flow_type}] 🔍 Đang tìm nút Đóng (X)...")
                                    # Lấy tất cả nút Đóng
                                    close_btns = driver.find_elements(By.XPATH, "//div[(@aria-label='Đóng' or @aria-label='Close' or @aria-label='Thoát') and @role='button']")
                                    
                                    if close_btns:
                                        print(f"[Thread-{flow_type}] ✅ Tìm thấy {len(close_btns)} nút Đóng trên trang.")
                                        for i, btn in enumerate(close_btns):
                                            try:
                                                is_disp = btn.is_displayed()
                                            except:
                                                is_disp = "Stale/Hidden"
                                                
                                            print(f"[Thread-{flow_type}] 👉 Đang click nút Đóng thứ {i+1} (Selenium is_displayed: {is_disp})...")
                                            from selenium.webdriver.common.action_chains import ActionChains
                                            from selenium.webdriver.common.keys import Keys
                                            
                                            # Cách 1: Kích hoạt sự kiện chuột cấp thấp
                                            try:
                                                script = "arguments[0].dispatchEvent(new MouseEvent('click', {view: window, bubbles: true, cancelable: true}));"
                                                driver.execute_script(script, btn)
                                                print(f"[Thread-{flow_type}]    -> JS dispatchEvent THÀNH CÔNG")
                                            except Exception as e: print(f"[Thread-{flow_type}]    -> JS dispatch lỗi: {e}")
                                            
                                            # Cách 2: JS click thông thường
                                            try:
                                                driver.execute_script("arguments[0].click();", btn)
                                            except: pass
                                            
                                            # Cách 3: Native click
                                            try:
                                                if btn.is_displayed():
                                                    btn.click()
                                            except: pass
                                            
                                            time.sleep(1.5)
                                    else:
                                        print(f"[Thread-{flow_type}] ℹ️ Không tìm thấy nút Đóng nào đang hiển thị trên link này.")
                                # ------------------------------------------------------
                            else:
                                print(f"[Thread-{flow_type}] ❌ Không thể lấy được link bài viết.")
                                        
                        except Exception as e:
                            print(f"[Thread-{flow_type}] Không tìm thấy link post theo cấu trúc HTML: {e}")
                else:
                    print(f"[Thread-{flow_type}] Không tìm thấy khung comment nào.")
            except Exception as e:
                print(f"[Thread-{flow_type}] Lỗi khi xử lý bài viết: {e}")

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
