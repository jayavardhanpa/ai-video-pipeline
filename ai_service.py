from openai import OpenAI
import os
import json
import time
from utils import logger
from pathlib import Path

CONFIG_DIR = Path("configs")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ---------------------------------------------------------------------------
# Fallback content used when config files are missing or unreadable
# ---------------------------------------------------------------------------

_FALLBACK_PROMPTS = {
    "ai_news": (
        "You are a viral AI content creator.\n\n"
        "HOOK STYLE:\n{hook_style}\n\n"
        "TREND CONTEXT:\n{rag_context}\n\n"
        "Create a HIGHLY ENGAGING AI short.\n\n"
        "RULES:\n- Curiosity-driven\n- Exciting\n- Beginner-friendly\n- Max 2\u20133 lines\n\n"
        "OUTPUT STRICT JSON:\n"
        "{{\n"
        "  \"hook_1\": \"...\",\n"
        "  \"hook_2\": \"...\",\n"
        "  \"english\": \"...\",\n"
        "  \"title_en\": \"...\",\n"
        "  \"hashtags_en\": [\"#AI\", \"#ChatGPT\"]\n"
        "}}"
    ),
    "gita": (
        "You are a viral YouTube Shorts creator.\n\n"
        "HOOK STYLE:\n{hook_style}\n\n"
        "RAG CONTEXT:\n{rag_context}\n\n"
        "Create a HIGHLY ENGAGING Bhagavad Gita short.\n\n"
        "RULES:\n- Emotional\n- Relatable\n- Curiosity-driven\n- Simple language\n- Max 2\u20133 lines\n\n"
        "OUTPUT STRICT JSON:\n"
        "{{\n"
        "  \"hook_1\": \"...\",\n"
        "  \"hook_2\": \"...\",\n"
        "  \"english\": \"...\",\n"
        "  \"telugu\": \"...\",\n"
        "  \"hindi\": \"...\",\n"
        "  \"title_en\": \"...\",\n"
        "  \"title_te\": \"...\",\n"
        "  \"title_hi\": \"...\",\n"
        "  \"hashtags_en\": [\"#shorts\"],\n"
        "  \"hashtags_te\": [\"#shorts\"],\n"
        "  \"hashtags_hi\": [\"#shorts\"]\n"
        "}}"
    ),
}

_FALLBACK_HOOKS = {
    "curiosity": "Nobody talks about this\nMost people don't realize this\nThis changes everything\nYou're doing this wrong",
    "emotional":  "Feeling lost in life?\nThis destroys anxiety\nWhy do we suffer?\nKrishna explained this",
    "fear":       "This is destroying your focus\nStop ignoring this warning\nYou're making this mistake daily",
}

_FALLBACK_RAG = {
    "ai_news": "OpenAI launched new coding improvements.\nClaude is improving agent workflows.\nAI coding assistants are replacing repetitive work.",
    "gita":    "You only control action, not results.\nPeace comes from detachment.\nOverthinking destroys clarity.",
}


def load_prompt(channel):
    prompt_file = CONFIG_DIR / "prompts" / f"{channel}_prompt.txt"
    logger.info(f"📂 Loading prompt file: {prompt_file}")
    try:
        text = prompt_file.read_text(encoding="utf-8")
        logger.info(f"✅ Prompt loaded for channel '{channel}'")
        return text
    except FileNotFoundError:
        logger.warning(f"⚠️  Prompt file not found: {prompt_file} — using fallback prompt")
        return _FALLBACK_PROMPTS.get(
            channel,
            _FALLBACK_PROMPTS["gita"]  # generic last-resort
        )


def load_hook_style(style):
    hook_file = CONFIG_DIR / "hooks" / f"{style}.json"
    logger.info(f"📂 Loading hook file: {hook_file}")
    try:
        data = json.loads(hook_file.read_text())
        text = "\n".join(data["style"])
        logger.info(f"✅ Hook style loaded for '{style}'")
        return text
    except FileNotFoundError:
        logger.warning(f"⚠️  Hook file not found: {hook_file} — using fallback hooks")
        return _FALLBACK_HOOKS.get(style, _FALLBACK_HOOKS["curiosity"])
    except (KeyError, json.JSONDecodeError) as e:
        logger.warning(f"⚠️  Hook file malformed ({e}): {hook_file} — using fallback hooks")
        return _FALLBACK_HOOKS.get(style, _FALLBACK_HOOKS["curiosity"])


def load_rag(channel):
    rag_map = {
        "gita":    "gita_quotes.txt",
        "ai_news": "ai_trends.txt",
    }

    if channel not in rag_map:
        logger.warning(f"⚠️  No RAG mapping for channel '{channel}' — using fallback context")
        return _FALLBACK_RAG.get(channel, "")

    rag_file = CONFIG_DIR / "rag" / rag_map[channel]
    logger.info(f"📂 Loading RAG file: {rag_file}")
    try:
        text = rag_file.read_text(encoding="utf-8")
        logger.info(f"✅ RAG context loaded for channel '{channel}'")
        return text
    except FileNotFoundError:
        logger.warning(f"⚠️  RAG file not found: {rag_file} — using fallback context")
        return _FALLBACK_RAG.get(channel, "")


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
        logger.info(f"✅ Prompt assembled for channel='{channel}', hook_style='{hook_style}'")

    except Exception as e:
        logger.error(f"❌ Unexpected error building prompt: {e} — falling through to API fallback")
        prompt = None

    # =========================
    # API CALL
    # =========================

    if prompt is None:
        logger.warning("⚠️  Skipping API call — prompt could not be built, returning static fallback")
    else:
        for attempt in range(retries):
            try:
                logger.info(f"🤖 Generating script for channel: {channel}, attempt {attempt + 1}/{retries}")

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
                logger.error(f"❌ Attempt {attempt + 1} failed: {e}")
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)

        logger.error("❌ All retries exhausted — returning static fallback")

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