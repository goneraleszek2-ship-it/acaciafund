"""SEC EDGAR source wrapper — wraps core.fetch.fetch_sec_edgar."""

from __future__ import annotations

import time
from datetime import datetime, timezone

from core.data import write_dlq
from core.fetch import fetch_sec_edgar
from core.sources.base import (
    BaseFetcher,
    FetchResult,
    HealthRecord,
    save_health_record,
)


class SecEdgarFetcher(BaseFetcher):
    """Fetches SEC EDGAR filings via the EFTS full-text search API."""

    def fetch(self, since_hours: int | None = None, **kwargs) -> FetchResult:
        t0 = time.time()
        cfg = self.config.params
        days_back = max(1, (since_hours or cfg.get("since_hours", 168)) // 24)
        try:
            items = fetch_sec_edgar(
                query=cfg.get("query", "financial markets OR quantitative finance OR market microstructure"),
                days_back=days_back,
                max_results=kwargs.get("max_results", cfg.get("max_results", 50)),
            )
            latency = (time.time() - t0) * 1000
            result = FetchResult(
                items=items, success=True, item_count=len(items), latency_ms=round(latency, 1)
            )
        except Exception as e:
            latency = (time.time() - t0) * 1000
            write_dlq(self.name, "sec_edgar_api", str(e), {"since_hours": since_hours})
            result = FetchResult(success=False, error=str(e), latency_ms=round(latency, 1))
        save_health_record(
            HealthRecord(
                source=self.name,
                timestamp=datetime.now(timezone.utc).isoformat(),
                success=result.success,
                latency_ms=result.latency_ms,
                item_count=result.item_count,
                error=result.error,
            )
        )
        return result
