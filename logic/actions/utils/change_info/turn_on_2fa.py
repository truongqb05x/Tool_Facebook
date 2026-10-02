import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def do_change_2fa(driver, uid, password, fa2_secret, flow_type="1"):
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
            print(f"[{uid}] UI_2FA_UPDATED|{khoa_2fa}")
            return True
        else:
            print(f"[Thread-{flow_type}] Không thể click chọn tài khoản.")
        
    except Exception as e:
        print(f"[Thread-{flow_type}] Lỗi khi xử lý 2FA: {e}")
    return False
