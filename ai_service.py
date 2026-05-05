from openai import OpenAI
import os
import json
import time
from utils import logger

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def generate_script(retries=3):
    prompt = """
You are a viral YouTube Shorts content creator.

Create a HIGHLY ENGAGING short script inspired by Bhagavad Gita.

RULES:
- Hook in first line (emotion, curiosity, or shock)
- Max 2–3 lines total
- Simple, powerful words
- Relatable to daily life (stress, failure, success, karma)
- Make it emotional and slightly dramatic
- Avoid complex Sanskrit explanations

OUTPUT STRICT JSON:

{
  "hook": "...",
  "english": "...",
  "telugu": "...",
  "hindi": "...",

  "title_en": "...",
  "title_te": "...",
  "title_hi": "...",

  "hashtags_en": ["#shorts", "..."],
  "hashtags_te": ["#shorts", "..."],
  "hashtags_hi": ["#shorts", "..."]
}
"""

    for attempt in range(retries):
        try:
            logger.info("🤖 Generating viral script...")

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                max_tokens=180,
                temperature=0.9
            )

            content = response.choices[0].message.content.strip()
            logger.info(f"📥 Raw response: {content}")

            data = json.loads(content)

            required_keys = [
                "hook",
                "english",
                "telugu",
                "hindi",
                "title_en",
                "title_te",
                "title_hi",
                "hashtags_en",
                "hashtags_te",
                "hashtags_hi"
            ]
            if not all(k in data for k in required_keys):
                raise ValueError("Invalid JSON format")

            return data

        except Exception as e:
            logger.error(f"❌ Attempt {attempt+1} failed: {e}")
            time.sleep(2 ** attempt)

    logger.error("❌ All retries failed. Using fallback.")

    return {
        "hook": "Feeling lost in life?",
        "english": "Do your duty without worrying about results.",
        "telugu": "నీ కర్తవ్యాన్ని చేయి, ఫలితంపై ఆలోచించకు.",
        "hindi": "कर्म करो, फल की चिंता मत करो।",

        "title_en": "Krishna's Advice You Need Today",
        "title_te": "కృష్ణుని మాటలు మీ జీవితాన్ని మార్చుతాయి",
        "title_hi": "कृष्ण की सीख जो जीवन बदल दे",

        "hashtags_en": ["#shorts", "#bhagavadgita", "#krishna", "#motivation"],
        "hashtags_te": ["#shorts", "#bhagavadgita", "#telugu", "#motivation"],
        "hashtags_hi": ["#shorts", "#bhagavadgita", "#hindi", "#motivation"]
    }