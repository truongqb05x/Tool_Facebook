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
    cookie_str = parts[2].strip() if len(parts) > 2 else ""
    fa2_secret = parts[3].strip() if len(parts) > 3 else ""  # TOTP secret key

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

    proxy_str = "mienbac.vnproxy.com:15952:8K35Fz:4jIe50"
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
                    login_with_credentials(driver, uid, password)
                    login_done.set()
                login_thread = threading.Thread(target=_do_login, daemon=True)
                login_thread.start()

                # Poll URL tối đa 35s — phát hiện 2FA thì xử lý ngay
                two_fa_detected = False
                end_poll = time.time() + 35
                while time.time() < end_poll:
                    time.sleep(1)
                    try:
                        curr_url = driver.current_url or ""
                    except:
                        break
                    if "two_step_verification" in curr_url or "two_factor" in curr_url:
                        two_fa_detected = True
                        print(f"[Thread-{flow_type}] Phát hiện trang 2FA!")
                        break
                    if login_done.is_set():
                        break  # login xong bình thường (không cần 2FA)

                if two_fa_detected:
                    if fa2_secret:
                        try:
                            import pyotp
                            totp = pyotp.TOTP(fa2_secret)
                            code = totp.now()
                            print(f"[Thread-{flow_type}] Mã 2FA tạo được: {code}")

                            # Tìm ô nhập mã
                            time.sleep(random.uniform(1.5, 3.0))
                            otp_input = None
                            for xp in [
                                "//input[@type='text'][@autocomplete='off']",
                                "//input[@id='_r_3_']",
                                "//input[@type='text']",
                            ]:
                                els = driver.find_elements(By.XPATH, xp)
                                for el in els:
                                    if el.is_displayed():
                                        otp_input = el
                                        break
                                if otp_input: break

                            if otp_input:
                                from selenium.webdriver.common.action_chains import ActionChains
                                driver.execute_script("arguments[0].scrollIntoView({behavior:'smooth', block:'center'});", otp_input)
                                time.sleep(random.uniform(0.5, 1.2))
                                ActionChains(driver).move_to_element(otp_input).click().perform()
                                time.sleep(random.uniform(0.5, 1.0))
                                for ch in code:
                                    otp_input.send_keys(ch)
                                    time.sleep(random.uniform(0.08, 0.18))
                                print(f"[Thread-{flow_type}] Đã nhập mã 2FA xong.")

                                # Nhấn Tiếp tục
                                time.sleep(random.uniform(1.0, 2.5))
                                tiep_tuc_btn = None
                                for xp in [
                                    "//div[@role='button'][.//span[normalize-space()='Tiếp tục' or normalize-space()='Continue']][@aria-disabled='false']",
                                    "//div[@role='button'][.//span[normalize-space()='Tiếp tục' or normalize-space()='Continue']]",
                                ]:
                                    els = driver.find_elements(By.XPATH, xp)
                                    for el in els:
                                        if el.is_displayed() and el.get_attribute('aria-disabled') != 'true':
                                            tiep_tuc_btn = el
                                            break
                                    if tiep_tuc_btn: break

                                if tiep_tuc_btn:
                                    driver.execute_script("arguments[0].scrollIntoView({behavior:'smooth', block:'center'});", tiep_tuc_btn)
                                    time.sleep(random.uniform(0.5, 1.0))
                                    ActionChains(driver).move_to_element(tiep_tuc_btn).perform()
                                    time.sleep(random.uniform(0.3, 0.8))
                                    driver.execute_script("""
                                        arguments[0].dispatchEvent(new MouseEvent('click', {view: window, bubbles: true, cancelable: true}));
                                    """, tiep_tuc_btn)
                                    print(f"[Thread-{flow_type}] Đã click 'Tiếp tục' sau 2FA!")

                                    # --- Chờ URL chuyển sang trang remember_browser ---
                                    print(f"[Thread-{flow_type}] Đang chờ trang 'Tin cậy thiết bị' xuất hiện...")
                                    end_rb = time.time() + 30
                                    remember_browser_appeared = False
                                    while time.time() < end_rb:
                                        time.sleep(1)
                                        try:
                                            rb_url = driver.current_url or ""
                                        except:
                                            break
                                        if "remember_browser" in rb_url or "two_factor/remember" in rb_url:
                                            remember_browser_appeared = True
                                            print(f"[Thread-{flow_type}] Trang 'Tin cậy thiết bị' đã xuất hiện!")
                                            break
                                        # Nếu đã về trang chủ thì xong
                                        if ("facebook.com" in rb_url
                                                and "two" not in rb_url
                                                and "login" not in rb_url
                                                and "checkpoint" not in rb_url):
                                            print(f"[Thread-{flow_type}] Đã về trang chủ sau 2FA!")
                                            break

                                    if remember_browser_appeared:
                                        time.sleep(random.uniform(1.5, 3.0))
                                        # Tìm nút "Tin cậy thiết bị này"
                                        tin_cay_btn = None
                                        for xp in [
                                            "//div[@role='button'][.//span[contains(normalize-space(), 'Tin cậy thiết bị')]]",
                                            "//div[@role='button'][.//span[contains(normalize-space(), 'Trust')]]",
                                            "//div[@role='button'][.//span[contains(normalize-space(), 'Remember')]]",
                                        ]:
                                            els = driver.find_elements(By.XPATH, xp)
                                            for el in els:
                                                if el.is_displayed():
                                                    tin_cay_btn = el
                                                    break
                                            if tin_cay_btn: break

                                        if tin_cay_btn:
                                            driver.execute_script("arguments[0].scrollIntoView({behavior:'smooth', block:'center'});", tin_cay_btn)
                                            time.sleep(random.uniform(0.5, 1.2))
                                            ActionChains(driver).move_to_element(tin_cay_btn).perform()
                                            time.sleep(random.uniform(0.3, 0.8))
                                            driver.execute_script("""
                                                arguments[0].dispatchEvent(new MouseEvent('click', {view: window, bubbles: true, cancelable: true}));
                                            """, tin_cay_btn)
                                            print(f"[Thread-{flow_type}] Đã click 'Tin cậy thiết bị này'!")
                                        else:
                                            print(f"[Thread-{flow_type}] Không tìm thấy nút 'Tin cậy thiết bị', bỏ qua.")

                                        # Đợi URL về trang chủ (checkpoint_src=any hoặc facebook.com/)
                                        print(f"[Thread-{flow_type}] Đang chờ về trang chủ sau xác thực...")
                                        end_home = time.time() + 20
                                        while time.time() < end_home:
                                            time.sleep(1)
                                            try:
                                                home_url = driver.current_url or ""
                                            except:
                                                break
                                            if ("checkpoint_src" in home_url
                                                    or ("facebook.com" in home_url
                                                        and "two" not in home_url
                                                        and "login" not in home_url)):
                                                print(f"[Thread-{flow_type}] ✅ Login 2FA hoàn tất! URL: {home_url}")
                                                break
                                else:
                                    driver.execute_script("document.querySelector('form').submit();")
                                    print(f"[Thread-{flow_type}] Fallback: submit form 2FA.")
                                    time.sleep(8)
                            else:
                                print(f"[Thread-{flow_type}] Không tìm thấy ô nhập mã 2FA!")
                        except ImportError:
                            print(f"[Thread-{flow_type}] Thiếu thư viện pyotp! Chạy: pip install pyotp")
                        except Exception as e2fa:
                            print(f"[Thread-{flow_type}] Lỗi 2FA: {e2fa}")
                    else:
                        print(f"[Thread-{flow_type}] Trang 2FA nhưng không có secret key, bỏ qua.")
                        time.sleep(5)

                login_verified = verify_uid(driver, uid)

        if login_verified:
            print(f"[Thread-{flow_type}] Xác minh login thành công.")
        else:
            print(f"[Thread-{flow_type}] Không thể login, dừng luồng này.")
            return

        # --- Kiểm tra modal "Nhớ mật khẩu" và click OK nếu có ---
        print(f"[Thread-{flow_type}] Kiểm tra modal 'Nhớ mật khẩu'...")
        try:
            time.sleep(random.uniform(1.5, 3.0))
            nho_mk_modal = driver.find_elements(By.XPATH,
                "//h3[.//span[contains(normalize-space(), 'Nhớ mật khẩu') or contains(normalize-space(), 'Save password') or contains(normalize-space(), 'Remember password')]]"
            )
            if nho_mk_modal and any(el.is_displayed() for el in nho_mk_modal):
                print(f"[Thread-{flow_type}] Phát hiện modal 'Nhớ mật khẩu', đang click OK...")
                ok_btn = None
                for xp in [
                    "//div[@aria-label='OK'][@role='button']",
                    "//div[@role='button'][.//span[normalize-space()='OK']]",
                ]:
                    els = driver.find_elements(By.XPATH, xp)
                    for el in els:
                        if el.is_displayed() and el.get_attribute('aria-disabled') != 'true':
                            ok_btn = el
                            break
                    if ok_btn: break

                if ok_btn:
                    from selenium.webdriver.common.action_chains import ActionChains
                    driver.execute_script("arguments[0].scrollIntoView({behavior:'smooth', block:'center'});", ok_btn)
                    time.sleep(random.uniform(0.5, 1.2))
                    ActionChains(driver).move_to_element(ok_btn).perform()
                    time.sleep(random.uniform(0.3, 0.8))
                    driver.execute_script("""
                        arguments[0].dispatchEvent(new MouseEvent('click', {view: window, bubbles: true, cancelable: true}));
                    """, ok_btn)
                    print(f"[Thread-{flow_type}] Đã click OK 'Nhớ mật khẩu'!")
                else:
                    print(f"[Thread-{flow_type}] Không tìm thấy nút OK, bỏ qua modal.")
            else:
                print(f"[Thread-{flow_type}] Không có modal 'Nhớ mật khẩu'.")
        except Exception as e_mk:
            print(f"[Thread-{flow_type}] Lỗi kiểm tra modal mật khẩu: {e_mk}")

        print(f"[Thread-{flow_type}] Đã hoàn tất luồng tự động, giữ trình duyệt mở.")
        while True:
            _ = driver.window_handles
            time.sleep(5)

    except Exception as e:
        print(f"[Thread-{flow_type}] Lỗi hoặc trình duyệt đóng: {e}")


def main():
    # --- Dùng cứng Account được chỉ định ---
    lines = [
        "61585156511244|aaassadasCNs|cookie_test|AFC3YONHIRABV3KPBX53QVYJEUHIR6KN"
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
