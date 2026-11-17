#!/usr/bin/env python3
"""Collect Rockstar GTA VI Newswire items into an unpublished editorial queue.

Only official Rockstar-owned sources are accepted. New discoveries are drafts,
never automatically published. No third-party article text is copied.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

FEED_URL = (
    "https://news.google.com/rss/search?q="
    + urllib.parse.quote('site:rockstargames.com/newswire "Grand Theft Auto VI"')
    + "&hl=en-US&gl=US&ceid=US:en"
)
ALLOWED_HOSTS = {"rockstargames.com", "www.rockstargames.com",
                 "support.rockstargames.com", "www.rockstargames.com"}
FEED_PATH = Path("data/gta-news.json")


def host_is_official(url: str) -> bool:
    try:
        host = (urllib.parse.urlparse(url).hostname or "").lower()
        return host in ALLOWED_HOSTS
    except Exception:
        return False


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "ODEVI-GTA6-NewsScout/1.0"})
    with urllib.request.urlopen(req, timeout=25) as response:
        return response.read(3_000_000)


def resolve_official_url(url: str) -> str | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ODEVI-GTA6-NewsScout/1.0"})
        with urllib.request.urlopen(req, timeout=20) as response:
            final_url = response.geturl()
        return final_url if host_is_official(final_url) else None
    except Exception:
        return None


def text_of(parent: ET.Element, tag: str) -> str:
    el = parent.find(tag)
    return "".join(el.itertext()).strip() if el is not None else ""


def main() -> int:
    current = json.loads(FEED_PATH.read_text(encoding="utf-8"))
    known = {str(item.get("url", "")).rstrip("/") for item in current.get("items", [])}
    try:
        root = ET.fromstring(fetch(FEED_URL))
    except Exception as exc:
        print(f"Scout could not fetch/parse RSS: {exc}", file=sys.stderr)
        return 1

    discovered = []
    for item in root.findall("./channel/item"):
        title = text_of(item, "title")
        raw_link = text_of(item, "link")
        source_el = item.find("source")
        source_url = source_el.attrib.get("url", "") if source_el is not None else ""
        source_name = "".join(source_el.itertext()).strip() if source_el is not None else ""
        if not title or not raw_link or not host_is_official(source_url):
            continue
        official_url = resolve_official_url(raw_link)
        if not official_url:
            continue
        canonical = official_url.split("?")[0].rstrip("/")
        if canonical in known:
            continue
        pub_date = text_of(item, "pubDate")
        description = text_of(item, "description")
        digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:12]
        discovered.append({
            "id": "scout-" + digest,
            "status": "draft",
            "type": "official",
            "title": title,
            "excerpt": "Rascunho recolhido do feed oficial. Redigir resumo original em PT-BR e validar antes de publicar.",
            "source": source_name or "Rockstar Games",
            "date": pub_date,
            "url": canonical,
            "editorialNote": "Revisar título, data e contexto; não publicar sem revisão."
        })
        known.add(canonical)

    if discovered:
        current.setdefault("items", [])
        current["items"] = discovered + current["items"]
        current["updatedAt"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        FEED_PATH.write_text(json.dumps(current, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Added {len(discovered)} official-source draft(s).")
    else:
        print("No new official GTA VI Newswire items.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
