import os
from functools import wraps
from flask import request

API_KEY = os.getenv("API_KEY")

def require_api_key(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if request.headers.get("Authorization") != f"Bearer {API_KEY}":
            return "Unauthorized", 401
        return f(*args, **kwargs)
    return wrapper