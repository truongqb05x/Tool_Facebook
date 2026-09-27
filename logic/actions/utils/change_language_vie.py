# -*- coding: utf-8 -*-
import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

def check_and_change_language_to_vi(driver, username):
    """Kiểm tra ngôn ngữ, nếu là tiếng Anh thì đổi sang Tiếng Việt. Thử tối đa 3 lần."""
    
    def do_click(xpath, fallback_texts=None):
        end_time = time.time() + 30
        while time.time() < end_time:
            try:
                elements = driver.find_elements(By.XPATH, xpath)
                for el in elements:
                    try:
                        if el.is_displayed() or el.get_attribute("aria-hidden") == "false" or True:
                            driver.execute_script("arguments[0].click();", el)
                            time.sleep(1)
                            return
                    except:
                        pass
                
                if fallback_texts:
                    success = driver.execute_script("""
                        var texts = arguments[0];
                        var els = document.querySelectorAll('span, div');
                        for(var i=0; i<els.length; i++) {
                            var text = els[i].innerText;
                            if (text && els[i].children.length === 0) {
                                text = text.trim();
                                for(var j=0; j<texts.length; j++) {
                                    if (text === texts[j] || text.includes(texts[j])) {
                                        els[i].click();
                                        return true;
                                    }
                                }
                            }
                        }
                        return false;
                    """, fallback_texts)
                    if success:
                        time.sleep(1)
                        return
            except Exception:
                pass
            time.sleep(1)
        print(f"[{username}] ⚠️ Không thể click vào phần tử: {fallback_texts if fallback_texts else xpath}")
        raise Exception("Timeout click")

    max_retries = 3
    for attempt in range(max_retries):
        try:
            current_lang = driver.execute_script("return document.documentElement.lang;")
            #print(f"[{username}] [Lần {attempt + 1}/{max_retries}] Ngôn ngữ hiện tại của trang web: {current_lang}")
            
            if current_lang and current_lang.startswith("en"):
                wait_time = random.uniform(10, 30)
                #print(f"[{username}] Đợi {wait_time:.1f}s trước khi đổi ngôn ngữ để trang load hoàn toàn...")
                time.sleep(wait_time)
                #print(f"[{username}] Bắt đầu tiến trình đổi ngôn ngữ sang Tiếng Việt...")
                
                try:
                    # 1. Tìm nút Account / Your profile và click
                    do_click("//div[@role='button' and (contains(@aria-label, 'Your profile') or contains(@aria-label, 'Trang cá nhân của bạn') or contains(@aria-label, 'Account') or contains(@aria-label, 'Tài khoản'))]")
                    
                    # 2. Tìm và click Cài đặt
                    do_click("//span[contains(text(), 'Settings & privacy') or contains(text(), 'Cài đặt & quyền riêng tư') or text()='Cài đặt' or text()='Settings']", ["Settings & privacy", "Cài đặt & quyền riêng tư", "Cài đặt", "Settings"])
                    
                    # 3. Tìm và click Ngôn ngữ
                    do_click("//span[contains(text(), 'Language') or contains(text(), 'Ngôn ngữ')]", ["Language", "Ngôn ngữ"])
                    
                    # 4. Tìm và click Facebook Language
                    do_click("//span[contains(text(), 'Facebook Language') or contains(text(), 'Ngôn ngữ trên Facebook') or contains(text(), 'Ngôn ngữ của Facebook')]", ["Facebook Language", "Ngôn ngữ trên Facebook", "Ngôn ngữ của Facebook"])
                    
                    # 5. Chọn Tiếng Việt
                    do_click("//span[text()='Tiếng Việt' or contains(text(), 'Tiếng Việt')]", ["Tiếng Việt"])
                    
                    #print(f"[{username}] Đang đợi trang web tải lại (tối đa 30s) để xác nhận...")
                    try:
                        WebDriverWait(driver, 30).until(
                            lambda d: d.execute_script("return document.documentElement.lang;") and d.execute_script("return document.documentElement.lang;").startswith("vi")
                        )
                        print(f"[{username}] Đổi ngôn ngữ thành công!")
                        return True
                    except Exception:
                        final_lang = driver.execute_script("return document.documentElement.lang;")
                        if final_lang and final_lang.startswith("vi"):
                            print(f"[{username}] Đổi ngôn ngữ thành công!")
                            return True
                        else:
                            print(f"[{username}] ⚠️ Hết 30s chờ nhưng ngôn ngữ vẫn là {final_lang}.")
                            raise Exception("Không thể xác nhận ngôn ngữ đổi thành công.")
                            
                except Exception as inner_e:
                    print(f"[{username}] ⚠️ Lỗi trong tiến trình đổi ngôn ngữ: {inner_e}")
                    if attempt < max_retries - 1:
                        print(f"[{username}] Đang F5 (refresh) lại trang và thử lại...")
                        driver.refresh()
                        time.sleep(30)
                        continue
                    else:
                        print(f"[{username}] ❌ Đã thử {max_retries} lần nhưng không đổi được ngôn ngữ.")
                        return False
                        
            elif current_lang and current_lang.startswith("vi"):
                #print(f"[{username}] Trang web đã là Tiếng Việt, không cần đổi.")
                return True
            else:
                print(f"[{username}] Ngôn ngữ không phải tiếng Anh ({current_lang}), bỏ qua bước đổi.")
                return True
                
        except Exception as ex:
            print(f"[{username}] ⚠️ Lỗi khi thao tác đổi ngôn ngữ (Lần {attempt+1}): {ex}")
            if attempt < max_retries - 1:
                print(f"[{username}] Đang F5 (refresh) lại trang và thử lại...")
                driver.refresh()
                time.sleep(30)
            else:
                print(f"[{username}] ❌ Thất bại hoàn toàn sau {max_retries} lần thử.")
                return False

