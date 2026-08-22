"""Z3 SMT-LIB2 Validator: Verify deontic constraints and PNC (Prime Implicant Non-Contradiction)."""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any


def encode_deontic_constraints(bitmask_data: dict) -> list:
    """Encode deontic bitmask constraints into Z3 SMT-LIB2 format.

    Deontic states O (Obligation), P (Permission), F (Prohibition)
    are encoded as boolean variables over concept indices.
    """
    from z3 import Ints, Bool, And, Or, Not, sat, solve

    obligation_mask = bitmask_data["obligation_mask"]
    permission_mask = bitmask_data["permission_mask"]
    prohibition_mask = bitmask_data["prohibition_mask"]

    # Extract concept indices from bitmasks
    obligation_indices = []
    permission_indices = []
    prohibition_indices = []

    for i in range(64):
        if obligation_mask & (1 << i):
            obligation_indices.append(i)
        if permission_mask & (1 << i):
            permission_indices.append(i)
        if prohibition_mask & (1 << i):
            prohibition_indices.append(i)

    # Z3 variables: O_i, P_i, F_i for each concept index
    O = [Bool(f"O_{i}") for i in obligation_indices]
    P = [Bool(f"P_{i}") for i in permission_indices]
    F = [Bool(f"F_{i}") for i in prohibition_indices]

    # Constraint: No concept can be both Obligation and Prohibition
    constraints = []

    # O_i -> not F_i (cannot be both obligatory and prohibited)
    for i_idx, i in enumerate(obligation_indices):
        for j_idx, j in enumerate(prohibition_indices):
            # Simplified: check if same index concept appears in both masks
            if i == j:
                constraints.append(Implies(O[i_idx], Not(F[j_idx])))

    # Constraint: A concept cannot have both Permission and Prohibition
    for i_idx, i in enumerate(permission_indices):
        for j_idx, j in enumerate(prohibition_indices):
            constraints.append(Implies(P[i_idx], Not(F[j_idx])))

    # PNC (Prime Implicant Non-Contradiction): At least one consistent assignment exists
    # If O_i and F_i both hold for same concept, it's a contradiction
    for i_idx in range(len(obligation_indices)):
        for j_idx in range(len(prohibition_indices)):
            if obligation_indices[i_idx] == prohibition_indices[j_idx]:
                constraints.append(Not(And(Ob[i_idx], F[j_idx])))

    return constraints


def run_z3_verification(bitmask_data: dict) -> dict:
    """Run Z3 verification and return PNC violation report."""
    from z3 import Implies, sat

    constraints = encode_deontic_constraints(bitmask_data)

    # Check satisfiability
    s = sat()
    for c in constraints:
        s.add(c)

    result = sat

    # If unsatisfiable, extract violations
    violations = []
    if sat is False:
        # Extract minimal unsatisfiable subset (MUS)
        # For now, report all pairwise contradictions
        obligation_indices = []
        permission_indices = []
        prohibition_indices = []

        obligation_mask = bitmask_data["obligation_mask"]
        permission_mask = bitmask_data["permission_mask"]
        prohibition_mask = bitmask_data["prohibition_mask"]

        for i in range(64):
            if obligation_mask & (1 << i):
                obligation_indices.append(i)
            if permission_mask & (1 << i):
                permission_indices.append(i)
            if prohibition_mask & (1 << i):
                prohibition_indices.append(i)

        # Pairwise contradictions: O_i & F_i can't both hold
        for i in obligation_indices:
            for j in prohibition_indices:
                if i == j:
                    violations.append(
                        {"type": "obligation_prohibition_contradiction",
                         "concept_index": i,
                         "detail": f"Concept {i} cannot be both obligatory and prohibited"}
                    )

        for i in permission_indices:
            for j in prohibition_indices:
                if i == j:
                    violations.append(
                        {"type": "permission_prohibition_contradiction",
                         "concept_index": i,
                         "detail": f"Concept {i} cannot be both permitted and prohibited"}
                    )

    return {
        "pnc_violations": violations,
        "satisfiable": sat,
        "constraint_count": len(constraints),
    }


def main(argv: list = None) -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Z3 SMT-LIB2 Validator")
    parser.add_argument("--deontic-dist", required=True, help="Path to deontic bitmasks JSON")
    parser.add_argument("--output", required=True, help="Path to output Z3 report JSON")
    args = parser.parse_args(argv) if argv else parser.parse_args()

    with open(args.deontic_dist) as f:
        bitmask_data = json.load(f)

    result = run_z3_verification(bitmask_data)

    with open(args.output, "w") as f:
        json.dump(result, f, indent=2)

    print(f"Z3 verification complete: {result['satisfiable']}")
    print(f"PNC violations: {len(result['pnc_violations'])}")
    print(f"Output written to: {args.output}")

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
