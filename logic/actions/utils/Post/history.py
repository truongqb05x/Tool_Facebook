# -*- coding: utf-8 -*-
"""
post_history.py — Quản lý lịch sử đăng bài theo UID.

File lưu trữ: post_history.json (cùng thư mục working dir)
Định dạng:
{
    "<uid>": "2024-10-01T14:30:00"   // ISO 8601, thời điểm đăng bài gần nhất
}

Quy tắc:
    - Nếu UID chưa có bản ghi → cho phép đăng.
    - Nếu thời gian đăng gần nhất < 7 ngày → bỏ qua.
    - Nếu thời gian đăng gần nhất >= 7 ngày → cho phép đăng.
"""

import os
import json
from datetime import datetime, timedelta

POST_HISTORY_FILE = "post_history.json"
POST_COOLDOWN_DAYS = 7


def _get_history_path():
    return os.path.join(os.getcwd(), POST_HISTORY_FILE)


def _load_history():
    path = _get_history_path()
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_history(data: dict):
    path = _get_history_path()
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[PostHistory] Lỗi lưu lịch sử: {e}")


def can_post(uid: str) -> tuple[bool, str]:
    """
    Kiểm tra xem uid có đủ điều kiện đăng bài không.

    Returns:
        (True, "")                        — được phép đăng
        (False, "<lý do>")               — bị bỏ qua
    """
    history = _load_history()
    uid = str(uid)

    if uid not in history:
        return True, ""

    try:
        last_post_time = datetime.fromisoformat(history[uid])
    except Exception:
        return True, ""  # bản ghi lỗi → cho phép đăng lại

    elapsed = datetime.now() - last_post_time
    days_ago = elapsed.total_seconds() / 86400

    if days_ago < POST_COOLDOWN_DAYS:
        remaining = POST_COOLDOWN_DAYS - days_ago
        last_str = last_post_time.strftime("%d/%m/%Y %H:%M")
        return False, (
            f"Đã đăng bài cách đây {days_ago:.1f} ngày (lúc {last_str}). "
            f"Cần chờ thêm {remaining:.1f} ngày nữa."
        )

    return True, ""


def record_post(uid: str):
    """Ghi lại thời điểm đăng bài thành công cho uid."""
    history = _load_history()
    uid = str(uid)
    history[uid] = datetime.now().isoformat()
    _save_history(history)


def get_last_post_time(uid: str):
    """Trả về datetime của lần đăng gần nhất, hoặc None nếu chưa đăng."""
    history = _load_history()
    uid = str(uid)
    if uid not in history:
        return None
    try:
        return datetime.fromisoformat(history[uid])
    except Exception:
        return None
