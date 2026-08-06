"""Tests for core/diagnostic.py (Tier 2.4 diagnostic placement quiz)."""

from core.diagnostic import (
    DIAGNOSTIC_QUESTIONS,
    PILLARS,
    build_payload,
    compute_placement,
)


def test_bank_has_nine_questions():
    assert len(DIAGNOSTIC_QUESTIONS) == 9


def test_bank_covers_all_pillars_and_tiers():
    pairs = {(q["pillar"], q["tier"]) for q in DIAGNOSTIC_QUESTIONS}
    assert len(pairs) == 9
    for pillar, _ in PILLARS:
        for tier in ("beginner", "intermediate", "expert"):
            assert (pillar, tier) in pairs


def test_every_question_is_valid_mc():
    allowed_prefix = {
        "aml": ("aml/", "compliance/"),
        "stock": ("markets/", "stock/"),
        "data-engineering": ("data/", "data-engineering/"),
    }
    for q in DIAGNOSTIC_QUESTIONS:
        assert len(q["options"]) == 4
        assert 0 <= q["correct"] < 4
        assert q["question"].strip()
        assert q["rationale"].strip()
        assert q["module"].startswith(allowed_prefix[q["pillar"]])


def test_all_module_links_exist_in_registry():
    import json

    reg = json.load(open("registry.json"))
    slugs = {i["slug"] for i in reg["content"]}
    for q in DIAGNOSTIC_QUESTIONS:
        assert q["module"] in slugs, q["module"]


def test_placement_thresholds():
    assert compute_placement(0) == "beginner"
    assert compute_placement(3) == "beginner"
    assert compute_placement(4) == "intermediate"
    assert compute_placement(6) == "intermediate"
    assert compute_placement(7) == "expert"
    assert compute_placement(9) == "expert"


def test_placement_with_explicit_total():
    assert compute_placement(5, 10) == "intermediate"
    assert compute_placement(8, 10) == "expert"


def test_payload_shape():
    payload = build_payload()
    assert payload["total"] == 9
    assert len(payload["pillars"]) == 3
    assert payload["levels"] == ["beginner", "intermediate", "expert"]
    assert len(payload["questions"]) == 9
