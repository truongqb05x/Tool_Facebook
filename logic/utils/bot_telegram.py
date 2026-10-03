import requests
import json
import os

def send_telegram_message(text):
    """
    Gửi thông báo Telegram sử dụng cấu hình từ settings.json
    """
    try:
        # Đọc cấu hình từ settings.json (nằm ở thư mục cha của Logic)
        settings_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "settings.json")
        if not os.path.exists(settings_path):
            return False

        with open(settings_path, "r", encoding="utf-8") as f:
            settings = json.load(f)

        bot_token = settings.get("telegramBotToken", "").strip()
        chat_id = settings.get("telegramChatId", "").strip()

        if not bot_token or not chat_id:
            return False

        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        response = requests.post(
            url,
            data={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "HTML"
            },
            timeout=10
        )
        return response.status_code == 200
    except Exception as e:
        print(f"Lỗi khi gửi thông báo Telegram: {e}")
        return False