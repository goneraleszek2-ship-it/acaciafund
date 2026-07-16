"""Tests for core/retention_engine.py — SM-2, gap detection, interleaving, data generation."""

import json
import tempfile
from pathlib import Path

import pytest

from core.retention_engine import (
    ConceptReviewItem,
    MasteryState,
    build_interleaved_session,
    calculate_mastery,
    detect_gaps,
    generate_concept_review_json,
    generate_concept_reviews,
    load_mastery_states_from_dict,
    mastery_label,
    save_concept_review_json,
    sm2_compute,
    sm2_next_due,
)

# ---------------------------------------------------------------------------
# SM-2 Algorithm
# ---------------------------------------------------------------------------


class TestSM2Compute:
    def test_again_resets_reps(self):
        ease, interval, reps = sm2_compute(0, 2.5, 10, 5)
        assert reps == 0
        assert interval == 1
        assert ease < 2.5

    def test_good_first_review(self):
        ease, interval, reps = sm2_compute(2, 2.5, 0, 0)
        assert reps == 1
        assert interval == 1
        assert ease > 2.5

    def test_good_second_review(self):
        ease, interval, reps = sm2_compute(2, 2.5, 1, 1)
        assert reps == 2
        assert interval == 6
        assert ease > 2.5

    def test_good_subsequent_review(self):
        ease, interval, reps = sm2_compute(2, 2.5, 6, 2)
        assert reps == 3
        assert interval == 15  # round(6 * 2.5)
        assert ease > 2.5

    def test_easy_increases_ease(self):
        _, _, reps_hard = sm2_compute(1, 2.5, 10, 5)
        _, _, reps_easy = sm2_compute(3, 2.5, 10, 5)
        assert reps_hard == 0  # hard resets
        assert reps_easy == 6  # easy increments

    def test_ease_floor_is_1_3(self):
        ease, _, _ = sm2_compute(1, 1.3, 1, 0)
        assert ease >= 1.3

    def test_hard_with_prior_reps(self):
        ease, interval, reps = sm2_compute(1, 2.5, 6, 3)
        assert reps == 0  # resets
        assert interval == 1

    def test_multiple_good_reviews_increase_interval(self):
        e, i, r = 2.5, 0, 0
        for _ in range(5):
            e, i, r = sm2_compute(2, e, i, r)
        assert r == 5
        assert i > 6  # interval grows


class TestSM2NextDue:
    def test_returns_future_timestamp(self):
        due = sm2_next_due(1)
        import time
        assert due > time.time() * 1000

    def test_larger_interval_returns_later(self):
        due1 = sm2_next_due(1)
        due7 = sm2_next_due(7)
        assert due7 > due1


# ---------------------------------------------------------------------------
# Mastery score computation
# ---------------------------------------------------------------------------


class TestCalculateMastery:
    def test_unseen_is_zero(self):
        state = MasteryState()
        assert calculate_mastery(state) == 0.0

    def test_after_one_review(self):
        state = MasteryState(reps=1, interval=1, ease=2.6)
        score = calculate_mastery(state)
        assert 0.0 < score < 1.0

    def test_after_many_reviews(self):
        state = MasteryState(reps=20, interval=90, ease=3.5)
        score = calculate_mastery(state)
        assert score > 0.8

    def test_increases_with_reps(self):
        low = calculate_mastery(MasteryState(reps=1, interval=1, ease=2.5))
        high = calculate_mastery(MasteryState(reps=10, interval=30, ease=2.8))
        assert high > low


class TestMasteryLabel:
    def test_unseen(self):
        assert mastery_label(0.0) == "unseen"

    def test_learning(self):
        assert mastery_label(0.15) == "learning"

    def test_reviewing(self):
        assert mastery_label(0.45) == "reviewing"

    def test_consolidating(self):
        assert mastery_label(0.7) == "consolidating"

    def test_mastered(self):
        assert mastery_label(0.9) == "mastered"


# ---------------------------------------------------------------------------
# Concept review item generation
# ---------------------------------------------------------------------------


class TestGenerateConceptReviews:
    @pytest.fixture
    def manager(self):
        from core.ontology import Concept, OntologyManager
        mgr = OntologyManager()
        mgr.add_concept(Concept(
            id="kyc", label="Know Your Customer", pillar="aml",
            description="Identity verification process",
            category="cdd-kyc", epistemic_status="regulatory",
            philosophical_lineage=["foucault_discipline"],
        ))
        mgr.add_concept(Concept(
            id="lob", label="Limit Order Book", pillar="stock",
            description="Order book mechanics",
            category="foundations", epistemic_status="constitutive",
        ))
        mgr.add_concept(Concept(
            id="etl", label="Extract-Transform-Load", pillar="data-engineering",
            description="Data pipeline pattern",
            category="foundations", epistemic_status="instrumental",
        ))
        return mgr

    def test_returns_all_concepts(self, manager):
        items = generate_concept_reviews(manager)
        assert len(items) == 3

    def test_item_structure(self, manager):
        items = generate_concept_reviews(manager)
        kyc = next(i for i in items if i.concept_slug == "kyc")
        assert kyc.label == "Know Your Customer"
        assert kyc.pillar == "aml"
        assert kyc.epistemic_status == "regulatory"
        assert "foucault_discipline" in kyc.philosophical_lineage

    def test_sorted_by_pillar_then_label(self, manager):
        items = generate_concept_reviews(manager)
        pillars = [i.pillar for i in items]
        assert pillars == sorted(pillars)

    def test_with_bloom_map(self, manager):
        items = generate_concept_reviews(manager, {"kyc": "analyze", "lob": "remember"})
        kyc = next(i for i in items if i.concept_slug == "kyc")
        assert kyc.bloom_level == "analyze"


class TestGenerateConceptReviewJson:
    @pytest.fixture
    def manager(self):
        from core.ontology import Concept, OntologyManager
        mgr = OntologyManager()
        mgr.add_concept(Concept(id="kyc", label="KYC", pillar="aml", description="Check"))
        return mgr

    def test_json_serializable(self, manager):
        result = generate_concept_review_json(manager)
        assert len(result) == 1
        assert result[0]["id"] == "concept:kyc"
        assert result[0]["conceptSlug"] == "kyc"
        assert result[0]["pillar"] == "aml"
        json.dumps(result)  # should not raise

    def test_camel_case_keys(self, manager):
        result = generate_concept_review_json(manager)
        item = result[0]
        assert "conceptSlug" in item
        assert "epistemicStatus" in item
        assert "philosophicalLineage" in item
        assert "bloomLevel" in item


class TestSaveConceptReviewJson:
    def test_writes_valid_json(self):
        items = [
            {"id": "concept:kyc", "conceptSlug": "kyc", "label": "KYC", "pillar": "aml",
             "definition": "test", "category": "cdd-kyc", "epistemicStatus": "",
             "philosophicalLineage": [], "bloomLevel": "remember",
             "sourceInspiration": "", "aliases": []},
        ]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            path = f.name
        try:
            save_concept_review_json(items, path)
            data = json.loads(Path(path).read_text(encoding="utf-8"))
            assert data["total"] == 1
            assert len(data["concepts"]) == 1
            assert "generatedAt" in data
        finally:
            Path(path).unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Gap detection
# ---------------------------------------------------------------------------


class TestDetectGaps:
    @pytest.fixture
    def review_items(self):
        return [
            ConceptReviewItem(id="concept:a", concept_slug="a", label="A",
                              pillar="aml", definition="", category=""),
            ConceptReviewItem(id="concept:b", concept_slug="b", label="B",
                              pillar="stock", definition="", category=""),
            ConceptReviewItem(id="concept:c", concept_slug="c", label="C",
                              pillar="data-engineering", definition="", category=""),
            ConceptReviewItem(id="concept:d", concept_slug="d", label="D",
                              pillar="aml", definition="", category=""),
        ]

    def test_all_unseen(self, review_items):
        report = detect_gaps(review_items, {})
        assert len(report.unseen_concepts) == 4
        assert report.total_gaps == 4

    def test_overdue_detection(self, review_items):
        import time
        states = {
            "concept:a": MasteryState(reps=5, interval=1, due=time.time() * 1000 - 10 * 86400000),
        }
        report = detect_gaps(review_items, states)
        assert len(report.unseen_concepts) == 3
        assert len(report.overdue_concepts) == 1
        assert report.total_gaps == 4

    def test_low_mastery_detection(self, review_items):
        import time
        states = {
            "concept:a": MasteryState(reps=1, interval=1, due=time.time() * 1000 + 86400000,
                                      ease=1.3),
        }
        report = detect_gaps(review_items, states, low_mastery_threshold=0.5)
        assert len(report.unseen_concepts) == 3
        assert len(report.low_mastery_concepts) == 1

    def test_no_gaps_with_high_mastery(self, review_items):
        import time
        states = {
            f"concept:{i}": MasteryState(reps=20, interval=90, ease=3.5,
                                         due=time.time() * 1000 + 86400000)
            for i in ["a", "b", "c", "d"]
        }
        report = detect_gaps(review_items, states)
        assert report.total_gaps == 0

    def test_pillar_breakdown(self, review_items):
        report = detect_gaps(review_items, {})
        assert report.pillar_breakdown.get("aml") == 2
        assert report.pillar_breakdown.get("stock") == 1
        assert report.pillar_breakdown.get("data-engineering") == 1


# ---------------------------------------------------------------------------
# Interleaved session building
# ---------------------------------------------------------------------------


class TestBuildInterleavedSession:
    @pytest.fixture
    def review_items(self):
        return [
            ConceptReviewItem(id=f"concept:{i}", concept_slug=str(i), label=f"Concept {i}",
                              pillar=p, definition="", category="")
            for i, p in enumerate(["aml", "stock", "data-engineering"] * 5)
        ]

    def test_returns_requested_size(self, review_items):
        session = build_interleaved_session(review_items, {}, session_size=5)
        assert len(session.items) == 5
        assert session.session_size == 5

    def test_includes_all_pillars(self, review_items):
        session = build_interleaved_session(review_items, {}, session_size=9)
        pillars = {i.pillar for i in session.items}
        assert "aml" in pillars
        assert "stock" in pillars
        assert "data-engineering" in pillars

    def test_prioritizes_due(self, review_items):
        import time
        states = {}
        for item in review_items[:5]:
            states[item.id] = MasteryState(reps=3, interval=1,
                                           due=time.time() * 1000 - 86400000)
        for item in review_items[5:]:
            states[item.id] = MasteryState(reps=3, interval=90,
                                           due=time.time() * 1000 + 86400000 * 30)
        session = build_interleaved_session(review_items, states, session_size=10)
        # Due items should be prioritized
        due_ids = {item.id for item in review_items[:5]}
        selected_ids = {item.id for item in session.items}
        assert len(due_ids & selected_ids) > 0

    def test_respects_max_per_pillar(self, review_items):
        session = build_interleaved_session(review_items, {}, session_size=15, max_per_pillar=2)
        from collections import Counter
        counts = Counter(i.pillar for i in session.items)
        for count in counts.values():
            assert count <= 2

    def test_empty_items(self):
        session = build_interleaved_session([], {}, session_size=5)
        assert len(session.items) == 0


# ---------------------------------------------------------------------------
# Mastery state deserialization
# ---------------------------------------------------------------------------


class TestLoadMasteryStates:
    def test_empty_dict(self):
        assert load_mastery_states_from_dict({}) == {}

    def test_converts_correctly(self):
        raw = {
            "concept:kyc": {
                "ease": 2.5, "interval": 6, "reps": 2,
                "due": 1000.0, "lastReview": 500.0,
                "qualityHistory": [2, 2],
            }
        }
        states = load_mastery_states_from_dict(raw)
        assert "concept:kyc" in states
        s = states["concept:kyc"]
        assert s.ease == 2.5
        assert s.interval == 6
        assert s.reps == 2
        assert s.due == 1000.0
        assert s.quality_history == [2, 2]
