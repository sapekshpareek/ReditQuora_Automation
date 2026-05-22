import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from apscheduler.schedulers.background import BackgroundScheduler
import uvicorn
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

# Initialize Scheduler
scheduler = BackgroundScheduler()

# Pydantic models for API
class TriggerPayload(BaseModel):
    platform: str = "both" # "reddit", "quora", or "both"
    news_type: str = "world" # "world" or "india"

def run_news_pipeline(platform="both", news_type="world"):
    """
    The main pipeline: Fetch -> Process -> Publish
    """
    logger.info(f"Starting news pipeline... Platform: {platform}, Type: {news_type}")
    
    # 1. Fetch News
    raw_news = ""
    prompt_file = ""
    title = f"Latest {news_type.capitalize()} News Update - {datetime.now().strftime('%Y-%m-%d')}"
    
    if news_type == "world":
        raw_news = fetch_world_news()
        prompt_file = "world_news.txt"
    elif news_type == "india":
        raw_news = fetch_india_news()
        prompt_file = "india_hindi_news.txt"
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Start the scheduler
    logger.info("Starting APScheduler...")
    # Schedule twice a day: 08:00 AM and 08:00 PM local server time
    scheduler.add_job(run_news_pipeline, 'cron', hour=8, minute=0, args=["quora", "world"], id="morning_world_news")
    scheduler.add_job(run_news_pipeline, 'cron', hour=20, minute=0, args=["quora", "india"], id="evening_india_news")
    scheduler.start()
    yield
    # Shutdown: Stop the scheduler
    logger.info("Shutting down APScheduler...")
    scheduler.shutdown()

# Initialize FastAPI App
app = FastAPI(lifespan=lifespan, title="News Auto-Poster API")

@app.post("/trigger-news-post")
async def trigger_news_post(payload: TriggerPayload, background_tasks: BackgroundTasks):
    """
    Manually triggers the news fetching and posting pipeline.
    """
    logger.info(f"Manual trigger received: {payload}")
    background_tasks.add_task(run_news_pipeline, payload.platform, payload.news_type)
    return {"message": "News pipeline triggered in the background.", "payload": payload}

@app.get("/")
async def root():
    return {"status": "Service is running."}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
