#!/usr/bin/env python3
"""Collect official Rockstar and selected international GTA VI coverage as editorial drafts.

Third-party headlines are never auto-published. Editors must verify context and write
an original Portuguese summary before changing status to published.
"""
from __future__ import annotations

import hashlib
import json
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

QUERIES = [
    'GTA VI OR GTA 6 site:rockstargames.com/newswire',
    'GTA VI OR GTA 6 (launch OR release OR gameplay OR map OR trailer)',
    'GTA VI OR GTA 6 (UK internet OR broadband OR download OR preload)',
    'GTA VI OR GTA 6 (worldwide OR countries OR search trends OR sales)',
]
ALLOWED_HOSTS = {
    "rockstargames.com", "www.rockstargames.com", "support.rockstargames.com",
    "bbc.com", "www.bbc.com", "bbc.co.uk", "www.bbc.co.uk",
    "reuters.com", "www.reuters.com", "apnews.com", "www.apnews.com",
    "theguardian.com", "www.theguardian.com", "independent.co.uk", "www.independent.co.uk",
    "ign.com", "www.ign.com", "eurogamer.net", "www.eurogamer.net",
    "gamespot.com", "www.gamespot.com", "polygon.com", "www.polygon.com",
    "pcgamer.com", "www.pcgamer.com", "vgc.com", "www.videogameschronicle.com",
    "videogameschronicle.com", "gamesradar.com", "www.gamesradar.com",
    "kotaku.com", "www.kotaku.com", "theverge.com", "www.theverge.com",
    "ispreview.co.uk", "www.ispreview.co.uk", "pushsquare.com", "www.pushsquare.com",
    "purexbox.com", "www.purexbox.com", "uol.com.br", "www.uol.com.br",
}
FEED_PATH = Path("data/gta-news.json")
USER_AGENT = "ODEVI-GTA6-NewsScout/2.0"


def host_is_allowed(url: str) -> bool:
    try:
        host = (urllib.parse.urlparse(url).hostname or "").lower()
        return host in ALLOWED_HOSTS
    except Exception:
        return False


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=25) as response:
        return response.read(3_000_000)


def resolve_publisher_url(url: str) -> str | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=20) as response:
            final_url = response.geturl()
        return final_url if host_is_allowed(final_url) else None
    except Exception:
        return None


def text_of(parent: ET.Element, tag: str) -> str:
    el = parent.find(tag)
    return "".join(el.itertext()).strip() if el is not None else ""


def main() -> int:
    current = json.loads(FEED_PATH.read_text(encoding="utf-8"))
    known = {str(item.get("url", "")).rstrip("/") for item in current.get("items", [])}
    discovered = []
    failures = []

    for query in QUERIES:
        url = "https://news.google.com/rss/search?q=" + urllib.parse.quote(query) + "&hl=en-US&gl=US&ceid=US:en"
        try:
            root = ET.fromstring(fetch(url))
        except Exception as exc:
            failures.append(f"RSS query failed: {exc}")
            continue

        for item in root.findall("./channel/item"):
            title = text_of(item, "title")
            raw_link = text_of(item, "link")
            source_el = item.find("source")
            source_url = source_el.attrib.get("url", "") if source_el is not None else ""
            source_name = "".join(source_el.itertext()).strip() if source_el is not None else ""
            if not title or not raw_link or not host_is_allowed(source_url):
                continue
            publisher_url = resolve_publisher_url(raw_link)
            if not publisher_url:
                continue
            canonical = publisher_url.split("?")[0].rstrip("/")
            if canonical in known:
                continue
            pub_date = text_of(item, "pubDate")
            digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:12]
            official = urllib.parse.urlparse(canonical).hostname in {
                "rockstargames.com", "www.rockstargames.com", "support.rockstargames.com"
            }
            discovered.append({
                "id": "scout-" + digest,
                "status": "draft",
                "type": "official" if official else "press",
                "title": title,
                "excerpt": (
                    "Rascunho recolhido de fonte oficial Rockstar. Confirmar data e contexto antes de publicar."
                    if official else
                    "Rascunho recolhido de imprensa selecionada. Verificar a notícia na fonte, confirmar contexto e escrever resumo original em português antes de publicar."
                ),
                "source": source_name or ("Rockstar Games" if official else "Imprensa internacional"),
                "date": pub_date,
                "url": canonical,
                "editorialNote": "Não publicar automaticamente. Validar a fonte, data, contexto e escrever resumo original."
            })
            known.add(canonical)

    if discovered:
        current.setdefault("items", [])
        current["items"] = discovered + current["items"]
        current["updatedAt"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        FEED_PATH.write_text(json.dumps(current, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Added {len(discovered)} new editorial draft(s).")
    if failures:
        print("\n".join(failures), file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
