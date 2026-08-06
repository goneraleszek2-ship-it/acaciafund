"""Flashcard collection and index helpers for the review/study queue pages.

Pure functions over the registry so the build can embed card data into
``review`` / ``study`` pages and expose a static index (``flashcard_index.json``)
for the header due-count badge.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def collect_flashcards(registry_items: list[Any]) -> list[dict]:
    """Return review cards from registry items' ``flashcards`` fields.

    Card id is ``{slug}#{index}`` and matches the SM-2 store key used by
    ``static/js/learning_hub.js``.
    """
    cards: list[dict] = []
    for raw in registry_items:
        item = raw if isinstance(raw, dict) else (raw.model_dump() if hasattr(raw, "model_dump") else {})
        flashcards = item.get("flashcards") or []
        if not flashcards:
            continue
        slug = item.get("slug", "")
        pillar = item.get("pillar", "aml")
        for index, fc in enumerate(flashcards):
            term = fc.get("term", "") or fc.get("front", "")
            definition = fc.get("definition", "") or fc.get("back", "")
            if not term:
                continue
            cards.append({
                "id": f"{slug}#{index}",
                "term": term,
                "definition": definition,
                "pillar": pillar,
                "slug": slug,
            })
    return cards


def write_flashcard_index(cards: list[dict], path: Path) -> None:
    """Write the lightweight card index consumed by the header due badge."""
    payload = {
        "generatedAt": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "total": len(cards),
        "cards": [
            {"id": c["id"], "term": c["term"], "pillar": c["pillar"]}
            for c in cards
        ],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
