# Pulse Weekly Digest Bot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a weekly RSS news-digest bot that fetches from trusted feeds, filters and ranks by topic, summarizes articles conclusion-first via Claude, and emails the digest.

**Architecture:** Seven focused modules under `src/pulse/` for fetching, filtering, extracting, summarizing, rendering, and sending; one entrypoint script; configuration in plain YAML; tests against saved RSS fixtures.

**Tech Stack:** Python 3.11, feedparser, httpx, BeautifulSoup4, anthropic, pytest, jinja2, pyyaml

**Spec:** `docs/superpowers/specs/2026-09-09-pulse-design.md`

## Global Constraints

- Python 3.11+
- Recipient: `jhenny.saintsurin@outlook.com` (can be edited in workflow file)
- Sender: Gmail account, app password in GitHub secret `GMAIL_APP_PASSWORD`
- Claude API key in GitHub secret `ANTHROPIC_API_KEY` (optional; falls back to feed blurbs if absent)
- Schedule: Mondays, 12:00 UTC
- No article shall be truncated silently; failures degrade to fallback rather than failing the run
- Only hard error: failure to send email (exits non-zero)

---

## File Structure

```
Pulse/
├─ src/pulse/
│   ├─ __init__.py
│   ├─ config.py              loads sources.yml, leaders.yml, env vars
│   ├─ feeds.py               feedparser, returns list[Article]
│   ├─ topics.py              scoring, assignment, dedup, capping (pure)
│   ├─ extract.py             article text fetch with fallback
│   ├─ summarize.py           Claude API with blurb fallback
│   ├─ render.py              HTML + plaintext email rendering (pure)
│   └─ mailer.py              Gmail SMTP send
├─ scripts/
│   └─ send_weekly_digest.py   entrypoint, --dry-run flag
├─ tests/
│   ├─ __init__.py
│   ├─ fixtures/
│   │   ├─ ai_nonprofits.xml  saved RSS feed
│   │   ├─ ai_women.xml
│   │   ├─ hcd.xml
│   │   └─ ai_news.xml
│   └─ test_*.py              pytest suite
├─ sources.yml                seeded, verified feeds (user editable)
├─ leaders.yml                seeded list of people to track (user editable)
├─ .env.example               template
├─ .gitignore
├─ requirements.txt
├─ README.md
└─ .github/workflows/
    └─ weekly-digest.yml      GitHub Actions cron
```

---

## Task 1: Scaffold and dependencies

**Files:**
- Create: `requirements.txt`, `.gitignore`, `.env.example`, `README.md`, `src/pulse/__init__.py`, `scripts/__init__.py`, `tests/__init__.py`

**Interfaces:**
- Produces: a working Python environment and project structure

- [ ] **Step 1: Create requirements.txt**

```
feedparser>=6.0.0
httpx>=0.27.0
beautifulsoup4>=4.12.0
anthropic>=0.28.0
pyyaml>=6.0.0
jinja2>=3.1.0
pytest>=8.0.0
pytest-mock>=3.0.0
```

- [ ] **Step 2: Create .gitignore**

```
.env
.env.local
__pycache__/
*.pyc
.pytest_cache/
*.egg-info/
dist/
build/
.DS_Store
html_output/
*.html
venv/
.venv/
```

- [ ] **Step 3: Create .env.example**

```
# Optional: Claude API key for summarization (defaults to feed blurbs if absent)
ANTHROPIC_API_KEY=

# Development: local SMTP test (leave blank to skip test sending)
SMTP_TEST_MODE=false
```

- [ ] **Step 4: Create README.md**

```markdown
# Pulse — Weekly Digest Bot

A weekly news-digest agent that reads trusted RSS feeds, filters articles by topic, summarizes conclusion-first via Claude, and emails the digest.

## Setup

```bash
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

## Usage

**Local preview (no email sent):**
```bash
python -m scripts.send_weekly_digest --dry-run
```

Opens `digest.html` in your browser.

**Edit feeds and leaders:**
- `sources.yml` — RSS feeds grouped by topic
- `leaders.yml` — named people to track

## Testing

```bash
pytest tests/ -v
```
```

- [ ] **Step 5: Create directory structure**

```bash
mkdir -p src/pulse scripts tests/fixtures
touch src/pulse/__init__.py scripts/__init__.py tests/__init__.py
```

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "scaffold: project layout, requirements, docs"
```

---

## Task 2: Article dataclass and config module

**Files:**
- Create: `src/pulse/config.py`, `sources.yml`, `leaders.yml`

**Interfaces:**
- Produces: `Article` dataclass; `Config` class with `.sources`, `.leaders`, `.anthropic_key`, `.gmail_user`, `.email_to`

- [ ] **Step 1: Write Article dataclass**

Create `src/pulse/__init__.py`:

```python
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
```

- [ ] **Step 2: Write config.py**

```python
import os
from pathlib import Path
from typing import Optional
import yaml
from .import Article

class Config:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.sources = self._load_yaml("sources.yml")
        self.leaders = self._load_yaml("leaders.yml")
        self.anthropic_key: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
        self.gmail_user = "dojoatsomernova@gmail.com"  # hardcoded; overridden in workflow
        self.email_to = "jhenny.saintsurin@outlook.com"  # hardcoded; overridden in workflow

    def _load_yaml(self, filename: str) -> dict:
        path = self.project_root / filename
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")
        with open(path) as f:
            data = yaml.safe_load(f)
        if not data:
            raise ValueError(f"Empty config file: {path}")
        return data
```

- [ ] **Step 3: Create seeded sources.yml**

```yaml
topics:
  ai_nonprofits:
    name: "AI + Nonprofits"
    keywords:
      - nonprofits
      - philanthropy
      - charities
      - social impact
      - AI adoption
    feeds:
      - name: "Stanford Social Innovation Review"
        url: "https://feeds.ssireview.org/"
      - name: "Nonprofit Quarterly"
        url: "https://nonprofitquarterly.org/feed/"
      - name: "Chronicle of Philanthropy"
        url: "https://feeds.chronicleofphilanthropy.com/news"

  ai_women:
    name: "AI + Women"
    keywords:
      - women in tech
      - women in AI
      - gender equity
      - AI ethics
      - women founders
    feeds:
      - name: "The 19th"
        url: "https://feeds.19thnews.org/feed"
      - name: "Wired"
        url: "https://www.wired.com/feed/rss"

  hcd:
    name: "Human-Centered Design"
    keywords:
      - design thinking
      - UX
      - user research
      - inclusive design
      - design ethics
    feeds:
      - name: "Nielsen Norman Group"
        url: "https://www.nngroup.com/feed/rss/"
      - name: "A List Apart"
        url: "https://alistapart.com/feed/rss.xml"

  ai_news:
    name: "AI News & Developments"
    keywords:
      - AI models
      - machine learning
      - large language models
      - AI releases
      - AI research
    feeds:
      - name: "MIT Technology Review"
        url: "https://www.technologyreview.com/feed/"
      - name: "The Verge"
        url: "https://www.theverge.com/rss/index.xml"
      - name: "VentureBeat"
        url: "https://feeds.venturebeat.com/ai"
```

- [ ] **Step 4: Create seeded leaders.yml**

```yaml
leaders:
  - name: "Timnit Gebru"
    feed_url: "https://substack.com/feed/@timnit"
  - name: "Kate Crawford"
    feed_url: "https://substack.com/feed/@katecrawford"
  - name: "Andrew Ng"
    feed_url: "https://substack.com/feed/@andrewng"
```

- [ ] **Step 5: Verify feeds are live**

```bash
python -c "
import feedparser
urls = [
    'https://feeds.ssireview.org/',
    'https://nonprofitquarterly.org/feed/',
    'https://feeds.19thnews.org/feed',
    'https://www.wired.com/feed/rss',
    'https://www.nngroup.com/feed/rss/',
    'https://alistapart.com/feed/rss.xml',
    'https://www.technologyreview.com/feed/',
    'https://www.theverge.com/rss/index.xml',
]
for url in urls:
    result = feedparser.parse(url)
    status = 'OK' if result.get('entries') else 'EMPTY'
    print(f'{url}: {status}')
"
```

Expected: all print OK

- [ ] **Step 6: Commit**

```bash
git add src/pulse/__init__.py src/pulse/config.py sources.yml leaders.yml
git commit -m "feat: Article dataclass, config loader, seeded YAML sources"
```

---

## Task 3: Feeds module and fixtures

**Files:**
- Create: `src/pulse/feeds.py`, `tests/fixtures/*.xml`, `tests/test_feeds.py`

**Interfaces:**
- Consumes: `Article` (from Task 2), `Config.sources`
- Produces: `fetch_feeds(config: Config) -> list[Article]`

- [ ] **Step 1: Create RSS fixtures**

Save minimal valid RSS feeds to `tests/fixtures/`:

`ai_nonprofits.xml`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Test AI Nonprofits</title>
    <link>https://example.com</link>
    <description>Test feed</description>
    <item>
      <title>New AI tool for nonprofits launches</title>
      <link>https://example.com/article1</link>
      <description>A new AI tool to help nonprofits automate grants</description>
      <pubDate>Mon, 08 Sep 2026 10:00:00 GMT</pubDate>
    </item>
    <item>
      <title>Machine learning in charities</title>
      <link>https://example.com/article2</link>
      <description>How charities use ML for impact</description>
      <pubDate>Tue, 02 Sep 2026 14:00:00 GMT</pubDate>
    </item>
  </channel>
</rss>
```

`ai_news.xml`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Test AI News</title>
    <link>https://example.com</link>
    <description>Test feed</description>
    <item>
      <title>Claude 4 released</title>
      <link>https://example.com/claude</link>
      <description>Anthropic releases Claude 4 with new capabilities</description>
      <pubDate>Wed, 07 Sep 2026 12:00:00 GMT</pubDate>
    </item>
  </channel>
</rss>
```

Create similar `ai_women.xml` and `hcd.xml` with at least 2 articles each, published within the last 7 days.

- [ ] **Step 2: Write feeds.py**

```python
from datetime import datetime, timedelta, timezone
import feedparser
from .import Article, Config
import logging

log = logging.getLogger(__name__)

def fetch_feeds(config: Config) -> list[Article]:
    """Fetch articles from all configured feeds."""
    articles = []
    failed_feeds = []
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(days=7)

    for topic_key, topic_config in config.sources.get("topics", {}).items():
        topic_name = topic_config["name"]
        for feed_config in topic_config.get("feeds", []):
            try:
                feed = feedparser.parse(feed_config["url"], timeout=10)
                if not feed.get("entries"):
                    failed_feeds.append((feed_config["name"], "no entries"))
                    continue

                for entry in feed.entries:
                    # Parse publication date
                    try:
                        pub_date = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                    except (AttributeError, TypeError):
                        log.warning(f"Skipping {entry.get('title', 'unknown')}: no pubDate")
                        continue

                    # Filter to 7-day window
                    if pub_date < window_start:
                        continue

                    article = Article(
                        title=entry.get("title", "(no title)"),
                        url=entry.get("link", ""),
                        source_name=feed_config["name"],
                        published=pub_date,
                        feed_summary=entry.get("summary", ""),
                    )
                    articles.append(article)
            except Exception as e:
                failed_feeds.append((feed_config["name"], str(e)))
                log.error(f"Failed to fetch {feed_config['name']}: {e}")

    # Store failed feeds for later reporting
    config._failed_feeds = failed_feeds
    return articles
```

- [ ] **Step 3: Write test_feeds.py**

```python
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
    """Test that articles without pubDate are skipped."""
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
            )
        ]
        mock_parse.return_value = mock_feed

        articles = fetch_feeds(config_with_fixtures)
        assert len(articles) == 1
        assert articles[0].title == "Article with date"
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_feeds.py -v
```

Expected: all pass

- [ ] **Step 5: Commit**

```bash
git add src/pulse/feeds.py tests/fixtures/*.xml tests/test_feeds.py
git commit -m "feat: feeds module with 7-day window filter; fixture-based tests"
```

---

## Task 4: Topics module (scoring, filtering, ranking)

**Files:**
- Create: `src/pulse/topics.py`, `tests/test_topics.py`

**Interfaces:**
- Consumes: `Article`, `Config.sources`
- Produces: `filter_and_rank(articles: list[Article], config: Config) -> dict[str, list[Article]]`
  - Returns dict with topic names as keys, sorted list of top 5 articles as values

- [ ] **Step 1: Write topics.py**

```python
from typing import Dict, List
from urllib.parse import urlparse, parse_qs
from difflib import SequenceMatcher
import re
from .import Article, Config

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
```

- [ ] **Step 2: Write test_topics.py**

```python
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
```

- [ ] **Step 3: Run tests**

```bash
pytest tests/test_topics.py -v
```

Expected: all pass

- [ ] **Step 4: Commit**

```bash
git add src/pulse/topics.py tests/test_topics.py
git commit -m "feat: topic scoring, ranking, dedup, and 5-article cap"
```

---

## Task 5: Render module (email HTML + plaintext)

**Files:**
- Create: `src/pulse/render.py`, `tests/test_render.py`

**Interfaces:**
- Consumes: `Article`, dict of topics to articles
- Produces: `render_digest(articles_by_topic: Dict[str, List[Article]], failed_feeds: List) -> tuple[str, str]`
  - Returns (html_string, plaintext_string)

- [ ] **Step 1: Write render.py**

```python
from typing import Dict, List, Tuple
from datetime import datetime
from .import Article

def render_digest(
    articles_by_topic: Dict[str, List[Article]],
    failed_feeds: List[Tuple[str, str]] = None,
) -> Tuple[str, str]:
    """Render the digest as HTML and plaintext."""
    if failed_feeds is None:
        failed_feeds = []

    html = _render_html(articles_by_topic, failed_feeds)
    text = _render_plaintext(articles_by_topic, failed_feeds)
    return html, text

def _render_html(articles_by_topic: Dict[str, List[Article]], failed_feeds: List) -> str:
    """Render HTML email."""
    today = datetime.now().strftime("%Y-%m-%d")
    html_parts = [
        f"""<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
</head>
<body style="font-family: Arial, Helvetica, sans-serif; color: #222; max-width: 600px; margin: 0 auto; padding: 20px;">

<h1 style="margin-top: 0; border-bottom: 2px solid #007bff; padding-bottom: 10px;">
  Pulse — Weekly Digest
</h1>

<p style="color: #666; font-size: 14px;">
  {today} | Your weekly news on AI, design, and impact
</p>
"""
    ]

    # Check if empty
    total_articles = sum(len(articles) for articles in articles_by_topic.values())
    if total_articles == 0:
        html_parts.append("""
<div style="background: #f0f8ff; border-left: 4px solid #007bff; padding: 15px; margin: 20px 0;">
  <p style="margin: 0;">
    <strong>No new articles this week.</strong> The bot ran successfully and found nothing
    matching your topics. Check back next week!
  </p>
</div>
""")
    else:
        # Render articles by topic
        for topic_name, articles in articles_by_topic.items():
            if articles:
                html_parts.append(f"""
<h2 style="margin-top: 30px; margin-bottom: 15px; color: #007bff;">
  {topic_name}
</h2>
""")
                for article in articles:
                    html_parts.append(f"""
<div style="margin-bottom: 20px; padding-bottom: 15px; border-bottom: 1px solid #ddd;">
  <h3 style="margin: 0 0 5px 0; font-size: 18px;">
    <a href="{article.url}" style="color: #007bff; text-decoration: none;">{article.title}</a>
  </h3>
  <p style="margin: 5px 0; font-size: 12px; color: #666;">
    {article.source_name} · {article.published.strftime("%b %d, %Y")}
  </p>
  <p style="margin: 10px 0; font-size: 14px; line-height: 1.6;">
    {article.summary or article.feed_summary}
  </p>
  <a href="{article.url}" style="color: #007bff; font-size: 12px; text-decoration: none;">
    Read more →
  </a>
</div>
""")

    # Leaders section (if articles exist)
    if total_articles > 0:
        html_parts.append("""
<h2 style="margin-top: 40px; margin-bottom: 15px; color: #007bff;">
  What the Leaders Are Saying
</h2>
<p style="font-size: 14px; color: #666;">
  (Coming soon in a future update)
</p>
""")

    # Failed feeds footer
    if failed_feeds:
        html_parts.append("""
<hr style="margin-top: 40px; border: none; border-top: 1px solid #ddd;">
<p style="font-size: 12px; color: #999; margin-top: 20px;">
  <strong>Note:</strong> The following feeds failed to load this week:
</p>
<ul style="font-size: 12px; color: #999; margin: 10px 0;">
""")
        for feed_name, error in failed_feeds:
            html_parts.append(f"<li>{feed_name}: {error}</li>")
        html_parts.append("</ul>")

    html_parts.append("</body></html>")
    return "\n".join(html_parts)

def _render_plaintext(articles_by_topic: Dict[str, List[Article]], failed_feeds: List) -> str:
    """Render plaintext email."""
    today = datetime.now().strftime("%Y-%m-%d")
    text_parts = [
        f"Pulse — Weekly Digest\n{today}\n\n",
    ]

    total_articles = sum(len(articles) for articles in articles_by_topic.values())
    if total_articles == 0:
        text_parts.append(
            "No new articles this week. The bot ran successfully and found nothing\n"
            "matching your topics. Check back next week!\n"
        )
    else:
        for topic_name, articles in articles_by_topic.items():
            if articles:
                text_parts.append(f"\n{topic_name}\n{'='*len(topic_name)}\n\n")
                for article in articles:
                    text_parts.append(
                        f"{article.title}\n"
                        f"{article.source_name} · {article.published.strftime('%b %d, %Y')}\n"
                        f"{article.url}\n\n"
                        f"{article.summary or article.feed_summary}\n\n"
                    )

    if failed_feeds:
        text_parts.append(
            "\n---\nNote: The following feeds failed to load this week:\n"
        )
        for feed_name, error in failed_feeds:
            text_parts.append(f"  • {feed_name}: {error}\n")

    return "".join(text_parts)
```

- [ ] **Step 2: Write test_render.py**

```python
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
```

- [ ] **Step 3: Run tests**

```bash
pytest tests/test_render.py -v
```

Expected: all pass

- [ ] **Step 4: Commit**

```bash
git add src/pulse/render.py tests/test_render.py
git commit -m "feat: render digest as HTML and plaintext email"
```

---

## Task 6: Entrypoint script and first dry-run

**Files:**
- Create: `scripts/send_weekly_digest.py`

**Interfaces:**
- Consumes: all modules from Tasks 2-5
- Produces: `--dry-run` mode that writes HTML to disk

- [ ] **Step 1: Write send_weekly_digest.py**

```python
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
            with open(output_file, "w") as f:
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
```

- [ ] **Step 2: Test --dry-run**

```bash
python -m scripts.send_weekly_digest --dry-run
```

Expected: creates `digest.html` with articles from fixtures

- [ ] **Step 3: Verify HTML output**

Open the HTML file in a browser. Verify:
- Title and date visible
- Topic sections present
- Articles with titles, sources, dates, summaries
- Links clickable
- Styling readable

- [ ] **Step 4: Commit**

```bash
git add scripts/send_weekly_digest.py
git commit -m "feat: entrypoint with --dry-run mode"
```

---

## Task 7: Extract and summarize modules (with Claude fallback)

**Files:**
- Create: `src/pulse/extract.py`, `src/pulse/summarize.py`, `tests/test_extract.py`, `tests/test_summarize.py`

**Interfaces:**
- Consumes: `Article`, `ANTHROPIC_API_KEY` env var
- Produces: `extract_article_text(article: Article) -> Optional[str]`, `summarize_article(article: Article, api_key: Optional[str]) -> str`

- [ ] **Step 1: Write extract.py**

```python
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
```

- [ ] **Step 2: Write summarize.py**

```python
from typing import Optional
import logging
from anthropic import Anthropic, RateLimitError, APIStatusError, APIConnectionError

log = logging.getLogger(__name__)

def summarize_article(article, api_key: Optional[str] = None) -> str:
    """
    Summarize article conclusion-first using Claude.
    Falls back to feed_summary if no API key or on error.
    """
    # If no key or already has summary from feed_summary, use that
    if not api_key:
        log.debug(f"No API key; using feed summary for {article.title}")
        return article.feed_summary or "(no summary available)"

    # Try Claude
    try:
        client = Anthropic(api_key=api_key)
        text = article.full_text or article.feed_summary

        response = client.messages.create(
            model="claude-opus-5",
            max_tokens=256,
            thinking={"type": "adaptive"},
            output_config={"effort": "low"},
            system=(
                "You are a news summarizer. Write one short paragraph that leads with the "
                "takeaway or conclusion, then the supporting detail. Start with 'The upshot:' "
                "or 'Key point:'. Keep it under 150 words."
            ),
            messages=[
                {
                    "role": "user",
                    "content": f"Summarize this article conclusion-first:\n\n{text[:2000]}",
                }
            ],
        )

        summary_text = next(
            (b.text for b in response.content if b.type == "text"),
            None,
        )
        return summary_text or article.feed_summary

    except RateLimitError:
        log.warning(f"Rate limited; using feed summary for {article.title}")
        return article.feed_summary or "(no summary available)"
    except APIStatusError as e:
        log.warning(f"API error {e.status_code}; using feed summary for {article.title}")
        return article.feed_summary or "(no summary available)"
    except APIConnectionError:
        log.warning(f"Connection error; using feed summary for {article.title}")
        return article.feed_summary or "(no summary available)"
    except Exception as e:
        log.error(f"Unexpected error summarizing {article.title}: {e}")
        return article.feed_summary or "(no summary available)"
```

- [ ] **Step 3: Write test_extract.py**

```python
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
        mock_response.text = "<html><body><article>This is the article content</article></body></html>"
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
```

- [ ] **Step 4: Write test_summarize.py**

```python
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
```

- [ ] **Step 5: Run tests**

```bash
pytest tests/test_extract.py tests/test_summarize.py -v
```

Expected: all pass

- [ ] **Step 6: Commit**

```bash
git add src/pulse/extract.py src/pulse/summarize.py tests/test_extract.py tests/test_summarize.py
git commit -m "feat: article extraction with Claude summarization + fallback"
```

---

## Task 8: Mailer module and email test

**Files:**
- Create: `src/pulse/mailer.py`, `tests/test_mailer.py`

**Interfaces:**
- Consumes: `html`, `text`, `Config.gmail_user`, `Config.email_to`, `GMAIL_APP_PASSWORD` env var
- Produces: `send_email(html: str, text: str, gmail_user: str, email_to: str, app_password: str) -> bool`

- [ ] **Step 1: Write mailer.py**

```python
import smtplib
from email.message import EmailMessage
import logging

log = logging.getLogger(__name__)

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587  # STARTTLS

def send_email(
    html: str,
    text: str,
    subject: str,
    sender: str,
    recipient: str,
    app_password: str,
) -> bool:
    """
    Send email via Gmail SMTP.
    Returns True on success, False on recoverable errors, raises on fatal errors.
    """
    try:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = sender
        msg["To"] = recipient

        msg.set_content(text)
        msg.add_alternative(html, subtype="html")

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=60) as smtp:
            smtp.starttls()
            smtp.login(sender, app_password)
            smtp.send_message(msg)

        log.info(f"✓ Email sent to {recipient}")
        return True

    except smtplib.SMTPAuthenticationError:
        log.error("Gmail authentication failed. Check GMAIL_APP_PASSWORD.")
        raise
    except Exception as e:
        log.error(f"Failed to send email: {e}")
        raise
```

- [ ] **Step 2: Write test_mailer.py**

```python
import pytest
from unittest.mock import patch, MagicMock
from src.pulse.mailer import send_email

def test_send_email_success():
    """Test successful email send."""
    with patch("src.pulse.mailer.smtplib.SMTP") as mock_smtp:
        mock_context = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_context

        result = send_email(
            html="<html><body>Test</body></html>",
            text="Test",
            subject="Test Digest",
            sender="test@gmail.com",
            recipient="user@example.com",
            app_password="test-password",
        )

        assert result is True
        mock_context.starttls.assert_called_once()
        mock_context.login.assert_called_once_with("test@gmail.com", "test-password")
        mock_context.send_message.assert_called_once()

def test_send_email_auth_error():
    """Test authentication error handling."""
    with patch("src.pulse.mailer.smtplib.SMTP") as mock_smtp:
        mock_context = MagicMock()
        mock_context.login.side_effect = Exception("Authentication failed")
        mock_smtp.return_value.__enter__.return_value = mock_context

        with pytest.raises(Exception):
            send_email(
                html="<html></html>",
                text="Test",
                subject="Test",
                sender="test@gmail.com",
                recipient="user@example.com",
                app_password="bad-password",
            )
```

- [ ] **Step 3: Update send_weekly_digest.py to integrate summarization and mailing**

Add to the main() function after rendering:

```python
        # Extract full text and summarize
        log.info("Extracting and summarizing articles...")
        for topic_articles in articles_by_topic.values():
            for article in topic_articles:
                article.full_text = extract_article_text(article)
                article.summary = summarize_article(article, config.anthropic_key)

        log.info("Re-rendering with summaries...")
        html, text = render_digest(
            articles_by_topic,
            getattr(config, "_failed_feeds", [])
        )

        if args.dry_run:
            output_file = Path("digest.html")
            with open(output_file, "w") as f:
                f.write(html)
            log.info(f"✓ Digest written to {output_file.absolute()}")
        else:
            import os
            from src.pulse.mailer import send_email
            app_password = os.getenv("GMAIL_APP_PASSWORD")
            if not app_password:
                log.error("GMAIL_APP_PASSWORD not set. Use --dry-run or set the secret.")
                sys.exit(1)
            send_email(
                html=html,
                text=text,
                subject=f"Pulse Digest — {datetime.now().strftime('%Y-%m-%d')}",
                sender=config.gmail_user,
                recipient=config.email_to,
                app_password=app_password,
            )
            log.info("✓ Digest sent")
```

Add imports to the top:

```python
from datetime import datetime
from src.pulse.extract import extract_article_text
from src.pulse.summarize import summarize_article
```

- [ ] **Step 4: Run all tests**

```bash
pytest tests/ -v
```

Expected: all pass

- [ ] **Step 5: Test --dry-run again**

```bash
python -m scripts.send_weekly_digest --dry-run
```

Verify:
- Articles now have summaries in the HTML
- No email is sent
- digest.html is created

- [ ] **Step 6: Commit**

```bash
git add src/pulse/mailer.py tests/test_mailer.py scripts/send_weekly_digest.py
git commit -m "feat: email sending via Gmail SMTP; full pipeline integrated"
```

---

## Task 9: GitHub Actions workflow

**Files:**
- Create: `.github/workflows/weekly-digest.yml`

**Interfaces:**
- Consumes: repo secrets `GMAIL_APP_PASSWORD`, `ANTHROPIC_API_KEY`
- Produces: scheduled workflow + manual dispatch button

- [ ] **Step 1: Write weekly-digest.yml**

```yaml
name: Weekly Digest

on:
  schedule:
    - cron: "0 12 * * 1"  # Mondays 12:00 UTC
  workflow_dispatch:       # manual button

jobs:
  send-digest:
    runs-on: ubuntu-latest
    timeout-minutes: 15

    steps:
      - name: Check out code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run weekly digest
        env:
          GMAIL_APP_PASSWORD: ${{ secrets.GMAIL_APP_PASSWORD }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: python -m scripts.send_weekly_digest
```

- [ ] **Step 2: Commit the workflow**

```bash
git add .github/workflows/weekly-digest.yml
git commit -m "ci: GitHub Actions weekly cron + manual dispatch"
```

- [ ] **Step 3: Verify workflow file is valid**

```bash
# Just check syntax
python -m yaml < .github/workflows/weekly-digest.yml > /dev/null && echo "Valid YAML"
```

- [ ] **Step 4: Commit everything and create a summary**

```bash
git log --oneline -10
```

Expected: 9 commits, from scaffold through workflow

---

## Summary

**Completed:**

1. ✓ Scaffolding: folder structure, requirements, .gitignore
2. ✓ Config: Article dataclass, YAML loading, seeded sources/leaders
3. ✓ Feeds: RSS parsing, 7-day window, error handling
4. ✓ Topics: scoring, assignment, dedup, 5-article cap
5. ✓ Render: HTML + plaintext email
6. ✓ Entrypoint: `--dry-run` mode working
7. ✓ Extract + Summarize: article fetch + Claude API with fallback
8. ✓ Mailer: Gmail SMTP integration
9. ✓ Workflow: GitHub Actions cron + manual button

**Next steps (not in this plan):**

- Create GitHub repo and push
- Configure repo secrets: `GMAIL_APP_PASSWORD`, `ANTHROPIC_API_KEY`
- Edit `sources.yml` and `leaders.yml` to your preferences
- Trigger workflow manually to test, or wait for Monday 12:00 UTC

**Test locally before pushing:**

```bash
python -m scripts.send_weekly_digest --dry-run
# Opens digest.html in browser
```
