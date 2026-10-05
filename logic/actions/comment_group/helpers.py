# -*- coding: utf-8 -*-
import time
import random
import string
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys


def generate_auto_comment():
    length = random.randint(5, 10)
    chars = ''.join(random.choices(string.ascii_lowercase, k=length)).capitalize()
    icons = ["👍", "❤️", "🥰", "😍", "🎉", "🔥", "✨", "💯", "😊", "😁", "⭐", "🍀", "🌸", "💐", "🎀", "💖", "💗"]
    return f"{chars} {random.choice(icons)}"

def close_obstructing_modals(driver, uid):
    try:
        current_url = driver.current_url
        if "/posts/" in current_url or "/permalink/" in current_url:
            print(f"[{uid}] 🔍 URL đang dạng Post, chờ nút Đóng tối đa 30s...")
            for wait_sec in range(30):
                # Lấy tất cả nút Đóng, không giới hạn SVG để bao phủ tất cả các dạng modal
                close_btns = driver.find_elements(By.XPATH, "//div[(@aria-label='Đóng' or @aria-label='Close' or @aria-label='Thoát') and @role='button']")
                if close_btns:
                    for i, btn in enumerate(close_btns):
                        # Kích hoạt sự kiện chuột cấp thấp (vượt qua mọi lớp chặn của React/Facebook)
                        try:
                            script = "arguments[0].dispatchEvent(new MouseEvent('click', {view: window, bubbles: true, cancelable: true}));"
                            driver.execute_script(script, btn)
                        except: pass
                        
                        # JS click thông thường
                        try:
                            driver.execute_script("arguments[0].click();", btn)
                        except: pass
                        
                        # Native click
                        try:
                            if btn.is_displayed():
                                btn.click()
                        except: pass
                        
                    print(f"[{uid}] ✅ Đã tìm thấy và click nút Đóng modal bài viết.")
                    time.sleep(1)
                    break
                else:
                    time.sleep(1)
        else:
            # Nếu url là dạng feed trang chủ group thì bỏ qua không cần check nút Đóng
            pass
    except Exception as e:
        print(f"[{uid}] Lỗi đóng modal: {e}")

def check_comment_status_after_post(driver, uid, is_edit_comment="no"):
    """
    Kiểm tra sau khi gửi comment:
    - Modal chặn tính năng (Feature Block)
    - Modal Xem xét quyền tham gia (Membership)
    - Comment bị từ chối / chờ duyệt (dựa vào nút Chỉnh sửa)
    Return: "BLOCK_MODAL_DETECTED" | "MEMBERSHIP_MODAL" | "BLOCK_EDIT_DETECTED" | "OK"
    """
    # 1. Feature Block Modal
    try:
        block_modal_selectors = [
            "//*[contains(text(), 'Giờ bạn chưa dùng được tính năng này')]",
            "//*[contains(text(), 'chưa dùng được tính năng này')]",
            "//*[contains(text(), 'giới hạn tần suất bạn đăng bài')]"
        ]
        for sel in block_modal_selectors:
            if driver.find_elements(By.XPATH, sel):
                print(f"[{uid}] ⚠️ Phát hiện modal chặn tính năng của Facebook!")
                try:
                    ok_btns = driver.find_elements(By.XPATH, "//div[@role='button']//span[text()='OK']")
                    if ok_btns:
                        ok_btns[0].click()
                        time.sleep(2)
                except: pass
                return "BLOCK_MODAL_DETECTED"
    except Exception as e:
        print(f"[{uid}] ⚠️ Lỗi khi check modal chặn tính năng: {e}")

    # 2. Membership Modal (Xem xét quyền tham gia)
    try:
        membership_selectors = [
            "//div[@aria-label='Xem xét quyền tham gia']",
            "//*[contains(text(), 'Xem xét quyền tham gia')]"
        ]
        for sel in membership_selectors:
            if driver.find_elements(By.XPATH, sel):
                textareas = driver.find_elements(By.TAG_NAME, "textarea")
                for ta in textareas:
                    try:
                        if ta.is_displayed():
                            ta.send_keys("ok")
                            time.sleep(random.uniform(1, 2))
                    except: pass
                submit_btns = driver.find_elements(By.XPATH, "//div[@aria-label='Gửi' and @role='button']")
                if submit_btns:
                    submit_btns[0].click()
                    time.sleep(3)
                return "MEMBERSHIP_MODAL"
    except Exception as e:
        print(f"[{uid}] ⚠️ Lỗi khi xử lý modal thành viên: {e}")

    # 3. Kiểm tra nút Chỉnh sửa (comment được duyệt hay bị từ chối)
    try:
        menu_xpath = "//div[@aria-label='Chỉnh sửa hoặc xóa bình luận này' or @aria-label='Edit or delete this comment' or @aria-label='Edit or delete this']"
        menu_btns = []
        timeout = 60
        start_time = time.time()
        while time.time() - start_time < timeout:
            menu_btns = driver.find_elements(By.XPATH, menu_xpath)
            if menu_btns:
                break
            time.sleep(2)

        if menu_btns:
            menu_btn = menu_btns[-1]
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", menu_btn)
            time.sleep(1)
            
            edit_opts = []
            for attempt in range(3):
                try:
                    ActionChains(driver).move_to_element(menu_btn).perform()
                    time.sleep(1)
                    menu_btn.click()
                except Exception as click_err:
                    print(f"[{uid}] ⚠️ Lỗi click bình thường, dùng js click: {click_err}")
                    driver.execute_script("arguments[0].click();", menu_btn)
                
                time.sleep(2)
                edit_opts = driver.find_elements(By.XPATH, "//span[contains(text(), 'Chỉnh sửa') or contains(text(), 'Edit')]")
                if edit_opts:
                    break
                print(f"[{uid}] ⚠️ Chưa thấy tùy chọn 'Chỉnh sửa' (thử lại {attempt + 1}/3)...")
                time.sleep(2)
                
            if not edit_opts:
                print(f"[{uid}] ❌ [DEBUG] Không có tùy chọn 'Chỉnh sửa' sau 3 lần click. Comment có thể đã bị từ chối hoặc đang chờ duyệt.")
                return "BLOCK_EDIT_DETECTED"
            else:
                if is_edit_comment == "yes":
                    print(f"[{uid}] 🔄 [DEBUG] Đã tìm thấy nút Chỉnh sửa. Đang click...")
                    try:
                        edit_opts[0].click()
                        print(f"[{uid}] ✅ [DEBUG] Đã click nút Chỉnh sửa thành công (Native click).")
                    except Exception as e_click:
                        print(f"[{uid}] ⚠️ [DEBUG] Lỗi Native click Chỉnh sửa: {e_click}, thử lại bằng JS...")
                        driver.execute_script("arguments[0].click();", edit_opts[0])
                        print(f"[{uid}] ✅ [DEBUG] Đã click nút Chỉnh sửa thành công (JS click).")
                    
                    time.sleep(3)
                else:
                    print(f"[{uid}] 🔄 [DEBUG] Không bật chế độ sửa comment, nhấn ESCAPE để đóng menu...")
                    ActionChains(driver).send_keys(Keys.ESCAPE).perform()
                    time.sleep(1)
        else:
            print(f"[{uid}] ⚠️ Không tìm thấy nút menu của comment sau {timeout}s. Có thể đã bị từ chối/chờ duyệt.")
            return "BLOCK_EDIT_DETECTED"
    except Exception as e:
        print(f"[{uid}] ⚠️ Lỗi khi kiểm tra nút Chỉnh sửa: {e}")
        return "BLOCK_EDIT_DETECTED"

    return "OK"
