from flask import Flask
from ai_service import generate_script
from db import init_db, insert_video, update_status
from telegram_bot import send_approval
from utils import require_api_key, logger   
from redis import Redis
from rq import Queue
from tasks import build_video
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

import os

app = Flask(__name__)

limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=["100 per day"]
) 

init_db()

redis_url = os.getenv("REDIS_URL")
redis_conn = Redis.from_url(redis_url)
q = Queue(connection=redis_conn)

@app.route("/")
def home():
    logger.info("Home page accessed.")
    return "Running 🚀"

@app.route("/api/generate", methods=["POST"])
@require_api_key
def generate():
    try:
        from ai_service import generate_script

        # script_data = generate_script()
        script_data = {
    "telugu": "కర్మ చేయండి, ఫలితం గురించి ఆలోచించవద్దు. ఇది భగవద్గీతలోని గొప్ప బోధ.",
    "hindi": "कर्म करो, फल की चिंता मत करो। यह गीता का संदेश है।",
    "english": "Do your duty without worrying about results. This is the message of Bhagavad Gita."
        }

        # Save English as preview for Telegram
        preview_script = script_data.get("english", "")

        vid = insert_video(str(script_data)) 

        # ✅ Move to background
        q.enqueue(send_approval, vid, preview_script)
        logger.info(f"Enqueued Telegram approval for video {vid}")
        return {"status": "ok", "id": vid}

    except Exception as e:
        logger.error(f"Error in /api/generate: {e}")
        return {"error": str(e)}, 500

@app.route("/approve/<int:vid>")
@limiter.limit("10 per minute")
def approve(vid):
    logger.info(f"Video {vid} approved. Enqueuing build task...")
    update_status(vid, "approved")
    q.enqueue(build_video, vid)
    return "Approved"

@app.route("/reject/<int:vid>")
@limiter.limit("10 per minute")
def reject(vid):
    logger.info(f"Video {vid} rejected.")
    update_status(vid, "rejected")
    return "Rejected"

@app.route("/health")
@limiter.limit("20 per minute")
def health():
    logger.info("Health check requested.")
    return {"status": "ok"}

@app.route("/test")
def test():
    return {"status": "ok"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)