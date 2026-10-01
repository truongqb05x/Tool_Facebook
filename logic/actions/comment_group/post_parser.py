# -*- coding: utf-8 -*-
import time
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains

def extract_post_info(driver, uid, box_to_comment):
    real_post_link = None
    post_time = "Không xác định"
    post_id = ""
    try:
        try:
            post_container = box_to_comment.find_element(By.XPATH, "./ancestor::div[.//a[@role='link' and @target='_blank']][1]")
            post_links = post_container.find_elements(By.XPATH, ".//a[@role='link' and @target='_blank']")
        except:
            try:
                post_container = box_to_comment.find_element(By.XPATH, "./ancestor::div[@role='article']")
            except:
                post_container = box_to_comment.find_element(By.XPATH, "./ancestor::div[12]")
            
            all_links = post_container.find_elements(By.XPATH, ".//a")
            post_links = []
            for a in all_links:
                try:
                    if a.find_elements(By.XPATH, ".//img"): continue
                    href = a.get_attribute("href") or ""
                    if "/posts/" in href or "/permalink/" in href:
                        post_links.insert(0, a)
                    else:
                        pt_text = a.find_element(By.XPATH, "..").text.lower()
                        time_kws = ["phút", "giờ", "ngày", "vừa xong", "min", "hr", "hôm qua", "tháng", "thg"]
                        if any(kw in pt_text for kw in time_kws) or a.get_attribute("aria-label"):
                            post_links.append(a)
                except: pass
        
        found_link_element = None
        for link in post_links:
            try:
                try:
                    parent_text = link.find_element(By.XPATH, "..").text
                    if parent_text:
                        post_time = parent_text.split("·")[0].strip()
                except:
                    pass

                href = link.get_attribute("href")
                if href and ("/posts/" in href or "/permalink/" in href):
                    real_post_link = href
                    found_link_element = link
                    break
                
                ActionChains(driver).move_to_element(link).perform()
                print(f"[{uid}] 🔍 [DEBUG] Đang hover thẻ <a>... Href ban đầu: {link.get_attribute('href')}")
                
                href_after_hover = None
                for step in range(20):
                    time.sleep(0.5)
                    href_after_hover = link.get_attribute("href")
                    print(f"[{uid}] 🔍 [DEBUG] Href đang chờ (bước {step + 1}): {href_after_hover}")
                    if href_after_hover and ("/posts/" in href_after_hover or "/permalink/" in href_after_hover):
                        break
                        
                if href_after_hover and ("/posts/" in href_after_hover or "/permalink/" in href_after_hover):
                    real_post_link = href_after_hover
                    found_link_element = link
                    break
            except Exception as e:
                print(f"[{uid}] ⚠️ Lỗi trong vòng lặp post_links: {e}")
                pass
                
        if post_time == "Không xác định" and found_link_element:
            try:
                pt = found_link_element.text.strip()
                if not pt:
                    pt = found_link_element.get_attribute("aria-label") or ""
                    pt = pt.strip()
                if not pt:
                    try:
                        labeled_span = found_link_element.find_element(By.XPATH, ".//*[@aria-labelledby]")
                        label_id = labeled_span.get_attribute("aria-labelledby")
                        if label_id:
                            label_el = driver.find_element(By.ID, label_id)
                            pt = label_el.text.strip()
                    except: pass
                if not pt:
                    try:
                        tooltips = driver.find_elements(By.XPATH, "//div[@role='tooltip']//span[@dir='auto']")
                        if tooltips: pt = tooltips[-1].text.strip()
                    except: pass
                if pt: post_time = pt
            except: pass
            
        if not real_post_link and post_links:
            href = post_links[0].get_attribute("href")
            if href: real_post_link = href
                
        if real_post_link:
            if "/posts/" in real_post_link or "/permalink/" in real_post_link:
                real_post_link = real_post_link.split("?")[0]
            import re
            match = re.search(r'/(?:posts|permalink)/(\d+)', real_post_link)
            if match: post_id = match.group(1)
            else: post_id = real_post_link.rstrip("/").split("/")[-1]
    except Exception as e:
        print(f"[{uid}] ⚠️ Lỗi khi bóc tách container/link: {e}")
        pass
    
    return post_time, post_id, real_post_link
