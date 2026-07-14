"""Tests for core/score.py — scoring and signal computation."""

from datetime import datetime, timedelta, timezone

from core.score import (
    compute_signal_score,
    cross_pillar_count,
    engagement_score,
    entity_density,
    novelty_score,
    source_authority,
)


class TestSourceAuthority:
    def test_known_domain_returns_high_score(self):
        score = source_authority("https://arxiv.org/abs/1234")
        assert isinstance(score, float)
        assert score > 0

    def test_unknown_domain_returns_default(self):
        score = source_authority("https://example-unknown.com/test")
        assert score == 0.2

    def test_empty_url_returns_default(self):
        score = source_authority("")
        assert score == 0.2


class TestEngagementScore:
    def test_zero_points_returns_zero(self):
        story = {"points": 0, "created_at": datetime.now(timezone.utc).isoformat()}
        now = datetime.now(timezone.utc)
        assert engagement_score(story, now) == 0.0

    def test_positive_points_returns_positive(self):
        story = {"points": 50, "created_at": datetime.now(timezone.utc).isoformat()}
        now = datetime.now(timezone.utc)
        score = engagement_score(story, now)
        assert 0.0 < score <= 1.0

    def test_older_story_lower_score(self):
        now = datetime.now(timezone.utc)
        fresh = {"points": 100, "created_at": now.isoformat()}
        old = {"points": 100, "created_at": (now - timedelta(hours=72)).isoformat()}
        fresh_score = engagement_score(fresh, now)
        old_score = engagement_score(old, now)
        assert fresh_score > old_score

    def test_missing_created_at_uses_default(self):
        story = {"points": 10}
        now = datetime.now(timezone.utc)
        score = engagement_score(story, now)
        assert isinstance(score, float)


class TestNoveltyScore:
    def test_novel_title_returns_high(self):
        history = {"2024-01-01": {"python", "data", "science"}}
        score = novelty_score("quantum computing in bioinformatics", history)
        assert score > 0.5

    def test_duplicate_title_returns_low(self):
        history = {"2024-01-01": {"quantum", "computing", "bio"}}
        score = novelty_score("quantum computing in bio", history)
        assert score < 0.5

    def test_empty_title_returns_default(self):
        score = novelty_score("", {"2024-01-01": {"test"}})
        assert score == 0.5


class TestCrossPillarCount:
    def test_returns_integer(self):
        count = cross_pillar_count("Test Title", "https://example.com")
        assert isinstance(count, int)
        assert count >= 0


class TestEntityDensity:
    def test_empty_title_returns_zero(self):
        assert entity_density("") == 0.0

    def test_returns_float(self):
        score = entity_density("Test about AML and KYC compliance")
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0


class TestComputeSignalScore:
    def test_returns_dict_with_expected_keys(self):
        story = {
            "title": "Test Article",
            "url": "https://example.com",
            "points": 10,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        now = datetime.now(timezone.utc)
        result = compute_signal_score(story, history={}, now=now)
        expected_keys = {"sqi", "engagement", "authority", "novelty", "timeliness", "cross_pillar", "entity_density"}
        assert set(result.keys()) == expected_keys

    def test_sqi_is_within_bounds(self):
        story = {
            "title": "Test",
            "url": "https://example.com",
            "points": 10,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        now = datetime.now(timezone.utc)
        result = compute_signal_score(story, history={}, now=now)
        assert 0.0 <= result["sqi"] <= 1.0

    def test_all_sub_scores_are_floats(self):
        story = {
            "title": "Test",
            "url": "https://example.com",
            "points": 10,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        now = datetime.now(timezone.utc)
        result = compute_signal_score(story, history={}, now=now)
        for key in ("engagement", "authority", "novelty", "timeliness", "entity_density"):
            assert isinstance(result[key], float), f"{key} is not float"

    def test_missing_fields_do_not_crash(self):
        result = compute_signal_score({}, history={}, now=datetime.now(timezone.utc))
        assert isinstance(result, dict)
