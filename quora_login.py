import asyncio
from playwright.async_api import async_playwright
import os

QUORA_USER_DATA_DIR = os.getenv("QUORA_USER_DATA_DIR", "./quora_profile")

async def main():
    print("Starting Playwright to log into Quora...")
    print(f"Session data will be saved to: {QUORA_USER_DATA_DIR}")
    
    async with async_playwright() as p:
        # Launch browser with the persistent context so cookies are saved
        # Headless is False so you can see the screen and log in
        browser_context = await p.chromium.launch_persistent_context(
            user_data_dir=QUORA_USER_DATA_DIR,
            headless=False,
            args=["--disable-blink-features=AutomationControlled"]
        )
        
        page = await browser_context.new_page()
        
        # We use stealth to prevent Quora from immediately blocking the browser
        try:
            from playwright_stealth import Stealth
            await Stealth().apply_stealth_async(page)
        except ImportError:
            print("playwright-stealth not installed. You may get blocked. Run `pip install playwright-stealth` if needed.")
            
        print("Navigating to Quora...")
        await page.goto("https://www.quora.com/")
        
        print("\n" + "="*50)
        print("ACTION REQUIRED: Please log into your Quora account in the browser window.")
        print("Once you are fully logged in and can see your feed, simply close the browser window.")
        print("="*50 + "\n")
        
        # Keep the script running until the user closes the browser
        try:
            # Wait for the page to be closed by the user
            await page.wait_for_event("close", timeout=0)
        except Exception:
            pass
            
        print("Browser closed. Session saved successfully!")

if __name__ == "__main__":
    # Ensure playwright browsers are installed first
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"An error occurred: {e}")
        print("\nNote: Have you installed the Playwright browsers? If not, run:")
        print("playwright install chromium")
