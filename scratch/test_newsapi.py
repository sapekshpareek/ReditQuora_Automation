import requests
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("NEWSAPI_KEY")

def test_india_variations():
    variations = [
        "country=in",
        "country=in&category=general",
        "q=india&language=en",
        "q=india&language=en&sortBy=publishedAt"
    ]
    
    for var in variations:
        url = f"https://newsapi.org/v2/top-headlines?{var}&apiKey={api_key}"
        if "sortBy" in var:
             url = f"https://newsapi.org/v2/everything?{var}&apiKey={api_key}"
             
        print(f"\nTesting URL: {url}")
        response = requests.get(url)
        print(f"Status Code: {response.status_code}")
        data = response.json()
        articles = data.get("articles", [])
        print(f"Articles found: {len(articles)}")
        if articles:
            for i, a in enumerate(articles[:2]):
                print(f"  {i+1}: {a['title']}")
        else:
            print("  No articles returned.")

if __name__ == "__main__":
    test_india_variations()
