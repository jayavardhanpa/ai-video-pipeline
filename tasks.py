from utils import logger
from pathlib import Path
import json
import moviepy
from gtts import gTTS
from db import update_status
from youtube_service import upload_video

# ✅ Import ONLY required modules (no TextClip)
try:
    from moviepy.editor import AudioFileClip, ColorClip
    MOVIEPY_AVAILABLE = True
    logger.info("✅ moviepy loaded successfully")
except (ImportError, ModuleNotFoundError) as _moviepy_err:
    MOVIEPY_AVAILABLE = False
    logger.warning(
        f"moviepy is not available — video building will be disabled. "
        f"Reason: {_moviepy_err}"
    )

OUTPUT_DIR = Path("/tmp/videos")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def build_video(item):
    try:
        # 🔥 HANDLE BOTH CASES
        if isinstance(item, int):
            logger.error(f"❌ Received int instead of payload: {item}")
            return

        video_id = item.get("id")
        script_data = item.get("scripts")

        if not script_data:
            logger.error(f"No script data for video {video_id}")
            return

        if not MOVIEPY_AVAILABLE:
            logger.error(
                f"Cannot build video {video_id}: moviepy not installed"
            )
            if video_id:
                update_status(video_id, "error")
            return None

        logger.info(f"Starting build for video {video_id}")

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

            logger.info(f"🎬 Generating {lang} video...")

            # 🎤 Voice
            tts = gTTS(text=script, lang=lang_code)
            tts.save(str(audio_path))

            # 🎧 Load audio
            audio = AudioFileClip(str(audio_path))

            # 🎬 Create simple background (NO ImageMagick)
            background = ColorClip(
                size=(720, 1280),
                color=(0, 0, 0)  # black background
            ).set_duration(audio.duration)

            # 🎥 Combine audio + background
            video = background.set_audio(audio)

            video.write_videofile(
                str(video_path),
                fps=24,
                codec="libx264",
                audio_codec="aac"
            )

            videos.append(str(video_path))

        logger.info(f"✅ Completed video {video_id}")

        # 🚀 Upload videos to YouTube
        for video_file in videos:
            try:
                logger.info(f"📤 Uploading {video_file} to YouTube...")

                upload_video(
                    video_file,
                    f"Bhagavad Gita Wisdom | GitaJeevanam"
                )

            except Exception as e:
                logger.error(f"YouTube upload failed: {e}")    
        if video_id:
            update_status(video_id, "ready")

        return videos

    except Exception as e:
        logger.error(f"❌ Error building video: {e}")
        if video_id:
            update_status(video_id, "error")
        return None