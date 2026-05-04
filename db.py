import sqlite3

DB_FILE = "videos.db"

def get_conn():
    return sqlite3.connect(DB_FILE)


def init_db():
    conn = get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            status TEXT,
            script TEXT
        )
    """)
    conn.commit()
    conn.close()


def insert_video(script):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO videos (status, script) VALUES (?, ?)",
        ("pending", script)
    )
    conn.commit()
    vid = cur.lastrowid
    conn.close()
    return vid


def update_status(id, status):
    conn = get_conn()
    conn.execute(
        "UPDATE videos SET status=? WHERE id=?",
        (status, id)
    )
    conn.commit()
    conn.close()