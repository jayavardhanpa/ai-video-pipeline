import json
import os

from flask import Flask
from db import init_db, insert_video, update_status
from telegram_bot import send_approval
from utils import require_api_key, logger
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

# 🔥 In-memory store
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
            logger.error("❌ Failed to generate script")
            return {"error": "Script generation failed"}, 500

        preview_script = f"{script_data.get('hook_1', '')} {script_data.get('english', '')}"

        logger.info(f"✅ Script generated: {preview_script[:50]}...")

        # Save in DB
        vid = insert_video(str(script_data))

        # Save in memory
        video_store[vid] = script_data

        # ✅ DIRECT TELEGRAM CALL (NO REDIS)
        send_approval(vid, preview_script)

        logger.info(f"✅ Telegram approval sent for video {vid}")

        return {
            "status": "ok",
            "id": vid,
            "preview": preview_script
        }

    except Exception as e:
        logger.error(f"❌ Error in /api/generate: {e}")
        return {"error": str(e)}, 500


# ✅ APPROVE
@app.route("/approve/<int:vid>")
@limiter.limit("10 per minute")
def approve(vid):
    logger.info(f"Approving video {vid}")

    update_status(vid, "approved")

    script_data = video_store.get(vid)

    if not script_data:
        logger.error(f"❌ No script data found for video {vid}")
        return {"error": "Data not found (app restarted?)"}, 500

    payload = {
        "id": vid,
        "scripts": script_data
    }

    try:
        # ✅ DIRECT VIDEO BUILD (NO REDIS)
        build_video(payload)

        logger.info(f"✅ Video build completed for {vid}")

        return {"status": "approved"}

    except Exception as e:
        logger.error(f"❌ Build failed: {e}")
        update_status(vid, "error")

        return {"error": str(e)}, 500


# ❌ REJECT
@app.route("/reject/<int:vid>")
@limiter.limit("10 per minute")
def reject(vid):
    logger.info(f"Video {vid} rejected.")

    update_status(vid, "rejected")

    return {"status": "rejected"}


# ❤️ HEALTH
@app.route("/health")
@limiter.limit("20 per minute")
def health():
    return {"status": "ok"}


# 🔑 CHECK OPENAI KEY
@app.route("/check-openai-key")
@limiter.limit("20 per minute")
def check_openai_key():
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        logger.error("❌ OPENAI_API_KEY not configured")

        return {
            "status": "error",
            "configured": False
        }, 500

    return {
        "status": "ok",
        "configured": True,
        "key_length": len(api_key)
    }


# 🧪 TEST
@app.route("/test")
def test():
    return {"status": "ok"}


# 🚀 RUN
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)