import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def view_story(driver, uid):
    try:
        print(f"[{uid}] Đang tìm danh sách story để xem...")
        driver.get("https://www.facebook.com/")
        
        wait_60 = WebDriverWait(driver, 60)
        
        # Chờ load xong trang chủ
        time.sleep(5) 
        
        # Tìm thẻ a trỏ tới trang xem tin (bỏ qua trang tạo tin)
        xpath_story = "//a[contains(@href, '/stories/') and not(contains(@href, '/stories/create'))]"
        wait_60.until(EC.presence_of_element_located((By.XPATH, xpath_story)))
        stories = driver.find_elements(By.XPATH, xpath_story)
        
        if not stories:
            print(f"[{uid}] Không có story nào hiển thị!")
            return False
            
        selected_story = random.choice(stories)
        print(f"[{uid}] Đã tìm thấy {len(stories)} story, đang click ngẫu nhiên...")
        try:
            selected_story.click()
        except:
            driver.execute_script("arguments[0].click();", selected_story)
            
        print(f"[{uid}] Kiểm tra modal 'Bạn đang xem Tin' (Nút OK)...")
        time.sleep(3) # Đợi giao diện xem tin tải lên
        
        try:
            # Tìm nút OK bên trong modal
            ok_btn = driver.find_element(By.XPATH, "//div[@aria-modal='true']//div[@aria-label='OK'] | //div[@aria-label='OK' and @role='button']")
            if ok_btn.is_displayed():
                print(f"[{uid}] Phát hiện modal OK, đang ấn bỏ qua...")
                try:
                    ok_btn.click()
                except:
                    driver.execute_script("arguments[0].click();", ok_btn)
        except Exception:
            pass
            
        watch_time = random.randint(15, 30)
        print(f"[{uid}] Đang xem story... chờ {watch_time} giây!")
        time.sleep(watch_time)
        
        driver.get("https://www.facebook.com/")
        print(f"[{uid}] Đã xem xong, quay lại trang chủ thành công!")
        return True
    except Exception as ex:
        print(f"[{uid}] Lỗi khi click xem story: {ex}")
        return False
