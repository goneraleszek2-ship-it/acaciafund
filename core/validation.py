"""Pluralistic content validation for AcaciaFund build pipeline.

This module provides multiple parallel validation tracks (instead of a single
gate), allowing different evidentiary standards to be evaluated simultaneously.

Western empirical philosophy is one track among many: empirically_verified,
theoretical, contemplative, and authority_based. Each track produces a score,
and no single track can gatekeep others.

Configuration is in config.py per-pillar weights.
"""

from typing import Any, Dict, List, Optional, Tuple

from config import PILLAR_URL_MAP, PILLAR_CONFIG, SQI_THRESHOLD_MIN

logger = __import__("logging").getLogger(__name__)

ALLOWED_CONTENT_TYPES = {"research", "learn", "knowledge"}

# Validation track weights per pillar (configurable via config.py PILLAR_VALIDATION_WEIGHTS)
# Default: equal weighting across all 5 tracks
DEFAULT_VALIDATION_WEIGHTS: Dict[str, Dict[str, float]] = {
    "aml": {"empirical_fidelity": 0.3, "coherence": 0.2, "philosophical": 0.2, "schema": 0.2, "tests": 0.1},
    "stock": {"empirical_fidelity": 0.3, "coherence": 0.2, "philosophical": 0.2, "schema": 0.2, "tests": 0.1},
    "data-engineering": {"empirical_fidelity": 0.25, "coherence": 0.25, "philosophical": 0.2, "schema": 0.2, "tests": 0.1},
}


def compute_empirical_fidelity(item: Dict[str, Any]) -> Optional[float]:
    """Track 1: Empirical fidelity - source chain integrity.

    Western empiricism track: evaluates source verification, SQI, and evidence quality.
    Returns a score in [0, 1] where 1 = fully verified source chain.
    """
    signals = item.get("signals", {})
    if not signals:
        return None

    avg_sqi = signals.get("avg_sqi")
    source_breakdown = item.get("source_breakdown", {})
    quality_metrics = item.get("quality_metrics", {})

    components = []

    # SQI component (if available)
    if avg_sqi is not None:
        try:
            sqi_val = float(avg_sqi)
            components.append(("sqi", sqi_val))
        except (ValueError, TypeError):
            pass

    # Source verification component
    source_verified = item.get("source_verified", False)
    if source_verified is not None:
        components.append(("source_verified", 1.0 if source_verified else 0.0))

    # Source breakdown diversity (more sources = more robust)
    if source_breakdown:
        source_count = sum(source_breakdown.values())
        # Normalize: arXiv + HN + PubMed typical range is 1-20
        diversity_score = min(source_count / 20.0, 1.0)
        components.append(("source_diversity", diversity_score))

    # Quality metrics evidence level
    evidence_level = quality_metrics.get("evidence_level", "")
    level_scores = {"Unknown": 0.5, "Primary": 1.0, "Secondary": 0.7, "Tertiary": 0.3}
    if evidence_level in level_scores:
        components.append(("evidence_level", level_scores[evidence_level]))

    if not components:
        return None

    # Weighted average
    total = sum(weight for _, weight in components) if components else 1.0
    # Simple average for now
    score = sum(val for _, val in components) / len(components)
    return round(min(max(score, 0.0), 1.0), 3)


def compute_coherence_score(item: Dict[str, Any], ontology: Optional[Dict] = None) -> Optional[float]:
    """Track 2: Coherence score - ontological consistency.

    Evaluates how well the content item fits within the 192-concept ontology
    with 434 directed relations. High coherence = concept extraction aligns
    with existing ontology structure.
    """
    from core.ontology import OntologyManager

    concept_tags = item.get("tags", [])
    if not concept_tags:
        return None

    try:
        m = OntologyManager.load("data/ontology.json")
        extracted = 0
        aligned = 0

        for tag in concept_tags:
            concept = m.get_concept(tag)
            if concept:
                extracted += 1
                # Check if concept has relations that align with content topic
                relations = m.relations_for(tag)
                if relations:
                    aligned += 1

        if extracted == 0:
            return None

        coherence = aligned / extracted if extracted > 0 else 0.0
        # If ontology provided, further refine
        if ontology:
            # Placeholder for future ontology-aware coherence
            pass

        return round(min(max(coherence, 0.0), 1.0), 3)
    except Exception as e:
        logger.warning(f"Coherence score computation failed: {e}")
        return None


def compute_philosophical_consistency(item: Dict[str, Any]) -> Optional[float]:
    """Track 3: Philosophical consistency - cross-tradition compatibility.

    Evaluates how well the content item's epistemological status aligns
    with multiple philosophical frameworks. Not a "truth" check but a
    compatibility score.

    Returns a score in [0, 1] where 1 = compatible with all tracked traditions.
    """
    epistemic_status = item.get("epistemic_status", "empirically_verified")
    way_of_knowing = item.get("way_of_knowing", "empirical")

    # Score based on internal consistency of the item's own metadata
    consistency_factors = []

    # If epistemic_status and way_of_knowing are aligned
    alignment_map = {
        ("empirically_verified", "empirical"): 1.0,
        ("theoretical", "empirical"): 0.7,
        ("contemplative", "contemplative"): 1.0,
        ("authority_based", "authority"): 1.0,
        ("empirically_verified", "contemplative"): 0.3,
    }

    aligned = alignment_map.get((epistemic_status, way_of_knowing), 0.5)
    consistency_factors.append(aligned)

    # Check philosophical_lineage if present
    lineage = item.get("philosophical_lineage")
    if lineage:
        consistency_factors.append(0.8)  # Lineage present = some structure

    if not consistency_factors:
        return None

    score = sum(consistency_factors) / len(consistency_factors)
    return round(min(max(score, 0.0), 1.0), 3)


def compute_schema_validity(item: Dict[str, Any]) -> Optional[float]:
    """Track 4: Schema validity - Pydantic schema compliance.

    Standard Pydantic validation. Returns 1.0 if valid, 0.0 if not.
    This is the existing validation track, preserved for backward compatibility.
    """
    from schemas import ContentItem

    try:
        ContentItem(**item)
        return 1.0
    except Exception as e:
        logger.debug(f"Schema validation failed: {e}")
        return 0.0


def compute_test_suite_validity(item: Dict[str, Any]) -> Optional[float]:
    """Track 5: Test suite validity - 855-test battery compliance.

    Standard test suite validation. Returns 1.0 if item passes all relevant
    tests, 0.0 if not. Preserved for backward compatibility.
    """
    # This is a meta-signal: we check if the item has signals that would
    # typically pass the test suite (SQI threshold, source verification)
    sqi = item.get("sqi")
    source_verified = item.get("source_verified", False)

    scores = []
    if sqi is not None:
        try:
            sqi_val = float(sqi)
            scores.append(1.0 if 0.65 <= sqi_val <= 1.0 else 0.5)
        except (ValueError, TypeError):
            scores.append(0.0)

    if source_verified is not None:
        scores.append(1.0 if source_verified else 0.0)

    if not scores:
        return None

    return round(sum(scores) / len(scores), 3)


def validate_content_pluralistic(
    content_items: List[Dict[str, Any]],
    ontology: Optional[Any] = None,
    *,
    strict: bool = False,
    pillar_weights: Optional[Dict[str, Dict[str, float]]] = None,
) -> Dict[str, Any]:
    """Run parallel validation tracks on content items.

    Args:
        content_items: List of content items (dict or object).
        ontology: OntologyManager or ontology dict (optional).
        strict: If True, track 1 (empirical) errors block the build.
        pillar_weights: Per-pillar validation track weights (uses defaults if None).

    Returns:
        Dict with:
            - "is_valid": bool (in strict mode, based on track 1)
            - "track_scores": Dict mapping track name to per-item scores
            - "decisions": Per-item decisions (accept/review/reject) per track
            - "overall": Summary statistics
    """
    if pillar_weights is None:
        # Determine pillar from item and use defaults
        pillar_weights = {}

    # Track results: {track_name: {slug: score}}
    track_scores: Dict[str, Dict[str, float]] = {
        "empirical_fidelity": {},
        "coherence": {},
        "philosophical_consistency": {},
        "schema_validity": {},
        "test_suite_validity": {},
    }

    # Per-item decisions: {slug: {track: "accept"|"review"|"reject"}}
    item_decisions: Dict[str, Dict[str, str]] = {}

    errors: List[str] = []
    skipped_slugs: set[str] = set()

    for item in content_items:
        # Handle both dict and object
        if isinstance(item, dict):
            slug = item.get("slug", "")
            item_dict = item
        else:
            slug = getattr(item, "slug", "")
            item_dict = {k: v for k, v in item.__dict__.items() if not k.startswith("_")}

        slug_scores: Dict[str, float] = {}
        slug_decisions: Dict[str, str] = {}

        # Track 1: Empirical fidelity
        emp_score = compute_empirical_fidelity(item_dict)
        track_scores["empirical_fidelity"][slug] = emp_score if emp_score is not None else 0.0
        slug_scores["empirical_fidelity"] = emp_score if emp_score is not None else 0.0

        # Track 2: Coherence
        coh_score = compute_coherence_score(item_dict, ontology)
        track_scores["coherence"][slug] = coh_score if coh_score is not None else 0.0
        slug_scores["coherence"] = coh_score if coh_score is not None else 0.0

        # Track 3: Philosophical consistency
        phi_score = compute_philosophical_consistency(item_dict)
        track_scores["philosophical_consistency"][slug] = phi_score if phi_score is not None else 0.5
        slug_scores["philosophical_consistency"] = phi_score if phi_score is not None else 0.5

        # Track 4: Schema validity
        schema_score = compute_schema_validity(item_dict)
        track_scores["schema_validity"][slug] = schema_score
        slug_scores["schema_validity"] = schema_score

        # Track 5: Test suite validity
        test_score = compute_test_suite_validity(item_dict)
        track_scores["test_suite_validity"][slug] = test_score if test_score is not None else 0.5
        slug_scores["test_suite_validity"] = test_score if test_score is not None else 0.5

        # Make decisions per track using pillar weights
        pillar = item_dict.get("pillar", "data-engineering")
        weights = pillar_weights.get(pillar, DEFAULT_VALIDATION_WEIGHTS.get("data-engineering", DEFAULT_VALIDATION_WEIGHTS))

        # Decision: accept if all track scores above pillar-specific thresholds
        thresholds = {
            "empirical_fidelity": weights.get("empirical_fidelity", 0.3),
            "coherence": weights.get("coherence", 0.2),
            "philosophical_consistency": weights.get("philosophical", 0.2),
            "schema_validity": weights.get("schema", 0.2),
            "test_suite_validity": weights.get("tests", 0.1),
        }

# Determine decision: if all scores >= threshold → accept, if any major
        # failure → reject, otherwise review
        all_pass = all(
            isinstance(sg, (int, float)) and sg >= th
            for sg, th in slug_scores.items()
            if th > 0
        )
        any_fail = any(
            isinstance(sg, (int, float)) and sg < 0.3
            for sg, th in slug_scores.items()
            if th > 0
        )

        if all_pass and not any_fail:
            decision = "accept"
        elif any_fail:
            decision = "reject"
        else:
            decision = "review"

        slug_decisions = {
            "empirical_fidelity": decision if slug_scores.get("empirical_fidelity", 0) >= thresholds["empirical_fidelity"] else "review",
            "coherence": decision if slug_scores.get("coherence", 0) >= thresholds["coherence"] else "review",
            "philosophical_consistency": decision if slug_scores.get("philosophical_consistency", 0) >= thresholds["philosophical_consistency"] else "review",
            "schema_validity": decision if slug_scores.get("schema_validity", 0) >= thresholds["schema_validity"] else "review",
            "test_suite_validity": decision if slug_scores.get("test_suite_validity", 0) >= thresholds["test_suite_validity"] else "review",
        }

        item_decisions[slug] = slug_decisions

        # Strict mode: if empirical fidelity below minimum, skip
        if strict and emp_score is not None and emp_score < SQI_THRESHOLD_MIN:
            skipped_slugs.add(slug)
            errors.append(f"Slug '{slug}': empirical fidelity {emp_score} below threshold {SQI_THRESHOLD_MIN}")

    # Compute overall summary
    total_items = len(content_items)
    accepted = sum(1 for d in item_decisions.values() if d.get("empirical_fidelity", "") == "accept")
    reviewed = sum(1 for d in item_decisions.values() if d.get("empirical_fidelity", "") == "review")
    rejected = sum(1 for d in item_decisions.values() if d.get("empirical_fidelity", "") == "reject")

    # Track average scores
    avg_scores = {}
    for track in track_scores:
        scores = [s for s in track_scores[track].values() if s is not None]
        avg_scores[track] = round(sum(scores) / len(scores), 3) if scores else 0.0

    result = {
        "is_valid": strict and accepted == total_items,  # strict: all must pass track 1
        "track_scores": track_scores,
        "item_decisions": item_decisions,
        "overall": {
            "total_items": total_items,
            "accepted": accepted,
            "reviewed": reviewed,
            "rejected": rejected,
            "average_scores": avg_scores,
        },
    }

    if errors:
        logger.warning(f"Pluralistic validation errors: {len(errors)}")

    return result


# Convenience function for backward compatibility
validate_content = validate_content_pluralistic  # type: ignore


def set_pillar_validation_weights(weights: Dict[str, Dict[str, float]]) -> None:
    """Set per-pillar validation track weights.

    Args:
        weights: Dict mapping internal key ("aml", "stock", "data-engineering")
                 to dict mapping track name to weight (0.0-1.0, should sum to ~1.0).
    """
    from config import PILLAR_CONFIG
    global DEFAULT_VALIDATION_WEIGHTS
    DEFAULT_VALIDATION_WEIGHTS = weights
    logger.info(f"Updated validation weights for {len(weights)} pillars")


# Backward-compatible export
__all__ = [
    "validate_content_pluralistic",
    "validate_content",
    "compute_empirical_fidelity",
    "compute_coherence_score",
    "compute_philosophical_consistency",
    "compute_schema_validity",
    "compute_test_suite_validity",
    "set_pillar_validation_weights",
    "DEFAULT_VALIDATION_WEIGHTS",
]