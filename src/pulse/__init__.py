from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

@dataclass
class Article:
    """A news article from an RSS feed."""
    title: str
    url: str
    source_name: str
    published: datetime
    feed_summary: str  # fallback summary from the feed
    topic: Optional[str] = None
    score: float = 0.0
    full_text: Optional[str] = None
    summary: Optional[str] = None
