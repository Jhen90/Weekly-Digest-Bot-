from typing import Optional
import httpx
from bs4 import BeautifulSoup
import logging

log = logging.getLogger(__name__)

def extract_article_text(article) -> Optional[str]:
    """
    Fetch article URL and extract main text content.
    Returns None on any failure; caller falls back to feed_summary.
    """
    if not article.url:
        return None

    try:
        response = httpx.get(
            article.url,
            timeout=5.0,
            headers={"User-Agent": "Pulse/1.0 (+https://github.com/jhen90)"}
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Remove script and style
        for tag in soup(["script", "style"]):
            tag.decompose()

        # Try to find main content area
        text = None
        for selector in ["article", "main", ".content", ".post", ".entry-content"]:
            elem = soup.select_one(selector)
            if elem:
                text = elem.get_text(separator="\n", strip=True)
                break

        if not text:
            text = soup.body.get_text(separator="\n", strip=True) if soup.body else None

        # Trim to reasonable length (avoid huge pages)
        if text and len(text) > 5000:
            text = text[:5000] + "..."

        return text if text and len(text) > 100 else None

    except Exception as e:
        log.debug(f"Failed to extract {article.url}: {e}")
        return None
