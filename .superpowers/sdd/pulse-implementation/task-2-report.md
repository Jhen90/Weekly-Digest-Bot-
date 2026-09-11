# Task 2 Report: Article dataclass and config module

**Commit:** f81db05

## Files created/modified

- `src/pulse/__init__.py` — Added `Article` dataclass exactly as specified (title, url, source_name, published, feed_summary, topic, score, full_text, summary).
- `src/pulse/config.py` — New `Config` class exactly as specified: loads `sources.yml` and `leaders.yml` from project root, reads `ANTHROPIC_API_KEY` from env, hardcodes `gmail_user` and `email_to`.
- `sources.yml` — Created with the 4 topics (ai_nonprofits, ai_women, hcd, ai_news) and 10 feeds, keywords preserved as specified.
- `leaders.yml` — Created with exact content specified in the task (3 leaders: Timnit Gebru, Kate Crawford, Andrew Ng, all with `substack.com/feed/@handle`-style URLs).

## Feed verification results (sources.yml)

Ran the verification script against the 10 URLs given in the task. **5 of 10 originally-specified URLs failed** (DNS failures on defunct FeedBurner-style `feeds.*` subdomains, a dead redirect, and a hard 404). I researched and substituted working replacement URLs for each failure, then re-verified all 10 against the final `sources.yml` — **all 10 now return entries** (7–50 entries each, all with September 2026 publish dates except A List Apart, whose latest post is from 2026-06-30 — it's a low-cadence blog but the feed itself is live).

| Topic | Source | Original URL (from task) | Status | Final URL used |
|---|---|---|---|---|
| ai_nonprofits | Stanford Social Innovation Review | `https://feeds.ssireview.org/` | **FAILED** (DNS: getaddrinfo failed — dead FeedBurner subdomain) | `https://ssir.org/site/rss_2.0` (found via `<link rel="alternate">` on ssir.org; 40 entries) |
| ai_nonprofits | Nonprofit Quarterly | `https://nonprofitquarterly.org/feed/` | OK (12 entries) | unchanged |
| ai_nonprofits | Chronicle of Philanthropy | `https://feeds.chronicleofphilanthropy.com/news` | **FAILED** (SSL error / connection reset — dead subdomain) | `https://www.philanthropy.com/feed` (10 entries) |
| ai_women | The 19th | `https://feeds.19thnews.org/feed` | **FAILED** (DNS: getaddrinfo failed — dead FeedBurner subdomain) | `https://19thnews.org/feed/` (20 entries) |
| ai_women | Wired | `https://www.wired.com/feed/rss` | OK (50 entries) | unchanged |
| hcd | Nielsen Norman Group | `https://www.nngroup.com/feed/rss/` | OK (20 entries) | unchanged |
| hcd | A List Apart | `https://alistapart.com/feed/rss.xml` | **FAILED** (404, malformed) | `https://alistapart.com/main/feed/` (found via `<link rel="alternate">`; 20 entries, latest 2026-06-30) |
| ai_news | MIT Technology Review | `https://www.technologyreview.com/feed/` | OK (10 entries) | unchanged |
| ai_news | The Verge | `https://www.theverge.com/rss/index.xml` | OK (10 entries) | unchanged |
| ai_news | VentureBeat | `https://feeds.venturebeat.com/ai` | **FAILED** (DNS resolves to an unrelated Google IP returning 404 — dead FeedBurner domain) | `https://venturebeat.com/category/ai/feed/` (7 entries) |

**Important implementation note for Task 3 (feeds module):** VentureBeat's feed returns HTTP 429 (rate limited) unless a browser-like `User-Agent` header is set on the request (feedparser's default UA gets blocked). The feeds module should set `feedparser.USER_AGENT` or pass a `User-Agent` header, e.g.:
```python
feedparser.USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
```
Without this, VentureBeat fetches will silently return zero entries in production.

## leaders.yml — concern

The task specified exact content for `leaders.yml` using URLs of the form `https://substack.com/feed/@handle`. I verified these against the live web and **all 3 fail** (HTTP 404 / malformed XML — `substack.com/feed/@handle` is not a valid Substack feed URL pattern). I wrote the file with the exact content as instructed (since the task specified it verbatim, unlike sources.yml which explicitly asked me to fetch-verify and fix), but investigated real alternatives and found none are viable as drop-in replacements:
- **Timnit Gebru**: no personal Substack found; she publishes via DAIR Institute (dair-institute.org), which has no discoverable RSS feed (`/feed/`, `/rss/`, `/blog/feed/` all 404).
- **Kate Crawford**: does have a real Substack (`katecrawford.substack.com`), but it is **invite-only** — `https://katecrawford.substack.com/feed` returns HTTP 400 "This publication is invite-only," so its feed is not publicly fetchable.
- **Andrew Ng**: publishes "The Batch" via deeplearning.ai, which has no discoverable public RSS feed (`/the-batch/feed/`, `/the-batch/rss/`, `/rss/` all 404).

**Recommendation:** before Task 3's feeds module is exercised against `leaders.yml` in production, a human should pick three AI leaders who actually maintain public RSS-enabled blogs/newsletters (e.g., a public Substack with a working `/feed` endpoint), since the currently-seeded list will fetch zero entries for all three leaders.

## Config class test output

```
Topics loaded: ['ai_nonprofits', 'ai_women', 'hcd', 'ai_news']
Leaders loaded: 3
Gmail user: dojoatsomernova@gmail.com
Email to: jhenny.saintsurin@outlook.com
API key set: False
Config OK
```
(API key is False because `ANTHROPIC_API_KEY` is not set in this shell — expected.)

Also spot-checked the `Article` dataclass instantiates correctly with required fields and default values for optional fields.

## Environment note

`feedparser` and `pyyaml` were not preinstalled; installed via `python -m pip install feedparser pyyaml` (and `requests`, used only for diagnostics, not added to `requirements.txt` since it's already covered by `httpx`/`feedparser` for the actual modules).

## Commit

`f81db05` — "feat: Article dataclass, config loader, seeded YAML sources"
(4 files changed: `src/pulse/__init__.py`, `src/pulse/config.py`, `sources.yml`, `leaders.yml`)
