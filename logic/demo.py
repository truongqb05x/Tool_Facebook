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
            
            try:
                print(f"[Thread-{flow_type}] Truy cập trang 2FA...")
                driver.get("https://accountscenter.facebook.com/password_and_security/two_factor")
                
                wait_120 = WebDriverWait(driver, 120)
                print(f"[Thread-{flow_type}] Đang chờ tài khoản hiển thị...")
                
                # Tìm phần tử role="button" có chứa chữ "Facebook" bên trong
                xpath = "//div[@role='button' and .//div[contains(text(), 'Facebook')]]"
                
                # Thử nhiều lần để chống lỗi stale element (React re-render)
                clicked = False
                for attempt in range(60):
                    try:
                        account_btn = wait_120.until(EC.presence_of_element_located((By.XPATH, xpath)))
                        
                        # Cuộn tới phần tử để đảm bảo nó nằm trong viewport
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'instant'});", account_btn)
                        time.sleep(0.5)
                        
                        # Thử dùng ActionChains (Mô phỏng chuột thật, tốt nhất cho React)
                        try:
                            from selenium.webdriver.common.action_chains import ActionChains
                            ActionChains(driver).move_to_element(account_btn).click().perform()
                        except:
                            # Thử click native
                            try:
                                account_btn.click()
                            except:
                                # Thử click bằng JS
                                driver.execute_script("arguments[0].click();", account_btn)
                        
                        clicked = True
                        break # Thành công thì thoát vòng lặp
                    except Exception as e:
                        if attempt == 59:
                            raise e
                        time.sleep(2)
                
                if clicked:
                    print(f"[Thread-{flow_type}] Đã click chọn tài khoản thành công.")
                    
                    password_handled = False
                    
                    def wait_and_handle_password_modal(dr, pwd, timeout=8):
                        nonlocal password_handled
                        if password_handled:
                            return False
                            
                        end_time = time.time() + timeout
                        while time.time() < end_time:
                            try:
                                pass_inputs = dr.find_elements(By.XPATH, "//input[@type='password']")
                                if pass_inputs:
                                    pass_input = pass_inputs[-1]
                                    if pass_input.is_displayed():
                                        print(f"[Thread-{flow_type}] Phát hiện popup mật khẩu, tiến hành điền...")
                                        dr.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'instant'});", pass_input)
                                        time.sleep(0.5)
                                        try:
                                            pass_input.click()
                                        except:
                                            pass
                                        
                                        # Xóa trắng nhỡ lưu đệm
                                        pass_input.clear()
                                        pass_input.send_keys(pwd)
                                        
                                        tiep_tuc_btns = dr.find_elements(By.XPATH, "//div[@role='button' and .//span[text()='Tiếp tục']]")
                                        if tiep_tuc_btns:
                                            btn = tiep_tuc_btns[-1]
                                            dr.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'instant'});", btn)
                                            time.sleep(0.5)
                                            try: btn.click()
                                            except: dr.execute_script("arguments[0].click();", btn)
                                        
                                        time.sleep(3)
                                        password_handled = True
                                        return True
                            except:
                                pass
                            time.sleep(1)
                        return False
                    
                    # 1. Chờ và ấn nút "Tiếp tục"
                    print(f"[Thread-{flow_type}] Kiểm tra popup mật khẩu trước bước 1...")
                    wait_and_handle_password_modal(driver, password, 8)
                    
                    print(f"[Thread-{flow_type}] Đang chờ nút 'Tiếp tục'...")
                    xpath_tiep_tuc = "//div[@role='button' and .//span[text()='Tiếp tục']]"
                    for attempt in range(60):
                        try:
                            # Lấy nút Tiếp tục mà KHÔNG phải của popup mật khẩu (chắc cú)
                            btn_tiep_tuc = wait_120.until(EC.presence_of_element_located((By.XPATH, xpath_tiep_tuc)))
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'instant'});", btn_tiep_tuc)
                            time.sleep(1)
                            try:
                                btn_tiep_tuc.click()
                            except:
                                driver.execute_script("arguments[0].click();", btn_tiep_tuc)
                            break
                        except Exception as e:
                            if attempt == 59: raise Exception(f"Lỗi bước 1 (Ấn 'Tiếp tục'): {e}")
                            time.sleep(2)
                    
                    # 2. Đợi nút "Sao chép khóa" xuất hiện, lấy nội dung khóa và ấn sao chép
                    print(f"[Thread-{flow_type}] Kiểm tra popup mật khẩu trước bước 2...")
                    wait_and_handle_password_modal(driver, password, 8)
                    
                    print(f"[Thread-{flow_type}] Đang chờ nút 'Sao chép khóa'...")
                    xpath_sao_chep = "//div[@role='button' and text()='Sao chép khóa']"
                    khoa_2fa = ""
                    for attempt in range(60):
                        try:
                            btn_sao_chep = wait_120.until(EC.presence_of_element_located((By.XPATH, xpath_sao_chep)))
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'instant'});", btn_sao_chep)
                            time.sleep(1)
                            
                            spans = driver.find_elements(By.TAG_NAME, "span")
                            for s in spans:
                                txt = s.text.strip()
                                if len(txt) >= 32 and len(txt) <= 50 and " " in txt and txt.replace(" ", "").isalnum():
                                    khoa_2fa = txt.replace(" ", "")
                                    break
                                    
                            try:
                                btn_sao_chep.click()
                            except:
                                driver.execute_script("arguments[0].click();", btn_sao_chep)
                            break
                        except Exception as e:
                            if attempt == 59: raise Exception(f"Lỗi bước 2 (Sao chép khóa): {e}")
                            time.sleep(2)
                            
                    print(f"[Thread-{flow_type}] Đã click 'Sao chép khóa'. Khóa bóc được: {khoa_2fa}")
                    
                    # 3. Đợi thông báo "Đã sao chép vào bộ nhớ tạm"
                    
                    print(f"[Thread-{flow_type}] Đang chờ thông báo 'Đã sao chép vào bộ nhớ tạm'...")
                    xpath_thong_bao = "//span[text()='Đã sao chép vào bộ nhớ tạm']"
                    for attempt in range(60):
                        try:
                            wait_120.until(EC.presence_of_element_located((By.XPATH, xpath_thong_bao)))
                            break
                        except Exception as e:
                            if attempt == 59: raise Exception(f"Lỗi bước 3 (Đợi thông báo sao chép): {e}")
                            time.sleep(2)
                    time.sleep(1)
                    
                    # 4. Ấn nút "Nhập mã"
                    
                    print(f"[Thread-{flow_type}] Đang chờ nút 'Nhập mã'...")
                    xpath_nhap_ma = "//div[@role='button' and .//span[text()='Nhập mã']]"
                    for attempt in range(60):
                        try:
                            btn_nhap_ma = wait_120.until(EC.presence_of_element_located((By.XPATH, xpath_nhap_ma)))
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'instant'});", btn_nhap_ma)
                            time.sleep(1)
                            try:
                                btn_nhap_ma.click()
                            except:
                                driver.execute_script("arguments[0].click();", btn_nhap_ma)
                            break
                        except Exception as e:
                            if attempt == 59: raise Exception(f"Lỗi bước 4 (Ấn 'Nhập mã'): {e}")
                            time.sleep(2)
                            
                    # 5. Tạo TOTP và nhập mã
                    print(f"[Thread-{flow_type}] Kiểm tra popup mật khẩu trước bước 5...")
                    wait_and_handle_password_modal(driver, password, 8)
                    
                    print(f"[Thread-{flow_type}] Đang chờ ô nhập mã...")
                    import pyotp
                    if not khoa_2fa:
                        khoa_2fa = fa2_secret
                        
                    totp = pyotp.TOTP(khoa_2fa)
                    
                    xpath_input_ma = "//input[@type='text' and @maxlength='6']"
                    for attempt in range(60):
                        try:
                            input_ma = wait_120.until(EC.presence_of_element_located((By.XPATH, xpath_input_ma)))
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'instant'});", input_ma)
                            time.sleep(1)
                            
                            try:
                                input_ma.click()
                            except:
                                driver.execute_script("arguments[0].click();", input_ma)
                            time.sleep(0.5)
                            
                            # Cập nhật mã mới nhất ngay trước khi gõ để chống hết hạn
                            ma_6_so = totp.now()
                            input_ma.send_keys(ma_6_so)
                            break
                        except Exception as e:
                            if attempt == 59: raise Exception(f"Lỗi bước 5 (Điền 6 số): {e}")
                            time.sleep(2)
                            
                    print(f"[Thread-{flow_type}] Đã nhập mã {ma_6_so}")
                    
                    # 6. Ấn "Tiếp"
                    print(f"[Thread-{flow_type}] Đang chờ nút 'Tiếp'...")
                    xpath_tiep = "//div[@role='button' and .//span[text()='Tiếp']]"
                    for attempt in range(60):
                        try:
                            btn_tiep = wait_120.until(EC.presence_of_element_located((By.XPATH, xpath_tiep)))
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'instant'});", btn_tiep)
                            time.sleep(1)
                            try:
                                btn_tiep.click()
                            except:
                                driver.execute_script("arguments[0].click();", btn_tiep)
                            break
                        except Exception as e:
                            if attempt == 59: raise Exception(f"Lỗi bước 6 (Ấn 'Tiếp'): {e}")
                            time.sleep(2)
                    
                    print(f"[Thread-{flow_type}] Kiểm tra popup mật khẩu sau bước 6...")
                    wait_and_handle_password_modal(driver, password, 8)
                    
                    # 7. Thông báo thành công và ấn "Xong"
                    print(f"[Thread-{flow_type}] Đang chờ popup báo thành công...")
                    xpath_xong = "//div[@role='button' and .//span[text()='Xong']]"
                    for attempt in range(60):
                        try:
                            btn_xong = wait_120.until(EC.presence_of_element_located((By.XPATH, xpath_xong)))
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'instant'});", btn_xong)
                            time.sleep(1)
                            try:
                                btn_xong.click()
                            except:
                                driver.execute_script("arguments[0].click();", btn_xong)
                            break
                        except Exception as e:
                            if attempt == 59: raise Exception(f"Lỗi bước 7 (Không thấy nút 'Xong' hoặc cài đặt thất bại): {e}")
                            time.sleep(2)
                            
                    print(f"[Thread-{flow_type}] Đã hoàn tất quy trình 2FA.")
                else:
                    print(f"[Thread-{flow_type}] Không thể click chọn tài khoản.")
                
            except Exception as e:
                print(f"[Thread-{flow_type}] Lỗi khi xử lý 2FA: {e}")
                
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
        "61585946429309|Jamesita@69293|c_user=61585946429309;datr=qzVWaTiaH3_DbkUsq814ROln;fr=0fOP4AsFOBq6IOUWt.AWcH3rzeaeuibCNyc7O4i5Zuss0FTZviD_JfPLRNSgJhniJ3YkQ.BpVjWr..AAA.0.0.BpVjWw.AWftP_rrajsIjz9JfAZkca7vg6E;ps_l=1;ps_n=1;sb=qzVWaSUO6o3WRychbD4d9uoY;locale=en_US;xs=39%3A0BAB46fc1t_9fg%3A2%3A1767257524%3A-1%3A-1"
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
