#!/usr/bin/env python3
"""Index hyper-specialized deep-domain modules into the primary registry.

Reads registry.json and appends any new specialist nodes (temporal-graph-aml,
hawkes-microstructure, zero-copy-arrow-iceberg) that do not already exist
by slug. Loads full body content from the generated Markdown files.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REGISTRY_PATH = ROOT / "registry.json"
CONTENT_PATH = ROOT / "content"

SPECIALIST_NODES = [
    {
        "slug": "temporal-graph-aml",
        "title": "Temporal Graph Networks and Multi-Hop Link Prediction for Layering Detection",
        "pillar": "aml",
        "file": "aml/temporal-graph-aml.md",
    },
    {
        "slug": "hawkes-microstructure",
        "title": "Stochastic Point Processes and Hawkes Self-Exciting Intensity Functions in LOB Dynamics",
        "pillar": "market",
        "file": "market/hawkes-microstructure.md",
    },
    {
        "slug": "zero-copy-arrow-iceberg",
        "title": "Zero-Copy Vectorized Analytics via Apache Arrow Flight and Parquet Columnar Pruning",
        "pillar": "data",
        "file": "data/zero-copy-arrow-iceberg.md",
    },
]


def load_body_html(content_path: Path, rel_path: str) -> str:
    """Read Markdown file, strip frontmatter, return body text."""
    path = content_path / rel_path
    if not path.exists():
        return ""
    raw = path.read_text(encoding="utf-8")
    match = re.match(r"^---\s*\n.*?\n---\s*\n(.*)", raw, re.DOTALL)
    return match.group(1).strip() if match else raw.strip()


def main() -> None:
    now = datetime.now(timezone.utc)
    today = now.strftime("%Y-%m-%d")
    today_iso = now.isoformat()

    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        registry = json.load(f)

    content_list = registry.get("content", [])
    existing_slugs = {item["slug"] for item in content_list}
    added = 0

    for node in SPECIALIST_NODES:
        slug = node["slug"]
        if slug in existing_slugs:
            print(f"  Skipped {slug} (already in registry)")
            continue

        body = load_body_html(CONTENT_PATH, node["file"])
        lines = body.splitlines()
        first_line = next(
            (l for l in lines if l.strip() and not l.startswith("#")),
            node["title"],
        )
        desc = first_line[:250]

        entry = {
            "slug": slug,
            "title": node["title"],
            "description": desc,
            "body_html": f"<pre>{body}</pre>",
            "category": "knowledge",
            "content_type": "knowledge",
            "tags": [node["pillar"], "advanced-analytics", "specialist-module"],
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
        print(f"  Registered {slug} ({node['title'][:60]}...)")

    registry["content"] = content_list
    registry["last_updated"] = today

    from core.registry_io import save_registry as _atomic_save
    _atomic_save(registry, REGISTRY_PATH)

    print(
        f"\nDone — {added} new specialist modules integrated "
        f"into {REGISTRY_PATH.name}."
    )
    if added > 0:
        print("Run `python build.py` to rebuild the site with the new assets.")


if __name__ == "__main__":
    main()
