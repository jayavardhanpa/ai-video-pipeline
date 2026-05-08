import base64
import json
import os
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from utils import logger

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def load_credentials(channel="gita"):

    if channel == "ai_news":
        token_payload = os.getenv("YOUTUBE_AI_TOKEN_B64")
    else:
        token_payload = os.getenv("YOUTUBE_TOKEN_B64")

    if not token_payload:
        raise RuntimeError(
            f"Missing YouTube token environment variable for channel '{channel}'. "
            "Set YOUTUBE_AI_TOKEN_B64 or YOUTUBE_TOKEN_B64 with the base64-encoded token JSON."
        )

    creds_data = None
    try:
        decoded = base64.b64decode(token_payload).decode("utf-8")
        creds_data = json.loads(decoded)
    except Exception:
        try:
            creds_data = json.loads(token_payload)
        except Exception as exc:
            logger.error(
                "Unable to parse YouTube token payload. "
                "Ensure the env var is either base64-encoded JSON or raw JSON."
            )
            raise RuntimeError("Invalid YOUTUBE token payload") from exc

    if not isinstance(creds_data, dict):
        raise RuntimeError("YouTube credentials must be a JSON object")

    missing_keys = [
        key for key in ("refresh_token", "client_id", "client_secret", "token_uri")
        if key not in creds_data
    ]

    if missing_keys:
        logger.error(
            "YouTube token payload is missing required fields: %s. "
            "Payload keys: %s",
            missing_keys,
            list(creds_data.keys())
        )
        raise RuntimeError(
            "Invalid YouTube credentials: missing required refresh_token/client_id/client_secret/token_uri"
        )

    return Credentials.from_authorized_user_info(creds_data, SCOPES)


def get_youtube_service(channel="gita"):
    creds = load_credentials(channel)
    return build("youtube", "v3", credentials=creds)


def upload_video(file_path, data, lang, variant, channel="gita"):

    logger.info(f"Uploading video: {file_path}")

    youtube = get_youtube_service(channel)

    if lang == "telugu":
        title = data.get("title_te")
        hashtags = data.get("hashtags_te", [])
    elif lang == "hindi":
        title = data.get("title_hi")
        hashtags = data.get("hashtags_hi", [])
    else:
        title = data.get("title_en")
        hashtags = data.get("hashtags_en", [])

        # =========================
        # CHANNEL-BASED DESCRIPTION
        # =========================

        if channel == "gita":

            description = f"""
        Daily Bhagavad Gita wisdom for peace, clarity and self-growth.

        {' '.join(hashtags)}
            """

        else:

            description = f"""
        AI tools, productivity hacks and latest AI updates.

        {' '.join(hashtags)}
            """

        # =========================
        # YOUTUBE UPLOAD
        # =========================

        request = youtube.videos().insert(
            part="snippet,status",
            body={
                "snippet": {
                    "title": f"{title} #shorts",
                    "description": description,
                    "tags": hashtags,
                    "categoryId": "22"
                },
                "status": {
                    "privacyStatus": "public"
                }
            },
            media_body=MediaFileUpload(file_path)
        )

    response = request.execute()
    youtube_video_id = response.get("id")
    logger.info(f"Upload complete: {youtube_video_id}")

    return {
        "youtube_video_id": youtube_video_id
    }