from utils import logger
from pathlib import Path
import json
import moviepy
from gtts import gTTS
from db import update_status
from youtube_service import upload_video
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from moviepy.editor import ImageClip


# ✅ Import ONLY required modules (no TextClip)
try:
    from moviepy.editor import AudioFileClip
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
            # 🎧 Load audio
            audio = AudioFileClip(str(audio_path))

            # 🖼 Create image
            img = Image.new("RGB", (720, 1280), color=(0, 0, 0))
            draw = ImageDraw.Draw(img)

            # 🔥 BIG FONT (mobile optimized)
            try:
                font = ImageFont.truetype("DejaVuSans-Bold.ttf", 90)
            except:
                font = ImageFont.load_default()

            # ✍️ BETTER TEXT HANDLING
            import textwrap

            text = script.strip()

            # 🔥 Smart wrapping (works for Telugu/Hindi/English)
            if lang == "english":
                lines = textwrap.wrap(text, width=18)
            else:
                # Telugu/Hindi safer split
                words = text.split()
                lines = []
                line = ""

                for word in words:
                    if len(line + " " + word) < 20:
                        line += " " + word
                    else:
                        lines.append(line.strip())
                        line = word

                if line:
                    lines.append(line)

            # 🔥 Limit to max 3 lines (VERY IMPORTANT)
            lines = lines[:3]

            # 🎯 Safe center zone
            total_height = len(lines) * 120
            y_start = (1280 - total_height) // 2
            y_start = max(350, y_start)

            for i, line in enumerate(lines):
                bbox = draw.textbbox((0, 0), line, font=font)
                w = bbox[2] - bbox[0]

                x = (720 - w) // 2
                y = y_start + (i * 120)

                # ✨ Shadow (premium look)
                draw.text((x+3, y+3), line, font=font, fill="black")

                # ✨ Main text
                draw.text((x, y), line, font=font, fill="white")

            # 🎬 Convert to video
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

        # 🚀 Upload videos to YouTube ( MULTIPLE - Commented due to the limit)
        # for video_file in videos:
        #     try:
        #         logger.info(f"📤 Uploading {video_file} to YouTube...")

        #         upload_video(
        #             video_file,
        #             f"Bhagavad Gita Wisdom | GitaJeevanam"
        #         )

        #     except Exception as e:
        #         logger.error(f"YouTube upload failed: {e}") 

        ## Remove below snippet if you want to upload all language videos. Currently uploading only English due to YouTube limits.
        video_file = videos[0]   # 🔥 only 1 video

        logger.info(f"📤 Uploading {video_file} to YouTube...")

        title = f"🔥 {script_data.get('english', '')[:45]} #shorts"
        
        upload_video(video_file, title)   
        ##
        if video_id:
            update_status(video_id, "ready")

        return videos

    except Exception as e:
        logger.error(f"❌ Error building video: {e}")
        if video_id:
            update_status(video_id, "error")
        return None