from actions.utils.read_notifications import read_one_random_notification
from actions.utils.chat_two_ways import run_two_way_chat

def execute_warmup_task(task_name, driver, uid, cfg):
    import os
    if task_name == "read_noti":
        read_one_random_notification(driver, uid)
    elif task_name == "chat":
        run_two_way_chat(driver, uid, task_config=cfg)
    elif task_name == "accept_friend":
        try:
            from actions.utils.chapnhan_add import accept_friends
            print(f"[{uid}] Chấp nhận 1 lời mời kết bạn...")
            accept_friends(driver, uid, 1)
        except Exception as e:
            print(f"[{uid}] Lỗi khi chạy Chấp nhận kết bạn: {e}")
    elif task_name == "up_story":
        try:
            from actions.utils.story.up_story import up_story, can_up_story, record_story
            allowed, reason = can_up_story(uid)
            if not allowed:
                print(f"[{uid}] ⏭ Bỏ qua Đăng Story: {reason}")
            else:
                print(f"[{uid}] Chạy chức năng Đăng Story...")
                story_folder = cfg.get("StoryFolderPath", "").strip()
                success = up_story(driver, uid, image_folder=story_folder if story_folder else None)
                if success:
                    record_story(uid)
        except Exception as e:
            print(f"[{uid}] Lỗi khi chạy Đăng Story: {e}")
    elif task_name == "view_story":
        try:
            from actions.utils.story.view_story import view_story
            print(f"[{uid}] Chạy chức năng Xem Story...")
            view_story(driver, uid)
        except Exception as e:
            print(f"[{uid}] Lỗi khi chạy Xem Story: {e}")
    elif task_name == "watch_reel":
        try:
            from actions.utils.reels import watch_reels
            print(f"[{uid}] Chạy chức năng Xem Reels...")
            reel_min = int(cfg.get("ReelTimeMin", 15))
            reel_max = int(cfg.get("ReelTimeMax", 30))
            is_like = bool(cfg.get("IsReelLike", False))
            is_save = bool(cfg.get("IsReelSave", False))
            is_share = bool(cfg.get("IsReelShare", False))
            delay_min = int(cfg.get("ReelDelayMin", 2))
            delay_max = int(cfg.get("ReelDelayMax", 5))
            watch_reels(driver, uid, reel_min, reel_max, is_like, is_save, is_share, delay_min, delay_max)
        except Exception as e:
            print(f"[{uid}] Lỗi khi chạy Xem Reels: {e}")
    elif task_name == "post":
        try:
            from actions.utils.Post import can_post, record_post, post_manual_content, get_random_post
            import json
            allowed, skip_reason = can_post(uid)
            if not allowed:
                print(f"[{uid}] ⏭ Bỏ qua đăng bài: {skip_reason}")
            else:
                post_config_path = os.path.join(os.getcwd(), "post_config.json")
                post_config = {}
                if os.path.exists(post_config_path):
                    try:
                        with open(post_config_path, "r", encoding="utf-8") as f:
                            post_config = json.load(f)
                    except:
                        pass
                mode = post_config.get("Mode", 1)
                is_feeling = post_config.get("IsFeeling", True)
                is_checkin = post_config.get("IsCheckIn", True)
                is_tag = post_config.get("IsTagFriends", True)
                post_success = False
                if mode == 1:
                    import random
                    content = None
                    txt_path = post_config.get("ContentPath", "")
                    img_path = post_config.get("ImagePath", "")
                    if txt_path and os.path.exists(txt_path):
                        try:
                            with open(txt_path, "r", encoding="utf-8") as f:
                                lines = [l.strip() for l in f if l.strip()]
                                if lines: content = random.choice(lines)
                        except: pass
                    if img_path and os.path.isdir(img_path):
                        valid_exts = ('.png', '.jpg', '.jpeg')
                        valid_images = [os.path.join(img_path, f) for f in os.listdir(img_path) if f.lower().endswith(valid_exts)]
                        if valid_images:
                            img_path = random.choice(valid_images)
                        else:
                            img_path = None
                    elif not img_path or not os.path.exists(img_path):
                        img_path = None
                    post_success = post_manual_content(driver, uid, post_content=content, image_path=img_path, is_feeling=is_feeling, is_checkin=is_checkin, is_tag=is_tag)
                elif mode == 2:
                    print(f"[{uid}] Lấy bài viết ngẫu nhiên từ API Graph...")
                    import random
                    target_uids = ["100044408347036", "100044255598168", "100012078365894"]
                    target_uid_api = random.choice(target_uids)
                    accounts_path = os.path.join(os.getcwd(), "accounts.json")
                    accounts_data = None
                    valid_tokens = []
                    try:
                        with open(accounts_path, 'r', encoding='utf-8') as f:
                            accounts_data = json.load(f)
                            for acc in accounts_data.get("Accounts", []):
                                t = acc.get("Token", "").strip()
                                if t:
                                    valid_tokens.append(acc)
                    except:
                        pass
                    post_data = None
                    fallback_token = "EAAAAUaZA8jlABQ7IWv8yBHIu1AnOHE8Wt4XqrACtZAKm0EERw8rcXoVIs2VQ2obfE98kpawmClywgMJzjEyJIYslODXFvAmr5v0ELBKs8Q6vMMX8dVgxpARgOPhPKzHkkKZAeGYpE2y8gNyStB1vWbwh2chje8H3CnNIAk8IXszu4LOEPZA4lMZAFvU1TEZBbz2PcX00EZCzwZDZD"
                    if not valid_tokens:
                        print(f"[{uid}] Không tìm thấy Token nào trong danh sách tài khoản, dùng token mặc định...")
                        post_data = get_random_post(target_uid_api, fallback_token)
                    else:
                        random.shuffle(valid_tokens)
                        for acc_obj in list(valid_tokens):
                            access_token = acc_obj.get("Token", "")
                            print(f"[{uid}] Thử lấy bài bằng Token của UID: {acc_obj.get('Uid')}")
                            post_data = get_random_post(target_uid_api, access_token)
                            if post_data:
                                print(f"[{uid}] Token hợp lệ!")
                                break
                            else:
                                print(f"[{uid}] Token lỗi, tiến hành xóa token này...")
                                acc_obj["Token"] = ""
                                try:
                                    with open(accounts_path, 'w', encoding='utf-8') as fw:
                                        json.dump(accounts_data, fw, ensure_ascii=False, indent=2)
                                except Exception as e:
                                    print(f"[{uid}] Lỗi khi cập nhật accounts.json: {e}")
                    if post_data:
                        print(f"[{uid}] Bài viết lấy được từ API: {post_data['message'][:30]}...")
                        post_success = post_manual_content(driver, uid, post_content=post_data["message"], image_path=post_data["image_path"], is_feeling=is_feeling, is_checkin=is_checkin, is_tag=is_tag)
                    else:
                        print(f"[{uid}] Lỗi lấy từ API, chuyển về mặc định...")
                        post_success = post_manual_content(driver, uid, is_feeling=is_feeling, is_checkin=is_checkin, is_tag=is_tag)
                if post_success:
                    record_post(uid)
                    print(f"[{uid}] UI_POST_SUCCESS")
                else:
                    print(f"[{uid}] ⚠ Đăng bài không thành công, không lưu lịch sử.")
        except Exception as e:
            print(f"[{uid}] Lỗi chạy chức năng đăng bài: {e}")
