"""HN (Hacker News) source wrapper — wraps core.fetch.fetch_hn_stories."""

from __future__ import annotations

import time
from datetime import datetime, timezone

from core.sources.base import BaseFetcher, SourceConfig, FetchResult, HealthRecord, save_health_record
from core.fetch import fetch_hn_stories
from core.data import write_dlq


class HNFetcher(BaseFetcher):
    """Fetches Hacker News stories via Algolia API."""

    def fetch(self, since_hours: int | None = None, **kwargs) -> FetchResult:
        t0 = time.time()
        cfg = self.config.params
        try:
            items = fetch_hn_stories(
                since_hours=since_hours or cfg.get("since_hours", 24),
                min_points=cfg.get("min_points", 2),
                max_hits=cfg.get("max_hits", 1000),
            )
            latency = (time.time() - t0) * 1000
            result = FetchResult(
                items=items,
                success=True,
                item_count=len(items),
                latency_ms=round(latency, 1),
            )
        except Exception as e:
            latency = (time.time() - t0) * 1000
            write_dlq(self.name, "algolia_api", str(e), {"since_hours": since_hours})
            result = FetchResult(success=False, error=str(e), latency_ms=round(latency, 1))

        save_health_record(HealthRecord(
            source=self.name,
            timestamp=datetime.now(timezone.utc).isoformat(),
            success=result.success,
            latency_ms=result.latency_ms,
            item_count=result.item_count,
            error=result.error,
        ))
        return result
