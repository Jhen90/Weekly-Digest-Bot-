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
