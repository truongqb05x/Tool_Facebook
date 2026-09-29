def do_change_city_now(driver, uid, flow_type="1"):
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
        #print(f"[Thread-{flow_type}] Truy cập vào tab Nơi từng sống của profile...")
        driver.get(f"https://www.facebook.com/profile.php?id={uid}&sk=directory_personal_details")
        time.sleep(5)
        
        xpath_already_filled = "//*[@aria-label and (contains(@aria-label, 'Chỉnh sửa') or contains(@aria-label, 'chỉnh sửa') or contains(@aria-label, 'Edit') or contains(@aria-label, 'edit')) and (contains(@aria-label, 'tỉnh/thành phố') or contains(@aria-label, 'Tỉnh/thành phố') or contains(@aria-label, 'Tỉnh/Thành phố') or contains(@aria-label, 'current city') or contains(@aria-label, 'Current city'))]"
        if driver.find_elements(By.XPATH, xpath_already_filled):
            print(f"[{uid}] BỎ QUA: Tài khoản đã có sẵn thông tin Tỉnh/Thành phố hiện tại rồi!")
            return
            
        #rint(f"[{uid}] Đang tìm nút Thêm 'Tỉnh/thành phố hiện tại'...")
        xpath_city = "//*[contains(text(), 'Tỉnh/thành phố') or contains(text(), 'tỉnh/thành phố') or contains(text(), 'Tỉnh/Thành phố') or contains(text(), 'Current city') or contains(text(), 'current city')]"
        city_els = wait_60.until(EC.presence_of_all_elements_located((By.XPATH, xpath_city)))
        for el in city_els:
            click_hard(driver, el)
            time.sleep(0.5)
            
        xpath_input_city = "//input[@aria-label='Tỉnh/Thành phố hiện tại' or contains(@aria-label, 'Tỉnh/thành phố') or contains(@aria-label, 'Current city')]"
        input_city_els = wait_60.until(EC.presence_of_all_elements_located((By.XPATH, xpath_input_city)))
        
        active_input = None
        for in_el in input_city_els:
            if click_hard(driver, in_el):
                active_input = in_el
                break
            time.sleep(0.5)
            
        if active_input:
            target_city = "Quảng Bình"
            try:
                with open("resources/danhsachthanhpho.txt", "r", encoding="utf-8") as f:
                    lines = [line.strip() for line in f if line.strip()]
                    if lines:
                        target_city = random.choice(lines)
            except: pass
            
            for char in target_city:
                try: active_input.send_keys(char)
                except: pass
                time.sleep(random.uniform(0.1, 0.3))
                
            xpath_options = "//ul[@role='listbox']//li[@role='option']"
            options = wait_60.until(EC.presence_of_all_elements_located((By.XPATH, xpath_options)))
            click_hard(driver, random.choice(options))
            time.sleep(1.5)
            
            xpath_save = "//*[text()='Lưu' or text()='Save']/ancestor::div[@role='button'] | //*[text()='Lưu' or text()='Save']"
            save_els = wait_60.until(EC.presence_of_all_elements_located((By.XPATH, xpath_save)))
            for s_el in save_els:
                click_hard(driver, s_el)
                time.sleep(0.5)
                
            xpath_success = "//*[contains(text(), 'Chia sẻ ngay') or contains(text(), 'Share to Feed') or contains(text(), 'Bảng feed')]"
            wait_60.until(EC.presence_of_element_located((By.XPATH, xpath_success)))
            
            try:
                xpath_no = "//*[text()='Không' or text()='No']/ancestor::div[@role='button'] | //*[text()='Không' or text()='No']"
                for n_el in driver.find_elements(By.XPATH, xpath_no):
                    click_hard(driver, n_el)
            except: pass
            
            print(f"[{uid}] Đổi thành công!")
            time.sleep(3)
    except Exception as e:
        print(f"[{uid}] Lỗi đổi thông tin Thành phố: {e}")
