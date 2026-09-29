import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# XPath nút Tham gia nhóm (dùng chung)
_JOIN_BTN_XPATH = (
    "//div[@aria-label='Tham gia nhóm' and @role='button']"
    " | //div[@aria-label='Join group' and @role='button']"
    " | //div[@aria-label='Join Group' and @role='button']"
)

# XPath kiểm tra đã tham gia / đã gửi yêu cầu
_ALREADY_JOINED_XPATH = (
    "//div[@aria-label='Hủy yêu cầu' and @role='button']"
    " | //div[@aria-label='Đã tham gia' and @role='button']"
    " | //div[@aria-label='Yêu cầu đang chờ xử lý' and @role='button']"
    " | //div[@aria-label='Joined' and @role='button']"
    " | //div[@aria-label='Pending' and @role='button']"
    " | //div[@aria-label='Pending request' and @role='button']"
    " | //div[@aria-label='Cancel request' and @role='button']"
    " | //span[contains(text(), 'Hủy yêu cầu')]"
    " | //span[contains(text(), 'Đã tham gia')]"
    " | //span[contains(text(), 'Yêu cầu đang chờ')]"
    " | //span[contains(text(), 'Đã gửi yêu cầu')]"
    " | //span[contains(text(), 'Joined')]"
    " | //span[contains(text(), 'Pending')]"
    " | //span[contains(text(), 'Request sent')]"
    " | //span[contains(text(), 'Cancel request')]"
)

def _is_already_joined(driver):
    """Kiểm tra nhanh xem đã tham gia / đã gửi yêu cầu chưa qua DOM + page_source."""
    try:
        els = driver.find_elements(By.XPATH, _ALREADY_JOINED_XPATH)
        if els:
            return True
    except Exception:
        pass
    src = driver.page_source
    # Dùng keyword tiếng Anh trong page_source rất dễ bị dính false positive (có trong script/json).
    # Vì vậy với tiếng Anh chỉ check khi nó nằm giữa các thẻ HTML hoặc có dấu ngoặc kép.
    if any(kw in src for kw in ["Đã tham gia", "Đã gửi yêu cầu", "Hủy yêu cầu", "Yêu cầu đang chờ"]):
        return True
    if any(kw in src for kw in [">Joined<", ">Pending<", ">Request sent<", ">Cancel request<", '"Joined"', '"Pending"']):
        return True
    return False

def _detect_group_privacy(driver):
    """
    Phát hiện loại nhóm từ DOM / page_source.
    Trả về: 'private' | 'public' | 'unknown'
    """
    try:
        # Ưu tiên tìm trong DOM trước (chính xác hơn)
        _PRIVACY_XPATH = (
            "//div[contains(text(),'Nhóm Riêng tư') or contains(.,'Nhóm Riêng tư')]"
            " | //div[contains(text(),'Private group') or contains(.,'Private group')]"
        )
        els = driver.find_elements(By.XPATH, _PRIVACY_XPATH)
        if els:
            return "private"

        _PUBLIC_XPATH = (
            "//div[contains(text(),'Nhóm Công khai') or contains(.,'Nhóm Công khai')]"
            " | //div[contains(text(),'Public group') or contains(.,'Public group')]"
        )
        els = driver.find_elements(By.XPATH, _PUBLIC_XPATH)
        if els:
            return "public"
    except Exception:
        pass

    # Fallback: kiểm tra page_source
    try:
        src = driver.page_source
        if any(kw in src for kw in ["Nhóm Riêng tư", "Private group"]):
            return "private"
        if any(kw in src for kw in ["Nhóm Công khai", "Public group"]):
            return "public"
    except Exception:
        pass

    return "unknown"


def _handle_private_group_modal(driver, uid, group_id):
    """
    Xử lý popup câu hỏi / nội quy dành riêng cho nhóm Riêng tư.
    Facebook yêu cầu trả lời câu hỏi hoặc đồng ý nội quy trước khi duyệt.
    """
    dialog_xpath = (
        "//div[@role='dialog' and ("
        "contains(@aria-label, 'câu hỏi') or contains(@aria-label, 'quy tắc')"
        " or contains(@aria-label, 'Trả lời') or contains(@aria-label, 'Quy tắc')"
        " or contains(@aria-label, 'Question') or contains(@aria-label, 'Rules')"
        ")]"
    )
    try:
        # Đợi modal xuất hiện (tối đa 30s)
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.XPATH, dialog_xpath))
        )
    except Exception:
        # Không có modal → nhóm riêng tư nhưng không có câu hỏi bổ sung
        print(f"[{uid}] Đã gửi yêu cầu tham gia nhóm riêng tư {group_id} (không có câu hỏi).")
        return

    #print(f"[{uid}] 📝 Phát hiện popup câu hỏi nhóm riêng tư! Đang chờ form tải...")

    # Chờ nội dung form tải bằng WebDriverWait thay vì sleep cứng
    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((
                By.XPATH,
                dialog_xpath + "//textarea | " + dialog_xpath + "//input[@type='text']"
                " | " + dialog_xpath + "//div[@role='textbox']"
                " | " + dialog_xpath + "//input[@type='checkbox']"
                " | " + dialog_xpath + "//input[@type='radio']"
            ))
        )
    except Exception:
        time.sleep(3)  # Fallback nếu wait không match

    # Thử điền form tối đa 3 lần để chống lỗi StaleElement (DOM bị ReactJS re-render)
    for retry in range(3):
        try:
            question_modal = driver.find_element(By.XPATH, dialog_xpath)

            text_inputs = question_modal.find_elements(
                By.XPATH, ".//textarea | .//input[@type='text'] | .//div[@role='textbox']"
            )
            choices = question_modal.find_elements(
                By.XPATH, ".//input[@type='checkbox'] | .//input[@type='radio']"
            )

            if not text_inputs and not choices:
                print(f"[{uid}] ⚠️ Chưa thấy ô nhập liệu, form đang tải... chờ thêm 3s.")
                time.sleep(3)
                text_inputs = question_modal.find_elements(
                    By.XPATH, ".//textarea | .//input[@type='text'] | .//div[@role='textbox']"
                )
                choices = question_modal.find_elements(
                    By.XPATH, ".//input[@type='checkbox'] | .//input[@type='radio']"
                )

            # 1. Điền "ok" vào tất cả các ô nhập text
            for ta in text_inputs:
                try:
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", ta)
                    if ta.tag_name == "div":
                        driver.execute_script("arguments[0].innerText = 'ok';", ta)
                    else:
                        ta.clear()
                        ta.send_keys("ok")
                except Exception:
                    pass

            # 2. Tích tất cả các ô checkbox hoặc radio chưa được chọn
            for cb in choices:
                try:
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", cb)
                    is_checked = (
                        cb.get_attribute("aria-checked") == "true"
                        or cb.get_attribute("checked")
                    )
                    if not is_checked:
                        driver.execute_script("arguments[0].click();", cb)
                except Exception:
                    pass

            time.sleep(1)

            # 3. Tìm và nhấn nút Gửi / Submit
            submit_xpath = (
                ".//div[@role='button' and ("
                "contains(@aria-label, 'Gửi') or contains(@aria-label, 'Submit')"
                " or contains(@aria-label, 'Xác nhận') or contains(@aria-label, 'Đồng ý')"
                " or contains(@aria-label, 'Tham gia')"
                ")]"
            )
            submit_buttons = question_modal.find_elements(By.XPATH, submit_xpath)

            if not submit_buttons:
                submit_buttons = question_modal.find_elements(
                    By.XPATH,
                    ".//div[@role='button' and ("
                    "contains(., 'Gửi') or contains(., 'Submit')"
                    " or contains(., 'Xác nhận') or contains(., 'Đồng ý')"
                    " or contains(., 'Tham gia')"
                    ")]"
                )

            submit_btn = next((btn for btn in submit_buttons if btn.is_displayed()), None)

            if not submit_btn:
                raise Exception("no such element")

            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", submit_btn)
            time.sleep(1)
            try:
                driver.execute_script("arguments[0].click();", submit_btn)
            except Exception:
                from selenium.webdriver.common.action_chains import ActionChains
                ActionChains(driver).move_to_element(submit_btn).click().perform()

            #print(f"[{uid}] ✅ Đã điền form và gửi yêu cầu tham gia nhóm riêng tư {group_id}!")
            break

        except Exception as inner_e:
            if "stale element reference" in str(inner_e).lower() and retry < 2:
                #print(f"[{uid}] 🔄 DOM re-render, thử lại ({retry+1}/3)...")
                time.sleep(2)
            elif "no such element" in str(inner_e).lower():
                if retry == 2:
                    print(f"[{uid}] ⚠️ Đã điền form nhưng không tìm thấy nút Gửi/Submit.")
                else:
                    time.sleep(2)
            else:
                raise inner_e


def _handle_public_group_after_join(driver, uid, group_id):
    """
    Xử lý sau khi click Join cho nhóm Công khai.

    Nhóm công khai có thể xuất hiện modal câu hỏi với cấu trúc:
      - Dialog dùng aria-modal="true" + aria-labelledby (KHÔNG có aria-label trực tiếp)
      - Textarea cần send_keys() để trigger React onChange (JS innerText sẽ KHÔNG kích hoạt)
      - Có 2 nút "Gửi": 1 ẩn (tabindex="-1"), 1 thật (tabindex="0") — chỉ click nút thật
      - Có nút "Lúc khác" để bỏ qua — không nhấn
    """
    # Modal nhóm công khai dùng aria-modal="true" (không có aria-label trên thẻ div gốc)
    dialog_xpath = "//div[@role='dialog' and @aria-modal='true']"

    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, dialog_xpath))
        )
    except Exception:
        # Không có modal → join thành công không cần điền form
        print(f"[{uid}] Tham gia nhóm công khai {group_id} thành công (không có form câu hỏi).")
        return

    # Chờ thêm để textarea xuất hiện
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, dialog_xpath + "//textarea"))
        )
    except Exception:
        # Không tìm thấy textarea → modal thông báo thành công, không có câu hỏi
        print(f"[{uid}] Tham gia nhóm công khai {group_id} thành công.")
        return

    for retry in range(3):
        try:
            modal = driver.find_element(By.XPATH, dialog_xpath)

            # Tìm textarea (nhóm công khai chủ yếu dùng <textarea> thuần)
            text_inputs = modal.find_elements(
                By.XPATH, ".//textarea | .//input[@type='text']"
            )

            # Điền bằng send_keys để React nhận onChange → nút Gửi mới enabled
            for ta in text_inputs:
                try:
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", ta)
                    ta.click()
                    ta.clear()
                    ta.send_keys("ok")
                except Exception:
                    pass

            time.sleep(1)

            # Tìm nút "Gửi" THẬT: tabindex="0" và không nằm trong div aria-hidden="true"
            # Facebook render 2 bản nút Gửi: 1 ẩn (tabindex="-1"), 1 thật (tabindex="0")
            submit_btn = None
            candidates = modal.find_elements(
                By.XPATH,
                ".//div[@role='button' and ("
                "contains(@aria-label,'Gửi') or contains(@aria-label,'Submit')"
                ") and @tabindex='0']"
            )
            for btn in candidates:
                # Loại bỏ nút nằm bên trong container aria-hidden
                hidden_ancestors = btn.find_elements(
                    By.XPATH, "ancestor::div[@aria-hidden='true']"
                )
                if not hidden_ancestors and btn.is_displayed():
                    submit_btn = btn
                    break

            if not submit_btn:
                raise Exception("no such element")

            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", submit_btn)
            time.sleep(1)
            try:
                driver.execute_script("arguments[0].click();", submit_btn)
            except Exception:
                from selenium.webdriver.common.action_chains import ActionChains
                ActionChains(driver).move_to_element(submit_btn).click().perform()

            #print(f"[{uid}] Đã điền câu hỏi và gửi yêu cầu tham gia nhóm công khai {group_id}.")
            break

        except Exception as inner_e:
            if "stale element reference" in str(inner_e).lower() and retry < 2:
                #print(f"[{uid}] 🔄 DOM re-render, thử lại ({retry+1}/3)...")
                time.sleep(2)
            elif "no such element" in str(inner_e).lower():
                if retry == 2:
                    print(f"[{uid}] ⚠️ Không tìm thấy nút Gửi cho nhóm công khai {group_id}.")
                else:
                    time.sleep(2)
            else:
                raise inner_e

def join_single_group(driver, wait, uid, group_id):
    """
    Thực hiện logic tham gia một nhóm cụ thể và xử lý popup câu hỏi nếu có.
    Trả về True nếu thành công hoặc đã tham gia, False nếu có lỗi.

    Dùng WebDriverWait local (45s) thay vì wait truyền vào để tránh timeout
    sớm khi nhiều luồng cùng truy cập một group (Facebook render chậm hơn).
    """
    # Tạo wait riêng với timeout dài hơn — tránh timeout do nhiều luồng cùng hit
    local_wait = WebDriverWait(driver, 45)

    try:
        group_url = f"https://www.facebook.com/{group_id}"
        #print(f"[{uid}] 🌐 Đang chuyển hướng đến nhóm: {group_url}")
        driver.get(group_url)

        # Chờ trình duyệt tải xong mã HTML cơ bản
        local_wait.until(lambda d: d.execute_script("return document.readyState") == "complete")

        # Thêm delay ngẫu nhiên nhỏ để các luồng không hit server cùng 1 thời điểm
        jitter = random.uniform(1.0, 3.5)
        time.sleep(jitter)

        # Kiểm tra trước xem đã join hoặc gửi yêu cầu chưa
        if _is_already_joined(driver):
            #print(f"[{uid}] ℹ️ Đã tham gia hoặc đã gửi yêu cầu nhóm {group_id} từ trước.")
            return True

        #print(f"[{uid}] 🔍 Đang tìm nút 'Tham gia nhóm' cho group {group_id}...")

        click_success = False

        for attempt in range(3):
            try:
                # Dùng XPath mở rộng để tìm nút (span lồng sâu, aria-label, text trực tiếp)
                # Sử dụng translate để không phân biệt hoa thường cho 'join group'
                join_btn_xpath_full = (
                    "//div[@aria-label='Tham gia nhóm' and @role='button']"
                    " | //div[contains(translate(@aria-label, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'join group') and @role='button']"
                    " | //span[text()='Tham gia nhóm']"
                    " | //span[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'join group')]"
                    " | //span[.//span[text()='Tham gia nhóm']]"
                    " | //span[.//span[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'join group')]]"
                    " | //a[contains(@href, 'join') and contains(., 'Tham gia nhóm')]"
                    " | //a[contains(@href, 'join') and contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'join group')]"
                )
                join_btn = local_wait.until(
                    EC.presence_of_element_located((By.XPATH, join_btn_xpath_full))
                )

                # Nếu tìm thấy span/a, leo lên div[role='button'] cha
                tag = join_btn.tag_name
                role = join_btn.get_attribute('role')
                if not (tag == 'div' and role == 'button'):
                    try:
                        join_btn = join_btn.find_element(By.XPATH, "ancestor::div[@role='button'][1]")
                    except Exception:
                        pass

                driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", join_btn)
                time.sleep(1.5)

                # Re-find để tránh stale element sau scroll
                join_btn = driver.find_element(By.XPATH, join_btn_xpath_full)
                tag = join_btn.tag_name
                role = join_btn.get_attribute('role')
                if not (tag == 'div' and role == 'button'):
                    try:
                        join_btn = join_btn.find_element(By.XPATH, "ancestor::div[@role='button'][1]")
                    except Exception:
                        pass

                # JS click (bypass overlay div vô hình)
                try:
                    driver.execute_script("arguments[0].click();", join_btn)
                    #print(f"[{uid}] ✅ Đã nhấn nút 'Tham gia nhóm' bằng JavaScript (Lần thử {attempt+1})!")
                    click_success = True
                    break
                except Exception as js_e:
                    #print(f"[{uid}] ⚠️ Click JS thất bại ({js_e}), thử ActionChains...")
                    from selenium.webdriver.common.action_chains import ActionChains
                    ActionChains(driver).move_to_element(join_btn).pause(0.5).click().perform()
                    #print(f"[{uid}] ✅ Đã nhấn nút 'Tham gia nhóm' bằng ActionChains (Lần thử {attempt+1})!")
                    click_success = True
                    break

            except Exception as e:
                err_str = str(e).lower()

                # Kiểm tra lại xem đã join chưa (có thể trang tải muộn)
                if _is_already_joined(driver):
                    #print(f"[{uid}] ℹ️ Đã tham gia hoặc đã gửi yêu cầu nhóm {group_id} (phát hiện sau timeout).")
                    return True

                if "stale element reference" in err_str or "not interactable" in err_str:
                    #print(f"[{uid}] 🔄 DOM thay đổi, đang thử lại ({attempt + 1}/3)...")
                    time.sleep(3)
                elif "timeout" in err_str and attempt < 2:
                    # Timeout — có thể do nhiều luồng cùng load: thử refresh + đợi thêm
                    #print(f"[{uid}] ⏱️ Timeout chờ nút, thử refresh trang (Lần {attempt + 1}/3)...")
                    driver.refresh()
                    local_wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
                    time.sleep(random.uniform(3.0, 6.0))
                else:
                    if attempt == 2:
                        print(f"[{uid}] ❌ Không tìm thấy nút tham gia cho group {group_id} sau 3 lần thử.")
                    break

        if not click_success:
            return False

        # ── Phân nhánh xử lý sau khi click Join theo loại nhóm ──────────────────
        group_type = _detect_group_privacy(driver)
        #print(f"[{uid}] 🔍 Loại nhóm {group_id}: {group_type}")

        try:
            if group_type == "private":
                # Nhóm Riêng tư: có thể có câu hỏi / nội quy cần trả lời
                _handle_private_group_modal(driver, uid, group_id)
            elif group_type == "public":
                # Nhóm Công khai: tham gia ngay, không có câu hỏi
                _handle_public_group_after_join(driver, uid, group_id)
            else:
                # Không xác định được loại → áp dụng logic chung (thử xử lý modal)
                #print(f"[{uid}] ❓ Không xác định loại nhóm, thử xử lý modal phòng trường hợp có câu hỏi...")
                _handle_private_group_modal(driver, uid, group_id)
        except Exception as e:
            print(f"[{uid}] ⚠️ Lỗi khi xử lý sau join nhóm {group_id} ({group_type}): {e}")

        return True

    except Exception as e:
        print(f"[{uid}] ❌ Lỗi không xác định khi xử lý group {group_id}: {e}")
        return False
