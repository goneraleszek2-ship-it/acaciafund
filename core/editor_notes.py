"""Editor's notes: human-written annotations merged into synthesized articles.

A note is a short editorial voice block that flags nuance, recency, or common
misconceptions inside articles that were automatically synthesized from feeds.
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional

DEFAULT_PATH = Path("data/editor_notes.json")


def load_editor_notes(path: Path | None = None) -> Dict[str, Dict[str, Any]]:
    """Load the slug → note mapping. Missing or malformed files yield {}."""
    notes_path = path or DEFAULT_PATH
    if not notes_path.exists():
        return {}
    try:
        data = json.loads(notes_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    if not isinstance(data, dict):
        return {}
    return {
        slug: note
        for slug, note in data.items()
        if isinstance(note, dict) and note.get("note")
    }


def attach_editor_notes(
    items: list[Any],
    notes: Optional[Dict[str, Dict[str, Any]]] = None,
    path: Path | None = None,
) -> int:
    """Attach editor notes to content items (by slug or suffix match).

    Items are matched on full slug first, then on the topic segment after
    the pillar/content-type prefixes (e.g. "markets/research/mean-reversion"
    matches a note keyed "mean-reversion"). Returns the number attached.
    """
    notes = notes if notes is not None else load_editor_notes(path)
    attached = 0
    for item in items:
        slug = getattr(item, "slug", "") or ""
        note = notes.get(slug) or notes.get(slug.rsplit("/", 1)[-1])
        if note:
            item.editor_note = note
            attached += 1
    return attached
