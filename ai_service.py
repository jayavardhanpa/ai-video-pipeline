from openai import OpenAI
import os
import json
import time
from utils import logger
from pathlib import Path
import json

CONFIG_DIR = Path("configs")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def load_prompt(channel):

    prompt_file = CONFIG_DIR / "prompts" / f"{channel}_prompt.txt"

    return prompt_file.read_text(encoding="utf-8")

def load_hook_style(style):

    hook_file = CONFIG_DIR / "hooks" / f"{style}.json"

    data = json.loads(hook_file.read_text())

    return "\n".join(data["style"])

def load_rag(channel):

    rag_map = {
        "gita": "gita_quotes.txt",
        "ai_news": "ai_trends.txt"
    }

    rag_file = CONFIG_DIR / "rag" / rag_map[channel]

    return rag_file.read_text(encoding="utf-8")


def generate_script(
    channel="gita",
    hook_style="curiosity",
    retries=3
):    

   # =========================
    # DYNAMIC PROMPT BUILDING
    # =========================

    try:

        prompt_template = load_prompt(channel)

        hook_style_text = load_hook_style(hook_style)

        rag_context = load_rag(channel)

        prompt = prompt_template.format(
            hook_style=hook_style_text,
            rag_context=rag_context
        )

    except Exception as e:

        logger.error(f"❌ Failed loading configs: {e}")

        raise

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