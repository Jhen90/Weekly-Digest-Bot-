#!/usr/bin/env python3
"""
Pulse weekly digest entrypoint.

Usage:
  python -m scripts.send_weekly_digest --dry-run    (write HTML to disk)
  python -m scripts.send_weekly_digest               (send email, requires GMAIL_APP_PASSWORD)
"""

import argparse
import sys
import logging
from pathlib import Path

# Add parent to path so we can import src.pulse
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pulse.config import Config
from src.pulse.feeds import fetch_feeds
from src.pulse.topics import filter_and_rank
from src.pulse.render import render_digest

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="Pulse weekly digest bot")
    parser.add_argument("--dry-run", action="store_true", help="Write HTML to disk instead of sending email")
    args = parser.parse_args()

    try:
        log.info("Loading configuration...")
        config = Config()

        log.info("Fetching feeds...")
        articles = fetch_feeds(config)
        log.info(f"Fetched {len(articles)} articles from all feeds")

        log.info("Filtering and ranking by topic...")
        articles_by_topic = filter_and_rank(articles, config)

        total = sum(len(a) for a in articles_by_topic.values())
        log.info(f"Ranked {total} articles across topics")

        log.info("Rendering digest...")
        html, text = render_digest(
            articles_by_topic,
            getattr(config, "_failed_feeds", [])
        )

        if args.dry_run:
            output_file = Path("digest.html")
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(html)
            log.info(f"✓ Digest written to {output_file.absolute()}")
            print(f"\nOpen file://{output_file.absolute()} in your browser")
        else:
            log.info("Sending email... (not yet implemented)")

    except Exception as e:
        log.error(f"Failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
