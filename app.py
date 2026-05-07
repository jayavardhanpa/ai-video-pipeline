import os

from flask import Flask, request
from db import init_db, insert_video, update_status
from telegram_bot import send_approval
from utils import require_api_key, logger
from tasks import build_video
from ai_service import generate_script
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from analytics_service import update_video_stats
from db import get_top_variants

app = Flask(__name__)

limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=["100 per day"]
)

init_db()

video_store = {}


@app.route("/")
def home():
    return "Running 🚀"


@app.route("/api/generate", methods=["POST"])
@require_api_key
def generate():

    try:
        channel = request.args.get("channel", "gita")

        logger.info(f"🚀 Generate triggered for channel: {channel}")

        script_data = generate_script(channel=channel)

        preview_script = f"{script_data.get('hook_1', '')} {script_data.get('english', '')}"

        vid = insert_video(str(script_data))

        video_store[vid] = {
            "channel": channel,
            "scripts": script_data
        }

        send_approval(vid, preview_script)

        return {
            "status": "ok",
            "id": vid,
            "channel": channel
        }

    except Exception as e:
        logger.error(f"❌ Generate error: {e}")
        return {"error": str(e)}, 500


@app.route("/approve/<int:vid>")
def approve(vid):

    update_status(vid, "approved")

    item = video_store.get(vid)

    if not item:
        return {"error": "Data not found"}, 500

    payload = {
        "id": vid,
        "channel": item["channel"],
        "scripts": item["scripts"]
    }

    build_video(payload)

    return {"status": "approved"}


@app.route("/reject/<int:vid>")
def reject(vid):
    update_status(vid, "rejected")
    return {"status": "rejected"}


@app.route("/health")
def health():
    return {"status": "ok"}

# ANALYTICS UPDATE
@app.route("/analytics/update")
def analytics_update():

    update_video_stats()

    return {"status": "updated"}

#Leader Board
@app.route("/analytics/top")
def analytics_top():

    rows = get_top_variants()

    return {
        "top_variants": rows
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)