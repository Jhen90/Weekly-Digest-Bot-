import pytest
from unittest.mock import patch, MagicMock
from src.pulse import Article
from src.pulse.summarize import summarize_article
from datetime import datetime, timezone

@pytest.fixture
def sample_article():
    return Article(
        title="Test Article",
        url="https://example.com/article",
        source_name="Test",
        published=datetime.now(timezone.utc),
        feed_summary="Feed summary text",
        full_text="Full article body text",
    )

def test_summarize_returns_feed_summary_without_api_key(sample_article):
    """Without API key, should return the feed summary."""
    result = summarize_article(sample_article, api_key=None)
    assert result == sample_article.feed_summary

def test_summarize_returns_feed_summary_on_api_error(sample_article):
    """On API error, should fall back to feed summary."""
    with patch("src.pulse.summarize.Anthropic") as mock_anthropic:
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = Exception("API error")
        mock_anthropic.return_value = mock_client

        result = summarize_article(sample_article, api_key="test-key")
        assert result == sample_article.feed_summary

def test_summarize_returns_claude_response(sample_article):
    """With valid API key and response, should return Claude summary."""
    with patch("src.pulse.summarize.Anthropic") as mock_anthropic:
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(type="text", text="The upshot: test summary")]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client

        result = summarize_article(sample_article, api_key="test-key")
        assert "The upshot" in result
