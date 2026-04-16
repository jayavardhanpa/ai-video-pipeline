import requests
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def send_approval(video_id, script):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    text = f"🎬 Script:\n{script[:150]}...\n\nApprove?"

    keyboard = {
        "inline_keyboard": [[
            {"text": "✅ Approve", "url": f"{os.getenv('APP_URL')}/approve/{video_id}"},
            {"text": "❌ Reject", "url": f"{os.getenv('APP_URL')}/reject/{video_id}"}
        ]]
    }

    try:
        response = requests.post(
            url,
            json={
                "chat_id": CHAT_ID,
                "text": text,
                "reply_markup": keyboard
            },
            timeout=5   # 🔥 VERY IMPORTANT
        )

        print("Telegram response:", response.text)

    except Exception as e:
        print("Telegram error:", e)