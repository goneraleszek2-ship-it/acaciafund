"""AcaciaFund Brand Visual System — single source of truth.

Generates all brand SVG assets: logo, domain icons, micro-icons,
domain patterns, and sparklines. Pure Python, no dependencies.

Usage:
    from core.brand import brand_logo_svg, brand_domain_icon, brand_micro_icon
    logo_html = brand_logo_svg(size=48)
    shield = brand_domain_icon("aml", size=24)
    clock = brand_micro_icon("time", size=16)
"""

from __future__ import annotations

import math
from typing import Optional


# ─────────────────────────────────────────────
# 1. CANONICAL BRAND TOKENS
# ─────────────────────────────────────────────

BRAND: dict[str, dict[str, str]] = {
    "aml": {
        "primary":   "#c97d3e",
        "secondary": "#d97706",
        "dark":      "#0f172a",
        "darker":    "#020617",
        "accent":    "#fbbf24",
        "label":     "AML",
    },
    "markets": {
        "primary":   "#3a7d5c",
        "secondary": "#22c55e",
        "dark":      "#052e16",
        "darker":    "#022c22",
        "accent":    "#6ee7b7",
        "label":     "MKT",
    },
    "science": {
        "primary":   "#6366f1",
        "secondary": "#818cf8",
        "dark":      "#1e1b4b",
        "darker":    "#0f0a3a",
        "accent":    "#a5b4fc",
        "label":     "SCI",
    },
}

# Alias: content_type slug → brand key
PILLAR_MAP: dict[str, str] = {
    "aml": "aml",
    "stock": "markets",
    "data-engineering": "science",
}

NEUTRAL = {
    "bg":       "#1a1a2e",
    "surface":  "#1f1f36",
    "border":   "#2d2d4a",
    "text":     "#e8e6e3",
    "muted":    "#9d9bb0",
    "bone":     "#f5f3ee",
}

Stroke = float


def _brand_key(pillar: str) -> str:
    """Resolve pillar slug to canonical brand key."""
    return PILLAR_MAP.get(pillar, pillar)


# ─────────────────────────────────────────────
# 2. PRIMARY MARK — Acacia Leaf + Data Node
# ─────────────────────────────────────────────

def brand_logo_svg(size: int = 48, color: str | None = None) -> str:
    """Geometric acacia leaf intersecting with a 3-node graph.

    The leaf is 3 angular segments (like a stylized acacia canopy).
    The node graph has 3 circles connected by edges, sitting at the
    leaf's stem base — symbolizing growth meets intelligence.

    Args:
        size: Output width/height in px.
        color: Override color (default: amber gradient).
    """
    c = color or BRAND["aml"]["primary"]
    accent = BRAND["aml"]["accent"]
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 48 48" fill="none">'
        f'<defs>'
        f'<linearGradient id="leaf" x1="0%" y1="0%" x2="100%" y2="100%">'
        f'<stop offset="0%" stop-color="{c}"/>'
        f'<stop offset="100%" stop-color="{accent}"/>'
        f'</linearGradient>'
        f'</defs>'
        # Leaf — 3 angular segments
        f'<path d="M24 6L14 20h20L24 6z" fill="url(#leaf)" opacity="0.9"/>'
        f'<path d="M18 12L10 24h16L18 12z" fill="{c}" opacity="0.6"/>'
        f'<path d="M30 12L22 24h16L30 12z" fill="{accent}" opacity="0.5"/>'
        # Stem
        f'<line x1="24" y1="24" x2="24" y2="36" stroke="{c}" stroke-width="2" stroke-linecap="round"/>'
        # Node graph — 3 nodes at stem base
        f'<circle cx="24" cy="38" r="3" fill="{c}" stroke="{NEUTRAL["bg"]}" stroke-width="1.5"/>'
        f'<circle cx="16" cy="42" r="2.5" fill="{accent}" stroke="{NEUTRAL["bg"]}" stroke-width="1.5"/>'
        f'<circle cx="32" cy="42" r="2.5" fill="{accent}" stroke="{NEUTRAL["bg"]}" stroke-width="1.5"/>'
        # Edges
        f'<line x1="24" y1="38" x2="16" y2="42" stroke="{c}" stroke-width="1.2" opacity="0.7"/>'
        f'<line x1="24" y1="38" x2="32" y2="42" stroke="{c}" stroke-width="1.2" opacity="0.7"/>'
        f'<line x1="16" y1="42" x2="32" y2="42" stroke="{accent}" stroke-width="0.8" opacity="0.4"/>'
        f'</svg>'
    )


# ─────────────────────────────────────────────
# 3. DOMAIN ICONS — 24×24, 2px stroke
# ─────────────────────────────────────────────

def brand_domain_icon(pillar: str, size: int = 24, color: str | None = None) -> str:
    """Domain-specific geometric icon.

    AML     → Shield + internal network (protection, typologies)
    Markets → Ascending line chart + signal pulse
    Science → Neuron soma + 3 dendrite branches + spark

    Args:
        pillar: "aml", "stock", or "data-engineering".
        size: Output size in px.
        color: Override stroke color.
    """
    key = _brand_key(pillar)
    palette = BRAND.get(key, BRAND["aml"])
    c = color or palette["primary"]
    accent = palette["accent"]

    icons = {
        "aml": (
            # Shield outline
            f'<path d="M12 3L4 7v6c0 5.5 3.4 10.7 8 12 4.6-1.3 8-6.5 8-12V7L12 3z" '
            f'fill="none" stroke="{c}" stroke-width="2" stroke-linejoin="round"/>'
            # Internal network — 3 nodes + edges
            f'<circle cx="12" cy="14" r="2" fill="{accent}"/>'
            f'<circle cx="8" cy="18" r="1.5" fill="{c}" opacity="0.7"/>'
            f'<circle cx="16" cy="18" r="1.5" fill="{c}" opacity="0.7"/>'
            f'<line x1="12" y1="14" x2="8" y2="18" stroke="{c}" stroke-width="1" opacity="0.5"/>'
            f'<line x1="12" y1="14" x2="16" y2="18" stroke="{c}" stroke-width="1" opacity="0.5"/>'
            f'<line x1="8" y1="18" x2="16" y2="18" stroke="{accent}" stroke-width="0.8" opacity="0.3"/>'
        ),
        "markets": (
            # Ascending line chart
            f'<polyline points="3,18 7,14 11,16 15,10 19,8 23,5" '
            f'fill="none" stroke="{c}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'
            # Signal pulse (vertical bar at peak)
            f'<line x1="23" y1="3" x2="23" y2="8" stroke="{accent}" stroke-width="2" stroke-linecap="round"/>'
            # Baseline
            f'<line x1="2" y1="21" x2="22" y2="21" stroke="{c}" stroke-width="1" opacity="0.3"/>'
            # Signal dot
            f'<circle cx="23" cy="3" r="1.5" fill="{accent}"/>'
        ),
        "science": (
            # Neuron soma (center)
            f'<circle cx="12" cy="12" r="4" fill="none" stroke="{c}" stroke-width="2"/>'
            f'<circle cx="12" cy="12" r="1.5" fill="{accent}"/>'
            # Dendrite branches — 3 paths radiating out
            f'<path d="M12 8V3" stroke="{c}" stroke-width="1.5" stroke-linecap="round"/>'
            f'<path d="M12 8L9 5" stroke="{c}" stroke-width="1" stroke-linecap="round" opacity="0.6"/>'
            f'<path d="M12 8L15 5" stroke="{c}" stroke-width="1" stroke-linecap="round" opacity="0.6"/>'
            f'<path d="M8.3 12H3" stroke="{c}" stroke-width="1.5" stroke-linecap="round"/>'
            f'<path d="M8.3 12L5 9" stroke="{c}" stroke-width="1" stroke-linecap="round" opacity="0.6"/>'
            f'<path d="M15.7 12H21" stroke="{c}" stroke-width="1.5" stroke-linecap="round"/>'
            f'<path d="M15.7 12L19 15" stroke="{c}" stroke-width="1" stroke-linecap="round" opacity="0.6"/>'
            # Spark at top
            f'<path d="M12 3l1 2-1 1" stroke="{accent}" stroke-width="1.2" stroke-linecap="round" fill="none"/>'
        ),
    }

    svg_content = icons.get(key, icons["aml"])
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 24 24" fill="none">{svg_content}</svg>'
    )


# ─────────────────────────────────────────────
# 4. MICRO-ICONS — 16×16, 1.5px stroke
# ─────────────────────────────────────────────

_MICRO_ICONS: dict[str, str] = {
    "time": (
        # Clock face
        f'<circle cx="8" cy="8" r="6.5" fill="none" stroke="currentColor" stroke-width="1.5"/>'
        f'<line x1="8" y1="4" x2="8" y2="8" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>'
        f'<line x1="8" y1="8" x2="11" y2="10" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>'
    ),
    "source": (
        # Document with arrow
        f'<rect x="2" y="1" width="9" height="12" rx="1.5" fill="none" stroke="currentColor" stroke-width="1.5"/>'
        f'<path d="M5 4h3M5 6h5M5 8h4" stroke="currentColor" stroke-width="1" stroke-linecap="round" opacity="0.6"/>'
        f'<path d="M11 7l3 0 0-3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" fill="none"/>'
        f'<path d="M14 4l-3 3" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>'
    ),
    "difficulty": (
        # 3-tier bars (ascending)
        f'<rect x="1" y="10" width="3" height="5" rx="0.8" fill="currentColor" opacity="0.4"/>'
        f'<rect x="6.5" y="6" width="3" height="9" rx="0.8" fill="currentColor" opacity="0.7"/>'
        f'<rect x="12" y="1" width="3" height="14" rx="0.8" fill="currentColor"/>'
    ),
    "domain": (
        # 3 overlapping circles (Venn)
        f'<circle cx="8" cy="6" r="4" fill="none" stroke="currentColor" stroke-width="1.3"/>'
        f'<circle cx="5.5" cy="10" r="4" fill="none" stroke="currentColor" stroke-width="1.3"/>'
        f'<circle cx="10.5" cy="10" r="4" fill="none" stroke="currentColor" stroke-width="1.3"/>'
    ),
    "version": (
        # Tag with dot
        f'<path d="M1 8.5V2.5a1.5 1.5 0 011.5-1.5H9l5.5 5.5-7 7L1 8.5z" '
        f'fill="none" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/>'
        f'<circle cx="4.5" cy="5.5" r="1.2" fill="currentColor"/>'
    ),
    "tags": (
        # Tag stack
        f'<path d="M1 9V3a1 1 0 011-1h6l6 6-6 6-7-7z" fill="none" stroke="currentColor" stroke-width="1.4"/>'
        f'<circle cx="4" cy="5" r="1" fill="currentColor"/>'
    ),
    "link": (
        # Chain link
        f'<path d="M6.5 9.5a3.5 3.5 0 005 0l2-2a3.5 3.5 0 00-5-5l-1 1" '
        f'fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>'
        f'<path d="M9.5 6.5a3.5 3.5 0 00-5 0l-2 2a3.5 3.5 0 005 5l1-1" '
        f'fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>'
    ),
    "calendar": (
        # Calendar
        f'<rect x="1.5" y="3" width="13" height="11" rx="1.5" fill="none" stroke="currentColor" stroke-width="1.4"/>'
        f'<line x1="1.5" y1="7" x2="14.5" y2="7" stroke="currentColor" stroke-width="1.2"/>'
        f'<line x1="5" y1="1.5" x2="5" y2="4.5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>'
        f'<line x1="11" y1="1.5" x2="11" y2="4.5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>'
    ),
    "chart": (
        # Mini bar chart
        f'<rect x="1" y="9" width="3" height="6" rx="0.5" fill="currentColor" opacity="0.5"/>'
        f'<rect x="5.5" y="5" width="3" height="10" rx="0.5" fill="currentColor" opacity="0.7"/>'
        f'<rect x="10" y="2" width="3" height="13" rx="0.5" fill="currentColor"/>'
    ),
}


def brand_micro_icon(name: str, size: int = 16, color: str | None = None) -> str:
    """Metadata micro-icon.

    Available: time, source, difficulty, domain, version, tags, link, calendar, chart.

    Args:
        name: Icon name.
        size: Output size in px.
        color: Override color (default: currentColor for CSS inheritance).
    """
    paths = _MICRO_ICONS.get(name, _MICRO_ICONS["time"])
    fill_attr = f' color="{color}"' if color else ""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 16 16"{fill_attr}>{paths}</svg>'
    )


# ─────────────────────────────────────────────
# 5. DOMAIN PATTERNS — subtle background textures
# ─────────────────────────────────────────────

def brand_pattern(pillar: str, width: int = 200, height: int = 200, opacity: float = 0.06) -> str:
    """Domain-specific background pattern SVG.

    AML     → Hexagonal mesh (blockchain/network)
    Markets → Sine waves (Bloomberg terminal style)
    Science → Branching L-system (discovery tree)

    Args:
        pillar: Domain key.
        width: Pattern tile width.
        height: Pattern tile height.
        opacity: Pattern opacity (0-1).
    """
    key = _brand_key(pillar)
    palette = BRAND.get(key, BRAND["aml"])
    c = palette["primary"]

    patterns = {
        "aml": _hex_mesh_pattern(c, width, height, opacity),
        "markets": _wave_pattern(c, width, height, opacity),
        "science": _branch_pattern(c, width, height, opacity),
    }
    return patterns.get(key, patterns["aml"])


def _hex_mesh_pattern(color: str, w: int, h: int, opacity: float) -> str:
    """Hexagonal mesh — each hex is a node in the network."""
    hexes = []
    size = 20
    for row in range(0, h + size, int(size * 1.5)):
        for col in range(0, w + size, int(size * 1.732)):
            offset = size * 0.866 if (row // int(size * 1.5)) % 2 else 0
            cx = col + offset
            cy = row
            if cx <= w and cy <= h:
                pts = []
                for i in range(6):
                    angle = math.pi / 3 * i + math.pi / 6
                    px = cx + size * 0.4 * math.cos(angle)
                    py = cy + size * 0.4 * math.sin(angle)
                    pts.append(f"{px:.1f},{py:.1f}")
                hexes.append(
                    f'<polygon points="{" ".join(pts)}" '
                    f'fill="none" stroke="{color}" stroke-width="0.5" opacity="{opacity}"/>'
                )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
        f'{"".join(hexes)}</svg>'
    )


def _wave_pattern(color: str, w: int, h: int, opacity: float) -> str:
    """Sine waves — like a Bloomberg terminal oscilloscope."""
    waves = []
    for i in range(6):
        y_offset = h * (i + 1) / 7
        amplitude = 8 + i * 2
        freq = 0.02 + i * 0.003
        points = []
        for x in range(0, w + 1, 4):
            y = y_offset + amplitude * math.sin(freq * x + i * 1.2)
            points.append(f"{x},{y:.1f}")
        waves.append(
            f'<polyline points="{" ".join(points)}" '
            f'fill="none" stroke="{color}" stroke-width="0.6" opacity="{opacity}"/>'
        )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
        f'{"".join(waves)}</svg>'
    )


def _branch_pattern(color: str, w: int, h: int, opacity: float) -> str:
    """Branching L-system — discovery tree fractal."""
    branches = []

    def _branch(x: float, y: float, angle: float, depth: int, length: float):
        if depth <= 0 or length < 2:
            return
        ex = x + length * math.cos(angle)
        ey = y + length * math.sin(angle)
        branches.append(
            f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{ex:.1f}" y2="{ey:.1f}" '
            f'stroke="{color}" stroke-width="{0.3 + depth * 0.2:.1f}" '
            f'opacity="{opacity * (0.5 + depth * 0.15):.2f}"/>'
        )
        _branch(ex, ey, angle - 0.45, depth - 1, length * 0.72)
        _branch(ex, ey, angle + 0.45, depth - 1, length * 0.72)

    _branch(w * 0.5, h * 0.95, -math.pi / 2, 5, h * 0.2)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
        f'{"".join(branches)}</svg>'
    )


# ─────────────────────────────────────────────
# 6. SPARKLINE — tiny inline SVG charts
# ─────────────────────────────────────────────

def brand_sparkline(
    data: list[float],
    pillar: str = "aml",
    width: int = 60,
    height: int = 24,
    stroke_width: float = 1.5,
    show_fill: bool = True,
) -> str:
    """Tiny pillar-colored sparkline for metadata cards.

    Args:
        data: List of numeric values (will be normalized to height).
        pillar: Domain key for color.
        width: SVG width.
        height: SVG height.
        stroke_width: Line thickness.
        show_fill: Whether to show area fill under line.
    """
    if not data or len(data) < 2:
        return ""

    key = _brand_key(pillar)
    palette = BRAND.get(key, BRAND["aml"])
    c = palette["primary"]
    accent = palette["accent"]

    mn, mx = min(data), max(data)
    rng = mx - mn if mx != mn else 1
    pad = 2

    points = []
    fill_points = [f"{pad},{height - pad}"]
    for i, v in enumerate(data):
        x = pad + (i / (len(data) - 1)) * (width - 2 * pad)
        y = pad + (1 - (v - mn) / rng) * (height - 2 * pad)
        points.append(f"{x:.1f},{y:.1f}")
        fill_points.append(f"{x:.1f},{y:.1f}")
    fill_points.append(f"{width - pad},{height - pad}")

    line = f'<polyline points="{" ".join(points)}" fill="none" stroke="{c}" stroke-width="{stroke_width}" stroke-linecap="round" stroke-linejoin="round"/>'
    fill = ""
    if show_fill:
        fill = (
            f'<polygon points="{" ".join(fill_points)}" '
            f'fill="{accent}" opacity="0.15"/>'
        )

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">{fill}{line}</svg>'
    )


# ─────────────────────────────────────────────
# 7. SECTION TYPE ICONS (for fallback SVGs)
# ─────────────────────────────────────────────

SECTION_ICONS: dict[int, str] = {
    0: '<circle cx="12" cy="12" r="8" fill="none" stroke-width="1.5"/><circle cx="12" cy="12" r="3"/>',
    1: '<path d="M12 2l3 6h6l-5 4 2 6-6-4-6 4 2-6-5-4h6z" fill="none" stroke-width="1.5"/>',
    2: '<polygon points="8,4 20,12 8,20" fill="none" stroke-width="1.5"/>',
    3: '<rect x="3" y="2" width="18" height="20" rx="2" fill="none" stroke-width="1.5"/><path d="M7 7h10M7 11h10M7 15h6"/>',
    4: '<rect x="3" y="12" width="4" height="10" rx="1" fill="none" stroke-width="1.5"/><rect x="10" y="6" width="4" height="16" rx="1" fill="none" stroke-width="1.5"/><rect x="17" y="2" width="4" height="20" rx="1" fill="none" stroke-width="1.5"/>',
    5: '<circle cx="6" cy="8" r="3" fill="none" stroke-width="1.5"/><circle cx="18" cy="8" r="3" fill="none" stroke-width="1.5"/><circle cx="12" cy="18" r="3" fill="none" stroke-width="1.5"/><line x1="8" y1="10" x2="10" y2="16" stroke-width="1.2"/><line x1="16" y1="10" x2="14" y2="16" stroke-width="1.2"/>',
    6: '<path d="M4 4l4 4-4 4M10 4l4 4-4 4M16 4l4 4-4 4" fill="none" stroke-width="1.5" stroke-linecap="round"/>',
}


def brand_section_icon(index: int, size: int = 24, color: str = "#ffffff") -> str:
    """Section-type icon for fallback SVGs.

    Args:
        index: Section index (0-6).
        size: Output size.
        color: Stroke/fill color.
    """
    paths = SECTION_ICONS.get(index, SECTION_ICONS[0])
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 24 24" fill="{color}" stroke="{color}">{paths}</svg>'
    )
