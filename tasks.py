from utils import logger
from pathlib import Path
from gtts import gTTS
import pyttsx3
from db import update_status
from youtube_service import upload_video
import subprocess
import random
import tempfile
import os
import shutil
import re
from db import save_video_analytics

OUTPUT_DIR = Path(tempfile.gettempdir()) / "ai_videos"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

ASSETS_DIR = Path("assets")
BG_DIR = ASSETS_DIR / "backgrounds"
FONT_DIR = ASSETS_DIR

TEMP_FONT_DIR = Path(tempfile.gettempdir()) / "ai_fonts"
TEMP_FONT_DIR.mkdir(parents=True, exist_ok=True)


def setup_fonts():
    if not any(TEMP_FONT_DIR.glob("*.ttf")):
        for font_file in FONT_DIR.glob("*.ttf"):
            shutil.copy(font_file, TEMP_FONT_DIR / font_file.name)
        logger.info(f"✅ Fonts copied to {TEMP_FONT_DIR}")


def get_background():
    images = list(BG_DIR.glob("*.jpg"))
    return str(random.choice(images)) if images else None


def font_for_lang(lang: str) -> str:
    return {
        "telugu": "Noto Sans Telugu",
        "hindi": "Noto Sans Devanagari",
        "english": "Noto Sans",
    }.get(lang, "Noto Sans")


def escape_ass_text(text: str) -> str:
    return text.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")


def ffmpeg_filter_path(path: str) -> str:
    safe_path = path.replace('\\', '/').replace("'", "\\'")
    return safe_path.replace(':', '\\:')


def create_ass_subtitle(text: str, out_path: Path, font_name: str):
    safe_text = escape_ass_text(text)
    ass = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 720
PlayResY: 1280
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,OutlineColour,BackColour,Bold,Italic,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Default,{font_name},60,&H00FFFFFF,&H00000000,&H64000000,1,0,1,3,0,2,40,40,80,1

[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
Dialogue: 0,0:00:00.00,9:59:59.00,Default,,0,0,0,,{safe_text}
"""
    out_path.write_text(ass, encoding="utf-8")


def generate_audio(text: str, audio_path: Path, lang: str, code: str):
    if lang == "english":
        try:
            engine = pyttsx3.init()
            engine.save_to_file(text, str(audio_path))
            engine.runAndWait()
            return
        except Exception as e:
            logger.warning(
                f"⚠️ pyttsx3 failed for english TTS, falling back to gTTS: {e}"
            )

    gTTS(text=text, lang=code).save(str(audio_path))


def build_video(item, upload=True):
    try:
        setup_fonts()

        video_id = item.get("id")
        scripts = item.get("scripts")

        if not scripts:
            logger.error("No script data")
            return

        videos = []

        channel = item.get("channel", "gita")

        if channel == "ai_news":
            languages = {
                "english": "en"
            }
        else:
            languages = {
                "english": "en",
                "telugu": "te",
                "hindi": "hi"
            }

        for lang, code in languages.items():

            hooks = [scripts.get("hook_1"), scripts.get("hook_2")]
            main_text = scripts.get(lang, "")

            for idx, hook in enumerate(hooks):
                if not hook or not main_text:
                    continue

                variant = f"v{idx+1}"
                text = f"{hook}\n\n{main_text}"

                logger.info(f"🎬 Generating {lang} - {variant}")

                vid_dir = OUTPUT_DIR / f"{video_id}_{lang}_{variant}"
                vid_dir.mkdir(parents=True, exist_ok=True)

                audio_path = vid_dir / "audio.mp3"
                video_path = OUTPUT_DIR / f"{video_id}_{lang}_{variant}.mp4"
                ass_path = vid_dir / "sub.ass"

                # 🔊 AUDIO
                try:
                    generate_audio(text, audio_path, lang, code)

                    duration = get_audio_duration(str(audio_path))
                    logger.info(f"✅ Audio generated for {lang}-{variant}: {duration}s")

                except Exception as e:
                    logger.error(f"❌ Failed to generate audio for {lang}-{variant}: {e}")
                    continue

                # 📝 SUBTITLE
                create_ass_subtitle(text, ass_path, font_for_lang(lang))

                # 🖼 BACKGROUND
                bg = get_background()
                if not bg:
                    logger.error("No background images found")
                    return

                ffmpeg_exe = "ffmpeg"
                bg_abs = str(Path(bg).absolute()).replace('\\', '/')
                ass_abs = ffmpeg_filter_path(str(ass_path.absolute()))
                audio_abs = str(audio_path.absolute()).replace('\\', '/')
                video_abs = str(video_path.absolute()).replace('\\', '/')
                fonts_dir = ffmpeg_filter_path(str(TEMP_FONT_DIR.absolute()))

                filter_str = f"scale=720:1280,subtitles='{ass_abs}':fontsdir='{fonts_dir}'"

                cmd = [
                    ffmpeg_exe,
                    "-y",
                    "-loop", "1",
                    "-i", bg_abs,
                    "-i", audio_abs,
                    "-vf", filter_str,
                    "-af", "volume=2.0",
                    "-c:v", "libx264",
                    "-preset", "medium",
                    "-tune", "stillimage",
                    "-c:a", "aac",
                    "-shortest",
                    "-pix_fmt", "yuv420p",
                    video_abs
                ]

                logger.info(f"📹 FFmpeg command: {' '.join(cmd)}")
                subprocess.run(cmd, check=True)

                logger.info(f"✅ Video created: {video_path}")
                videos.append((str(video_path), lang, variant))

        logger.info(f"✅ Completed video {video_id}")

        upload_success = True

        if videos and upload:
            for video_path, lang, variant in videos:
                try:
                    title_key = f"title_{'en' if lang=='english' else 'te' if lang=='telugu' else 'hi'}"
                    if not scripts.get(title_key):
                        logger.warning(f"⚠️ Missing title for {lang}")

                    upload_result = upload_video(
                        video_path,
                        scripts,
                        lang,
                        variant,
                        channel
                    )
                    
                    save_video_analytics(
                        video_id=video_id,
                        channel=channel,
                        language=lang,
                        variant=variant,
                        youtube_video_id=upload_result["youtube_video_id"]
                    )
                    
                    logger.info(f"✅ Uploaded {lang}-{variant}")

                except Exception as e:
                    logger.error(f"❌ Upload failed for {lang}-{variant}: {e}")
                    upload_success = False

            update_status(video_id, "completed" if upload_success else "partial")
        else:
            update_status(video_id, "completed")

        return videos

    except Exception as e:
        logger.error(f"❌ Error: {e}")
        try:
            update_status(video_id, "error")
        except:
            pass
        return None


def get_audio_duration(audio_path: str) -> float:
    try:
        result = subprocess.run(
            ["ffmpeg", "-i", audio_path],
            capture_output=True,
            text=True,
            check=False
        )
        stderr = result.stderr
        match = re.search(r'Duration: (\d+):(\d+):(\d+\.\d+)', stderr)
        if match:
            hours = int(match.group(1))
            minutes = int(match.group(2))
            seconds = float(match.group(3))
            return hours * 3600 + minutes * 60 + seconds
        return 5.0
    except Exception as e:
        logger.warning(f"Failed to read audio duration: {e}")
        return 5.0