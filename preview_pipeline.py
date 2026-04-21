import os
import sys
import subprocess
import random
from pathlib import Path

from gtts import gTTS
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np
from moviepy.editor import ImageClip, AudioFileClip

if not hasattr(Image, "ANTIALIAS"):
    Image.ANTIALIAS = Image.Resampling.LANCZOS

# ==============================
# CONFIG
# ==============================
OUTPUT_DIR = Path("./output")
OUTPUT_DIR.mkdir(exist_ok=True)

ASSETS_DIR = Path("./assets")

FONT_MAP = {
    "telugu": ASSETS_DIR / "NotoSansTelugu-Bold.ttf",
    "hindi": ASSETS_DIR / "NotoSansDevanagari-Bold.ttf",
    "english": ASSETS_DIR / "NotoSans-Bold.ttf"
}

PROXY_ENV_VARS = [
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "ALL_PROXY",
    "http_proxy",
    "https_proxy",
    "all_proxy",
]

# ==============================
# PREVIEW HELPER
# ==============================
def preview_video(video_path):
    print(f"Opening preview: {video_path}")

    if sys.platform == "win32":
        os.startfile(video_path)
    elif sys.platform == "darwin":
        subprocess.run(["open", video_path])
    else:
        subprocess.run(["xdg-open", video_path])


def disable_proxies_for_tts():
    for env_var in PROXY_ENV_VARS:
        os.environ.pop(env_var, None)


# ==============================
# FONT HANDLING
# ==============================
def get_font(lang, text):
    font_path = FONT_MAP[lang]

    size = 100 if lang != "english" else 90

    if len(text) > 80:
        size -= 20
    elif len(text) > 50:
        size -= 10

    return ImageFont.truetype(str(font_path), size)


# ==============================
# TEXT WRAP
# ==============================
def wrap_text(draw, text, font, max_width):
    lines = []
    current = ""

    for char in text:
        test = current + char
        bbox = draw.textbbox((0, 0), test, font=font)
        width = bbox[2] - bbox[0]

        if width <= max_width:
            current = test
        else:
            lines.append(current.strip())
            current = char

    if current:
        lines.append(current.strip())

    return lines[:2]


# ==============================
# BACKGROUND LOADER
# ==============================
def get_background():
    bg_dir = ASSETS_DIR / "backgrounds"
    images = list(bg_dir.glob("*.jpg"))

    if not images:
        return Image.new("RGB", (720, 1280), (10, 10, 10))

    img_path = random.choice(images)

    img = Image.open(img_path).convert("RGB")
    img = img.resize((720, 1280))

    # Blur + overlay
    img = img.filter(ImageFilter.GaussianBlur(6))
    overlay = Image.new("RGB", (720, 1280), (0, 0, 0))
    img = Image.blend(img, overlay, 0.4)

    return img


# ==============================
# VIDEO BUILDER
# ==============================
def build_video(item):
    video_id = item["id"]
    scripts = item["scripts"]

    languages = {
        "english": "en",
        "telugu": "te",
        "hindi": "hi"
    }

    outputs = []

    for lang, code in languages.items():
        text = scripts.get(lang)
        if not text:
            continue

        print(f"Generating {lang}...")

        # Paths
        audio_path = OUTPUT_DIR / f"{video_id}_{lang}.mp3"
        video_path = OUTPUT_DIR / f"{video_id}_{lang}.mp4"

        # Generate audio
        disable_proxies_for_tts()
        gTTS(text=text, lang=code).save(str(audio_path))
        audio = AudioFileClip(str(audio_path))

        # Background
        img = get_background()
        draw = ImageDraw.Draw(img)

        # Text
        font = get_font(lang, text)
        lines = wrap_text(draw, text, font, 600)

        line_heights = []
        line_widths = []

        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            w = bbox[2] - bbox[0]
            h = bbox[3] - bbox[1]
            line_widths.append(w)
            line_heights.append(h)

        total_height = sum(line_heights) + (len(lines) - 1) * 30

        y = (1280 - total_height) // 2

        for i, line in enumerate(lines):
            w = line_widths[i]
            h = line_heights[i]

            x = (720 - w) // 2

            draw.text((x + 4, y + 4), line, font=font, fill="black")
            draw.text((x, y), line, font=font, fill="white")

            y += h + 30

        frame = np.array(img)

        # Zoom animation
        clip = ImageClip(frame)\
            .set_duration(audio.duration)\
            .resize(lambda t: 1 + 0.05 * t)

        video = clip.set_audio(audio)

        # FAST RENDER
        video.write_videofile(
            str(video_path),
            fps=15,
            preset="ultrafast",
            codec="libx264",
            audio_codec="aac",
            verbose=False,
            logger=None
        )

        outputs.append(video_path)

    return outputs


# ==============================
# TEST RUN
# ==============================
if __name__ == "__main__":
    test_item = {
        "id": "preview1",
        "scripts": {
            "english": "Discipline creates success",
            "telugu": "క్రమశిక్షణ విజయాన్ని తీసుకువస్తుంది",
            "hindi": "अनुशासन सफलता लाता है"
        }
    }

    videos = build_video(test_item)

    if videos:
        preview_video(videos[0])
