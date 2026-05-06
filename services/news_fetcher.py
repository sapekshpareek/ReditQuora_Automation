import requests
from bs4 import BeautifulSoup
import logging
from config import config

logger = logging.getLogger(__name__)

def fetch_world_news() -> str:
    """
    Fetches raw world news. Using NewsAPI as a reliable example.
    Alternatively, you can implement web scraping here.
    """
    logger.info("Fetching world news...")
    if config.NEWSAPI_KEY:
        url = f"https://newsapi.org/v2/top-headlines?language=en&apiKey={config.NEWSAPI_KEY}"
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            articles = data.get("articles", [])[:10] # Top 10
            news_text = "\\n\\n".join([f"Headline: {a['title']}\\nSummary: {a.get('description', '')}" for a in articles])
            return news_text
        except Exception as e:
            logger.error(f"Error fetching world news via NewsAPI: {e}")
            return "Failed to fetch world news."
    else:
        # Fallback basic scraping example (e.g., from a public news site)
        logger.warning("No NewsAPI key found, attempting fallback scrape.")
        try:
            # Note: Web scraping logic depends heavily on the target site structure.
            # This is a generic placeholder.
            response = requests.get("https://html.duckduckgo.com/html/?q=world+news")
            soup = BeautifulSoup(response.text, 'html.parser')
            results = soup.find_all('a', class_='result__snippet')
            news_text = "\\n\\n".join([res.text for res in results[:10]])
            return news_text
        except Exception as e:
            logger.error(f"Error fetching world news via scraping: {e}")
            return "Failed to fetch world news."

def fetch_india_news() -> str:
    """
    Fetches raw Indian news. 
    Tries top-headlines for India first, falls back to a general search if empty.
    """
    logger.info("Fetching India news...")
    if not config.NEWSAPI_KEY:
        return "Failed: No NewsAPI key available."

    try:
        # Attempt 1: Top Headlines for India
        url = f"https://newsapi.org/v2/top-headlines?country=in&apiKey={config.NEWSAPI_KEY}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        articles = data.get("articles", [])

        # Attempt 2: If no top headlines, use general search for India
        if not articles:
            logger.warning("No top headlines found for India, falling back to general search.")
            url = f"https://newsapi.org/v2/everything?q=india&language=en&sortBy=publishedAt&pageSize=10&apiKey={config.NEWSAPI_KEY}"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            articles = data.get("articles", [])

        if not articles:
            return "Failed: No articles found for India."

        news_text = "\\n\\n".join([f"Headline: {a['title']}\\nSummary: {a.get('description', '')}" for a in articles[:10]])
        return news_text

    except Exception as e:
        logger.error(f"Error fetching India news: {e}")
        return f"Failed: {str(e)}"
