# Automated News Publisher 🚀

A highly efficient, modular Python application that fetches live news, formats it into engaging summaries using an LLM (Gemini 2.5 Flash), and automatically posts the results to Reddit and Quora.

## Features

- **Automated Scheduling:** Runs twice a day automatically using `APScheduler` (e.g., Morning for World News, Evening for India News).
- **Manual Triggering:** Provides a FastAPI webhook endpoint (`/trigger-news-post`) for on-demand execution.
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
│   └── india_hindi_news.txt   
├── services/
│   ├── news_fetcher.py     # Fetches raw news (NewsAPI / Web Scraping)
│   ├── llm_processor.py    # Sends raw news + prompt to Gemini
│   ├── reddit_publisher.py # Posts to Reddit via PRAW
│   └── quora_publisher.py  # Posts to Quora via Playwright
├── requirements.txt        # Python dependencies
└── .gitignore              # Ignored files (venv, .env, quora_profile)
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

1. Open `services/quora_publisher.py`.
2. Temporarily change `headless=True` to `headless=False` inside the `launch_persistent_context` block.
3. Write a temporary script to run the Playwright block, or just run the FastAPI server and trigger the Quora script.
4. When the browser opens Quora, **manually log in**, solve any captchas, and verify you are on the authenticated homepage.
5. Close the browser. Playwright will have saved your session cookies inside the `./quora_profile` directory.
6. **Change `headless=False` back to `headless=True`** in your code for future automated runs.

## Running the Application

Start the FastAPI application and the background scheduler:

```bash
python main.py
# OR
uvicorn main:app --host 0.0.0.0 --port 8000
```

- The background scheduler will automatically trigger the World News pipeline at **08:00 AM** and the India News pipeline at **08:00 PM** (local server time).

### Manual Triggering API
You can trigger the pipeline manually by sending a POST request:

**Endpoint:** `POST /trigger-news-post`

**JSON Payload:**
```json
{
  "platform": "both", 
  "news_type": "world" 
}
```
* `platform` options: `"reddit"`, `"quora"`, `"both"`
* `news_type` options: `"world"`, `"india"`

Example using `curl`:
```bash
curl -X POST http://127.0.0.1:8000/trigger-news-post \
     -H "Content-Type: application/json" \
     -d '{"platform":"reddit", "news_type":"india"}'
```
