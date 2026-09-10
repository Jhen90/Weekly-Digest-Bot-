import pytest
from datetime import datetime, timezone
from src.pulse import Article
from src.pulse.render import render_digest

@pytest.fixture
def sample_digest():
    articles = {
        "AI + Nonprofits": [
            Article(
                title="Nonprofit AI tool launches",
                url="https://example.com/1",
                source_name="SSIR",
                published=datetime(2026, 9, 8, 10, 0, 0, tzinfo=timezone.utc),
                feed_summary="A new tool",
                topic="AI + Nonprofits",
                score=50.0,
                summary="The upshot: nonprofits now have access to AI.",
            )
        ],
        "AI + Women": [],
        "Human-Centered Design": [],
        "AI News & Developments": [],
    }
    return articles

def test_render_digest_returns_html_and_text(sample_digest):
    html, text = render_digest(sample_digest)
    assert isinstance(html, str)
    assert isinstance(text, str)
    assert "<html>" in html
    assert "Pulse" in text

def test_render_digest_includes_article_title(sample_digest):
    html, text = render_digest(sample_digest)
    assert "Nonprofit AI tool launches" in html
    assert "Nonprofit AI tool launches" in text

def test_render_digest_empty_shows_no_articles_message(sample_digest):
    empty_digest = {
        "AI + Nonprofits": [],
        "AI + Women": [],
        "Human-Centered Design": [],
        "AI News & Developments": [],
    }
    html, text = render_digest(empty_digest)
    assert "No new articles this week" in html
    assert "No new articles this week" in text

def test_render_digest_with_failed_feeds(sample_digest):
    failed_feeds = [("Example Feed", "timeout")]
    html, text = render_digest(sample_digest, failed_feeds)
    assert "Example Feed" in html
    assert "Example Feed" in text
