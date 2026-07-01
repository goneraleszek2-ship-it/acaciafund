#!/usr/bin/env python3
"""
Build a knowledge graph from registry items.
Outputs JSON mapping each article slug to top 3 related articles by tag overlap.
"""

import json
from pathlib import Path

REGISTRY_PATH = Path("/root/acaciafund/registry.json")
OUTPUT_PATH = Path("/root/acaciafund/data/knowledge_graph.json")


def load_registry():
    with open(REGISTRY_PATH, "r") as f:
        data = json.load(f)
    # Assuming data has a "content" list of items
    return data.get("content", [])


def build_graph():
    items = load_registry()
    print(f"Loaded {len(items)} items from registry")
    # Map slug -> set of tags (lowercase)
    doc_tags = {}
    for it in items:
        slug = it.get("slug")
        if not slug:
            continue
        tags = it.get("tags", [])
        # Normalize tags to lowercase strings
        tag_set = {str(t).lower() for t in tags}
        doc_tags[slug] = tag_set
    # Compute Jaccard similarity on tag sets
    graph = {}
    for slug1, tags1 in doc_tags.items():
        scores = []
        for slug2, tags2 in doc_tags.items():
            if slug1 == slug2:
                continue
            if not tags1 or not tags2:
                sim = 0.0
            else:
                inter = len(tags1 & tags2)
                union = len(tags1 | tags2)
                sim = inter / union if union else 0.0
            scores.append((slug2, sim))
        scores.sort(key=lambda x: x[1], reverse=True)
        top3 = scores[:3]
        graph[slug1] = [{"slug": s2, "score": round(s, 4)} for s2, s in top3]
    # Write output
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(graph, f, indent=2)
    print(f"Knowledge graph written to {OUTPUT_PATH}")
    return graph


if __name__ == "__main__":
    build_graph()
