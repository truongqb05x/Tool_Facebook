# -*- coding: utf-8 -*-
"""
Post package — Toàn bộ logic đăng bài tự động Facebook.

Cấu trúc:
    post_helper.py  — do_click(), REACT_CLICK_SCRIPT (dùng chung)
    audience.py     — ensure_public_audience()
    feeling.py      — add_feeling()
    upload.py       — upload_media()
    content.py      — type_content()
    checkin.py      — add_checkin()
    tag.py          — add_tag()
    publish.py      — click_publish()
    api_post.py     — get_random_post() từ Graph API
    history.py      — can_post(), record_post(), get_last_post_time()
"""
import os
import time
import random
from selenium.webdriver.common.by import By

from .post_helper import do_click, REACT_CLICK_SCRIPT
from .audience import ensure_public_audience
from .feeling import add_feeling
from .upload import upload_media
from .content import type_content
from .checkin import add_checkin
from .tag import add_tag
from .publish import click_publish
from .api_post import get_random_post
from .history import can_post, record_post, get_last_post_time


def post_manual_content(driver, uid, post_content=None, image_path=None,
                        is_feeling=True, is_checkin=True, is_tag=True) -> bool:
    """
    Orchestrator: điều phối toàn bộ luồng đăng bài.
    Trả về True nếu click Đăng thành công, False nếu thất bại.
    """
    print(f"[Account-{uid}] Truy cập trang chủ Facebook...")
    driver.get("https://www.facebook.com/")
    time.sleep(5)

    for attempt in range(3):
        print(f"[Account-{uid}] (Lần {attempt+1}) Đang nhấn 'Bạn đang nghĩ gì thế?'...")
        do_click(
            driver, uid,
            "//div[@role='button'][.//span[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'nghĩ gì') or contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'mind')]] | //span[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'nghĩ gì')]",
            ["nghĩ gì", "mind", "tạo bài viết", "create post"]
        )

        print(f"[Account-{uid}] Đang kiểm tra các popup đăng bài (tối đa 60s)...")
        end_time_popup = time.time() + 60
        is_ready = False

        while time.time() < end_time_popup:
            try:
                cong_khai_xpath = (
                    "//span[translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')='công khai'"
                    " or translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')='public']"
                    " | //div[@role='radio' or @role='button']//span[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'công khai')]"
                )
                luu_xpath = (
                    "//div[contains(@aria-label, 'Lưu') or contains(@aria-label, 'Save')][@role='button']"
                    " | //span[translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')='lưu'"
                    " or translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')='save']"
                )
                cong_khai_els = driver.find_elements(By.XPATH, cong_khai_xpath)
                luu_els = driver.find_elements(By.XPATH, luu_xpath)
                if (cong_khai_els and any(t.is_displayed() for t in cong_khai_els)
                        and luu_els and any(t.is_displayed() for t in luu_els)):
                    print(f"[Account-{uid}] Phát hiện bảng 'Chọn đối tượng', đang chọn 'Công khai'...")
                    do_click(driver, uid, cong_khai_xpath, ["công khai", "public"])
                    time.sleep(1)
                    do_click(driver, uid, luu_xpath, ["lưu", "save"])
                    time.sleep(3)
                    driver.refresh()
                    time.sleep(5)
                    break

                tiep_tuc_xpath = (
                    "//div[@aria-label='Tiếp tục' or @aria-label='Continue'][@role='button']"
                    " | //span[text()='Tiếp tục' or text()='Continue']"
                )
                tiep_tuc = driver.find_elements(By.XPATH, tiep_tuc_xpath)
                if tiep_tuc and any(t.is_displayed() for t in tiep_tuc):
                    print(f"[Account-{uid}] Phát hiện popup 'Xem lại đối tượng', đang nhấn 'Tiếp tục'...")
                    do_click(driver, uid, tiep_tuc_xpath, ["tiếp tục", "continue"])
                    time.sleep(1)
                    continue

                textbox_xpath = "//div[@role='textbox' and @contenteditable='true']"
                textbox = driver.find_elements(By.XPATH, textbox_xpath)
                if textbox and any(tb.is_displayed() for tb in textbox):
                    print(f"[Account-{uid}] Khung đăng bài đã sẵn sàng.")
                    is_ready = True
                    break
            except Exception:
                pass
            time.sleep(1)

        if is_ready:
            try:
                ensure_public_audience(driver, uid)

                if is_feeling:
                    add_feeling(driver, uid)

                upload_media(driver, uid, image_path)
                type_content(driver, uid, post_content)

                if is_checkin:
                    add_checkin(driver, uid)

                if is_tag:
                    add_tag(driver, uid)

                time.sleep(random.uniform(2.0, 4.0))
                result = click_publish(driver, uid)
            except Exception as e:
                print(f"[Account-{uid}] Lỗi trong luồng đăng bài: {e}")
                result = False

            # Dọn dẹp ảnh tạm
            if image_path and os.path.exists(image_path):
                try:
                    os.remove(image_path)
                    print(f"[Account-{uid}] Đã dọn dẹp ảnh tạm: {image_path}")
                except Exception as e:
                    print(f"[Account-{uid}] Lỗi khi xóa ảnh tạm: {e}")

            return result

        else:
            if time.time() >= end_time_popup:
                print(f"[Account-{uid}] Quá 60s không thấy khung đăng bài. Bỏ qua.")
                break

    return False


__all__ = [
    "post_manual_content",
    "get_random_post",
    "can_post",
    "record_post",
    "get_last_post_time",
]
