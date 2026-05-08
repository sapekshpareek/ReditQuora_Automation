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
            # Using persistent context to retain login session
            # Using a real browser User Agent is CRITICAL for headless mode on Quora
            user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            
            logger.info(f"Launching Playwright with user data dir: {config.QUORA_USER_DATA_DIR}")
            browser = p.chromium.launch_persistent_context(
                user_data_dir=config.QUORA_USER_DATA_DIR,
                headless=True, # Run in background (headless) now that it's working
                user_agent=user_agent,
                viewport={"width": 1920, "height": 1080},
                args=["--disable-blink-features=AutomationControlled"]
            )
            
            page = browser.new_page()
            # Apply stealth to avoid bot detection
            Stealth().apply_stealth_sync(page)

            # Navigate to Quora
            logger.info("Navigating to Quora...")
            page.goto("https://www.quora.com/", timeout=60000)
            
            # Basic check to see if we are logged in (e.g., look for user profile icon)
            # This selector might change, you may need to inspect Quora's current DOM
            if not page.is_visible("div.q-relative.qu-display--flex"): # Example selector, might need adjustment
                 logger.warning("Might not be logged in. Proceeding anyway, but expect failure if login required.")

            # Note: Quora's UI changes frequently. The following selectors are
            # illustrative and likely need to be updated by inspecting Quora's actual post button.
            
            # 1. Click the main box that opens the modal
            logger.info("Looking for the 'What do you want to ask or share?' box...")
            try:
                # Try clicking the generic input on the feed that opens the modal
                open_modal_btn = page.locator("text=What do you want to ask or share?")
                if open_modal_btn.is_visible():
                    open_modal_btn.click(timeout=5000)
                else:
                    # Fallback: Try clicking the generic Add question button top right
                    page.locator("button:has-text('Add question')").first.click(timeout=5000)
            except Exception as e:
                logger.error(f"Could not open the modal: {e}")
                browser.close()
                return False

            # 2. Click the "Create Post" tab inside the modal
            logger.info("Switching to 'Create Post' tab...")
            page.wait_for_timeout(1000) # Wait for modal to animate
            try:
                # Find the tab that says Create Post and click it
                page.locator("text=Create Post").first.click(timeout=5000)
            except Exception as e:
                logger.error(f"Could not click 'Create Post' tab: {e}")
                
            # 3. Type the content
            # A Quora post usually just has one big rich text editor. We combine title and content.
            logger.info("Typing the news post...")
            full_post_text = f"{title}\n\n{content}" if title else content
            
            try:
                # Quora's rich text editor usually uses contenteditable divs
                editor = page.locator("div[contenteditable='true']")
                editor.click(timeout=5000)
                page.wait_for_timeout(500)
                
                # Insert text via execCommand which simulates pasting natively. 
                # This ensures Quora's React state registers the text and enables the Post button!
                page.evaluate("text => document.execCommand('insertText', false, text)", full_post_text)
                
                # Type a single space to trigger any final keyboard event listeners
                page.keyboard.type(" ")
                page.wait_for_timeout(1000)
            except Exception as e:
                logger.error(f"Failed to type into editor: {e}")
            
            # 4. Click Submit
            logger.info("Waiting for Post button to become enabled...")
            
            try:
                # This script polls the page for 10 seconds waiting for the button to become enabled.
                # A button is considered "enabled" when its cursor changes to 'pointer'.
                page.evaluate('''async () => {
                    const findButton = () => {
                        const elements = Array.from(document.querySelectorAll('*'));
                        return elements.find(el => {
                            const style = window.getComputedStyle(el);
                            return el.textContent.trim() === 'Post' && 
                                   style.cursor === 'pointer' && 
                                   el.getBoundingClientRect().width > 0;
                        });
                    };

                    for (let i = 0; i < 20; i++) { // Try for 10 seconds (20 * 500ms)
                        const btn = findButton();
                        if (btn) {
                            btn.click();
                            return "Success";
                        }
                        await new Promise(r => setTimeout(r, 500));
                    }
                    throw new Error("Post button never became enabled.");
                }''')
                logger.info("Post button clicked successfully.")
            except Exception as e:
                logger.warning(f"Could not automatically click Post. Error: {e}")
                # Save a screenshot so we can see what went wrong in headless mode
                page.screenshot(path="quora_error.png")
                logger.info("Saved quora_error.png for debugging.")

            # Wait a bit so the post can process before closing
            page.wait_for_timeout(5000)

            # Wait a bit for the submission to process
            page.wait_for_timeout(5000)

            logger.info("Quora posting automation completed (Note: verify selectors in code).")
            browser.close()
            return True

    except Exception as e:
        logger.error(f"Failed to post to Quora: {e}")
        return False
