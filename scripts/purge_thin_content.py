#!/usr/bin/env python3
"""Phase 0: Purge thin content by marking items as status: draft.

Criteria for draft:
- Research: body_html < 1000 chars OR contains template filler pattern
- Learn: 0 flashcards AND 0 bloom_questions AND body_html < 2000 chars
- Knowledge: body_html contains template filler AND < 2000 chars
"""

import json
import re
from pathlib import Path

REGISTRY = Path(__file__).parent.parent / "registry.json"

TEMPLATE_FILLER = re.compile(r'Content about.*This section covers', re.IGNORECASE)
TRUNCATED_ABSTRACT = re.compile(
    r'(Significance|Further Reading).*advancing knowledge',
    re.IGNORECASE
)


def is_thin_research(item: dict) -> bool:
    body = item.get("body_html", "")
    if len(body) < 1000:
        return True
    if TEMPLATE_FILLER.search(body) or TRUNCATED_ABSTRACT.search(body):
        return True
    return False


def is_thin_learn(item: dict) -> bool:
    fcs = item.get("flashcards", [])
    bqs = item.get("bloom_questions", [])
    body = item.get("body_html", "")
    if len(fcs) == 0 and len(bqs) == 0 and len(body) < 2000:
        return True
    return False


def is_thin_knowledge(item: dict) -> bool:
    body = item.get("body_html", "")
    if len(body) < 2000 and (TEMPLATE_FILLER.search(body) or TRUNCATED_ABSTRACT.search(body)):
        return True
    return False


def main():
    with open(REGISTRY) as f:
        reg = json.load(f)

    content = reg["content"]
    purged = {"research": [], "learn": [], "knowledge": []}
    kept = {"research": 0, "learn": 0, "knowledge": 0}

    for item in content:
        ct = item.get("content_type", "")
        slug = item.get("slug", "")

        if item.get("status") == "draft":
            continue

        if ct == "research" and is_thin_research(item):
            item["status"] = "draft"
            purged["research"].append(slug)
        elif ct == "learn" and is_thin_learn(item):
            item["status"] = "draft"
            purged["learn"].append(slug)
        elif ct == "knowledge" and is_thin_knowledge(item):
            item["status"] = "draft"
            purged["knowledge"].append(slug)
        else:
            kept[ct] = kept.get(ct, 0) + 1

    with open(REGISTRY, "w") as f:
        json.dump(reg, f, indent=2)

    total_purged = sum(len(v) for v in purged.values())
    total_kept = sum(kept.values())

    print("=== PURGE RESULTS ===")
    for ct, slugs in purged.items():
        print(f"  {ct}: {len(slugs)} purged")
    print(f"\n  Total purged: {total_purged}")
    print(f"  Total kept: {total_kept}")

    print("\n=== PURGED SLUGS ===")
    for ct, slugs in purged.items():
        for s in slugs:
            print(f"  [{ct}] {s}")


if __name__ == "__main__":
    main()
