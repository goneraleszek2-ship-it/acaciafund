#!/usr/bin/env python3
"""Retroactive off-topic cleanup for registry items.

Strategy: scan each item's TITLE for negative keyword matches.  If the title
itself contains off-topic signals (e.g. "crispr", "genom", "differential
geometry", "protein", "bun runtime") it almost certainly does not belong under
its assigned pillar.

This avoids the false-positive problem of scanning body/description text where
off-topic words can appear in legitimate passing references.

Usage:
    python3 scripts/cleanup_offtopic.py --dry-run          # preview only (default)
    python3 scripts/cleanup_offtopic.py --apply            # actually remove flagged items
    python3 scripts/cleanup_offtopic.py --pillar data      # single pillar
    python3 scripts/cleanup_offtopic.py --verbose          # per-item detail
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.knowledge_ingester import PILLAR_NEGATIVE_TAGS, PILLAR_CONFIGS, score_pillar_relevance

logger = logging.getLogger(__name__)

REGISTRY_PILLAR_TO_INTERNAL = {
    "aml": "aml",
    "data-engineering": "data",
    "stock": "market",
    "compliance": "aml",
}


def title_has_negative_tags(title: str, negative_patterns: list[str]) -> list[str]:
    """Return list of negative patterns that match in the title."""
    lower = title.lower()
    hits: list[str] = []
    for p in negative_patterns:
        if re.search(p, lower):
            hits.append(p)
    return hits


def title_has_positive_tags(title: str, config) -> list[str]:
    """Return list of positive tags that match in the title."""
    lower = title.lower()
    hits: list[str] = []
    for tag, patterns in config.keyword_patterns.items():
        for p in patterns:
            if re.search(p, lower):
                hits.append(tag)
                break
    return hits


def main() -> int:
    parser = argparse.ArgumentParser(description="Retroactive off-topic cleanup")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Preview only (default)")
    parser.add_argument("--apply", action="store_true", help="Actually remove flagged items")
    parser.add_argument("--pillar", choices=["aml", "data", "market", "data-engineering", "stock", "compliance", "all"], default="all", help="Which pillar to check")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show per-item scores")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(message)s")

    if args.apply:
        args.dry_run = False

    registry_path = ROOT / "registry.json"
    with open(registry_path) as f:
        registry = json.load(f)

    content: list[dict[str, Any]] = registry.get("content", [])
    if not content:
        logger.info("No content items found.")
        return 0

    if args.pillar == "all":
        target_internal = set(REGISTRY_PILLAR_TO_INTERNAL.values())
    elif args.pillar in ("data-engineering", "stock", "compliance"):
        pillar_map = {"data-engineering": "data", "stock": "market", "compliance": "aml"}
        target_internal = {pillar_map[args.pillar]}
    else:
        target_internal = {args.pillar}

    to_remove: list[dict[str, Any]] = []
    kept: list[dict[str, Any]] = []

    for item in content:
        registry_pillar = item.get("pillar", "")
        internal_key = REGISTRY_PILLAR_TO_INTERNAL.get(registry_pillar)
        if internal_key is None or internal_key not in target_internal:
            kept.append(item)
            continue

        config = PILLAR_CONFIGS[internal_key]
        negative_patterns = PILLAR_NEGATIVE_TAGS.get(internal_key, [])
        title = item.get("title", "")

        neg_hits = title_has_negative_tags(title, negative_patterns)
        pos_hits = title_has_positive_tags(title, config)

        slug = item.get("slug", "?")

        # Remove if title has negative hits AND zero positive signal in title
        if neg_hits and not pos_hits:
            to_remove.append(item)
            if args.verbose:
                logger.debug(f"  REMOVE  [{slug}] neg={neg_hits}")
        elif neg_hits and pos_hits:
            # Mixed signals — keep but log
            if args.verbose:
                logger.debug(f"  MIXED   [{slug}] neg={neg_hits} pos={pos_hits}")
            kept.append(item)
        else:
            kept.append(item)
            if args.verbose:
                logger.debug(f"  KEEP    [{slug}]")

    logger.info("")
    logger.info(f"Checked {len(content)} items  |  To remove: {len(to_remove)}  |  Kept: {len(kept)}")

    if to_remove:
        logger.info("")
        logger.info("Items to remove:")
        for item in sorted(to_remove, key=lambda x: x.get("slug", "")):
            slug = item.get("slug", "?")
            title = item.get("title", "")[:100]
            neg_hits = title_has_negative_tags(title, PILLAR_NEGATIVE_TAGS.get(
                REGISTRY_PILLAR_TO_INTERNAL.get(item.get("pillar", "")), []))
            logger.info(f"  • {slug}")
            logger.info(f"    Title: {title}")
            logger.info(f"    Negative matches: {neg_hits}")
            logger.info("")

    if not args.dry_run and to_remove:
        remove_slugs = {item.get("slug") for item in to_remove}
        registry["content"] = [item for item in kept if item.get("slug") not in remove_slugs]
        with open(registry_path, "w") as f:
            json.dump(registry, f, indent=1)
        logger.info(f"Removed {len(to_remove)} items from {registry_path}")
        logger.info(f"Registry now has {len(registry['content'])} items")
    elif to_remove:
        logger.info(f"Dry run — {len(to_remove)} items would be removed. Use --apply to proceed.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
