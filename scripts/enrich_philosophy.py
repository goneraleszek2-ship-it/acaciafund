#!/usr/bin/env python3
"""Enrich ontology concepts with philosophical foundations metadata.

Reads data/philosophy_metadata.json and merges it into
the ontology (data/ontology.json) by updating each Concept's
philosophical_* fields.

Usage:
    python3 scripts/enrich_philosophy.py                     # merge into existing ontology
    python3 scripts/enrich_philosophy.py --output path       # write to separate file
"""

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
ONTOLOGY_PATH = PROJECT_ROOT / "data" / "ontology.json"
PHILOSOPHY_PATH = PROJECT_ROOT / "data" / "philosophy_metadata.json"


def load_json(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def enrich_ontology(ontology: dict, metadata: dict) -> int:
    """Merge philosophical fields into each concept. Returns count enriched."""
    enriched = 0
    for concept in ontology.get("concepts", []):
        cid = concept.get("id")
        if cid and cid in metadata:
            meta = metadata[cid]
            changed = False
            META_FIELDS = [
                "philosophical_lineage",
                "epistemic_status",
                "normative_basis",
                "ontological_commitment",
                "temporal_ontology",
                "uncertainty_class",
                "governance_model",
                "semantic_contract_type",
                "philosophical_sources",
                "cross_pillar_analogs",
            ]
            for field in META_FIELDS:
                if field in meta:
                    if field not in concept or not concept[field]:
                        concept[field] = meta[field]
                        changed = True
                else:
                    # Ensure default empty value
                    if field not in concept:
                        concept[field] = [] if field in ("philosophical_lineage", "philosophical_sources", "cross_pillar_analogs") else ""
                        changed = True
            if changed:
                enriched += 1
    return enriched


def main():
    output_path = None
    args = sys.argv[1:]
    for i, a in enumerate(args):
        if a == "--output" and i + 1 < len(args):
            output_path = Path(args[i + 1])
        elif a == "--ontology" and i + 1 < len(args):
            # allow specifying a different ontology file
            global ONTOLOGY_PATH
            ONTOLOGY_PATH = Path(args[i + 1])

    if not PHILOSOPHY_PATH.exists():
        print(f"Error: philosophy metadata not found at {PHILOSOPHY_PATH}")
        sys.exit(1)

    if not ONTOLOGY_PATH.exists():
        print(f"Error: ontology file not found at {ONTOLOGY_PATH}")
        sys.exit(1)

    metadata = load_json(PHILOSOPHY_PATH)
    if output_path:
        # Write enriched ontology to separate file
        ontology = load_json(ONTOLOGY_PATH)
        count = enrich_ontology(ontology, metadata)
        save_json(output_path, ontology)
        print(f"Enriched {count} concepts. Written to {output_path}")
    else:
        # Inline merge
        ontology = load_json(ONTOLOGY_PATH)
        count = enrich_ontology(ontology, metadata)
        save_json(ONTOLOGY_PATH, ontology)
        print(f"Enriched {count} concepts in {ONTOLOGY_PATH}")


if __name__ == "__main__":
    main()
