# -*- coding: utf-8 -*-
"""
api_post.py — Lấy bài viết ngẫu nhiên từ Facebook Graph API.
"""
import os
import time
import random
import requests

def get_random_post(target_uid: str, access_token: str, limit: int = 20):
    """
    Gọi Graph API lấy danh sách bài của target_uid,
    chọn ngẫu nhiên 1 bài, tải ảnh về temp_images/.
    Trả về dict {id, message, image_path, permalink_url} hoặc None.
    """
    url = f"https://graph.facebook.com/v23.0/{target_uid}/posts"
    params = {
        "access_token": access_token,
        "fields": "id,message,created_time,permalink_url,full_picture",
        "limit": limit,
    }
    try:
        response = requests.get(url, params=params, timeout=20)
        if not response.ok:
            print(f"[API] HTTP Error: {response.status_code} {response.text}")
            return None

        posts = response.json().get("data", [])
        if not posts:
            return None

        post = random.choice(posts)
        message = post.get("message", "")
        picture_url = post.get("full_picture", "")

        image_path = None
        if picture_url:
            try:
                img_res = requests.get(picture_url, timeout=15)
                if img_res.ok:
                    temp_dir = os.path.join(os.getcwd(), "temp_images")
                    os.makedirs(temp_dir, exist_ok=True)
                    image_path = os.path.join(temp_dir, f"post_img_{int(time.time())}.jpg")
                    with open(image_path, "wb") as f:
                        f.write(img_res.content)
            except Exception as e:
                print(f"[API] Lỗi tải ảnh từ bài viết: {e}")

        return {
            "id": post.get("id"),
            "message": message,
            "image_path": image_path,
            "permalink_url": post.get("permalink_url"),
        }
    except Exception as e:
        print(f"[API] Lỗi gọi API: {e}")
        return None
