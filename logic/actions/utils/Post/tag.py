# -*- coding: utf-8 -*-
"""
tag.py — Gắn thẻ bạn bè ngẫu nhiên khi đăng bài.
"""
import time
import random
from selenium.webdriver.common.by import By
from .post_helper import do_click, REACT_CLICK_SCRIPT
from .checkin import _open_more_options


def add_tag(driver, uid):
    """Mở menu, click Gắn thẻ người khác, chọn 1-3 bạn bè ngẫu nhiên."""
    _open_more_options(driver, uid)

    print(f"[Account-{uid}] Đang tìm nút 'Gắn thẻ người khác'...")
    tag_xpath = "//div[@role='dialog']//div[@aria-label='Gắn thẻ người khác' or @aria-label='Tag people'][@role='button']"
    tag_els = driver.find_elements(By.XPATH, tag_xpath)
    clicked = False
    for el in tag_els:
        if el.is_displayed():
            try:
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", el)
                time.sleep(0.5)
                driver.execute_script(REACT_CLICK_SCRIPT, el)
                clicked = True
                print(f"[Account-{uid}] Đã click 'Gắn thẻ người khác'!")
                break
            except Exception as e:
                print(f"[Account-{uid}] Lỗi click Gắn thẻ: {e}")

    if not clicked:
        do_click(driver, uid, tag_xpath, ["gắn thẻ", "tag"])

    time.sleep(random.uniform(2.0, 3.5))

    try:
        print(f"[Account-{uid}] Đang chọn ngẫu nhiên bạn bè để gắn thẻ...")
        friends = driver.find_elements(By.XPATH, "//ul[@role='listbox']//li[@role='option']")
        visible_friends = [f for f in friends if f.is_displayed()]
        if visible_friends:
            num_to_tag = random.randint(1, min(3, len(visible_friends)))
            chosen_friends = random.sample(visible_friends, num_to_tag)

            for i, friend in enumerate(chosen_friends):
                friend_name = friend.text.replace('\n', ' - ') if friend.text else f"Bạn bè {i+1}"
                print(f"[Account-{uid}] Đang gắn thẻ: {friend_name}")
                try:
                    click_target = friend.find_element(By.XPATH,
                        ".//div[contains(@class, 'x1i10hfl')] | .//div[@role='button'] | .//div[@role='none']"
                    )
                except:
                    click_target = friend
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", click_target)
                time.sleep(0.5)
                driver.execute_script(REACT_CLICK_SCRIPT, click_target)
                time.sleep(0.5)

            print(f"[Account-{uid}] Đã gắn thẻ {num_to_tag} người, đang nhấn 'Xong'...")
            xong_xpath = (
                "//div[@role='button'][.//span[translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')='xong'"
                " or translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')='done']]"
            )
            xong_els = driver.find_elements(By.XPATH, xong_xpath)
            clicked_xong = False
            for el in xong_els:
                if el.is_displayed():
                    try:
                        driver.execute_script(REACT_CLICK_SCRIPT, el)
                        clicked_xong = True
                        break
                    except:
                        pass
            if not clicked_xong:
                do_click(driver, uid, xong_xpath, ["xong", "done"])
        else:
            print(f"[Account-{uid}] Không tìm thấy danh sách bạn bè để gắn thẻ!")
    except Exception as e:
        print(f"[Account-{uid}] Lỗi khi gắn thẻ bạn bè: {e}")
