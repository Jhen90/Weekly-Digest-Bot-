# Pulse — Weekly Digest Bot: Design

**Date:** 2026-09-09
**Status:** Approved design, pre-implementation
**Source spec:** `weekly-digest-bot-SPEC.md` (Jhenny, 2026-09-08)

---

## 1. What Pulse is

A weekly news-digest agent. Once a week it reads a fixed list of trusted RSS
feeds, keeps only the recent articles that are genuinely on-topic, summarizes
each one conclusion-first with the Claude API, and emails the result to Jhenny
with direct links.

The pipeline, end to end:

> read trusted feeds → filter to the 4 topics → rank and cap → fetch article text
> → summarize conclusion-first → render email → send

It reads only the feeds it is told to read. It never crawls the open web.

**Recipient:** jhenny.saintsurin@outlook.com
**Sender:** a Gmail account (Outlook blocks bot sending), app password in a GitHub secret
**Schedule:** Mondays, 12:00 UTC

---

## 2. Topics

Four, fixed, five articles each at most:

1. **AI + Nonprofits** — AI tools for nonprofits, adoption, funding, case studies
2. **AI + Women** — women in AI, gender and AI, equity, notable women in the field
3. **Human-Centered Design** — HCD, UX, inclusive and women-centered design, design thinking
4. **AI News & Developments** — new tools, new skills, major releases

Plus a closing section, **"What the leaders are saying"** — the most recent piece
from each named person on the leaders list, one line each.

Fewer good articles beat five padded ones. A relevance floor enforces this: a
thin week produces a short digest, not filler.

---

## 3. Architecture

Approach chosen: small modules with a thin entrypoint, mirroring the Grant Nova
pattern already working in this user's other projects. Rejected alternatives are
recorded in §10.

```
Pulse/
├─ .github/workflows/weekly-digest.yml   weekly cron + manual dispatch
├─ sources.yml                            user-editable: feeds, grouped by topic
├─ leaders.yml                            user-editable: named people + feeds
├─ src/pulse/
│   ├─ config.py      loads and validates the YAML files and env vars
│   ├─ feeds.py       feedparser → list[Article]        (only feed network I/O)
│   ├─ topics.py      score, assign, dedupe, cap        (pure)
│   ├─ extract.py     best-effort article text, falls back to the feed blurb
│   ├─ summarize.py   Claude backend + no-key fallback  (only Claude I/O)
│   ├─ render.py      articles → (html, text)           (pure)
│   └─ mailer.py      Gmail SMTP send                   (only SMTP I/O)
├─ scripts/send_weekly_digest.py          entrypoint, supports --dry-run
├─ tests/
│   ├─ fixtures/*.xml                     saved RSS, so tests need no network
│   └─ test_*.py
├─ requirements.txt  .env.example  README.md  .gitignore
```

Each module has one job and one seam. Network access is confined to three files
(`feeds`, `extract`, `summarize`) plus `mailer`. Everything else is pure
functions over plain data, which is what makes the ranking logic and the email
layout testable with no network, no API key, and no secrets configured.

### The Article object

One dataclass carries state through the pipeline:

| Field | Set by | Meaning |
|---|---|---|
| `title`, `url`, `source_name`, `published` | `feeds` | from the feed entry |
| `feed_summary` | `feeds` | the entry's own description, the fallback summary |
| `topic`, `score` | `topics` | assigned topic and relevance score |
| `full_text` | `extract` | article body when retrievable, else `None` |
| `summary` | `summarize` | the conclusion-first paragraph that ships |

### Ordering constraint

Filtering and capping happen **before** extraction and summarization. A run
reads several hundred entries but pays Claude only for the ~25 that ship. This
is what bounds the cost; changing the order would multiply it by ten.

---

## 4. Fetching

`feeds.py` uses `feedparser` over the URLs in `sources.yml`. Each feed entry
becomes an `Article`; the source name and home topic come from the config, not
from the feed's own metadata, so a feed with a sloppy title still labels
correctly.

Feeds fail. A feed that times out, 404s, or returns unparseable XML is skipped,
recorded, and reported in the email footer — one dead source must never fail the
run, and must never silently shrink the digest for months unnoticed.

Dates are normalized to timezone-aware UTC. Entries with no parseable date are
dropped rather than guessed at, since the 7-day window is meaningless without one.

---

## 5. Topic sorting and ranking

Pure functions in `topics.py`, in this order:

1. **Window.** Keep entries published within the last 7 days.
2. **Score.** Each feed declares a home topic in `sources.yml`, which gives its
   articles a base score for that topic. Each topic has a keyword list; keyword
   hits add points, weighted heavier in the headline than in the blurb.
3. **Assign.** Each article goes to its single highest-scoring topic, ties
   resolved to the feed's home topic. One article never appears in two sections.
4. **Floor.** Articles below a relevance threshold are dropped.
5. **Dedupe.** By normalized URL (query strings and tracking parameters
   stripped), then by near-identical headline, since the same story breaks in
   several outlets on the same morning.
6. **Cap.** Sort by score, then recency; keep the top 5 per topic.

Leaders bypass steps 2–6 entirely: they are already curated by being on the
list. Each leader contributes their most recent piece inside the window.

**Known limitation, accepted:** with a fixed 7-day window, a run that fires late
can occasionally re-show an article from the previous week's boundary. The
remedy if it ever becomes annoying is to adjust the window by a few hours. It
does not justify persistent state (§10).

---

## 6. Summarization

`summarize.py` exposes one function returning a conclusion-first paragraph,
with two backends:

- **Claude** (default) — `claude-opus-5`, adaptive thinking, `effort: low`.
  Summarizing a news article is not hard reasoning; low effort is the correct
  cost lever, and is preferred over disabling thinking, which has known failure
  modes on this model.
- **Fallback** — the article's own feed blurb, used when `ANTHROPIC_API_KEY` is
  absent or the API call fails.

The prompt asks for the takeaway first ("The upshot: …"), then the supporting
detail, in one short paragraph.

`extract.py` makes a best-effort fetch of the article page (short timeout,
`httpx` + `BeautifulSoup`) so Claude summarizes real text rather than a
one-sentence blurb. On any failure it returns `None` and the blurb is used.
Content is never silently truncated to fit.

**Cost.** ~25 articles per week, roughly 1,700 input and a few hundred output
tokens each, at $5/$25 per million tokens: under about $0.50 per week. Switching
`claude-haiku-4-5` in config cuts that by roughly 80% if desired. The Batch API
would halve the cost but adds polling for a saving of about fifteen cents a
week — deliberately not used.

**Error handling** follows a most-specific-first chain (`RateLimitError` →
`APIStatusError` → `APIConnectionError`), each falling back to the blurb rather
than failing the run.

---

## 7. Email and delivery

`render.py` produces HTML and plain text from the same data; the message carries
both, since HTML-only mail scores as spam. Styles are inline per element,
because most mail clients discard a `<style>` block.

Structure follows the source spec: four topic sections, each article a linked
headline with source name and date, the conclusion-first paragraph beneath;
then "What the leaders are saying" as one-line takes with links; then a footer
listing any feed that failed this run.

**A quiet week still sends an email**, stating plainly that the run succeeded and
found little. Silence must never be ambiguous between "nothing happened" and
"the bot broke."

`mailer.py` sends via Gmail SMTP on port 587 with STARTTLS, using
`email.message.EmailMessage`. Failure to send is the one hard error — it exits
non-zero so the GitHub Actions run goes red and is visible.

---

## 8. Configuration and secrets

`sources.yml` and `leaders.yml` are plain text, edited without touching code.
Both ship seeded — sources with verified feeds for the outlets named in the
source spec, leaders with a starter set Jhenny cuts down and adds to. Every
seeded feed URL is confirmed to return recent entries before it ships; any
outlet with no working feed is reported rather than left silently broken.

`config.py` validates on load and fails loudly on a malformed file, so a typo
surfaces at the start of the run instead of as a mysteriously empty section.

| Value | Where it lives | Sensitive |
|---|---|---|
| `GMAIL_APP_PASSWORD` | GitHub repo secret | yes |
| `ANTHROPIC_API_KEY` | GitHub repo secret | yes |
| `GMAIL_USER` | inline in the workflow | no |
| `EMAIL_TO` | inline in the workflow | no |

`.gitignore` covers `.env` from the first commit. No key is ever committed.

---

## 9. Testing and local development

`--dry-run` runs the full pipeline and writes the digest to an HTML file to open
in a browser, sending nothing. This is the development loop.

`pytest` runs against RSS fixtures saved in `tests/fixtures/`, so the entire
sorting, ranking, dedupe, and rendering layer is verified with no network, no
API key, and no secrets. SMTP and the Claude client are mocked; the suite never
sends mail and never spends money.

Coverage targets the logic that can silently be wrong: the 7-day window
boundary, topic assignment and tie-breaking, the relevance floor, URL and
headline dedupe, the per-topic cap, the empty-digest email, and the
feed-failure footer.

**Degradation rule:** a dead feed is skipped and reported; a failed article
fetch falls back to the blurb; a failed Claude call falls back to the blurb;
only a failure to send is fatal.

---

## 10. Rejected alternatives

**Single-file script.** Matches the existing `jobscout.py`, and is the fastest
to write. Rejected because no piece can be tested without running the whole
thing, including the parts that cost money and send mail.

**SQLite article history.** Would guarantee no repeat across weeks and give a
searchable archive. Rejected because GitHub Actions runners are ephemeral: the
database would have to be committed back to the repo on every run, making the
bot push to its own main branch weekly. That is substantial machinery bought to
solve a boundary case the 7-day window already mostly handles.

**Opinion detection over the main feeds** for the leaders section. Rejected
because "leader" would become whoever happened to publish, rather than the
people Jhenny chose to follow.

**Batch API** for summarization. Halves an already-small cost, adds polling.
Rejected on the trade.

---

## 11. Build order

1. Scaffold: repo layout, `requirements.txt`, `.gitignore`, `.env.example`, README
2. `config.py` + seeded `sources.yml` / `leaders.yml`, feeds verified live
3. `feeds.py` + RSS fixtures
4. `topics.py` — the ranking logic, tested hardest
5. `render.py` — email HTML and text
6. `scripts/send_weekly_digest.py --dry-run` → **first viewable digest**
7. `extract.py` + `summarize.py` — the Claude layer
8. `mailer.py` + a real test send
9. `.github/workflows/weekly-digest.yml` on `main`

Step 6 is the milestone: a real digest, real articles, real layout, viewable in
a browser before any credential exists.

---

## 12. Open inputs from Jhenny

Not blockers for steps 1–6:

- **The leaders list** — which people to track. Ships seeded with a starter set
  to edit.
- **Credentials, at step 8** — Gmail app password, Anthropic API key.
- **The GitHub repo** — created and pushed only with explicit approval.
