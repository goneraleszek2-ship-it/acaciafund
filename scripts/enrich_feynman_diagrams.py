#!/usr/bin/env python3
"""Generate `feynman_diagram` SVGs for every ontology concept.

The Feynman diagram layer (`feynman_diagram` field) is the only Feynman field
left empty for all 199 concepts — `scripts/enrich_feynman.py` generates every
other stage but skips diagrams. This script closes that gap by rendering a
deterministic relationship diagram for each concept from the real ontology
`requires` relations:

    [prerequisite]  →  [ CONCEPT ]  →  [dependent]

Left = concepts this concept requires. Right = concepts that require this one.
Concepts with no `requires` relations render a self-contained "foundation"
node. Output is deterministic (sorted by label, no runtime memory addresses),
matches the site's pillar color scheme, and is escaped for safe embedding.

Usage:
    python3 scripts/enrich_feynman_diagrams.py            # write diagrams
    python3 scripts/enrich_feynman_diagrams.py --dry-run  # preview without saving
"""

from __future__ import annotations

import html
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ONTOLOGY_PATH = PROJECT_ROOT / "data" / "ontology.json"

PILLAR_COLORS = {
    "aml": {"line": "#d97706", "fill": "rgba(217,119,6,0.12)", "text": "#d97706", "border": "#d97706"},
    "stock": {"line": "#22c55e", "fill": "rgba(34,197,94,0.12)", "text": "#22c55e", "border": "#22c55e"},
    "data-engineering": {"line": "#6366f1", "fill": "rgba(99,102,241,0.12)", "text": "#6366f1", "border": "#6366f1"},
}
_FALLBACK = {"line": "#6b7280", "fill": "rgba(107,114,128,0.08)", "text": "#6b7280", "border": "#6b7280"}

_MAX_SIDE_NODES = 3
_CENTRAL_W = 230
_CENTRAL_H = 58
_SIDE_W = 168
_SIDE_H = 44
_WIDTH = 620
_MARKER_IDS: set[str] = set()


def _pal(pillar: str) -> dict:
    return PILLAR_COLORS.get(pillar, _FALLBACK)


def _trunc(label: str, limit: int = 24) -> str:
    if len(label) <= limit:
        return label
    return label[: limit - 1] + "…"


def _node(x: int, y: int, w: int, h: int, label: str, color: dict, center: bool = False) -> str:
    radius = 8 if center else 6
    fill = color["fill"] if center else "rgba(30,30,34,0.6)"
    stroke = color["border"]
    parts = [
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="1" opacity="0.92"/>'
    ]
    parts.append(
        f'<text x="{x + w / 2}" y="{y + h / 2}" text-anchor="middle" dominant-baseline="middle" '
        f'fill="{color["text"]}" font-family="system-ui,sans-serif" font-size="11" '
        f'font-weight="{600 if center else 400}">{html.escape(_trunc(label))}</text>'
    )
    return "\n".join(parts)


def _arrow(x1: int, y1: int, x2: int, y2: int, color: dict, marker_id: str) -> str:
    return (
        f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color["line"]}" '
        f'stroke-width="1.4" opacity="0.55" marker-end="url(#{marker_id})"/>'
    )


def _marker_def(marker_id: str, color: dict) -> str:
    if marker_id in _MARKER_IDS:
        return ""
    _MARKER_IDS.add(marker_id)
    return (
        f'<defs><marker id="{marker_id}" viewBox="0 0 10 10" refX="8" refY="5" '
        f'markerWidth="6" markerHeight="6" orient="auto">'
        f'<path d="M0,0 L10,5 L0,10 Z" fill="{color["line"]}" opacity="0.55"/>'
        f"</marker></defs>"
    )


def render_feynman_diagram(
    concept_id: str,
    label: str,
    pillar: str,
    prerequisites: list[str],
    dependents: list[str],
) -> str:
    """Deterministic relationship-diagram SVG for a single concept."""
    color = _pal(pillar)
    marker_id = f"fd-arrow-{pillar or 'misc'}"

    prereqs = sorted(prerequisites)[:_MAX_SIDE_NODES]
    deps = sorted(dependents)[:_MAX_SIDE_NODES]
    side = max(len(prereqs), len(deps))
    rows = max(1, side)
    row_h = _SIDE_H + 18
    pad = 14
    title_h = 14

    center_y = int(title_h + pad + (rows * row_h - _CENTRAL_H) / 2)
    left_x = pad
    center_x = left_x + _SIDE_W + 44
    right_x = center_x + _CENTRAL_W + 44
    total_h = title_h + pad * 2 + rows * row_h
    total_w = _WIDTH

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{total_w}" height="{total_h}" '
        f'viewBox="0 0 {total_w} {total_h}" class="feynman-diagram" role="img" '
        f'aria-label="Diagram of {html.escape(label)}">',
        _marker_def(marker_id, color),
        f'<text x="14" y="10" fill="{color["text"]}" font-family="system-ui,sans-serif" '
        f'font-size="9" font-weight="600" letter-spacing="0.5" opacity="0.8">'
        f'REQUIRES \u2192 \u2192 ENABLES</text>',
    ]

    # Left column: prerequisites
    for i, pid in enumerate(prereqs):
        y = title_h + pad + i * row_h
        parts.append(_node(left_x, y, _SIDE_W, _SIDE_H, pid, color))
        parts.append(_arrow(left_x + _SIDE_W, y + _SIDE_H // 2, center_x, center_y + _CENTRAL_H // 2, color, marker_id))

    # Right column: dependents
    for i, did in enumerate(deps):
        y = title_h + pad + i * row_h
        parts.append(_node(right_x, y, _SIDE_W, _SIDE_H, did, color))
        parts.append(_arrow(center_x + _CENTRAL_W, center_y + _CENTRAL_H // 2, right_x, y + _SIDE_H // 2, color, marker_id))

    # Central concept
    parts.append(_node(center_x, center_y, _CENTRAL_W, _CENTRAL_H, label, color, center=True))

    if not prereqs and not deps:
        parts.append(
            f'<text x="{_WIDTH / 2}" y="{total_h - 16}" text-anchor="middle" '
            f'fill="var(--color-text-secondary, #475569)" font-family="system-ui,sans-serif" '
            f'font-size="10">Foundation concept — no formal prerequisites</text>'
        )

    parts.append("</svg>")
    return "\n".join(parts)


def build_diagram_map() -> dict[str, str]:
    ontology = json.loads(ONTOLOGY_PATH.read_text(encoding="utf-8"))
    concepts = {c["id"]: c for c in ontology["concepts"]}
    labels = {cid: c["label"] for cid, c in concepts.items()}

    prereq_map: dict[str, list[str]] = {cid: [] for cid in concepts}
    dep_map: dict[str, list[str]] = {cid: [] for cid in concepts}
    for rel in ontology.get("relations", []):
        if rel.get("relation_type") != "requires":
            continue
        src, tgt = rel.get("source_id"), rel.get("target_id")
        if src in concepts and tgt in concepts:
            prereq_map[src].append(labels[tgt])  # this concept requires -> target is prereq
            dep_map[tgt].append(labels[src])  # source requires this concept -> source is dependent

    diagrams: dict[str, str] = {}
    for cid, c in concepts.items():
        diagrams[cid] = render_feynman_diagram(
            cid, c["label"], c.get("pillar", ""),
            prereq_map[cid], dep_map[cid],
        )
    return diagrams


def main() -> int:
    dry_run = "--dry-run" in sys.argv
    diagrams = build_diagram_map()

    ontology = json.loads(ONTOLOGY_PATH.read_text(encoding="utf-8"))
    updated = 0
    for c in ontology["concepts"]:
        new_svg = diagrams[c["id"]]
        if c.get("feynman_diagram") != new_svg:
            c["feynman_diagram"] = new_svg
            updated += 1

    print(f"feynman_diagram coverage: {sum(1 for c in ontology['concepts'] if c.get('feynman_diagram'))}/{len(ontology['concepts'])} concepts")
    if dry_run:
        print(f"dry-run: would update {updated} concepts")
        return 0

    ONTOLOGY_PATH.write_text(
        json.dumps(ontology, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"updated {updated} concepts in {ONTOLOGY_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
