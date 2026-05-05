import json
import os

from flask import Flask
from db import init_db, insert_video, update_status
from telegram_bot import send_approval
from utils import require_api_key, logger   
from redis import Redis
from rq import Queue
from tasks import build_video
from ai_service import generate_script
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)

limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=["100 per day"]
)

# ✅ Init DB
init_db()

# ✅ Redis Queue
redis_url = os.getenv("REDIS_URL")
redis_conn = Redis.from_url(redis_url)
q = Queue(connection=redis_conn)

# 🔥 In-memory store (IMPORTANT)
video_store = {}


@app.route("/")
def home():
    logger.info("Home page accessed.")
    return "Running 🚀"


# 🚀 GENERATE
@app.route("/api/generate", methods=["POST"])
@require_api_key
def generate():
    logger.info("🚀 Scheduler triggered generate API")
    try:
        logger.info("📝 Calling generate_script() from OpenAI...")
        script_data = generate_script()
        
        if not script_data:
            logger.error("❌ Failed to generate script from OpenAI")
            return {"error": "Script generation failed - check OpenAI API key"}, 500
        
        preview_script = f"{script_data.get('hook','')} {script_data.get('english','')}"
        logger.info(f"✅ Script generated: {preview_script[:50]}...")

        # Save in DB (optional)
        vid = insert_video(str(script_data))

        # ✅ SAVE IN MEMORY (CRITICAL)
        video_store[vid] = script_data

        # Send Telegram
        q.enqueue(send_approval, vid, preview_script)

        logger.info(f"Enqueued Telegram approval for video {vid}")

        return {"status": "ok", "id": vid, "preview": preview_script}

    except Exception as e:
        logger.error(f"Error in /api/generate: {e}")
        return {"error": str(e)}, 500


# ✅ APPROVE
@app.route("/approve/<int:vid>")
@limiter.limit("10 per minute")
def approve(vid):
    logger.info(f"Approving video {vid}")

    update_status(vid, "approved")

    # 🔥 GET DATA FROM MEMORY
    script_data = video_store.get(vid)

    if not script_data:
        logger.error(f"No script data found for video {vid}")
        return {"error": "Data not found (app restarted?)"}, 500

    payload = {
        "id": vid,
        "scripts": video_store.get(vid)
    }

    q.enqueue(build_video, payload)

    return "Approved"


# ❌ REJECT
@app.route("/reject/<int:vid>")
@limiter.limit("10 per minute")
def reject(vid):
    logger.info(f"Video {vid} rejected.")
    update_status(vid, "rejected")
    return "Rejected"


# ❤️ HEALTH
@app.route("/health")
@limiter.limit("20 per minute")
def health():
    return {"status": "ok"}


# 🔑 CHECK OPENAI API KEY
@app.route("/check-openai-key")
@limiter.limit("20 per minute")
def check_openai_key():
    """Check if OpenAI API key is configured"""
    import os
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        logger.error("❌ OPENAI_API_KEY not configured")
        return {
            "status": "error",
            "message": "OPENAI_API_KEY environment variable is not set",
            "configured": False
        }, 500
    
    key_preview = f"{api_key[:8]}...{api_key[-4:]}" if len(api_key) > 12 else "***"
    logger.info(f"✅ OPENAI_API_KEY is configured: {key_preview}")
    
    return {
        "status": "ok",
        "message": "OpenAI API key is configured",
        "configured": True,
        "key_length": len(api_key),
        "key_preview": key_preview
    }


# 🧪 TEST
@app.route("/test")
def test():
    return {"status": "ok"}


# 🚀 RUN
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)