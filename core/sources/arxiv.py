"""arXiv source wrapper — wraps core.fetch.fetch_arxiv."""

from __future__ import annotations

import time
from datetime import datetime, timezone

from core.sources.base import BaseFetcher, SourceConfig, FetchResult, HealthRecord, save_health_record
from core.fetch import fetch_arxiv
from core.data import write_dlq


class ArxivFetcher(BaseFetcher):
    def fetch(self, since_hours: int | None = None, **kwargs) -> FetchResult:
        t0 = time.time()
        cfg = self.config.params
        try:
            items = fetch_arxiv(
                since_hours=since_hours or cfg.get("since_hours", 72),
                max_results=kwargs.get("max_results", cfg.get("max_results", 100)),
            )
            latency = (time.time() - t0) * 1000
            result = FetchResult(items=items, success=True, item_count=len(items), latency_ms=round(latency, 1))
        except Exception as e:
            latency = (time.time() - t0) * 1000
            write_dlq(self.name, "arxiv_api", str(e), {"since_hours": since_hours})
            result = FetchResult(success=False, error=str(e), latency_ms=round(latency, 1))
        save_health_record(HealthRecord(source=self.name, timestamp=datetime.now(timezone.utc).isoformat(),
                                        success=result.success, latency_ms=result.latency_ms,
                                        item_count=result.item_count, error=result.error))
        return result
