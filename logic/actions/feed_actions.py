# -*- coding: utf-8 -*-
import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from actions.utils.like_actions import random_like_post
from actions.warmup_tasks import execute_warmup_task


def warm_up_account(driver, uid, warmup_time=None, cfg=None):
    if warmup_time is None:
        warmup_time = random.randint(120, 240) # 2-4 phút
    start_time = time.time()
    
    # Parse cfg
    is_like_post = False
    allowed_reactions = []
    reaction_delay_min = 5
    reaction_delay_max = 15
    if cfg:
        is_like_post = cfg.get("IsLikePost", False)
        if cfg.get("IsReactionLike"): allowed_reactions.extend(["Thích", "Like"])
        if cfg.get("IsReactionLove"): allowed_reactions.extend(["Yêu thích", "Love"])
        if cfg.get("IsReactionCare"): allowed_reactions.extend(["Thương thương", "Care"])
        if cfg.get("IsReactionHaha"): allowed_reactions.extend(["Haha"])
        if cfg.get("IsReactionWow"): allowed_reactions.extend(["Wow"])
        if cfg.get("IsReactionSad"): allowed_reactions.extend(["Buồn", "Sad"])
        if cfg.get("IsReactionAngry"): allowed_reactions.extend(["Phẫn nộ", "Angry"])
        reaction_delay_min = cfg.get("ReactionDelayMin", 5)
        reaction_delay_max = cfg.get("ReactionDelayMax", 15)
        is_read_noti = cfg.get("IsReadNoti", False)
        read_noti_count = cfg.get("ReadNotiCount", 5)
        is_chat = cfg.get("IsChat", False)
        is_random_click = cfg.get("IsRandomClick", True)
    else:
        is_read_noti = False
        read_noti_count = 5
        is_chat = False
        is_random_click = True

    pending_tasks = []
    if is_read_noti:
        for _ in range(read_noti_count):
            pending_tasks.append("read_noti")
    if is_chat:
        pending_tasks.append("chat")
    if cfg:
        if cfg.get("IsAcceptFriend", False):
            count = int(cfg.get("AcceptFriendCount", 5))
            for _ in range(count):
                pending_tasks.append("accept_friend")
        if cfg.get("IsAddFriendSuggested", False):
            pending_tasks.append("add_friend_suggested")
        if cfg.get("IsUpStory", False):
            pending_tasks.append("up_story")
        if cfg.get("IsViewStory", False):
            pending_tasks.append("view_story")
        if cfg.get("IsWatchReel", False):
            pending_tasks.append("watch_reel")
        if cfg.get("IsPost", False):
            pending_tasks.append("post")
            
    random.shuffle(pending_tasks)
    
    # Tạo các mốc thời gian ngẫu nhiên để thực hiện task
    task_times = []
    if pending_tasks:
        for _ in range(len(pending_tasks)):
            # Chọn một thời điểm ngẫu nhiên trong khoảng từ giây thứ 10 đến sát giờ kết thúc
            trigger = start_time + random.uniform(10, max(11, warmup_time - 10))
            task_times.append(trigger)
        task_times.sort(reverse=True) # Sắp xếp giảm dần để dùng pop() lấy mốc thời gian gần nhất

    # Ưu tiên News Feed để có nhiều link tương tác
    url = "https://www.facebook.com/"
    try:
        driver.get(url)
    except Exception as e:
        err_msg = str(e).split('\n')[0] if str(e) else "Lỗi không xác định"
        print(f"[{uid}] [-] Lỗi tải trang chủ: {err_msg}")
    
    while (time.time() - start_time) < warmup_time:
        if task_times and time.time() > task_times[-1]:
            task_to_run = pending_tasks.pop()
            task_times.pop()
            execute_warmup_task(task_to_run, driver, uid, cfg)
            
            # Quay lại Feed để tiếp tục lướt sau khi thực hiện xong task
            try:
                driver.get(url)
                time.sleep(3)
            except: pass
        scroll_amount = random.randint(400, 800)
        try:
            driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
        except Exception:
            pass
        time.sleep(random.uniform(4, 9))
        
        # Ngẫu nhiên mở link (khoảng 20% cơ hội mỗi lần cuộn)
        if is_random_click and random.random() < 0.2:
            try:
                # Tìm các link tiềm năng (bài viết, link chia sẻ...)
                candidates = driver.find_elements(By.CSS_SELECTOR, 'a[role="link"]:not([data-scanned="true"])')
                
                # Lọc links có vẻ là bài viết hoặc permalink
                post_links = [c for c in candidates if c.get_attribute("href") and 
                             ("/posts/" in c.get_attribute("href") or 
                              "/permalink/" in c.get_attribute("href") or 
                              "story_fbid" in c.get_attribute("href"))]
                
                if post_links:
                    target = random.choice(post_links)
                    # Đánh dấu đã quét để tránh click lại chính nó
                    driver.execute_script("arguments[0].setAttribute('data-scanned', 'true')", target)
                    
                    link_href = target.get_attribute("href")
                    
                    # Click trực tiếp trong cùng tab
                    target.click()
                    
                    # Tính toán thời gian xem sao cho không vượt quá thời gian nuôi còn lại
                    remaining_time = warmup_time - (time.time() - start_time)
                    wait_view = random.randint(5, 50)
                    
                    # Cắt giảm thời gian xem nếu sắp hết giờ (chừa lại 3s để load & back)
                    if wait_view > remaining_time - 3:
                        wait_view = int(remaining_time - 3)
                    
                    if wait_view > 0:
                        end_view_time = time.time() + wait_view
                        
                        # Vòng lặp cuộn dần dần để giả lập người dùng đọc nội dung
                        while time.time() < end_view_time:
                            scroll_dist = random.randint(100, 300)
                            try:
                                driver.execute_script(f"window.scrollBy(0, {scroll_dist});")
                            except:
                                pass
                            
                            chunk_sleep = random.uniform(2, 5)
                            if time.time() + chunk_sleep > end_view_time:
                                time.sleep(max(0, end_view_time - time.time()))
                                break
                            else:
                                time.sleep(chunk_sleep)
                    
                    # Quay lại Feed để tiếp tục nuôi
                    driver.back()
                    time.sleep(3)
            except Exception:
                # Bỏ qua lỗi nhỏ khi tìm link/click để không làm crash luồng nuôi
                pass
        
        # Logic like bài viết
        if is_like_post and 'next_like_time' not in locals():
            next_like_time = time.time() + random.uniform(reaction_delay_min, reaction_delay_max)
            
        if is_like_post and time.time() > next_like_time:
            random_like_post(driver, uid, allowed_reactions=allowed_reactions)
            next_like_time = time.time() + random.uniform(reaction_delay_min, reaction_delay_max)

    print(f"[{uid}] ✅ Hoàn thành warm-up.")
