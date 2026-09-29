def do_change_uni(driver, uid, flow_type="1"):
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
        
        #print(f"[{uid}] Kiểm tra xem đã có Trường cao đẳng/đại học chưa...")
        xpath_edu_filled = "//*[@aria-label='Chỉnh sửa trường cao đẳng/đại học' or @aria-label='Edit college' or @aria-label='Edit university']"
        if driver.find_elements(By.XPATH, xpath_edu_filled):
            print(f"[{uid}] BỎ QUA: Tài khoản đã có sẵn thông tin Trường đại học rồi!")
            return
            
        #print(f"[Thread-{flow_type}] Đang tìm nút 'Trường cao đẳng/đại học'...")
        xpath_edu_btn = "//*[contains(text(), 'Trường cao đẳng') or contains(text(), 'đại học') or contains(text(), 'College') or contains(text(), 'University')]"
        edu_els = wait_60.until(EC.presence_of_all_elements_located((By.XPATH, xpath_edu_btn)))
        for el in edu_els:
            click_hard(driver, el)
            time.sleep(0.5)
            
        xpath_input_edu = "//input[contains(@aria-label, 'đại học') or contains(@aria-label, 'cao đẳng') or contains(@aria-label, 'trường') or contains(@aria-label, 'College') or contains(@aria-label, 'University') or contains(@aria-label, 'School')]"
        input_edu_els = wait_60.until(EC.presence_of_all_elements_located((By.XPATH, xpath_input_edu)))
        
        active_edu = None
        for in_el in input_edu_els:
            if click_hard(driver, in_el):
                active_edu = in_el
                break
            time.sleep(0.5)
            
        if active_edu:
            target_edu = "Quảng Bình"
            try:
                with open("resources/danhsachthanhpho.txt", "r", encoding="utf-8") as f:
                    lines = [line.strip() for line in f if line.strip()]
                    if lines:
                        target_edu = random.choice(lines)
            except: pass
            
            for char in target_edu:
                try: active_edu.send_keys(char)
                except: pass
                time.sleep(random.uniform(0.1, 0.3))
                
            xpath_opts = "//ul[@role='listbox']//li[@role='option']"
            edu_options = wait_60.until(EC.presence_of_all_elements_located((By.XPATH, xpath_opts)))
            click_hard(driver, random.choice(edu_options))
            time.sleep(1.5)
            
            xpath_save = "//*[text()='Lưu' or text()='Save']/ancestor::div[@role='button'] | //*[text()='Lưu' or text()='Save']"
            save_edu = wait_60.until(EC.presence_of_all_elements_located((By.XPATH, xpath_save)))
            for s_el in save_edu:
                click_hard(driver, s_el)
                time.sleep(0.5)
                
            print(f"[{uid}] Đổi thành công")
            time.sleep(3)
    except Exception as e:
        print(f"[{uid}] Lỗi đổi thông tin Trường ĐH: {e}")
