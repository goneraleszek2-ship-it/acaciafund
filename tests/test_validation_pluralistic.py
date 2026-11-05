"""Tests for the pluralistic validation rubric (core/validation.py).

These tests guard the property that the rubric is able to *fail*: a known-bad
item must be rejected, an evidence-backed item accepted, and the aggregate
decision must not collapse into a single class.
"""

from core.validation import (
    ACCEPT_THRESHOLD,
    apply_validation_fields,
    compute_composite_score,
    compute_philosophical_consistency,
    compute_test_suite_validity,
    decide,
    validate_content_pluralistic,
)


class FakeOntology:
    """Minimal stand-in for OntologyManager used by coherence scoring."""

    def get_concept(self, tag):
        return {"id": tag} if tag.startswith("c") else None

    def relations_for(self, tag):
        return [1] if tag.startswith("c") else []


def _good_item(slug="data-engineering/research/good"):
    return {
        "slug": slug,
        "title": "A well-sourced, testable article",
        "content_type": "research",
        "pillar": "data-engineering",
        "tags": ["c1", "c2"],
        "signals": {"avg_sqi": 0.85},
        "sqi": 0.85,
        "source_verified": True,
        "source_breakdown": {"arxiv": 3},
        "bloom_questions": [{"q": "?"}],
        "flashcards": [{"front": "a", "back": "b"}],
        "epistemic_status": "empirically_verified",
        "way_of_knowing": "empirical",
        "verification_level": "test_suite_passed",
    }


def _bad_item(slug="data-engineering/research/bad"):
    return {
        "slug": slug,
        "title": "An empty, unsourced article",
        "content_type": "research",
        "pillar": "data-engineering",
        "tags": [],
    }


# ── Track 3: philosophical consistency ──

def test_philosophical_penalizes_unsourced_empirical_claim():
    unsourced = {"epistemic_status": "empirically_verified", "way_of_knowing": "empirical"}
    sourced = {
        "epistemic_status": "empirically_verified",
        "way_of_knowing": "empirical",
        "source_verified": True,
        "source_breakdown": {"arxiv": 1},
        "verification_level": "test_suite_passed",
    }
    unsourced_score = compute_philosophical_consistency(unsourced)
    sourced_score = compute_philosophical_consistency(sourced)
    assert unsourced_score is not None and sourced_score is not None
    assert unsourced_score < sourced_score
    assert sourced_score == 1.0


def test_philosophical_returns_none_without_metadata():
    assert compute_philosophical_consistency({"slug": "x"}) is None


# ── Track 5: test-suite validity ──

def test_test_suite_validity_reflects_artifacts():
    assert compute_test_suite_validity({"bloom_questions": [], "flashcards": []}) == 0.0
    assert compute_test_suite_validity(_good_item()) == 1.0
    assert compute_test_suite_validity({"slug": "x"}) is None


# ── Decision helpers ──

def test_decide_rejects_on_schema_failure():
    assert decide(0.99, {"schema_validity": 0.0}) == "reject"


def test_decide_rejects_low_composite():
    scores = {"empirical_fidelity": 0.2, "coherence": 0.2, "philosophical_consistency": 0.5,
              "schema_validity": 1.0, "test_suite_validity": 0.5}
    assert decide(0.4, scores) == "reject"


def test_decide_accepts_high_composite():
    scores = {"empirical_fidelity": 0.8, "coherence": 0.9, "philosophical_consistency": 1.0,
              "schema_validity": 1.0, "test_suite_validity": 1.0}
    assert decide(0.9, scores) == "accept"


def test_composite_score_is_weighted_mean():
    values = {"a": 1.0, "b": 0.0}
    assert compute_composite_score(values, {"a": 0.5, "b": 0.5}) == 0.5
    assert compute_composite_score(values, {"a": 0.75, "b": 0.25}) == 0.75


# ── Aggregate behaviour ──

def test_aggregate_is_non_degenerate_and_rejects_bad_item():
    good = _good_item()
    bad = _bad_item()
    result = validate_content_pluralistic([good, bad], ontology=FakeOntology())
    overall = result["overall"]

    assert overall["accepted"] == 1
    assert overall["rejected"] == 1
    assert result["item_decisions"][good["slug"]]["overall"] == "accept"
    assert result["item_decisions"][bad["slug"]]["overall"] == "reject"
    assert set([overall["accepted"], overall["reviewed"], overall["rejected"]]) != {0}


def test_good_item_composite_crosses_accept_threshold():
    result = validate_content_pluralistic([_good_item()], ontology=FakeOntology())
    slug = _good_item()["slug"]
    assert result["composite_scores"][slug] >= ACCEPT_THRESHOLD


def test_strict_is_valid_requires_all_accepted():
    result = validate_content_pluralistic(
        [_good_item(), _bad_item()], ontology=FakeOntology(), strict=True
    )
    assert result["is_valid"] is False


def test_apply_validation_fields_persists_scores():
    good = _good_item()
    result = validate_content_pluralistic([good], ontology=FakeOntology())
    updated = apply_validation_fields([good], result)

    assert updated == 1
    assert good["empirical_fidelity"] is not None
    assert good["coherence_score"] == 1.0
    assert good["philosophical_consistency"] == 1.0
    assert good["validation_decision"] == "accept"
    assert "validation_composite" in good


# ── Schema: declared rubric fields + warn-mode unknown-field report ──

def test_schema_declares_rubric_fields():
    from schemas import ContentItem

    for field in (
        "empirical_fidelity",
        "coherence_score",
        "philosophical_consistency",
        "schema_validity",
        "test_suite_validity",
        "validation_composite",
        "validation_decision",
    ):
        assert field in ContentItem.known_fields()


def test_find_unknown_fields_reports_undeclared_keys():
    from schemas import find_unknown_fields

    item = {"slug": "x", "title": "t", "totally_undeclared": 1, "_private": 2}
    assert find_unknown_fields(item) == {"totally_undeclared"}
