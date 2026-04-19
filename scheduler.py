import os
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from db import insert_video
from telegram_bot import send_approval
from utils import logger


def scheduled_generate(q, video_store):
    """
    Runs on a schedule to automatically generate a video script,
    persist it to the database and in-memory store, then enqueue
    a Telegram approval message — identical to the /api/generate
    endpoint but triggered without an HTTP request.
    """
    logger.info("⏰ Scheduler: starting scheduled video generation")

    try:
        # 🔥 Replace with AI-generated script when ready
        script_data = {
            "telugu": "కర్మ చేయండి, ఫలితం గురించి ఆలోచించవద్దు. ఇది భగవద్గీతలోని గొప్ప బోధ.",
            "hindi": "कर्म करो, फल की चिंता मत करो। यह गीता का संदेश है।",
            "english": "Do your duty without worrying about results. This is the message of Bhagavad Gita."
        }

        preview_script = script_data.get("english", "")

        # Persist to database
        vid = insert_video(str(script_data))

        # Keep in memory so /approve can retrieve it later
        video_store[vid] = script_data

        # Enqueue Telegram approval message
        q.enqueue(send_approval, vid, preview_script)

        logger.info(f"⏰ Scheduler: enqueued Telegram approval for video {vid}")

    except Exception as e:
        logger.error(f"⏰ Scheduler: error during scheduled generation — {e}")


def start_scheduler(q, video_store, interval_hours=24):
    """
    Create and start a BackgroundScheduler that calls scheduled_generate
    every `interval_hours` hours.  Returns the running scheduler instance
    so the caller can shut it down cleanly if needed.
    """
    scheduler = BackgroundScheduler()

    scheduler.add_job(
        func=scheduled_generate,
        trigger=IntervalTrigger(hours=interval_hours),
        args=[q, video_store],
        id="scheduled_generate",
        name="Auto video generation",
        replace_existing=True,
    )

    scheduler.start()
    logger.info(
        f"⏰ Scheduler started — video generation will run every {interval_hours} hour(s)"
    )

    return scheduler
