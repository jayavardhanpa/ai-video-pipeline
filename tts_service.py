from pathlib import Path
from openai import OpenAI
import os

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

TEMP_DIR = Path("/tmp/tts")
TEMP_DIR.mkdir(parents=True, exist_ok=True)


def generate_tts(text, lang="english", channel="gita"):

    voice_map = {
        "gita": "onyx",
        "ai_news": "alloy"
    }

    voice = voice_map.get(channel, "alloy")

    output_path = TEMP_DIR / f"{lang}_{channel}.mp3"

    with client.audio.speech.with_streaming_response.create(
        model="gpt-4o-mini-tts",
        voice=voice,
        input=text
    ) as response:

        response.stream_to_file(output_path)

    return str(output_path)