def do_change_quequan(driver, uid, flow_type="1"):
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
        print(f"[Thread-{flow_type}] Truy cập vào tab Nơi từng sống của profile...")
        driver.get(f"https://www.facebook.com/profile.php?id={uid}&sk=about_places")
        time.sleep(5)
        
        print(f"[Thread-{flow_type}] Kiểm tra xem tài khoản đã có thông tin Quê quán chưa...")
        xpath_ht_filled = "//*[@aria-label='Chỉnh sửa quê quán' or @aria-label='Edit hometown' or @aria-label='Edit Hometown']"
        if driver.find_elements(By.XPATH, xpath_ht_filled):
            print(f"[Thread-{flow_type}] BỎ QUA: Tài khoản đã có sẵn thông tin Quê quán rồi!")
            return
            
        print(f"[Thread-{flow_type}] Đang tìm nút Thêm 'Quê quán'...")
        xpath_ht = "//*[contains(text(), 'Quê quán') or contains(text(), 'quê quán') or contains(text(), 'Hometown') or contains(text(), 'hometown')]"
        ht_els = wait_60.until(EC.presence_of_all_elements_located((By.XPATH, xpath_ht)))
        for el in ht_els:
            click_hard(driver, el)
            time.sleep(0.5)
            
        xpath_input_ht = "//input[@aria-label='Quê quán' or contains(@aria-label, 'Quê quán') or contains(@aria-label, 'Hometown')]"
        input_ht_els = wait_60.until(EC.presence_of_all_elements_located((By.XPATH, xpath_input_ht)))
        
        active_ht = None
        for in_el in input_ht_els:
            if click_hard(driver, in_el):
                active_ht = in_el
                break
            time.sleep(0.5)
            
        if active_ht:
            target_ht = "Hà Nội"
            try:
                with open("resources/danhsachthanhpho.txt", "r", encoding="utf-8") as f:
                    lines = [line.strip() for line in f if line.strip()]
                    if lines:
                        target_ht = random.choice(lines)
            except: pass
            
            for char in target_ht:
                try: active_ht.send_keys(char)
                except: pass
                time.sleep(random.uniform(0.1, 0.3))
                
            xpath_options = "//ul[@role='listbox']//li[@role='option']"
            options_ht = wait_60.until(EC.presence_of_all_elements_located((By.XPATH, xpath_options)))
            click_hard(driver, random.choice(options_ht))
            time.sleep(1.5)
            
            xpath_save = "//*[text()='Lưu' or text()='Save']/ancestor::div[@role='button'] | //*[text()='Lưu' or text()='Save']"
            save_els_ht = wait_60.until(EC.presence_of_all_elements_located((By.XPATH, xpath_save)))
            for s_el in save_els_ht:
                click_hard(driver, s_el)
                time.sleep(0.5)
                
            print(f"[Thread-{flow_type}] Đã hoàn tất 100% quy trình cập nhật Quê quán!")
            time.sleep(3)
    except Exception as e:
        print(f"[Thread-{flow_type}] Lỗi đổi thông tin Quê quán: {e}")
