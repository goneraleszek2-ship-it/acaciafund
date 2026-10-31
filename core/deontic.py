"""Shared deontic classification and bitmask assignment.

The deontic layer classifies ontology concepts as Obligation (O), Permission (P),
or Prohibition (F) and packs them into integer masks for O(1) Edge-KV lookup.

The original implementation derived a concept's bit position from a
non-injective hash of its id::

    offset = sum(ord(c) for c in cid[:3]) % 60

Every id beginning with ``aml`` maps to bit 14 (97 + 109 + 108 = 314; 314 % 60
= 14), so an entire pillar collapsed onto a single bit and the classification
was destroyed. Worse, the masks were truncated to 64 bits while the ontology has
more than 64 deontically-classified concepts, so even a corrected scheme could
not have been injective. The functions here assign bit positions by a stable
dense index and emit arbitrary-precision integer masks (Python ints / hex
strings), which whole-registry classification requires. The id→bit mapping is
exported so lookups match the masks that were built.
"""

from __future__ import annotations

from typing import Dict, Iterable, List, Optional

DEONTIC_STATES = ("O", "P", "F")


def classify_deontic(concept: dict) -> Optional[str]:
    """Classify an ontology concept into a deontic state.

    Returns "O" (obligation), "P" (permission), "F" (prohibition), or None when
    the concept carries no deontic commitment.
    """
    pillar = (concept.get("pillar") or "").strip().lower()
    epistemic = (concept.get("epistemic_status") or "").lower()

    if epistemic in ("regulatory", "constitutive") and pillar in ("aml", "compliance"):
        return "O"
    if epistemic in ("instrumental", "pragmatic") and pillar in ("stock", "market"):
        return "P"
    if epistemic == "ontological":
        return "F"
    return None


def assign_bit_positions(concept_ids: Iterable[str]) -> Dict[str, int]:
    """Assign a unique dense bit position to each concept id.

    Deterministic (ids are sorted) and injective; positions are 0..n-1.
    """
    ids = sorted(set(concept_ids))
    return {cid: i for i, cid in enumerate(ids)}


def build_deontic_masks(concepts: List[dict]) -> dict:
    """Build O/P/F integer masks plus the id→bit index map.

    Args:
        concepts: Ontology concept dicts (each with ``id``, ``pillar`` and
            ``epistemic_status``).

    Returns:
        Dict with ``obligation_mask``, ``permission_mask``, ``prohibition_mask``,
        their bit counts, ``index_map`` (concept id → bit position), and
        ``bit_to_concept`` (the inverse map). Only classified concepts receive a
        bit; unclassified concepts are absent from the index map. Masks are
        arbitrary-precision integers (not limited to 64 bits).
    """
    classified: List[tuple] = []
    for c in concepts:
        cid = c.get("id")
        if not cid:
            continue
        state = classify_deontic(c)
        if state in DEONTIC_STATES:
            classified.append((cid, state))

    index_map = assign_bit_positions(cid for cid, _ in classified)

    masks = {"O": 0, "P": 0, "F": 0}
    for cid, state in classified:
        masks[state] |= 1 << index_map[cid]

    return {
        "obligation_mask": masks["O"],
        "permission_mask": masks["P"],
        "prohibition_mask": masks["F"],
        "obligation_count": bin(masks["O"]).count("1"),
        "permission_count": bin(masks["P"]).count("1"),
        "prohibition_count": bin(masks["F"]).count("1"),
        "index_map": index_map,
        "bit_to_concept": {bit: cid for cid, bit in index_map.items()},
    }
