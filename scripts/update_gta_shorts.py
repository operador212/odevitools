#!/usr/bin/env python3
"""Refresh the ODEVI+ YouTube gallery from public YouTube Atom feeds.

No YouTube API key or RSS-to-JSON proxy is used. The workflow fetches feeds
server-side every two hours and writes only official YouTube embed URLs.
"""
from __future__ import annotations
import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

CONFIG = Path("config/youtube-channels.json")
OUTPUT = Path("data/gta-shorts.json")
ATOM = "{http://www.w3.org/2005/Atom}"
YT = "{http://www.youtube.com/xml/schemas/2015}"


def fetch_feed(channel_id: str) -> bytes:
    url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    req = urllib.request.Request(url, headers={"User-Agent": "ODEVI-YouTube-RSS/1.0"})
    with urllib.request.urlopen(req, timeout=25) as response:
        return response.read(2_000_000)


def main() -> int:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    old = json.loads(OUTPUT.read_text(encoding="utf-8")) if OUTPUT.exists() else {"items": []}
    videos = {}
    for channel in config.get("channels", []):
        if not channel.get("enabled", True):
            continue
        channel_id = str(channel.get("channelId", ""))
        if not re.fullmatch(r"UC[a-zA-Z0-9_-]{22}", channel_id):
            print(f"Skipping invalid YouTube channel ID for {channel.get('name', 'unknown')}")
            continue
        try:
            root = ET.fromstring(fetch_feed(channel_id))
        except Exception as exc:
            print(f"Feed failed for {channel.get('name', channel_id)}: {exc}")
            continue
        keywords = [str(k).casefold() for k in channel.get("keywords", [])]
        for entry in root.findall(f"{ATOM}entry"):
            video_id = (entry.findtext(f"{YT}videoId") or "").strip()
            title = (entry.findtext(f"{ATOM}title") or "").strip()
            published = (entry.findtext(f"{ATOM}published") or "").strip()
            if not re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id) or not title:
                continue
            if keywords and not any(k in title.casefold() for k in keywords):
                continue
            url = f"https://www.youtube.com/watch?v={video_id}"
            videos[video_id] = {
                "id": video_id,
                "status": "published",
                "title": title,
                "creator": channel.get("name", "YouTube"),
                "url": url,
                "embedUrl": f"https://www.youtube-nocookie.com/embed/{video_id}",
                "pubDate": published,
                "source": "YouTube RSS público",
            }
    merged = {item.get("id"): item for item in old.get("items", []) if item.get("id")}
    merged.update(videos)
    items = sorted(merged.values(), key=lambda x: x.get("pubDate", ""), reverse=True)[:24]
    payload = {
        "updatedAt": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source": "YouTube public Atom/RSS feeds",
        "items": items,
    }
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Updated YouTube gallery: {len(items)} video(s) from {len(config.get('channels', []))} configured channel(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
