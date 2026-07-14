#!/usr/bin/env python3
"""Bayesian SQI Update Engine for AcaciaFund.

Implements the Signal Quality Index (SQI) revision framework from
content/docs/2026-06-30-cybernetic-foundations-of-knowledge-fabric.md:

  P(H|E) = P(E|H) * P(H) / P(E)

Where:
  - P(H) is the prior SQI (stored in registry.json)
  - P(E|H) is the likelihood ratio based on evidence
  - P(E) is the marginal likelihood (normalizing constant)
  - P(H|E) is the posterior SQI

Evidence signals and likelihood ratios:
  - Governance Gate PASS: LR = 1.5
  - Governance Gate FAIL (structural: too_short / boilerplate_dominated): LR = 0.20
  - Governance Gate FAIL (analysis: low_analytical_coverage):      LR = 0.50
  - Governance Gate FAIL (topical overlap: high_similarity):       LR = 0.80
  - Human Correction PASS: LR = 2.0
  - Human Correction FAIL: LR = 0.2

Daily decay: 0.2% compound decay applied to prior before Bayesian update.

Deprecation trigger: SQI < 0.50 marks item as deprecated.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

REGISTRY_PATH = ROOT / "registry.json"
HUMAN_CORRECTIONS_PATH = ROOT / "registry" / "human_corrections.json"
GOVERNANCE_REPORT_PATH = ROOT / "registry" / "governance_report.json"

# Bayesian parameters
DECAY_RATE_DAILY = 0.002  # 0.2% daily decay (~345-day half-life)
DEPRECATION_THRESHOLD = 0.50
SQI_MIN = 0.01
SQI_MAX = 0.99

# Likelihood ratios
LR_GOV_PASS = 1.5
LR_HUMAN_PASS = 2.0
LR_HUMAN_FAIL = 0.2

# Failure-specific likelihood ratios (applied when governance fails)
# Structural / critical failures
LR_FAIL_TOO_SHORT = 0.20
LR_FAIL_BOILERPLATE = 0.20
# Content quality deficits
LR_FAIL_LOW_ANALYTICAL = 0.50
# Topical overlap (mild penalty) — higher threshold (0.85 Jaccard)
# means only near-duplicates are caught; keeping the penalty mild
# avoids collateral deprecation of domain-similar content.
LR_FAIL_HIGH_SIMILARITY = 0.90
# Default for other failures (e.g. high_entropy — diverse vocabulary is
# a legitimate feature of technical research, not a quality defect)
LR_FAIL_DEFAULT = 0.85

FAILURE_LR_MAP: dict[str, float] = {
    "too_short": LR_FAIL_TOO_SHORT,
    "boilerplate_dominated": LR_FAIL_BOILERPLATE,
    "low_analytical_coverage": LR_FAIL_LOW_ANALYTICAL,
    "high_similarity": LR_FAIL_HIGH_SIMILARITY,
}


def load_registry() -> dict:
    """Load registry.json."""
    if not REGISTRY_PATH.exists():
        print(f"Error: {REGISTRY_PATH} not found.")
        sys.exit(1)
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_registry(reg: dict) -> None:
    """Save registry.json atomically."""
    from core.registry_io import save_registry as _atomic_save
    _atomic_save(reg, REGISTRY_PATH)


def load_governance_report() -> dict:
    """Load governance report from last run."""
    if not GOVERNANCE_REPORT_PATH.exists():
        return {}
    with open(GOVERNANCE_REPORT_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_human_corrections() -> dict:
    """Load human corrections."""
    if not HUMAN_CORRECTIONS_PATH.exists():
        return {"corrections": []}
    with open(HUMAN_CORRECTIONS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def compute_days_since_last_update(last_updated: str | None) -> float:
    """Compute days since last update (default to 1 day if unknown)."""
    if not last_updated:
        return 1.0
    try:
        # Parse ISO format with Z suffix
        if last_updated.endswith("Z"):
            last_updated = last_updated[:-1] + "+00:00"
        last_dt = datetime.fromisoformat(last_updated)
        now = datetime.now(timezone.utc)
        delta = now - last_dt
        return max(delta.total_seconds() / 86400, 0.0)
    except (ValueError, TypeError):
        return 1.0


def apply_decay(prior: float, days: float) -> float:
    """Apply daily compound decay: P_decayed = P * (1 - decay_rate)^days"""
    decay_factor = (1 - DECAY_RATE_DAILY) ** days
    return max(prior * decay_factor, SQI_MIN)


def compute_likelihood_ratio(
    gov_passed: bool | None,
    failures: list[str] | None,
    human_correction: str | None,
) -> float:
    """Compute cumulative likelihood ratio from evidence.

    Applies failure-specific likelihood ratios when governance fails,
    rather than a blanket penalty.  The most severe (lowest) LR among
    the current item's failures is used.
    """
    lr = 1.0  # Neutral baseline

    # Governance gate evidence
    if gov_passed is True:
        lr *= LR_GOV_PASS
    elif gov_passed is False and failures:
        # Apply the most severe (lowest) LR among the failures
        failure_lrs = [
            FAILURE_LR_MAP.get(f, LR_FAIL_DEFAULT)
            for f in failures
        ]
        lr *= min(failure_lrs)

    # Human correction evidence (overrides governance)
    if human_correction == "pass":
        lr *= LR_HUMAN_PASS
    elif human_correction == "fail":
        lr *= LR_HUMAN_FAIL

    return lr


def bayesian_update(prior: float, likelihood_ratio: float) -> float:
    """Compute posterior: P(H|E) = P(E|H) * P(H) / P(E)

    P(E) = P(E|H) * P(H) + P(E|~H) * P(~H)
    where P(E|~H) = 1 - P(E|H) (complement)

    Simplified: posterior = (LR * prior) / (LR * prior + (1 - LR) * (1 - prior))
    But we need to handle LR > 1 and LR < 1 carefully.

    Alternative formulation using odds:
    odds_posterior = odds_prior * LR
    posterior = odds / (1 + odds)
    """
    if prior <= 0 or prior >= 1:
        return prior  # Boundary cases

    # Convert to odds
    odds_prior = prior / (1 - prior)

    # Apply likelihood ratio
    odds_posterior = odds_prior * likelihood_ratio

    # Convert back to probability
    posterior = odds_posterior / (1 + odds_posterior)

    # Clamp to valid range
    return max(SQI_MIN, min(SQI_MAX, posterior))


def update_sqi_for_item(
    item: dict,
    gov_result: dict | None,
    human_correction: str | None,
    days_since_update: float,
) -> tuple[float, bool, str]:
    """Update SQI for a single item. Returns (new_sqi, deprecated, reason)."""
    slug = item.get("slug", "unknown")
    prior = item.get("sqi", 0.5)

    # Apply daily decay
    decayed_prior = apply_decay(prior, days_since_update)

    # Compute likelihood ratio from evidence (failure-specific LRs)
    lr = compute_likelihood_ratio(
        gov_result.get("passed") if gov_result else None,
        gov_result.get("failures", []) if gov_result else None,
        human_correction,
    )

    # Bayesian update
    posterior = bayesian_update(decayed_prior, lr)

    # Determine deprecation
    deprecated = posterior < DEPRECATION_THRESHOLD

    # Build reason
    reasons = []
    if days_since_update > 0:
        reasons.append(f"decay:{prior:.3f}->{decayed_prior:.3f} ({days_since_update:.1f}d)")
    if gov_result:
        status = "pass" if gov_result.get("passed") else "fail"
        failures = gov_result.get("failures", [])
        if failures:
            reasons.append(f"gov_{status}({','.join(failures)})")
        else:
            reasons.append(f"gov_{status}")
    if human_correction:
        reasons.append(f"human_{human_correction}")
    reasons.append(f"posterior:{posterior:.3f}")

    reason = ", ".join(reasons)

    return posterior, deprecated, reason


def main() -> int:
    parser = argparse.ArgumentParser(
        description="AcaciaFund Bayesian SQI Update Engine"
    )
    parser.add_argument(
        "--registry",
        default=str(REGISTRY_PATH),
        help="Path to registry.json"
    )
    parser.add_argument(
        "--governance-report",
        default=str(GOVERNANCE_REPORT_PATH),
        help="Path to governance report JSON"
    )
    parser.add_argument(
        "--human-corrections",
        default=str(HUMAN_CORRECTIONS_PATH),
        help="Path to human corrections JSON"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show updates without writing"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed output"
    )
    args = parser.parse_args()

    # Load data
    reg = load_registry()
    gov_report = load_governance_report()
    human_corrections = load_human_corrections()

    # Build lookup for governance results
    gov_results = {}
    for item in gov_report.get("results", []):
        slug = item.get("slug", "") or item.get("path", "")
        if slug:
            gov_results[slug] = item

    # Build lookup for human corrections
    human_corr_map = {}
    for corr in human_corrections.get("corrections", []):
        slug = corr.get("slug", "")
        if slug:
            human_corr_map[slug] = corr.get("correction")

    # Update SQI for each item
    updated_items = []
    deprecated_count = 0

    for item in reg.get("content", []):
        slug = item.get("slug", "")
        prior = item.get("sqi", 0.5)

        # Get governance result (match by slug)
        gov_result = gov_results.get(slug)

        # Get human correction
        human_correction = human_corr_map.get(slug)

        # Compute days since last update
        last_updated = item.get("updated_at") or item.get("created_at")
        days = compute_days_since_last_update(last_updated)

        # Update SQI
        new_sqi, deprecated, reason = update_sqi_for_item(
            item, gov_result, human_correction, days
        )

        # Track changes
        if abs(new_sqi - prior) > 0.001 or deprecated != item.get("deprecated", False):
            updated_items.append({
                "slug": slug,
                "prior": prior,
                "new_sqi": new_sqi,
                "deprecated": deprecated,
                "reason": reason
            })

            if deprecated:
                deprecated_count += 1

        # Apply update to item
        item["sqi"] = new_sqi
        item["deprecated"] = deprecated
        item["updated_at"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

        if args.verbose:
            status = "DEPRECATED" if deprecated else "active"
            print(f"  {slug}: {prior:.3f} -> {new_sqi:.3f} [{status}] {reason}")

    # Update registry metadata
    reg["last_updated"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    # Write changes
    if not args.dry_run:
        save_registry(reg)

    # Summary
    print("=" * 60)
    print("SQI UPDATE ENGINE REPORT")
    print("=" * 60)
    print(f"Total items processed: {len(reg.get('content', []))}")
    print(f"Items with SQI changes: {len(updated_items)}")
    print(f"Items deprecated (SQI < {DEPRECATION_THRESHOLD}): {deprecated_count}")

    if updated_items and args.verbose:
        print()
        print("--- SQI CHANGES ---")
        for u in sorted(updated_items, key=lambda x: abs(x["new_sqi"] - x["prior"]), reverse=True)[:20]:
            direction = "DOWN" if u["new_sqi"] < u["prior"] else "UP"
            print(f"  {direction}: {u['slug']}")
            print(f"       {u['prior']:.3f} -> {u['new_sqi']:.3f} ({u['reason']})")

    print()
    print("=" * 60)

    if args.dry_run:
        print("DRY RUN - No changes written")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
