from typing import Dict, List
from urllib.parse import urlparse, parse_qs
from difflib import SequenceMatcher
import re
from . import Article
from .config import Config

def normalize_url(url: str) -> str:
    """Remove query strings and fragments for deduplication."""
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

def similarity(a: str, b: str) -> float:
    """Compute headline similarity (0-1)."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def score_article(article: Article, topic_keywords: List[str], is_home_topic: bool) -> float:
    """Score an article for a specific topic."""
    score = 100.0 if is_home_topic else 0.0  # base score for home topic

    keywords_lower = [kw.lower() for kw in topic_keywords]
    text = f"{article.title} {article.feed_summary}".lower()

    # Headline keywords: 3 points each
    for kw in keywords_lower:
        if kw in article.title.lower():
            score += 3.0

    # Summary keywords: 1 point each
    for kw in keywords_lower:
        if kw in article.feed_summary.lower():
            score += 1.0

    return score

def filter_and_rank(articles: List[Article], config: Config) -> Dict[str, List[Article]]:
    """
    Filter and rank articles by topic.
    Returns dict of topic names to sorted article lists (max 5 each).
    """
    result = {}
    topics_config = config.sources.get("topics", {})

    # Initialize result dict
    for topic_key, topic_data in topics_config.items():
        result[topic_data["name"]] = []

    # Score each article for each topic
    for article in articles:
        scored = {}
        for topic_key, topic_data in topics_config.items():
            topic_name = topic_data["name"]
            keywords = topic_data.get("keywords", [])

            # Find if this article's feed is a home topic for this topic
            is_home = False
            for feed in topic_data.get("feeds", []):
                if feed["name"] == article.source_name:
                    is_home = True
                    break

            score = score_article(article, keywords, is_home)
            scored[topic_name] = score

        # Assign to highest-scoring topic
        if scored:
            best_topic = max(scored, key=scored.get)
            article.topic = best_topic
            article.score = scored[best_topic]

    # Deduplicate by URL and headline
    for topic_name in result:
        seen_urls = set()
        seen_headlines = set()
        deduped = []

        for article in articles:
            if article.topic != topic_name:
                continue

            norm_url = normalize_url(article.url)
            if norm_url in seen_urls:
                continue

            # Check headline similarity
            is_duplicate = False
            for seen_headline in seen_headlines:
                if similarity(article.title, seen_headline) > 0.8:
                    is_duplicate = True
                    break

            if is_duplicate:
                continue

            seen_urls.add(norm_url)
            seen_headlines.add(article.title)
            deduped.append(article)

        # Sort by score (desc) then by date (desc)
        deduped.sort(key=lambda a: (-a.score, -a.published.timestamp()))

        # Apply relevance floor (min score 1.0 to keep)
        filtered = [a for a in deduped if a.score >= 1.0]

        # Cap at 5 per topic
        result[topic_name] = filtered[:5]

    return result
