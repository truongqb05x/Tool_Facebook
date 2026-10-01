# -*- coding: utf-8 -*-
import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from utils.waiter import wait_for_element_with_retry, wait_for_clickable_with_retry

from actions.utils.change_language_vie import check_and_change_language_to_vi

def login_with_credentials(driver, username, password, fa2_secret=None):
    """
    Login vào Facebook bằng tài khoản và mật khẩu.
    Tự động xử lý 2FA (TOTP) nếu cung cấp fa2_secret,
    xử lý trang remember_browser sau 2FA,
    và dismiss modal "Nhớ mật khẩu" sau khi login thành công.
    """
    from selenium.webdriver.common.action_chains import ActionChains

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
                print(f"[{username}] Phát hiện trang 2FA!")
                
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
                if fa2_secret:
                    try:
                        import pyotp
                        totp = pyotp.TOTP(fa2_secret)
                        code = totp.now()
                        print(f"[{username}] Mã 2FA: {code}")

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
                        else:
                            print(f"[{username}] Không tìm thấy ô nhập mã 2FA!")
                    except ImportError:
                        print(f"[{username}] Thiếu thư viện pyotp! Chạy: pip install pyotp")
                    except Exception as e2fa:
                        print(f"[{username}] Lỗi xử lý 2FA: {e2fa}")
                        return "INVALID_REQUEST"
                else:
                    two_fa_no_secret_count += 1
                    print(f"[{username}] Trang 2FA xuất hiện nhưng không có fa2_secret.")
                    if two_fa_no_secret_count >= 2:
                        print(f"[{username}] ❌ Tài khoản yêu cầu 2FA nhưng không có fa2_secret. Dừng login.")
                        return False
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

        # 6. Sau khi success → đổi ngôn ngữ + check modal "Nhớ mật khẩu"
        if success:
            check_and_change_language_to_vi(driver, username)
            time.sleep(random.uniform(2.0, 4.0))

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

            time.sleep(6)
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
