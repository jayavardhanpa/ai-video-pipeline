from flask import Flask
from db import init_db, insert_video, update_status
from telegram_bot import send_approval
from utils import require_api_key
from redis import Redis
from rq import Queue
from tasks import build_video
import os

app = Flask(__name__)

init_db()

redis_conn = Redis()
q = Queue(connection=redis_conn)

@app.route("/")
def home():
    return "Running 🚀"

@app.route("/api/generate", methods=["POST"])
@require_api_key
def generate():
    script = "This is AI generated script"  # replace with LLM later

    vid = insert_video(script)

    send_approval(vid, script)

    return {"status": "sent for approval"}

@app.route("/approve/<int:vid>")
def approve(vid):
    update_status(vid, "approved")
    q.enqueue(build_video, vid)
    return "Approved"

@app.route("/reject/<int:vid>")
def reject(vid):
    update_status(vid, "rejected")
    return "Rejected"