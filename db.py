import sqlite3

DB_FILE = "videos.db"


def get_conn():
    return sqlite3.connect(DB_FILE)


# =========================
# INIT DB
# =========================
def init_db():

    conn = get_conn()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            status TEXT,
            script TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS video_analytics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id TEXT,
            channel TEXT,
            language TEXT,
            variant TEXT,
            youtube_video_id TEXT,
            views INTEGER DEFAULT 0,
            likes INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


# =========================
# VIDEO TABLE
# =========================
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


# =========================
# ANALYTICS TABLE
# =========================
def save_video_analytics(
    video_id,
    channel,
    language,
    variant,
    youtube_video_id
):

    conn = get_conn()

    cur = conn.cursor()

    cur.execute("""
    INSERT INTO video_analytics
    (
        video_id,
        channel,
        language,
        variant,
        youtube_video_id
    )
    VALUES (?, ?, ?, ?, ?)
    """, (
        video_id,
        channel,
        language,
        variant,
        youtube_video_id
    ))

    conn.commit()
    conn.close()


def update_video_analytics(
    youtube_video_id,
    views,
    likes
):

    conn = get_conn()

    conn.execute("""
    UPDATE video_analytics
    SET views=?, likes=?
    WHERE youtube_video_id=?
    """, (
        views,
        likes,
        youtube_video_id
    ))

    conn.commit()
    conn.close()


def get_top_variants():

    conn = get_conn()

    cur = conn.cursor()

    cur.execute("""
    SELECT
        channel,
        language,
        variant,
        SUM(views) as total_views,
        SUM(likes) as total_likes
    FROM video_analytics
    GROUP BY channel, language, variant
    ORDER BY total_views DESC
    """)

    rows = cur.fetchall()

    conn.close()

    return rows