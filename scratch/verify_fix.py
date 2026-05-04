import logging
import sys
import os

# Add the project root to sys.path
sys.path.append(os.getcwd())

from services.news_fetcher import fetch_india_news
from config import config

# Configure logging to see the output
logging.basicConfig(level=logging.INFO)

def test_fetcher():
    print("Testing fetch_india_news()...")
    result = fetch_india_news()
    if result.startswith("Failed"):
        print(f"FAILED: {result}")
    else:
        print("SUCCESS! News content fetched:")
        print(result[:500] + "...")

if __name__ == "__main__":
    test_fetcher()
