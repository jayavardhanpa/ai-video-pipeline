from openai import OpenAI
import os
from utils import logger

# Check if OpenAI API key is configured
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    logger.error("❌ OPENAI_API_KEY environment variable is not set!")
    logger.error("⚠️  Please configure OPENAI_API_KEY in Railway environment variables")
else:
    logger.info(f"✅ OpenAI API key found (length: {len(api_key)} chars)")

client = OpenAI(api_key=api_key) if api_key else None

def generate_voice(text, filename):
    """Generate voice using OpenAI Text-to-Speech"""
    try:
        if not api_key or not client:
            logger.error("❌ OpenAI API key is not configured - cannot generate voice")
            logger.error("📋 To fix: Set OPENAI_API_KEY environment variable in Railway")
            return None
            
        logger.info(f"🎤 Generating voice for text: {text[:30]}... and saving to {filename}")
        
        with client.audio.speech.with_streaming_response.create(
            model="tts-1",
            voice="alloy",
            input=text
        ) as r:
            logger.info("🎵 Receiving audio stream from OpenAI...")    
            r.stream_to_file(filename)
        
        logger.info(f"✅ Voice generated successfully: {filename}")
        return filename
        
    except Exception as e:
        logger.error(f"❌ Error generating voice: {e}")
        logger.error(f"📋 Make sure OPENAI_API_KEY is set in Railway environment variables")
        return None