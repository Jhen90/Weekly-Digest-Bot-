import pytest
from pathlib import Path
from datetime import datetime, timezone
from src.pulse.feeds import fetch_feeds
from src.pulse.config import Config
from unittest.mock import patch, MagicMock

@pytest.fixture
def config_with_fixtures(tmp_path):
    """Mock config pointing to local fixture files."""
    config = MagicMock()
    config.sources = {
        "topics": {
            "ai_nonprofits": {
                "name": "AI + Nonprofits",
                "feeds": [
                    {"name": "Test Nonprofits", "url": "file://" + str(Path("tests/fixtures/ai_nonprofits.xml").absolute())}
                ]
            }
        }
    }
    return config

def test_fetch_feeds_parses_entries(config_with_fixtures):
    """Test that feeds are parsed and articles created."""
    with patch("src.pulse.feeds.feedparser.parse") as mock_parse:
        mock_feed = MagicMock()
        mock_feed.entries = [
            MagicMock(
                title="AI for nonprofits",
                link="https://example.com/1",
                summary="A story",
                published_parsed=(2026, 9, 8, 10, 0, 0, 0, 0, 0),
            )
        ]
        mock_parse.return_value = mock_feed

        articles = fetch_feeds(config_with_fixtures)
        assert len(articles) == 1
        assert articles[0].title == "AI for nonprofits"
        assert articles[0].source_name == "Test Nonprofits"

def test_fetch_feeds_filters_7_day_window(config_with_fixtures):
    """Test that only articles from the last 7 days are kept."""
    with patch("src.pulse.feeds.feedparser.parse") as mock_parse:
        mock_feed = MagicMock()
        mock_feed.entries = [
            MagicMock(
                title="Recent article",
                link="https://example.com/recent",
                summary="New",
                published_parsed=(2026, 9, 8, 10, 0, 0, 0, 0, 0),  # today
            ),
            MagicMock(
                title="Old article",
                link="https://example.com/old",
                summary="Old",
                published_parsed=(2026, 8, 25, 10, 0, 0, 0, 0, 0),  # 14 days ago
            )
        ]
        mock_parse.return_value = mock_feed

        articles = fetch_feeds(config_with_fixtures)
        assert len(articles) == 1
        assert articles[0].title == "Recent article"

def test_fetch_feeds_handles_missing_pubdate(config_with_fixtures):
    """Test that articles without pubDate are kept with today's date as fallback."""
    with patch("src.pulse.feeds.feedparser.parse") as mock_parse:
        mock_feed = MagicMock()
        mock_feed.entries = [
            MagicMock(
                title="Article with date",
                link="https://example.com/1",
                summary="Good",
                published_parsed=(2026, 9, 8, 10, 0, 0, 0, 0, 0),
            ),
            MagicMock(
                title="Article without date",
                link="https://example.com/2",
                summary="Bad",
                published_parsed=None,
                updated_parsed=None,
                created_parsed=None,
            )
        ]
        mock_parse.return_value = mock_feed

        articles = fetch_feeds(config_with_fixtures)
        assert len(articles) == 2
        assert articles[0].title == "Article with date"
        assert articles[1].title == "Article without date"
        # Article without date should have today's date
        from datetime import datetime, timezone
        today = datetime.now(timezone.utc).date()
        assert articles[1].published.date() == today
