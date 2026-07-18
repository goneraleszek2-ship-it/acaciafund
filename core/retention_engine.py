"""Retention & Retrieval — SM-2, gap detection, interleaved practice, Feynman review modes."""

from __future__ import annotations

import enum
import json
import random
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from core.ontology import OntologyManager

# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class ConceptReviewItem:
    """A concept ready for spaced-repetition review."""

    id: str
    concept_slug: str
    label: str
    pillar: str
    definition: str
    category: str
    epistemic_status: str = ""
    philosophical_lineage: List[str] = field(default_factory=list)
    bloom_level: str = "remember"
    source_inspiration: str = ""
    aliases: List[str] = field(default_factory=list)


@dataclass
class MasteryState:
    """Per-concept SM-2 state tracked in localStorage."""

    ease: float = 2.5
    interval: int = 0
    reps: int = 0
    due: float = 0.0
    last_review: float = 0.0
    quality_history: List[int] = field(default_factory=list)


@dataclass
class GapReport:
    """Identified gaps in a user's knowledge coverage."""

    unseen_concepts: List[ConceptReviewItem] = field(default_factory=list)
    overdue_concepts: List[ConceptReviewItem] = field(default_factory=list)
    low_mastery_concepts: List[ConceptReviewItem] = field(default_factory=list)
    pillar_breakdown: Dict[str, int] = field(default_factory=dict)
    total_gaps: int = 0


@dataclass
class InterleavedSession:
    """An interleaved practice session mixing concepts across pillars."""

    session_id: str
    items: List[ConceptReviewItem] = field(default_factory=list)
    pillar_order: List[str] = field(default_factory=list)
    session_size: int = 10


# ---------------------------------------------------------------------------
# Feynman Review Modes
# ---------------------------------------------------------------------------


class FeynmanReviewMode(enum.Enum):
    """Modes for Feynman-style active recall review."""

    ELI5 = "eli5"
    TEACH_BACK = "teach_back"
    ANALOGY_MAP = "analogy_map"
    GAP_FIND = "gap_find"
    BUILD_IT = "build_it"


@dataclass
class FeynmanAttempt:
    """Records a single Feynman exercise attempt."""

    concept_id: str
    mode: FeynmanReviewMode
    quality: int = 0  # 0-4 self-assessment scale
    timestamp: float = 0.0
    response: str = ""


@dataclass
class FeynmanReviewItem:
    """A concept review card in Feynman mode."""

    concept_id: str
    mode: FeynmanReviewMode
    prompt: str
    expected_elements: List[str] = field(default_factory=list)
    difficulty: int = 1


FEYNMAN_MODE_WEIGHTS: Dict[FeynmanReviewMode, float] = {
    FeynmanReviewMode.ELI5: 0.05,
    FeynmanReviewMode.TEACH_BACK: 0.10,
    FeynmanReviewMode.ANALOGY_MAP: 0.08,
    FeynmanReviewMode.GAP_FIND: 0.07,
    FeynmanReviewMode.BUILD_IT: 0.15,
}


def select_feynman_mode(
    concept: Dict[str, Any],
    history: List[FeynmanAttempt],
    path_position: Optional[str] = None,
) -> FeynmanReviewMode:
    """Select the best Feynman mode for a concept based on learner history
    and position in a Feynman learning path.

    If path_position is provided, biases mode selection:
      - "eli5" or "analogy" (early stages) → prefer ELI5, ANALOGY_MAP
      - "concrete" (mid stage) → prefer GAP_FIND
      - "build" or "teach_back" (late stages) → prefer BUILD_IT, TEACH_BACK

    Otherwise falls back to history-based selection (prioritises untried modes,
    then lowest average quality).
    """
    if path_position:
        stage_biases = {
            "eli5": [FeynmanReviewMode.ELI5, FeynmanReviewMode.ANALOGY_MAP],
            "analogy": [FeynmanReviewMode.ANALOGY_MAP, FeynmanReviewMode.ELI5],
            "concrete": [FeynmanReviewMode.GAP_FIND, FeynmanReviewMode.ELI5],
            "gap_map": [FeynmanReviewMode.GAP_FIND, FeynmanReviewMode.TEACH_BACK],
            "build": [FeynmanReviewMode.BUILD_IT, FeynmanReviewMode.TEACH_BACK],
            "teach_back": [FeynmanReviewMode.TEACH_BACK, FeynmanReviewMode.BUILD_IT],
        }
        modes = stage_biases.get(path_position, [FeynmanReviewMode.ELI5])
        attempted = {
            a.mode for a in history
            if a.concept_id in (concept.get("id"), concept.get("conceptSlug"))
        }
        for mode in modes:
            if mode not in attempted:
                return mode

    # Fallback: standard history-based selection
    ids = {concept.get("id"), concept.get("conceptSlug")}
    attempted_modes = {a.mode for a in history if a.concept_id in ids}

    priority_order = [
        FeynmanReviewMode.BUILD_IT,
        FeynmanReviewMode.TEACH_BACK,
        FeynmanReviewMode.GAP_FIND,
        FeynmanReviewMode.ANALOGY_MAP,
        FeynmanReviewMode.ELI5,
    ]

    for mode in priority_order:
        if mode not in attempted_modes:
            return mode

    # All attempted — return the one with lowest average quality
    mode_qualities: Dict[FeynmanReviewMode, List[int]] = {}
    for a in history:
        if a.concept_id in (concept.get("id"), concept.get("conceptSlug")):
            mode_qualities.setdefault(a.mode, []).append(a.quality)

    worst = FeynmanReviewMode.ELI5
    worst_avg = float("inf")
    for mode, quals in mode_qualities.items():
        avg = sum(quals) / len(quals)
        if avg < worst_avg:
            worst_avg = avg
            worst = mode
    return worst


def get_feynman_prompt(concept: Dict[str, Any], mode: FeynmanReviewMode) -> str:
    """Generate a review prompt for a concept in a given Feynman mode."""
    label = concept.get("label", concept.get("conceptSlug", "this concept"))
    prompts = {
        FeynmanReviewMode.ELI5: (
            f'Explain "{label}" like I am 5 years old. '
            "One paragraph. No jargon. Use an everyday analogy."
        ),
        FeynmanReviewMode.TEACH_BACK: (
            f'Teach "{label}" to a colleague who asks '
            "'How does this work?' Cover: what it is, how it works, "
            "why it matters. Use a concrete example."
        ),
        FeynmanReviewMode.ANALOGY_MAP: (
            f'Create a NEW analogy for "{label}" — '
            "different from the one in the concept card. "
            "Explain why your analogy works and where it breaks down."
        ),
        FeynmanReviewMode.GAP_FIND: concept.get(
            "teach_back_prompt",
            f'Explain "{label}" in your own words. '
            "Then list exactly what you are still unsure about.",
        ),
        FeynmanReviewMode.BUILD_IT: concept.get(
            "build_exercise", {}
        ).get(
            "prompt",
            f'Build something using "{label}" — code, a diagram, or '
            "a calculation. Then explain your design choices.",
        ),
    }
    return prompts.get(mode, prompts[FeynmanReviewMode.ELI5])


def calculate_feynman_mastery(
    state: MasteryState,
    feynman_attempts: List[FeynmanAttempt],
) -> float:
    """Compute mastery score weighted by Feynman exercise completion.

    Base SM-2 mastery is boosted by Feynman mode completion:
    - ELI5: +0.05, Gap Find: +0.07, Analogy: +0.08
    - Teach Back: +0.10, Build It: +0.15 (creation = deepest understanding)
    """
    base = calculate_mastery(state)
    bonus = 0.0
    for attempt in feynman_attempts:
        if attempt.quality >= 3:
            bonus += FEYNMAN_MODE_WEIGHTS.get(attempt.mode, 0.05)
    return round(min(1.0, base + bonus), 3)


def generate_feynman_review_items(
    concept: Dict[str, Any],
) -> List[FeynmanReviewItem]:
    """Generate all possible Feynman review items for a given concept dict."""
    feynman_data = concept.get("eli5_explanation") or concept.get("feynman_difficulty")
    if not feynman_data:
        return []

    items = []
    for mode in FeynmanReviewMode:
        prompt = get_feynman_prompt(concept, mode)
        difficulty = concept.get("feynman_difficulty", 2)
        items.append(FeynmanReviewItem(
            concept_id=concept.get("id") or concept.get("conceptSlug", ""),
            mode=mode,
            prompt=prompt,
            expected_elements=concept.get("gap_questions", []),
            difficulty=difficulty,
        ))
    return items


# ---------------------------------------------------------------------------
# SM-2 Algorithm (server-side reference implementation)
# ---------------------------------------------------------------------------

SM2_GRADE_AGAIN = 0
SM2_GRADE_HARD = 1
SM2_GRADE_GOOD = 2
SM2_GRADE_EASY = 3


def sm2_compute(
    quality: int,
    ease: float,
    interval: int,
    reps: int,
) -> Tuple[float, int, int]:
    """Pure SM-2 algorithm. Returns (new_ease, new_interval, new_reps).

    quality: 0 (Again) .. 3 (Easy) — matching current front-end scale.
    """
    quality = max(0, min(3, quality))

    if quality < 2:
        reps = 0
        interval = 1
    else:
        if reps == 0:
            interval = 1
        elif reps == 1:
            interval = 6
        else:
            interval = round(interval * ease)
        reps += 1

    # ease factor update (mapped from 0-3 to 0-5 range for SM-2 formula)
    q5 = quality * 5.0 / 3.0
    ease += 0.1 - (3 - q5) * (0.08 + (3 - q5) * 0.02)
    ease = max(1.3, ease)

    return round(ease, 2), interval, reps


def sm2_next_due(interval: int) -> float:
    """Return timestamp (epoch ms) for next review given interval in days."""
    return (datetime.now(timezone.utc).timestamp() + interval * 86400) * 1000


def calculate_mastery(state: MasteryState) -> float:
    """Compute a 0.0–1.0 mastery score from SM-2 state."""
    if state.reps == 0:
        return 0.0
    base = min(state.reps / 10.0, 1.0) * 0.5
    interval_factor = min(state.interval / 90.0, 1.0) * 0.3
    ease_factor = min((state.ease - 1.3) / 2.0, 1.0) * 0.2
    return round(base + interval_factor + ease_factor, 3)


def mastery_label(score: float) -> str:
    """Map mastery score to human label."""
    if score == 0.0:
        return "unseen"
    if score < 0.3:
        return "learning"
    if score < 0.6:
        return "reviewing"
    if score < 0.85:
        return "consolidating"
    return "mastered"


# ---------------------------------------------------------------------------
# Concept review item generation
# ---------------------------------------------------------------------------


def generate_concept_reviews(
    manager: OntologyManager,
    bloom_map: Optional[Dict[str, str]] = None,
) -> List[ConceptReviewItem]:
    """Build review items from every concept in the ontology."""
    items = []
    for concept in manager._concepts.values():
        bloom = (bloom_map or {}).get(concept.id, "remember")
        items.append(ConceptReviewItem(
            id=f"concept:{concept.id}",
            concept_slug=concept.id,
            label=concept.label,
            pillar=concept.pillar,
            definition=concept.description or concept.label,
            category=concept.category,
            epistemic_status=concept.epistemic_status,
            philosophical_lineage=concept.philosophical_lineage,
            bloom_level=bloom,
            source_inspiration=concept.source_inspiration,
            aliases=concept.aliases,
        ))
    items.sort(key=lambda x: (x.pillar, x.label))
    return items


def generate_concept_review_json(
    manager: OntologyManager,
    bloom_map: Optional[Dict[str, str]] = None,
) -> List[Dict[str, Any]]:
    """Generate JSON-serializable review items for the front-end."""
    items = generate_concept_reviews(manager, bloom_map)
    result = []
    for item in items:
        c = manager.get_concept(item.concept_slug)
        result.append({
            "id": item.id,
            "conceptSlug": item.concept_slug,
            "label": item.label,
            "pillar": item.pillar,
            "definition": item.definition,
            "category": item.category,
            "epistemicStatus": item.epistemic_status,
            "philosophicalLineage": item.philosophical_lineage[:3],
            "bloomLevel": item.bloom_level,
            "sourceInspiration": item.source_inspiration,
            "aliases": item.aliases[:5],
            # Feynman fields
            "eli5Explanation": getattr(c, "eli5_explanation", None),
            "analogy": getattr(c, "analogy", None),
            "concreteExample": getattr(c, "concrete_example", None),
            "feynmanDifficulty": getattr(c, "feynman_difficulty", 1),
            "gapQuestions": getattr(c, "gap_questions", []),
            "teachBackPrompt": getattr(c, "teach_back_prompt", None),
            "buildExercise": getattr(c, "build_exercise", None),
        })
    return result


# ---------------------------------------------------------------------------
# Gap detection
# ---------------------------------------------------------------------------


def detect_gaps(
    review_items: List[ConceptReviewItem],
    mastery_states: Dict[str, MasteryState],
    *,
    overdue_threshold_days: int = 7,
    low_mastery_threshold: float = 0.3,
) -> GapReport:
    """Analyze which concepts are unseen, overdue, or have low mastery."""
    unseen: List[ConceptReviewItem] = []
    overdue: List[ConceptReviewItem] = []
    low_mastery: List[ConceptReviewItem] = []
    pillar_counts: Dict[str, int] = {}
    now_ms = datetime.now(timezone.utc).timestamp() * 1000

    seen_ids = set()

    for item in review_items:
        state = mastery_states.get(item.id, MasteryState())
        pillar_counts[item.pillar] = pillar_counts.get(item.pillar, 0) + 1

        if state.reps == 0:
            unseen.append(item)
            seen_ids.add(item.id)
            continue

        mastery = calculate_mastery(state)

        if state.due > 0 and state.due <= now_ms:
            overdue_days = (now_ms - state.due) / 86400000
            if overdue_days >= overdue_threshold_days:
                overdue.append(item)
                seen_ids.add(item.id)
                continue

        if mastery < low_mastery_threshold:
            low_mastery.append(item)
            seen_ids.add(item.id)

    return GapReport(
        unseen_concepts=unseen,
        overdue_concepts=overdue,
        low_mastery_concepts=low_mastery,
        pillar_breakdown=pillar_counts,
        total_gaps=len(unseen) + len(overdue) + len(low_mastery),
    )


# ---------------------------------------------------------------------------
# Interleaved practice scheduling
# ---------------------------------------------------------------------------


def build_interleaved_session(
    review_items: List[ConceptReviewItem],
    mastery_states: Dict[str, MasteryState],
    *,
    session_size: int = 10,
    max_per_pillar: Optional[int] = None,
) -> InterleavedSession:
    """Build an interleaved review session mixing pillars.

    Prioritizes unseen and overdue concepts. Ensures pillar diversity.
    """
    now_ms = datetime.now(timezone.utc).timestamp() * 1000
    due: List[ConceptReviewItem] = []
    unseen: List[ConceptReviewItem] = []
    other: List[ConceptReviewItem] = []

    for item in review_items:
        state = mastery_states.get(item.id, MasteryState())
        if state.reps == 0:
            unseen.append(item)
        elif state.due <= now_ms:
            due.append(item)
        else:
            other.append(item)

    random.shuffle(unseen)
    random.shuffle(due)
    random.shuffle(other)

    candidates = due + unseen + other
    pillar_order: List[str] = []
    selected: List[ConceptReviewItem] = []
    pillar_count: Dict[str, int] = {}
    max_per = max_per_pillar or max(3, session_size // 2)

    for item in candidates:
        if len(selected) >= session_size:
            break
        pc = pillar_count.get(item.pillar, 0)
        if pc >= max_per:
            continue
        selected.append(item)
        pillar_count[item.pillar] = pc + 1
        if item.pillar not in pillar_order:
            pillar_order.append(item.pillar)

    return InterleavedSession(
        session_id=datetime.now(timezone.utc).strftime("session-%Y%m%d-%H%M%S"),
        items=selected,
        pillar_order=pillar_order,
        session_size=len(selected),
    )


# ---------------------------------------------------------------------------
# Persistence helpers
# ---------------------------------------------------------------------------


def save_concept_review_json(items: List[Dict[str, Any]], path: str | Path) -> None:
    """Write concept review data as JSON for the front-end to load."""
    payload = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "total": len(items),
        "concepts": items,
    }
    Path(path).write_text(json.dumps(payload, indent=2), encoding="utf-8")


def load_mastery_states_from_dict(
    data: Dict[str, Dict[str, Any]],
) -> Dict[str, MasteryState]:
    """Deserialize localStorage-style mastery data."""
    states = {}
    for cid, raw in data.items():
        states[cid] = MasteryState(
            ease=raw.get("ease", 2.5),
            interval=raw.get("interval", 0),
            reps=raw.get("reps", 0),
            due=raw.get("due", 0.0),
            last_review=raw.get("lastReview", 0.0),
            quality_history=raw.get("qualityHistory", []),
        )
    return states
