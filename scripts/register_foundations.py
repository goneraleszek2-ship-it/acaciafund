#!/usr/bin/env python3
"""Index foundational knowledge assets into the primary registry.

Reads registry.json and appends any new foundational nodes (manifesto,
AML core, market core, data core) that do not already exist by slug.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REGISTRY_PATH = ROOT / "registry.json"
FOUNDATIONS_PATH = ROOT / "content"

FOUNDATIONAL_NODES = [
    {
        "slug": "cybernetic-manifesto",
        "title": "The Cybernetic Manifest",
        "pillar": "system",
    },
    {
        "slug": "aml-core-foundations",
        "title": "Foundations of Financial Intelligence and Network Topology",
        "pillar": "aml",
    },
    {
        "slug": "market-core-foundations",
        "title": "Limit Order Book Physics and Systemic Risk Mechanics",
        "pillar": "market",
    },
    {
        "slug": "data-core-foundations",
        "title": "Declarative DataOps and Schema Governance Architectures",
        "pillar": "data",
    },
]


def load_content_html(foundations_path: Path, slug: str) -> str:
    """Load the Markdown content file and convert to basic HTML paragraphs
    for the registry's body_html field. Returns empty string on failure."""
    mapping = {
        "cybernetic-manifesto": "manifesto.md",
        "aml-core-foundations": "aml/core-foundations.md",
        "market-core-foundations": "market/core-foundations.md",
        "data-core-foundations": "data/core-foundations.md",
    }
    rel = mapping.get(slug)
    if rel is None:
        return ""
    path = foundations_path / rel
    if not path.exists():
        return ""
    raw = path.read_text(encoding="utf-8")
    # Strip frontmatter
    import re
    match = re.match(r"^---\s*\n.*?\n---\s*\n(.*)", raw, re.DOTALL)
    body = match.group(1).strip() if match else raw.strip()
    # Strip leading # heading lines for description
    lines = body.splitlines()
    return body


def main() -> None:
    now = datetime.now(timezone.utc)
    today = now.strftime("%Y-%m-%d")
    today_iso = now.isoformat()

    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        registry = json.load(f)

    content_list = registry.get("content", [])
    existing_slugs = {item["slug"] for item in content_list}
    added = 0

    for node in FOUNDATIONAL_NODES:
        slug = node["slug"]
        if slug in existing_slugs:
            print(f"  Skipped {slug} (already in registry)")
            continue

        body = load_content_html(FOUNDATIONS_PATH, slug)
        lines = body.splitlines()
        first_line = next((l for l in lines if l.strip() and not l.startswith("#")), node["title"])
        desc = first_line[:200]

        entry = {
            "slug": slug,
            "title": node["title"],
            "description": desc,
            "body_html": f"<pre>{body}</pre>",
            "category": "knowledge",
            "content_type": "knowledge",
            "tags": [node["pillar"], "foundations", "core-architecture"],
            "pillar": node["pillar"],
            "author": "AcaciaFund",
            "date_str": today,
            "sqi": 1.0,
            "language": "en",
            "created_at": today_iso,
            "updated_at": today_iso,
            "deprecated": False,
            "enriched": True,
            "enriched_at": today,
        }
        content_list.append(entry)
        existing_slugs.add(slug)
        added += 1
        print(f"  Registered {slug} ({node['title']})")

    registry["content"] = content_list
    registry["last_updated"] = today

    from core.registry_io import save_registry as _atomic_save
    _atomic_save(registry, REGISTRY_PATH)

    print(f"\nDone — {added} new foundational nodes integrated into {REGISTRY_PATH.name}.")
    if added > 0:
        print("Run `python build.py` to rebuild the site with the new assets.")


if __name__ == "__main__":
    main()
