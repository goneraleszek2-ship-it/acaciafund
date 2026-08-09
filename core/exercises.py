"""Load and attach browser sandbox exercises to content items.

Exercises are defined in data/exercises.json and matched to learn items by
slug. Attached exercises are serialized into the page for the client-side
sandboxes (sql.js, Pyodide/Polars, and pure-JS simulations).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

DEFAULT_PATH = Path("data/exercises.json")

EXERCISE_KEYS = ("sql", "polars", "sims")

KIND_MAP = {"sql": "sql", "polars": "polars", "sims": "sim"}


def load_exercises(path: Path | None = None) -> Dict[str, Any]:
    """Load exercises.json; returns {"dataset": {...}, "sql": [...], ...}."""
    path = path or DEFAULT_PATH
    if not path.exists():
        return {"dataset": None, "sql": [], "polars": [], "sims": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"dataset": None, "sql": [], "polars": [], "sims": []}
    if not isinstance(data, dict):
        return {"dataset": None, "sql": [], "polars": [], "sims": []}
    for key in EXERCISE_KEYS:
        if not isinstance(data.get(key), list):
            data[key] = []
    data.setdefault("dataset", None)
    return data


def attach_exercises(
    items: list[Any],
    data: Optional[Dict[str, Any]] = None,
    path: Path | None = None,
) -> int:
    """Attach matching exercises to content items (by full slug).

    Each matched exercise is attached with an injected ``kind`` field
    ("sql" | "polars" | "sim") so templates can route rendering. Items that
    need the SQL dataset (sql/polars exercises) also receive ``sandbox_db``
    with schema + seed. Returns the number of items that received exercises.
    """
    data = data if data is not None else load_exercises(path)
    dataset = data.get("dataset")
    matched = 0
    for item in items:
        slug = getattr(item, "slug", "") or ""
        exercises: List[Dict[str, Any]] = []
        for kind in EXERCISE_KEYS:
            for ex in data.get(kind, []):
                if isinstance(ex, dict) and slug in (ex.get("lesson_slugs") or []):
                    entry = dict(ex)
                    entry["kind"] = KIND_MAP.get(kind, kind)
                    if kind in ("sql", "polars") and dataset:
                        entry["dataset"] = dataset
                    exercises.append(entry)
        if exercises:
            item.sandbox_exercises = exercises
            matched += 1
    return matched
