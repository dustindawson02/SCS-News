import json
import os
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

import requests

FEED_URL = (
    "https://blog.scssoft.com/feeds/posts/default"
    "?alt=json&max-results=10&orderby=published"
)
STATE_FILE = Path("last_scs_post.json")
WEBHOOK_URL = os.environ["DISCORD_WEBHOOK_URL"]


def clean_link(link):
    parts = urlsplit(link)
    return urlunsplit(("https", parts.netloc, parts.path, "", ""))


def post_to_discord(title, link):
    message = {
        "username": "SCS Newsletter",
        "content": f"📰 **{title}**\n\n{link}",
        "allowed_mentions": {"parse": []}
    }

    response = requests.post(WEBHOOK_URL, json=message, timeout=30)
    response.raise_for_status()


response = requests.get(
    FEED_URL,
    headers={
        "User-Agent": "SCS-Discord-News/1.0",
        "Accept": "application/json"
    },
    timeout=30
)
response.raise_for_status()

entries = response.json()["feed"].get("entry", [])
articles = []

for entry in entries:
    title = entry["title"]["$t"].strip()

    link = next(
        item["href"]
        for item in entry["link"]
        if item.get("rel") == "alternate"
    )

    articles.append({
        "title": title,
        "link": clean_link(link)
    })

if not articles:
    raise RuntimeError("No SCS articles were found.")

saved_link = None

if STATE_FILE.exists():
    saved_data = json.loads(STATE_FILE.read_text(encoding="utf-8"))

    if saved_data.get("last_link"):
        saved_link = clean_link(saved_data["last_link"])

if saved_link is None:
    new_articles = [articles[0]]
else:
    new_articles = []
    found_saved_article = False

    for article in articles:
        if article["link"] == saved_link:
            found_saved_article = True
            break

        new_articles.append(article)

    if not found_saved_article:
        new_articles = [articles[0]]

for article in reversed(new_articles):
    post_to_discord(article["title"], article["link"])

latest = articles[0]

STATE_FILE.write_text(
    json.dumps(
        {
            "last_link": latest["link"],
            "last_title": latest["title"]
        },
        indent=2
    ),
    encoding="utf-8"
)

print(f"Posted {len(new_articles)} new SCS article(s).")
