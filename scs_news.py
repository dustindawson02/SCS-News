import json
import os
from pathlib import Path

import feedparser
import requests

FEED_URL = "https://blog.scssoft.com/feeds/posts/default?alt=rss"
STATE_FILE = Path("last_scs_post.json")
WEBHOOK_URL = os.environ["DISCORD_WEBHOOK_URL"]


def post_to_discord(title, link):
    message = {
        "username": "SCS Newsletter",
        "content": f"📰 **{title}**\n\n{link}",
        "allowed_mentions": {"parse": []}
    }

    response = requests.post(WEBHOOK_URL, json=message, timeout=30)
    response.raise_for_status()


feed = feedparser.parse(FEED_URL)

if not feed.entries:
    raise RuntimeError("No SCS articles were found.")

saved_link = None

if STATE_FILE.exists():
    saved_data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    saved_link = saved_data.get("last_link")

if saved_link is None:
    # On the first run, only post the newest article.
    newest = feed.entries[0]
    post_to_discord(newest.title, newest.link)
    posted_count = 1
else:
    new_articles = []

    for article in feed.entries:
        if article.link == saved_link:
            break

        new_articles.append(article)

    # Post oldest first if several articles are new.
    for article in reversed(new_articles):
        post_to_discord(article.title, article.link)

    posted_count = len(new_articles)

latest = feed.entries[0]

STATE_FILE.write_text(
    json.dumps(
        {
            "last_link": latest.link,
            "last_title": latest.title
        },
        indent=2
    ),
    encoding="utf-8"
)

print(f"Posted {posted_count} new SCS article(s).")
