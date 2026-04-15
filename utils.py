import os
from functools import wraps
from flask import request
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)
API_KEY = os.getenv("API_KEY")

def require_api_key(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        logger.info("Checking API key for incoming request...")
        if request.headers.get("Authorization") != f"Bearer {API_KEY}":
            logger.warning("Invalid API key provided.")
            return "Unauthorized", 401
        logger.info("API key is valid.")
        return f(*args, **kwargs)
    logger.info("API key authentication decorator created.")
    return wrapper