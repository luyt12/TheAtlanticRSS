"""
New Yorker RSS Reader
抓取 feedx.net RSS 源，保存当日文章
"""
import os
import feedparser
import pytz
from datetime import datetime

RSS_URL = "https://feedx.net/rss/newyorker.xml"
ARTICLES_DIR = "articles"

TZ = pytz.timezone("America/New_York")


def fetch_rss():
    print("Fetching RSS: " + RSS_URL)
    feed = feedparser.parse(RSS_URL)
    print("Total: " + str(len(feed.entries)))
    return feed


def is_today(entry):
    try:
        pub = entry.get("published_parsed") or entry.get("updated_parsed")
        if not pub:
            return False
        published = datetime(*pub[:6], tzinfo=pytz.UTC)
        today = datetime.now(TZ).replace(hour=0, minute=0, second=0, microsecond=0)
        return published.date() == today.date()
    except Exception:
        return False


def extract_content(entry):
    title = entry.get("title", "")
    link = entry.get("link", "")
    summary = entry.get("summary", "")
    content = entry.get("content", [{}])[0].get("value", summary)
    return title, link, content


def save_articles(feed):
    os.makedirs(ARTICLES_DIR, exist_ok=True)
    today = datetime.now(TZ).strftime("%Y%m%d")
    today_file = os.path.join(ARTICLES_DIR, today + ".md")

    today_articles = []
    all_articles = []

    for entry in feed.entries:
        title, link, content = extract_content(entry)
        article_md = "## " + title + "\n\n"
        article_md += "链接：" + link + "\n\n"
        article_md += content + "\n\n---\n\n"
        all_articles.append(article_md)
        if is_today(entry):
            today_articles.append(article_md)

    # 保存全部
    all_file = os.path.join(ARTICLES_DIR, "all_" + today + ".md")
    with open(all_file, "w", encoding="utf-8") as f:
        f.write("# New Yorker Articles - " + today + "\n\n")
        f.write("".join(all_articles))
    print("Saved all: " + all_file)

    # 保存今日
    if today_articles:
        with open(today_file, "w", encoding="utf-8") as f:
            f.write("# New Yorker Articles - " + today + "\n\n")
            f.write("".join(today_articles))
        print("Saved today: " + today_file + " (" + str(len(today_articles)) + " articles)")
    else:
        print("No articles for today")

    return len(today_articles)


def main():
    feed = fetch_rss()
    count = save_articles(feed)
    print("Today: " + str(count))
    return count


if __name__ == "__main__":
    main()
