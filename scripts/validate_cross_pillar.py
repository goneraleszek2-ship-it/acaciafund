"""Validate cross-pillar analog mappings bidirectionally.

Usage:
    python3 scripts/validate_cross_pillar.py
    python3 scripts/validate_cross_pillar.py --fix
    python3 scripts/validate_cross_pillar.py --format json

Checks:
  1. Every cross_pillar_analog reference points to an existing concept
  2. Every analog relationship is bidirectional (A→B implies B→A)
  3. Reports missing reciprocal mappings
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def load_metadata() -> dict:
    path = PROJECT_ROOT / "data" / "philosophy_metadata.json"
    if not path.exists():
        print(f"ERROR: {path} not found")
        sys.exit(1)
    return json.loads(path.read_text())


def load_ontology() -> dict:
    path = PROJECT_ROOT / "data" / "ontology.json"
    if not path.exists():
        print(f"ERROR: {path} not found")
        sys.exit(1)
    return json.loads(path.read_text())


def validate(
    metadata: dict,
    ontology: dict,
    fix: bool = False,
    output_format: str = "text",
) -> int:
    all_concept_ids = {c["id"] for c in ontology["concepts"]}
    all_labels = {c["id"]: c["label"] for c in ontology["concepts"]}
    all_pillars = {c["id"]: c["pillar"] for c in ontology["concepts"]}

    # Build forward analog mapping
    analogs: dict[str, list[str]] = {}
    for cid, data in metadata.items():
        refs = data.get("cross_pillar_analogs", [])
        if refs:
            analogs[cid] = refs

    # Build reverse mapping (who points to whom)
    reverse: dict[str, list[str]] = defaultdict(list)
    for cid, refs in analogs.items():
        for ref in refs:
            reverse[ref].append(cid)

    # === Check 1: Dangling references ===
    dangling: list[tuple[str, str]] = []
    for cid, refs in analogs.items():
        for ref in refs:
            if ref not in all_concept_ids:
                dangling.append((cid, ref))

    # === Check 2: Non-reciprocal mappings ===
    non_reciprocal: list[dict[str, Any]] = []
    for cid, refs in analogs.items():
        for ref in refs:
            if ref in analogs:
                if cid not in analogs[ref]:
                    non_reciprocal.append({
                        "source": cid,
                        "source_label": all_labels.get(cid, cid),
                        "source_pillar": all_pillars.get(cid, ""),
                        "target": ref,
                        "target_label": all_labels.get(ref, ref),
                        "target_pillar": all_pillars.get(ref, ""),
                    })
            else:
                non_reciprocal.append({
                    "source": cid,
                    "source_label": all_labels.get(cid, cid),
                    "source_pillar": all_pillars.get(cid, ""),
                    "target": ref,
                    "target_label": all_labels.get(ref, ref),
                    "target_pillar": all_pillars.get(ref, ""),
                    "note": "target has no cross_pillar_analogs at all",
                })

    # === Check 3: Concepts in ontology with analogs but missing metadata ===
    missing_metadata: list[dict[str, Any]] = []
    for c in ontology["concepts"]:
        analogs_from_ont = c.get("cross_pillar_analogs", [])
        if analogs_from_ont:
            cid = c["id"]
            if cid not in metadata:
                missing_metadata.append({
                    "id": cid,
                    "label": c["label"],
                    "pillar": c["pillar"],
                    "analogs": analogs_from_ont,
                })
            else:
                meta_analogs = metadata[cid].get("cross_pillar_analogs", [])
                if sorted(meta_analogs) != sorted(analogs_from_ont):
                    missing_metadata.append({
                        "id": cid,
                        "label": c["label"],
                        "pillar": c["pillar"],
                        "in_ontology": analogs_from_ont,
                        "in_metadata": meta_analogs,
                        "note": "ontology and metadata mismatch",
                    })

    # === Stats ===
    total_with_analogs = len(analogs)
    total_in_ontology = sum(1 for c in ontology["concepts"] if c.get("cross_pillar_analogs"))
    reciprocal_count = sum(
        1 for cid in analogs
        if all(ref in analogs and cid in analogs[ref] for ref in analogs[cid] if ref in analogs)
    )

    report = {
        "summary": {
            "total_concepts_in_ontology": len(all_concept_ids),
            "concepts_with_analogs_ontology": total_in_ontology,
            "concepts_with_analogs_metadata": total_with_analogs,
            "fully_reciprocal_pairs": reciprocal_count,
            "non_reciprocal": len(non_reciprocal),
            "dangling_refs": len(dangling),
            "metadata_mismatches": len(missing_metadata),
        },
        "non_reciprocal": non_reciprocal,
        "dangling": [{"source": s, "target": t} for s, t in dangling],
        "metadata_mismatches": missing_metadata,
    }

    if output_format == "json":
        print(json.dumps(report, indent=2))
    else:
        s = report["summary"]
        print(f"{'='*60}")
        print(f"  CROSS-PILLAR ANALOG VALIDATION")
        print(f"{'='*60}")
        print(f"  Concepts in ontology:        {s['total_concepts_in_ontology']}")
        print(f"  With analogs (ontology):     {s['concepts_with_analogs_ontology']}")
        print(f"  With analogs (metadata):     {s['concepts_with_analogs_metadata']}")
        print(f"  Fully reciprocal pairs:      {s['fully_reciprocal_pairs']}")
        print(f"  Non-reciprocal:              {s['non_reciprocal']}")
        print(f"  Dangling references:         {s['dangling_refs']}")
        print(f"  Metadata mismatches:         {s['metadata_mismatches']}")
        print()

        if dangling:
            print(f"  {'─'*40}")
            print(f"  DANGLING REFERENCES ({len(dangling)})")
            print(f"  {'─'*40}")
            for s, t in dangling:
                print(f"    {s} -> {t}  (target concept does not exist)")

        if non_reciprocal:
            print(f"  {'─'*40}")
            print(f"  NON-RECIPROCAL ({len(non_reciprocal)})")
            print(f"  {'─'*40}")
            for nr in non_reciprocal:
                note = f"  [{nr.get('note', 'missing reverse')}]" if "note" in nr else ""
                print(f"    {nr['source']:25s} ({nr['source_pillar']:20s}) -> {nr['target']:25s} ({nr['target_pillar']:20s}){note}")

        if missing_metadata:
            print(f"  {'─'*40}")
            print(f"  METADATA MISMATCHES ({len(missing_metadata)})")
            print(f"  {'─'*40}")
            for mm in missing_metadata:
                note = mm.get("note", "missing from philosophy_metadata.json")
                print(f"    {mm['id']:25s} ({mm['pillar']}) — {note}")

        print(f"  {'─'*40}")

    # Auto-fix reciprocal mappings
    if fix and non_reciprocal:
        _apply_fixes(metadata, ontology, non_reciprocal, all_concept_ids)
        _save_both(metadata, ontology)
        print(f"  Fixed {len(non_reciprocal)} non-reciprocal mappings")

    return 1 if (dangling or non_reciprocal) else 0


def _apply_fixes(
    metadata: dict,
    ontology: dict,
    non_reciprocal: list[dict],
    all_ids: set[str],
) -> None:
    ontology_concept_map = {c["id"]: c for c in ontology["concepts"]}
    for nr in non_reciprocal:
        target = nr["target"]
        source = nr["source"]
        if target not in metadata:
            continue
        if target in all_ids:
            meta_refs = metadata[target].setdefault("cross_pillar_analogs", [])
            if source not in meta_refs:
                meta_refs.append(source)
            ont_concept = ontology_concept_map.get(target)
            if ont_concept:
                ont_refs = ont_concept.setdefault("cross_pillar_analogs", [])
                if source not in ont_refs:
                    ont_refs.append(source)


def _save_both(metadata: dict, ontology: dict) -> None:
    meta_path = PROJECT_ROOT / "data" / "philosophy_metadata.json"
    meta_path.write_text(json.dumps(metadata, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    print(f"  Updated: {meta_path}")
    ont_path = PROJECT_ROOT / "data" / "ontology.json"
    ont_path.write_text(json.dumps(ontology, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    print(f"  Updated: {ont_path}")


def main():
    parser = argparse.ArgumentParser(description="Validate cross-pillar analog mappings")
    parser.add_argument("--fix", action="store_true", help="Auto-add missing reciprocal mappings")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    args = parser.parse_args()

    metadata = load_metadata()
    ontology = load_ontology()
    print(f"  Loaded philosophy_metadata.json: {len(metadata)} concepts")
    print(f"  Loaded ontology.json: {len(ontology['concepts'])} concepts")

    exit_code = validate(metadata, ontology, fix=args.fix, output_format=args.format)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
