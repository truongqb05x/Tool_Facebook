import time
import random
import os
import json
from datetime import datetime
from selenium.webdriver.common.by import By

REEL_SHARE_HISTORY_FILE = "reel_share_history.json"
REEL_SHARE_COOLDOWN_DAYS = 2

def _get_history_path():
    return os.path.join(os.getcwd(), REEL_SHARE_HISTORY_FILE)

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
        print(f"[ReelHistory] Lỗi lưu lịch sử: {e}")

def can_share_reel(uid: str) -> tuple:
    history = _load_history()
    uid = str(uid)
    if uid not in history:
        return True, ""
    try:
        last_time = datetime.fromisoformat(history[uid])
    except Exception:
        return True, ""
        
    elapsed = datetime.now() - last_time
    days_ago = elapsed.total_seconds() / 86400
    if days_ago < REEL_SHARE_COOLDOWN_DAYS:
        remaining = REEL_SHARE_COOLDOWN_DAYS - days_ago
        return False, f"Đã share reel cách đây {days_ago:.1f} ngày. Cần chờ thêm {remaining:.1f} ngày."
    return True, ""

def record_share_reel(uid: str):
    history = _load_history()
    history[str(uid)] = datetime.now().isoformat()
    _save_history(history)

def watch_reels(driver, uid, reel_time_min, reel_time_max, is_like=False, is_save=False, is_share=False, delay_min=2.0, delay_max=4.0):
    try:
        print(f"[{uid}] Đang chuyển đến trang Reel...")
        driver.get("http://facebook.com/reel")
        
        watch_time = random.randint(reel_time_min, reel_time_max)
        print(f"[{uid}] Xem Reel tổng cộng trong {watch_time}s...")
        
        end_time = time.time() + watch_time
        while time.time() < end_time:
            # Random thời gian xem từng reel từ 60s đến 90s
            sleep_chunk = random.randint(60, 90)
            remaining_time = end_time - time.time()
            
            if sleep_chunk > remaining_time:
                sleep_chunk = int(remaining_time)
                
            if sleep_chunk > 0:
                print(f"[{uid}] Đang xem Reel hiện tại trong {sleep_chunk}s...")
                time.sleep(sleep_chunk)
                
            if time.time() >= end_time:
                break
                
            print(f"[{uid}] Tìm và click nút 'Thẻ tiếp theo'...")
            try:
                next_btn = driver.find_element(By.XPATH, "//div[@aria-label='Thẻ tiếp theo'][@role='button']")
                try:
                    next_btn.click()
                except:
                    driver.execute_script("arguments[0].click();", next_btn)
                print(f"[{uid}] Đã click 'Thẻ tiếp theo'!")
            except Exception as e:
                print(f"[{uid}] Lỗi khi click 'Thẻ tiếp theo' (có thể chưa tải xong hoặc hết reel).")

        actions = []
        if is_like: actions.append(("//div[@aria-label='Thích'][@role='button']", "Thích"))
        if is_save: actions.append(("//div[@aria-label='Lưu'][@role='button']", "Lưu"))
        
        allowed_share = False
        if is_share:
            allowed, reason = can_share_reel(uid)
            if not allowed:
                print(f"[{uid}] ⏭ Bỏ qua Chia sẻ Reel: {reason}")
            else:
                allowed_share = True
                actions.append(("//div[@aria-label='Chia sẻ'][@role='button']", "Chia sẻ"))

        for xp, action_name in actions:
            print(f"[{uid}] Tìm nút '{action_name}'...")
            try:
                btns = driver.find_elements(By.XPATH, xp)
                for btn in reversed(btns):
                    if btn.is_displayed():
                        try:
                            btn.click()
                        except:
                            driver.execute_script("arguments[0].click();", btn)
                        print(f"[{uid}] Đã click {action_name}!")
                        
                        if action_name == "Chia sẻ":
                            print(f"[{uid}] Đang chờ nút 'Chia sẻ ngay' (tối đa 60s)...")
                            end_wait_share = time.time() + 60
                            while time.time() < end_wait_share:
                                try:
                                    share_now_btns = driver.find_elements(By.XPATH, "//div[@aria-label='Chia sẻ ngay'][@role='button']")
                                    share_now_clicked = False
                                    for sn_btn in reversed(share_now_btns):
                                        if sn_btn.is_displayed():
                                            try:
                                                sn_btn.click()
                                            except:
                                                driver.execute_script("arguments[0].click();", sn_btn)
                                            print(f"[{uid}] Đã click 'Chia sẻ ngay'!")
                                            share_now_clicked = True
                                            break
                                    if share_now_clicked:
                                        record_share_reel(uid)
                                        break
                                except Exception:
                                    pass
                                time.sleep(1)
                                
                        break
            except Exception as e:
                print(f"[{uid}] Lỗi click {action_name}: {e}")
            
            time.sleep(random.uniform(delay_min, delay_max))

        return True
    except Exception as e:
        print(f"[{uid}] Lỗi xem Reels: {e}")
        return False
