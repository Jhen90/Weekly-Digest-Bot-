from typing import Dict, List, Tuple
from datetime import datetime
from . import Article

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
