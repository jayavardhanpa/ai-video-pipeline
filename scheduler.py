import os
import requests
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from utils import logger

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
API_KEY = os.getenv("API_KEY", "")
BASE_URL = os.getenv("BASE_URL", "http://localhost:8080")


def trigger_generate():
    """Call the /api/generate endpoint to kick off a new video generation."""
    url = f"{BASE_URL}/api/generate"
    headers = {"X-API-KEY": API_KEY}
    try:
        logger.info("⏰ Scheduler firing — calling /api/generate ...")
        response = requests.post(url, headers=headers, timeout=30)
        logger.info(f"✅ /api/generate responded: {response.status_code} — {response.text}")
    except Exception as e:
        logger.error(f"❌ Scheduler failed to call /api/generate: {e}")


if __name__ == "__main__":
    scheduler = BlockingScheduler()

    # -----------------------------------------------------------------------
    # Schedule: daily at 6:00 AM IST (Asia/Kolkata)
    # Equivalent to 00:30 UTC.
    # -----------------------------------------------------------------------
    scheduler.add_job(
        trigger_generate,
        trigger=CronTrigger(
            hour=6,
            minute=0,
            timezone="Asia/Kolkata",
        ),
        id="daily_generate",
        name="Daily video generation at 6:00 AM IST",
        replace_existing=True,
    )

    logger.info("🗓  Scheduler started — job will run daily at 6:00 AM IST (00:30 UTC).")
    scheduler.start()
