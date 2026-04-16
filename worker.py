from rq import Worker, Queue
from redis import Redis
from utils import logger
import os

# 🔥 ADD THIS
from db import init_db

listen = ['default']

redis_url = os.getenv("REDIS_URL")
redis_conn = Redis.from_url(redis_url)

if __name__ == "__main__":
    logger.info("Starting worker...")

    # 🔥 IMPORTANT: Initialize DB
    init_db()

    logger.info("Database initialized in worker.")

    worker = Worker([Queue(name, connection=redis_conn) for name in listen])
    worker.work()