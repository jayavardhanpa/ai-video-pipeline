from openai import OpenAI
import os
import json
import time
from utils import logger
from pathlib import Path
import json

CONFIG_DIR = Path("configs")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

_FALLBACK_PROMPTS = {
    "ai_news": """You are a viral AI content creator.

HOOK STYLE:
{hook_style}

TREND CONTEXT:
{rag_context}

Create a HIGHLY ENGAGING AI short.

RULES:
- Curiosity-driven
- Exciting
- Beginner-friendly
- Max 2–3 lines

OUTPUT STRICT JSON:
{
  "hook_1": "...",
  "hook_2": "...",

  "english": "...",

  "title_en": "...",

  "hashtags_en": ["#AI", "#ChatGPT"]
}""",
    "gita": """You are a viral YouTube Shorts creator.

HOOK STYLE:
{hook_style}

RAG CONTEXT:
{rag_context}

Create a HIGHLY ENGAGING Bhagavad Gita short.

CONTENT GOAL:
- Make viewers stop scrolling immediately
- Trigger emotion, curiosity, or self-reflection
- Feel deeply relatable to modern life
- Create share-worthy wisdom

RULES:
- Emotional
- Relatable
- Curiosity-driven
- Simple language
- Avoid difficult Sanskrit
- Max 2–3 short lines
- Ideal duration: 12–22 seconds
- First line must feel powerful instantly

HOOK RULES:
- hook_1 and hook_2 must be VERY DIFFERENT
- One hook should trigger curiosity
- One hook should trigger emotion or pain
- Hooks should feel modern and conversational

TITLE RULES:
- Titles must feel emotional and clickable
- Include "Krishna" or "Bhagavad Gita"
- Keep under 60 characters
- Avoid generic titles
- English titles should feel spiritual and modern
- Titles should create curiosity or emotional pull

HASHTAG RULES:
- Include relevant spiritual and motivational hashtags
- Include #shorts in all languages

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
}""",
}

_FALLBACK_HOOKS = {
    "curiosity": [
        "Nobody talks about this",
        "Most people don't realize this",
        "This changes everything",
        "You're doing this wrong",
    ],
    "emotional": [
        "Feeling lost in life?",
        "This destroys anxiety",
        "Why do we suffer?",
        "Krishna explained this",
    ],
}

_FALLBACK_RAG = {
    "ai_news": "OpenAI launched new coding improvements.\nClaude is improving agent workflows.\nAI coding assistants are replacing repetitive work.",
    "gita": "You only control action, not results.\nPeace comes from detachment.\nOverthinking destroys clarity.\n",
}

def load_prompt(channel):

    prompt_file = CONFIG_DIR / "prompts" / f"{channel}_prompt.txt"

    try:
        return prompt_file.read_text(encoding="utf-8")
    except Exception:
        return _FALLBACK_PROMPTS[channel]

def load_hook_style(style):

    hook_file = CONFIG_DIR / "hooks" / f"{style}.json"

    try:
        data = json.loads(hook_file.read_text())
        return "\n".join(data["style"])
    except Exception:
        return "\n".join(_FALLBACK_HOOKS[style])

def load_rag(channel):

    rag_map = {
        "gita": "gita_quotes.txt",
        "ai_news": "ai_trends.txt"
    }

    rag_file = CONFIG_DIR / "rag" / rag_map[channel]

    try:
        return rag_file.read_text(encoding="utf-8")
    except Exception:
        return _FALLBACK_RAG[channel]


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

        prompt = prompt_template.replace("{hook_style}", hook_style_text).replace("{rag_context}", rag_context)

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