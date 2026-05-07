from googleapiclient.discovery import build

from youtube_service import load_credentials
from db import get_conn, update_video_analytics


def update_video_stats():

    conn = get_conn()

    cur = conn.cursor()

    cur.execute("""
    SELECT
        youtube_video_id,
        channel
    FROM video_analytics
    """)

    rows = cur.fetchall()

    conn.close()

    for row in rows:

        youtube_video_id = row[0]
        channel = row[1]

        try:

            # ✅ Load correct credentials per channel
            creds = load_credentials(channel)

            youtube = build(
                "youtube",
                "v3",
                credentials=creds
            )

            response = youtube.videos().list(
                part="statistics",
                id=youtube_video_id
            ).execute()

            items = response.get("items", [])

            if not items:
                continue

            stats = items[0]["statistics"]

            views = int(stats.get("viewCount", 0))
            likes = int(stats.get("likeCount", 0))

            update_video_analytics(
                youtube_video_id,
                views,
                likes
            )

            print(
                f"Updated {channel} | "
                f"{youtube_video_id} | "
                f"Views={views} Likes={likes}"
            )

        except Exception as e:

            print(
                f"Failed analytics for "
                f"{channel} - {youtube_video_id}: {e}"
            )