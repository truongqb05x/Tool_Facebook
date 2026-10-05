# -*- coding: utf-8 -*-
import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from utils.waiter import wait_for_element_with_retry
import json, os
from actions.utils.change_language_vie import check_and_change_language_to_vi

def login_with_credentials(driver, username, password, fa2_secret=None):

    def _js_click(el):
        driver.execute_script("""
            var el = arguments[0];
            ['mousedown', 'mouseup', 'click'].forEach(function(t) {
                el.dispatchEvent(new MouseEvent(t, {view: window, bubbles: true, cancelable: true}));
            });
        """, el)

    try:
        # 1. Kiểm tra nếu có nút "Dùng trang cá nhân khác" thì nhấn trước
        switch_selectors = [
            (By.XPATH, "//div[@aria-label='Dùng trang cá nhân khác' or @aria-label='Use another profile']"),
            (By.XPATH, "//span[contains(text(), 'Dùng trang cá nhân khác') or contains(text(), 'Use another account')]")
        ]
        switch_btn = None
        for by, val in switch_selectors:
            try:
                switch_btn = driver.find_element(by, val)
                if switch_btn and switch_btn.is_displayed():
                    driver.execute_script("arguments[0].click();", switch_btn)
                    time.sleep(3)
                    break
            except: continue

        # 2. Chờ input email
        email_input = wait_for_element_with_retry(driver, By.NAME, "email", timeout=15, description="Email input")
        if not email_input:
            print(f"[{username}] ❌ Login thất bại.")
            return False

        email_input.clear()
        for char in username:
            email_input.send_keys(char)
            time.sleep(random.uniform(0.05, 0.2))

        # 3. Chờ input password
        pass_input = wait_for_element_with_retry(driver, By.NAME, "pass", timeout=15, description="Password input")
        if not pass_input:
            print(f"[{username}] ❌ Login thất bại.")
            return False

        pass_input.clear()
        for char in password:
            pass_input.send_keys(char)
            time.sleep(random.uniform(0.05, 0.2))

        # 4. Click nút Đăng nhập
        login_btn_selectors = [
            (By.XPATH, "//*[(@aria-label='Log in' or @aria-label='Đăng nhập' or @aria-label='Log In') and @role='button']"),
            (By.NAME, "login"),
            (By.XPATH, "//button[@name='login' or @type='submit']"),
            (By.XPATH, "//div[@role='button']//*[contains(text(), 'Đăng nhập') or contains(text(), 'Log in')]")
        ]
        login_btn_clicked = False
        for by, val in login_btn_selectors:
            try:
                btns = driver.find_elements(by, val)
                if btns:
                    for btn in btns:
                        if btn.is_displayed():
                            try:
                                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                                time.sleep(0.5)
                                driver.execute_script("arguments[0].click();", btn)
                                login_btn_clicked = True
                                break
                            except Exception:
                                pass
                if login_btn_clicked:
                    break
            except Exception:
                continue

        if not login_btn_clicked:
            try:
                pass_input.send_keys(Keys.ENTER)
            except:
                pass

        # 5. Polling URL — xử lý 2FA, remember_browser, checkpoint_src
        max_wait = 60
        poll_interval = 1
        elapsed = 0
        success = False
        two_fa_no_secret_count = 0  # Đếm số lần gặp 2FA mà không có fa2_secret

        from utils.helpers import is_checkpoint as check_checkpoint
        while elapsed < max_wait:
            time.sleep(poll_interval)
            elapsed += poll_interval
            url = driver.current_url.lower()

            is_login    = "login"     in url
            is_two_step = "two_step"  in url or "two_factor" in url

            # Kiểm tra xem có thông báo sai thông tin / bị chặn đăng nhập không
            if is_login:
                try:
                    error_msg_xpaths = [
                        "//span[contains(., 'The login information you entered is incorrect')]",
                        "//span[contains(., 'Thông tin đăng nhập bạn nhập không chính xác')]",
                        "//span[contains(., 'Thông tin đăng nhập bạn đã nhập không chính xác')]",
                        "//a[contains(., 'Find your account and log in.')]",
                        "//a[contains(., 'Tìm tài khoản của bạn và đăng nhập')]"
                    ]
                    for xp in error_msg_xpaths:
                        error_elements = driver.find_elements(By.XPATH, xp)
                        if error_elements and any(el.is_displayed() for el in error_elements):
                            print(f"[{username}] ❌ Bị chặn đăng nhập (Sai thông tin đăng nhập).")
                            return "BLOCKED_LOGIN"
                except Exception:
                    pass

            # checkpoint_src=any → thành công sau 2FA trust device
            if "checkpoint_src" in url:
                success = True
                print(f"[{username}] ✅ Login thành công (sau 2FA trust device).")
                break

            # Trang remember_browser → click "Tin cậy thiết bị này"
            if "remember_browser" in url or "two_factor/remember" in url:
                print(f"[{username}] Trang 'Tin cậy thiết bị' xuất hiện, đang click...")
                time.sleep(random.uniform(1.5, 3.0))
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
                    _js_click(tin_cay_btn)
                    print(f"[{username}] Đã click 'Tin cậy thiết bị này'!")
                else:
                    print(f"[{username}] Không tìm thấy nút Tin cậy thiết bị, bỏ qua.")
                continue  # tiếp tục poll để chờ về trang chủ

            # Trang 2FA → nhập mã TOTP
            if is_two_step:
                # Kiểm tra lỗi modal "Invalid request"
                try:
                    invalid_request = driver.find_elements(By.XPATH, "//div[contains(text(), 'We could not validate your request') or contains(text(), 'Invalid request')]")
                    if invalid_request and any(el.is_displayed() for el in invalid_request):
                        print(f"[{username}] ❌ Phát hiện lỗi 'Invalid request' ở trang 2FA!")
                        ok_btn = driver.find_elements(By.XPATH, "//div[@role='button'][.//span[normalize-space()='OK']]")
                        if ok_btn and any(el.is_displayed() for el in ok_btn):
                            try:
                                _js_click(ok_btn[0])
                            except: pass
                        return "INVALID_REQUEST"
                except Exception:
                    pass

                # Tìm ô nhập 2FA trước khi xác nhận đây là trang cần xử lý mã
                otp_input = None
                for xp in [
                    "//input[@id='approvals_code']",
                    "//input[@name='approvals_code']",
                    "//input[@id='recovery_code_entry']",
                    "//input[@type='text' and @autocomplete='one-time-code']",
                    "//input[@type='text'][@autocomplete='off']",
                ]:
                    try:
                        els = driver.find_elements(By.XPATH, xp)
                        for el in els:
                            if el.is_displayed():
                                otp_input = el
                                break
                        if otp_input: break
                    except: pass

                if otp_input:
                    print(f"[{username}] Phát hiện form nhập mã 2FA!")
                    if fa2_secret:
                        try:
                            import pyotp
                            clean_secret = fa2_secret.replace(' ', '').replace('-', '').upper()
                            totp = pyotp.TOTP(clean_secret)
                            code = totp.now()
                            print(f"[{username}] Mã 2FA: {code}")

                            driver.execute_script("arguments[0].scrollIntoView({behavior:'smooth', block:'center'});", otp_input)
                            time.sleep(random.uniform(0.5, 1.2))
                            ActionChains(driver).move_to_element(otp_input).click().perform()
                            time.sleep(random.uniform(0.5, 1.0))
                            for ch in code:
                                otp_input.send_keys(ch)
                                time.sleep(random.uniform(0.08, 0.18))
                            print(f"[{username}] Đã nhập mã 2FA.")

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
                                _js_click(tiep_tuc_btn)
                                print(f"[{username}] Đã click 'Tiếp tục' sau 2FA!")
                            else:
                                driver.execute_script("document.querySelector('form').submit();")
                                print(f"[{username}] Fallback: submit form 2FA.")
                        except ImportError:
                            print(f"[{username}] Thiếu thư viện pyotp! Chạy: pip install pyotp")
                        except Exception as e2fa:
                            print(f"[{username}] Lỗi xử lý 2FA (có thể sai định dạng secret): {e2fa}. Vẫn chờ bạn tự xác nhận...")
                    else:
                        two_fa_no_secret_count += 1
                        if two_fa_no_secret_count == 1 or two_fa_no_secret_count % 10 == 0:
                            print(f"[{username}] Trang 2FA yêu cầu mã nhưng không có fa2_secret. Đang chờ bạn tự xác nhận...")
                continue  # tiếp tục poll sau khi xử lý 2FA

            is_checkpoint = check_checkpoint(driver)
            if is_checkpoint:
                break  # Checkpoint cứng — không tự giải quyết được

            if not is_login and not is_two_step and not is_checkpoint:
                # Đợi thêm 3s để đảm bảo không tự redirect về 2FA/checkpoint
                time.sleep(3)
                elapsed += 3
                url = driver.current_url.lower()
                is_login      = "login"    in url
                is_two_step   = "two_step" in url or "two_factor" in url
                is_checkpoint = check_checkpoint(driver)

                if is_checkpoint:
                    break

                if not is_login and not is_two_step and not is_checkpoint:
                    success = True
                    print(f"[{username}] ✅ Login thành công.")
                    break

        # 6. Sau khi success → check modal "Nhớ mật khẩu" + về trang chủ + đổi ngôn ngữ
        if success:
            time.sleep(random.uniform(3.0, 5.0))

            # Kiểm tra modal "Nhớ mật khẩu" và click OK nếu có
            try:
                nho_mk = driver.find_elements(By.XPATH,
                    "//h3[.//span[contains(normalize-space(), 'Nhớ mật khẩu') "
                    "or contains(normalize-space(), 'Save password') "
                    "or contains(normalize-space(), 'Remember password')]]"
                )
                if nho_mk and any(el.is_displayed() for el in nho_mk):
                    print(f"[{username}] Phát hiện modal 'Nhớ mật khẩu', đang click OK...")
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
                        driver.execute_script("arguments[0].scrollIntoView({behavior:'smooth', block:'center'});", ok_btn)
                        time.sleep(random.uniform(0.5, 1.2))
                        ActionChains(driver).move_to_element(ok_btn).perform()
                        time.sleep(random.uniform(0.3, 0.8))
                        _js_click(ok_btn)
                        print(f"[{username}] Đã click OK 'Nhớ mật khẩu'!")
                    time.sleep(random.uniform(1.0, 2.0))
            except Exception as e_mk:
                pass  # modal không bắt buộc, bỏ qua lỗi

            print(f"[{username}] Chuyển về trang chủ để kiểm tra ngôn ngữ...")
            driver.get("https://www.facebook.com/")
            time.sleep(random.uniform(4.0, 6.0))

            check_and_change_language_to_vi(driver, username)
            time.sleep(random.uniform(2.0, 4.0))

            return True

        # Hết 60s hoặc gặp checkpoint → thử soft checkpoint
        if check_checkpoint(driver):
            from utils.helpers import is_soft_checkpoint
            if is_soft_checkpoint(driver):
                driver.get("https://www.facebook.com/")
                time.sleep(5)
                if not check_checkpoint(driver):
                    print(f"[{username}] ✅ Login thành công.")
                    check_and_change_language_to_vi(driver, username)
                    time.sleep(10)
                    return True

        print(f"[{username}] ❌ Login thất bại.")
        return False

    except Exception as e:
        print(f"[{username}] ❌ Login thất bại.")
        return False

def verify_and_relogin(driver, uid, cfg):
    curr_url = driver.current_url or ""
    cookies = driver.get_cookies()
    is_logged_in = False
    if any(c['name'] == 'c_user' for c in cookies):
        if "login" not in curr_url and "checkpoint" not in curr_url:
            is_logged_in = True
            
    if not is_logged_in:
        print(f"[{uid}] Phát hiện mất phiên đăng nhập, tiến hành login lại...")
        acc_infos = cfg.get("SelectedAccountsInfo", [])
        password = ""
        fa2 = ""
        cookie_str = ""
        for line in acc_infos:
            parts = line.split("|")
            if len(parts) > 0 and parts[0] == uid:
                if len(parts) > 1: password = parts[1]
                if len(parts) > 2:
                    for p in parts[2:]:
                        p = p.strip()
                        if "c_user=" in p or "sb=" in p or "datr=" in p or ";" in p:
                            cookie_str = p
                        elif p.isalnum() and len(p) >= 10:
                            fa2 = p
                break
        
        login_method = 0
        try:
            curr = os.getcwd()
            for _ in range(4):
                candidate = os.path.join(curr, "settings.json")
                if os.path.exists(candidate):
                    with open(candidate, "r", encoding="utf-8") as f:
                        settings_data = json.load(f)
                        login_method = settings_data.get("loginMethod", 0)
                    break
                curr = os.path.dirname(curr)
        except Exception:
            pass

        res = False
        if login_method == 1 or login_method == 2:
            if cookie_str:
                print(f"[{uid}] Đăng nhập lại bằng Cookie...")
                driver.delete_all_cookies()
                expiry_time = int(time.time()) + (365 * 24 * 3600)
                for c in cookie_str.split(";"):
                    c = c.strip()
                    if not c: continue
                    if "=" in c:
                        k, v = c.split("=", 1)
                        k = k.strip()
                        v = v.strip()
                        if k.lower() != "useragent":
                            try:
                                driver.add_cookie({
                                    "name": k,
                                    "value": v,
                                    "domain": ".facebook.com",
                                    "path": "/",
                                    "expiry": expiry_time
                                })
                            except Exception: pass
                driver.refresh()
                time.sleep(5)
                curr_url_after = driver.current_url or ""
                cookies_after = driver.get_cookies()
                if any(c['name'] == 'c_user' for c in cookies_after) and "login" not in curr_url_after and "checkpoint" not in curr_url_after:
                    res = True
                
                if not res:
                    print(f"[{uid}] Login Cookie thất bại.")
                    if login_method == 2:
                        print(f"[{uid}] Chuyển sang Username/Password (Chế độ Tự động)...")
                        res = login_with_credentials(driver, uid, password, fa2_secret=fa2)
            else:
                if login_method == 1:
                    print(f"[{uid}] Đã chọn Login Cookie nhưng không tìm thấy cookie cho tài khoản này.")
                elif login_method == 2:
                    print(f"[{uid}] Không có cookie, chuyển sang Username/Password (Chế độ Tự động)...")
                    res = login_with_credentials(driver, uid, password, fa2_secret=fa2)
        else:
            print(f"[{uid}] Đăng nhập lại bằng Username/Password...")
            res = login_with_credentials(driver, uid, password, fa2_secret=fa2)

        if not res or res in ["BLOCKED_LOGIN", "INVALID_REQUEST"]:
            print(f"[{uid}] Đăng nhập lại thất bại, bỏ qua task này.")
            

            msg = (
                f"🚨 <b>THÔNG BÁO TÀI KHOẢN DIE</b> 🚨\n\n"
                f"👤 <b>UID:</b> <code>{uid}</code>"
            )
            try:
                from utils.bot_telegram import send_telegram_message
                send_telegram_message(msg)
            except Exception as e:
                print(f"[{uid}] Không thể gửi thông báo Telegram: {e}")

            return False
        print(f"[{uid}] Đăng nhập lại thành công!")
        
        try:
            get_cookie = False
            curr = os.getcwd()
            for _ in range(4):
                candidate = os.path.join(curr, "settings.json")
                if os.path.exists(candidate):
                    with open(candidate, "r", encoding="utf-8") as f:
                        settings_data = json.load(f)
                        get_cookie = settings_data.get("getCookieOnLogin", False)
                    break
                curr = os.path.dirname(curr)
            
            if get_cookie:
                print(f"[{uid}] Đang lấy cookie mới và lưu vào accounts.json...")
                cookies = driver.get_cookies()
                cookie_str = "; ".join([f"{c['name']}={c['value']}" for c in cookies])
                from utils.file_utils import update_account_cookie
                update_account_cookie(uid, cookie_str)
                print(f"[{uid}] Đã cập nhật cookie thành công!")
        except Exception as e:
            print(f"[{uid}] Lỗi khi lấy hoặc lưu cookie: {e}")
            
    return True
