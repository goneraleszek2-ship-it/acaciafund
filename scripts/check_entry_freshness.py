#!/usr/bin/env python3
"""Entry Freshness Checker — walks registry items and computes freshness status.

Outputs `freshness.json` to dist/ and `entry_freshness.json` to data/.

Usage:
    python3 scripts/check_entry_freshness.py                     # report (default)
    python3 scripts/check_entry_freshness.py report
    python3 scripts/check_entry_freshness.py triage [--group pillar|type|category] [--status never stale outdated fresh]
    python3 scripts/check_entry_freshness.py mark-verified SLUG [SLUG ...]
    python3 scripts/check_entry_freshness.py mark-reviewed SLUG [SLUG ...]
    python3 scripts/check_entry_freshness.py mark-reviewed --status stale        # batch
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
REGISTRY_PATH = REPOSITORY_ROOT / "registry.json"
DATA_PATH = REPOSITORY_ROOT / "data" / "entry_freshness.json"
DIST_PATH = REPOSITORY_ROOT / "dist" / "freshness.json"

VALID_STATUSES = ("fresh", "stale", "outdated", "never")
GROUP_KEYS = ("pillar", "type", "category")


def compute_freshness(last_verified: date | None, today: date | None = None) -> str:
    """Compute freshness status based on last_verified date.

    Returns one of: 'fresh', 'stale', 'outdated', 'never'.
    """
    if last_verified is None:
        return "never"
    days = ((today or date.today()) - last_verified).days
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
    last_verified: date | None,
    last_reviewed: date | None,
    today: date | None = None,
) -> str:
    """Compute freshness using the most recent of last_verified/last_reviewed.

    A manual review (last_reviewed) signals an item is current, but a newer
    last_verified still wins when it is more recent.
    """
    anchor = last_reviewed if last_reviewed and (not last_verified or last_reviewed > last_verified) else last_verified
    return compute_freshness(anchor, today=today)


def verification_anchor(item: dict[str, Any], today: date | None = None) -> str:
    """Freshness status for a registry item.

    Anchors on the most recent of `date_str` (publication) and
    `last_verified` (explicit verification), then defers to a newer
    `last_reviewed`.
    """
    published = parse_date(item.get("date_str"))
    verified = parse_date(item.get("last_verified"))
    anchor = verified if verified and (not published or verified > published) else published
    return compute_freshness_with_review(anchor, parse_date(item.get("last_reviewed")), today=today)


def load_registry(path: Path | None = None) -> dict[str, Any]:
    """Load the registry JSON."""
    return json.loads((path or REGISTRY_PATH).read_text(encoding="utf-8"))


def save_registry(registry: dict[str, Any], path: Path | None = None) -> None:
    """Persist the registry JSON back to disk."""
    registry["last_updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    (path or REGISTRY_PATH).write_text(json.dumps(registry, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def build_freshness_report(items: list[dict[str, Any]], today: date | None = None) -> dict[str, Any]:
    """Build the freshness report structure for a list of registry items."""
    report: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "total_items": len(items),
        "entries": [],
        "summary": {s: 0 for s in VALID_STATUSES},
    }
    for item in items:
        slug = item.get("slug", "unknown")
        title = item.get("title", slug)
        last_verified = parse_date(item.get("date_str")) or parse_date(item.get("last_verified"))
        last_reviewed = parse_date(item.get("last_reviewed"))
        freshness = verification_anchor(item, today=today)
        report["entries"].append({
            "slug": slug,
            "title": title,
            "freshness": freshness,
            "last_verified": last_verified.isoformat() if last_verified else None,
            "last_reviewed": last_reviewed.isoformat() if last_reviewed else None,
        })
        report["summary"][freshness] += 1
    return report


def select_by_status(items: list[dict[str, Any]], statuses: list[str], today: date | None = None) -> list[dict[str, Any]]:
    """Return items whose current freshness is in `statuses`."""
    wanted = set(statuses)
    return [i for i in items if verification_anchor(i, today=today) in wanted]


def mark_items(
    items: list[dict[str, Any]],
    slugs: list[str],
    field: str,
    today: date | None = None,
) -> list[dict[str, Any]]:
    """Set `last_verified`/`last_reviewed` to today for the given slugs.

    Returns the list of marked items. Slugs not found in the registry are
    reported by the caller; this function only mutates matches.
    """
    stamp = (today or date.today()).isoformat()
    marked: list[dict[str, Any]] = []
    for item in items:
        if item.get("slug") in slugs:
            item[field] = stamp
            marked.append(item)
    return marked


def run_report(today: date | None = None) -> int:
    """Compute and write the freshness report (dist/ + data/)."""
    registry = load_registry()
    items: list[dict[str, Any]] = registry.get("content", [])
    report = build_freshness_report(items, today=today)
    for path in (DIST_PATH, DATA_PATH):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    s = report["summary"]
    print(f"Freshness check complete: {len(items)} items")
    print(f"  🟢 Fresh (<30d):   {s['fresh']}")
    print(f"  🟡 Stale (30-90d): {s['stale']}")
    print(f"  🔴 Outdated (>90d): {s['outdated']}")
    print(f"  ⚪ Never verified:  {s['never']}")
    print(f"  Report: {DIST_PATH}")
    return 0


def run_triage(group_by: str | None, statuses: list[str], today: date | None = None) -> int:
    """Print a prioritized list of items grouped by the requested key."""
    registry = load_registry()
    items = select_by_status(registry.get("content", []), statuses, today=today)
    print(f"Triage: {len(items)} items in status(es) {', '.join(statuses)}")
    if group_by:
        from collections import defaultdict

        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for item in items:
            key: str = ""
            if group_by == "pillar":
                key = item.get("pillar") or "unknown"
            elif group_by == "type":
                key = item.get("content_type") or "unknown"
            elif group_by == "category":
                key = item.get("knowledge_category") or item.get("category") or "unknown"
            grouped[key].append(item)
        for key in sorted(grouped):
            grp = grouped[key]
            print(f"\n  {key} ({len(grp)}):")
            for item in sorted(grp, key=lambda i: (i.get("date_str") or "9999"))[:40]:
                flag = verification_anchor(item, today=today)
                print(f"    [{flag}] {item.get('slug')} — {item.get('title', '')[:60]}")
    else:
        for item in sorted(items, key=lambda i: i.get("date_str") or "9999"):
            flag = verification_anchor(item, today=today)
            print(f"  [{flag}] {item.get('slug')} — {item.get('title', '')[:60]}")
    return 0


def run_mark(field: str, slugs: list[str], statuses: list[str], today: date | None = None) -> int:
    """Set `last_verified` or `last_reviewed` to today on registry items."""
    registry = load_registry()
    items: list[dict[str, Any]] = registry.get("content", [])
    if statuses:
        slugs = [i.get("slug", "") for i in select_by_status(items, statuses, today=today)]
        print(f"  Selecting {len(slugs)} item(s) matching status(es): {', '.join(statuses)}")
    marked = mark_items(items, slugs, field, today=today)
    if not marked:
        print(f"No items marked (checked {len(items)} items, {len(slugs)} slug(s) requested)")
        return 1
    save_registry(registry)
    print(f"Marked {field} = {date.today().isoformat()} on {len(marked)} item(s):")
    for item in marked:
        print(f"  {item.get('slug')} — {item.get('title', '')[:60]}")
    return 0


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. No args = report mode (backward compatible)."""
    parser = argparse.ArgumentParser(description="AcaciaFund entry freshness checker")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("report", help="compute and write freshness report (default)")

    triage = sub.add_parser("triage", help="list items needing attention")
    triage.add_argument("--group", choices=GROUP_KEYS, default=None, help="group output by pillar/type/category")
    triage.add_argument(
        "--status", nargs="+", choices=VALID_STATUSES, default=["never", "stale", "outdated"],
        help="filter by freshness status (default: all but fresh)",
    )

    for name, field in (("mark-verified", "last_verified"), ("mark-reviewed", "last_reviewed")):
        mark = sub.add_parser(name, help=f"set {field} to today on registry items")
        mark.add_argument("slugs", nargs="*", help="registry slugs to mark")
        if name == "mark-reviewed":
            mark.add_argument(
                "--status", nargs="+", choices=VALID_STATUSES, default=[],
                help="batch-mark all items currently in these statuses (alternative to explicit slugs)",
            )
        mark.set_defaults(_field=field)

    args = parser.parse_args(argv)

    if not REGISTRY_PATH.exists():
        print(f"Registry not found: {REGISTRY_PATH}")
        return 1

    if args.command in (None, "report"):
        return run_report()
    if args.command == "triage":
        return run_triage(args.group, args.status)
    if args.command in ("mark-verified", "mark-reviewed"):
        if args.command == "mark-verified" and args.status:
            print("mark-verified requires explicit slugs (verification must be per-item); use mark-reviewed --status for batch sweeps")
            return 2
        if not args.slugs and not args.status:
            print(f"{args.command} requires at least one slug (or --status for mark-reviewed)")
            return 2
        return run_mark(args._field, args.slugs, args.status)
    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
