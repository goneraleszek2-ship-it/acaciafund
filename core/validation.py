"""Pluralistic content validation for AcaciaFund build pipeline.

This module provides multiple parallel validation tracks (instead of a single
gate), allowing different evidentiary standards to be evaluated simultaneously.

Western empirical philosophy is one track among many: empirically_verified,
theoretical, contemplative, and authority_based. Each track produces a score,
and no single track can gatekeep others.

Configuration is in config.py per-pillar weights.
"""

from typing import Any, Dict, List, Optional

from config import SQI_THRESHOLD_MIN

logger = __import__("logging").getLogger(__name__)

ALLOWED_CONTENT_TYPES = {"research", "learn", "knowledge"}

# Validation track weights per pillar (configurable via config.py PILLAR_VALIDATION_WEIGHTS)
# Default: equal weighting across all 5 tracks
DEFAULT_VALIDATION_WEIGHTS: Dict[str, Dict[str, float]] = {
    "aml": {"empirical_fidelity": 0.3, "coherence": 0.2, "philosophical": 0.2, "schema": 0.2, "tests": 0.1},
    "stock": {"empirical_fidelity": 0.3, "coherence": 0.2, "philosophical": 0.2, "schema": 0.2, "tests": 0.1},
    "data-engineering": {"empirical_fidelity": 0.25, "coherence": 0.25, "philosophical": 0.2, "schema": 0.2, "tests": 0.1},
}

# Decision thresholds for the pluralistic rubric.
#
# These are *thresholds*, not weights. The earlier implementation conflated the
# per-pillar track weights (0.1-0.3) with decision thresholds, which forced every
# item into "review" and made the rubric incapable of accepting or rejecting.
#
# Calibration (over 261 registry items):
#   composite = weighted mean of the 5 track scores using normalized pillar weights.
#   * reject  : schema invalid, OR composite < REJECT_THRESHOLD,
#               OR any track below HARD_FLOOR.
#   * accept  : composite >= ACCEPT_THRESHOLD AND every track >= TRACK_FLOOR.
#   * review  : otherwise.
ACCEPT_THRESHOLD = 0.75  # composite at/above which an item may be accepted
REJECT_THRESHOLD = 0.45  # composite below which an item is rejected
TRACK_FLOOR = 0.30  # per-track minimum required for acceptance
HARD_FLOOR = 0.10  # per-track level that forces rejection

# Mapping of rubric track names to the per-item registry field names.
TRACK_TO_FIELD: Dict[str, str] = {
    "empirical_fidelity": "empirical_fidelity",
    "coherence": "coherence_score",
    "philosophical_consistency": "philosophical_consistency",
    "schema_validity": "schema_validity",
    "test_suite_validity": "test_suite_validity",
}

# Cached ontology manager (loading ontology.json per item is prohibitively slow).
_ONTOLOGY_CACHE: Any = None


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

    # Simple average of the available components.
    score = sum(val for _, val in components) / len(components)
    return round(min(max(score, 0.0), 1.0), 3)


def _load_ontology_manager(ontology: Optional[Any] = None) -> Any:
    """Return an OntologyManager, using the passed object or a cached default.

    Loading `data/ontology.json` on every item is prohibitively slow; the
    manager is cached at module level.
    """
    global _ONTOLOGY_CACHE
    if ontology is not None:
        # Accept either an OntologyManager or a raw ontology dict.
        if hasattr(ontology, "get_concept"):
            return ontology
        from core.ontology import OntologyManager

        mgr = OntologyManager()
        if isinstance(ontology, dict):
            mgr.from_dict(ontology)
        return mgr
    if _ONTOLOGY_CACHE is None:
        from core.ontology import OntologyManager

        _ONTOLOGY_CACHE = OntologyManager.load("data/ontology.json")
    return _ONTOLOGY_CACHE


def compute_coherence_score(item: Dict[str, Any], ontology: Optional[Dict] = None) -> Optional[float]:
    """Track 2: Coherence score - ontological consistency.

    Evaluates how well the content item fits within the ontology: the fraction
    of the item's concept tags that resolve to ontology concepts which carry at
    least one canonical relation. High coherence = extracted concepts align with
    an existing, connected ontology structure.
    """
    concept_tags = item.get("tags", [])
    if not concept_tags:
        return None

    try:
        m = _load_ontology_manager(ontology)
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

        coherence = aligned / extracted
        return round(min(max(coherence, 0.0), 1.0), 3)
    except Exception as e:
        logger.warning(f"Coherence score computation failed: {e}")
        return None


def compute_philosophical_consistency(item: Dict[str, Any]) -> Optional[float]:
    """Track 3: Philosophical consistency - metadata/evidence compatibility.

    This is *not* a truth check. It scores whether an item's own epistemic
    claims are internally coherent and backed by the evidence those claims
    require. Crucially, an item asserting ``empirically_verified`` knowledge
    without any verifiable source is penalized: a claim that names an evidence
    standard must meet it.

    Returns a score in [0, 1], or None if the item carries no epistemic metadata.
    """
    epistemic_status = item.get("epistemic_status")
    way_of_knowing = item.get("way_of_knowing")
    verification_level = item.get("verification_level")

    if not any([epistemic_status, way_of_knowing, verification_level]):
        return None

    epistemic_status = epistemic_status or "empirically_verified"
    way_of_knowing = way_of_knowing or "empirical"

    alignment_map = {
        ("empirically_verified", "empirical"): 1.0,
        ("theoretical", "empirical"): 0.7,
        ("theoretical", "rational"): 1.0,
        ("contemplative", "contemplative"): 1.0,
        ("contemplative", "intuitive"): 0.8,
        ("authority_based", "authority"): 1.0,
        ("authority_based", "testimonial"): 0.8,
        ("empirically_verified", "contemplative"): 0.3,
        ("pragmatic", "empirical"): 0.8,
    }

    factors: List[float] = []
    factors.append(alignment_map.get((epistemic_status, way_of_knowing), 0.5))

    # Evidence backing: a claim to empirical verification must carry a source.
    has_evidence = bool(item.get("source_verified")) and (
        bool(item.get("source_breakdown")) or bool(item.get("citations"))
    )
    if epistemic_status == "empirically_verified":
        factors.append(1.0 if has_evidence else 0.2)
    elif epistemic_status in ("authority_based", "authority"):
        has_sources = (
            bool(item.get("citations"))
            or bool(item.get("source_inspiration"))
            or bool(item.get("philosophical_sources"))
        )
        factors.append(1.0 if has_sources else 0.4)

    # verification_level must cohere with the declared epistemic_status.
    coherent_levels: Dict[str, set] = {
        "empirically_verified": {"test_suite_passed", "source_verified", "peer_reviewed", "verified"},
        "theoretical": {"formal_proof", "internal_consistency", "not_verified", "reasoned"},
        "authority_based": {"cited", "not_verified", "attributed"},
        "contemplative": {"introspective", "not_verified"},
        "pragmatic": {"field_tested", "not_verified"},
    }
    if verification_level:
        allowed = coherent_levels.get(epistemic_status)
        if allowed is not None:
            factors.append(1.0 if verification_level in allowed else 0.4)

    # Presence of a documented philosophical lineage indicates structured metadata.
    if item.get("philosophical_lineage"):
        factors.append(0.9)

    score = sum(factors) / len(factors)
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
    """Track 5: Test suite validity - per-item testable artifacts.

    The item's "test suite" is the set of generated testable artifacts the
    cognitive architecture attaches to a page: Bloom questions (active-recall
    checks) and flashcards (spaced-retrieval cards). An item without these has
    no testable surface and scores low; SQI is included only as a supporting
    signal.

    Returns a score in [0, 1], or None if the item carries no testable signals.
    """
    signals: List[float] = []

    bloom_questions = item.get("bloom_questions")
    if bloom_questions is not None:
        signals.append(1.0 if bloom_questions else 0.0)

    flashcards = item.get("flashcards")
    if flashcards is not None:
        signals.append(1.0 if flashcards else 0.0)

    sqi = item.get("sqi")
    if sqi is not None:
        try:
            sqi_val = float(sqi)
            if sqi_val >= SQI_THRESHOLD_MIN:
                signals.append(1.0)
            elif sqi_val > 0:
                signals.append(0.5)
            else:
                signals.append(0.0)
        except (ValueError, TypeError):
            signals.append(0.0)

    if not signals:
        return None

    return round(sum(signals) / len(signals), 3)


def compute_composite_score(
    track_values: Dict[str, float], weights: Dict[str, float]
) -> float:
    """Weighted mean of track scores using normalized weights.

    Track values missing from `weights` (or with zero weight) are ignored.
    Returns a value in [0, 1].
    """
    weight_sum = sum(weights.get(k, 0.0) for k in track_values)
    if weight_sum <= 0:
        return 0.0
    composite = sum(track_values[k] * weights.get(k, 0.0) for k in track_values) / weight_sum
    return round(min(max(composite, 0.0), 1.0), 3)


def decide(composite: float, track_scores: Dict[str, float]) -> str:
    """Aggregate a per-item decision from the composite and track scores.

    A rubric that cannot reject is not a rubric: this function is what lets the
    system register failure.
    """
    if track_scores.get("schema_validity", 1.0) < 1.0:
        return "reject"
    if composite < REJECT_THRESHOLD or any(s < HARD_FLOOR for s in track_scores.values()):
        return "reject"
    if composite >= ACCEPT_THRESHOLD and all(s >= TRACK_FLOOR for s in track_scores.values()):
        return "accept"
    return "review"


def _track_decision(score: float) -> str:
    """Per-track decision label, independent of the aggregate decision."""
    if score >= ACCEPT_THRESHOLD:
        return "accept"
    if score < TRACK_FLOOR:
        return "reject"
    return "review"


def validate_content_pluralistic(
    content_items: List[Any],
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
    # Per-item composite score: {slug: float}
    composite_scores: Dict[str, float] = {}

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
        schema_score = 0.0 if schema_score is None else schema_score
        track_scores["schema_validity"][slug] = schema_score
        slug_scores["schema_validity"] = schema_score

        # Track 5: Test suite validity
        test_score = compute_test_suite_validity(item_dict)
        track_scores["test_suite_validity"][slug] = test_score if test_score is not None else 0.5
        slug_scores["test_suite_validity"] = test_score if test_score is not None else 0.5

        # Composite decision using normalized per-pillar weights.
        pillar = item_dict.get("pillar", "data-engineering")
        weights = pillar_weights.get(
            pillar, DEFAULT_VALIDATION_WEIGHTS.get(pillar, DEFAULT_VALIDATION_WEIGHTS["data-engineering"])
        )
        composite = compute_composite_score(slug_scores, weights)
        composite_scores[slug] = composite

        slug_decisions = {track: _track_decision(score) for track, score in slug_scores.items()}
        slug_decisions["overall"] = decide(composite, slug_scores)
        item_decisions[slug] = slug_decisions

        # Strict mode: if empirical fidelity below minimum, skip
        if strict and emp_score is not None and emp_score < SQI_THRESHOLD_MIN:
            skipped_slugs.add(slug)
            errors.append(f"Slug '{slug}': empirical fidelity {emp_score} below threshold {SQI_THRESHOLD_MIN}")

    # Compute overall summary from the aggregate decision.
    total_items = len(content_items)
    accepted = sum(1 for d in item_decisions.values() if d.get("overall") == "accept")
    reviewed = sum(1 for d in item_decisions.values() if d.get("overall") == "review")
    rejected = sum(1 for d in item_decisions.values() if d.get("overall") == "reject")

    # Track average scores
    avg_scores = {}
    for track in track_scores:
        scores = [s for s in track_scores[track].values() if s is not None]
        avg_scores[track] = round(sum(scores) / len(scores), 3) if scores else 0.0

    composite_values = list(composite_scores.values())
    avg_composite = round(sum(composite_values) / len(composite_values), 3) if composite_values else 0.0

    result = {
        "is_valid": strict and rejected == 0 and accepted == total_items,
        "track_scores": track_scores,
        "item_decisions": item_decisions,
        "composite_scores": composite_scores,
        "overall": {
            "total_items": total_items,
            "accepted": accepted,
            "reviewed": reviewed,
            "rejected": rejected,
            "average_composite": avg_composite,
            "average_scores": avg_scores,
        },
    }

    if errors:
        logger.warning(f"Pluralistic validation errors: {len(errors)}")

    return result


# Convenience function for backward compatibility
validate_content = validate_content_pluralistic  # type: ignore


def apply_validation_fields(
    content_items: List[Any], result: Dict[str, Any]
) -> int:
    """Persist rubric results onto registry item dicts, in place.

    Writes the five track scores, the composite score, and the aggregate
    decision onto each matching dict item. Object items are left untouched
    (they are not the registry representation). Returns the number of items
    updated.
    """
    track_scores = result.get("track_scores", {})
    decisions = result.get("item_decisions", {})
    composites = result.get("composite_scores", {})

    updated = 0
    for item in content_items:
        if not isinstance(item, dict):
            continue
        slug = item.get("slug")
        if not slug or slug not in decisions:
            continue

        item["empirical_fidelity"] = track_scores.get("empirical_fidelity", {}).get(slug)
        item["coherence_score"] = track_scores.get("coherence", {}).get(slug)
        item["philosophical_consistency"] = track_scores.get("philosophical_consistency", {}).get(slug)
        item["schema_validity"] = track_scores.get("schema_validity", {}).get(slug)
        item["test_suite_validity"] = track_scores.get("test_suite_validity", {}).get(slug)
        item["validation_composite"] = composites.get(slug)
        item["validation_decision"] = decisions.get(slug, {}).get("overall")
        updated += 1

    return updated


def set_pillar_validation_weights(weights: Dict[str, Dict[str, float]]) -> None:
    """Set per-pillar validation track weights.

    Args:
        weights: Dict mapping internal key ("aml", "stock", "data-engineering")
                 to dict mapping track name to weight (0.0-1.0, should sum to ~1.0).
    """
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
    "compute_composite_score",
    "apply_validation_fields",
    "decide",
    "set_pillar_validation_weights",
    "DEFAULT_VALIDATION_WEIGHTS",
    "ACCEPT_THRESHOLD",
    "REJECT_THRESHOLD",
    "TRACK_FLOOR",
    "HARD_FLOOR",
]
