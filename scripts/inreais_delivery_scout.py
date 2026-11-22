#!/usr/bin/env python3
"""Collect public food-delivery courier headlines across four regions into a review queue.

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
    "uber_eats": '"Uber Eats" (rider OR courier OR delivery driver OR entregador) food delivery news',
    "deliveroo": 'Deliveroo (rider OR courier OR delivery driver OR entregador) food delivery news',
    "just_eat": '"Just Eat" (courier OR rider OR delivery driver) food delivery news',
    "glovo": 'Glovo (courier OR rider OR repartidor OR estafeta OR entregador) food delivery news',
    "brazil": '(motoboy OR entregador OR delivery) (iFood OR Rappi) (greve OR viral OR acidente OR polemica OR direitos OR pagamento)',
    "portugal": '(estafeta OR entregador OR courier) (Glovo OR Uber Eats) (greve OR viral OR acidente OR polemica OR pagamento)',
    "ireland": '("food delivery" OR takeaway courier) (rider OR cyclist OR motorbike) Ireland Dublin',
    "uk": '("food delivery" OR takeaway courier) (rider OR cyclist OR motorbike) UK London',
    "viral_food_delivery": '("food delivery rider" OR "Uber Eats rider" OR "Deliveroo rider" OR motoboy OR estafeta) (viral OR trending OR bizarre OR unusual OR funny OR shocking)',
    "controversies_food_delivery": '("food delivery" OR "Uber Eats" OR Deliveroo OR Glovo OR "Just Eat") (controversy OR dispute OR scandal OR protest OR allegation OR strike) courier rider',
    "curious_food_delivery": '("food delivery rider" OR motoboy OR estafeta OR courier) (strange order OR unusual delivery OR rescued OR surprising story)',
    "creator_food_delivery": 'food delivery courier rider creator viral TikTok YouTube Shorts Instagram',
}
OUT = Path("data/inreais-delivery-news.json")
MAX_PER_QUERY = 20
USER_AGENT = "InreaisDeliveryNewsScout/1.0 (public RSS headlines; contact: repository owner)"


def clean(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


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
