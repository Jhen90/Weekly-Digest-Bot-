# Task 3 Report: Feeds module and fixtures

**Commit:** b5439f8

## Files created

- `src/pulse/feeds.py` — `fetch_feeds(config: Config) -> list[Article]`, fetching entries from all feeds in `config.sources["topics"]`, filtering to a 7-day publish window, and recording `config._failed_feeds` for feeds that raise or return zero entries.
- `tests/fixtures/ai_nonprofits.xml`, `tests/fixtures/ai_news.xml`, `tests/fixtures/ai_women.xml`, `tests/fixtures/hcd.xml` — minimal valid RSS 2.0 fixtures, 2 entries each, all publish dates within the 7-day window relative to today (2026-09-09). Verified all 4 parse cleanly via `feedparser.parse()` with `bozo=False` and 2 entries apiece.
- `tests/test_feeds.py` — 3 unit tests using mocked `feedparser.parse`, per the plan.

## Deviations from the plan's literal code (required for correctness)

The plan's `feeds.py` snippet (line 392) does `from .import Article, Config`, but `Config` is defined in `src/pulse/config.py` and is never re-exported from `src/pulse/__init__.py` (confirmed against the actual Task 2 output — `__init__.py` only defines `Article`). Importing `Config` this way raises `ImportError: cannot import name 'Config' from 'src.pulse'`. Fixed by importing directly from the submodule instead of touching the Task 2 files:
```python
from . import Article
from .config import Config
```

Separately, the plan's `feeds.py` reads entry fields with `entry.get("title", ...)` (dict-style), but the plan's own `test_feeds.py` mocks entries as `MagicMock(title=..., link=..., summary=..., published_parsed=...)` — plain attribute assignment. `MagicMock.get(...)` is not automatically wired to constructor kwargs, so calling it returns an unrelated `MagicMock`, and all three tests failed with `AssertionError: assert <MagicMock> == 'Recent article'` (etc.). Real feedparser `FeedParserDict` entries support both attribute and dict-style access, so switched the three field reads (title, link, summary) and the warning-log fallback to `getattr(entry, field, default)`, which works identically against real feeds and against the plan's mocks. `test_feeds.py` and the fixtures were kept exactly as specified in the plan — no test code was changed.

Both fixes are scoped entirely to `feeds.py`; no other file (including Task 1/2 deliverables) was modified.

## VentureBeat User-Agent fix

Included per the Task 2 report's note. `feedparser.USER_AGENT` is set to a browser-like string near the top of `fetch_feeds()`, right after `now = datetime.now(timezone.utc)`:
```python
feedparser.USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
```
Without this, VentureBeat's feed (in `sources.yml`) returns HTTP 429 and zero entries.

## Test output

```
$ python -m pytest tests/test_feeds.py -v
============================= test session starts =============================
platform win32 -- Python 3.14.7, pytest-9.1.1, pluggy-1.6.0 -- ...python.exe
rootdir: C:\Users\jhenn\OneDrive\Desktop\Pulse
plugins: mock-3.15.1
collecting ... collected 3 items

tests/test_feeds.py::test_fetch_feeds_parses_entries PASSED              [ 33%]
tests/test_feeds.py::test_fetch_feeds_filters_7_day_window PASSED        [ 66%]
tests/test_feeds.py::test_fetch_feeds_handles_missing_pubdate PASSED     [100%]

============================== 3 passed in 0.11s ==============================
```

Full suite (`python -m pytest -v`) also shows the same 3 tests, all passing.

## Environment note

`pytest`, `pytest-mock`, `feedparser`, and `pyyaml` were not preinstalled in this environment (consistent with Task 2's note); installed via `python -m pip install pytest pytest-mock feedparser pyyaml` to run the suite. All four are already declared in `requirements.txt`.

## Commit

`b5439f8` — "feat: feeds module with 7-day window filter; fixture-based tests"
(6 files changed: `src/pulse/feeds.py`, 4 fixture XML files, `tests/test_feeds.py`)

## Fix Round 1

**Issue:** feedparser.parse(..., timeout=10) fails on feedparser 6.0.14 (timeout parameter unsupported).

**Fix:** Removed `timeout=10` from feedparser.parse() call (line 21).

**Test:** pytest tests/test_feeds.py still passes. `scripts.send_weekly_digest --dry-run` now fetches articles.

Detail: `python -m pytest tests/test_feeds.py -v` — 3/3 passed, unchanged. `python -m scripts.send_weekly_digest --dry-run` now fetches 97 articles across all 10 feeds (previously all 10 failed with `TypeError: parse() got an unexpected keyword argument 'timeout'`) and ranks 17 across topics. The dry-run then fails later at HTML-file-write time with an unrelated bug: `UnicodeEncodeError: 'charmap' codec can't encode character '→'` in `scripts/send_weekly_digest.py` line 57 (Windows default `cp1252` file encoding choking on an arrow character in the rendered digest HTML). That failure is in the digest-sending script, not in `feeds.py`, and is outside Task 3's scope — flagged for whichever task owns `scripts/send_weekly_digest.py`.

**Commit:** c07d3a1 — "fix: remove unsupported feedparser timeout kwarg (feedparser 6.0.14)"
