"""Adaptive presentation engine — difficulty/interest/modality personalization.

Provides:
  UserProfile, ContentProfile, Recommendation — data models
  AdaptiveEngine — scores content relevance, adapts difficulty, recommends
  build_user_profile — factory for creating profiles from mastery data
  rank_content — convenience function for ranking content items
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DifficultyLevel = str  # "beginner" | "intermediate" | "advanced"
ModalityType = str     # "read" | "visual" | "interactive" | "mixed"

DIFFICULTY_MAP: Dict[str, int] = {
    "beginner": 1,
    "intermediate": 2,
    "advanced": 3,
}

DIFFICULTY_LABELS: Dict[int, str] = {
    1: "beginner",
    2: "intermediate",
    3: "advanced",
}

MODALITY_BY_DIFFICULTY: Dict[str, List[ModalityType]] = {
    "beginner": ["read", "visual"],
    "intermediate": ["read", "visual", "interactive"],
    "advanced": ["read", "interactive", "mixed"],
}

CONTENT_TYPE_MODALITY: Dict[str, ModalityType] = {
    "research": "read",
    "learn": "interactive",
    "knowledge": "visual",
}


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class ContentProfile:
    """Profile of a content item for adaptation."""

    slug: str
    pillar: str
    content_type: str
    difficulty: DifficultyLevel = "intermediate"
    concept_ids: List[str] = field(default_factory=list)
    concept_difficulties: Dict[str, int] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    sqi: float = 0.0
    title: str = ""
    description: str = ""


@dataclass
class UserProfile:
    """Profile of a user for personalization."""

    knowledge_levels: Dict[str, float] = field(default_factory=dict)
    pillar_interest: Dict[str, float] = field(default_factory=dict)
    modality_preference: ModalityType = "read"
    mastered_concepts: List[str] = field(default_factory=list)
    interest_concepts: List[str] = field(default_factory=list)
    content_history: List[str] = field(default_factory=list)
    last_active: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def get_knowledge_level(self, concept_id: str) -> float:
        return self.knowledge_levels.get(concept_id, 0.0)

    def get_pillar_interest(self, pillar: str) -> float:
        return self.pillar_interest.get(pillar, 0.5)

    def get_overall_difficulty(self) -> DifficultyLevel:
        avg = (
            sum(self.knowledge_levels.values()) / len(self.knowledge_levels)
            if self.knowledge_levels
            else 0.0
        )
        if avg >= 0.7:
            return "advanced"
        elif avg >= 0.4:
            return "intermediate"
        return "beginner"


@dataclass
class Recommendation:
    """A recommended content item with relevance score."""

    slug: str
    title: str
    score: float
    difficulty: DifficultyLevel
    modality: ModalityType
    reason: str
    pillar: str = ""
    content_type: str = ""
    concept_ids: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# AdaptiveEngine
# ---------------------------------------------------------------------------


class AdaptiveEngine:
    """Personalization engine for adaptive content presentation.

    Scores content relevance for a user based on:
    - Knowledge level match (difficulty alignment)
    - Concept interest overlap
    - Pillar interest alignment
    - Content quality (SQI bonus)
    - Modality preference
    """

    def __init__(self, user: Optional[UserProfile] = None):
        self.user = user or UserProfile()

    def set_user(self, user: UserProfile) -> None:
        self.user = user

    # --- Difficulty adaptation ---

    def adapt_difficulty(self, profile: ContentProfile) -> DifficultyLevel:
        """Recommend the best difficulty level for a user on this content."""
        user_diff = self.user.get_overall_difficulty()
        content_diff = profile.difficulty

        levels = ["beginner", "intermediate", "advanced"]
        user_idx = levels.index(user_diff)
        content_idx = levels.index(content_diff)

        diff = abs(user_idx - content_idx)

        if diff <= 1:
            return content_diff
        elif user_idx > content_idx:
            return user_diff
        return content_diff

    def suggest_modality(
        self,
        profile: ContentProfile,
        preferred_modality: Optional[ModalityType] = None,
    ) -> ModalityType:
        """Suggest the best learning modality for this content and user."""
        diff = profile.difficulty
        available = MODALITY_BY_DIFFICULTY.get(diff, ["read"])

        pref = preferred_modality or self.user.modality_preference
        if pref in available:
            return pref

        default = CONTENT_TYPE_MODALITY.get(profile.content_type, "read")
        if default in available:
            return default

        return available[0] if available else "read"

    # --- Scoring ---

    def score_content(self, profile: ContentProfile) -> float:
        """Score how relevant a content item is for the current user. [0, 1]."""
        score = 0.5

        concept_ids = profile.concept_ids
        if concept_ids:
            known = sum(
                self.user.get_knowledge_level(cid)
                for cid in concept_ids
                if self.user.get_knowledge_level(cid) > 0
            )
            possible = len(concept_ids)
            score += 0.2 * (known / possible) if possible else 0

        interest = self.user.get_pillar_interest(profile.pillar)
        score += 0.15 * (interest - 0.5)

        sqi_bonus = profile.sqi * 0.1
        score += sqi_bonus

        diff = self.adapt_difficulty(profile)
        user_diff = self.user.get_overall_difficulty()
        levels = ["beginner", "intermediate", "advanced"]
        diff_match = 1.0 - abs(levels.index(diff) - levels.index(user_diff)) / 2.0
        score += 0.15 * diff_match

        return max(0.0, min(1.0, score))

    def explain_reason(self, profile: ContentProfile) -> str:
        """Generate a human-readable reason for a recommendation."""
        parts: List[str] = []

        concept_ids = profile.concept_ids
        if concept_ids:
            known = [
                cid
                for cid in concept_ids
                if self.user.get_knowledge_level(cid) > 0
            ]
            if known:
                parts.append(
                    f"Builds on your knowledge of {known[0].replace('-', ' ')}"
                )
            unknown = [
                cid
                for cid in concept_ids
                if self.user.get_knowledge_level(cid) == 0
            ]
            if unknown:
                parts.append(
                    f"Introduces {unknown[0].replace('-', ' ')}"
                )

        interest = self.user.get_pillar_interest(profile.pillar)
        if interest >= 0.7:
            pillar_labels = {
                "aml": "Compliance",
                "stock": "Markets",
                "data-engineering": "Data Engineering",
            }
            parts.append(
                f"Matches your interest in {pillar_labels.get(profile.pillar, profile.pillar)}"
            )

        if profile.sqi >= 0.8:
            parts.append("High-quality content")

        return " — ".join(parts) if parts else "Recommended for you"

    # --- Recommendation ---

    def recommend(
        self,
        profiles: List[ContentProfile],
        top_n: int = 5,
        min_score: float = 0.0,
    ) -> List[Recommendation]:
        """Rank content profiles and return top-N recommendations."""
        scored: List[tuple[float, ContentProfile]] = []
        for p in profiles:
            s = self.score_content(p)
            if s >= min_score:
                scored.append((s, p))

        scored.sort(key=lambda x: -x[0])
        results: List[Recommendation] = []
        for score, p in scored[:top_n]:
            diff = self.adapt_difficulty(p)
            modality = self.suggest_modality(p)
            reason = self.explain_reason(p)
            results.append(
                Recommendation(
                    slug=p.slug,
                    title=p.title,
                    score=round(score, 2),
                    difficulty=diff,
                    modality=modality,
                    reason=reason,
                    pillar=p.pillar,
                    content_type=p.content_type,
                    concept_ids=p.concept_ids,
                )
            )
        return results


# ---------------------------------------------------------------------------
# Convenience functions
# ---------------------------------------------------------------------------


def build_user_profile(
    knowledge_levels: Optional[Dict[str, float]] = None,
    pillar_interest: Optional[Dict[str, float]] = None,
    modality_preference: ModalityType = "read",
    mastered_concepts: Optional[List[str]] = None,
    interest_concepts: Optional[List[str]] = None,
    content_history: Optional[List[str]] = None,
) -> UserProfile:
    """Build a UserProfile from explicit data.

    Args:
        knowledge_levels: dict of concept_id → mastery (0-1).
        pillar_interest: dict of pillar → interest (0-1).
        modality_preference: preferred learning modality.
        mastered_concepts: concepts the user already knows.
        interest_concepts: concepts the user is interested in.
        content_history: slugs of content viewed.

    Returns:
        UserProfile populated from the provided data.
    """
    return UserProfile(
        knowledge_levels=knowledge_levels or {},
        pillar_interest=pillar_interest or {},
        modality_preference=modality_preference,
        mastered_concepts=mastered_concepts or [],
        interest_concepts=interest_concepts or [],
        content_history=content_history or [],
    )


def build_content_profile(
    slug: str,
    pillar: str,
    content_type: str,
    difficulty: DifficultyLevel = "intermediate",
    concept_ids: Optional[List[str]] = None,
    concept_difficulties: Optional[Dict[str, int]] = None,
    tags: Optional[List[str]] = None,
    sqi: float = 0.0,
    title: str = "",
    description: str = "",
) -> ContentProfile:
    """Build a ContentProfile from content item data."""
    return ContentProfile(
        slug=slug,
        pillar=pillar,
        content_type=content_type,
        difficulty=difficulty,
        concept_ids=concept_ids or [],
        concept_difficulties=concept_difficulties or {},
        tags=tags or [],
        sqi=sqi,
        title=title,
        description=description,
    )


def rank_content(
    profiles: List[ContentProfile],
    user: Optional[UserProfile] = None,
    top_n: int = 5,
    min_score: float = 0.3,
) -> List[Recommendation]:
    """Rank content items for a user. Convenience wrapper around AdaptiveEngine.

    Args:
        profiles: List of ContentProfile for available content.
        user: UserProfile for personalization. Creates default if None.
        top_n: Maximum recommendations to return.
        min_score: Minimum relevance score threshold.

    Returns:
        Ranked list of Recommendations.
    """
    engine = AdaptiveEngine(user or UserProfile())
    return engine.recommend(profiles, top_n=top_n, min_score=min_score)
