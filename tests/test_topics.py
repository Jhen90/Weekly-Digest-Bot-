import pytest
from datetime import datetime, timezone, timedelta
from src.pulse import Article
from src.pulse.topics import filter_and_rank, normalize_url, similarity
from unittest.mock import MagicMock

@pytest.fixture
def sample_articles():
    """Create test articles."""
    return [
        Article(
            title="New AI tool for nonprofits",
            url="https://example.com/article1",
            source_name="Stanford Social Innovation Review",
            published=datetime.now(timezone.utc),
            feed_summary="A new nonprofit AI tool",
            topic=None,
            score=0.0,
        ),
        Article(
            title="Women in AI breaking barriers",
            url="https://example.com/article2",
            source_name="The 19th",
            published=datetime.now(timezone.utc) - timedelta(hours=1),
            feed_summary="Women leaders in artificial intelligence",
            topic=None,
            score=0.0,
        ),
        Article(
            title="Design thinking for user experience",
            url="https://example.com/article3",
            source_name="Nielsen Norman Group",
            published=datetime.now(timezone.utc) - timedelta(hours=2),
            feed_summary="How to apply design thinking principles",
            topic=None,
            score=0.0,
        ),
    ]

@pytest.fixture
def mock_config():
    config = MagicMock()
    config.sources = {
        "topics": {
            "ai_nonprofits": {
                "name": "AI + Nonprofits",
                "keywords": ["nonprofits", "philanthropy", "charities"],
                "feeds": [{"name": "Stanford Social Innovation Review"}],
            },
            "ai_women": {
                "name": "AI + Women",
                "keywords": ["women", "female", "gender", "equity"],
                "feeds": [{"name": "The 19th"}],
            },
            "hcd": {
                "name": "Human-Centered Design",
                "keywords": ["design", "ux", "user research"],
                "feeds": [{"name": "Nielsen Norman Group"}],
            },
        }
    }
    return config

def test_filter_and_rank_assigns_topics(sample_articles, mock_config):
    """Test that articles are assigned to topics."""
    result = filter_and_rank(sample_articles, mock_config)
    assert "AI + Nonprofits" in result
    assert "AI + Women" in result
    assert len(result["AI + Nonprofits"]) == 1
    assert result["AI + Nonprofits"][0].title == "New AI tool for nonprofits"

def test_filter_and_rank_respects_5_article_cap(sample_articles, mock_config):
    """Test that at most 5 articles per topic are kept."""
    # Add more articles to the same topic
    for i in range(10):
        sample_articles.append(
            Article(
                title=f"AI nonprofit article {i}",
                url=f"https://example.com/nonprofit{i}",
                source_name="Stanford Social Innovation Review",
                published=datetime.now(timezone.utc) - timedelta(hours=i),
                feed_summary="nonprofit related",
                topic=None,
                score=0.0,
            )
        )
    result = filter_and_rank(sample_articles, mock_config)
    assert len(result["AI + Nonprofits"]) <= 5

def test_normalize_url_removes_query_strings():
    """Test URL normalization."""
    url1 = "https://example.com/article?utm_source=feed&id=123"
    url2 = "https://example.com/article"
    assert normalize_url(url1) == normalize_url(url2)

def test_similarity_detects_identical_headlines():
    """Test headline similarity."""
    assert similarity("AI tool for nonprofits", "AI tool for nonprofits") > 0.95
    assert similarity("AI tool", "Machine learning") < 0.5

def test_filter_deduplicates_by_url(mock_config):
    """Test that duplicate URLs are removed."""
    articles = [
        Article(
            title="Same article",
            url="https://example.com/same",
            source_name="Stanford Social Innovation Review",
            published=datetime.now(timezone.utc),
            feed_summary="nonprofit",
            topic=None,
            score=0.0,
        ),
        Article(
            title="Same article",
            url="https://example.com/same?ref=twitter",  # same after normalization
            source_name="Stanford Social Innovation Review",
            published=datetime.now(timezone.utc),
            feed_summary="nonprofit",
            topic=None,
            score=0.0,
        ),
    ]
    result = filter_and_rank(articles, mock_config)
    assert len(result["AI + Nonprofits"]) == 1
