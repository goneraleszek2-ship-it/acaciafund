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

TIME_SENSITIVE_CATEGORIES = {"earnings-analysis", "industry-analysis", "market-analysis"}
VALID_TIERS = ("time_sensitive", "timeless")


def currency_tier(item: dict[str, Any]) -> str:
    """Classify an item as time_sensitive or timeless.

    An explicit stored `currency_tier` wins; otherwise research items in
    news-driven categories (earnings/industry/market analysis) are
    time_sensitive, everything else is timeless (evergreen).
    """
    explicit = item.get("currency_tier")
    if explicit in VALID_TIERS:
        return explicit
    if item.get("content_type") == "research" and (item.get("category") or "") in TIME_SENSITIVE_CATEGORIES:
        return "time_sensitive"
    return "timeless"


def compute_freshness(last_verified: date | None, today: date | None = None, tier: str = "timeless") -> str:
    """Compute freshness status based on last_verified date.

    Timeless (evergreen) items never degrade: verified at any point they
    are 'fresh'; unverified is 'never'. Time-sensitive items decay through
    the 30/90-day buckets.

    Returns one of: 'fresh', 'stale', 'outdated', 'never'.
    """
    if last_verified is None:
        return "never"
    if tier == "timeless":
        return "fresh"
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
    tier: str = "timeless",
) -> str:
    """Compute freshness using the most recent of last_verified/last_reviewed.

    A manual review (last_reviewed) signals an item is current, but a newer
    last_verified still wins when it is more recent.
    """
    anchor = last_reviewed if last_reviewed and (not last_verified or last_reviewed > last_verified) else last_verified
    return compute_freshness(anchor, today=today, tier=tier)


def verification_anchor(item: dict[str, Any], today: date | None = None, tier: str | None = None) -> str:
    """Freshness status for a registry item.

    Anchors on the most recent of `date_str` (publication) and
    `last_verified` (explicit verification), then defers to a newer
    `last_reviewed`. Tier-aware: timeless items never decay past fresh.
    """
    if tier is None:
        tier = currency_tier(item)
    published = parse_date(item.get("date_str"))
    verified = parse_date(item.get("last_verified"))
    anchor = verified if verified and (not published or verified > published) else published
    return compute_freshness_with_review(anchor, parse_date(item.get("last_reviewed")), today=today, tier=tier)


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
        "tiers": {"time_sensitive": {s: 0 for s in VALID_STATUSES}, "timeless": {s: 0 for s in VALID_STATUSES}},
    }
    for item in items:
        slug = item.get("slug", "unknown")
        title = item.get("title", slug)
        tier = currency_tier(item)
        last_verified = parse_date(item.get("date_str")) or parse_date(item.get("last_verified"))
        last_reviewed = parse_date(item.get("last_reviewed"))
        freshness = verification_anchor(item, today=today, tier=tier)
        report["entries"].append({
            "slug": slug,
            "title": title,
            "currency_tier": tier,
            "freshness": freshness,
            "last_verified": last_verified.isoformat() if last_verified else None,
            "last_reviewed": last_reviewed.isoformat() if last_reviewed else None,
        })
        report["summary"][freshness] += 1
        report["tiers"][tier][freshness] += 1
    return report


def build_topic_report(items: list[dict[str, Any]], today: date | None = None) -> dict[str, Any]:
    """Aggregate freshness of time-sensitive items by category (topic).

    A topic is:
      - 'cold'   when it has >= 1 outdated or >= 2 stale time-sensitive items
      - 'cooling' when it has >= 1 stale time-sensitive item
      - 'current' otherwise

    Timeless items never make a topic cold (evergreen content ages fine).
    """
    by_topic: dict[str, dict[str, Any]] = {}
    for item in items:
        tier = currency_tier(item)
        status = verification_anchor(item, today=today, tier=tier)
        topic = (item.get("category") or item.get("knowledge_category") or "uncategorized")
        bucket = by_topic.setdefault(topic, {
            "category": topic,
            "total": 0,
            "time_sensitive": 0,
            "timeless": 0,
            "fresh": 0, "stale": 0, "outdated": 0, "never": 0,
            "oldest_slug": None,
            "oldest_date": None,
        })
        bucket["total"] += 1
        bucket[tier] += 1
        bucket[status] += 1
        if tier == "time_sensitive":
            anchor = parse_date(item.get("date_str")) or parse_date(item.get("last_verified"))
            if anchor and (bucket["oldest_date"] is None or anchor < bucket["oldest_date"]):
                bucket["oldest_date"] = anchor
                bucket["oldest_slug"] = item.get("slug")

    topics: list[dict[str, Any]] = []
    for bucket in by_topic.values():
        if bucket["time_sensitive"] and (bucket["outdated"] >= 1 or bucket["stale"] >= 2):
            bucket["status"] = "cold"
        elif bucket["time_sensitive"] and bucket["stale"] >= 1:
            bucket["status"] = "cooling"
        else:
            bucket["status"] = "current"
        bucket.pop("oldest_date", None)
        topics.append(bucket)

    return {
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "total_topics": len(topics),
        "cold_topics": [t for t in topics if t["status"] == "cold"],
        "cooling_topics": [t for t in topics if t["status"] == "cooling"],
        "topics": sorted(topics, key=lambda t: (t["status"] != "current", t["category"])),
    }


def topic_status_summary(topic_report: dict[str, Any]) -> str:
    """Short human-readable summary line for a topic report."""
    cold = len(topic_report["cold_topics"])
    cooling = len(topic_report["cooling_topics"])
    return f"{len(topic_report['topics'])} topics: {cold} cold, {cooling} cooling"


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
    t = report["tiers"]
    print(f"Freshness check complete: {len(items)} items")
    print(f"  🟢 Fresh (<30d):   {s['fresh']}")
    print(f"  🟡 Stale (30-90d): {s['stale']}")
    print(f"  🔴 Outdated (>90d): {s['outdated']}")
    print(f"  ⚪ Never verified:  {s['never']}")
    print(f"  time_sensitive: {t['time_sensitive']}")
    print(f"  timeless:       {t['timeless']}")
    print(f"  Report: {DIST_PATH}")
    return 0


def run_topics(fail_on_cold: int, today: date | None = None) -> int:
    """Aggregate time-sensitive freshness by topic; write dist/topic-currency.json."""
    registry = load_registry()
    items: list[dict[str, Any]] = registry.get("content", [])
    report = build_topic_report(items, today=today)
    DIST_PATH.parent.mkdir(parents=True, exist_ok=True)
    TOPIC_PATH = REPOSITORY_ROOT / "dist" / "topic-currency.json"
    TOPIC_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    summary = topic_status_summary(report)
    print(f"Topic currency: {summary}")
    for topic in report["cold_topics"]:
        print(f"  ❄️ COLD {topic['category']}: {topic['outdated']} outdated, {topic['stale']} stale "
              f"(oldest: {topic['oldest_slug']})")
    for topic in report["cooling_topics"]:
        print(f"  🌬️ cooling {topic['category']}: {topic['stale']} stale")
    print(f"  Report: {TOPIC_PATH}")
    if len(report["cold_topics"]) > fail_on_cold:
        print(f"FAIL: {len(report['cold_topics'])} cold topic(s) exceed fail-on-cold={fail_on_cold}")
        return 1
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

    topics = sub.add_parser("topics", help="aggregate time-sensitive freshness by topic (dist/topic-currency.json)")
    topics.add_argument("--fail-on-cold", type=int, default=0, help="exit 1 when more cold topics than this (default 0)")

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
    if args.command == "topics":
        return run_topics(args.fail_on_cold)
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
