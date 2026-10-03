# -*- coding: utf-8 -*-
"""
content.py — Nhập nội dung văn bản vào ô soạn thảo bài đăng.
"""
import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains

def type_content(driver, uid, post_content=None):
    """Nhập nội dung bài viết vào textbox contenteditable."""
    content = post_content if post_content else f"Hôm nay thật tuyệt vời! {random.randint(1000, 9999)}"
    print(f"[Account-{uid}] Đang nhập nội dung bài viết: '{content}'")

    textbox_xpath = "//div[@role='textbox' and @contenteditable='true']"
    textboxes = driver.find_elements(By.XPATH, textbox_xpath)
    tb = next((t for t in textboxes if t.is_displayed()), None)

    if not tb:
        print(f"[Account-{uid}] Lỗi: Không tìm thấy ô nhập nội dung!")
        return

    try:
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", tb)
        time.sleep(0.5)
        ActionChains(driver).move_to_element(tb).click().perform()
        time.sleep(0.5)

        active_el = driver.switch_to.active_element
        for char in content:
            try:
                active_el.send_keys(char)
            except Exception as char_ex:
                if "BMP" in str(char_ex):
                    driver.execute_script("document.execCommand('insertText', false, arguments[0]);", char)
                else:
                    raise char_ex
            time.sleep(random.uniform(0.02, 0.1))
    except Exception as e:
        print(f"[Account-{uid}] Lỗi gõ ActionChains, thử fallback... ({e})")
        try:
            driver.execute_script("arguments[0].click();", tb)
            time.sleep(0.5)
            for char in content:
                try:
                    tb.send_keys(char)
                except Exception as char_ex:
                    if "BMP" in str(char_ex):
                        driver.execute_script("document.execCommand('insertText', false, arguments[0]);", char)
                    else:
                        raise char_ex
                time.sleep(random.uniform(0.02, 0.1))
        except Exception as e2:
            print(f"[Account-{uid}] Lỗi nhập nội dung fallback: {e2}")

    time.sleep(2)
