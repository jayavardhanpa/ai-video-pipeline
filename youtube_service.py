import base64
import json
import os
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from utils import logger

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def load_credentials():
    logger.info("Decoding YouTube credentials from base64...")

    # Decode token.json
    token_b64 = os.getenv("YOUTUBE_TOKEN_B64")
    token_json = base64.b64decode(token_b64).decode("utf-8")
    logger.info(f"Token length: {len(token_b64)}")    
    creds_data = json.loads(token_json)

    creds = Credentials.from_authorized_user_info(creds_data, SCOPES)

    return creds


def get_youtube_service():
    creds = load_credentials()
    return build("youtube", "v3", credentials=creds)


def upload_video(file_path, title):
    logger.info(f"Uploading video: {file_path}")

    youtube = get_youtube_service()

    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": f"{title} | GitaJeevanam",
                "description": "Daily Bhagavad Gita wisdom 🙏",
                "tags": ["bhagavad gita", "krishna", "dharma"],
                "categoryId": "22"
            },
            "status": {
                "privacyStatus": "public"
            }
        },
        media_body=MediaFileUpload(file_path)
    )

    response = request.execute()

    logger.info(f"Upload complete: {response.get('id')}")

    return response