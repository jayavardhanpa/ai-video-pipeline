from tasks import build_video
import os
import sys
import subprocess
from db import init_db

init_db()

def preview(video):
    print(f"Opening preview: {video}")
    if sys.platform == "win32":
        os.startfile(video)
    elif sys.platform == "darwin":
        subprocess.run(["open", video])
    else:
        subprocess.run(["xdg-open", video])

if __name__ == "__main__":
    init_db()

    item = {
        "id": 1,
        "scripts": {
            "hook": "Feeling lost in life?",
            "english": "...",
            "telugu": "...",
            "hindi": "...",

            "title_en": "...",
            "title_te": "...",
            "title_hi": "...",

            "hashtags_en": ["#shorts"],
            "hashtags_te": ["#shorts"],
            "hashtags_hi": ["#shorts"]
        }
    }

    videos = build_video(item, upload=False)

    if videos:
        preview(videos[0])