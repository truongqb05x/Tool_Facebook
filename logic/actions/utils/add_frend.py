import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

def add_suggested_friends(driver, uid, target_clicks=1):
    try:
        print(f"[{uid}] Đang chuyển đến trang Gợi ý kết bạn...")
        driver.get("https://www.facebook.com/friends/suggestions")
        
        try:
            # Chờ để tải giao diện
            WebDriverWait(driver, 10).until(
                lambda d: "Lời mời và gợi ý kết bạn sẽ hiển thị tại đây." in d.page_source or 
                          "Thêm bạn bè" in d.page_source or 
                          "Add Friend" in d.page_source
            )
        except:
            pass
            
        time.sleep(2)
        
        clicks_done = 0

        if "Lời mời và gợi ý kết bạn sẽ hiển thị tại đây." in driver.page_source:
            print(f"[{uid}] Không có gợi ý lời mời nào. Chuyển hướng đến https://www.facebook.com/lichsungoaitruyen/")
            driver.get("https://www.facebook.com/lichsungoaitruyen/")
            time.sleep(5)
            
            print(f"[{uid}] Bắt đầu lướt tìm khối cảm xúc...")
            found = False
            for _ in range(50):
                try:
                    el = driver.find_element(By.XPATH, "//*[@aria-label='Xem ai đã bày tỏ cảm xúc về tin này']")
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", el)
                    time.sleep(2)
                    
                    try:
                        el.click()
                    except:
                        driver.execute_script("arguments[0].click();", el)
                        
                    print(f"[{uid}] Đã click vào khối cảm xúc thành công.")
                    found = True
                    
                    print(f"[{uid}] Đợi modal danh sách người thả cảm xúc...")
                    try:
                        WebDriverWait(driver, 30).until(
                            lambda d: len(d.find_elements(By.XPATH, "//div[@aria-label='Thêm bạn bè']")) > 0
                        )
                        time.sleep(3)
                        add_btns = driver.find_elements(By.XPATH, "//div[@aria-modal='true']//div[@aria-label='Thêm bạn bè'] | //div[@aria-label='Thêm bạn bè']")
                        print(f"[{uid}] Tìm thấy {len(add_btns)} nút Thêm bạn bè trong danh sách.")
                        
                        if add_btns:
                            for btn in add_btns[:target_clicks]:
                                try:
                                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                                    time.sleep(1)
                                    driver.execute_script("arguments[0].click();", btn)
                                    clicks_done += 1
                                    print(f"[{uid}] Đã gửi lời mời kết bạn từ modal ({clicks_done}/{target_clicks}).")
                                    time.sleep(1.5)
                                except Exception as e:
                                    print(f"[{uid}] Lỗi click: {e}")
                    except Exception as e:
                        print(f"[{uid}] Không tải được modal danh sách: {e}")
                        
                    break
                except Exception:
                    driver.execute_script("window.scrollBy(0, 400);")
                    time.sleep(1.5)
                    
            if not found:
                print(f"[{uid}] Không tìm thấy khối cảm xúc trên trang.")
        else:
            print(f"[{uid}] Đã tải trang gợi ý kết bạn có danh sách.")
            try:
                sugg_btns = driver.find_elements(By.XPATH, "//div[@aria-label='Thêm bạn bè']")
                if sugg_btns:
                    print(f"[{uid}] Tìm thấy {len(sugg_btns)} nút Thêm bạn bè ở trang gợi ý.")
                    for btn in sugg_btns[:target_clicks]:
                        try:
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                            time.sleep(1)
                            driver.execute_script("arguments[0].click();", btn)
                            clicks_done += 1
                            print(f"[{uid}] Đã gửi lời mời kết bạn từ trang gợi ý ({clicks_done}/{target_clicks}).")
                            time.sleep(1.5)
                        except Exception as e:
                            print(f"[{uid}] Lỗi click Thêm bạn bè: {e}")
            except Exception as e:
                pass

    except Exception as e:
        print(f"[{uid}] Lỗi khi chạy Kết bạn gợi ý: {e}")
