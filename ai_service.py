from openai import OpenAI
import os
import json
import time
from utils import logger

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def generate_script(retries=3):
    prompt = """
Generate a short spiritual YouTube script based on Bhagavad Gita.

Return STRICT JSON ONLY:

{
  "telugu": "...",
  "hindi": "...",
  "english": "..."
}
"""

    for attempt in range(retries):
        try:
            logger.info("🤖 Sending request to OpenAI API...")

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.7,
                response_format={"type": "json_object"}
            )

            content = response.choices[0].message.content.strip()

            logger.info(f"📥 Raw response: {content}")

            # ✅ Safe JSON parsing
            data = json.loads(content)

            # ✅ Validate keys
            if not all(k in data for k in ["telugu", "hindi", "english"]):
                raise ValueError("Invalid JSON format from AI")

            return data

        except Exception as e:
            logger.error(f"❌ Attempt {attempt+1} failed: {e}")

            if attempt < retries - 1:
                time.sleep(2 ** attempt)  # exponential backoff
            else:
                logger.error("❌ All retries failed. Using fallback script.")

                # ✅ Fallback (so pipeline never breaks)
                return {
                    "telugu": "కర్మ చేయండి, ఫలితం గురించి ఆలోచించవద్దు.",
                    "hindi": "कर्म करो, फल की चिंता मत करो।",
                    "english": "Do your duty without worrying about results."
                }
            