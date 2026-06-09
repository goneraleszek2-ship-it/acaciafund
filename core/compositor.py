"""SVG compositing engine for the Graphics-as-Code pipeline.

Takes structured data from extractors and renders inline SVG
visualizations: timelines, process flows, comparison tables.
"""

import html
import math
from typing import Any

PILLAR_COMPOSITOR_COLORS = {
    "aml":              {"line": "#d97706", "fill": "rgba(217,119,6,0.12)", "text": "#d97706", "border": "#d97706"},
    "stock":            {"line": "#22c55e", "fill": "rgba(34,197,94,0.12)",  "text": "#22c55e", "border": "#22c55e"},
    "data-engineering": {"line": "#6366f1", "fill": "rgba(99,102,241,0.12)", "text": "#6366f1", "border": "#6366f1"},
}
_FALLBACK = {"line": "#6b7280", "fill": "rgba(107,114,128,0.08)", "text": "#6b7280", "border": "#6b7280"}


def _pal(pillar: str) -> dict:
    return PILLAR_COMPOSITOR_COLORS.get(pillar, _FALLBACK)


# ── Timeline SVG ───────────────────────────────────────────────

def render_timeline(events: list[dict], pillar: str = "", width: int = 600, height: int | None = None) -> str:
    """Render a vertical timeline as inline SVG.

    Each event: {date, event}
    Returns complete <svg> string.
    """
    if not events:
        return ""
    pal = _pal(pillar)
    n = len(events)
    item_h = 52
    pad_top = 20
    pad_bot = 20
    h = height or (pad_top + n * item_h + pad_bot)
    line_x = 120

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{h}" viewBox="0 0 {width} {h}" class="gac-timeline">',
        f'<rect width="{width}" height="{h}" fill="none"/>',
    ]

    title_y = pad_top - 4
    parts.append(
        f'<text x="14" y="{title_y}" fill="var(--color-text-secondary, #475569)" '
        f'font-family="system-ui,sans-serif" font-size="9" font-weight="600" '
        f'letter-spacing="0.5">TIMELINE</text>'
    )

    for i, ev in enumerate(events):
        y = pad_top + i * item_h
        date_str = html.escape(str(ev.get("date", "")))
        event_str = html.escape(str(ev.get("event", ""))[:110])

        # Vertical line
        parts.append(
            f'<line x1="{line_x}" y1="{y + 6}" x2="{line_x}" y2="{y + item_h - 4}" '
            f'stroke="{pal["line"]}" stroke-width="1.5" opacity="0.25"/>'
        )
        # Dot on timeline
        parts.append(
            f'<circle cx="{line_x}" cy="{y + 6}" r="4" fill="{pal["line"]}" opacity="0.7"/>'
        )
        # Date label
        parts.append(
            f'<text x="{line_x - 10}" y="{y + 10}" text-anchor="end" '
            f'fill="{pal["text"]}" font-family="system-ui,sans-serif" '
            f'font-size="11" font-weight="600">{date_str}</text>'
        )
        # Event text
        parts.append(
            f'<text x="{line_x + 16}" y="{y + 10}" '
            f'fill="var(--color-text, #e8e6e3)" font-family="system-ui,sans-serif" '
            f'font-size="12">{event_str}</text>'
        )

    parts.append("</svg>")
    return "\n".join(parts)


# ── Flow Diagram SVG ───────────────────────────────────────────

def render_flow(steps: list[dict], pillar: str = "", width: int = 600, height: int | None = None) -> str:
    """Render a process flow as left-to-right connected boxes.

    Each step: {step, description}
    Returns complete <svg> string.
    """
    if not steps:
        return ""
    pal = _pal(pillar)
    n = len(steps)
    box_w = 160
    box_h = 40
    gap_x = 40
    gap_y = 10
    pad = 16

    cols = max(1, (width - pad * 2 + gap_x) // (box_w + gap_x))
    cols = min(cols, n)
    rows = (n + cols - 1) // cols

    total_w = max(width, cols * (box_w + gap_x) - gap_x + pad * 2)
    total_h = height or (pad * 2 + rows * (box_h + gap_y) - gap_y)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{total_w}" height="{total_h}" viewBox="0 0 {total_w} {total_h}" class="gac-flow">',
        f'<rect width="{total_w}" height="{total_h}" fill="none"/>',
    ]

    title_y = pad - 4
    parts.append(
        f'<text x="14" y="{title_y}" fill="var(--color-text-secondary, #475569)" '
        f'font-family="system-ui,sans-serif" font-size="9" font-weight="600" '
        f'letter-spacing="0.5">FLOW</text>'
    )

    for i, step in enumerate(steps):
        col = i % cols
        row = i // cols
        x = pad + col * (box_w + gap_x)
        y = pad + row * (box_h + gap_y) + 6
        desc = html.escape(str(step.get("description", ""))[:100])

        # Box
        parts.append(
            f'<rect x="{x}" y="{y}" width="{box_w}" height="{box_h}" rx="6" '
            f'fill="{pal["fill"]}" stroke="{pal["border"]}" stroke-width="1" opacity="0.85"/>'
        )
        # Step number badge
        parts.append(
            f'<circle cx="{x + 14}" cy="{y + 14}" r="9" fill="{pal["line"]}" opacity="0.85"/>'
        )
        parts.append(
            f'<text x="{x + 14}" y="{y + 18}" text-anchor="middle" fill="#fff" '
            f'font-family="system-ui,sans-serif" font-size="9" font-weight="700">{step.get("step", i + 1)}</text>'
        )
        # Description text
        parts.append(
            f'<text x="{x + 28}" y="{y + 18}" '
            f'fill="var(--color-text, #e8e6e3)" font-family="system-ui,sans-serif" '
            f'font-size="10">{desc}</text>'
        )
        # Arrow to next
        if i < n - 1:
            next_col = (i + 1) % cols
            if next_col > col:
                # Right arrow
                ax = x + box_w + 2
                ay = y + box_h // 2
                parts.append(
                    f'<line x1="{ax}" y1="{ay}" x2="{ax + gap_x - 6}" y2="{ay}" '
                    f'stroke="{pal["line"]}" stroke-width="1.5" marker-end="url(#arrow-{id(pal)})" opacity="0.5"/>'
                )

    # Define arrow marker
    marker_id = f"arrow-{id(pal)}"
    arrow_def = (
        f'<defs><marker id="{marker_id}" viewBox="0 0 10 10" refX="8" refY="5" '
        f'markerWidth="6" markerHeight="6" orient="auto">'
        f'<path d="M0,0 L10,5 L0,10 Z" fill="{pal["line"]}" opacity="0.5"/>'
        f'</marker></defs>'
    )
    parts.insert(2, arrow_def)

    parts.append("</svg>")
    return "\n".join(parts)


# ── Comparison Table SVG ───────────────────────────────────────

def render_comparisons(comparisons: list[dict], pillar: str = "", width: int = 600, height: int | None = None) -> str:
    """Render comparisons as a small table.

    Each comparison: {entity_a, entity_b, metric, value_a, value_b}
    Returns complete <svg> string.
    """
    if not comparisons:
        return ""
    pal = _pal(pillar)
    n = len(comparisons)
    row_h = 28
    col_w = [160, 80, 80]
    header_h = 22
    pad = 16

    total_w = max(width, sum(col_w) + pad * 2)
    total_h = height or (pad * 2 + header_h + n * row_h)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{total_w}" height="{total_h}" viewBox="0 0 {total_w} {total_h}" class="gac-comparison">',
        f'<rect width="{total_w}" height="{total_h}" fill="none"/>',
    ]

    title_y = pad - 4
    parts.append(
        f'<text x="14" y="{title_y}" fill="var(--color-text-secondary, #475569)" '
        f'font-family="system-ui,sans-serif" font-size="9" font-weight="600" '
        f'letter-spacing="0.5">COMPARISONS</text>'
    )

    x_start = pad
    y_start = pad + 6

    def _text(x: int, y: int, txt: str, cls: str = "", size: int = 10, fw: str = "500", anchor: str = "start"):
        return (
            f'<text x="{x}" y="{y}" text-anchor="{anchor}" fill="{cls}" '
            f'font-family="system-ui,sans-serif" font-size="{size}" font-weight="{fw}">'
            f'{html.escape(txt)}</text>'
        )

    def _line(y: int, opacity: str = "0.08"):
        return f'<line x1="{x_start}" y1="{y}" x2="{x_start + sum(col_w)}" y2="{y}" stroke="var(--color-text, #e8e6e3)" stroke-width="1" opacity="{opacity}"/>'

    # Header
    headers = ["Entity / Metric", "Value A", "Value B"]
    cx = x_start
    for i, hdr in enumerate(headers):
        cw = col_w[i]
        parts.append(
            _text(cx + 6, y_start + header_h - 6, hdr,
                  cls="var(--color-text-secondary, #475569)", size=9, fw="600")
        )
        cx += cw
    parts.append(_line(y_start + header_h))

    # Rows
    for i, comp in enumerate(comparisons):
        ry = y_start + header_h + i * row_h
        entity = html.escape(str(comp.get("entity_a", ""))[:35])
        metric = str(comp.get("metric", ""))
        va = html.escape(str(comp.get("value_a", ""))[:15])
        vb = html.escape(str(comp.get("value_b", ""))[:15])

        display = f"{entity} ({metric})" if metric and metric not in ("comparison", "change") else entity
        parts.append(
            _text(x_start + 6, ry + row_h - 8, display, cls="var(--color-text, #e8e6e3)", size=10)
        )
        parts.append(
            _text(x_start + col_w[0] + 6, ry + row_h - 8, va,
                  cls=pal["text"], size=10, fw="600")
        )
        if vb:
            parts.append(
                _text(x_start + col_w[0] + col_w[1] + 6, ry + row_h - 8, vb,
                      cls="var(--color-text, #e8e6e3)", size=10)
            )

    parts.append("</svg>")
    return "\n".join(parts)


# ── Entity Badges SVG ──────────────────────────────────────────

def render_entity_badges(entities: list[str], pillar: str = "", width: int = 580) -> str:
    """Render a horizontal tag cloud of named entities."""
    if not entities:
        return ""
    pal = _pal(pillar)
    n = len(entities)
    badge_h = 24
    gap = 8
    pad = 14
    cols = min(4, n)
    rows = (n + cols - 1) // cols
    total_h = pad * 2 + rows * (badge_h + gap)
    total_w = max(width, 280)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{total_w}" height="{total_h}" viewBox="0 0 {total_w} {total_h}" class="gac-entities">',
        f'<rect width="{total_w}" height="{total_h}" fill="none"/>',
    ]
    parts.append(
        f'<text x="14" y="{pad - 4}" fill="var(--color-text-secondary, #475569)" '
        f'font-family="system-ui,sans-serif" font-size="9" font-weight="600" '
        f'letter-spacing="0.5">KEY ENTITIES</text>'
    )

    col_w = (total_w - pad * 2 - (cols - 1) * gap) // cols
    for i, ent in enumerate(entities):
        col = i % cols
        row = i // cols
        x = pad + col * (col_w + gap)
        y = pad + 6 + row * (badge_h + gap)
        safe = html.escape(ent[:25])
        parts.append(
            f'<rect x="{x}" y="{y}" width="{col_w}" height="{badge_h}" rx="12" '
            f'fill="{pal["fill"]}" stroke="{pal["border"]}" stroke-width="0.8" opacity="0.85"/>'
        )
        parts.append(
            f'<text x="{x + col_w // 2}" y="{y + badge_h // 2 + 1}" text-anchor="middle" '
            f'dominant-baseline="middle" fill="{pal["text"]}" '
            f'font-family="system-ui,sans-serif" font-size="10">{safe}</text>'
        )

    parts.append("</svg>")
    return "\n".join(parts)


# ── Key Numbers SVG ────────────────────────────────────────────

def render_key_numbers(numbers: list[dict], pillar: str = "", width: int = 580) -> str:
    """Render key numeric metrics as styled tiles.

    Each item: {value, label}
    """
    if not numbers:
        return ""
    pal = _pal(pillar)
    n = min(len(numbers), 6)
    cols = min(3, n)
    rows = (n + cols - 1) // cols
    gap = 8
    pad = 14
    tile_w = (width - pad * 2 - (cols - 1) * gap) // cols
    tile_h = 56
    total_h = pad * 2 + rows * (tile_h + gap)
    total_w = max(width, 220)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{total_w}" height="{total_h}" viewBox="0 0 {total_w} {total_h}" class="gac-numbers">',
        f'<rect width="{total_w}" height="{total_h}" fill="none"/>',
    ]
    parts.append(
        f'<text x="14" y="{pad - 4}" fill="var(--color-text-secondary, #475569)" '
        f'font-family="system-ui,sans-serif" font-size="9" font-weight="600" '
        f'letter-spacing="0.5">KEY NUMBERS</text>'
    )

    for i, item in enumerate(numbers):
        col = i % cols
        row = i // cols
        x = pad + col * (tile_w + gap)
        y = pad + 6 + row * (tile_h + gap)
        val = html.escape(str(item.get("value", ""))[:12])
        label = html.escape(str(item.get("label", ""))[:20])

        # Background tile
        parts.append(
            f'<rect x="{x}" y="{y}" width="{tile_w}" height="{tile_h}" rx="6" '
            f'fill="{pal["fill"]}" stroke="{pal["border"]}" stroke-width="0.6" opacity="0.75"/>'
        )
        # Value
        parts.append(
            f'<text x="{x + tile_w // 2}" y="{y + 22}" text-anchor="middle" '
            f'fill="{pal["text"]}" font-family="system-ui,sans-serif" '
            f'font-size="18" font-weight="700">{val}</text>'
        )
        # Label
        if label:
            parts.append(
                f'<text x="{x + tile_w // 2}" y="{y + 36}" text-anchor="middle" '
                f'fill="var(--color-text-secondary, #475569)" font-family="system-ui,sans-serif" '
                f'font-size="8">{label}</text>'
            )

    parts.append("</svg>")
    return "\n".join(parts)


# ── Connections SVG ────────────────────────────────────────────

def render_connections(connections: list[str], pillar: str = "", width: int = 580) -> str:
    """Render cross-pillar connections as a compact badge row."""
    if not connections:
        return ""
    pal = _pal(pillar)
    n = len(connections)
    gap = 8
    pad = 14
    total_h = 44
    total_w = max(width, 200)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{total_w}" height="{total_h}" viewBox="0 0 {total_w} {total_h}" class="gac-connections">',
        f'<rect width="{total_w}" height="{total_h}" fill="none"/>',
    ]
    parts.append(
        f'<text x="14" y="{pad - 4}" fill="var(--color-text-secondary, #475569)" '
        f'font-family="system-ui,sans-serif" font-size="9" font-weight="600" '
        f'letter-spacing="0.5">CONNECTIONS</text>'
    )

    cx = pad
    cy = pad + 8
    for conn in connections:
        safe = html.escape(conn.strip()[:30])
        bw = max(40, len(safe) * 7 + 16)
        parts.append(
            f'<rect x="{cx}" y="{cy}" width="{bw}" height="20" rx="10" '
            f'fill="{pal["fill"]}" stroke="{pal["border"]}" stroke-width="0.6"/>'
        )
        parts.append(
            f'<text x="{cx + bw // 2}" y="{cy + 14}" text-anchor="middle" '
            f'fill="{pal["text"]}" font-family="system-ui,sans-serif" '
            f'font-size="9">{safe}</text>'
        )
        cx += bw + gap

    parts.append("</svg>")
    return "\n".join(parts)


# ── Auto-compose: pick best visualization type ─────────────────

def auto_compose(body_text: str, pillar: str = "", width: int = 600) -> list[dict[str, Any]]:
    """Run all extractors on body text and return rendered SVGs with labels.

    Returns list of {type, label, svg} dicts for any data found.
    """
    from core.extractors import extract_timeline, extract_flow, extract_comparisons

    results: list[dict] = []

    timeline = extract_timeline(body_text)
    if len(timeline) >= 2:
        h = 28 + len(timeline) * 52
        svg = render_timeline(timeline, pillar=pillar, width=width, height=h)
        results.append({"type": "timeline", "label": "Timeline", "svg": svg})

    flow = extract_flow(body_text)
    if len(flow) >= 2:
        rows = (len(flow) + 3) // 4
        h = 24 + rows * 56
        svg = render_flow(flow, pillar=pillar, width=width, height=h)
        results.append({"type": "flow", "label": "Process Flow", "svg": svg})

    comparisons = extract_comparisons(body_text)
    if comparisons:
        n = min(len(comparisons), 5)
        h = 24 + 22 + n * 28
        svg = render_comparisons(comparisons[:n], pillar=pillar, width=width, height=h)
        results.append({"type": "comparison", "label": "Comparisons", "svg": svg})

    return results
