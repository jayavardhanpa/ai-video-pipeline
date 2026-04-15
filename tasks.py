from db import update_status
import time

def build_video(video_id):
    print("Building video...")

    update_status(video_id, "building")

    time.sleep(5)  # simulate

    update_status(video_id, "uploading")

    time.sleep(3)

    update_status(video_id, "uploaded")

    print("Done")