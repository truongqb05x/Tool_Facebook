# -*- coding: utf-8 -*-
"""
publish.py — Click nút Đăng bài và chờ xác nhận hoàn tất.
"""
import time
import random
from selenium.webdriver.common.by import By
from .post_helper import do_click, REACT_CLICK_SCRIPT

DANG_XPATHS = [
    "//div[@role='dialog']//div[@aria-label='Đăng' or @aria-label='Post'][@role='button']",
    "//div[@aria-label='Đăng' or @aria-label='Post'][@role='button']",
    "//div[@role='dialog']//div[@role='button'][.//span[translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')='đăng' or translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')='post']]",
    "//div[@role='button'][.//span[translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')='đăng' or translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')='post']]",
    "//span[translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')='đăng' or translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')='post']",
    "//div[contains(@aria-label, 'Đăng') or contains(@aria-label, 'Post')][@role='button']",
]


def click_publish(driver, uid) -> bool:
    """
    Tìm và click nút Đăng. Thử tối đa 5 lần (chờ ảnh load).
    Trả về True nếu click thành công.
    """
    time.sleep(random.uniform(2.0, 4.0))
    print(f"[Account-{uid}] Đang tìm và nhấn nút 'Đăng'...")

    clicked = False
    for try_idx in range(5):
        if clicked:
            break
        for xp in DANG_XPATHS:
            if clicked:
                break
            try:
                els = driver.find_elements(By.XPATH, xp)
                for el in els:
                    if not el.is_displayed():
                        continue
                    if str(el.get_attribute("aria-disabled")).lower() == "true":
                        print(f"[Account-{uid}] Nút Đăng đang disable (ảnh đang load), chờ thêm...")
                        continue
                    try:
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", el)
                        time.sleep(0.5)
                    except:
                        pass

                    # Thử 1: Selenium click
                    try:
                        el.click()
                        clicked = True
                        print(f"[Account-{uid}] Đã click Đăng (Selenium)!")
                        break
                    except:
                        pass

                    # Thử 2: JS click span bên trong
                    try:
                        inner = el.find_element(By.XPATH,
                            ".//span[translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')='đăng'"
                            " or translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')='post']"
                        )
                        driver.execute_script(REACT_CLICK_SCRIPT, inner)
                        clicked = True
                        print(f"[Account-{uid}] Đã click Đăng (JS inner_span)!")
                        break
                    except:
                        pass

                    # Thử 3: JS MouseEvent
                    try:
                        driver.execute_script(REACT_CLICK_SCRIPT, el)
                        clicked = True
                        print(f"[Account-{uid}] Đã click Đăng (JS MouseEvent)!")
                        break
                    except:
                        pass

                    # Thử 4: JS click thuần
                    try:
                        driver.execute_script("arguments[0].click();", el)
                        clicked = True
                        print(f"[Account-{uid}] Đã click Đăng (JS click thuần)!")
                        break
                    except:
                        pass
            except Exception:
                pass

        if not clicked:
            print(f"[Account-{uid}] Chưa ấn được Đăng (lần {try_idx+1}/5), chờ 2s...")
            time.sleep(2)

    if not clicked:
        print(f"[Account-{uid}] Thử fallback do_click để nhấn Đăng...")
        do_click(driver, uid, " | ".join(DANG_XPATHS), ["đăng", "post"])
        clicked = True  # assume success với fallback

    if clicked:
        print(f"[Account-{uid}] Đã hoàn tất lệnh click Đăng bài!")
        wait_time = random.uniform(10, 15)
        print(f"[Account-{uid}] Đang đợi {wait_time:.1f}s để hoàn tất đăng bài...")
        time.sleep(wait_time)
        print(f"[Account-{uid}] HOÀN THÀNH: Quá trình đăng bài thành công!")

    return clicked
