import base64
import json
import os
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from utils import logger

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def load_credentials():
    token_b64 = os.getenv("YOUTUBE_TOKEN_B64")
    token_json = base64.b64decode(token_b64).decode("utf-8")
    creds_data = json.loads(token_json)
    return Credentials.from_authorized_user_info(creds_data, SCOPES)


def get_youtube_service():
    creds = load_credentials()
    return build("youtube", "v3", credentials=creds)


def upload_video(file_path, data, lang, variant):
    logger.info(f"Uploading video: {file_path}")

    youtube = get_youtube_service()

    if lang == "telugu":
        title = data.get("title_te")
        hashtags = data.get("hashtags_te", [])
    elif lang == "hindi":
        title = data.get("title_hi")
        hashtags = data.get("hashtags_hi", [])
    else:
        title = data.get("title_en")
        hashtags = data.get("hashtags_en", [])

    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": f"{title} ({variant})",
                "description": f"""
Daily Bhagavad Gita wisdom 🙏

{' '.join(hashtags)}
                """,
                "tags": hashtags,
                "categoryId": "22"
            },
            "status": {"privacyStatus": "public"}
        },
        media_body=MediaFileUpload(file_path)
    )

    response = request.execute()
    logger.info(f"Upload complete: {response.get('id')}")
    return response