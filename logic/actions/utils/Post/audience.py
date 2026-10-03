# -*- coding: utf-8 -*-
"""
audience.py — Kiểm tra và đổi đối tượng bài viết sang Công khai.
"""
import time
import random
from selenium.webdriver.common.by import By
from .post_helper import do_click, REACT_CLICK_SCRIPT
from selenium.webdriver.common.action_chains import ActionChains

def ensure_public_audience(driver, uid):
    """
    Kiểm tra đối tượng hiện tại của bài đăng.
    Nếu chưa phải Công khai → mở modal → chọn Công khai → tick mặc định → click Xong.
    """
    print(f"[Account-{uid}] Kiểm tra đối tượng hiện tại của bài viết...")

    already_public = False
    try:
        ck_check_xpath = (
            "//div[@role='dialog']//div[@role='button'][.//span[normalize-space()='Công khai' or normalize-space()='Public']]"
            " | //div[@role='dialog']//div[contains(@class,'x1qhmfi1')][.//span[normalize-space()='Công khai' or normalize-space()='Public']]"
        )
        ck_check_els = driver.find_elements(By.XPATH, ck_check_xpath)
        if ck_check_els and any(el.is_displayed() for el in ck_check_els):
            already_public = True
            print(f"[Account-{uid}] ✅ Đã là 'Công khai', không cần thay đổi đối tượng.")
    except:
        pass

    if already_public:
        return

    print(f"[Account-{uid}] Đối tượng chưa phải Công khai, đang mở modal để thay đổi...")
    doi_tuong_xpath = (
        "//div[@role='dialog']//div[@role='button'][.//span[contains(text(), 'Bạn bè') or contains(text(), 'Friends')"
        " or contains(text(), 'Chỉ mình tôi') or contains(text(), 'Only me')"
        " or contains(text(), 'Bạn thân') or contains(text(), 'Close Friends')]]"
        " | //div[@role='dialog']//div[contains(@class,'x1qhmfi1')][.//span[contains(text(), 'Bạn bè') or contains(text(), 'Friends')]]"
    )
    doi_tuong_els = driver.find_elements(By.XPATH, doi_tuong_xpath)
    clicked_dt = False
    for el in doi_tuong_els:
        try:
            if el.is_displayed():
                driver.execute_script("arguments[0].scrollIntoView({behavior:'smooth', block:'center'});", el)
                time.sleep(random.uniform(1.2, 2.5))
                ActionChains(driver).move_to_element(el).perform()
                time.sleep(random.uniform(0.8, 1.8))
                driver.execute_script("arguments[0].click();", el)
                clicked_dt = True
                print(f"[Account-{uid}] Đã click nút đối tượng bài viết!")
                break
        except:
            pass
    if not clicked_dt:
        do_click(driver, uid, doi_tuong_xpath, ["bạn bè", "friends", "bạn thân", "chỉ mình tôi"])

    time.sleep(random.uniform(2.5, 5.0))

    # Chờ modal "Đối tượng của bài viết" xuất hiện
    print(f"[Account-{uid}] Đang chờ modal 'Đối tượng của bài viết' (tối đa 60s)...")
    modal_appeared = False
    end_modal = time.time() + 60
    while time.time() < end_modal:
        try:
            modal_title = driver.find_elements(By.XPATH,
                "//h2[.//span[contains(text(), 'Đối tượng của bài viết') or contains(text(), 'Post audience')]]"
            )
            if modal_title and any(el.is_displayed() for el in modal_title):
                modal_appeared = True
                print(f"[Account-{uid}] Modal 'Đối tượng của bài viết' đã xuất hiện!")
                break
        except:
            pass
        time.sleep(0.8)

    if not modal_appeared:
        print(f"[Account-{uid}] Không thấy modal đối tượng sau 60s, bỏ qua bước này.")
        return

    time.sleep(random.uniform(2.5, 5.5))

    # Chọn "Công khai"
    print(f"[Account-{uid}] Đang chọn 'Công khai'...")
    try:
        cong_khai_labels = driver.find_elements(By.XPATH,
            "//label[.//span[normalize-space()='Công khai' or normalize-space()='Public']]"
        )
        clicked_ck = False
        for lbl in cong_khai_labels:
            try:
                if lbl.is_displayed():
                    driver.execute_script("arguments[0].scrollIntoView({behavior:'smooth', block:'center'});", lbl)
                    time.sleep(random.uniform(1.2, 2.5))
                    ActionChains(driver).move_to_element(lbl).perform()
                    time.sleep(random.uniform(0.8, 1.8))
                    driver.execute_script("""
                        arguments[0].dispatchEvent(new MouseEvent('click', {view: window, bubbles: true, cancelable: true}));
                    """, lbl)
                    clicked_ck = True
                    print(f"[Account-{uid}] Đã chọn 'Công khai'!")
                    break
            except:
                pass
        if not clicked_ck:
            do_click(driver, uid, "//span[normalize-space()='Công khai' or normalize-space()='Public']", ["công khai", "public"])
    except Exception as e:
        print(f"[Account-{uid}] Lỗi khi chọn Công khai: {e}")

    time.sleep(random.uniform(2.0, 4.5))

    # Tick checkbox "Đặt làm đối tượng mặc định"
    print(f"[Account-{uid}] Đang tick 'Đặt làm đối tượng mặc định'...")
    try:
        mac_dinh_cb = driver.find_elements(By.XPATH,
            "//input[@type='checkbox'][@value='default_privacy_checkbox' or @aria-labelledby]"
            " | //input[@type='checkbox'][ancestor::div[.//span[contains(text(), 'Đặt làm đối tượng mặc định')]]]"
        )
        for cb in mac_dinh_cb:
            try:
                checked = cb.get_attribute("aria-checked")
                if checked != "true":
                    driver.execute_script("arguments[0].scrollIntoView({behavior:'smooth', block:'center'});", cb)
                    time.sleep(random.uniform(1.5, 3.0))
                    ActionChains(driver).move_to_element(cb).perform()
                    time.sleep(random.uniform(0.8, 1.5))
                    driver.execute_script("arguments[0].click();", cb)
                    print(f"[Account-{uid}] Đã tick 'Đặt làm đối tượng mặc định'!")
                else:
                    print(f"[Account-{uid}] Checkbox 'Đặt làm đối tượng mặc định' đã được tích sẵn.")
                break
            except:
                pass
    except Exception as e:
        print(f"[Account-{uid}] Lỗi khi tick checkbox mặc định: {e}")

    time.sleep(random.uniform(2.0, 4.0))

    # Click "Xong"
    print(f"[Account-{uid}] Đang click nút 'Xong'...")
    xong_doi_tuong_xpath = (
        "//div[@aria-label='Đã lựa chọn xong đối tượng quyền riêng tư và đóng hộp thoại'][@role='button']"
        " | //div[@role='button'][.//span[normalize-space()='Xong' or normalize-space()='Done']]"
    )
    xong_dt_els = driver.find_elements(By.XPATH, xong_doi_tuong_xpath)
    clicked_xong_dt = False
    for el in xong_dt_els:
        try:
            if el.is_displayed():
                driver.execute_script("arguments[0].scrollIntoView({behavior:'smooth', block:'center'});", el)
                time.sleep(random.uniform(0.8, 1.5))
                ActionChains(driver).move_to_element(el).perform()
                time.sleep(random.uniform(0.5, 1.0))
                driver.execute_script("""
                    arguments[0].dispatchEvent(new MouseEvent('click', {view: window, bubbles: true, cancelable: true}));
                """, el)
                clicked_xong_dt = True
                print(f"[Account-{uid}] Đã click 'Xong'!")
                break
        except:
            pass
    if not clicked_xong_dt:
        do_click(driver, uid, xong_doi_tuong_xpath, ["xong", "done"])

    time.sleep(random.uniform(2.0, 3.5))
