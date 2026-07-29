"""Tests for core/adaptive.py — adaptive difficulty/interest/modality engine."""

import pytest

from core.adaptive import (
    AdaptiveEngine,
    ContentProfile,
    Recommendation,
    UserProfile,
    build_content_profile,
    build_user_profile,
    rank_content,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def beginner_user():
    return UserProfile(
        knowledge_levels={"kyc": 0.1, "aml": 0.2},
        pillar_interest={"aml": 0.8, "stock": 0.3, "data-engineering": 0.2},
        modality_preference="visual",
    )


@pytest.fixture
def advanced_user():
    return UserProfile(
        knowledge_levels={"kyc": 0.9, "aml": 0.85, "hft": 0.8},
        pillar_interest={"aml": 0.6, "stock": 0.9, "data-engineering": 0.7},
        modality_preference="interactive",
        mastered_concepts=["kyc", "aml"],
    )


@pytest.fixture
def sample_profiles():
    return [
        ContentProfile(
            slug="aml/kyc-basics",
            pillar="aml",
            content_type="learn",
            difficulty="beginner",
            concept_ids=["kyc"],
            sqi=0.9,
            title="KYC Basics",
        ),
        ContentProfile(
            slug="aml/advanced-aml",
            pillar="aml",
            content_type="research",
            difficulty="advanced",
            concept_ids=["aml", "kyc"],
            sqi=0.7,
            title="Advanced AML Techniques",
        ),
        ContentProfile(
            slug="stock/hft-overview",
            pillar="stock",
            content_type="knowledge",
            difficulty="intermediate",
            concept_ids=["hft"],
            sqi=0.85,
            title="HFT Overview",
        ),
        ContentProfile(
            slug="data/streaming-pipelines",
            pillar="data-engineering",
            content_type="learn",
            difficulty="advanced",
            concept_ids=["streaming"],
            sqi=0.6,
            title="Streaming Pipelines",
        ),
    ]


@pytest.fixture
def engine():
    return AdaptiveEngine()


# ---------------------------------------------------------------------------
# UserProfile
# ---------------------------------------------------------------------------


class TestUserProfile:
    def test_get_knowledge_level_known(self):
        user = UserProfile(knowledge_levels={"kyc": 0.8})
        assert user.get_knowledge_level("kyc") == 0.8

    def test_get_knowledge_level_unknown(self):
        user = UserProfile()
        assert user.get_knowledge_level("nonexistent") == 0.0

    def test_get_pillar_interest_known(self):
        user = UserProfile(pillar_interest={"aml": 0.9})
        assert user.get_pillar_interest("aml") == 0.9

    def test_get_pillar_interest_default(self):
        user = UserProfile()
        assert user.get_pillar_interest("aml") == 0.5

    def test_overall_difficulty_beginner(self):
        user = UserProfile(knowledge_levels={"kyc": 0.1, "aml": 0.2})
        assert user.get_overall_difficulty() == "beginner"

    def test_overall_difficulty_intermediate(self):
        user = UserProfile(knowledge_levels={"kyc": 0.5, "aml": 0.4})
        assert user.get_overall_difficulty() == "intermediate"

    def test_overall_difficulty_advanced(self):
        user = UserProfile(knowledge_levels={"kyc": 0.9, "aml": 0.8})
        assert user.get_overall_difficulty() == "advanced"

    def test_overall_difficulty_empty(self):
        assert UserProfile().get_overall_difficulty() == "beginner"


# ---------------------------------------------------------------------------
# AdaptiveEngine — difficulty adaptation
# ---------------------------------------------------------------------------


class TestAdaptDifficulty:
    def test_same_difficulty(self, beginner_user):
        engine = AdaptiveEngine(beginner_user)
        profile = ContentProfile(slug="x", difficulty="beginner", pillar="aml", content_type="learn")
        assert engine.adapt_difficulty(profile) == "beginner"

    def test_one_step_apart(self, beginner_user):
        engine = AdaptiveEngine(beginner_user)
        profile = ContentProfile(slug="x", difficulty="intermediate", pillar="aml", content_type="learn")
        assert engine.adapt_difficulty(profile) == "intermediate"

    def test_two_steps_apart_user_lower(self, beginner_user):
        engine = AdaptiveEngine(beginner_user)
        profile = ContentProfile(slug="x", difficulty="advanced", pillar="aml", content_type="learn")
        assert engine.adapt_difficulty(profile) == "advanced"

    def test_two_steps_apart_user_higher(self):
        user = UserProfile(knowledge_levels={"kyc": 0.9})
        engine = AdaptiveEngine(user)
        profile = ContentProfile(slug="x", difficulty="beginner", pillar="aml", content_type="learn")
        assert engine.adapt_difficulty(profile) == "advanced"


# ---------------------------------------------------------------------------
# AdaptiveEngine — modality suggestion
# ---------------------------------------------------------------------------


class TestSuggestModality:
    def test_preferred_modality_available(self):
        user = UserProfile(modality_preference="visual")
        engine = AdaptiveEngine(user)
        profile = ContentProfile(slug="x", difficulty="beginner", pillar="aml", content_type="learn")
        assert engine.suggest_modality(profile) == "visual"

    def test_preferred_not_available(self):
        user = UserProfile(modality_preference="interactive")
        engine = AdaptiveEngine(user)
        profile = ContentProfile(slug="x", difficulty="beginner", pillar="aml", content_type="research")
        assert engine.suggest_modality(profile) == "read"

    def test_override_preferred(self):
        engine = AdaptiveEngine()
        profile = ContentProfile(slug="x", difficulty="beginner", pillar="aml", content_type="learn")
        assert engine.suggest_modality(profile, preferred_modality="interactive") == "read"


# ---------------------------------------------------------------------------
# AdaptiveEngine — scoring
# ---------------------------------------------------------------------------


class TestScoreContent:
    def test_high_relevance(self, beginner_user):
        engine = AdaptiveEngine(beginner_user)
        profile = ContentProfile(
            slug="aml/kyc-basics",
            pillar="aml",
            content_type="learn",
            difficulty="beginner",
            concept_ids=["kyc"],
            sqi=0.9,
        )
        score = engine.score_content(profile)
        assert score >= 0.6

    def test_low_relevance(self, beginner_user):
        engine = AdaptiveEngine(beginner_user)
        profile = ContentProfile(
            slug="data/obscure",
            pillar="data-engineering",
            content_type="research",
            difficulty="advanced",
            concept_ids=["obscure"],
            sqi=0.1,
        )
        score = engine.score_content(profile)
        assert score < 0.6

    def test_score_bounds(self, beginner_user):
        engine = AdaptiveEngine(beginner_user)
        profile = ContentProfile(
            slug="x", pillar="aml", content_type="learn",
            difficulty="beginner", sqi=0.0,
        )
        score = engine.score_content(profile)
        assert 0.0 <= score <= 1.0


# ---------------------------------------------------------------------------
# AdaptiveEngine — recommendation
# ---------------------------------------------------------------------------


class TestRecommend:
    def test_recommend_returns_sorted(self, beginner_user, sample_profiles):
        engine = AdaptiveEngine(beginner_user)
        recs = engine.recommend(sample_profiles, top_n=10)
        assert len(recs) <= len(sample_profiles)
        for i in range(len(recs) - 1):
            assert recs[i].score >= recs[i + 1].score

    def test_recommend_top_n(self, beginner_user, sample_profiles):
        engine = AdaptiveEngine(beginner_user)
        recs = engine.recommend(sample_profiles, top_n=2)
        assert len(recs) <= 2

    def test_recommend_min_score(self, beginner_user, sample_profiles):
        engine = AdaptiveEngine(beginner_user)
        recs = engine.recommend(sample_profiles, min_score=0.8)
        for r in recs:
            assert r.score >= 0.8

    def test_recommend_empty_profiles(self, beginner_user):
        engine = AdaptiveEngine(beginner_user)
        recs = engine.recommend([])
        assert recs == []

    def test_recommend_includes_reasons(self, beginner_user, sample_profiles):
        engine = AdaptiveEngine(beginner_user)
        recs = engine.recommend(sample_profiles, top_n=1)
        assert len(recs) == 1
        assert recs[0].reason
        assert "Compliance" in recs[0].reason

    def test_recommend_different_users(self, beginner_user, advanced_user):
        profiles = [
            ContentProfile(
                slug="aml/kyc-basics", pillar="aml", content_type="learn",
                difficulty="beginner", concept_ids=["kyc"], sqi=0.9,
            ),
            ContentProfile(
                slug="stock/hft-strategies", pillar="stock", content_type="learn",
                difficulty="advanced", concept_ids=["hft"], sqi=0.9,
            ),
            ContentProfile(
                slug="data/streaming", pillar="data-engineering", content_type="learn",
                difficulty="advanced", concept_ids=["streaming"], sqi=0.9,
            ),
        ]
        engine_b = AdaptiveEngine(beginner_user)
        engine_a = AdaptiveEngine(advanced_user)
        recs_b = engine_b.recommend(profiles, top_n=3)
        recs_a = engine_a.recommend(profiles, top_n=3)
        slugs_b = [r.slug for r in recs_b]
        slugs_a = [r.slug for r in recs_a]
        assert slugs_b != slugs_a


# ---------------------------------------------------------------------------
# build_user_profile
# ---------------------------------------------------------------------------


class TestBuildUserProfile:
    def test_build_basic(self):
        user = build_user_profile(
            knowledge_levels={"kyc": 0.8},
            pillar_interest={"aml": 0.9},
        )
        assert user.get_knowledge_level("kyc") == 0.8
        assert user.get_pillar_interest("aml") == 0.9
        assert user.get_overall_difficulty() == "advanced"

    def test_build_empty(self):
        user = build_user_profile()
        assert user.knowledge_levels == {}
        assert user.pillar_interest == {}
        assert user.modality_preference == "read"


# ---------------------------------------------------------------------------
# build_content_profile
# ---------------------------------------------------------------------------


class TestBuildContentProfile:
    def test_build_basic(self):
        profile = build_content_profile(
            slug="aml/kyc-basics",
            pillar="aml",
            content_type="learn",
            difficulty="beginner",
            concept_ids=["kyc"],
            sqi=0.9,
            title="KYC Basics",
        )
        assert profile.slug == "aml/kyc-basics"
        assert profile.difficulty == "beginner"
        assert profile.sqi == 0.9

    def test_build_minimal(self):
        profile = build_content_profile(slug="x", pillar="aml", content_type="research")
        assert profile.concept_ids == []
        assert profile.tags == []


# ---------------------------------------------------------------------------
# rank_content
# ---------------------------------------------------------------------------


class TestRankContent:
    def test_rank_returns_recommendations(self, sample_profiles):
        user = UserProfile(
            knowledge_levels={"kyc": 0.1},
            pillar_interest={"aml": 0.9},
        )
        recs = rank_content(sample_profiles, user=user, top_n=3)
        assert all(isinstance(r, Recommendation) for r in recs)
        assert len(recs) <= 3

    def test_rank_default_user(self, sample_profiles):
        recs = rank_content(sample_profiles, top_n=2)
        assert len(recs) <= 2

    def test_rank_empty(self):
        recs = rank_content([])
        assert recs == []
