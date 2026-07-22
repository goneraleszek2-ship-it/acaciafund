"""Audit concept coverage across all registry content.

Usage:
    python3 scripts/audit_concept_coverage.py
    python3 scripts/audit_concept_coverage.py --fail-on-orphans 5
    python3 scripts/audit_concept_coverage.py --format json

Exits with code 1 if orphan count exceeds --fail-on-orphans threshold.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.ontology import OntologyManager, extract_concepts_from_text  # noqa: E402


def load_registry() -> list[dict]:
    path = PROJECT_ROOT / "registry.json"
    if not path.exists():
        print(f"ERROR: registry not found at {path}")
        sys.exit(1)
    data = json.loads(path.read_text())
    items = data.get("content", []) + data.get("learn", [])
    return items


def extract_body_text(item: dict) -> str:
    body = item.get("body_html", "") or ""
    return re.sub(r"<[^>]+>", " ", body)


def build_concept_content_map(
    items: list[dict],
    ontology: OntologyManager,
    min_confidence: float = 0.35,
) -> dict[str, list[dict]]:
    concept_map: dict[str, list[dict]] = {}
    content_map: dict[str, list[str]] = {}

    for item in items:
        slug = item.get("slug", "")
        tags = " ".join(item.get("tags", []) or [])
        title = item.get("title", "") or ""
        body = extract_body_text(item)
        combined = f"{title} {tags} {body[:800]}"
        matches = extract_concepts_from_text(combined, ontology)
        matched_ids = []
        for concept, score in matches:
            if score >= min_confidence:
                if concept.id not in concept_map:
                    concept_map[concept.id] = []
                concept_map[concept.id].append({
                    "slug": slug,
                    "title": title,
                    "pillar": item.get("pillar", ""),
                    "content_type": item.get("content_type", ""),
                    "score": round(score, 2),
                })
                matched_ids.append(concept.id)
        content_map[slug] = matched_ids

    return concept_map, content_map


def audit(
    concept_map: dict[str, list[dict]],
    content_map: dict[str, list[str]],
    ontology: OntologyManager,
    fail_threshold: int = 0,
    format: str = "text",
) -> int:
    all_concepts = list(ontology._concepts.values())

    # Per-concept coverage stats
    orphan_concepts: list[Any] = []
    thin_concepts: list[Any] = []
    covered_concepts: list[Any] = []

    for concept in all_concepts:
        items = concept_map.get(concept.id, [])
        count = len(items)
        entry = {
            "id": concept.id,
            "label": concept.label,
            "pillar": concept.pillar,
            "category": concept.category,
            "epistemic_status": getattr(concept, "epistemic_status", "") or "",
            "content_count": count,
            "items": items[:5],
        }
        if count == 0:
            orphan_concepts.append(entry)
        elif count < 3:
            thin_concepts.append(entry)
        else:
            covered_concepts.append(entry)

    # Per-content-type unclassified items
    unclassified: list[Any] = []
    for slug, matched_ids in content_map.items():
        if not matched_ids:
            unclassified.append(slug)

    # Per-pillar coverage
    pillar_stats: dict[str, dict] = {}
    for concept in all_concepts:
        p = concept.pillar
        if p not in pillar_stats:
            pillar_stats[p] = {"total": 0, "covered": 0, "orphans": 0}
        pillar_stats[p]["total"] += 1
        if concept.id in concept_map and len(concept_map[concept.id]) > 0:
            pillar_stats[p]["covered"] += 1
        else:
            pillar_stats[p]["orphans"] += 1

    # Per-category coverage
    cat_stats: dict[str, dict] = {}
    for concept in all_concepts:
        cat = concept.category or "uncategorized"
        if cat not in cat_stats:
            cat_stats[cat] = {"total": 0, "covered": 0, "orphans": 0}
        cat_stats[cat]["total"] += 1
        if concept.id in concept_map and len(concept_map[concept.id]) > 0:
            cat_stats[cat]["covered"] += 1
        else:
            cat_stats[cat]["orphans"] += 1

    # Per epistemic status
    epi_stats: dict[str, dict] = {}
    for concept in all_concepts:
        epi = getattr(concept, "epistemic_status", "") or "missing"
        if epi not in epi_stats:
            epi_stats[epi] = {"total": 0, "covered": 0, "orphans": 0}
        epi_stats[epi]["total"] += 1
        if concept.id in concept_map and len(concept_map[concept.id]) > 0:
            epi_stats[epi]["covered"] += 1
        else:
            epi_stats[epi]["orphans"] += 1

    report = {
        "summary": {
            "total_concepts": len(all_concepts),
            "covered": len(covered_concepts),
            "thin_coverage": len(thin_concepts),
            "orphans": len(orphan_concepts),
            "unclassified_items": len(unclassified),
            "total_items": len(content_map),
            "coverage_pct": round(len(covered_concepts) / len(all_concepts) * 100, 1) if all_concepts else 0,
        },
        "orphans": orphan_concepts,
        "thin_coverage": thin_concepts,
        "pillar_stats": pillar_stats,
        "category_stats": cat_stats,
        "epistemic_stats": epi_stats,
    }

    if format == "json":
        print(json.dumps(report, indent=2))
    else:
        s = report["summary"]
        print(f"{'='*60}")
        print("  CONCEPT COVERAGE AUDIT")
        print(f"{'='*60}")
        print(f"  Total concepts:    {s['total_concepts']}")
        print(f"  Covered (≥3 refs): {s['covered']} ({s['coverage_pct']}%)")
        print(f"  Thin (1-2 refs):   {s['thin_coverage']}")
        print(f"  Orphans (0 refs):  {s['orphans']}")
        print(f"  Unclassified items:{s['unclassified_items']} / {s['total_items']}")
        print()

        if orphan_concepts:
            print(f"  {'─'*40}")
            print(f"  ORPHAN CONCEPTS ({len(orphan_concepts)})")
            print(f"  {'─'*40}")
            for c in sorted(orphan_concepts, key=lambda x: x["pillar"]):
                print(f"    {c['id']:30s}  pillar={c['pillar']:20s}  cat={c['category']}")
        if thin_concepts:
            print(f"  {'─'*40}")
            print(f"  THIN COVERAGE ({len(thin_concepts)})")
            print(f"  {'─'*40}")
            for c in sorted(thin_concepts, key=lambda x: (x["pillar"], x["category"])):
                print(f"    {c['id']:30s}  pillar={c['pillar']:20s}  refs={c['content_count']}")

        print(f"  {'─'*40}")
        print("  PILLAR COVERAGE")
        print(f"  {'─'*40}")
        for p, st in sorted(pillar_stats.items()):
            pct = round(st["covered"] / st["total"] * 100, 1) if st["total"] else 0
            print(f"    {p:20s}  {st['covered']:2d}/{st['total']:2d} ({pct:5.1f}%)  orphans={st['orphans']}")

        print(f"  {'─'*40}")
        print("  EPISTEMIC STATUS COVERAGE")
        print(f"  {'─'*40}")
        for e, st in sorted(epi_stats.items()):
            pct = round(st["covered"] / st["total"] * 100, 1) if st["total"] else 0
            print(f"    {e:20s}  {st['covered']:2d}/{st['total']:2d} ({pct:5.1f}%)  orphans={st['orphans']}")

        if unclassified:
            print(f"  {'─'*40}")
            print(f"  UNCLASSIFIED ITEMS ({len(unclassified)} / {s['total_items']})")
            print(f"  {'─'*40}")
            batch = unclassified[:10]
            for slug in batch:
                print(f"    {slug}")
            if len(unclassified) > 10:
                print(f"    ... and {len(unclassified) - 10} more")
        print(f"  {'─'*40}")

    orphan_count = len(orphan_concepts)
    if fail_threshold > 0 and orphan_count > fail_threshold:
        print(f"\n  FAIL: {orphan_count} orphans exceeds threshold of {fail_threshold}")
        return 1
    return 0


def _load_cached() -> tuple[dict[str, list[dict]], dict[str, list[str]]] | None:
    """Load previously built concept_content_map.json from build cache."""
    path = PROJECT_ROOT / "data" / "concept_content_map.json"
    if not path.exists():
        return None
    data = json.loads(path.read_text())
    concept_map: dict[str, list[dict]] = {}
    content_map: dict[str, list[str]] = {}
    for slug, concept_ids in data.items():
        content_map[slug] = concept_ids
        for cid in concept_ids:
            if cid not in concept_map:
                concept_map[cid] = []
            concept_map[cid].append({
                "slug": slug,
                "title": slug,
                "pillar": "",
                "content_type": "",
                "score": 1.0,
            })
    return concept_map, content_map


def main():
    parser = argparse.ArgumentParser(description="Audit concept coverage across registry content")
    parser.add_argument("--fail-on-orphans", type=int, default=0, help="Exit code 1 if orphans exceed this threshold")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    parser.add_argument("--cached", action="store_true", help="Use build-persisted concept_content_map.json instead of re-extracting")
    args = parser.parse_args()

    ontology_path = PROJECT_ROOT / "data" / "ontology.json"
    if not ontology_path.exists():
        print(f"ERROR: ontology not found at {ontology_path}")
        sys.exit(1)

    ontology = OntologyManager.load(ontology_path)
    print(f"  Loaded ontology: {ontology.concept_count()} concepts, {ontology.relation_count()} relations")

    items = load_registry()
    print(f"  Loaded registry: {len(items)} items (content + learn)")

    if args.cached:
        cached = _load_cached()
        if cached is None:
            print("  WARNING: concept_content_map.json not found — re-extracting")
            concept_map, content_map = build_concept_content_map(items, ontology)
        else:
            concept_map, content_map = cached
            print(f"  Using cached concept map: {len(concept_map)} concepts, {len(content_map)} items")
    else:
        concept_map, content_map = build_concept_content_map(items, ontology)
        print(f"  Built concept map: {len(concept_map)} concepts matched to content")

    exit_code = audit(concept_map, content_map, ontology, fail_threshold=args.fail_on_orphans, format=args.format)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
