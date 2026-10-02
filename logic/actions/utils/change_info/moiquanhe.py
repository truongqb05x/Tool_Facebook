def do_change_moiquanhe(driver, uid, flow_type="1"):
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
        #print(f"[Thread-{flow_type}] Truy cập vào tab Mối quan hệ của profile...")
        driver.get(f"https://www.facebook.com/profile.php?id={uid}&sk=directory_personal_details")
        time.sleep(5)
        
        #print(f"[{uid}] Kiểm tra xem tài khoản đã có Tình trạng mối quan hệ chưa...")
        xpath_rel_filled = "//*[@aria-label='Chỉnh sửa mối quan hệ' or @aria-label='Edit relationship' or @aria-label='Edit Relationship']"
        if driver.find_elements(By.XPATH, xpath_rel_filled):
            print(f"[{uid}] BỎ QUA: Tài khoản đã có sẵn Tình trạng mối quan hệ rồi!")
            return
            
        #print(f"[Thread-{flow_type}] Đang tìm nút 'Tình trạng mối quan hệ'...")
        xpath_rel_btn = "//*[contains(text(), 'Tình trạng mối quan hệ') or contains(text(), 'Relationship status')]"
        rel_els = wait_60.until(EC.presence_of_all_elements_located((By.XPATH, xpath_rel_btn)))
        for el in rel_els:
            click_hard(driver, el)
            time.sleep(0.5)
        
        xpath_combo = "//*[@aria-label='Chọn tình trạng mối quan hệ của bạn' or @aria-label='Select your relationship status']"
        combo_el = wait_60.until(EC.presence_of_element_located((By.XPATH, xpath_combo)))
        click_hard(driver, combo_el)
        time.sleep(random.uniform(1.0, 1.5))
        
        xpath_options = "//div[@role='option' or @role='listbox']//span[contains(text(), 'Độc thân') or contains(text(), 'Đang hẹn hò') or contains(text(), 'Tìm hiểu') or contains(text(), 'Single') or contains(text(), 'In a relationship') or contains(text(), \"It's complicated\")]"
        all_options = wait_60.until(EC.presence_of_all_elements_located((By.XPATH, xpath_options)))
        chosen = random.choice(all_options)
        click_hard(driver, chosen)
        time.sleep(random.uniform(1.0, 2.0))
        
        xpath_save = "//*[text()='Lưu' or text()='Save']/ancestor::div[@role='button'] | //*[text()='Lưu' or text()='Save']"
        save_els = wait_60.until(EC.presence_of_all_elements_located((By.XPATH, xpath_save)))
        for s_el in save_els:
            click_hard(driver, s_el)
            time.sleep(0.5)
            
        print(f"[{uid}] Đổi thành công")
        time.sleep(3)
    except Exception as e:
        print(f"[{uid}] Lỗi đổi thông tin Mối quan hệ: {e}")
