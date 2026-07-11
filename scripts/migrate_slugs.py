#!/usr/bin/env python3
"""Migrate registry.json slugs to pillar-first URL structure.

New format:
  research: {pillar_url}/research/{topic-slug}
  learn:    {pillar_url}/learn/{topic-slug}
  knowledge (platform): knowledge/{page-slug}  (unchanged)
  knowledge (domain):   {pillar_url}/knowledge/{topic-slug}

Usage:
    python3 scripts/migrate_slugs.py              # Preview migration
    python3 scripts/migrate_slugs.py --verbose     # Preview with per-item output
    python3 scripts/migrate_slugs.py --apply       # Apply migration
    python3 scripts/migrate_slugs.py --rollback    # Restore from backup
    python3 scripts/migrate_slugs.py --check       # Validate registry without writing
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

REGISTRY_PATH = ROOT / "registry.json"
BACKUP_DIR = ROOT / ".registry-archive"
REDIRECTS_PATH = ROOT / "redirects.json"

# Pillar URL mapping: internal key → URL segment
from config import PILLAR_URL_MAP

# Platform knowledge pages that stay under /knowledge/ (no pillar prefix)
PLATFORM_KNOWLEDGE_PAGES = {
    "about", "contact", "changelog", "faq", "glossary",
    "research-methodology", "pillar-taxonomy", "system-architecture",
    "diagrams", "dataops-trends-2026", "dataops-glossary",
    "open-source-tools", "cybernetic-foundations",
}


def _slugify(text: str, max_len: int = 60) -> str:
    """Convert text to URL-safe slug."""
    s = text.lower()
    s = s.replace("'", "").replace('"', "")
    s = re.sub(r"[^a-z0-9-]+", "-", s).strip("-")
    s = re.sub(r"-{2,}", "-", s)
    return s[:max_len].rstrip("-")


def migrate_slug(item: dict) -> tuple[str, str]:
    """Compute new slug for a registry item. Returns (old_slug, new_slug)."""
    old_slug = item.get("slug", "")
    pillar = item.get("pillar", "")
    content_type = item.get("content_type", "")

    if not old_slug or not pillar:
        return old_slug, old_slug

    pillar_url = PILLAR_URL_MAP.get(pillar, pillar)

    if content_type == "knowledge":
        # Platform pages stay at knowledge/{page}
        slug_without_prefix = old_slug
        if old_slug.startswith("knowledge/"):
            slug_without_prefix = old_slug[10:]

        if slug_without_prefix in PLATFORM_KNOWLEDGE_PAGES:
            # Platform page — keep at /knowledge/{page}
            new_slug = f"knowledge/{slug_without_prefix}"
        elif old_slug.startswith("knowledge/"):
            # Already has knowledge/ prefix, extract topic
            topic = slug_without_prefix
            new_slug = f"{pillar_url}/knowledge/{topic}"
        elif "/" not in old_slug:
            # Flat slug (e.g. "aml-core-foundations") → pillar/knowledge/topic
            # Extract the topic part (strip pillar prefix if present)
            topic = old_slug
            for prefix in [f"{pillar}-", "aml-", "market-", "data-", "stock-"]:
                if topic.startswith(prefix):
                    topic = topic[len(prefix):]
                    break
            new_slug = f"{pillar_url}/knowledge/{topic}"
        else:
            # Some other format, wrap with pillar
            new_slug = f"{pillar_url}/knowledge/{old_slug.split('/')[-1]}"

    elif content_type == "learn":
        if old_slug.startswith("learn/"):
            # learn/aml/topic or learn/topic
            parts = old_slug[6:].split("/", 1)
            if len(parts) == 2:
                # learn/{pillar}/{topic} → {pillar_url}/learn/{topic}
                new_slug = f"{pillar_url}/learn/{parts[1]}"
            else:
                # learn/{topic} → {pillar_url}/learn/{topic}
                new_slug = f"{pillar_url}/learn/{parts[0]}"
        elif old_slug.startswith("lesson/"):
            # lesson/{topic} → {pillar_url}/learn/{topic}
            topic = old_slug[7:]
            new_slug = f"{pillar_url}/learn/{topic}"
        else:
            # Flat slug → {pillar_url}/learn/{slug}
            new_slug = f"{pillar_url}/learn/{old_slug}"

    elif content_type == "research":
        if old_slug.startswith("blog/"):
            # blog/YYYY-MM-DD-topic → {pillar_url}/research/{topic}
            blog_part = old_slug[5:]  # strip "blog/"
            # Try to strip date prefix
            date_match = re.match(r"(\d{4}-\d{2}-\d{2})[-_](.+)", blog_part)
            if date_match:
                topic = date_match.group(2)
            else:
                topic = blog_part
            new_slug = f"{pillar_url}/research/{topic}"
        else:
            # Flat or other format → {pillar_url}/research/{slug}
            new_slug = f"{pillar_url}/research/{old_slug}"
    else:
        new_slug = old_slug

    return old_slug, new_slug


def validate_no_collisions(migrations: list[tuple[str, str]]) -> list[str]:
    """Check for slug collisions after migration."""
    errors = []
    seen = {}
    for old_slug, new_slug in migrations:
        if new_slug in seen:
            errors.append(
                f"COLLISION: '{new_slug}' generated from both "
                f"'{seen[new_slug]}' and '{old_slug}'"
            )
        seen[new_slug] = old_slug
    return errors


def _ts() -> str:
    """Current timestamp for log lines."""
    return datetime.now(timezone.utc).strftime("%H:%M:%S")


def main():
    parser = argparse.ArgumentParser(description="Migrate slugs to pillar-first structure")
    parser.add_argument("--apply", action="store_true", help="Apply migration (default: preview)")
    parser.add_argument("--rollback", action="store_true", help="Restore from backup")
    parser.add_argument("--check", action="store_true", help="Validate registry without writing")
    parser.add_argument("--verbose", action="store_true", help="Show per-item slug changes")
    args = parser.parse_args()

    # Load registry
    print(f"[{_ts()}] Loading registry...")
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        registry = json.load(f)

    items = registry.get("content", [])
    print(f"[{_ts()}] Registry: {len(items)} items")

    # Warn about existing compliance/ slugs (from prior migration)
    compliance_slugs = [i.get("slug", "") for i in items if i.get("slug", "").startswith("compliance/")]
    if compliance_slugs:
        print(f"[{_ts()}] Note: {len(compliance_slugs)} items already have compliance/ prefix")

    # Compute migrations
    migrations = []
    for item in items:
        old_slug, new_slug = migrate_slug(item)
        migrations.append((old_slug, new_slug))

    # Resolve collisions by appending numeric suffix
    slug_counts: dict[str, int] = {}
    resolved = []
    collisions_resolved = 0
    for old_slug, new_slug in migrations:
        if new_slug in slug_counts:
            slug_counts[new_slug] += 1
            new_slug = f"{new_slug}-{slug_counts[new_slug]}"
            collisions_resolved += 1
        else:
            slug_counts[new_slug] = 0
        resolved.append((old_slug, new_slug))
    migrations = resolved

    if collisions_resolved:
        print(f"[{_ts()}] Collisions resolved: {collisions_resolved}")

    # Show summary
    changed = [(o, n) for o, n in migrations if o != n]
    unchanged = len(migrations) - len(changed)
    print(f"\n[{_ts()}] Migration summary:")
    print(f"  Total items:     {len(migrations)}")
    print(f"  Slugs to change: {len(changed)}")
    print(f"  Slugs unchanged: {unchanged}")

    # Group by content type and pillar
    by_type: dict[str, list] = {}
    by_pillar: dict[str, int] = {}
    for item, (old_slug, new_slug) in zip(items, migrations):
        ct = item.get("content_type", "unknown")
        pillar = item.get("pillar", "none")
        if old_slug != new_slug:
            by_type.setdefault(ct, []).append((old_slug, new_slug))
            by_pillar[pillar] = by_pillar.get(pillar, 0) + 1

    for ct, pairs in sorted(by_type.items()):
        print(f"\n  {ct} ({len(pairs)} items):")
        show = pairs if args.verbose else pairs[:5]
        for old, new in show:
            print(f"    {old}")
            print(f"      → {new}")
        if not args.verbose and len(pairs) > 5:
            print(f"    ... and {len(pairs) - 5} more")

    if by_pillar:
        print(f"\n  By pillar:")
        for pillar, count in sorted(by_pillar.items()):
            url = PILLAR_URL_MAP.get(pillar, pillar)
            print(f"    {pillar} → {url}: {count} items")

    # Validate no collisions
    errors = validate_no_collisions(migrations)
    if errors:
        print(f"\n[{_ts()}] ❌ COLLISION ERRORS ({len(errors)}):")
        for e in errors:
            print(f"  {e}")
        sys.exit(1)

    if args.check:
        print(f"\n[{_ts()}] Check complete — no errors found.")
        return

    if args.rollback:
        # Find latest backup
        backups = sorted(BACKUP_DIR.glob("registry-*.json"), reverse=True)
        if not backups:
            print(f"[{_ts()}] No backups found in .registry-archive/")
            sys.exit(1)
        latest = backups[0]
        print(f"\n[{_ts()}] Restoring from: {latest.name}")
        shutil.copy2(latest, REGISTRY_PATH)
        print(f"[{_ts()}] ✅ Registry restored")
        return

    if not args.apply:
        print(f"\n[{_ts()}] Dry run — no changes made. Use --apply to apply.")
        return

    # Create backup
    BACKUP_DIR.mkdir(exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    backup_path = BACKUP_DIR / f"registry-{ts}.json"
    shutil.copy2(REGISTRY_PATH, backup_path)
    print(f"\n[{_ts()}] Backup: {backup_path}")

    # Apply migrations
    for item, (old_slug, new_slug) in zip(items, migrations):
        if old_slug != new_slug:
            item["slug"] = new_slug

    # Save updated registry
    with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)

    # Save redirect mapping
    redirect_map = {
        old: new for old, new in migrations if old != new
    }
    with open(REDIRECTS_PATH, "w", encoding="utf-8") as f:
        json.dump(redirect_map, f, indent=2)

    print(f"[{_ts()}] ✅ Registry updated: {len(changed)} slugs migrated")
    print(f"[{_ts()}] ✅ Redirects saved: {REDIRECTS_PATH}")


if __name__ == "__main__":
    main()
