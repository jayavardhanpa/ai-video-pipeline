from db import update_status, get_video
from utils import logger
from pathlib import Path
import json

from gtts import gTTS
from moviepy.editor import TextClip, AudioFileClip

OUTPUT_DIR = Path("/tmp/videos")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def build_video(video_id):
    try:
        logger.info(f"Starting build for video {video_id}")

        update_status(video_id, "building")

        item = get_video(video_id)

        if not item:
            raise Exception("Video not found in DB")

        script_data = json.loads(item["script"])

        languages = {
            "telugu": "te",
            "hindi": "hi",
            "english": "en"
        }

        videos = []

        for lang, lang_code in languages.items():
            script = script_data.get(lang)

            if not script:
                continue

            vid_dir = OUTPUT_DIR / f"{video_id}_{lang}"
            vid_dir.mkdir(parents=True, exist_ok=True)

            audio_path = vid_dir / "audio.mp3"
            video_path = OUTPUT_DIR / f"{video_id}_{lang}.mp4"

            logger.info(f"Generating {lang} video...")

            # 🎤 Voice
            tts = gTTS(text=script, lang=lang_code)
            tts.save(str(audio_path))

            # 🎬 Video
            audio = AudioFileClip(str(audio_path))

            clip = TextClip(
                script[:400],
                fontsize=40,
                color='white',
                size=(720, 1280),
                method='caption'
            ).set_duration(audio.duration)

            video = clip.set_audio(audio)

            video.write_videofile(
                str(video_path),
                fps=24,
                codec="libx264",
                audio_codec="aac"
            )

            videos.append(str(video_path))

        update_status(video_id, "ready")

        logger.info(f"Completed video {video_id}")

        return videos

    except Exception as e:
        logger.error(f"Error building video {video_id}: {e}")
        update_status(video_id, "error")
        return None