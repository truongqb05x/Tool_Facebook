def do_change_thpt(driver, uid, flow_type="1"):
    import time
    import random
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    wait_60 = WebDriverWait(driver, 60)
    
    def click_hard(drv, element):
        try: drv.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});", element)
        except: pass
        time.sleep(0.5)
        try: element.click(); return True
        except: pass
        try: drv.execute_script("arguments[0].click();", element)
        except: pass
        return False

    try:
        #print(f"[Thread-{flow_type}] Truy cập vào tab Giáo dục của profile...")
        driver.get(f"https://www.facebook.com/profile.php?id={uid}&sk=directory_education")
        time.sleep(5)
        
        #print(f"[{uid}] Kiểm tra xem đã có Trường THPT chưa...")
        xpath_hs_filled = "//h2[.//span[text()='Trường trung học']] | //h2[.//span[text()='High School']]"
        if driver.find_elements(By.XPATH, xpath_hs_filled):
            print(f"[{uid}] BỎ QUA: Tài khoản đã có sẵn thông tin Trường THPT rồi!")
            return
            
        #print(f"[Thread-{flow_type}] Đang tìm nút 'Trường trung học phổ thông'...")
        xpath_hs_btn = "//*[contains(text(), 'Trường trung học phổ thông') or contains(text(), 'trung học phổ thông') or contains(text(), 'High school') or contains(text(), 'High School')]"
        hs_els = wait_60.until(EC.presence_of_all_elements_located((By.XPATH, xpath_hs_btn)))
        for el in hs_els:
            click_hard(driver, el)
            time.sleep(0.5)
            
        xpath_input_hs = "//input[@aria-label='Trường học' or @aria-label='School' or contains(@aria-label, 'Trường học') or contains(@aria-label, 'High school')]"
        input_hs_els = wait_60.until(EC.presence_of_all_elements_located((By.XPATH, xpath_input_hs)))
        
        active_hs = None
        for in_el in input_hs_els:
            if click_hard(driver, in_el):
                active_hs = in_el
                break
            time.sleep(0.5)
            
        if active_hs:
            target_hs = "Quảng Bình"
            try:
                with open("resources/danhsachthanhpho.txt", "r", encoding="utf-8") as f:
                    lines = [line.strip() for line in f if line.strip()]
                    if lines:
                        target_hs = random.choice(lines)
            except: pass
            
            for char in target_hs:
                try: active_hs.send_keys(char)
                except: pass
                time.sleep(random.uniform(0.1, 0.3))
                
            xpath_opts = "//ul[@role='listbox']//li[@role='option']"
            hs_options = wait_60.until(EC.presence_of_all_elements_located((By.XPATH, xpath_opts)))
            click_hard(driver, random.choice(hs_options))
            time.sleep(1.5)
            
            xpath_save = "//*[text()='Lưu' or text()='Save']/ancestor::div[@role='button'] | //*[text()='Lưu' or text()='Save']"
            save_hs = wait_60.until(EC.presence_of_all_elements_located((By.XPATH, xpath_save)))
            for s_el in save_hs:
                click_hard(driver, s_el)
                time.sleep(0.5)
                
            print(f"[{uid}] Đổi thành công")
            time.sleep(3)
    except Exception as e:
        print(f"[{uid}] Lỗi đổi thông tin Trường THPT: {e}")
