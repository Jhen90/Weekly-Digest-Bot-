import pytest
from unittest.mock import patch, MagicMock
from src.pulse import Article
from src.pulse.extract import extract_article_text
from datetime import datetime, timezone

@pytest.fixture
def sample_article():
    return Article(
        title="Test Article",
        url="https://example.com/article",
        source_name="Test",
        published=datetime.now(timezone.utc),
        feed_summary="Feed summary",
    )

def test_extract_returns_none_on_request_error(sample_article):
    with patch("src.pulse.extract.httpx.get") as mock_get:
        mock_get.side_effect = Exception("Network error")
        result = extract_article_text(sample_article)
        assert result is None

def test_extract_returns_text_content(sample_article):
    with patch("src.pulse.extract.httpx.get") as mock_get:
        mock_response = MagicMock()
        mock_response.text = (
            "<html><body><article>This is the article content. It contains more "
            "than one hundred characters so that the extraction length check "
            "will pass during testing.</article></body></html>"
        )
        mock_get.return_value = mock_response

        result = extract_article_text(sample_article)
        assert result is not None
        assert "article content" in result

def test_extract_returns_none_for_very_short_content(sample_article):
    with patch("src.pulse.extract.httpx.get") as mock_get:
        mock_response = MagicMock()
        mock_response.text = "<html><body>Hi</body></html>"
        mock_get.return_value = mock_response

        result = extract_article_text(sample_article)
        assert result is None
