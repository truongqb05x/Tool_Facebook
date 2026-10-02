# file_utils.py
import json
import os
def read_file(path):
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            return [l.strip() for l in f if l.strip()]
    except:
        return []

def write_file(path, lines):
    with open(path, "w", encoding="utf-8") as f:
        for l in lines:
            f.write(l + "\n")

def append_file(path, line):
    with open(path, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def get_valid_tokens_from_accounts(accounts_path):
    import json
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
    return valid_tokens

def remove_token_from_accounts(accounts_path, uid):
    import json
    try:
        with open(accounts_path, 'r', encoding='utf-8') as f:
            accounts_data = json.load(f)
            
        modified = False
        for acc in accounts_data.get("Accounts", []):
            if acc.get("Uid") == uid:
                acc["Token"] = ""
                modified = True
                
        if modified:
            with open(accounts_path, 'w', encoding='utf-8') as fw:
                json.dump(accounts_data, fw, ensure_ascii=False, indent=2)
    except:
        pass

def update_account_cookie(uid, cookie_str):
    # accounts.json is usually at the base directory, same level as the exe
    # Since python scripts run in `Logic`, base directory is `..`
    accounts_path = os.path.join(os.path.dirname(os.getcwd()), "accounts.json")
    if not os.path.exists(accounts_path):
        return

    try:
        with open(accounts_path, 'r', encoding='utf-8') as f:
            app_data = json.load(f)
            
        modified = False
        accounts = app_data.get("Accounts", [])
        for acc in accounts:
            if acc.get("Uid") == uid:
                acc["Cookie"] = cookie_str
                modified = True
                break
                
        if modified:
            with open(accounts_path, 'w', encoding='utf-8') as fw:
                json.dump(app_data, fw, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[{uid}] Lỗi khi cập nhật cookie vào accounts.json: {e}")
