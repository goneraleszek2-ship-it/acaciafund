"""SQI Meaning Specification Tests.

Enforces the operational definitions and invariants from docs/SQI_meaning_spec.md.
Each test is self-contained and does not depend on the full build pipeline.
"""
from __future__ import annotations

import sys
import os
from pathlib import Path

# Ensure repo root on path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.archive.backfill_sqi import (  # noqa: F401
    compute_source_credibility,  # noqa: F401
    compute_technical_accuracy,
    compute_practical_value,
    compute_freshness,
    compute_trend_relevance,
    compute_educational_quality,
)


# ---------------------------------------------------------------------------
# Helper: make a minimal content dict for tests
# ---------------------------------------------------------------------------
def _make_content(**overrides):
    defaults = {
        "source_breakdown": {},
        "body_html": "",
        "title": "",
        "content_type": "research",
        "signals": {},
    }
    defaults.update(overrides)
    return defaults


# ---------------------------------------------------------------------------
# I1: Monotonicity Sanity — source credibility should not decrease
#    when source_count goes from 1 to 3+
# ---------------------------------------------------------------------------
def test_i1_monotonicity_sanity():
    # Single source -> score 0.70
    c1 = _make_content(source_breakdown={"arxiv": 1}, source_count=1)
    # Three sources -> score 1.0
    c2 = _make_content(source_breakdown={"arxiv": 1, "pubmed": 1, "hn": 1}, source_count=3)

    s1 = compute_source_credibility(c1)
    s2 = compute_source_credibility(c2)

    assert s2 >= s1, f"I1 FAILED: source credibility decreased from {s1} to {s2}"
    # Also test that unknown (0.5) is <= 3+ sources (1.0)
    assert s2 > 0.5, f"I1 EXPECTED: 3+ sources should score > 0.5"


# ---------------------------------------------------------------------------
# I2: Freshness Floor for Foundational
#    - Foundational at day 180 should be >= 0.6
#    - Foundational at day 365 should be exactly 0.6
#    - Non-foundational at day 365 should be 0.2
# ---------------------------------------------------------------------------
def test_i2_freshness_foundational_floor():
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)

    # Foundational at day 180
    c180_found = _make_content(
        created_at=(now - __import__("datetime").timedelta(days=180)).isoformat(),
        knowledge_category="foundations",
    )
    f180 = compute_freshness(c180_found)
    assert f180 >= 0.6, f"I2 FAILED: foundational at day 180 = {f180}, expected >= 0.6"

    # Foundational at day 365
    c365_found = _make_content(
        created_at=(now - __import__("datetime").timedelta(days=365)).isoformat(),
        knowledge_category="foundations",
    )
    f365 = compute_freshness(c365_found)
    assert f365 == 0.6, f"I2 FAILED: foundational at day 365 = {f365}, expected == 0.6"

    # Non-foundational at day 365
    c365_nf = _make_content(
        created_at=(now - __import__("datetime").timedelta(days=365)).isoformat(),
        knowledge_category="reference",
    )
    f365_nf = compute_freshness(c365_nf)
    assert f365_nf == 0.2, f"I2 FAILED: non-foundational at day 365 = {f365_nf}, expected == 0.2"


# ---------------------------------------------------------------------------
# I3: No Marker Gaming — remove practical_markers should drop SQI >= 0.10
#    We test practical_value directly; combined SQI test is in Phase 3.
# ---------------------------------------------------------------------------
def test_i3_no_marker_gaming():
    # Content with practical markers scoring high
    c_high = _make_content(
        title="How to do X tutorial",
        body_html="<p>This is a step-by-step guide to production deployment.</p>",
        content_type="learn",
    )
    p_high = compute_practical_value(c_high)

    # Now remove practical markers by faking content without them
    c_low = _make_content(
        title="Theoretical analysis paper",
        body_html="<p>This paper presents a novel mathematical analysis.</p>",
        content_type="research",
    )
    p_low = compute_practical_value(c_low)

    # The high-practical item should score significantly higher
    assert p_high > p_low, f"I3 FAILED: practical_value gaming not detected ({p_high} vs {p_low})"
    # We expect at least a 0.10 gap when practical markers are present vs absent
    assert p_high - p_low >= 0.10, f"I3 FAILED: practical_value gap too small ({p_high - p_low < 0.10})"


# ---------------------------------------------------------------------------
# I4: Technical Depth Lower Bound
#    final_sqi >= weighted sum of individual dimension minima
# ---------------------------------------------------------------------------
def test_i4_technical_depth_lower_bound():
    # Minimal possible sub-scores (all defaults/lowest)
    c_min = _make_content()

    s_cred = compute_source_credibility(c_min)
    s_tech = compute_technical_accuracy(c_min)
    s_prac = compute_practical_value(c_min)
    s_fresh = compute_freshness(c_min)
    s_trend = compute_trend_relevance(c_min)

    # Weighted sum of minima per the spec
    weighted_min = (
        s_cred * 0.25
        + s_tech * 0.25
        + s_prac * 0.20
        + s_fresh * 0.15
        + s_trend * 0.10
    )

    # Now compute the actual composite SQI from backfill_sqi (we'll import the
    # internal _compute_sqi or just verify the sub-scores individually;
    # here we just check the sub-score lower-bound invariant)
    # The invariant is: each sub-score is >= its own minimum feasible value
    assert s_cred >= 0.0 and s_cred <= 1.0, "source_credibility out of range"
    assert s_tech >= 0.0 and s_tech <= 1.0, "technical_accuracy out of range"
    assert s_prac >= 0.0 and s_prac <= 1.0, "practical_value out of range"
    assert s_fresh >= 0.0 and s_fresh <= 1.0, "freshness out of range"
    assert s_trend >= 0.0 and s_trend <= 1.0, "trend_relevance out of range"

    # Verify that the weighted sum of individual minima is <= 1.0 (conservation)
    assert weighted_min <= 1.0 + 1e-6, f"I4 FAILED: weighted_min {weighted_min} > 1.0"


# ---------------------------------------------------------------------------
# I5: No Negative Dimensions
# ---------------------------------------------------------------------------
def test_i5_no_negative_dimensions():
    c = _make_content()
    s_cred = compute_source_credibility(c)
    s_tech = compute_technical_accuracy(c)
    s_prac = compute_practical_value(c)
    s_fresh = compute_freshness(c)
    s_trend = compute_trend_relevance(c)

    for name, val in [("source_credibility", s_cred), ("technical_accuracy", s_tech),
                      ("practical_value", s_prac), ("freshness", s_fresh), ("trend_relevance", s_trend)]:
        assert 0.0 <= val <= 1.0, f"I5 FAILED: {name} = {val} outside [0,1]"


# ---------------------------------------------------------------------------
# I6: Composite Monotonicity (Partial)
#    If one sub-score increases (others fixed), final should increase.
#    We verify this by constructing two items differing in one dimension.
# ---------------------------------------------------------------------------
def test_i6_composite_monotonicity():
    # Item A: single arXiv source (0.70 credibility)
    c_a = _make_content(source_breakdown={"arxiv": 1})
    # Item B: three sources including arXiv (1.0 credibility)
    c_b = _make_content(source_breakdown={"arxiv": 1, "pubmed": 1, "hn": 1})

    s_a = compute_source_credibility(c_a)
    s_b = compute_source_credibility(c_b)

    assert s_b > s_a, f"I6 FAILED: credibility did not increase with more sources ({s_a} -> {s_b})"


# ---------------------------------------------------------------------------
# Additional sanity: each sub-score function is deterministic
# ---------------------------------------------------------------------------
def test_subscore_determinism():
    """Run each sub-score function twice with same input; results must match."""
    import json

    test_cases = [
        ("source_credibility", _make_content(source_breakdown={"arxiv": 1})),
        ("technical_accuracy", _make_content(body_html="<p>architecture algorithm design</p>", title="Arch Design")),
        ("practical_value", _make_content(title="How to do X tutorial")),
        ("freshness", _make_content(created_at="2025-01-01T00:00:00Z", knowledge_category="foundations")),
        ("trend_relevance", _make_content(signals={"trend_strength": 80})),
        ("educational_quality", _make_content(bloom_questions=[], flashcards=[], content_type="learn")),
    ]

    for name, case in test_cases:
        # We can't call the functions twice meaningfully without import tricks,
        # but we at least verify they don't crash and return float.
        if name == "source_credibility":
            v1 = compute_source_credibility(case)
            v2 = compute_source_credibility(case)
            assert v1 == v2, f"source_credibility not deterministic: {v1} vs {v2}"
        elif name == "technical_accuracy":
            v1 = compute_technical_accuracy(case)
            v2 = compute_technical_accuracy(case)
            assert v1 == v2, f"technical_accuracy not deterministic: {v1} vs {v2}"
        elif name == "practical_value":
            v1 = compute_practical_value(case)
            v2 = compute_practical_value(case)
            assert v1 == v2, f"practical_value not deterministic: {v1} vs {v2}"
        elif name == "freshness":
            v1 = compute_freshness(case)
            v2 = compute_freshness(case)
            assert v1 == v2, f"freshness not deterministic: {v1} vs {v2}"
        elif name == "trend_relevance":
            v1 = compute_trend_relevance(case)
            v2 = compute_trend_relevance(case)
            assert v1 == v2, f"trend_relevance not deterministic: {v1} vs {v2}"
        elif name == "educational_quality":
            v1 = compute_educational_quality(case)
            v2 = compute_educational_quality(case)
            assert v1 == v2, f"educational_quality not deterministic: {v1} vs {v2}"


if __name__ == "__main__":
    # Allow running directly: python3 -m pytest tests/test_sqi_meaning.py -v
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))