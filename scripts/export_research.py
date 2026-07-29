#!/usr/bin/env python3
"""
Export research workspace — generate Markdown / JSON reports from source trails,
contradiction detection, and evidence grading.

Usage:
    python3 scripts/export_research.py --pillar aml --format md
    python3 scripts/export_research.py --concept-id kyc --format json
    python3 scripts/export_research.py --all --format md --output report.md
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.contradiction import ContradictionReport, detect_contradictions
from core.evidence_grade import EvidenceScore, grade_evidence
from core.source_trail import SourceTrailManager

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------


def _pillar_label(pillar: str) -> str:
    labels = {
        "aml": "Compliance",
        "stock": "Markets",
        "data-engineering": "Data Engineering",
    }
    return labels.get(pillar, pillar.replace("-", " ").title())


def generate_markdown_report(
    scores: List[EvidenceScore],
    contradiction_report: ContradictionReport,
    pillar: Optional[str] = None,
    concept_id: Optional[str] = None,
) -> str:
    """Generate a Markdown research report from evidence scores and contradictions."""
    lines: List[str] = []
    lines.append("# Research Workspace Report")
    lines.append("")

    meta_parts = [f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"]
    if pillar:
        meta_parts.append(f"Pillar: {_pillar_label(pillar)} ({pillar})")
    if concept_id:
        meta_parts.append(f"Concept: {concept_id}")
    meta_parts.append(f"Claims graded: {len(scores)}")
    lines.append(" | ".join(meta_parts))
    lines.append("")

    if pillar or concept_id:
        lines.append(f"**Filter**: {'Pillar = ' + _pillar_label(pillar) if pillar else ''}{'Concept = ' + concept_id if concept_id else ''}")
        lines.append("")

    # --- Evidence Quality Summary ---
    lines.append("## Evidence Quality Summary")
    lines.append("")
    lines.append("| Level | Count |")
    lines.append("|-------|-------|")
    level_counts: Dict[str, int] = {}
    for s in scores:
        level_counts[s.level.value] = level_counts.get(s.level.value, 0) + 1
    for level in ["high", "moderate", "low", "very_low"]:
        count = level_counts.get(level, 0)
        label = level.replace("_", " ").title()
        lines.append(f"| {label} | {count} |")
    lines.append("")

    avg = sum(s.score for s in scores) / len(scores) if scores else 0.0
    lines.append(f"**Average score**: {avg:.2f}")
    lines.append("")

    # --- Contradictions ---
    lines.append("## Contradictions")
    lines.append("")
    if contradiction_report.total_pairs == 0:
        lines.append("No contradictions detected.")
    else:
        lines.append(f"Total pairs: {contradiction_report.total_pairs}")
        if contradiction_report.by_type:
            type_str = ", ".join(f"{t}: {c}" for t, c in sorted(contradiction_report.by_type.items()))
            lines.append(f"By type: {type_str}")
        if contradiction_report.by_severity:
            sev_str = ", ".join(f"{s}: {c}" for s, c in sorted(contradiction_report.by_severity.items()))
            lines.append(f"By severity: {sev_str}")
        lines.append("")

        for i, pair in enumerate(contradiction_report.pairs, 1):
            lines.append(f"### Contradiction {i}")
            lines.append("")
            lines.append(f"- **Type**: {pair.contradiction_type.value}")
            lines.append(f"- **Severity**: {pair.severity.value}")
            lines.append(f"- **Confidence**: {pair.confidence}")
            lines.append(f"- **Claim A**: {pair.claim_a}")
            lines.append(f"- **Claim B**: {pair.claim_b}")
            if pair.concept_ids:
                lines.append(f"- **Concepts**: {', '.join(pair.concept_ids)}")
            if pair.citation_a:
                lines.append(f"- **Source A**: {pair.citation_a}")
            if pair.citation_b:
                lines.append(f"- **Source B**: {pair.citation_b}")
            lines.append("")

    # --- Per-Claim Evidence Grades ---
    lines.append("## Claim-Level Evidence")
    lines.append("")
    lines.append("| # | Claim | Level | Score | Downgrades | Upgrades | Citations |")
    lines.append("|---|-------|-------|-------|------------|----------|-----------|")
    sorted_scores = sorted(scores, key=lambda s: s.score)
    for i, s in enumerate(sorted_scores, 1):
        claim_short = s.claim[:60].replace("\n", " ")
        level = s.level.value.replace("_", " ").title()
        dg = ", ".join(d.value for d in s.downgrades) if s.downgrades else "—"
        ug = ", ".join(u.value for u in s.upgrades) if s.upgrades else "—"
        lines.append(f"| {i} | {claim_short} | {level} | {s.score:.2f} | {dg} | {ug} | {s.citations_used} |")
    lines.append("")

    # --- Downgrade Breakdown ---
    lines.append("## Downgrade Reasons")
    lines.append("")
    all_downgrades: Dict[str, int] = {}
    for s in scores:
        for d in s.downgrades:
            all_downgrades[d.value] = all_downgrades.get(d.value, 0) + 1
    if all_downgrades:
        lines.append("| Reason | Count |")
        lines.append("|--------|-------|")
        for reason, count in sorted(all_downgrades.items(), key=lambda x: -x[1]):
            lines.append(f"| {reason.replace('_', ' ').title()} | {count} |")
    else:
        lines.append("No downgrades applied.")
    lines.append("")

    lines.append("---")
    lines.append(f"*Report generated by AcaciaFund Research Export at {datetime.now(timezone.utc).isoformat()}*")
    lines.append("")

    return "\n".join(lines)


def generate_json_report(
    scores: List[EvidenceScore],
    contradiction_report: ContradictionReport,
    pillar: Optional[str] = None,
    concept_id: Optional[str] = None,
) -> str:
    """Generate a JSON research report."""
    report: Dict = {
        "report_type": "research_workspace",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "filter": {},
        "summary": {
            "total_claims": len(scores),
            "average_score": round(sum(s.score for s in scores) / len(scores), 2) if scores else 0.0,
            "level_counts": {},
            "total_contradictions": contradiction_report.total_pairs,
        },
        "contradictions": {
            "total_pairs": contradiction_report.total_pairs,
            "by_type": contradiction_report.by_type,
            "by_severity": contradiction_report.by_severity,
            "pairs": [
                {
                    "claim_a": p.claim_a,
                    "claim_b": p.claim_b,
                    "type": p.contradiction_type.value,
                    "severity": p.severity.value,
                    "confidence": p.confidence,
                    "concept_ids": p.concept_ids,
                    "source_a": p.source_a,
                    "source_b": p.source_b,
                }
                for p in contradiction_report.pairs
            ],
        },
        "evidence_scores": [
            {
                "claim": s.claim,
                "level": s.level.value,
                "score": s.score,
                "downgrades": [d.value for d in s.downgrades],
                "upgrades": [u.value for u in s.upgrades],
                "citations_used": s.citations_used,
                "pillar": s.pillar,
                "concept_ids": s.concept_ids,
                "criteria": s.criteria,
            }
            for s in scores
        ],
    }

    if pillar:
        report["filter"]["pillar"] = pillar
    if concept_id:
        report["filter"]["concept_id"] = concept_id

    level_counts: Dict[str, int] = {}
    for s in scores:
        level_counts[s.level.value] = level_counts.get(s.level.value, 0) + 1
    report["summary"]["level_counts"] = level_counts

    return json.dumps(report, indent=2)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_trail_manager_from_data(data_path: Path) -> SourceTrailManager:
    """Load a SourceTrailManager from a JSON file."""
    if not data_path.exists():
        logger.warning("Trail data file not found: %s", data_path)
        return SourceTrailManager()
    with open(data_path) as f:
        data = json.load(f)
    return SourceTrailManager.from_dict(data)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export research workspace report from source trails."
    )
    parser.add_argument(
        "--pillar",
        type=str,
        help="Filter to a specific pillar (aml, stock, data-engineering)",
    )
    parser.add_argument(
        "--concept-id",
        type=str,
        help="Filter to a specific concept ID",
    )
    parser.add_argument(
        "--format",
        type=str,
        choices=["md", "markdown", "json"],
        default="md",
        help="Output format (default: md)",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output file path (default: stdout)",
    )
    parser.add_argument(
        "--data",
        type=str,
        default="data/trails.json",
        help="Path to trail data JSON (default: data/trails.json)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Include all claims (no filter)",
    )
    args = parser.parse_args()

    data_path = Path(args.data)
    if not data_path.is_absolute():
        data_path = PROJECT_ROOT / data_path

    trail_manager = build_trail_manager_from_data(data_path)

    if args.pillar or args.concept_id or args.all:
        scores = grade_evidence(
            trail_manager,
            pillar=args.pillar,
            concept_id=args.concept_id,
        )
        contradiction_report = detect_contradictions(
            trail_manager,
            pillar=args.pillar,
            concept_id=args.concept_id,
        )
    else:
        scores = []
        contradiction_report = ContradictionReport()

    if args.format in ("md", "markdown"):
        output = generate_markdown_report(
            scores, contradiction_report,
            pillar=args.pillar,
            concept_id=args.concept_id,
        )
    else:
        output = generate_json_report(
            scores, contradiction_report,
            pillar=args.pillar,
            concept_id=args.concept_id,
        )

    if args.output:
        out_path = Path(args.output)
        if not out_path.is_absolute():
            out_path = PROJECT_ROOT / out_path
        out_path.write_text(output)
        print(f"Report written to {out_path}")
    else:
        print(output)


if __name__ == "__main__":
    main()
