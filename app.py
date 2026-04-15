from flask import Flask
from db import init_db, insert_video, update_status
from telegram_bot import send_approval
from utils import require_api_key, logger   
from redis import Redis
from rq import Queue
from tasks import build_video
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(get_remote_address, app=app)  
import os

app = Flask(__name__)

init_db()

redis_conn = Redis()
q = Queue(connection=redis_conn)

@app.route("/")
def home():
    logger.info("Home page accessed.")
    return "Running 🚀"

@app.route("/api/generate", methods=["POST"])
@limiter.limit("5 per hour")
@require_api_key
def generate():
    logger.info("Received request to generate video...")
    script = "This is AI generated script"  # replace with LLM later

    vid = insert_video(script)

    send_approval(vid, script)

    return {"status": "sent for approval"}

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