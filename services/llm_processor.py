import os
import logging
from config import config

logger = logging.getLogger(__name__)

# Initialize LLM Clients
try:
    if config.LLM_PROVIDER == 'openai':
        from openai import OpenAI
        openai_client = OpenAI(api_key=config.OPENAI_API_KEY)
    elif config.LLM_PROVIDER == 'gemini':
        from google import genai
        gemini_client = genai.Client(api_key=config.GEMINI_API_KEY)
except Exception as e:
    logger.error(f"Failed to initialize LLM clients: {e}")

def read_prompt(filename: str) -> str:
    """Reads prompt template from the prompts directory."""
    filepath = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'prompts', filename)
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        logger.error(f"Prompt file not found: {filepath}")
        return ""
    except Exception as e:
        logger.error(f"Error reading prompt file {filepath}: {e}")
        return ""

def process_news(raw_news: str, prompt_filename: str) -> str:
    """
    Combines the prompt with raw news and gets the formatted response from the LLM.
    """
    base_prompt = read_prompt(prompt_filename)
    if not base_prompt:
        return "Error: Could not load prompt template."

    full_prompt = f"{base_prompt}\\n\\nHere is the raw news data:\\n{raw_news}"
    logger.info(f"Processing news with LLM provider: {config.LLM_PROVIDER}")

    try:
        if config.LLM_PROVIDER == 'openai':
            if not config.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY is not set.")
            response = openai_client.chat.completions.create(
                model="gpt-3.5-turbo", # Or gpt-4
                messages=[
                    {"role": "system", "content": "You are an expert news editor and social media manager."},
                    {"role": "user", "content": full_prompt}
                ]
            )
            return response.choices[0].message.content

        elif config.LLM_PROVIDER == 'gemini':
            if not config.GEMINI_API_KEY:
                raise ValueError("GEMINI_API_KEY is not set.")
                
            import time
            max_retries = 5
            for attempt in range(max_retries):
                try:
                    response = gemini_client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=full_prompt,
                    )
                    return response.text
                except Exception as e:
                    if "503" in str(e) or "UNAVAILABLE" in str(e):
                        if attempt < max_retries - 1:
                            logger.warning(f"Gemini API busy (503). Retrying in 10 seconds... (Attempt {attempt + 1}/{max_retries})")
                            time.sleep(10)
                        else:
                            logger.error(f"Gemini API failed after {max_retries} attempts.")
                            raise
                    else:
                        raise
            
        else:
            raise ValueError(f"Unsupported LLM provider: {config.LLM_PROVIDER}")

    except Exception as e:
        logger.error(f"LLM processing error: {e}")
        return f"Error formatting news: {str(e)}"
