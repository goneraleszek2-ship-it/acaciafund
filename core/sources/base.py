"""Base classes for the AcaciaFund source framework (DataOps Foundation).

Every content/image source implements BaseFetcher and is registered
in etc/sources.toml. The registry provides health tracking, DLQ wiring,
and uniform metrics across all sources.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ── Data classes ──

@dataclass
class SourceConfig:
    """Configuration for a single source, loaded from etc/sources.toml."""
    name: str
    type: str                # "api" | "rss" | "scraper" | "image_api"
    enabled: bool = True
    category: str = "general"
    quality_weight: float = 0.5
    params: dict = field(default_factory=dict)
    schedule_hours: int = 24

    @classmethod
    def from_toml(cls, name: str, data: dict) -> "SourceConfig":
        return cls(
            name=name,
            type=data.get("type", "api"),
            enabled=data.get("enabled", True),
            category=data.get("category", "general"),
            quality_weight=data.get("quality_weight", 0.5),
            params=data.get("params", {}),
            schedule_hours=data.get("schedule", {}).get("every_hours", 24),
        )


@dataclass
class FetchResult:
    items: list[dict] = field(default_factory=list)
    success: bool = True
    error: str | None = None
    item_count: int = 0
    latency_ms: float = 0.0


@dataclass
class HealthRecord:
    source: str
    timestamp: str = ""
    success: bool = True
    latency_ms: float = 0.0
    item_count: int = 0
    error: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


# ── Base fetcher ──

class BaseFetcher(ABC):
    """Abstract base for all content/image fetchers.

    Subclasses must implement fetch() and provide name/category metadata.
    """

    def __init__(self, config: SourceConfig):
        self.config = config

    @property
    def name(self) -> str:
        return self.config.name

    @property
    def category(self) -> str:
        return self.config.category

    @abstractmethod
    def fetch(self, since_hours: int | None = None, **kwargs) -> FetchResult:
        """Fetch items from this source. Returns FetchResult with items + health data."""
        ...

    def health_check(self) -> dict:
        """Lightweight health probe. Returns {'ok': bool, 'latency_ms': float}."""
        import time
        t0 = time.time()
        try:
            result = self.fetch(since_hours=1, max_results=1)
            return {"ok": result.success, "latency_ms": result.latency_ms, "error": result.error}
        except Exception as e:
            return {"ok": False, "latency_ms": (time.time() - t0) * 1000, "error": str(e)}


# ── Health persistence ──

HEALTH_PATH = Path(__file__).resolve().parent.parent.parent / "registry" / "source-health.json"


def load_health_records() -> dict[str, list[dict]]:
    if not HEALTH_PATH.exists():
        return {}
    try:
        return json.loads(HEALTH_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def save_health_record(record: HealthRecord) -> None:
    records = load_health_records()
    records.setdefault(record.source, []).append(record.to_dict())
    # Keep last 100 per source
    records[record.source] = records[record.source][-100:]
    HEALTH_PATH.parent.mkdir(parents=True, exist_ok=True)
    HEALTH_PATH.write_text(json.dumps(records, indent=2, default=str), encoding="utf-8")


def source_summary(source_name: str) -> dict:
    """Compute summary stats for a source from health records."""
    records = load_health_records().get(source_name, [])
    if not records:
        return {"name": source_name, "total_runs": 0, "success_rate": 0, "avg_latency_ms": 0, "total_items": 0}
    successes = sum(1 for r in records if r.get("success"))
    total = len(records)
    return {
        "name": source_name,
        "total_runs": total,
        "success_rate": round(successes / total * 100, 1) if total else 0,
        "avg_latency_ms": round(sum(r.get("latency_ms", 0) for r in records) / total, 1) if total else 0,
        "total_items": sum(r.get("item_count", 0) for r in records),
        "last_run": records[-1].get("timestamp", "") if records else "",
        "last_success": records[-1].get("success", False) if records else None,
        "last_error": records[-1].get("error") if records and not records[-1].get("success") else None,
    }


def all_source_summaries(source_names: list[str]) -> list[dict]:
    return [source_summary(name) for name in source_names]
