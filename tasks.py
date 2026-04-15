from db import update_status
import time
from utils import logger

def build_video(video_id):
    update_status(video_id, "building")

    try:
        # build video
        update_status(video_id, "built")

        # upload
        update_status(video_id, "uploading")

        # simulate upload
        update_status(video_id, "uploaded")

    except Exception as e:
        logger.error(f"Error occurred while building video {video_id}: {e}")    
        update_status(video_id, "failed")
