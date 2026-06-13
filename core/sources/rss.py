"""Generic RSS/Atom feed reader source."""

from __future__ import annotations

import time
import re
from datetime import datetime, timezone
from xml.etree import ElementTree as ET
from typing import Any

from core.sources.base import BaseFetcher, SourceConfig, FetchResult, HealthRecord, save_health_record
from core.data import write_dlq, log
from core.fetch import _request, _cached_request


class RSSFetcher(BaseFetcher):
    """Fetches articles from any RSS/Atom feed URL."""

    def __init__(self, config: SourceConfig):
        super().__init__(config)
        self.feed_url = config.params.get("url", "")
        if not self.feed_url:
            raise ValueError(f"RSSFetcher '{config.name}' requires 'url' in params")

    def fetch(self, since_hours: int | None = None, **kwargs) -> FetchResult:
        t0 = time.time()
        cfg = self.config.params
        max_items = kwargs.get("max_results", cfg.get("max_results", 20))
        cache_hours = cfg.get("cache_ttl_hours", 6)

        try:
            raw = _cached_request(self.feed_url, f"rss_{self.config.name}", ttl_hours=cache_hours)
            if raw is None:
                raise OSError(f"Failed to fetch RSS feed: {self.feed_url}")

            items = self._parse_feed(raw, since_hours or cfg.get("since_hours", 168), max_items)
            latency = (time.time() - t0) * 1000
            result = FetchResult(items=items, success=True, item_count=len(items), latency_ms=round(latency, 1))

        except Exception as e:
            latency = (time.time() - t0) * 1000
            write_dlq(self.name, self.feed_url, str(e), {"since_hours": since_hours})
            result = FetchResult(success=False, error=str(e), latency_ms=round(latency, 1))

        save_health_record(HealthRecord(source=self.name, timestamp=datetime.now(timezone.utc).isoformat(),
                                        success=result.success, latency_ms=result.latency_ms,
                                        item_count=result.item_count, error=result.error))
        return result

    def _parse_feed(self, raw: str, since_hours: int, max_items: int) -> list[dict]:
        items: list[dict] = []
        root = ET.fromstring(raw)

        # Detect RSS vs Atom
        is_rss = root.tag == "rss"

        if is_rss:
            entries = root.findall(".//item")
            for entry in entries[:max_items * 2]:
                item = self._parse_rss_item(entry)
                if item and self._is_recent(item.get("published", ""), since_hours):
                    items.append(item)
        else:
            entries = root.findall("{http://www.w3.org/2005/Atom}entry")
            for entry in entries[:max_items * 2]:
                item = self._parse_atom_item(entry)
                if item and self._is_recent(item.get("published", ""), since_hours):
                    items.append(item)

        return items[:max_items]

    def _parse_rss_item(self, entry: Any) -> dict | None:
        def _tag(tag: str) -> str:
            el = entry.find(tag)
            return el.text.strip() if el is not None and el.text else ""

        title = _tag("title")
        link = _tag("link")
        if not title or not link:
            return None
        return {
            "title": title,
            "url": link,
            "published": _tag("pubDate") or _tag("dc:date"),
            "author": _tag("author") or _tag("dc:creator"),
            "summary": re.sub(r'<[^>]+>', '', _tag("description"))[:500],
            "source": self.name,
        }

    def _parse_atom_item(self, entry: Any) -> dict | None:
        ns = "{http://www.w3.org/2005/Atom}"
        title_el = entry.find(f"{ns}title")
        link_el = entry.find(f"{ns}link")
        if title_el is None or link_el is None:
            return None
        title = (title_el.text or "").strip()
        link = (link_el.get("href") or "").strip()
        if not title or not link:
            return None
        published_el = entry.find(f"{ns}published") or entry.find(f"{ns}updated")
        author_el = entry.find(f"{ns}author/{ns}name")
        summary_el = entry.find(f"{ns}summary") or entry.find(f"{ns}content")
        return {
            "title": title,
            "url": link,
            "published": (published_el.text or "").strip() if published_el is not None else "",
            "author": (author_el.text or "").strip() if author_el is not None else "",
            "summary": re.sub(r'<[^>]+>', '', (summary_el.text or "") if summary_el is not None else "")[:500],
            "source": self.name,
        }

    @staticmethod
    def _is_recent(pub_date_str: str, since_hours: int) -> bool:
        if not pub_date_str:
            return True
        try:
            from email.utils import parsedate_to_datetime
            pub = parsedate_to_datetime(pub_date_str)
            return (datetime.now(timezone.utc) - pub).total_seconds() < since_hours * 3600
        except Exception:
            try:
                pub = datetime.fromisoformat(pub_date_str.replace("Z", "+00:00"))
                return (datetime.now(timezone.utc) - pub).total_seconds() < since_hours * 3600
            except Exception:
                return True  # can't parse, include it
