#!/usr/bin/env python3
"""Export registry items as a bipartite document–tag graph for Cytoscape.js.

Reads registry.json and produces a JSON payload with nodes (documents + tags)
and edges (document-to-tag assignments), plus an optional layer of
document-to-document similarity edges.

Output: data/cytograph.json
"""

import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REGISTRY_PATH = ROOT / "registry.json"
OUTPUT_PATH = ROOT / "data" / "cytograph.json"

# Domain colour palette (CSS-friendly hex)
DOMAIN_COLORS = {
    "blog": "#6366f1",
    "learn": "#22c55e",
    "knowledge": "#d97706",
    "docs": "#a855f7",
    "other": "#6b7280",
}

TAG_COLOR = "#14b8a6"

# Domain prefixes extracted from slug
DOMAIN_PREFIX_RE = re.compile(r"^([a-z]+)/")


def _domain(slug: str) -> str:
    m = DOMAIN_PREFIX_RE.match(slug)
    return m.group(1) if m else "other"


def load_registry() -> list[dict]:
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("content", [])


def build_graph() -> dict:
    items = load_registry()
    print(f"Loaded {len(items)} items from registry")

    doc_tag_map: dict[str, set[str]] = {}
    tag_doc_map: dict[str, set[str]] = {}

    for item in items:
        slug = item.get("slug", "")
        tags = item.get("tags", [])
        tag_set = {t.lower() for t in tags if isinstance(t, str)}
        doc_tag_map[slug] = tag_set
        for t in tag_set:
            tag_doc_map.setdefault(t, set()).add(slug)

    # --- Nodes ---
    nodes: list[dict] = []
    seen_ids: set[str] = set()

    # Document nodes
    tag_counts = Counter()
    for slug, tags in doc_tag_map.items():
        tag_counts.update(tags)
        domain = _domain(slug)
        title = next(
            (i.get("title", "") for i in items if i.get("slug") == slug),
            slug,
        )
        nodes.append(
            {
                "data": {
                    "id": f"doc:{slug}",
                    "label": title[:80],
                    "type": "document",
                    "domain": domain,
                    "slug": slug,
                    "size": max(10, min(50, len(tags) * 8)),
                    "color": DOMAIN_COLORS.get(domain, DOMAIN_COLORS["other"]),
                }
            }
        )
        seen_ids.add(f"doc:{slug}")

    # Tag nodes
    for tag, doc_set in sorted(tag_doc_map.items()):
        count = len(doc_set)
        if tag not in seen_ids:
            nodes.append(
                {
                    "data": {
                        "id": f"tag:{tag}",
                        "label": tag,
                        "type": "concept",
                        "count": count,
                        "size": max(8, min(40, 8 + count * 3)),
                        "color": TAG_COLOR,
                    }
                }
            )
            seen_ids.add(f"tag:{tag}")

    # Build lookup: slug → domain
    slug_domain = {}
    for item in items:
        s = item.get("slug", "")
        if s:
            slug_domain[s] = _domain(s)

    # --- Edges ---
    edges: list[dict] = []
    for slug, tags in doc_tag_map.items():
        src_pillar = slug_domain.get(slug, "")
        for t in tags:
            edges.append(
                {
                    "data": {
                        "id": f"edge:{slug}:{t}",
                        "source": f"doc:{slug}",
                        "target": f"tag:{t}",
                        "sourcePillar": src_pillar,
                        "targetPillar": "",
                    }
                }
            )

    print(f"  Nodes: {len(nodes)} ({len([n for n in nodes if n['data']['type'] == 'document'])} docs, "
          f"{len([n for n in nodes if n['data']['type'] == 'concept'])} tags)")
    print(f"  Edges: {len(edges)}")

    graph = {"nodes": nodes, "edges": edges}

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(graph, f, indent=2)
    print(f"Graph written to {OUTPUT_PATH}")
    return graph


if __name__ == "__main__":
    build_graph()
