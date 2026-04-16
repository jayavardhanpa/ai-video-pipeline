
from utils import logger
from pathlib import Path
import json
import moviepy
logger.info("✅ moviepy loaded successfully")
from gtts import gTTS

OUTPUT_DIR = Path("/tmp/videos")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def build_video(item):
    try:
        # 🔥 HANDLE BOTH CASES (important)
        if isinstance(item, int):
            logger.error(f"❌ Received int instead of payload: {item}")
            return

        video_id = item.get("id")
        script_data = item.get("scripts")

        if not script_data:
            logger.error(f"No script data for video {video_id}")
            return

        logger.info(f"Starting build for video {video_id}")

        languages = {
            "telugu": "te",
            "hindi": "hi",
            "english": "en"
        }

        from pathlib import Path
        from gtts import gTTS
        from moviepy.editor import TextClip, AudioFileClip

        OUTPUT_DIR = Path("/tmp/videos")
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

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

        logger.info(f"Completed video {video_id}")

        return videos

    except Exception as e:
        logger.error(f"Error building video: {e}")
        return None