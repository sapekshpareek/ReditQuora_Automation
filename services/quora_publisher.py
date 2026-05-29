import os
import logging
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
from config import config

logger = logging.getLogger(__name__)

def post_to_quora(title: str, content: str) -> bool:
    """
    Posts content to Quora using Playwright with stealth evasions.
    Requires an existing session/profile in config.QUORA_USER_DATA_DIR.
    """
    logger.info("Attempting to post to Quora...")

    try:
        with sync_playwright() as p:
            import json
            import gzip
            import base64
            
            # Using a real browser User Agent is CRITICAL for headless mode on Quora
            user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            
            is_headless = os.getenv("HEADLESS", "true").lower() == "true"
            
            if config.QUORA_COOKIES_JSON:
                logger.info("QUORA_COOKIES_JSON found. Launching standard browser and injecting cookies.")
                playwright_browser = p.chromium.launch(
                    headless=is_headless,
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--no-sandbox",
                        "--disable-setuid-sandbox",
                        "--disable-dev-shm-usage"
                    ]
                )
                context = playwright_browser.new_context(
                    user_agent=user_agent,
                    viewport={"width": 1920, "height": 1080}
                )
                
                # Decode and Inject cookies
                try:
                    # Decompress the base64 gzip string
                    compressed = base64.b64decode(config.QUORA_COOKIES_JSON)
                    json_str = gzip.decompress(compressed).decode('utf-8')
                    cookies = json.loads(json_str)
                    context.add_cookies(cookies)
                except Exception as e:
                    logger.error(f"Failed to parse or inject cookies: {e}")
                    playwright_browser.close()
                    return False
                
                page = context.new_page()
                browser_to_close = playwright_browser
                
            else:
                logger.info(f"Launching Playwright with persistent user data dir: {config.QUORA_USER_DATA_DIR}")
                context = p.chromium.launch_persistent_context(
                    user_data_dir=config.QUORA_USER_DATA_DIR,
                    headless=is_headless,
                    user_agent=user_agent,
                    viewport={"width": 1920, "height": 1080},
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--no-sandbox",
                        "--disable-setuid-sandbox",
                        "--disable-dev-shm-usage"
                    ]
                )
                
                # launch_persistent_context creates a default page
                if len(context.pages) > 0:
                    page = context.pages[0]
                else:
                    page = context.new_page()
                    
                browser_to_close = context
            
            # Apply stealth to avoid bot detection
            Stealth().apply_stealth_sync(page)

            # Navigate to Quora Space
            logger.info("Navigating to Quora Space...")
            page.goto("https://globalnewsspacehindienglish.quora.com/", timeout=60000)
            logger.info("Waiting for Space page to load...")
            page.wait_for_timeout(5000)
            
            # Basic check to see if we are logged in (e.g., look for user profile icon)
            # This selector might change, you may need to inspect Quora's current DOM
            if not page.is_visible("div.q-relative.qu-display--flex"): # Example selector, might need adjustment
                 logger.warning("Might not be logged in. Proceeding anyway, but expect failure if login required.")

            # Note: Quora's UI changes frequently. The following selectors are
            # illustrative and likely need to be updated by inspecting Quora's actual post button.
            
            # 1. Click the main box that opens the modal
            logger.info("Looking for the 'Say something...' box...")
            try:
                clicked = page.evaluate('''() => {
                    const elements = Array.from(document.querySelectorAll('*'));
                    const target = elements.find(el => {
                        const text = el.textContent.trim();
                        const style = window.getComputedStyle(el);
                        return text.startsWith('Say something') && style.cursor === 'text';
                    });
                    if (target) {
                        target.click();
                        return true;
                    }
                    return false;
                }''')
                
                if not clicked:
                    logger.warning("'Say something' not found. Trying generic qu-cursor--text...")
                    fallback = page.locator(".qu-cursor--text").first
                    if fallback.is_visible():
                        fallback.click(timeout=5000, force=True)
                    else:
                        raise Exception("No input box found.")
            except Exception as e:
                logger.error(f"Could not open the modal at all: {e}")
                browser_to_close.close()
                return False

            # 2. Click the "Create Post" tab inside the modal
            logger.info("Switching to 'Create Post' tab...")
            page.wait_for_timeout(1000) # Wait for modal to animate
            try:
                # Find the tab that says Create Post and click it
                page.locator("text=Create Post").first.click(timeout=5000, force=True)
            except Exception as e:
                logger.error(f"Could not click 'Create Post' tab: {e}")
                
            # 3. Type the content
            # A Quora post usually just has one big rich text editor. We combine title and content.
            logger.info("Typing the news post...")
            full_post_text = f"{title}\n\n{content}" if title else content
            
            try:
                # Quora's rich text editor usually uses contenteditable divs
                editor = page.locator("div[contenteditable='true']")
                editor.click(timeout=5000, force=True)
                logger.info("Waiting before typing...")
                page.wait_for_timeout(5000)
                
                # Insert text via execCommand which simulates pasting natively. 
                # This ensures Quora's React state registers the text and enables the Post button!
                page.evaluate("text => document.execCommand('insertText', false, text)", full_post_text)
                
                # Type a single space to trigger any final keyboard event listeners
                page.keyboard.type(" ")
                logger.info("Waiting after typing before submitting...")
                page.wait_for_timeout(5000)
            except Exception as e:
                logger.error(f"Failed to type into editor: {e}")
            
            # 4. Click Submit / Next
            logger.info("Waiting for Next or Post button to become enabled...")
            
            try:
                # This script polls the page for 10 seconds waiting for the button to become enabled.
                page.evaluate('''async () => {
                    const findButton = (texts) => {
                        const elements = Array.from(document.querySelectorAll('*'));
                        return elements.find(el => {
                            const style = window.getComputedStyle(el);
                            return texts.includes(el.textContent.trim()) && 
                                   style.cursor === 'pointer' && 
                                   el.getBoundingClientRect().width > 0;
                        });
                    };

                    for (let i = 0; i < 20; i++) { // Try for 10 seconds (20 * 500ms)
                        const btn = findButton(['Post', 'Next']);
                        if (btn) {
                            btn.click();
                            return "Success";
                        }
                        await new Promise(r => setTimeout(r, 500));
                    }
                    throw new Error("Next/Post button never became enabled.");
                }''')
                logger.info("Next/Post button clicked successfully.")
            except Exception as e:
                logger.warning(f"Could not automatically click Next/Post. Error: {e}")
                # Save a screenshot so we can see what went wrong
                page.screenshot(path="quora_error.png")
                logger.info("Saved quora_error.png for debugging.")

            # Wait a bit for the submission or next dialog to process
            page.wait_for_timeout(5000)
            
            # 5. Handle Monetization dialog if it appears
            try:
                monetized_btn = page.locator("text=Monetized").first
                if monetized_btn.is_visible():
                    logger.info("Monetization dialog detected. Selecting 'Monetized'...")
                    monetized_btn.click(timeout=3000, force=True)
                    page.wait_for_timeout(2000)
                    
                    # Click the final Post button in the dialog
                    logger.info("Clicking final Post button in monetization dialog...")
                    post_btn = page.locator("button:has-text('Post')").first
                    if post_btn.is_visible():
                        post_btn.click(timeout=3000, force=True)
                    else:
                        page.locator("text=Post").last.click(timeout=3000, force=True)
                    page.wait_for_timeout(5000)
            except Exception as e:
                logger.info("No monetization dialog found or failed to handle it.")
            
            # --- DEBUGGING: CAPTURE THE SCREEN ---
            # Since it works locally but not on the server, Quora might be showing a CAPTCHA
            # or silently blocking the post because of the Google Cloud IP address.
            try:
                import base64
                screenshot = page.screenshot(type="jpeg", quality=30)
                b64_img = base64.b64encode(screenshot).decode('utf-8')
                logger.info("FINAL SCREENSHOT: Copy the text below and paste it into your browser URL bar to see what Quora is displaying:")
                logger.info(f"data:image/jpeg;base64,{b64_img}")
            except Exception as e:
                logger.error(f"Could not capture screenshot: {e}")

            logger.info("Quora posting automation completed (Note: verify selectors in code).")
            browser_to_close.close()
            return True

    except Exception as e:
        logger.error(f"Failed to post to Quora: {e}")
        return False
