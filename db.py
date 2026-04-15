import sqlite3
from utils import logger

def init_db():
    logger.info("Initializing database...")
    conn = sqlite3.connect("data.db")
    conn.execute("""
    CREATE TABLE IF NOT EXISTS videos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        script TEXT,
        status TEXT
    )
    """)
    conn.close()

def insert_video(script):
    logger.info("Inserting new video into database...")
    conn = sqlite3.connect("data.db")
    cur = conn.cursor()
    cur.execute("INSERT INTO videos (script, status) VALUES (?, ?)", (script, "pending"))
    vid = cur.lastrowid
    conn.commit()
    conn.close()
    return vid

def update_status(id, status):
    logger.info(f"Updating status for video {id}...")
    conn = sqlite3.connect("data.db")
    conn.execute("UPDATE videos SET status=? WHERE id=?", (status, id))
    conn.commit()
    conn.close()