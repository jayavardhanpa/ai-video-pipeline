from openai import OpenAI
import os
from utils import logger

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_voice(text, filename):
    logger.info(f"Generating voice for text: {text[:30]}... and saving to {filename}")
    with client.audio.speech.with_streaming_response.create(
        model="gpt-4o-mini-tts",
        voice="alloy",
        input=text
    ) as r:
        logger.info("Receiving audio stream from OpenAI...")    
        r.stream_to_file(filename)

    return filename