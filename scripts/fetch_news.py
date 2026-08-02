#!/usr/bin/env python3
"""Fetch and curate field news for the AcaciaFund portal.

Sources:
  - Hacker News (Algolia API) — scored against each pillar's keyword matrix
  - Curated RSS/Atom feeds per pillar (best-effort, stdlib XML parsing)

Writes ``data/news.json``, consumed by the build to render the ``/news/``
page and the homepage "Latest from the field" section. Degrades gracefully:
if every network source fails, the previously fetched news is preserved so
the site never ships an empty news page.

Usage:
    python3 scripts/fetch_news.py                # HN + RSS feeds
    python3 scripts/fetch_news.py --hn-only      # skip feeds
    python3 scripts/fetch_news.py --limit 45     # cap total items
"""

import argparse
import json
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.data import USER_AGENT  # noqa: E402

NEWS_PATH = PROJECT_ROOT / "data" / "news.json"

DEFAULT_LIMIT = 45
PER_PILLAR_CAP = 10

# ── RSS / Atom feeds per pillar (best-effort; failures are skipped) ──────
FEEDS: list[dict[str, Any]] = [
    {"name": "FinCEN", "pillar": "aml", "url": "https://www.fincen.gov/rss.xml"},
    {"name": "ACAMS", "pillar": "aml", "url": "https://www.acams.org/feed/"},
    {"name": "FATF", "pillar": "aml", "url": "https://www.fatf-gafi.org/en/fatf.rss"},
    {"name": "MarketWatch", "pillar": "market", "url": "https://feeds.content.dowjones.io/public/rss/mw_topstories"},
    {"name": "NASDAQ", "pillar": "market", "url": "https://www.nasdaq.com/rss/markets/market-news"},
    {"name": "Traders Magazine", "pillar": "market", "url": "https://www.tradersmagazine.com/feed/"},
    {"name": "InfoQ", "pillar": "data", "url": "https://www.infoq.com/feed/"},
    {"name": "Datanami", "pillar": "data", "url": "https://www.datanami.com/feed/"},
    {"name": "Apache Flink", "pillar": "data", "url": "https://flink.apache.org/feed.xml"},
]


def _http_get(url: str, timeout: int = 20) -> str | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception:
        return None


def _parse_rss(raw: str) -> list[dict[str, Any]]:
    """Parse RSS 2.0 / Atom into {title, url, published_at} items."""
    try:
        root = ET.fromstring(raw)
    except ET.ParseError:
        return []
    items: list[dict[str, Any]] = []
    for node in root.iter():
        tag = node.tag.rsplit("}", 1)[-1]
        if tag not in ("item", "entry"):
            continue
        title = pub = link = ""
        for child in node:
            ctag = child.tag.rsplit("}", 1)[-1]
            if ctag == "title":
                title = (child.text or "").strip()
            elif ctag in ("link", "guid"):
                if ctag == "link" and link:
                    continue
                if child.get("href"):
                    link = child.get("href") or ""
                else:
                    link = (child.text or "").strip()
            elif ctag in ("pubDate", "published", "updated", "date"):
                pub = (child.text or "").strip()
        if title and link:
            items.append({"title": title, "url": link, "published_at": pub})
    return items


def _parse_date(value: str) -> datetime | None:
    if not value:
        return None
    for fmt in (
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S %Z",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%d",
    ):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def _norm_url(url: str) -> str:
    return re.sub(r"[?#].*$", "", url).rstrip("/").lower()


def _title_key(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", title.lower()).strip()


def _dedupe(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen_urls: set[str] = set()
    seen_titles: set[str] = set()
    out: list[dict[str, Any]] = []
    for item in items:
        key = _norm_url(item["url"])
        tkey = _title_key(item["title"])[:80]
        if key and key in seen_urls:
            continue
        if tkey and tkey in seen_titles:
            continue
        seen_urls.add(key)
        seen_titles.add(tkey)
        out.append(item)
    return out


def _pillar_key(label: str) -> str:
    return {"aml": "aml", "market": "stock", "data": "data-engineering"}.get(label, label)


def fetch_hn_items(since_hours: int = 72, min_points: int = 5) -> list[dict[str, Any]]:
    from core.fetch import fetch_hn_stories

    stories = fetch_hn_stories(since_hours=since_hours, min_points=min_points, max_hits=400)
    items = []
    for s in stories:
        created = s.get("created_at_i")
        published = None
        if created:
            published = datetime.fromtimestamp(int(created), tz=timezone.utc).isoformat()
        items.append(
            {
                "title": s.get("title", ""),
                "url": s.get("url", ""),
                "source": "Hacker News",
                "source_type": "hn",
                "points": int(s.get("points", 0) or 0),
                "published_at": published,
            }
        )
    return items


def fetch_feed_items() -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for feed in FEEDS:
        raw = _http_get(feed["url"])
        if not raw:
            continue
        for it in _parse_rss(raw):
            items.append(
                {
                    "title": it["title"],
                    "url": it["url"],
                    "source": feed["name"],
                    "source_type": "feed",
                    "points": 0,
                    "published_at": it["published_at"],
                }
            )
    return items


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hn-only", action="store_true", help="Skip RSS feeds")
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT, help="Max total items")
    parser.add_argument("--min-score", type=float, default=0.15, help="Pillar relevance threshold")
    args = parser.parse_args()

    from scripts.knowledge_ingester import PILLAR_CONFIGS, score_pillar_relevance  # noqa: E402

    prior = None
    if NEWS_PATH.exists():
        try:
            prior = json.loads(NEWS_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            prior = None

    raw_items: list[dict[str, Any]] = []
    if not args.hn_only:
        feed_items = fetch_feed_items()
        raw_items.extend(feed_items)
        print(f"  feeds: {len(feed_items)} raw items")
    hn_items = fetch_hn_items()
    raw_items.extend(hn_items)
    print(f"  hn:    {len(hn_items)} raw items")

    # Score and assign each item to its best pillar
    scored: list[dict[str, Any]] = []
    for it in raw_items:
        title = it["title"] or ""
        if not title:
            continue
        best_pillar, best_score = None, 0.0
        for slug, cfg in PILLAR_CONFIGS.items():
            score, _ = score_pillar_relevance(title, cfg)
            if score > best_score:
                best_score, best_pillar = score, slug
        if best_pillar is None or best_score < args.min_score:
            continue
        published = None
        if it.get("published_at"):
            dt = _parse_date(it["published_at"])
            if dt:
                published = dt.astimezone(timezone.utc).isoformat()
        scored.append(
            {
                "title": title[:200],
                "url": it["url"],
                "source": it.get("source", "unknown"),
                "source_type": it.get("source_type", "feed"),
                "points": it.get("points", 0),
                "pillar": _pillar_key(best_pillar),
                "published_at": published,
            }
        )

    scored = _dedupe(scored)
    scored.sort(
        key=lambda x: (
            x["published_at"] or "1970-01-01T00:00:00+00:00",
            x["points"],
        ),
        reverse=True,
    )

    # Cap per pillar for balance
    counts: dict[str, int] = {}
    balanced: list[dict[str, Any]] = []
    for it in scored:
        if counts.get(it["pillar"], 0) >= PER_PILLAR_CAP:
            continue
        counts[it["pillar"]] = counts.get(it["pillar"], 0) + 1
        balanced.append(it)
    balanced = balanced[: args.limit]

    if not balanced and prior:
        print("  no fresh items; preserving previously fetched news")
        return 0

    payload = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "item_count": len(balanced),
        "items": balanced,
    }
    NEWS_PATH.write_text(json.dumps(payload, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    per = {}
    for it in balanced:
        per[it["pillar"]] = per.get(it["pillar"], 0) + 1
    print(f"  saved {len(balanced)} news items -> data/news.json ({per})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
