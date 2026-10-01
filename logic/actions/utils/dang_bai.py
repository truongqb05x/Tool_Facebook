# -*- coding: utf-8 -*-
"""
dang_bai.py — Backward compatibility shim.
File này đã được tách thành package: actions/utils/Post/
Import trực tiếp từ đó để có đầy đủ tính năng.
"""
from actions.utils.Post import (
    post_manual_content,
    get_random_post,
    can_post,
    record_post,
    get_last_post_time,
)

__all__ = [
    "post_manual_content",
    "get_random_post",
    "can_post",
    "record_post",
    "get_last_post_time",
]