"""Retention & Retrieval Engine — SM-2 scheduling, gap detection, interleaved practice."""

from __future__ import annotations

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
    return [
        {
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
        }
        for item in items
    ]


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
