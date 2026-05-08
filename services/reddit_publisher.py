import praw
import logging
from config import config

logger = logging.getLogger(__name__)

def post_to_reddit(title: str, content: str, subreddit_name: str = None) -> bool:
    """
    Posts content to Reddit.
    """
    subreddit_to_post = subreddit_name or config.REDDIT_TARGET_SUBREDDIT
    logger.info(f"Attempting to post to Reddit: r/{subreddit_to_post}")

    if not all([config.REDDIT_CLIENT_ID, config.REDDIT_CLIENT_SECRET, config.REDDIT_USERNAME, config.REDDIT_PASSWORD]):
        logger.error("Reddit credentials are missing in config.")
        return False

    try:
        reddit = praw.Reddit(
            client_id=config.REDDIT_CLIENT_ID,
            client_secret=config.REDDIT_CLIENT_SECRET,
            user_agent=config.REDDIT_USER_AGENT,
            username=config.REDDIT_USERNAME,
            password=config.REDDIT_PASSWORD
        )

        subreddit = reddit.subreddit(subreddit_to_post)
        
        # Ensure title isn't too long for Reddit (max 300 chars usually)
        safe_title = title[:295] + "..." if len(title) > 300 else title

        submission = subreddit.submit(title=safe_title, selftext=content)
        logger.info(f"Successfully posted to Reddit! URL: {submission.url}")
        return True

    except Exception as e:
        logger.error(f"Failed to post to Reddit: {e}")
        return False
