# -*- coding: utf-8 -*-
"""
upload.py — Upload ảnh/video vào bài đăng.
"""
import os
import time
import random
from selenium.webdriver.common.by import By

VALID_EXTS = ('.png', '.jpg', '.jpeg', '.gif', '.mp4', '.webp')


def _get_default_image() -> str | None:
    """
    Tìm ngẫu nhiên 1 file ảnh từ thư mục resources/images
    tính từ working directory (cwd). Không dùng path cứng.
    """
    resources_dir = os.path.join(os.getcwd(), "resources", "images")
    if not os.path.isdir(resources_dir):
        return None
    files = [
        os.path.join(resources_dir, f)
        for f in os.listdir(resources_dir)
        if f.lower().endswith(VALID_EXTS)
    ]
    return random.choice(files) if files else None


def upload_media(driver, uid, image_path=None):
    """Tải file ảnh/video lên ô nhập bài đăng qua input[type=file]."""
    print(f"[Account-{uid}] Đang tải lên file ảnh/video...")
    try:
        file_path = image_path if (image_path and os.path.exists(image_path)) else _get_default_image()
        if file_path and os.path.exists(file_path):
            file_input = driver.find_element(By.XPATH, "//input[@type='file']")
            file_input.send_keys(file_path)
            print(f"[Account-{uid}] Đã gửi lệnh tải lên file: {os.path.basename(file_path)}")
            time.sleep(random.uniform(3.0, 5.0))
        else:
            print(f"[Account-{uid}] Không tìm thấy file ảnh nào trong resources/images, bỏ qua upload.")
    except Exception as e:
        print(f"[Account-{uid}] Lỗi khi tải ảnh lên: {e}")
