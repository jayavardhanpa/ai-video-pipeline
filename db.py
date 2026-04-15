import sqlite3

def init_db():
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
    conn = sqlite3.connect("data.db")
    cur = conn.cursor()
    cur.execute("INSERT INTO videos (script, status) VALUES (?, ?)", (script, "pending"))
    vid = cur.lastrowid
    conn.commit()
    conn.close()
    return vid

def update_status(id, status):
    conn = sqlite3.connect("data.db")
    conn.execute("UPDATE videos SET status=? WHERE id=?", (status, id))
    conn.commit()
    conn.close()