#!/usr/bin/env python3
"""Generate or update current week's weekly notes entry.

Reads existing weekly_notes.json, creates/updates current ISO week entry
with placeholder data from recent registry items and source freshness changes.
For automated weekly runs — produces skeleton for manual refinement.

Usage:
    python3 scripts/generate_weekly_notes.py
    python3 scripts/generate_weekly_notes.py --force  # overwrite existing
"""
from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from core.urls import canonical_path, slug_to_fspath

PROJECT_ROOT = Path(__file__).parent.parent
WEEKLY_NOTES_PATH = PROJECT_ROOT / "data" / "weekly_notes.json"
REGISTRY_PATH = PROJECT_ROOT / "registry.json"
SOURCE_HEALTH_PATH = PROJECT_ROOT / "data" / "source_health.json"


def canonical_url_for_slug(slug: str) -> str:
    """Translate a registry slug to its canonical URL path (e.g. 'aml/learn/x' → '/compliance/learn/x/')."""
    return "/" + canonical_path(slug_to_fspath(slug)).strip("/") + "/"


def iso_week_range(year: int, week: int) -> tuple[date, date]:
    """Return (monday, sunday) for an ISO week."""
    jan4 = date(year, 1, 4)
    start = jan4 - timedelta(days=jan4.isoweekday() - 1) + timedelta(weeks=week - 1)
    return start, start + timedelta(days=6)


def current_iso_week() -> tuple[int, int]:
    """Return (year, week_number) for today."""
    today = date.today()
    return today.isocalendar()[:2]


def week_id(year: int, week: int) -> str:
    return f"{year}-W{week:02d}"


def get_pillar_for_slug(slug: str) -> str:
    """Map registry slug to pillar key."""
    pillar_map = {"aml/": "aml", "compliance/": "aml", "markets/": "markets", "stock/": "markets", "data/": "data-engineering", "data-engineering": "data-engineering"}
    for prefix, pillar in pillar_map.items():
        if slug.startswith(prefix):
            return pillar
    return "unknown"


def gather_recent_registry_items(days_back: int = 7) -> dict[str, list[dict]]:
    """Gather registry items from last N days, grouped by pillar."""
    from datetime import timezone as tz
    cutoff = datetime.now(tz.utc) - timedelta(days=days_back)
    items_by_pillar: dict[str, list[dict]] = {"aml": [], "markets": [], "data-engineering": []}
    try:
        with open(REGISTRY_PATH, encoding="utf-8") as f:
            registry = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return items_by_pillar
    for item in registry.get("content", []):
        created = item.get("created_at", "")
        updated = item.get("updated_at", "")
        try:
            dt = datetime.fromisoformat(updated or created)
        except (ValueError, TypeError):
            continue
        if dt >= cutoff:
            pillar = get_pillar_for_slug(item.get("slug", ""))
            if pillar in items_by_pillar:
                items_by_pillar[pillar].append({
                    "title": item.get("title", ""),
                    "slug": item.get("slug", ""),
                    "pillar": item.get("pillar", pillar),
                    "description": item.get("description", ""),
                    "date": item.get("date_str", "")[:10],
                })
    return items_by_pillar


def gather_source_freshness_changes() -> list[dict]:
    """Gather source freshness changes (degraded → error, etc.)."""
    try:
        with open(SOURCE_HEALTH_PATH, encoding="utf-8") as f:
            health = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []
    changes = []
    for src in health.get("sources", []):
        status = src.get("status", "unknown")
        if status in ("error", "degraded"):
            changes.append({
                "name": src.get("name", "Unknown"),
                "status": status,
                "response_time_ms": src.get("response_time_ms", 0),
                "url": src.get("url", ""),
            })
    return changes


def make_placeholder_events(recent_items: list[dict]) -> list[dict]:
    """Create placeholder event dicts from recent registry items."""
    events = []
    for item in recent_items[:5]:
        title = item.get("title", "")
        desc = item.get("description", "")[:200]
        events.append({
            "date": item.get("date", ""),
            "title": title,
            "feynman": f"PLACEHOLDER: {desc}",
            "analogy": "PLACEHOLDER: Add Feynman analogy here.",
            "why_it_matters": "PLACEHOLDER: Add significance here.",
            "links": [{"label": title[:60], "url": canonical_url_for_slug(item.get("slug", ""))}],
        })
    return events


def make_vibe(statuses: list[str]) -> str:
    """Derive vibe emoji from events."""
    if not statuses:
        return "🔄 Quiet week"
    keywords = {"crisis": "📉", "reform": "🏛️", "launch": "⚡", "breakthrough": "⚡⚡", "landmark": "⚡⚡⚡", "warning": "⚠️"}
    for kw, vibe in keywords.items():
        if any(kw in s.lower() for s in statuses):
            return vibe
    return "🔄" if len(statuses) < 2 else "📈"


def generate_current_week(force: bool = False) -> bool:
    """Generate or update current week entry. Returns True if changed."""
    year, wn = current_iso_week()
    wid = week_id(year, wn)
    mon, sun = iso_week_range(year, wn)
    date_range = f"{mon.strftime('%b %-d')} – {sun.strftime('%b %-d')}"

    try:
        with open(WEEKLY_NOTES_PATH, encoding="utf-8") as f:
            data: dict[str, Any] = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = {"weeks": []}

    existing_idx = next((i for i, w in enumerate(data["weeks"]) if w["week_id"] == wid), None)
    if existing_idx is not None and not force:
        return False

    recent = gather_recent_registry_items()

    pillars = {}
    for p_key, p_label in [("aml", "Compliance"), ("markets", "Markets"), ("data-engineering", "Data Engineering")]:
        items = recent.get(p_key, [])
        events = make_placeholder_events(items)
        vibes = [e.get("title", "") for e in events]
        vibe = make_vibe(vibes)
        takeaway = f"PLACEHOLDER: Feynman takeaway for {p_label} week {wid}."
        pillars[p_key] = {"vibe": vibe, "feynman_takeaway": takeaway, "events": events}

    new_week = {"week_id": wid, "date_range": date_range, "pillars": pillars}

    if existing_idx is not None:
        data["weeks"][existing_idx] = new_week
    else:
        data["weeks"].append(new_week)

    with open(WEEKLY_NOTES_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate weekly notes")
    parser.add_argument("--force", action="store_true", help="Overwrite existing current week")
    args = parser.parse_args()
    changed = generate_current_week(args.force)
    if changed:
        print("Weekly notes updated for current week.")
    else:
        print("Weekly notes: current week already exists (use --force to overwrite).")
