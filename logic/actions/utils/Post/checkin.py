# -*- coding: utf-8 -*-
"""
checkin.py — Chọn check-in vị trí ngẫu nhiên khi đăng bài.
"""
import time
import random
from selenium.webdriver.common.by import By
from .post_helper import do_click, REACT_CLICK_SCRIPT


def _open_more_options(driver, uid):
    """Mở menu 3 chấm 'Lựa chọn khác'."""
    print(f"[Account-{uid}] Đang mở menu 'Lựa chọn khác'...")
    driver.execute_script("if(document.activeElement) document.activeElement.blur();")
    time.sleep(0.5)
    xp = "//div[@role='dialog']//div[@aria-label='Lựa chọn khác cho bài viết' or @aria-label='More options for your post'][@role='button']"
    els = driver.find_elements(By.XPATH, xp)
    for el in els:
        if el.is_displayed():
            try:
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", el)
                time.sleep(0.5)
                driver.execute_script(REACT_CLICK_SCRIPT, el)
                print(f"[Account-{uid}] Đã mở menu thành công!")
                time.sleep(random.uniform(1.0, 2.0))
                return True
            except:
                pass
    return False


def add_checkin(driver, uid):
    """Mở menu, click Check in, chọn vị trí ngẫu nhiên."""
    _open_more_options(driver, uid)

    print(f"[Account-{uid}] Đang tìm nút 'Check in'...")
    checkin_xpath = "//div[@role='dialog']//div[@aria-label='Check in' or @aria-label='Check In'][@role='button']"
    checkin_els = driver.find_elements(By.XPATH, checkin_xpath)
    clicked = False
    for el in checkin_els:
        if el.is_displayed():
            try:
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", el)
                time.sleep(0.5)
                driver.execute_script(REACT_CLICK_SCRIPT, el)
                clicked = True
                print(f"[Account-{uid}] Đã click 'Check in'!")
                break
            except Exception as e:
                print(f"[Account-{uid}] Lỗi click Check in: {e}")

    if not clicked:
        do_click(driver, uid, checkin_xpath, ["check in", "check-in"])

    time.sleep(random.uniform(2.0, 3.5))

    try:
        print(f"[Account-{uid}] Đang chọn ngẫu nhiên một vị trí...")
        locations = driver.find_elements(By.XPATH,
            "//ul[@role='listbox']//li[@role='option']//div[@role='button']"
            " | //ul[@role='listbox']//li[@role='option']"
        )
        visible_locs = [loc for loc in locations if loc.is_displayed()]
        if visible_locs:
            chosen = random.choice(visible_locs)
            loc_name = chosen.text.replace('\n', ' - ') if chosen.text else chosen.get_attribute("aria-label") or "Một vị trí ẩn danh"
            print(f"[Account-{uid}] Đã bốc trúng vị trí: {loc_name}")
            try:
                click_target = chosen.find_element(By.XPATH,
                    ".//div[contains(@class, 'x1i10hfl')] | .//div[@role='button'] | .//div[@role='none']"
                )
            except:
                click_target = chosen
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", click_target)
            time.sleep(0.5)
            driver.execute_script(REACT_CLICK_SCRIPT, click_target)
            print(f"[Account-{uid}] Đã chọn vị trí thành công!")
        else:
            print(f"[Account-{uid}] Không tìm thấy danh sách vị trí!")
    except Exception as e:
        print(f"[Account-{uid}] Lỗi khi chọn vị trí: {e}")

    time.sleep(random.uniform(1.5, 3.0))
