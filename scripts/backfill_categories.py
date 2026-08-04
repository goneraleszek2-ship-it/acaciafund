#!/usr/bin/env python3
"""Backfill canonical PILLAR_SUBCATEGORIES categories for registry research items.

Research items ingested before the tag→subcategory mapping existed carry
``category: "blog"`` or no category at all.  This script re-scores each item's
title + description with ``score_pillar_relevance``, merges detected tags with
existing ones, and writes the canonical subcategory (``category_from_tags``).

Scope: research items only — learn ("lesson") and knowledge
(``knowledge_category``) items are left untouched.

Usage:
    python3 scripts/backfill_categories.py --dry-run   # preview changes
    python3 scripts/backfill_categories.py --apply     # write registry.json
    python3 scripts/backfill_categories.py --validate  # report + exit 1 if non-conforming
"""

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import PILLAR_SUBCATEGORIES  # noqa: E402
from scripts.knowledge_ingester import (  # noqa: E402
    PILLAR_CONFIGS,
    category_from_tags,
    score_pillar_relevance,
)

REGISTRY_PATH = PROJECT_ROOT / "registry.json"

# registry pillar key → ingester pillar slug
_PILLAR_KEY_TO_SLUG = {
    "aml": "aml",
    "stock": "market",
    "data-engineering": "data",
}


def load_registry() -> dict:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def save_registry(data: dict) -> None:
    REGISTRY_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def categorize_item(item: dict) -> tuple[str | None, list[str] | None]:
    """Return (new_category, new_tags) for an item, or (None, None) if untouched."""
    if item.get("content_type") != "research":
        return None, None
    current = item.get("category")
    if current not in (None, "", "blog"):
        return None, None
    slug = _PILLAR_KEY_TO_SLUG.get(item.get("pillar", ""))
    if not slug or slug not in PILLAR_CONFIGS:
        return None, None
    cfg = PILLAR_CONFIGS[slug]
    text = " ".join([
        item.get("title", "") or "",
        item.get("description", "") or "",
    ])
    _, tags = score_pillar_relevance(text, cfg)
    existing = [t for t in (item.get("tags") or []) if isinstance(t, str)]
    merged = list(dict.fromkeys(existing + tags))
    if not merged:
        return None, None
    return category_from_tags(merged, slug), merged


def validate_categories(data: dict) -> Counter:
    """Return a counter of non-conforming categories (category ∉ pillar taxonomy)."""
    bad: Counter = Counter()
    valid_learn = {None, "lesson", "learn"}
    for item in data.get("content", []) or []:
        cat = item.get("category")
        pillar = item.get("pillar", "")
        ctype = item.get("content_type", "")
        if ctype == "research":
            allowed = set(PILLAR_SUBCATEGORIES.get(pillar, {}).keys())
            if cat not in allowed:
                bad[(pillar, ctype, cat)] += 1
        elif ctype == "learn":
            if cat not in valid_learn:
                bad[(pillar, ctype, cat)] += 1
    return bad


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Preview changes without writing")
    mode.add_argument("--apply", action="store_true", help="Write registry.json")
    mode.add_argument("--validate", action="store_true", help="Report non-conforming categories; exit 1 if any")
    parser.add_argument("--verbose", action="store_true", help="List each changed item")
    args = parser.parse_args()

    if args.validate:
        data = load_registry()
        bad = validate_categories(data)
        for (pillar, ctype, cat), n in sorted(bad.items(), key=lambda kv: str(kv[0])):
            print(f"  [{pillar}/{ctype}] category={cat!r}: {n} items")
        print(f"\n{sum(bad.values())} non-conforming items")
        return 1 if bad else 0

    data = load_registry()
    changed = 0
    examples: list[str] = []
    by_cat: Counter = Counter()
    for item in data.get("content", []) or []:
        new_cat, new_tags = categorize_item(item)
        if new_cat is None:
            continue
        if new_tags is not None:
            item["tags"] = new_tags
        old = item.get("category")
        item["category"] = new_cat
        by_cat[new_cat] += 1
        changed += 1
        if args.verbose and len(examples) < 12:
            examples.append(f"  {item['slug']}: {old!r} → {new_cat!r}")

    print(f"{changed} research items updated")
    if by_cat:
        print("  distribution:", dict(sorted(by_cat.items())))
    for e in examples:
        print(e)

    if args.apply:
        save_registry(data)
        print("registry.json written")
    else:
        print("(dry run — re-run with --apply to write)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
