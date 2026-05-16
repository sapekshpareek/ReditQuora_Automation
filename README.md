# Automated News Publisher 🚀

A highly efficient, modular Python application that fetches live news, formats it into engaging summaries using an LLM (Gemini 2.5 Flash), and automatically posts the results to Reddit and Quora.

## Features

- **Automated Scheduling:** Designed to run reliably using Google Cloud Scheduler.
- **Manual Triggering:** Provides a FastAPI webhook endpoint (`/trigger-news-post`) for on-demand or scheduled execution.
- **LLM Powered:** Uses Google's Gemini 2.5 Flash (or OpenAI) to rewrite and summarize raw news data based on customizable prompts.
- **Reddit Integration:** Securely posts to Reddit using the official `PRAW` wrapper.
- **Quora Integration:** Posts to Quora using browser automation via `Playwright` and `playwright-stealth` with persistent session profiles to avoid bot detection.
- **Modular Design:** Built with SOLID principles, making it easy to swap out news sources, LLMs, or publishing platforms.

## Project Structure

```text
project_root/
├── main.py                 # FastAPI app initialization and APScheduler setup
├── config.py               # Environment variables loading and constants
├── prompts/                # Text files containing your LLM prompts
│   ├── world_news.txt         
│   ├── national_news.txt         
│   └── india_hindi_news.txt   
├── services/
│   ├── news_fetcher.py     # Fetches raw news (NewsAPI / Web Scraping)
│   ├── llm_processor.py    # Sends raw news + prompt to Gemini
│   ├── reddit_publisher.py # Posts to Reddit via PRAW
│   └── quora_publisher.py  # Posts to Quora via Playwright
├── Dockerfile              # Docker configuration for Cloud Run
├── requirements.txt        # Python dependencies
└── .dockerignore           # Ignored files (venv, .env, etc.)
```

## Setup Instructions

### 1. Prerequisites
- Python 3.11+
- API Keys for Reddit, Gemini (or OpenAI), and optionally NewsAPI.

### 2. Install Dependencies
Clone the repository, create a virtual environment, and install dependencies:

```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Install Playwright Browsers
Playwright requires you to install the Chromium browser binaries to automate Quora:
```bash
playwright install chromium
```

### 4. Configure Environment Variables
Create a file named `.env` in the root directory and populate it with your credentials:

```env
# --- LLM Settings ---
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here # Only if using OpenAI

# --- News Source ---
# Optional: Get an API key from https://newsapi.org/ for better reliability
NEWSAPI_KEY=your_newsapi_key_here

# --- Reddit Settings ---
# Go to https://www.reddit.com/prefs/apps and create a "script" app
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USERNAME=your_reddit_username
REDDIT_PASSWORD=your_reddit_password
REDDIT_USER_AGENT=NewsBot/1.0
REDDIT_TARGET_SUBREDDIT=test # Subreddit to post to

# --- Quora Settings ---
QUORA_USER_DATA_DIR=./quora_profile
```

### 5. Setup Prompts
Open `prompts/world_news.txt` and `prompts/india_hindi_news.txt` and insert the base prompts you want the LLM to follow (e.g., "Write an engaging Twitter-style thread summarizing these headlines:"). The raw scraped news will automatically be appended to these files at runtime.

### 6. Quora Authentication Setup (CRITICAL)
Quora actively blocks headless bots. To post successfully, you must generate a persistent login session using a standard browser window first.

1. Run the local helper script: `python quora_login.py`
2. When the browser opens Quora, **manually log in**, solve any captchas, and verify you are on the authenticated homepage.
3. Close the browser. Playwright will have saved your session cookies inside the `./quora_profile` directory.
4. **Important**: This profile will be bundled into your Docker container when you deploy. If cookies expire later, you will need to run this script again and redeploy.

## Deployment (Google Cloud Run)

The application is containerized and designed specifically for Google Cloud Run to keep costs at zero when idle. 

### 1. Build and Test Locally
```bash
docker build -t news-autoposter .
docker run -p 8080:8080 --env-file .env news-autoposter
```

### 2. Deploy to Cloud Run
Using the Google Cloud CLI (`gcloud`), deploy your service:
```bash
gcloud run deploy news-autoposter --source . --region us-central1 --allow-unauthenticated --timeout 5m
```
*Note: Make sure to set a Request Timeout of at least 5 minutes so Playwright has enough time to scrape.*

### 3. Set Environment Variables
In the Google Cloud Console, navigate to your Cloud Run service's **Edit & Deploy New Revision** > **Variables & Secrets** and add your credentials (`REDDIT_CLIENT_ID`, `GEMINI_API_KEY`, etc.) rather than uploading your `.env` file.

## Setting Up the Auto-Post Schedule

We use **Google Cloud Scheduler** to trigger the API. This prevents duplicate posts when Cloud Run scales up.

1. Go to **Cloud Scheduler** in the Google Cloud Console.
2. Click **Create Job**.
3. Target: `HTTP`, Method: `POST`.
4. URL: `https://<YOUR_CLOUD_RUN_URL>/trigger-news-post`

Here are the recommended schedules and JSON bodies for your jobs:

**Morning International News (9:00 AM)**
* **Frequency:** `0 9 * * *`
* **Body:** `{"platform": "both", "news_type": "international"}`

**Afternoon National News (4:00 PM)**
* **Frequency:** `0 16 * * *`
* **Body:** `{"platform": "both", "news_type": "national"}`

**Evening Hindi News (8:00 PM)**
* **Frequency:** `0 20 * * *`
* **Body:** `{"platform": "both", "news_type": "hindi"}`

**Late Night Recap - International (2:00 AM)**
* **Frequency:** `0 2 * * *`
* **Body:** `{"platform": "both", "news_type": "international"}`

### Triggering Manually
You can still trigger the pipeline locally or in the cloud using `curl`:

```bash
curl -X POST https://<YOUR_CLOUD_RUN_URL>/trigger-news-post \
     -H "Content-Type: application/json" \
     -d '{"platform":"both", "news_type":"national"}'
```
* `platform` options: `"reddit"`, `"quora"`, `"both"`
* `news_type` options: `"international"`, `"national"`, `"hindi"`
