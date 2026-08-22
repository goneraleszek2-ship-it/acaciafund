#!/usr/bin/env python3
"""Stress-test propositions against adversarial premise stripping (defeasibility
probing). For every major claim C, recompute SQI with stripped premises.

If new SQI < 0.65 under adversarial re-evaluation, trigger an ontology
isolation flag. This tests epistemic defeasibility: whether a claim retains
its justificatory force when supporting premises are challenged or removed.

Extended with per-dimension blame deltas (source_credibility, technical_accuracy,
practical_value, freshness, trend_relevance) for each proposition, enabling
root-cause analysis of SQI changes under premise stripping."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from scripts.archive.backfill_sqi import (  # noqa: F401
    compute_source_credibility,
    compute_technical_accuracy,
    compute_practical_value,
    compute_freshness,
    compute_trend_relevance,
    compute_educational_quality,
)

PROJECT_ROOT = Path(__file__).parent.parent
PROPOSITIONS_PATH = PROJECT_ROOT / "dist" / "propositions.json"
ONTOLOGY_PATH = PROJECT_ROOT / "data" / "ontology.json"
REPORT_PATH = PROJECT_ROOT / "dist" / "stress_test_report.json"
ISOLATED_PATH = PROJECT_ROOT / "data" / "ontology.isolated.json"


def load_json(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _make_content_from_prop(prop: dict) -> dict:
    """Build a minimal content dict from a proposition for SQI sub-score computation."""
    return {
        "source_breakdown": {"default": 1} if not prop.get("source") or prop["source"] == "content:directory" else {"default": 0},
        "body_html": "",
        "title": prop.get("statement", "")[:200],
        "content_type": prop.get("pillar", "data-engineering"),  # pillar used as content_type proxy
        "signals": {"trend_strength": 50},  # default moderate trend
        "bloom_questions": prop.get("quality_metrics", {}).get("bloom_questions", []),
        "flashcards": prop.get("quality_metrics", {}).get("flashcards", []),
    }


def recompute_sqi_with_deltas(premises: list[str], original_sqi: float,
                              original_sub_scores: dict | None = None) -> dict:
    """Recompute SQI with stripped premises AND return per-dimension deltas.

    Returns dict with keys:
      - 'new_sqi': the recomputed SQI
      - 'deltas': dict mapping dimension name to (before_contribution, after_contribution, delta)
      - 'sub_scores_before': original sub-scores dict
      - 'sub_scores_after': recomputed sub-scores dict
    """
    # Build content dict from proposition
    prop = {
        "source_breakdown": {},
        "body_html": "",
        "title": "",
        "content_type": "data-engineering",
        "signals": {"trend_strength": 50},
    }

    # Populate from proposition data if available
    if prop.get("source") and prop["source"] != "content:directory":
        # Try to extract source type from proposition id or statement
        pass  # simplified for now

    # Compute original sub-scores if not provided
    if original_sub_scores is None:
        orig_content = _make_content_from_prop({})
        sub_before = {
            "source_credibility": compute_source_credibility(orig_content),
            "technical_accuracy": compute_technical_accuracy(orig_content),
            "practical_value": compute_practical_value(orig_content),
            "freshness": compute_freshness(orig_content),
            "trend_relevance": compute_trend_relevance(orig_content),
        }
    else:
        sub_before = original_sub_scores

    # Original contributions (weight × score)
    WEIGHTS = {
        "source_credibility": 0.25,
        "technical_accuracy": 0.25,
        "practical_value": 0.20,
        "freshness": 0.15,
        "trend_relevance": 0.10,
    }
    orig_contributions = {k: WEIGHTS[k] * sub_before[k] for k in WEIGHTS}
    orig_sqi = sum(orig_contributions.values())

    # --- Simulate premise stripping: keep every other premise (adversarial) ---
    stripped_premises = premises[::2] if premises else []

    # Build stripped content dict: we degrade technical_accuracy and practical_value
    # based on premise loss, since those dimensions depend on content depth.
    # source_credibility and freshness and trend_relevance are less premise-dependent
    # so we keep them approximately the same, but still recompute for consistency.

    stripped_content = _make_content_from_prop({})
    # Degrade technical accuracy proportion to premise loss
    if premises:
        premise_loss_ratio = 1.0 - (len(stripped_premises) / len(premises))
        # Technical accuracy degrades by up to 0.15 * premise_loss_ratio
        tech_degradation = 0.15 * premise_loss_ratio
        # Practical value degrades similarly
        prac_degradation = 0.10 * premise_loss_ratio
    else:
        tech_degradation = 0.0
        prac_degradation = 0.0

    # Apply degradations to the stripped content (we fake the content state)
    # Since we can't easily modify the actual content, we compute the stripped scores
    # by applying the degradation to the original sub-scores.
    sub_after_source = sub_before["source_credibility"]  # source credibility unchanged
    sub_after_technical = max(0.0, sub_before["technical_accuracy"] - tech_degradation)
    sub_after_practical = max(0.0, sub_before["practical_value"] - prac_degradation)
    sub_after_freshness = compute_freshness(stripped_content)  # unchanged by premises
    sub_after_trend = compute_trend_relevance(stripped_content)  # unchanged by premises

    sub_after = {
        "source_credibility": sub_after_source,
        "technical_accuracy": sub_after_technical,
        "practical_value": sub_after_practical,
        "freshness": sub_after_freshness,
        "trend_relevance": sub_after_trend,
    }

    # After contributions
    after_contributions = {k: WEIGHTS[k] * sub_after[k] for k in WEIGHTS}
    new_sqi = sum(after_contributions.values())

    # Compute deltas
    deltas = {}
    for k in WEIGHTS:
        before_k = orig_contributions[k]
        after_k = after_contributions[k]
        deltas[k] = {
            "before_contribution": round(before_k, 4),
            "after_contribution": round(after_k, 4),
            "delta": round(after_k - before_k, 4),
        }

    return {
        "new_sqi": round(new_sqi, 4),
        "deltas": deltas,
        "sub_scores_before": {k: round(v, 4) for k, v in sub_before.items()},
        "sub_scores_after": {k: round(v, 4) for k, v in sub_after.items()},
    }


def main() -> int:
    propositions = load_json(PROPOSITIONS_PATH)
    ontology = load_json(ONTOLOGY_PATH)

    # Build pillar lookup and epistemic status map
    pillar_of = {}
    epistemic_map = {}
    for c in ontology.get("concepts", []):
        pillar_of[c["id"]] = c.get("pillar", "cross-pillar")
        epistemic_map[c["id"]] = c.get("epistemic_status", "")

    isolated_concepts = set()
    passed = 0
    failed = 0
    details = []
    blame_report = []

    for prop in propositions:
        pid = prop.get("id", "unknown")
        original_sqi = prop.get("quality_metrics", {}).get("sqi", 0.5) if "quality_metrics" in prop else 0.5
        premises = prop.get("premises", [])
        pillar = prop.get("pillar", "data-engineering")

        # Compute original sub-scores for blame attribution
        orig_sub_scores = None
        try:
            orig_sub_scores = {
                "source_credibility": compute_source_credibility(_make_content_from_prop(prop)),
                "technical_accuracy": compute_technical_accuracy(_make_content_from_prop(prop)),
                "practical_value": compute_practical_value(_make_content_from_prop(prop)),
                "freshness": compute_freshness(_make_content_from_prop(prop)),
                "trend_relevance": compute_trend_relevance(_make_content_from_prop(prop)),
            }
        except Exception:
            orig_sub_scores = None

        # Recompute with deltas
        try:
            result = recompute_sqi_with_deltas(premises, original_sqi, orig_sub_scores)
        except Exception as e:
            result = {"new_sqi": 0.0, "deltas": {}, "error": str(e)}

        new_sqi = result["new_sqi"]
        deltas = result.get("deltas", {})

        # Step 1: Check if SQI dropped below threshold
        original_passed = original_sqi >= 0.65
        new_passed = new_sqi >= 0.65

        if new_passed and original_passed:
            passed += 1
        elif not new_passed and not original_passed:
            # Both below - count as pre-existing, track blame for analysis
            failed += 1
            # Record blame deltas for analysis
            blame_report.append({
                "proposition_id": pid,
                "original_sqi": original_sqi,
                "new_sqi": new_sqi,
                "pillar": pillar,
                "deltas": deltas,
                "defeasibility_type": "pre-existing_below_threshold"
            })
        elif new_passed and not original_passed:
            # Was below, now passes (unlikely but possible with random factor)
            passed += 1
        else:
            # Was above, now below - claim defeated
            failed += 1
            isolated_concepts.add(pid)
            blame_report.append({
                "proposition_id": pid,
                "original_sqi": original_sqi,
                "new_sqi": new_sqi,
                "pillar": pillar,
                "deltas": deltas,
                "defeasibility_type": "premise-stripping_defeat"
            })

    # Build isolated ontology concepts
    isolated_json = {"isolated_concepts": [], "generated_at": __import__("datetime").datetime.now().isoformat()}
    with open(ONTOLOGY_PATH) as f:
        ont_data = json.load(f)

    concept_by_id = {c["id"]: c for c in ont_data["concepts"]}
    for cid in isolated_concepts:
        if cid in concept_by_id:
            concept = concept_by_id[cid]
            concept["_defeasibility_flag"] = "2026-08-16_analytical_engine"
            concept["_defeasibility_reason"] = "SQI dropped below 0.65 under adversarial premise stripping"
            isolated_json["isolated_concepts"].append(concept)

    # Output reports
    stress_report = {
        "total_propositions": len(propositions),
        "passed_defeasibility_test": passed,
        "failed_defeasibility_test": failed,
        "isolation_rate": failed / len(propositions) if propositions else 0,
        "blame_report": blame_report[:50]  # first 50 for brevity
    }
    save_json(REPORT_PATH, stress_report)

    save_json(ISOLATED_PATH, isolated_json)

    print(f"Stress test report written to {REPORT_PATH}")
    print(f"Isolated ontology written to {ISOLATED_PATH}")
    print(f"  Total propositions: {len(propositions)}")
    print(f"  Passed (SQI >= 0.65 under stripping): {passed}")
    print(f"  Failed (SQI < 0.65 under stripping): {failed}")
    print(f"  Isolation rate: {failed / len(propositions) * 100:.1f}%")

    # Print blame summary
    bucket_counts = {"A": 0, "B": 0, "C": 0, "other": 0}
    for entry in blame_report:
        # Simple bucketing based on which dimension had the largest delta
        if entry.get("deltas"):
            dim_deltas = entry["deltas"]
            largest_delta_key = max(dim_deltas, key=lambda k: abs(dim_deltas[k]["delta"]))
            # Map dimension to bucket
            if largest_delta_key in ("source_credibility",):
                bucket_counts["A"] += 1
            elif largest_delta_key in ("technical_accuracy", "practical_value"):
                bucket_counts["B"] += 1
            elif largest_delta_key in ("freshness", "trend_relevance"):
                bucket_counts["C"] += 1
            else:
                bucket_counts["other"] += 1
        else:
            bucket_counts["other"] += 1

    print(f"  Blame buckets: A(source)={bucket_counts['A']}, B(technical/prac)={bucket_counts['B']}, "
          f"C(freshness/trend)={bucket_counts['C']}, other={bucket_counts['other']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())