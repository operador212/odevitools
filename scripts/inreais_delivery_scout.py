#!/usr/bin/env python3
"""Collect public UK delivery-sector headlines into an editorial review queue.

This scout stores headlines and source links only. It does not download or reuse
third-party video. Every item requires fact-checking and editorial approval.
"""
from __future__ import annotations

import json
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

QUERIES = {
    "platform_updates": '("Uber Eats" OR Deliveroo OR "Just Eat") UK rider OR courier news',
    "rules_and_rights": 'UK delivery couriers riders employment rights legislation rules',
    "pay_and_fees": 'UK food delivery rider pay fees insurance account deactivation',
    "incidents_and_disputes": 'UK delivery rider controversy dispute protest accident platform',
    "brazil": "entregadores delivery aplicativos Brasil iFood greve confusao violencia direitos",
    "portugal": "estafetas entregadores brasileiros Portugal Uber Eats Glovo polemica regras",
    "ireland": "delivery riders couriers Ireland Dublin Brazilian migrant gig workers news",
    "uk": "UK delivery riders couriers Brazilian migrant Uber Eats Deliveroo Just Eat news",
    "industry": 'UK gig economy food delivery courier industry changes',
}
OUT = Path("data/inreais-delivery-news.json")
MAX_PER_QUERY = 20
USER_AGENT = "InreaisDeliveryNewsScout/1.0 (public RSS headlines; contact: repository owner)"


def clean(value: str) -> str:
    return re.sub(r"\\s+", " ", value or "").strip()


def fetch_feed(query: str) -> list[dict]:
    params = urllib.parse.urlencode({
        "q": query, "hl": "en-GB", "gl": "GB", "ceid": "GB:en"
    })
    url = "https://news.google.com/rss/search?" + params
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=25) as response:
        payload = response.read()
    root = ET.fromstring(payload)
    items = []
    for item in root.findall("./channel/item")[:MAX_PER_QUERY]:
        source = item.find("source")
        items.append({
            "title": clean(item.findtext("title")),
            "url": clean(item.findtext("link")),
            "published_at": clean(item.findtext("pubDate")),
            "source": clean(source.text if source is not None else ""),
        })
    return items


def main() -> None:
    now = datetime.now(timezone.utc).isoformat()
    previous = {}
    if OUT.exists():
        try:
            previous = json.loads(OUT.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            previous = {}

    existing = {
        item.get("url"): item
        for item in previous.get("items", [])
        if item.get("url")
    }
    errors = []
    for category, query in QUERIES.items():
        try:
            for item in fetch_feed(query):
                if not item["url"] or not item["title"]:
                    continue
                item.update({
                    "category": category,
                    "discovered_at": now,
                    "status": "needs_review",
                    "editorial_note": "",
                    "video_permission": "not_checked",
                })
                existing[item["url"]] = item
            time.sleep(1)
        except Exception as exc:  # keep other categories running if one feed fails
            errors.append({"category": category, "error": str(exc)[:300]})

    items = sorted(
        existing.values(),
        key=lambda x: x.get("published_at", ""),
        reverse=True
    )[:150]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps({
            "project": "INREAIS DELIVERY",
            "updated_at": now,
            "source_policy": "Headlines and links for editorial review; no video reuse permission is implied.",
            "items": items,
            "feed_errors": errors,
        }, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Saved {len(items)} unique headlines; feed errors: {len(errors)}")


if __name__ == "__main__":
    main()
