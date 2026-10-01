import time
import random
from selenium.webdriver.common.by import By

def accept_friends(driver, uid, target_clicks):
    try:
        print(f"[{uid}] Đang chuyển đến trang Friends Requests...")
        driver.get("https://www.facebook.com/friends/requests")
        time.sleep(3)
        
        print(f"[{uid}] Đang chờ nút 'Xác nhận'...")
        end_wait = time.time() + 15
        clicks_done = 0
        has_no_requests = False
        
        while time.time() < end_wait:
            try:
                # Check for "Không có yêu cầu mới"
                no_req_els = driver.find_elements(By.XPATH, "//*[contains(text(), 'Không có yêu cầu mới')]")
                if no_req_els and any(el.is_displayed() for el in no_req_els):
                    print(f"[{uid}] Không có lời mời kết bạn nào.")
                    has_no_requests = True
                    break

                confirm_btns = driver.find_elements(By.XPATH, "//div[@aria-label='Xác nhận'][@role='button']")
                visible_btns = [btn for btn in confirm_btns if btn.is_displayed()]
                
                if visible_btns:
                    btns_to_click = random.sample(visible_btns, min(len(visible_btns), target_clicks - clicks_done))
                    for btn in btns_to_click:
                        driver.execute_script("arguments[0].scrollIntoView({behavior:'smooth', block:'center'});", btn)
                        time.sleep(random.uniform(0.5, 1.0))
                        try:
                            btn.click()
                        except:
                            driver.execute_script("arguments[0].click();", btn)
                        
                        clicks_done += 1
                        print(f"[{uid}] Đã click 'Xác nhận' kết bạn! ({clicks_done}/{target_clicks})")
                        time.sleep(random.uniform(1.0, 2.0))
                        
                if clicks_done >= target_clicks:
                    break
            except Exception:
                pass
            time.sleep(1)
            
        if clicks_done == 0 and not has_no_requests:
            print(f"[{uid}] Không tìm thấy nút 'Xác nhận' nào.")
    except Exception as e:
        print(f"[{uid}] Lỗi khi chấp nhận kết bạn: {e}")
