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
            "english": "Discipline creates success",
            "telugu": "క్రమశిక్షణ విజయాన్ని తీసుకువస్తుంది",
            "hindi": "अनुशासन सफलता लाता है"
        }
    }

    videos = build_video(item, upload=False)

    if videos:
        preview(videos[0])