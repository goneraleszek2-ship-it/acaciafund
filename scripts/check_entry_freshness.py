#!/usr/bin/env python3
"""Entry Freshness Checker — walks registry items and computes freshness status.

Outputs `freshness.json` to dist/ and optionally `entry_freshness.json` to data/.

Usage:
    python3 scripts/check_entry_freshness.py
    python3 scripts/check_entry_freshness.py --update-registry
"""

from __future__ import annotations

import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
REGISTRY_PATH = REPOSITORY_ROOT / "registry.json"
DATA_PATH = REPOSITORY_ROOT / "data" / "entry_freshness.json"
DIST_PATH = REPOSITORY_ROOT / "dist" / "freshness.json"


def compute_freshness(last_verified: date | None) -> str:
    """Compute freshness status based on last_verified date.

    Returns one of: 'fresh', 'stale', 'outdated', 'never'.
    """
    if last_verified is None:
        return "never"
    days = (date.today() - last_verified).days
    if days < 30:
        return "fresh"
    if days < 90:
        return "stale"
    return "outdated"


def parse_date(date_str: str | None) -> date | None:
    """Try to parse a date string in YYYY-MM-DD, ISO, or other common formats."""
    if not date_str:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            return datetime.strptime(date_str[:19], fmt).date()
        except (ValueError, IndexError):
            continue
    return None


def compute_freshness_with_review(
    last_verified: date | None, last_reviewed: date | None
) -> str:
    """Compute freshness using the most recent of last_verified/last_reviewed.

    A manual review (last_reviewed) signals an item is current, but a newer
    last_verified still wins when it is more recent.
    """
    anchor = last_reviewed if last_reviewed and (not last_verified or last_reviewed > last_verified) else last_verified
    return compute_freshness(anchor)


def main() -> int:
    if not REGISTRY_PATH.exists():
        print(f"Registry not found: {REGISTRY_PATH}")
        return 1

    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    items: list[dict[str, Any]] = registry.get("content", [])
    if not items:
        print("No content items in registry")
        return 1

    freshness_report: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "total_items": len(items),
        "entries": [],
        "summary": {
            "fresh": 0,
            "stale": 0,
            "outdated": 0,
            "never": 0,
        },
    }

    for item in items:
        slug = item.get("slug", "unknown")
        title = item.get("title", slug)
        date_str = item.get("date_str") or item.get("last_verified")
        last_verified = parse_date(date_str)
        last_reviewed = parse_date(item.get("last_reviewed"))

        freshness = compute_freshness_with_review(last_verified, last_reviewed)

        freshness_report["entries"].append({
            "slug": slug,
            "title": title,
            "freshness": freshness,
            "last_verified": last_verified.isoformat() if last_verified else None,
            "last_reviewed": last_reviewed.isoformat() if last_reviewed else None,
        })
        freshness_report["summary"][freshness] += 1

    # Write to dist/
    DIST_PATH.parent.mkdir(parents=True, exist_ok=True)
    DIST_PATH.write_text(
        json.dumps(freshness_report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    # Write persistent copy to data/
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    DATA_PATH.write_text(
        json.dumps(freshness_report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    s = freshness_report["summary"]
    print(f"Freshness check complete: {len(items)} items")
    print(f"  🟢 Fresh (<30d):   {s['fresh']}")
    print(f"  🟡 Stale (30-90d): {s['stale']}")
    print(f"  🔴 Outdated (>90d): {s['outdated']}")
    print(f"  ⚪ Never verified:  {s['never']}")
    print(f"  Report: {DIST_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
