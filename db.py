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

def get_video(id):
    logger.info(f"Fetching video {id} from database...")
    conn = sqlite3.connect("data.db")
    cur = conn.cursor()

    cur.execute("SELECT id, script, status FROM videos WHERE id=?", (id,))
    row = cur.fetchone()

    conn.close()

    if not row:
        logger.warning(f"Video {id} not found.")
        return None

    return {
        "id": row[0],
        "script": row[1],
        "status": row[2]
    }