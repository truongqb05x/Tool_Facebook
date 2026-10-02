# file_utils.py

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
