# -*- coding: utf-8 -*-
import time
import re
import os
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from utils.file_utils import read_file
from utils.waiter import wait_for_element_with_retry
from utils.locks import FILE_LOCK
from utils.helpers import (
    type_human_like,
    is_logged_out
)
from actions.utils.like_actions import random_like_post
from actions.join_groups import join_single_group

import string
from .helpers import generate_auto_comment, close_obstructing_modals, check_comment_status_after_post
from .post_parser import extract_post_info











def process_group_cycle(driver, uid, group_id, is_edit_comment="yes", task_config=None, comment_index=0):
    if is_logged_out(driver):
        print(f"[{uid}] ⚠️ Phát hiện tài khoản đã bị đăng xuất!")
        return "LOGGED_OUT"

    try:
        # Xử lý nếu group_id đã là full URL (ví dụ https://www.facebook.com/groups/xxxx/)
        if group_id.startswith("http"):
            # Chuẩn hóa URL để lấy link gốc của group
            m = re.match(r"(https?://(?:www\.|m\.)?facebook\.com/groups/[^/]+)/?", group_id)
            if m:
                base_url = m.group(1).rstrip("/") + "/"
            else:
                base_url = group_id.split("?")[0].rstrip("/") + "/"
            g_id = base_url.rstrip("/").split("/")[-1]
        else:
            base_url = f"https://www.facebook.com/groups/{group_id}/"
            g_id = group_id

        target_url = f"{base_url}?sorting_setting=CHRONOLOGICAL"

        # Truy cập danh sách nhóm đã tham gia
        joins_url = "https://www.facebook.com/groups/joins/?nav_source=tab"
        
        # Chuyển hướng bằng DOM click để an toàn và giống người thật hơn
        script_joins = f"""
            var a = document.createElement('a');
            a.href = '{joins_url}';
            document.body.appendChild(a);
            a.click();
        """
        driver.execute_script(script_joins)
        time.sleep(5)
        
        group_clicked = False
        for _ in range(4): # Cuộn vài lần để load thêm nhóm
            try:
                group_links = driver.find_elements(By.XPATH, f"//a[contains(@href, '/groups/{g_id}')]")
                for glnk in group_links:
                    if glnk.is_displayed():
                        # Kiểm tra trạng thái chờ duyệt trên giao diện danh sách
                        try:
                            list_item = glnk.find_element(By.XPATH, "./ancestor::div[@role='listitem']")
                            item_text = list_item.text.lower()
                            if "đã yêu cầu" in item_text or "đang chờ" in item_text or "requested" in item_text or "pending" in item_text:
                                print(f"[{uid}] ⏳ Nhóm {g_id} đang ở trạng thái chờ duyệt. Bỏ qua.")
                                continue # Bỏ qua không click link này
                        except:
                            pass
                            
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", glnk)
                        time.sleep(1)
                        glnk.click()
                        group_clicked = True
                        break
                if group_clicked:
                    break
            except:
                pass
            driver.execute_script("window.scrollBy(0, 1000);")
            time.sleep(2)
            
        if not group_clicked:
            print(f"[{uid}] ⚠️ Nhóm {g_id} không nằm trong danh sách đã tham gia. Bỏ qua và lấy ID kế tiếp.")
            return "NOT_JOINED"
        else:
            time.sleep(4)
            if "sorting_setting=CHRONOLOGICAL" not in driver.current_url:
                # Đảm bảo vào chế độ bài viết mới nhất
                script_target = f"""
                    var a = document.createElement('a');
                    a.href = '{target_url}';
                    document.body.appendChild(a);
                    a.click();
                """
                driver.execute_script(script_target)
                time.sleep(4)
        
        current_url = driver.current_url
        if f"facebook.com/{g_id}" in current_url and "/groups/" not in current_url:
            print(f"[{uid}] 🚫 Nhóm {g_id} bị chặn hoặc không khả dụng (URL: {current_url}). Bỏ qua ID này.")
            return False

        # Kiểm tra xem có phải nhóm riêng tư hoặc đang chờ duyệt
        is_private = False
        try:
            private_xpaths = [
                "//*[contains(text(), 'Hủy yêu cầu')]",
                "//*[contains(text(), 'Đã yêu cầu')]",
                "//*[contains(text(), 'Yêu cầu đang chờ')]",
                "//*[contains(text(), 'Đã gửi yêu cầu')]",
                "//*[contains(text(), 'Pending')]",
                "//*[contains(text(), 'Cancel request')]",
                "//*[contains(text(), 'Request sent')]"
            ]
            for xpath in private_xpaths:
                elements = driver.find_elements(By.XPATH, xpath)
                for el in elements:
                    if el.is_displayed():
                        is_private = True
                        break
                if is_private:
                    break
        except Exception:
            pass
            
        if is_private:
            print(f"[{uid}] 🔒 Nhóm {g_id} là nhóm riêng tư hoặc yêu cầu đang chờ duyệt. Bỏ qua comment.")
            return "PRIVATE_GROUP"

        # Đợi modal (nếu có) xuất hiện, thử nhiều lần trong 8 giây
        modal_closed = False
        for _ in range(4): # Thử 4 lần, mỗi lần chờ 2 giây
            time.sleep(2)
            try:
                close_modal_xpath = "//div[@role='dialog']//div[(@aria-label='Đóng' or @aria-label='Close') and @role='button']"
                close_btns = driver.find_elements(By.XPATH, close_modal_xpath)
                for btn in close_btns:
                    try:
                        script = "arguments[0].dispatchEvent(new MouseEvent('click', {view: window, bubbles: true, cancelable: true}));"
                        driver.execute_script(script, btn)
                    except: pass
                    try:
                        driver.execute_script("arguments[0].click();", btn)
                    except: pass
                    modal_closed = True
                    time.sleep(1)
                    break
                if modal_closed:
                    break
            except Exception:
                pass
        
        # 1. Đợi feed hiện (nhiều lớp bảo vệ)
        feed_selectors = ["div[role='feed']", "div[data-pagelet^='FeedUnit']", "div[aria-label='Nội dung nhúm']", "div[aria-label='Feed of Group']"]
        feed_found = False
        for selector in feed_selectors:
            try:
                WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                feed_found = True
                break
            except: continue
        

        collected_links = set()

        # 2. Scan & Scroll loop
        is_first_post_evaluated = True
        
        # --- START DIRECT MODE ---
        if True:
            is_image_comment = False
            is_image_comment_with_text = False
            images_dir = "resources/images"
            if task_config:
                if task_config.get("IsImageComment"):
                    is_image_comment = True
                    images_dir = task_config.get("ImageFolderPath") or "resources/images"
                    is_image_comment_with_text = task_config.get("IsImageCommentWithText", False)
                    is_image_comment_auto_generate = task_config.get("IsImageCommentAutoGenerate", False)
                else:
                    image_group_uids = task_config.get("ImageGroupUids", [])
                    if image_group_uids:
                        is_image_comment = any(item in group_id or item in target_url for item in image_group_uids)
                        
                        # Ưu tiên nội dung comment riêng (nếu có)
                        custom_comments = task_config.get("CustomGroupCommentsList", [])
                        if custom_comments and any((c.get("GroupId") == group_id or c.get("GroupId") in target_url) for c in custom_comments):
                            is_image_comment = False
                            
                        if is_image_comment:
                            print(f"[{uid}] 🖼️ PHÁT HIỆN GROUP ƯU TIÊN ẢNH (Text Mode)! Sử dụng chế độ comment bằng ảnh.")
                            images_dir = task_config.get("ImageFolderPath") or "resources/images"
            for attempt in range(2):
                if attempt > 0:
                    driver.refresh()
                    time.sleep(10)
                
                comment_box_found = False
                is_permalink_fallback = False
                
                # Hàm kiểm tra thời gian
                def is_valid_time(pt):
                    pt_lower = pt.lower()
                    invalid_keywords = ["ngày", "tháng", "năm", "day", "month", "year", "tuần", "week"]
                    for kw in invalid_keywords:
                        if kw in pt_lower:
                            return False
                    valid_keywords = ["giây", "phút", "giờ", "second", "minute", "hour", "vừa xong", "just now"]
                    for kw in valid_keywords:
                        if kw in pt_lower:
                            return True
                    return False
                    
                # Load lịch sử post đã comment
                history_file = "resources/commented_post_ids.txt"
                commented_posts = []
                try:
                    with FILE_LOCK:
                        if os.path.exists(history_file):
                            with open(history_file, 'r', encoding='utf-8') as f:
                                commented_posts = f.read().splitlines()
                except: pass

                for scan_idx in range(10): # Tối đa 10 lần cuộn
                    try:
                        comment_boxes = driver.find_elements(By.XPATH, "//div[@role='textbox' and @contenteditable='true' and not(@data-commented='true')]")
                        box_to_comment = None
                        
                        for box in comment_boxes:
                            if box.is_displayed():
                                aria_label = box.get_attribute("aria-label") or ""
                                if "viết gì đó" in aria_label.lower() or "write something" in aria_label.lower() or "tạo bài viết" in aria_label.lower() or "create a public post" in aria_label.lower():
                                    continue
                                box_to_comment = box
                                break
                        
                        if not box_to_comment:
                            comment_btns = driver.find_elements(By.XPATH, "//div[@role='button' and (@aria-label='Bình luận' or @aria-label='Comment' or @aria-label='Viết bình luận' or @aria-label='Write a comment' or @aria-label='Để lại bình luận' or @aria-label='Leave a comment') and not(@data-scanned='true')]")
                            for btn in comment_btns:
                                if btn.is_displayed():
                                    try:
                                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                                        time.sleep(1)
                                    except: pass
                                    driver.execute_script("arguments[0].setAttribute('data-scanned', 'true')", btn)
                                    driver.execute_script("arguments[0].click();", btn)
                                    time.sleep(2)
                                    break
                                    
                            comment_boxes = driver.find_elements(By.XPATH, "//div[@role='textbox' and @contenteditable='true' and not(@data-commented='true')]")
                            for box in comment_boxes:
                                if box.is_displayed():
                                    aria_label = box.get_attribute("aria-label") or ""
                                    if "viết gì đó" in aria_label.lower() or "write something" in aria_label.lower() or "tạo bài viết" in aria_label.lower() or "create a public post" in aria_label.lower():
                                        continue
                                    box_to_comment = box
                                    break

                        if box_to_comment:
                            driver.execute_script("arguments[0].setAttribute('data-commented', 'true')", box_to_comment)
                            
                            # Lấy link bài viết và thời gian
                            post_time, post_id, real_post_link = extract_post_info(driver, uid, box_to_comment)
                            print(f"[{uid}] 🕒 Thời gian đăng: {post_time} | ID: {post_id}")
                            
                            if not is_valid_time(post_time):
                                print(f"[{uid}] ⏭️ Bỏ qua vì thời gian ({post_time}) không thỏa mãn (chứa ngày/tháng/năm).")
                                
                                if post_time == "Không xác định":
                                    # 1. Đóng modal nếu có
                                    close_obstructing_modals(driver, uid)
                                    
                                    # 2. Kiểm tra xem có bị văng ra trang chủ không
                                    curr_url = driver.current_url
                                    if curr_url.rstrip("/") in ["https://www.facebook.com", "https://m.facebook.com"]:
                                        print(f"[{uid}] ⚠️ Bị văng ra trang chủ, truy cập lại URL group...")
                                        driver.get(target_url)
                                        time.sleep(5)
                                        continue
                                    
                                    # 3. Kiểm tra xem có đúng định dạng URL bài viết mới nhất không
                                    elif "sorting_setting=CHRONOLOGICAL" not in curr_url:
                                        print(f"[{uid}] ⚠️ URL hiện tại không phải dạng bài viết mới nhất, điều hướng lại...")
                                        driver.get(target_url)
                                        time.sleep(5)
                                        continue
                                
                                driver.execute_script("window.scrollBy(0, 400);")
                                time.sleep(2)
                                continue
                                
                            if post_id and post_id in commented_posts:
                                print(f"[{uid}] ⏭️ Bỏ qua vì post_id {post_id} đã được comment trước đó.")
                                driver.execute_script("window.scrollBy(0, 400);")
                                time.sleep(2)
                                continue
                                
                            # OK, thực hiện comment
                            delay1 = random.randint(1, 10)
                            time.sleep(delay1)
                            
                            close_obstructing_modals(driver, uid)
                            random_like_post(driver, uid)
                            
                            delay2 = random.randint(3, 5)
                            time.sleep(delay2)
                            
                            # Kiểm tra URL xem có bị văng ra trang chủ không
                            current_url_check = driver.current_url.strip().rstrip('/')
                            if current_url_check in ("https://www.facebook.com", "https://facebook.com"):
                                print(f"[{uid}] ⚠️ Bị văng ra trang chủ, tiến hành vào lại group {g_id} và lặp lại logic...")
                                driver.get(target_url)
                                time.sleep(5)
                                break  # Thoát vòng lặp tìm bài viết (scan_idx) để bắt đầu attempt mới
                                

                            comment_input = box_to_comment
                                
                            try:
                                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", comment_input)
                                time.sleep(1)
                                driver.execute_script("window.scrollBy(0, 100);")
                                time.sleep(1)
                            except:
                                pass
                            
                            target_edit_content = "Check inbox nhé"
                            if task_config:
                                custom_comments = task_config.get("CustomGroupCommentsList", [])
                                matched_custom_content = None
                                for c_item in custom_comments:
                                    if c_item.get("GroupId") == group_id or c_item.get("GroupId") in current_url:
                                        matched_custom_content = c_item.get("Content", "")
                                        break
                                
                                if matched_custom_content:
                                    target_edit_content = matched_custom_content
                                    # Vô hiệu hóa auto generate nếu nhóm này có nội dung riêng
                                    if task_config.get("IsImageCommentAutoGenerate"):
                                        is_image_comment_auto_generate = False
                                        is_image_comment_with_text = True
                                else:
                                    comment_list = task_config.get("CommentsList", [])
                                    if comment_list:
                                        if task_config.get("IsSequentialComment"):
                                            idx = comment_index % len(comment_list)
                                            target_edit_content = comment_list[idx]
                                        else:
                                            target_edit_content = random.choice(comment_list)

                                if task_config.get("IsImageCommentAutoGenerate", False) and not matched_custom_content:
                                    content = generate_auto_comment()
                                else:
                                    if is_edit_comment == "yes":
                                        with FILE_LOCK:
                                            stt_lines = read_file("resources/stt.txt")
                                        content = random.choice(stt_lines) if stt_lines else "Up bài giúp b nhé"
                                    else:
                                        content = target_edit_content
                            time.sleep(random.uniform(2, 5))
                            
                            current_url = driver.current_url
                            if "/permalink/" in current_url or "/posts/" in current_url or "story_fbid=" in current_url:
                                collected_links.add(current_url)
                                is_permalink_fallback = True
                                break
                            
                            if is_image_comment:
                                driver.execute_script("arguments[0].click(); arguments[0].focus();", comment_input)
                                time.sleep(2)
                                
                                if (is_image_comment_with_text or task_config.get("IsImageCommentAutoGenerate", False) or is_edit_comment == "yes") and content:
                                    type_human_like(driver, content, element=comment_input)
                                    time.sleep(2)
                                
                                image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp')
                                available_images = []
                                if os.path.exists(images_dir):
                                    available_images = [os.path.abspath(os.path.join(images_dir, img_f)) for img_f in os.listdir(images_dir) if img_f.lower().endswith(image_extensions)]
                                if not available_images:
                                    print(f"[{uid}] ❌ Không có ảnh. Bỏ qua.")
                                    return False
                                chosen_image = random.choice(available_images)
                                
                                file_input = None
                                
                                try:
                                    parent_form = comment_input.find_element(By.XPATH, "./ancestor::form")
                                    if parent_form:
                                        els = parent_form.find_elements(By.XPATH, ".//input[@type='file']")
                                        if els: file_input = els[0]
                                except: pass
                                    
                                if not file_input:
                                    try:
                                        attach_btn = driver.find_element(By.XPATH, "//div[@aria-label='Đính kèm một ảnh hoặc video' or @aria-label='Attach a photo or video']/ancestor::li//input[@type='file']")
                                        file_input = attach_btn
                                    except: pass
                                if not file_input:
                                    try:
                                        els = driver.find_elements(By.CSS_SELECTOR, "#focused-state-actions-list input[type='file']")
                                        if els: file_input = els[0]
                                    except: pass
                                if not file_input:
                                    try:
                                        els = driver.find_elements(By.CSS_SELECTOR, "form[role='presentation'] input[type='file']")
                                        if els: file_input = els[0]
                                    except: pass
                                
                                if file_input:
                                    file_input.send_keys(chosen_image)
                                    submitted = False
                                    start_wait = time.time()
                                    while time.time() - start_wait < 30:
                                        for submit_xpath in [
                                            "//div[@id='focused-state-composer-submit']//div[@role='button' and not(@aria-disabled='true')]",
                                            "//div[@aria-label='Đăng bình luận' and @role='button' and not(@aria-disabled='true')]",
                                            "//div[@aria-label='Post comment' and @role='button' and not(@aria-disabled='true')]",
                                        ]:
                                            try:
                                                btn = driver.find_element(By.XPATH, submit_xpath)
                                                if btn.is_displayed():
                                                    btn.click()
                                                    submitted = True
                                                    break
                                            except: continue
                                        if submitted: break
                                        time.sleep(1)
                                    if not submitted:
                                        ActionChains(driver).send_keys(Keys.ENTER).perform()
                                    time.sleep(15)
                                else:
                                    print(f"[{uid}] ❌ Không tìm thấy input ảnh.")
                                    return False
                            else:
                                driver.execute_script("arguments[0].click(); arguments[0].focus();", comment_input)
                                time.sleep(1)
                                type_human_like(driver, content, element=None)
                                time.sleep(1)
                                
                                submitted = False
                                for submit_xpath in [
                                    "//div[@id='focused-state-composer-submit']//div[@role='button']",
                                    "//div[@aria-label='Đăng bình luận' and @role='button']",
                                    "//div[@aria-label='Post comment' and @role='button']",
                                ]:
                                    try:
                                        btns = driver.find_elements(By.XPATH, submit_xpath)
                                        for btn in btns:
                                            if btn.is_displayed():
                                                try:
                                                    driver.execute_script("arguments[0].click();", btn)
                                                except:
                                                    btn.click()
                                                submitted = True
                                                break
                                    except: pass
                                    if submitted: break
                                    
                                if not submitted:
                                    ActionChains(driver).send_keys(Keys.ENTER).perform()
                                time.sleep(5)
                            
                            # ===== KIỂM TRA BỊ CHẶN / CHỜ DUYỆT =====
                            _status = check_comment_status_after_post(driver, uid)
                            is_success = True
                            if _status in ("BLOCK_MODAL_DETECTED", "BLOCK_EDIT_DETECTED", "MEMBERSHIP_MODAL"):
                                is_success = False
                            
                            if is_edit_comment == "yes" and is_success:
                                try:
                                    safe_search_text = content.split('\n')[0].strip()[:30]
                                    if not safe_search_text: safe_search_text = "Check inbox nhé"
                                    comment_text_xpath = f"//*[contains(text(), '{safe_search_text}')]"
                                    posted_comment = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, comment_text_xpath)))
                                    
                                    actions = ActionChains(driver)
                                    actions.move_to_element(posted_comment).perform()
                                    time.sleep(1)
                                    
                                    menu_xpath = "//div[@aria-label='Chỉnh sửa hoặc xóa bình luận này' or @aria-label='Edit or delete this comment']"
                                    menu_btn = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, menu_xpath)))
                                    menu_btn.click()
                                    time.sleep(2)
                                    
                                    edit_xpath = "//span[contains(text(), 'Chỉnh sửa') or contains(text(), 'Edit')]"
                                    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, edit_xpath))).click()
                                    time.sleep(3)
                                    
                                    box = driver.switch_to.active_element
                                    box.send_keys(Keys.CONTROL, "a")
                                    box.send_keys(Keys.BACKSPACE)
                                    time.sleep(1)
                                    
                                    new_content = "Check inbox nhé"
                                    if task_config:
                                        new_content = target_edit_content
                                    
                                    type_human_like(driver, new_content, element=box)
                                    time.sleep(1)
                                    box.send_keys(Keys.ENTER)
                                    print(f"[{uid}] ✅ Đã sửa comment thành công.")
                                    time.sleep(3)
                                except Exception as e_edit:
                                    print(f"[{uid}] ⚠️ Lỗi quy trình sửa comment: {e_edit}")
                                    is_success = False

                            # Chỉ lưu vào lịch sử nếu thao tác comment hoàn tất thành công và không bị pending/block
                            if is_success and post_id:
                                with FILE_LOCK:
                                    # Tạo thư mục nếu chưa có
                                    os.makedirs(os.path.dirname(history_file), exist_ok=True)
                                    with open(history_file, 'a', encoding='utf-8') as f:
                                        f.write(post_id + "\n")
                                print(f"[{uid}] ✅ Đã lưu post_id {post_id} vào lịch sử.")

                            if _status in ("BLOCK_MODAL_DETECTED", "BLOCK_EDIT_DETECTED"): return _status
                            if _status == "MEMBERSHIP_MODAL": return "MEMBERSHIP_MODAL"

                            comment_box_found = True
                            break
                    except Exception as e:
                        pass
                        
                    # Cuộn tiếp nếu chưa thấy ô comment hoặc đã bỏ qua bài viết
                    driver.execute_script("window.scrollBy(0, 400);")
                    time.sleep(2)
                
                if comment_box_found or is_permalink_fallback:
                    break
            
            if comment_box_found:
                return True
            if not is_permalink_fallback:
                print(f"[{uid}] ⚠️ Không tìm thấy ô comment nào trực tiếp trong nhóm này.")
                return False
        # --- END DIRECT MODE ---

        # Xác định chế độ comment ảnh (Image Group logic)
        is_image_comment = False
        is_image_comment_with_text = False
        images_dir = "resources/images"
        if task_config:
            if task_config.get("IsImageComment"):
                is_image_comment = True
                images_dir = task_config.get("ImageFolderPath") or "resources/images"
                is_image_comment_with_text = task_config.get("IsImageCommentWithText", False)
            else:
                image_group_uids = task_config.get("ImageGroupUids", [])
                if image_group_uids:
                    is_image_comment = any(item in group_id or item in target_url for item in image_group_uids)
                    
                    custom_comments = task_config.get("CustomGroupCommentsList", [])
                    if custom_comments and any((c.get("GroupId") == group_id or c.get("GroupId") in target_url) for c in custom_comments):
                        is_image_comment = False
                        
                    if is_image_comment:
                        print(f"[{uid}] 🖼️ PHÁT HIỆN GROUP ƯU TIÊN ẢNH! Sử dụng chế độ comment bằng ảnh.")
                        images_dir = task_config.get("ImageFolderPath") or "resources/images"

        # Comment logic
        post_url = list(collected_links)[0]
        driver.get(post_url)
        time.sleep(5)
        
        # 3. Lấy nội dung comment
        if task_config:
            if task_config.get("IsImageCommentAutoGenerate", False):
                content = generate_auto_comment()
            else:
                comment_list = task_config.get("CommentsList", [])
                if comment_list:
                    if task_config.get("IsSequentialComment"):
                        idx = comment_index % len(comment_list)
                        content = comment_list[idx]
                    else:
                        content = random.choice(comment_list)
                else:
                    content = "Check inbox nhé"



        textbox_xpath = '//div[@role="textbox"]'
        comment_input = wait_for_element_with_retry(driver, By.XPATH, textbox_xpath, timeout=15)
        if comment_input:
            delay1 = random.randint(1, 10)
            time.sleep(delay1)
            
            close_obstructing_modals(driver, uid)
            random_like_post(driver, uid)
            
            delay2 = random.randint(3, 5)
            time.sleep(delay2)
            
            time.sleep(random.uniform(5, 10))
            
            # Cuộn trang xuống giữa màn hình và thêm 100px để tránh che khuất footer
            try:
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", comment_input)
                time.sleep(1)
                driver.execute_script("window.scrollBy(0, 100);")
                time.sleep(1)
            except:
                pass

            if is_image_comment:
                # === CHẾ ĐỘ COMMENT ẢNH ===
                if (is_image_comment_with_text or task_config.get("IsImageCommentAutoGenerate", False) or is_edit_comment == "yes") and content:
                    driver.execute_script("arguments[0].focus();", comment_input)
                    time.sleep(1)
                    type_human_like(driver, content, element=comment_input)
                    time.sleep(2)
                    
                # Bỏ qua hoàn toàn việc click, vì Selenium có thể tương tác trực tiếp với input type=file
                pass

                # images_dir đã được lấy ở trên
                image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp')
                available_images = []
                if os.path.exists(images_dir):
                    available_images = [
                        os.path.abspath(os.path.join(images_dir, img_f))
                        for img_f in os.listdir(images_dir)
                        if img_f.lower().endswith(image_extensions)
                    ]

                if not available_images:
                    print(f"[{uid}] ❌ Không có ảnh nào trong thư mục '{images_dir}'. Bỏ qua group này.")
                    return False

                chosen_image = random.choice(available_images)
                print(f"[{uid}] 🖼️ Chọn ảnh: {os.path.basename(chosen_image)}")

                # Tìm input[type="file"] đúng của comment bar (tránh nhầm input của ô tạo bài viết)
                # Ưu tiên tìm trong #focused-state-actions-list (div riêng của comment area)
                file_input = None

                # Cách 1: Tìm qua button "Đính kèm ảnh" → ancestor li → input (chính xác nhất)
                try:
                    attach_btn = driver.find_element(By.XPATH,
                        "//div[@aria-label='Đính kèm một ảnh hoặc video' or @aria-label='Attach a photo or video']/ancestor::li//input[@type='file']"
                    )
                    file_input = attach_btn
                except Exception:
                    pass

                # Cách 2: Tìm trong #focused-state-actions-list (comment toolbar)
                if not file_input:
                    try:
                        els = driver.find_elements(By.CSS_SELECTOR, "#focused-state-actions-list input[type='file']")
                        if els:
                            file_input = els[0]
                    except Exception:
                        pass

                # Cách 3: Tìm trong form comment (form[role='presentation'])
                if not file_input:
                    try:
                        els = driver.find_elements(By.CSS_SELECTOR, "form[role='presentation'] input[type='file']")
                        if els:
                            file_input = els[0]
                    except Exception:
                        pass

                if not file_input:
                    print(f"[{uid}] ❌ Không tìm thấy input file của comment để upload ảnh.")
                    return False

                file_input.send_keys(chosen_image)
                submitted = False
                start_wait = time.time()
                while time.time() - start_wait < 30:
                    for submit_xpath in [
                        "//div[@id='focused-state-composer-submit']//div[@role='button' and not(@aria-disabled='true')]",
                        "//div[@aria-label='Đăng bình luận' and @role='button' and not(@aria-disabled='true')]",
                        "//div[@aria-label='Post comment' and @role='button' and not(@aria-disabled='true')]",
                    ]:
                        try:
                            btn = driver.find_element(By.XPATH, submit_xpath)
                            if btn.is_displayed():
                                btn.click()
                                submitted = True
                                break
                        except: continue
                    if submitted:
                        break
                    time.sleep(1)

                if not submitted:
                    print(f"[{uid}] ⚠️ Không tìm thấy nút gửi, thử Enter fallback.")
                    ActionChains(driver).send_keys(Keys.ENTER).perform()

                time.sleep(15)
            else:
                # === CHẾ ĐỘ COMMENT TEXT (logic gốc) ===
                driver.execute_script("arguments[0].focus();", comment_input)
                time.sleep(1)
                time_human_start = time.time()
                type_human_like(driver, content, element=comment_input)

                # Gửi
                ActionChains(driver).send_keys_to_element(comment_input, Keys.ENTER).perform()
                print(f"[{uid}] ✅ Đã gửi comment (Gõ trong {int(time.time()-time_human_start)}s)")
                time.sleep(5)

            # ===== KIỂM TRA BỊ CHẶN / CHỜ DUYỆT (LINK MODE) =====
            _status = check_comment_status_after_post(driver, uid)
            if _status in ("BLOCK_MODAL_DETECTED", "BLOCK_EDIT_DETECTED"):
                return _status
            if _status == "MEMBERSHIP_MODAL":
                return "MEMBERSHIP_MODAL"
            # =================================================================

            # ================= START EDIT & RE-COMMENT =================
            if is_edit_comment == "yes":
                try:
                    print(f"[{uid}] 🔄 Đang bắt đầu quy trình Sửa & Re-comment (Bulk Content)...")
                    # 1. Tìm comment vừa đăng (theo nội dung vừa gõ)
                    safe_search_text = content.split('\n')[0].strip()[:30]
                    if not safe_search_text: safe_search_text = "Check inbox nhé"
                    comment_text_xpath = f"//*[contains(text(), '{safe_search_text}')]"
                    posted_comment = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, comment_text_xpath)))
                    
                    # Hover & Click Menu
                    actions = ActionChains(driver)
                    actions.move_to_element(posted_comment).perform()
                    time.sleep(1)
                    
                    menu_xpath = "//div[@aria-label='Chỉnh sửa hoặc xóa bình luận này' or @aria-label='Edit or delete this comment']"
                    menu_btn = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, menu_xpath)))
                    menu_btn.click()
                    time.sleep(2)
                    
                    # Click Chỉnh sửa
                    edit_xpath = "//span[contains(text(), 'Chỉnh sửa') or contains(text(), 'Edit')]"
                    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, edit_xpath))).click()
                    time.sleep(3)
                    
                    # Xóa cũ, nhập mới qua active_element
                    box = driver.switch_to.active_element
                    box.send_keys(Keys.CONTROL, "a")
                    box.send_keys(Keys.BACKSPACE)
                    time.sleep(1)
                    
                    # LẤY TOÀN BỘ NỘI DUNG FILE ĐÍCH Hoặc TỪ CONFIG
                    new_content = "Check inbox nhé" # Fallback
                    if task_config:
                        new_content = target_edit_content
                    
                    type_human_like(driver, new_content, element=box)
                    time.sleep(1)
                    box.send_keys(Keys.ENTER)
                    print(f"[{uid}] ✅ Đã sửa comment thành công.")
                    time.sleep(10)
                except Exception as e_edit:
                    print(f"[{uid}] ⚠️ Lỗi quy trình sửa comment: {e_edit}")
            else:
                print(f"[{uid}] ⏳ Đợi 10s trước khi kết thúc quá trình...")
                time.sleep(10)
            # ===========================================================
            return True # THÀNH CÔNG

    except Exception as e:
        print(f"[{uid}] ❌ Lỗi group cycle: {e}")
    return False # THẤT BẠI
