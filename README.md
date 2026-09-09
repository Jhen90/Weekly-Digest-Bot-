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
