"""Multi-level caching for ontology operations."""
from __future__ import annotations

import hashlib
import json
import threading
import time
from collections import OrderedDict
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from core.ontology import Concept, OntologyManager, extract_concepts_from_text


class LRUCache:
    """Generic LRU cache with TTL support, thread-safe via threading.Lock."""

    def __init__(self, maxsize: int = 128, ttl: float = 300.0) -> None:
        self._maxsize = maxsize
        self._ttl = ttl
        self._cache: OrderedDict[str, Tuple[float, Any]] = OrderedDict()
        self._lock = threading.Lock()
        self._hit_count = 0
        self._miss_count = 0

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                self._miss_count += 1
                return None
            expiry, value = entry
            if time.monotonic() > expiry:
                del self._cache[key]
                self._miss_count += 1
                return None
            self._cache.move_to_end(key)
            self._hit_count += 1
            return value

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            expiry = time.monotonic() + self._ttl
            self._cache[key] = (expiry, value)
            self._cache.move_to_end(key)
            while len(self._cache) > self._maxsize:
                self._cache.popitem(last=False)

    def invalidate(self, key: Optional[str] = None) -> None:
        with self._lock:
            if key is None:
                self._cache.clear()
            else:
                self._cache.pop(key, None)

    def clear(self) -> None:
        self.invalidate()

    @property
    def stats(self) -> Dict[str, Any]:
        with self._lock:
            total = self._hit_count + self._miss_count
            return {
                "hit_count": self._hit_count,
                "miss_count": self._miss_count,
                "hit_rate": self._hit_count / total if total > 0 else 0.0,
                "size": len(self._cache),
                "maxsize": self._maxsize,
            }


def cached(cache: LRUCache, key_prefix: str = ""):
    """Decorator that caches function results in the given LRUCache.

    Usage::

        @cached(my_cache, "extract")
        def extract_concepts(text: str) -> list[Concept]:
            ...
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            key_parts = [key_prefix, func.__qualname__]
            key_parts.extend(str(a) for a in args)
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            key = hashlib.md5(":".join(key_parts).encode()).hexdigest()
            result = cache.get(key)
            if result is not None:
                return result
            result = func(*args, **kwargs)
            cache.set(key, result)
            return result
        return wrapper
    return decorator


class OntologyCache:
    """Application-level cache wrapping expensive OntologyManager operations.

    Cache levels:
        L1: In-memory LRU cache (fast, process-local).
        L2: Disk-based JSON cache in *cache_dir* (persistent across runs).
    """

    def __init__(
        self,
        ontology_manager: OntologyManager,
        cache_dir: Optional[Path] = None,
    ) -> None:
        self._om = ontology_manager
        self._cache_dir = cache_dir
        self._l1 = LRUCache(maxsize=128, ttl=300.0)
        self._l2: Dict[str, Any] = {}
        self._l2_files = 0
        self._l2_size_bytes = 0
        if cache_dir is not None:
            cache_dir.mkdir(parents=True, exist_ok=True)
            self._load_l2()

    # ------------------------------------------------------------------
    # L2 helpers
    # ------------------------------------------------------------------

    def _l2_key(self, key: str) -> Optional[Path]:
        if self._cache_dir is None:
            return None
        h = hashlib.sha256(key.encode()).hexdigest()
        return self._cache_dir / f"{h}.json"

    def _load_l2(self) -> None:
        if self._cache_dir is None:
            return
        for f in sorted(self._cache_dir.glob("*.json")):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                self._l2[data["_key"]] = data["value"]
                self._l2_files += 1
                self._l2_size_bytes += f.stat().st_size
            except (json.JSONDecodeError, KeyError, OSError):
                pass

    def _save_l2(self, key: str, value: Any) -> None:
        path = self._l2_key(key)
        if path is None:
            return
        data: Dict[str, Any] = {"_key": key, "value": value}
        path.write_text(json.dumps(data, default=str, indent=2), encoding="utf-8")
        self._l2[key] = value

    def _l2_get(self, key: str) -> Any:
        return self._l2.get(key)

    # ------------------------------------------------------------------
    # Cached operations
    # ------------------------------------------------------------------

    def get_concept(self, concept_id: str) -> Optional[Concept]:
        l1_key = f"get_concept:{concept_id}"
        result = self._l1.get(l1_key)
        if result is not None:
            return result
        result = self._om.get_concept(concept_id)
        self._l1.set(l1_key, result)
        return result

    def find_concepts(
        self,
        *,
        pillar: Optional[str] = None,
        category: Optional[str] = None,
        text_query: Optional[str] = None,
    ) -> List[Concept]:
        l1_key = f"find_concepts:p={pillar}:c={category}:q={text_query}"
        result = self._l1.get(l1_key)
        if result is not None:
            return result
        result = self._om.find_concepts(
            pillar=pillar, category=category, text_query=text_query
        )
        self._l1.set(l1_key, result)
        return result

    def concepts_by_pillar(self) -> Dict[str, List[Concept]]:
        l1_key = "concepts_by_pillar"
        result = self._l1.get(l1_key)
        if result is not None:
            return result
        result = self._om.concepts_by_pillar()
        self._l1.set(l1_key, result)
        return result

    def extract_concepts(
        self,
        text: str,
        *,
        min_confidence: float = 0.5,
    ) -> List[Tuple[str, float]]:
        text_hash = hashlib.md5(text.encode()).hexdigest()
        l1_key = f"extract:{text_hash}:mc={min_confidence}"

        result = self._l1.get(l1_key)
        if result is not None:
            return result

        l2_result = self._l2_get(l1_key)
        if l2_result is not None:
            self._l1.set(l1_key, l2_result)
            return l2_result

        raw = extract_concepts_from_text(
            text, self._om, min_confidence=min_confidence
        )
        result = [(c.id, s) for c, s in raw]
        self._l1.set(l1_key, result)
        self._save_l2(l1_key, result)
        return result

    def related_concepts(
        self, concept_id: str, max_depth: int = 1
    ) -> List[Concept]:
        l1_key = f"related:{concept_id}:d={max_depth}"
        result = self._l1.get(l1_key)
        if result is not None:
            return result

        if max_depth <= 1:
            result = self._om.related_concepts(concept_id)
        else:
            seen: set[str] = {concept_id}
            frontier: set[str] = {concept_id}
            for _ in range(max_depth):
                next_frontier: set[str] = set()
                for cid in frontier:
                    for r in self._om.relations_for(cid):
                        other = (
                            r.target_id if r.source_id == cid else r.source_id
                        )
                        if other not in seen:
                            seen.add(other)
                            next_frontier.add(other)
                frontier = next_frontier
                if not frontier:
                    break
            seen.discard(concept_id)
            result = []
            for cid in seen:
                c = self._om.get_concept(cid)
                if c is not None:
                    result.append(c)

        self._l1.set(l1_key, result)
        return result

    def auto_populate_cross_pillar_analogs(self) -> int:
        l1_key = "auto_populate_cross_pillar_analogs"
        result = self._l1.get(l1_key)
        if result is not None:
            return result
        result = self._om.auto_populate_cross_pillar_analogs()
        self._l1.set(l1_key, result)
        return result

    # ------------------------------------------------------------------
    # Invalidation & statistics
    # ------------------------------------------------------------------

    def invalidate(self) -> None:
        self._l1.clear()
        self._l2.clear()
        if self._cache_dir is not None:
            for f in self._cache_dir.glob("*.json"):
                f.unlink()
        self._l2_files = 0
        self._l2_size_bytes = 0

    @property
    def stats(self) -> Dict[str, Any]:
        l1_s = self._l1.stats
        return {
            "l1_size": l1_s["size"],
            "l1_maxsize": l1_s["maxsize"],
            "l1_hits": l1_s["hit_count"],
            "l1_misses": l1_s["miss_count"],
            "l1_hit_rate": l1_s["hit_rate"],
            "l2_files": self._l2_files,
            "l2_size_bytes": self._l2_size_bytes,
        }
