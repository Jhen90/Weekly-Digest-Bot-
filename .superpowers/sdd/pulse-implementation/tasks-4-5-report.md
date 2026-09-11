# Tasks 4 & 5 Report: Topics module + Render module

## Files created

- `src/pulse/topics.py` — `filter_and_rank(articles, config)`, plus helpers `normalize_url`, `similarity`, `score_article`. Content copied verbatim from the plan (topic scoring, home-topic bonus, keyword scoring, URL/headline dedup, relevance floor of 1.0, 5-article cap, sort by score desc then date desc).
- `tests/test_topics.py` — 5 tests: topic assignment, 5-article cap, URL normalization for dedup, headline similarity, dedup by URL.
- `src/pulse/render.py` — `render_digest(articles_by_topic, failed_feeds=None)` returning `(html, text)`, plus `_render_html` and `_render_plaintext` helpers. Content copied verbatim from the plan (empty-digest message, per-topic sections, "What the Leaders Are Saying" placeholder section, failed-feeds footer).
- `tests/test_render.py` — 4 tests: HTML+text returned, article title present in both, empty-digest message, failed-feeds footer present.

## Deviation from plan (noted, not a functional change)

The plan's source snippet used `from .import Article, Config` in `topics.py` and `from .import Article` in `render.py` — both a formatting typo (missing space) and, for `topics.py`, `Config` is not actually re-exported from `src/pulse/__init__.py` (it lives in `src/pulse/config.py`, confirmed by how `test_feeds.py` imports it: `from src.pulse.config import Config`). Corrected the imports to:
- `topics.py`: `from . import Article` and `from .config import Config`
- `render.py`: `from . import Article`

All other code is copied exactly as written in the plan.

## Test output

```
cd /c/Users/jhenn/OneDrive/Desktop/Pulse && python -m pytest tests/test_topics.py tests/test_render.py -v

============================= test session starts =============================
platform win32 -- Python 3.14.7, pytest-9.1.1, pluggy-1.6.0
collected 9 items

tests/test_topics.py::test_filter_and_rank_assigns_topics PASSED         [ 11%]
tests/test_topics.py::test_filter_and_rank_respects_5_article_cap PASSED [ 22%]
tests/test_topics.py::test_normalize_url_removes_query_strings PASSED    [ 33%]
tests/test_topics.py::test_similarity_detects_identical_headlines PASSED [ 44%]
tests/test_topics.py::test_filter_deduplicates_by_url PASSED             [ 55%]
tests/test_render.py::test_render_digest_returns_html_and_text PASSED    [ 66%]
tests/test_render.py::test_render_digest_includes_article_title PASSED   [ 77%]
tests/test_render.py::test_render_digest_empty_shows_no_articles_message PASSED [ 88%]
tests/test_render.py::test_render_digest_with_failed_feeds PASSED        [100%]

============================== 9 passed in 0.07s ==============================
```

Note: the task brief anticipated 10 tests (6 topics + 4 render), but the plan's actual `test_topics.py` section (as written in `docs/superpowers/plans/2026-09-09-pulse-implementation.md`) contains 5 test functions, not 6 — there is no separate standalone "relevance floor" test in the plan's source; the floor behavior is exercised implicitly within the other tests. Copied the plan's test file exactly as written, yielding 9 total tests, all passing.

## Concerns

None functional. The only note is the import-path fix described above (required for the code to run at all, since the plan's snippet had a typo/omission); this does not change any behavior described in the interfaces.

## Commit

`d013bf2` — "feat: topic scoring/ranking and email rendering (pure functions)"

4 files changed, 421 insertions(+):
- src/pulse/render.py (new)
- src/pulse/topics.py (new)
- tests/test_render.py (new)
- tests/test_topics.py (new)
