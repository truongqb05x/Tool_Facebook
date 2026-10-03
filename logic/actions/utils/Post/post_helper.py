# -*- coding: utf-8 -*-
"""
post_helper.py — Tiện ích click dùng chung cho toàn bộ module Post.
"""
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
# Script click React-safe (mousedown + mouseup + click event)
REACT_CLICK_SCRIPT = """
var el = arguments[0];
['mousedown', 'mouseup', 'click'].forEach(function(eventType) {
    el.dispatchEvent(new MouseEvent(eventType, {
        view: window, bubbles: true, cancelable: true, buttons: 1
    }));
});
"""

def do_click(driver, uid, xpath, fallback_texts=None):
    """
    Thử click phần tử theo XPath trong vòng tối đa 60s.
    Thứ tự ưu tiên: ActionChains → JS click → JS tìm span bằng text.
    """
    end_time = time.time() + 60
    while time.time() < end_time:
        try:
            elements = driver.find_elements(By.XPATH, xpath)
            for el in elements:
                try:
                    driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", el)
                    time.sleep(0.5)
                    if el.is_displayed():
                        try:
                            ActionChains(driver).move_to_element(el).click().perform()
                            time.sleep(1)
                            return
                        except:
                            pass
                    driver.execute_script("arguments[0].click();", el)
                    time.sleep(1)
                    return
                except:
                    pass

            if fallback_texts:
                success = driver.execute_script("""
                    var texts = arguments[0].map(function(t) { return t.toLowerCase(); });
                    function tryClick(el) {
                        try { el.click(); } catch(e) {}
                        try {
                            ['mousedown', 'mouseup', 'click'].forEach(function(eventType) {
                                el.dispatchEvent(new MouseEvent(eventType, {
                                    view: window, bubbles: true, cancelable: true, buttons: 1
                                }));
                            });
                        } catch(e) {}
                    }
                    var spans = document.querySelectorAll('span');
                    for (var i = 0; i < spans.length; i++) {
                        var text = (spans[i].innerText || spans[i].textContent || '').trim().toLowerCase();
                        if (text) {
                            for (var j = 0; j < texts.length; j++) {
                                if (text.includes(texts[j])) {
                                    var target = spans[i];
                                    target.scrollIntoView({block: 'center'});
                                    var curr = target;
                                    while (curr && curr !== document.body) {
                                        if (curr.getAttribute('role') === 'button' ||
                                            curr.tagName.toLowerCase() === 'div' && curr.getAttribute('aria-label')) {
                                            target = curr; break;
                                        }
                                        curr = curr.parentElement;
                                    }
                                    tryClick(target);
                                    return true;
                                }
                            }
                        }
                    }
                    return false;
                """, fallback_texts)
                if success:
                    time.sleep(1)
                    return
        except Exception:
            pass
        time.sleep(1)
    print(f"[Account-{uid}] Không thể click vào: {fallback_texts or xpath} sau 60s")
