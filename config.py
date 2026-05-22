import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Reddit Settings
    # Create an app at https://www.reddit.com/prefs/apps as a "script"
    REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
    REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
    REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "NewsBot/1.0")
    REDDIT_USERNAME = os.getenv("REDDIT_USERNAME")
    REDDIT_PASSWORD = os.getenv("REDDIT_PASSWORD")
    REDDIT_TARGET_SUBREDDIT = os.getenv("REDDIT_TARGET_SUBREDDIT", "test")

    # LLM Settings (OpenAI or Gemini)
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini") # 'openai' or 'gemini'
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

    # Quora Settings
    # This directory will store your session cookies and data.
    # To use it, you must first run Quora via Playwright in headed mode
    # manually, log into Quora, and let it save the state here.
    QUORA_USER_DATA_DIR = os.getenv("QUORA_USER_DATA_DIR", "./quora_profile")
    
    # Secure alternative: Inject cookies directly via JSON string
    QUORA_COOKIES_JSON = os.getenv("QUORA_COOKIES_JSON")
    
    # NewsAPI Setting (if using NewsAPI instead of scraping)
    # Get a key from https://newsapi.org/
    NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")

config = Config()
