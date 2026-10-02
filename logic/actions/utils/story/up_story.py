import time
import os
import random
import json
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

STORY_HISTORY_FILE = "story_history.json"
STORY_COOLDOWN_DAYS = 2

def _get_history_path():
    return os.path.join(os.getcwd(), STORY_HISTORY_FILE)

def _load_history():
    path = _get_history_path()
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def _save_history(data: dict):
    path = _get_history_path()
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[StoryHistory] Lỗi lưu lịch sử: {e}")

def can_up_story(uid: str) -> tuple:
    history = _load_history()
    uid = str(uid)
    if uid not in history:
        return True, ""
    try:
        last_time = datetime.fromisoformat(history[uid])
    except Exception:
        return True, ""
        
    elapsed = datetime.now() - last_time
    days_ago = elapsed.total_seconds() / 86400
    if days_ago < STORY_COOLDOWN_DAYS:
        remaining = STORY_COOLDOWN_DAYS - days_ago
        return False, f"Đã up story cách đây {days_ago:.1f} ngày. Cần chờ thêm {remaining:.1f} ngày."
    return True, ""

def record_story(uid: str):
    history = _load_history()
    history[str(uid)] = datetime.now().isoformat()
    _save_history(history)


def up_story(driver, uid, image_path=None, image_folder=None):
    try:
        print(f"[{uid}] Đang tìm nút Tạo tin...")
        driver.get("https://www.facebook.com/")
        
        wait_60 = WebDriverWait(driver, 60)
        
        # Chờ nút Tạo tin hiện rõ trên màn hình
        create_story_btn = wait_60.until(EC.visibility_of_element_located((By.XPATH, "//a[contains(@href, '/stories/create')] | //a[@aria-label='Tạo tin' or @aria-label='Create Story']")))
        time.sleep(2) # Cho React nạp xong event
        driver.execute_script("arguments[0].click();", create_story_btn)
        print(f"[{uid}] Đã click vào nút Tạo tin thành công!")
        
        print(f"[{uid}] Chờ tải trang Tạo tin (tối đa 180s)...")
        wait_180 = WebDriverWait(driver, 180)
        wait_180.until(EC.url_contains("/stories/create"))
        
        print(f"[{uid}] Chờ giao diện load xong (tìm thẻ h1 'Tin của bạn')...")
        wait_180.until(EC.presence_of_element_located((By.XPATH, "//h1[text()='Tin của bạn' or text()='Your Story']")))
        
        print(f"[{uid}] Đang tìm nút Loại tin (Ảnh/Chữ)...")
        xpath_photo_story = "//div[@aria-label='Tạo tin có ảnh hoặc video' or contains(@aria-label, 'Photo Story') or contains(@aria-label, 'photo or video')]"
        story_type_btn = wait_180.until(EC.presence_of_element_located((By.XPATH, xpath_photo_story)))
        
        if not image_path:
            import glob
            # Lấy ngẫu nhiên ảnh trong thư mục img
            if image_folder and os.path.exists(image_folder):
                img_dir = image_folder
            else:
                img_dir = os.path.join(os.getcwd(), "resources", "images")
                
            if not os.path.exists(img_dir):
                print(f"[{uid}] Không tìm thấy thư mục ảnh {img_dir}. Bỏ qua up story.")
                return False
            images = glob.glob(os.path.join(img_dir, "*.[pj][pn]*"))
            if not images:
                print(f"[{uid}] Không tìm thấy ảnh trong {img_dir}. Bỏ qua up story.")
                return False
            image_path = random.choice(images)
            
        print(f"[{uid}] Dùng file ảnh: {image_path}")
        
        def handle_os_dialog(path):
            import time
            try:
                import pyautogui
                import pyperclip
                pyautogui.FAILSAFE = False
            except ImportError:
                print(f"[{uid}] THIẾU THƯ VIỆN: Chạy 'pip install pyautogui pyperclip'")
                return
            time.sleep(2)
            pyperclip.copy(path)
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(1)
            pyautogui.press('enter')
            
        import threading
        threading.Thread(target=handle_os_dialog, args=(image_path,), daemon=True).start()
        
        try:
            story_type_btn.click()
        except:
            driver.execute_script("arguments[0].click();", story_type_btn)
            
        print(f"[{uid}] Đã xử lý xong popup chọn file của OS!")
        
        print(f"[{uid}] Chờ giao diện chỉnh sửa và tìm nút 'Thêm nhạc'...")
        add_music_btn = wait_180.until(EC.presence_of_element_located((By.XPATH, "//span[contains(text(), 'Thêm nhạc') or contains(text(), 'Add Music')]")))
        time.sleep(2)
        
        try:
            add_music_btn.click()
        except:
            driver.execute_script("arguments[0].click();", add_music_btn)
            
        print(f"[{uid}] Chờ popup tìm nhạc xuất hiện...")
        search_music_input = wait_180.until(EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Tìm kiếm nhạc' or @placeholder='Search music' or @aria-label='Tìm kiếm nhạc']")))
        time.sleep(3)
        
        song_rows_xpath = "//div[@data-visualcompletion='ignore-dynamic']/div[@role='button']"
        song_rows = driver.find_elements(By.XPATH, song_rows_xpath)
        
        if song_rows:
            selected_song = random.choice(song_rows)
            try:
                selected_song.click()
            except:
                driver.execute_script("arguments[0].click();", selected_song)
            print(f"[{uid}] Đã chọn nhạc thành công!")
            
            try:
                done_btn = wait_60.until(EC.presence_of_element_located((By.XPATH, "//div[@aria-label='Xong' or @aria-label='Done']")))
                time.sleep(1)
                try:
                    done_btn.click()
                except:
                    driver.execute_script("arguments[0].click();", done_btn)
            except Exception:
                pass
                
            try:
                share_btn = wait_60.until(EC.presence_of_element_located((By.XPATH, "//div[@aria-label='Chia sẻ lên tin' or @aria-label='Share to Story'] | //span[text()='Chia sẻ lên tin' or text()='Share to Story']/ancestor::div[@role='button']")))
                time.sleep(1)
                try:
                    share_btn.click()
                except:
                    driver.execute_script("arguments[0].click();", share_btn)
                print(f"[{uid}] Đã ấn Chia sẻ lên tin thành công!")
            except Exception as ex:
                print(f"[{uid}] Không tìm thấy nút Chia sẻ: {ex}")
                
        return True
    except Exception as e:
        print(f"[{uid}] Lỗi khi up story: {e}")
        return False
