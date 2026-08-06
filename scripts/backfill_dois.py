"""Backfill DOIs for existing registry items with derivable provenance.

Current scope (deterministic, no network):
- arXiv items with an arxiv.org source URL get their canonical DOI
  (10.48550/arXiv.<id>); arXiv assigns a DOI to every paper.
- Items already carrying a doi are left untouched.

Run: python3 scripts/backfill_dois.py [--dry-run]

Registry is backed up to registry.pre-doi-backfill.json on apply.
"""

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
REGISTRY_PATH = REPO_ROOT / "registry.json"

ARXIV_ID_RE = re.compile(r"arxiv\.org/(?:abs|pdf)/([^/?#]+)")


def derive_doi_for_item(item: dict) -> str | None:
    """Return a DOI derivable from the item's stored fields, or None."""
    if item.get("doi"):
        return None
    source_url = item.get("source_url") or ""
    match = ARXIV_ID_RE.search(source_url)
    if match:
        arxiv_id = match.group(1).split("v")[0]
        return f"10.48550/arXiv.{arxiv_id}"
    return None


def backfill(items: list[dict], dry_run: bool = True) -> int:
    updated = 0
    for item in items:
        doi = derive_doi_for_item(item)
        if doi:
            updated += 1
            if dry_run:
                print(f"  would set {item.get('slug')}: {doi}")
            else:
                item["doi"] = doi
                print(f"  {item.get('slug')}: {doi}")
    return updated


def main() -> int:
    dry_run = "--dry-run" in sys.argv or "--dry" in sys.argv
    if not REGISTRY_PATH.exists():
        print(f"ERROR: {REGISTRY_PATH} not found")
        return 1
    with open(REGISTRY_PATH, encoding="utf-8") as f:
        registry = json.load(f)
    items = registry.get("content", [])
    updated = backfill(items, dry_run=dry_run)
    print(f"{'[dry-run] ' if dry_run else ''}DOI backfill: {updated} of {len(items)} items")
    if updated and not dry_run:
        backup = REPO_ROOT / "registry.pre-doi-backfill.json"
        backup.write_text(json.dumps(registry, indent=2), encoding="utf-8")
        with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
            json.dump(registry, f, indent=2)
        print(f"Registry written; backup at {backup}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
