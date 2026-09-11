# Task 6 Report: Entrypoint script and first dry-run

## File created

- `scripts/send_weekly_digest.py` — CLI entrypoint (`argparse` with `--dry-run`), orchestrates `Config()` → `fetch_feeds()` → `filter_and_rank()` → `render_digest()`, writes `digest.html` to disk on `--dry-run`, logs each stage, and wraps the whole run in try/except that logs and exits 1 on failure. Content copied verbatim from the plan (docs/superpowers/plans/2026-09-09-pulse-implementation.md:754-809), no deviations.

## Test output

```
cd /c/Users/jhenn/OneDrive/Desktop/Pulse && python -m scripts.send_weekly_digest --dry-run

2026-09-09 21:19:59,783 [INFO] Loading configuration...
2026-09-09 21:19:59,787 [INFO] Fetching feeds...
2026-09-09 21:19:59,788 [ERROR] Failed to fetch Stanford Social Innovation Review: parse() got an unexpected keyword argument 'timeout'
2026-09-09 21:19:59,788 [ERROR] Failed to fetch Nonprofit Quarterly: parse() got an unexpected keyword argument 'timeout'
2026-09-09 21:19:59,788 [ERROR] Failed to fetch Chronicle of Philanthropy: parse() got an unexpected keyword argument 'timeout'
2026-09-09 21:19:59,788 [ERROR] Failed to fetch The 19th: parse() got an unexpected keyword argument 'timeout'
2026-09-09 21:19:59,788 [ERROR] Failed to fetch Wired: parse() got an unexpected keyword argument 'timeout'
2026-09-09 21:19:59,788 [ERROR] Failed to fetch Nielsen Norman Group: parse() got an unexpected keyword argument 'timeout'
2026-09-09 21:19:59,788 [ERROR] Failed to fetch A List Apart: parse() got an unexpected keyword argument 'timeout'
2026-09-09 21:19:59,788 [ERROR] Failed to fetch MIT Technology Review: parse() got an unexpected keyword argument 'timeout'
2026-09-09 21:19:59,788 [ERROR] Failed to fetch The Verge: parse() got an unexpected keyword argument 'timeout'
2026-09-09 21:19:59,788 [ERROR] Failed to fetch VentureBeat: parse() got an unexpected keyword argument 'timeout'
2026-09-09 21:19:59,788 [INFO] Fetched 0 articles from all feeds
2026-09-09 21:19:59,788 [INFO] Filtering and ranking by topic...
2026-09-09 21:19:59,788 [INFO] Ranked 0 articles across topics
2026-09-09 21:19:59,788 [INFO] Rendering digest...
2026-09-09 21:19:59,790 [INFO] \u2713 Digest written to C:\Users\jhenn\OneDrive\Desktop\Pulse\digest.html

Open file://C:\Users\jhenn\OneDrive\Desktop\Pulse\digest.html in your browser
```

All expected log stages appeared in order (Loading configuration → Fetching feeds → Filtering and ranking → Rendering digest), the file was written, and the "Open file://..." message printed as specified.

## Verification results

- `digest.html` was created at the project root (confirmed via `ls -la`, 1872 bytes).
- HTML is well-formed, inline-styled (`<body style="font-family: Arial...">`), and includes the date header (`2026-09-09 | Your weekly news on AI, design, and impact`).
- The digest correctly hit the render module's empty-state path (`<strong>No new articles this week.</strong>...`) and the failed-feeds footer, both of which are legitimate, tested code paths in `render.py`.
- **Could not verify** "article titles, sources, dates, summaries grouped by topic" rendering with real data, because 0 articles were fetched — see concern below.

## Concerns

**Pre-existing bug in `src/pulse/feeds.py` (Task 3, already committed) blocked full end-to-end verification.** Line 21 calls:
```python
feed = feedparser.parse(feed_config["url"], timeout=10)
```
The installed `feedparser` (6.0.14) does not accept a `timeout` kwarg at all (confirmed via `inspect.signature(feedparser.parse)` — no `timeout` parameter exists in this version). Every one of the 10 configured feeds failed with `parse() got an unexpected keyword argument 'timeout'`, so `fetch_feeds()` returned 0 articles and the digest fell back to the "no articles this week" empty state plus a 10-item failed-feeds footer, rather than showing real article titles/sources/dates/summaries.

This is **not a bug in the file I was asked to create** — `scripts/send_weekly_digest.py` behaved exactly as designed: it orchestrated the pipeline, surfaced the per-feed failures via logging and the rendered footer, and still produced valid, openable HTML (a correctly-exercised degenerate-code-path, not a crash). I left `feeds.py` unmodified since it's outside Task 6's scope (the task's commit instructions are specifically `git add scripts/send_weekly_digest.py`), but flagging it here since it will block any future dry-run from showing real content until fixed (likely just removing the unsupported `timeout=10` kwarg, or achieving the timeout a different way, e.g. `socket.setdefaulttimeout()`).

## Commit

`f408ebd` — "feat: entrypoint with --dry-run mode"

1 file changed, 68 insertions(+):
- scripts/send_weekly_digest.py (new)
