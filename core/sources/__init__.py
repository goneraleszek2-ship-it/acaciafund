"""Source registry — loads and manages all data sources.

Usage:
    from core.sources import registry
    for fetcher in registry.get_enabled():
        result = fetcher.fetch(since_hours=24)
        process(result.items)
"""

from __future__ import annotations

import tomllib
from pathlib import Path

from core.sources.arxiv import ArxivFetcher
from core.sources.base import BaseFetcher, SourceConfig, all_source_summaries
from core.sources.hn import HNFetcher
from core.sources.pubmed import PubMedFetcher
from core.sources.rss import RSSFetcher
from core.sources.semantic_scholar import SemanticScholarFetcher

SOURCES_TOML = Path(__file__).resolve().parent.parent.parent / "etc" / "sources.toml"

FETCHER_CLASSES: dict[str, type[BaseFetcher]] = {
    "hn": HNFetcher,
    "arxiv": ArxivFetcher,
    "pubmed": PubMedFetcher,
    "semantic_scholar": SemanticScholarFetcher,
    "rss": RSSFetcher,
}


def _load_toml() -> dict:
    if not SOURCES_TOML.exists():
        return {"source": {}}
    try:
        with open(SOURCES_TOML, "rb") as f:
            return tomllib.load(f)
    except (tomllib.TOMLDecodeError, OSError):
        return {"source": {}}


class SourceRegistry:
    """Registry of all configured sources. Loaded lazily from etc/sources.toml."""

    def __init__(self):
        self._fetchers: list[BaseFetcher] | None = None
        self._fetcher_map: dict[str, BaseFetcher] = {}

    def _load(self) -> list[BaseFetcher]:
        if self._fetchers is not None:
            return self._fetchers
        raw = _load_toml()
        fetchers: list[BaseFetcher] = []
        for name, data in raw.get("source", {}).items():
            if not isinstance(data, dict):
                continue
            source_type = data.get("type", "api")
            config = SourceConfig.from_toml(name, data)
            fetcher_class = FETCHER_CLASSES.get(source_type)
            if fetcher_class is None:
                continue
            try:
                fetcher = fetcher_class(config)
                fetchers.append(fetcher)
                self._fetcher_map[name] = fetcher
            except Exception:
                continue
        self._fetchers = fetchers
        return fetchers

    def invalidate(self) -> None:
        self._fetchers = None
        self._fetcher_map = {}

    @property
    def all(self) -> list[BaseFetcher]:
        return self._load()

    @property
    def enabled(self) -> list[BaseFetcher]:
        return [f for f in self._load() if f.config.enabled]

    def get(self, name: str) -> BaseFetcher | None:
        self._load()
        return self._fetcher_map.get(name)

    # ── Health / summaries ──

    def summaries(self) -> list[dict]:
        names = [f.name for f in self._load()]
        return all_source_summaries(names)

    def source_list(self) -> list[dict]:
        """Return all sources as dicts for admin UI."""
        result = []
        for f in self._load():
            s = {
                "name": f.name,
                "type": f.config.type,
                "category": f.category,
                "enabled": f.config.enabled,
                "quality_weight": f.config.quality_weight,
                "schedule_hours": f.config.schedule_hours,
            }
            result.append(s)
        return result


# Singleton
registry = SourceRegistry()


__all__ = ["registry", "SourceRegistry", "BaseFetcher", "SourceConfig"]
