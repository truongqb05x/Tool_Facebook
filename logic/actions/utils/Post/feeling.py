# -*- coding: utf-8 -*-
"""
feeling.py — Chọn cảm xúc/hoạt động ngẫu nhiên khi đăng bài.
"""
import time
import random
from selenium.webdriver.common.by import By
from .post_helper import do_click


def add_feeling(driver, uid):
    """Mở panel Cảm xúc/Hoạt động và chọn ngẫu nhiên một cảm xúc."""
    print(f"[Account-{uid}] Đang tìm và nhấn nút 'Cảm xúc/hoạt động'...")
    camxuc_xpath = "//div[@aria-label='Cảm xúc/hoạt động' or @aria-label='Feeling/activity'][@role='button']"
    camxuc_els = driver.find_elements(By.XPATH, camxuc_xpath)
    clicked = False
    for el in camxuc_els:
        if el.is_displayed():
            try:
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", el)
                time.sleep(0.5)
                driver.execute_script("arguments[0].click();", el)
                clicked = True
                print(f"[Account-{uid}] Đã click 'Cảm xúc/hoạt động'!")
                break
            except Exception as e:
                print(f"[Account-{uid}] Lỗi click cảm xúc: {e}")

    if not clicked:
        do_click(driver, uid, camxuc_xpath, ["cảm xúc", "feeling"])

    time.sleep(random.uniform(2.0, 3.5))

    try:
        print(f"[Account-{uid}] Đang chọn ngẫu nhiên một cảm xúc...")
        feelings = driver.find_elements(By.XPATH,
            "//ul[@role='listbox']//li[@role='option']//div[@role='button']"
        )
        visible_feelings = [f for f in feelings if f.is_displayed()]
        if visible_feelings:
            chosen = random.choice(visible_feelings)
            feeling_name = chosen.get_attribute("aria-label") or "Không rõ"
            print(f"[Account-{uid}] Đã bốc trúng cảm xúc: {feeling_name}")
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", chosen)
            time.sleep(0.5)
            driver.execute_script("arguments[0].click();", chosen)
            print(f"[Account-{uid}] Đã click chọn cảm xúc thành công!")
        else:
            print(f"[Account-{uid}] Không tìm thấy danh sách cảm xúc!")
    except Exception as e:
        print(f"[Account-{uid}] Lỗi khi chọn cảm xúc: {e}")

    time.sleep(random.uniform(1.5, 3.0))
