from datetime import datetime, timedelta, timezone
import feedparser
from . import Article
from .config import Config
import logging

log = logging.getLogger(__name__)

def fetch_feeds(config: Config) -> list[Article]:
    """Fetch articles from all configured feeds."""
    articles = []
    failed_feeds = []
    now = datetime.now(timezone.utc)
    feedparser.USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    window_start = now - timedelta(days=7)

    for topic_key, topic_config in config.sources.get("topics", {}).items():
        topic_name = topic_config["name"]
        for feed_config in topic_config.get("feeds", []):
            try:
                feed = feedparser.parse(feed_config["url"])
                if not feed.get("entries"):
                    failed_feeds.append((feed_config["name"], "no entries"))
                    continue

                for entry in feed.entries:
                    # Parse publication date — try normalized feedparser fields in order
                    pub_date = None
                    for field in ['published_parsed', 'updated_parsed', 'created_parsed']:
                        try:
                            parsed = getattr(entry, field, None)
                            if parsed:
                                pub_date = datetime(*parsed[:6], tzinfo=timezone.utc)
                                break
                        except (AttributeError, TypeError, ValueError):
                            continue

                    # If no date found, use today (keep article, log at INFO)
                    if pub_date is None:
                        pub_date = now
                        log.info(f"No date found for '{getattr(entry, 'title', 'unknown')}' — using today's date")

                    # Filter to 7-day window
                    if pub_date < window_start:
                        continue

                    article = Article(
                        title=getattr(entry, "title", "(no title)"),
                        url=getattr(entry, "link", ""),
                        source_name=feed_config["name"],
                        published=pub_date,
                        feed_summary=getattr(entry, "summary", ""),
                    )
                    articles.append(article)
            except Exception as e:
                failed_feeds.append((feed_config["name"], str(e)))
                log.error(f"Failed to fetch {feed_config['name']}: {e}")

    # Store failed feeds for later reporting
    config._failed_feeds = failed_feeds
    return articles
