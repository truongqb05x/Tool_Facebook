def do_change_change_name(driver, uid, flow_type="1"):
    import time
    import random
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    wait_60 = WebDriverWait(driver, 60)
    
    try:
        #print(f"[Thread-{flow_type}] Truy cập trực tiếp trang đổi Tên của Account Center...")
        driver.get(f"https://accountscenter.facebook.com/profiles/{uid}/name")
        time.sleep(5)
        
        xpath_limit = "//*[contains(text(), 'chưa thể đổi tên') or contains(text(), 'You can\\'t change your name') or contains(text(), '60 ngày qua') or contains(text(), '60 days')]"
        try:
            wait_3 = WebDriverWait(driver, 3)
            wait_3.until(EC.presence_of_element_located((By.XPATH, xpath_limit)))
            print(f"[{uid}] LỖI: Tài khoản KHÔNG ĐỦ ĐIỀU KIỆN (Bị kẹt 60 ngày)! Bỏ qua.")
            return
        except: pass
        
        xpath_input_ten = "//input[following-sibling::label[text()='Tên' or text()='First name']]"
        xpath_input_ho = "//input[following-sibling::label[text()='Họ' or text()='Last name']]"
        
        input_ten = wait_60.until(EC.presence_of_element_located((By.XPATH, xpath_input_ten)))
        input_ho = wait_60.until(EC.presence_of_element_located((By.XPATH, xpath_input_ho)))
        time.sleep(2)
        
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        ho_path = os.path.join(current_dir, "resources", "ho.txt")
        ten_path = os.path.join(current_dir, "resources", "ten.txt")
        
        with open(ho_path, 'r', encoding='utf-8') as f:
            list_ho = [x.strip() for x in f.readlines() if x.strip()]
        with open(ten_path, 'r', encoding='utf-8') as f:
            list_ten = [x.strip() for x in f.readlines() if x.strip()]
            
        random_ho = random.choice(list_ho)
        random_ten = random.choice(list_ten)
        
        if random.random() < 0.3:
            random_ho = random_ho.split()[0]
        
        def type_like_human(element, text):
            from selenium.webdriver.common.keys import Keys
            element.send_keys(Keys.CONTROL + "a")
            time.sleep(0.3)
            element.send_keys(Keys.BACKSPACE)
            time.sleep(0.5)
            for char in text:
                element.send_keys(char)
                time.sleep(random.uniform(0.05, 0.2))
                
        type_like_human(input_ho, random_ho)
        time.sleep(random.uniform(1, 2))
        type_like_human(input_ten, random_ten)
        time.sleep(random.uniform(1, 2))
        
        delay_save = random.uniform(3.0, 5.0)
        time.sleep(delay_save)
        
        xpath_review = "//*[contains(text(), 'Xem lại thay đổi') or contains(text(), 'Review change')]"
        review_els = wait_60.until(EC.presence_of_all_elements_located((By.XPATH, xpath_review)))
        
        for rel in review_els:
            try: rel.click(); break
            except:
                try: driver.execute_script("arguments[0].click();", rel); break
                except:
                    try: driver.execute_script("arguments[0].parentElement.click();", rel); break
                    except: pass
                    
        xpath_done = "//*[text()='Xong' or text()='Done' or contains(text(), 'Done')]"
        done_els = wait_60.until(EC.presence_of_all_elements_located((By.XPATH, xpath_done)))
        time.sleep(2)
        
        for del_btn in done_els:
            try: del_btn.click(); break
            except:
                try: driver.execute_script("arguments[0].click();", del_btn); break
                except:
                    try: driver.execute_script("arguments[0].parentElement.click();", del_btn); break
                    except: pass
                    
        def is_done_redirected(drv):
            curr = drv.current_url or ""
            return f"/profiles/{uid}" in curr and "/name" not in curr
            
        wait_60.until(is_done_redirected)
        print(f"[{uid}] Đổi tên thành công")
        
    except Exception as ex:
        print(f"[{uid}] Lỗi khi đổi tên: {ex}")
