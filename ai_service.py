from openai import OpenAI
import os
from utils import logger

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_script():
    prompt = """
    Generate a short spiritual YouTube script based on Bhagavad Gita.

    Return JSON format ONLY:

    {
      "telugu": "Telugu script (80-120 words)",
      "hindi": "Hindi script",
      "english": "English script"
    }
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300
    )

    logger.info(f"Received script generation response from OpenAI.")

    return eval(response.choices[0].message.content)