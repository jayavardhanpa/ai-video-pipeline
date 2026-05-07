from openai import OpenAI
import os
import json
import time
from utils import logger

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def generate_script(channel="gita", retries=3):

    # =========================
    # GITA CHANNEL
    # =========================
    if channel == "gita":

        prompt = """
You are a viral YouTube Shorts content creator.

Create a HIGHLY ENGAGING short script inspired by Bhagavad Gita.

RULES:
- Hook in first line
- Max 2–3 lines total
- Emotional and relatable
- Simple words
- Avoid complex Sanskrit

OUTPUT STRICT JSON:

{
  "hook_1": "...",
  "hook_2": "...",

  "english": "...",
  "telugu": "...",
  "hindi": "...",

  "title_en": "...",
  "title_te": "...",
  "title_hi": "...",

  "hashtags_en": ["#shorts"],
  "hashtags_te": ["#shorts"],
  "hashtags_hi": ["#shorts"]
}
"""

    # =========================
    # AI NEWS CHANNEL
    # =========================
    elif channel == "ai_news":

        prompt = """
You are a viral AI YouTube Shorts creator.

Create a HIGHLY ENGAGING AI short video.

TOPICS:
- ChatGPT tips
- AI tools
- AI coding hacks
- Claude/Gemini updates
- AI news
- AI productivity

RULES:
- Hook in first line
- Max 2–3 lines
- Curiosity-driven
- Exciting
- Beginner friendly

OUTPUT STRICT JSON:

{
  "hook_1": "...",
  "hook_2": "...",

  "english": "...",

  "title_en": "...",

  "hashtags_en": ["#AI", "#ChatGPT"]
}
"""

    else:
        raise ValueError(f"Unsupported channel: {channel}")

    # =========================
    # API CALL
    # =========================

    for attempt in range(retries):
        try:
            logger.info(f"🤖 Generating script for channel: {channel}")

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                max_tokens=500,
                temperature=0.9
            )

            content = response.choices[0].message.content.strip()
            logger.info(f"📥 Raw response: {content}")

            data = json.loads(content)

            return data

        except Exception as e:
            logger.error(f"❌ Attempt {attempt+1} failed: {e}")
            time.sleep(2 ** attempt)

    logger.error("❌ All retries failed")

    # =========================
    # FALLBACKS
    # =========================

    if channel == "ai_news":
        return {
            "hook_1": "AI is changing everything.",
            "hook_2": "Most people are using ChatGPT wrong.",

            "english": "Use AI to save hours every single day.",

            "title_en": "AI Trick You Should Start Using",
            "hashtags_en": ["#AI", "#ChatGPT", "#AITools"]
        }

    return {
        "hook_1": "Feeling lost in life?",
        "hook_2": "Why do we suffer so much?",

        "english": "Do your duty without worrying about results.",
        "telugu": "నీ కర్తవ్యాన్ని చేయి, ఫలితంపై ఆలోచించకు.",
        "hindi": "कर्म करो, फल की चिंता मत करो।",

        "title_en": "Krishna's Advice You Need Today",
        "title_te": "కృష్ణుని మాటలు మీ జీవితాన్ని మార్చుతాయి",
        "title_hi": "कृष्ण की सीख जो जीवन बदल दे",

        "hashtags_en": ["#shorts", "#bhagavadgita"],
        "hashtags_te": ["#shorts", "#bhagavadgita"],
        "hashtags_hi": ["#shorts", "#bhagavadgita"]
    }