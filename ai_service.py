from openai import OpenAI
import os
import json
import re
from utils import logger

# Check if OpenAI API key is configured
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    logger.error("❌ OPENAI_API_KEY environment variable is not set!")
    logger.error("⚠️  Please configure OPENAI_API_KEY in Railway environment variables")
else:
    logger.info(f"✅ OpenAI API key found (length: {len(api_key)} chars)")

client = OpenAI(api_key=api_key) if api_key else None

def generate_script():
    """Generate a spiritual YouTube script using OpenAI"""
    try:
        if not api_key or not client:
            logger.error("❌ OpenAI API key is not configured - cannot generate script")
            logger.error("📋 To fix: Set OPENAI_API_KEY environment variable in Railway")
            return None
            
        prompt = """
        Generate a short spiritual YouTube script based on Bhagavad Gita.

        Return JSON format ONLY:

        {
          "telugu": "Telugu script (80-120 words)",
          "hindi": "Hindi script",
          "english": "English script"
        }
        """

        logger.info("🤖 Sending request to OpenAI API...")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300
        )

        logger.info(f"✅ Received script generation response from OpenAI.")
        raw_content = response.choices[0].message.content

        # Strip markdown code fences if present (e.g. ```json ... ```)
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw_content, re.DOTALL)
        if match:
            json_str = match.group(1)
        else:
            # Fall back to extracting the first {...} block from the response
            match = re.search(r"\{.*\}", raw_content, re.DOTALL)
            json_str = match.group(0) if match else raw_content

        result = json.loads(json_str)
        logger.info(f"📝 Generated script (English): {result.get('english', '')[:50]}...")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error generating script: {e}")
        logger.error(f"📋 Make sure OPENAI_API_KEY is set in Railway environment variables")
        return None