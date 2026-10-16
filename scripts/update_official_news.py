#!/usr/bin/env python3
"""Collect official Blizzard WoW: Forever news links; never mirror article bodies."""
import json
import re
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse

ROOT = "https://worldofwarcraft.blizzard.com"
SOURCE = ROOT + "/en-us/news"
DEST = Path(__file__).resolve().parents[1] / "data" / "official-news.json"
NEWS_URL = re.compile(r"^/(?:en-us|ko-kr|en-gb)/news/(\d+)(?:/[^?#]*)?$", re.I)
TOPIC = re.compile(r"\bforever\b|포에버", re.I)
PATCH = re.compile(r"patch notes?|hotfix(?:es)?|패치\s*노트|긴급\s*수정", re.I)
NOTICE = re.compile(r"beta|stress test|maintenance|launch|공지|점검|베타", re.I)

class NewsLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.href = None
        self.text = []
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.href = dict(attrs).get("href", "")
            self.text = []

    def handle_data(self, data):
        if self.href is not None:
            self.text.append(data)

    def handle_endtag(self, tag):
        if tag == "a" and self.href is not None:
            self.links.append((self.href, " ".join(" ".join(self.text).split())))
            self.href = None
            self.text = []

def category(title):
    if PATCH.search(title):
        return "패치노트"
    if NOTICE.search(title):
        return "공지"
    return "소식"

def main():
    previous = json.loads(DEST.read_text(encoding="utf-8"))
    existing = previous.get("items", [])
    req = urllib.request.Request(SOURCE, headers={"User-Agent": "ForeverAzerothFanArchive/1.0 (official news link index)", "Accept-Language": "en-US,en;q=0.8"})
    try:
        with urllib.request.urlopen(req, timeout=25) as response:
            html = response.read(3_000_000).decode("utf-8", "replace")
        parser = NewsLinks()
        parser.feed(html)
        found = []
        seen = set()
        for href, title in parser.links:
            url = urljoin(SOURCE, href)
            parts = urlparse(url)
            if parts.hostname != "worldofwarcraft.blizzard.com":
                continue
            match = NEWS_URL.match(parts.path)
            if not match or not TOPIC.search(title) or len(title) < 12 or len(title) > 220:
                continue
            ident = match.group(1)
            if ident in seen:
                continue
            seen.add(ident)
            found.append({"title": title, "url": ROOT + parts.path, "date": "", "category": category(title)})
        if not found:
            print("No matching official links parsed; preserving previous feed.")
            return
        # Retain existing dates and preferred labels; add new official links at the top.
        old_by_id = {}
        for item in existing:
            m = NEWS_URL.match(urlparse(item.get("url", "")).path)
            if m:
                old_by_id[m.group(1)] = item
        merged = []
        ids = set()
        for item in found + existing:
            m = NEWS_URL.match(urlparse(item.get("url", "")).path)
            if not m or m.group(1) in ids:
                continue
            ids.add(m.group(1))
            prior = old_by_id.get(m.group(1))
            if prior:
                item = prior
            merged.append(item)
        result = {"source": SOURCE, "updated_at": datetime.now(timezone.utc).isoformat(), "items": merged[:80]}
        # Avoid committing every run when no links have changed.
        if result["items"] == existing:
            print("No new links.")
            return
        DEST.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Indexed {len(result['items'])} official links, {len(found)} seen on source.")
    except Exception as exc:
        print(f"Source unavailable ({type(exc).__name__}: {exc}); previous feed preserved.")

if __name__ == "__main__":
    main()
