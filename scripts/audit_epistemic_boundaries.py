#!/usr/bin/env python3
"""Enforce Salamucha's rule of non-contradiction across distinct categories
of knowledge: Empirical Data ⇏ Normative Compliance (direct derivation)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
ONTOLOGY_PATH = PROJECT_ROOT / "data" / "ontology.json"
CONFIG_PATH = PROJECT_ROOT / "config.py"
REPORT_PATH = PROJECT_ROOT / "dist" / "epistemic_audit.json"


def load_json(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def determine_pillar(concept_id: str, ontology: dict) -> str | None:
    """Determine the pillar for a concept from its ID or ontology entry."""
    for c in ontology.get("concepts", []):
        if c.get("id") == concept_id:
            return c.get("pillar", "cross-pillar")
    # Heuristic from ID prefix
    if concept_id.startswith(("aml", "compliance")):
        return "aml"
    if concept_id.startswith(("stock", "market")):
        return "stock"
    if concept_id.startswith(("data", "pipeline", "warehouse")):
        return "data-engineering"
    return None


def main() -> int:
    ontology = load_json(ONTOLOGY_PATH)
    concepts = ontology.get("concepts", [])
    relations = ontology.get("relations", [])

    # Build pillar lookup
    pillar_of = {}
    for c in concepts:
        pillar_of[c["id"]] = c.get("pillar", "cross-pillar")

    # Audit boundary violations:
    # Rule: data-engineering → (aml or compliance) with "governs" or "requires"
    # is a direct empirical→normative derivation violation
    boundary_violations = []

    for r in relations:
        u = r["source_id"]
        v = r["target_id"]
        rtype = r.get("relation_type", "")

        u_pillar = determine_pillar(u, ontology)
        v_pillar = determine_pillar(v, ontology)

        # Check: empirical data (data-engineering) dictating normative rules (aml/compliance)
        if u_pillar == "data-engineering" and v_pillar in ("aml", "compliance"):
            if rtype in ("governs", "requires", "regulates"):
                boundary_violations.append({
                    "source": u,
                    "target": v,
                    "u_pillar": u_pillar,
                    "v_pillar": v_pillar,
                    "relation_type": rtype,
                    "violation": f"Direct empirical→normative: {u_pillar}({rtype}) → {v_pillar}"
                })

    # Also check via concept metadata fields
    for c in concepts:
        c_pillar = c.get("pillar", "cross-pillar")
        # If a data-engineering concept has normative_basis set that influences compliance
        if c_pillar == "data-engineering" and c.get("normative_basis"):
            # Check if this concept connects to aml/compliance nodes
            for r in relations:
                if r["source_id"] == c["id"] and r["target_id"] in [
                    n for n in pillar_of if pillar_of[n] in ("aml", "compliance")
                ]:
                    if r.get("relation_type") in ("governs", "requires"):
                        boundary_violations.append({
                            "source": c["id"],
                            "target": r["target_id"],
                            "u_pillar": c_pillar,
                            "v_pillar": "aml/compliance",
                            "relation_type": r.get("relation_type", ""),
                            "violation": f"Data-eng concept '{c['id']}' with normative_basis='{c.get('normative_basis')}' directly governs compliance"
                        })

    # Deduplicate violations
    seen_keys = set()
    unique_violations = []
    for v in boundary_violations:
        key = (v["source"], v["target"], v["relation_type"])
        if key not in seen_keys:
            seen_keys.add(key)
            unique_violations.append(v)

    report = {
        "total_violations": len(unique_violations),
        "boundary_violations": unique_violations,
        "rule": "Empirical data (data-engineering) must not directly derive normative rules (aml/compliance) without intermediate normative premise",
        "pillars_audited": ["data-engineering", "aml", "compliance"]
    }

    save_json(REPORT_PATH, report)
    print(f"Epistemic audit written to {REPORT_PATH}")
    print(f"  Boundary violations: {len(unique_violations)}")

    for v in unique_violations:
        print(f"  - {v['violation']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())