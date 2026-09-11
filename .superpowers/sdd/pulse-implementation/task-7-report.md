# Task 7 Report: Extract and summarize modules (with Claude fallback)

## Note on task instructions

The task description pointed to `docs/superpowers/plans/2026-09-09-pulse-implementation.md:813-927`, but that range is actually Task 5 (render module). The real Task 7 content ("## Task 7: Extract and summarize modules (with Claude fallback)") lives at lines 1155-1386 of the same plan file. Sourced all four files from there.

## Files created

- `src/pulse/extract.py` — `extract_article_text(article) -> Optional[str]`. Fetches the article URL via `httpx.get` (5s timeout), strips `script`/`style` tags, tries content selectors (`article`, `main`, `.content`, `.post`, `.entry-content`) before falling back to `soup.body`, trims to 5000 chars, and returns `None` if the result is falsy or ≤100 characters (or on any exception). Copied verbatim from plan lines 1166-1216.
- `src/pulse/summarize.py` — `summarize_article(article, api_key=None) -> str`. Returns `article.feed_summary` immediately if no API key. Otherwise calls `Anthropic().messages.create(model="claude-opus-5", thinking={"type": "adaptive"}, output_config={"effort": "low"}, ...)` with a conclusion-first system prompt, and falls back to `feed_summary` on `RateLimitError`, `APIStatusError`, `APIConnectionError`, or any other exception. Copied verbatim from plan lines 1220-1278. (Verified against the bundled `claude-api` skill: `claude-opus-5` + adaptive thinking + `output_config.effort` is the current, correct API shape — no changes needed.)
- `tests/test_extract.py` — 3 tests: request-error → None, valid `<article>` HTML → extracted text, very-short content → None. Sourced from plan lines 1282-1323, with one fix (see Concerns).
- `tests/test_summarize.py` — 3 tests: no API key → feed summary, API exception → feed summary, mocked Claude response → returned text contains "The upshot". Copied verbatim from plan lines 1327-1371.

## Test output

```
python -m pytest tests/test_extract.py tests/test_summarize.py -v

tests/test_extract.py::test_extract_returns_none_on_request_error PASSED
tests/test_extract.py::test_extract_returns_text_content PASSED
tests/test_extract.py::test_extract_returns_none_for_very_short_content PASSED
tests/test_summarize.py::test_summarize_returns_feed_summary_without_api_key PASSED
tests/test_summarize.py::test_summarize_returns_feed_summary_on_api_error PASSED
tests/test_summarize.py::test_summarize_returns_claude_response PASSED

6 passed in 1.81s
```

Full suite (`python -m pytest tests/ -v`) also run afterward: **18 passed**, no regressions in `test_feeds.py`, `test_render.py`, or `test_topics.py`.

## Environment setup

`httpx`, `beautifulsoup4`, and `anthropic` were not installed in the active Python environment (only `feedparser`, `pytest`, `pytest-mock`, `PyYAML` were present, despite `requirements.txt` listing all of them). Ran `pip install httpx beautifulsoup4 anthropic`, which pulled in `anthropic==1.4.0` (the current major version). The plan's `from anthropic import Anthropic, RateLimitError, APIStatusError, APIConnectionError` import works unchanged against this version.

## Concerns

**Fixed a bug in the plan's own test fixture (`test_extract_returns_text_content`).** The plan's mock HTML was `<article>This is the article content</article>` — only 28 characters of extracted text. `extract_article_text` requires extracted text to exceed 100 characters (a real content-length gate, not a copy-paste artifact — confirmed by the adjacent `test_extract_returns_none_for_very_short_content` test, which exists specifically to check that gate). With the plan's original fixture, the test failed against the plan's own implementation (`assert result is not None` → `None is not None`). I lengthened the mock article text past 100 characters while preserving the test's intent (checking that `<article>` content is extracted and the phrase "article content" survives). This is the only deviation from "exact code from plan" in any of the four files — `extract.py`, `summarize.py`, and `test_summarize.py` are unmodified verbatim copies.

## Commit

`5f82cdd` — "feat: article extraction with Claude summarization + fallback"

4 files changed, 193 insertions(+):
- src/pulse/extract.py (new)
- src/pulse/summarize.py (new)
- tests/test_extract.py (new)
- tests/test_summarize.py (new)
