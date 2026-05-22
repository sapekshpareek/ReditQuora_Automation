import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
import os
from datetime import datetime

# Import services
from services.news_fetcher import fetch_world_news, fetch_india_news
from services.llm_processor import process_news
from services.reddit_publisher import post_to_reddit
from services.quora_publisher import post_to_quora

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Removed APScheduler for Cloud Run. Use Cloud Scheduler instead.
# Pydantic models for API
class TriggerPayload(BaseModel):
    platform: str = "both" # "reddit", "quora", or "both"
    news_type: str = "international" # "international", "national", "hindi"

def run_news_pipeline(platform="both", news_type="international"):
    """
    The main pipeline: Fetch -> Process -> Publish
    """
    logger.info(f"Starting news pipeline... Platform: {platform}, Type: {news_type}")
    
    # 1. Fetch News
    raw_news = ""
    prompt_file = ""
    title = f"Latest {news_type.capitalize()} News Update - {datetime.now().strftime('%Y-%m-%d')}"
    
    if news_type in ["world", "international"]:
        raw_news = fetch_world_news()
        prompt_file = "world_news.txt"
        title = f"Latest International News Update - {datetime.now().strftime('%Y-%m-%d')}"
    elif news_type == "national":
        raw_news = fetch_india_news()
        prompt_file = "national_news.txt"
        title = f"Latest National News Update - {datetime.now().strftime('%Y-%m-%d')}"
    elif news_type in ["india", "hindi"]:
        raw_news = fetch_india_news()
        prompt_file = "india_hindi_news.txt"
        title = f"आज की ताज़ा ख़बरें (Latest Hindi News) - {datetime.now().strftime('%Y-%m-%d')}"
    else:
        logger.error(f"Invalid news_type: {news_type}")
        return

    if not raw_news or raw_news.startswith("Failed"):
        logger.error("Failed to fetch raw news. Aborting pipeline.")
        return

    # 2. Process with LLM
    formatted_content = process_news(raw_news, prompt_file)
    
    # Strip markdown bold/italic asterisks since automated typing doesn't format them natively
    formatted_content = formatted_content.replace("**", "").replace("*", "")
    
    # Programmatic check: Ensure there are clear gaps before any numbered item (starting with 2., 3., etc.)
    # We look for a newline followed by a digit and a dot, and ensure it has multiple newlines before it.
    import re
    formatted_content = re.sub(r'\n+(\d\.)', r'\n\n\n\n\1', formatted_content)
    # Remove any extra leading newlines that might have been added to the very first item
    formatted_content = formatted_content.lstrip()
    
    if formatted_content.startswith("Error"):
        logger.error(f"LLM processing failed: {formatted_content}")
        return

    # 3. Publish
    logger.info("Publishing generated content...")
    
    if platform in ["reddit", "both"]:
        # Reddit requires a title
        reddit_success = post_to_reddit(title=title, content=formatted_content)
        if not reddit_success:
            logger.error("Reddit publication failed.")
            
    if platform in ["quora", "both"]:
        # For Quora, start directly with content (no header)
        quora_success = post_to_quora(title="", content=formatted_content)
        if not quora_success:
            logger.error("Quora publication failed.")
            
    logger.info("Pipeline execution finished.")


# Initialize FastAPI App
# Removed APScheduler lifespan since Cloud Scheduler will trigger the endpoint
app = FastAPI(title="News Auto-Poster API")

@app.post("/trigger-news-post")
async def trigger_news_post(payload: TriggerPayload):
    """
    Manually triggers the news fetching and posting pipeline.
    Runs synchronously to prevent Cloud Run CPU throttling.
    """
    logger.info(f"Manual trigger received: {payload}")
    # Run synchronously
    run_news_pipeline(payload.platform, payload.news_type)
    return {"message": "News pipeline completed successfully.", "payload": payload}

@app.get("/")
async def root():
    return {"status": "Service is running."}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
