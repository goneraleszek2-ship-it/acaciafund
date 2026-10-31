"""Tests for the shared deontic layer (core/deontic.py).

Includes a regression test for the non-injective hash bug: under the old
`sum(ord(c) for c in cid[:3]) % 60` scheme, every `aml*` id mapped to bit 14,
collapsing a whole pillar onto one bit.
"""

import pytest

from core.deontic import (
    assign_bit_positions,
    build_deontic_masks,
    classify_deontic,
)

# ── Classification ──

@pytest.mark.parametrize(
    "concept,expected",
    [
        ({"pillar": "aml", "epistemic_status": "regulatory"}, "O"),
        ({"pillar": "aml", "epistemic_status": "constitutive"}, "O"),
        ({"pillar": "compliance", "epistemic_status": "regulatory"}, "O"),
        ({"pillar": "stock", "epistemic_status": "instrumental"}, "P"),
        ({"pillar": "market", "epistemic_status": "pragmatic"}, "P"),
        ({"pillar": "data-engineering", "epistemic_status": "ontological"}, "F"),
        ({"pillar": "aml", "epistemic_status": "instrumental"}, None),
        ({"pillar": "stock", "epistemic_status": "regulatory"}, None),
        ({"pillar": "data-engineering", "epistemic_status": "pragmatic"}, None),
        ({}, None),
    ],
)
def test_classify_deontic(concept, expected):
    assert classify_deontic(concept) == expected


def test_classify_deontic_case_insensitive():
    assert classify_deontic({"pillar": "AML", "epistemic_status": "Regulatory"}) == "O"


# ── Bit assignment ──

def test_assign_bit_positions_is_unique_and_dense():
    ids = [f"c{i}" for i in range(50)]
    positions = assign_bit_positions(ids)
    assert len(set(positions.values())) == 50
    assert sorted(positions.values()) == list(range(50))


def test_assign_bit_positions_deterministic_regardless_of_order():
    assert assign_bit_positions(["b", "a", "c"]) == assign_bit_positions(["c", "a", "b"])


def test_assign_bit_positions_handles_more_than_64_concepts():
    """The ontology has 79 classified concepts; more than 64 must be supported."""
    positions = assign_bit_positions([f"c{i}" for i in range(79)])
    assert len(set(positions.values())) == 79
    assert max(positions.values()) == 78


# ── Mask building + regression ──

def _concepts():
    return [
        {"id": "aml-a", "pillar": "aml", "epistemic_status": "regulatory"},
        {"id": "aml-b", "pillar": "aml", "epistemic_status": "constitutive"},
        {"id": "stock-x", "pillar": "stock", "epistemic_status": "instrumental"},
        {"id": "ont-1", "pillar": "data-engineering", "epistemic_status": "ontological"},
        {"id": "none-1", "pillar": "data-engineering", "epistemic_status": "instrumental"},
    ]


def test_build_deontic_masks_counts_and_map():
    result = build_deontic_masks(_concepts())
    assert result["obligation_count"] == 2
    assert result["permission_count"] == 1
    assert result["prohibition_count"] == 1
    # Unclassified concepts are absent from the index map.
    assert "none-1" not in result["index_map"]
    # bit_to_concept is the inverse of index_map.
    assert {v: k for k, v in result["index_map"].items()} == result["bit_to_concept"]


def test_aml_concepts_do_not_collide():
    """Regression: the old hash mapped every aml* id to bit 14."""
    result = build_deontic_masks(_concepts())
    bit_a = result["index_map"]["aml-a"]
    bit_b = result["index_map"]["aml-b"]
    assert bit_a != bit_b
    assert result["obligation_mask"] & (1 << bit_a)
    assert result["obligation_mask"] & (1 << bit_b)


def test_get_deontic_state_round_trips():
    from scripts.bitmask_exporter import get_deontic_state

    result = build_deontic_masks(_concepts())
    assert get_deontic_state("aml", "aml-a", result) == "O"
    assert get_deontic_state("stock", "stock-x", result) == "P"
    assert get_deontic_state("data-engineering", "ont-1", result) == "F"
    assert get_deontic_state("data-engineering", "none-1", result) == "N"
    assert get_deontic_state("data-engineering", "missing", result) == "N"


def test_get_deontic_state_accepts_hex_export():
    """The exported static artifact stores hex masks, not integer masks."""
    from scripts.bitmask_exporter import get_deontic_state

    result = build_deontic_masks(_concepts())
    exported = {
        "obligation_mask_hex": hex(result["obligation_mask"]),
        "permission_mask_hex": hex(result["permission_mask"]),
        "prohibition_mask_hex": hex(result["prohibition_mask"]),
        "index_map": result["index_map"],
    }
    assert get_deontic_state("aml", "aml-a", exported) == "O"
    assert get_deontic_state("stock", "stock-x", exported) == "P"
    assert get_deontic_state("data-engineering", "ont-1", exported) == "F"
