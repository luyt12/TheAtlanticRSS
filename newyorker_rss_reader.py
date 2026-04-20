"""
New Yorker RSS fetcher
Fetches articles from feedx.net RSS, with dedup against sent_articles.json.
Logic:
  1. Try today's articles (NY timezone)
  2. Fall back to yesterday's if today=0
  3. Deduplicate against sent_articles.json
  4. Return at most MAX_DAILY articles (newest first)
  5. backfill mode: fetch from N days ago; latest mode: fetch latest N articles regardless of date
"""
import os
import re
import requests
import feedparser
import pytz
import json as _json
from datetime import datetime, timedelta

RSS_URL = "https://feedx.net/rss/newyorker.xml"
ARTICLES_DIR = "articles"
SENT_FILE = "sent_articles.json"
MAX_DAILY = 5          # articles per email
TZ = pytz.timezone("America/New_York")


def setup():
    if not os.path.exists(ARTICLES_DIR):
        os.makedirs(ARTICLES_DIR)


def load_sent():
    if os.path.exists(SENT_FILE):
        try:
            with open(SENT_FILE, "r", encoding="utf-8") as f:
                return set(_json.load(f).get("sent", []))
        except Exception:
            pass
    return set()


def fetch():
    print("Fetching RSS: " + RSS_URL)
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0)"}
    resp = requests.get(RSS_URL, headers=headers, timeout=15)
    resp.raise_for_status()
    return resp.text


def fetch_full_content(url):
    """Strip HTML tags from a full article page."""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code != 200:
            return None
        text = resp.text
        text = re.sub(r"<script[\s\S]*?</script>", "", text)
        text = re.sub(r"<style[\s\S]*?</style>", "", text)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text[:3000] if len(text) > 3000 else text
    except Exception:
        return None


def parse_rss(xml):
    """Parse RSS and return list of entry dicts with pub_dt."""
    feed = feedparser.parse(xml)
    now = datetime.now(TZ)

    entries = []
    for e in feed.entries:
        title = e.get("title", "No title")
        link = e.get("link", "#").strip()
        pub = e.get("published_parsed") or e.get("updated_parsed")
        pub_str = "unknown"
        pub_dt = None
        if pub:
            try:
                dt = datetime(*pub[:6], tzinfo=TZ)
                pub_str = dt.strftime("%Y-%m-%d")
                pub_dt = dt
            except Exception:
                pass

        summary = ""
        if hasattr(e, "summary"):
            summary = re.sub(r"<[^>]+>", "", e.summary)
        elif hasattr(e, "description"):
            summary = re.sub(r"<[^>]+>", "", e.description)

        entries.append({
            "title": title.strip(),
            "link": link,
            "published": pub_str,
            "summary": summary.strip(),
            "pub_dt": pub_dt,
        })
    return entries


def filter_by_date(entries, days_back):
    """Filter entries to those published on target date (0=today, 1=yesterday, ...)."""
    now = datetime.now(TZ)
    if days_back > 0:
        target = (now - timedelta(days=days_back)).strftime("%Y-%m-%d")
    else:
        target = now.strftime("%Y-%m-%d")

    matched = [e for e in entries if e["published"] == target]
    label = "today" if days_back == 0 else f"{days_back} day(s) back"
    print(f"Total RSS entries: {len(entries)} | {label}: {len(matched)}")
    return matched


def format_single(article):
    lines = []
    lines.append("## " + article["title"])
    lines.append("")
    lines.append(f"📅 *Published: {article['published']}*")
    lines.append(f"[🔗 Read on New Yorker]({article['link']})")
    lines.append("")
    content = article.get("full_content") or article.get("summary", "")
    lines.append(content)
    return "\n".join(lines)


def main(days_back=0, latest=False):
    """
    Args:
      days_back: fetch articles from N days ago (0=today)
      latest: ignore date filter, take the latest MAX_DAILY from RSS
    Returns list of (filepath, url) tuples.
    """
    setup()

    sent_urls = load_sent()
    print("Already sent: " + str(len(sent_urls)) + " articles in sent_articles.json")

    xml = fetch()
    entries = parse_rss(xml)

    if latest:
        # Take latest MAX_DAILY, skip already-sent
        print(f"LATEST mode: taking latest {MAX_DAILY} articles from RSS")
        remaining = [e for e in entries if e["link"] not in sent_urls]
        top = remaining[:MAX_DAILY]
    else:
        matched = filter_by_date(entries, days_back)
        if not matched and days_back == 0:
            matched = filter_by_date(entries, days_back=1)
            if matched:
                print("No today articles — using yesterday's articles")
        if not matched:
            print("No articles found for target date.")
            return None

        candidates = [e for e in matched if e["link"] not in sent_urls]
        print("After dedup: " + str(len(candidates)) + " candidates")
        if not candidates:
            print("All target-date articles already sent. Nothing new.")
            return None

        candidates.sort(key=lambda x: x["pub_dt"] or "", reverse=True)
        top = candidates[:MAX_DAILY]

    print("Selected " + str(len(top)) + " articles")

    for article in top:
        full = fetch_full_content(article["link"])
        article["full_content"] = full or article["summary"]

    today_str = datetime.now(TZ).strftime("%Y%m%d")
    suffix = "_latest" if latest else (f"_d{days_back}" if days_back > 0 else "")
    saved = []
    for i, article in enumerate(top):
        filename = today_str + suffix + "_art" + str(i + 1) + ".md"
        filepath = os.path.join(ARTICLES_DIR, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(format_single(article))
        print("Saved: " + filepath)
        saved.append((filepath, article["link"]))

    print("Done: " + str(len(saved)) + " articles saved")
    return saved


if __name__ == "__main__":
    import sys
    days_back = 0
    latest = False
    if len(sys.argv) > 1:
        if sys.argv[1] == "latest":
            latest = True
        else:
            try:
                days_back = int(sys.argv[1])
            except ValueError:
                print("Usage: python newyorker_rss_reader.py [days_back|latest]")
                sys.exit(1)
    main(days_back=days_back, latest=latest)
