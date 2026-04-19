from utils import logger
from pathlib import Path
from gtts import gTTS
from db import update_status
from youtube_service import upload_video

from PIL import Image, ImageDraw, ImageFont
import numpy as np
from moviepy.editor import ImageClip

# ✅ Safe import
try:
    from moviepy.editor import AudioFileClip
    MOVIEPY_AVAILABLE = True
    logger.info("✅ moviepy loaded successfully")
except Exception as e:
    MOVIEPY_AVAILABLE = False
    logger.warning(f"moviepy not available: {e}")

OUTPUT_DIR = Path("/tmp/videos")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def build_video(item):
    try:
        if isinstance(item, int):
            logger.error(f"❌ Invalid payload: {item}")
            return

        video_id = item.get("id")
        script_data = item.get("scripts")

        if not script_data:
            logger.error(f"No script data for video {video_id}")
            return

        if not MOVIEPY_AVAILABLE:
            logger.error("MoviePy not available")
            update_status(video_id, "error")
            return

        logger.info(f"Starting build for video {video_id}")

        languages = {
            "telugu": "te",
            "hindi": "hi",
            "english": "en"
        }

        videos = []

        # 🔥 USE ONE FONT FOR EVERYTHING
        font_path = Path(__file__).parent / "assets/NotoSansTelugu-Bold.ttf"
        font = ImageFont.truetype(str(font_path), 110)

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
            gTTS(text=script, lang=lang_code).save(str(audio_path))

            audio = AudioFileClip(str(audio_path))

            # 🖼 Background
            img = Image.new("RGB", (720, 1280), color=(0, 0, 0))
            draw = ImageDraw.Draw(img)

            # ✍️ TEXT (SHORT & CLEAN)
            text = script.strip()
            words = text.split()

            # 🔥 FORCE 2 STRONG LINES
            line1 = " ".join(words[:3])
            line2 = " ".join(words[3:6])

            lines = [line1, line2]

            # 🎯 CENTER
            y_start = 550

            for i, line in enumerate(lines):
                bbox = draw.textbbox((0, 0), line, font=font)
                w = bbox[2] - bbox[0]

                x = (720 - w) // 2
                y = y_start + (i * 140)

                # Shadow
                draw.text((x+5, y+5), line, font=font, fill="black")

                # Main text
                draw.text((x, y), line, font=font, fill="white")

            # 🎬 Create video
            frame = np.array(img)
            clip = ImageClip(frame).set_duration(audio.duration)
            video = clip.set_audio(audio)

            video.write_videofile(
                str(video_path),
                fps=24,
                codec="libx264",
                audio_codec="aac"
            )

            videos.append(str(video_path))

        logger.info(f"✅ Completed video {video_id}")

        # 🚀 Upload ONLY ONE video
        if videos:
            video_file = videos[0]

            title = f"🔥 {script_data.get('english','')[:45]} #shorts"

            try:
                logger.info(f"📤 Uploading {video_file}")
                upload_video(video_file, title)
            except Exception as e:
                logger.error(f"YouTube upload failed: {e}")

        update_status(video_id, "ready")

        return videos

    except Exception as e:
        logger.error(f"❌ Error: {e}")
        update_status(video_id, "error")
        return None