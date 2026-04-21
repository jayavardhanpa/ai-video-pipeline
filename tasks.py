from utils import logger
from pathlib import Path
from gtts import gTTS
from db import update_status
from youtube_service import upload_video

from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np
import random
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

# 🎯 Fonts
FONT_MAP = {
    "telugu": "assets/NotoSansTelugu-Bold.ttf",
    "hindi": "assets/NotoSansDevanagari-Bold.ttf",
    "english": "assets/NotoSans-Bold.ttf"
}


# 🔥 Improved font scaling
def get_font(lang, text):
    font_path = Path(__file__).parent / FONT_MAP.get(lang)

    base_size = 105 if lang == "telugu" else 85

    if len(text) > 100:
        base_size -= 30
    elif len(text) > 70:
        base_size -= 20
    elif len(text) > 40:
        base_size -= 10

    return ImageFont.truetype(str(font_path), base_size)


# 🔥 FINAL wrap logic (no word cutting)
def wrap_text(draw, text, font, max_width_px):
    words = text.split()
    lines = []
    current = ""

    for word in words:
        test = current + (" " if current else "") + word
        bbox = draw.textbbox((0, 0), test, font=font)
        width = bbox[2] - bbox[0]

        if width <= max_width_px:
            current = test
        else:
            lines.append(current)
            current = word

    if current:
        lines.append(current)

    return lines[:2]


# 🔥 Clean AI text
def clean_text(text):
    text = text.replace(" ,", "").replace(", ", "")
    text = text.replace("  ", " ")
    text = text.replace(" .", ".")
    return text.strip()


# 🎨 Background loader
def get_background():
    bg_dir = Path(__file__).parent / "assets/backgrounds"
    images = list(bg_dir.glob("*.jpg"))

    if not images:
        return Image.new("RGB", (720, 1280), (10, 10, 10))

    img_path = random.choice(images)

    img = Image.open(img_path).convert("RGB")
    img = img.resize((720, 1280))

    img = img.filter(ImageFilter.GaussianBlur(6))

    overlay = Image.new("RGB", (720, 1280), (0, 0, 0))
    img = Image.blend(img, overlay, 0.4)

    return img


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

        logger.info(f"🚀 Starting build for video {video_id}")

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
            gTTS(text=script, lang=lang_code).save(str(audio_path))
            audio = AudioFileClip(str(audio_path))

            # 🖼 Background
            img = get_background()
            draw = ImageDraw.Draw(img)

            # ✍️ Text processing
            text = clean_text(script)
            
            font = get_font(lang, text)
            lines = wrap_text(draw, text, font, 600)

            # 🔥 Measure text block
            line_heights = []
            line_widths = []

            for line in lines:
                bbox = draw.textbbox((0, 0), line, font=font)
                w = bbox[2] - bbox[0]
                h = bbox[3] - bbox[1]
                line_widths.append(w)
                line_heights.append(h)

            total_height = sum(line_heights) + (len(lines) - 1) * 40

            # 🔥 Center vertically
            y = (1280 - total_height) // 2

            for i, line in enumerate(lines):
                w = line_widths[i]
                h = line_heights[i]

                x = (720 - w) // 2

                # Shadow
                draw.text((x + 4, y + 4), line, font=font, fill="black")

                # Main text
                draw.text((x, y), line, font=font, fill=(255, 255, 255))

                y += h + 25

            # 🎬 Convert to video
            frame = np.array(img)

            clip = ImageClip(frame)\
                .set_duration(audio.duration)\
                .resize(lambda t: 1 + 0.05 * t)

            video = clip.set_audio(audio)

            video.write_videofile(
                str(video_path),
                fps=24,
                codec="libx264",
                audio_codec="aac",
                verbose=False,
                logger=None
            )

            videos.append(str(video_path))

        logger.info(f"✅ Completed video {video_id}")

        # 🚀 Upload first video
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