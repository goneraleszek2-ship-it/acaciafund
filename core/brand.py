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


# ─────────────────────────────────────────────
# 8. SECTION PATTERNS — repeating background tiles
# ─────────────────────────────────────────────

def section_pattern_svg(section_type: int, pillar: str, size: int = 160, opacity: float = 0.08) -> str:
    """Generate a repeating SVG tile for a section type.

    NVIDIA-inspired complex patterns — multiple layers, varying densities,
    conceptually meaningful geometry for each section type:
      0 Overview       — triangular tessellation (GPU parallel processing)
      1 Key Findings   — bursting node network (discovery radiating outward)
      2 Applied Sce.   — circuit board trace (implementation in your domain)
      3 Source Analysis — constellation map (evidence connections)
      4 Domain Breakd. — layered waveform (signal decomposition)
      5 Cross-Pillar   — hexagonal mesh with highlighted paths
      6 Methodology    — recursive L-system branching tree

    Args:
        section_type: Index 0-6.
        pillar: Domain key for color.
        size: Tile width/height.
        opacity: Pattern opacity.
    """
    key = _brand_key(pillar)
    palette = BRAND.get(key, BRAND["aml"])
    c = palette["primary"]
    accent = palette["accent"]

    s = size
    mid = s / 2
    elements = ""

    if section_type == 0:
        # ── Triangular tessellation — GPU parallel processing metaphor ──
        # Three interlocking grids of equilateral triangles
        tri_h = 26  # triangle height
        tri_w = tri_h * 2 / math.sqrt(3)  # triangle width
        # Layer 1: filled triangles (sparse, varying opacity)
        fill_opacities = [0.03, 0.05, 0.07, 0.04, 0.06, 0.08]
        fill_idx = 0
        for row in range(-1, int(s / tri_h) + 2):
            for col in range(-1, int(s / tri_w) + 2):
                x_base = col * tri_w + (row % 2) * tri_w * 0.5
                y_base = row * tri_h
                # Upward triangle
                pts_up = (
                    f"{x_base:.1f},{(y_base + tri_h):.1f} "
                    f"{(x_base + tri_w / 2):.1f},{y_base:.1f} "
                    f"{(x_base + tri_w):.1f},{(y_base + tri_h):.1f}"
                )
                if (row + col) % 3 == 0:
                    op = fill_opacities[fill_idx % len(fill_opacities)]
                    elements += f'<polygon points="{pts_up}" fill="{c}" opacity="{op}"/>'
                    fill_idx += 1
                else:
                    elements += f'<polygon points="{pts_up}" fill="none" stroke="{c}" stroke-width="0.3" opacity="{opacity * 0.4}"/>'
                # Downward triangle
                pts_down = (
                    f"{x_base:.1f},{y_base:.1f} "
                    f"{(x_base + tri_w / 2):.1f},{(y_base + tri_h):.1f} "
                    f"{(x_base + tri_w):.1f},{y_base:.1f}"
                )
                if (row + col) % 5 == 0:
                    elements += f'<polygon points="{pts_down}" fill="{accent}" opacity="{opacity * 0.3}"/>'
                else:
                    elements += f'<polygon points="{pts_down}" fill="none" stroke="{c}" stroke-width="0.2" opacity="{opacity * 0.25}"/>'

    elif section_type == 1:
        # ── Bursting node network — discovery radiating outward ──
        # Central hub + radiating branches with sub-branches and glow nodes
        branches = 6
        for i in range(branches):
            angle = math.radians(i * 360 / branches - 90)
            # Primary branch
            bx = mid + mid * 0.65 * math.cos(angle)
            by = mid + mid * 0.65 * math.sin(angle)
            elements += (
                f'<line x1="{mid}" y1="{mid}" x2="{bx:.1f}" y2="{by:.1f}" '
                f'stroke="{c}" stroke-width="1.0" opacity="{opacity * 1.2}" stroke-linecap="round"/>'
            )
            # Glow at branch end
            elements += (
                f'<circle cx="{bx:.1f}" cy="{by:.1f}" r="5" '
                f'fill="{c}" opacity="{opacity * 0.15}"/>'
            )
            elements += (
                f'<circle cx="{bx:.1f}" cy="{by:.1f}" r="2" '
                f'fill="{accent}" opacity="{opacity * 2.0}"/>'
            )
            # Two sub-branches
            for sub_offset in (-0.35, 0.35):
                sub_angle = angle + sub_offset
                mid_x = mid + mid * 0.35 * math.cos(angle)
                mid_y = mid + mid * 0.35 * math.sin(angle)
                sbx = mid_x + mid * 0.3 * math.cos(sub_angle)
                sby = mid_y + mid * 0.3 * math.sin(sub_angle)
                elements += (
                    f'<line x1="{mid_x:.1f}" y1="{mid_y:.1f}" x2="{sbx:.1f}" y2="{sby:.1f}" '
                    f'stroke="{c}" stroke-width="0.5" opacity="{opacity * 0.7}" stroke-linecap="round"/>'
                )
                elements += (
                    f'<circle cx="{sbx:.1f}" cy="{sby:.1f}" r="1.5" '
                    f'fill="{accent}" opacity="{opacity * 1.2}"/>'
                )
        # Center glow
        elements += f'<circle cx="{mid}" cy="{mid}" r="8" fill="{c}" opacity="{opacity * 0.1}"/>'
        elements += f'<circle cx="{mid}" cy="{mid}" r="3" fill="{accent}" opacity="{opacity * 1.8}"/>'

    elif section_type == 2:
        # ── Circuit board trace — implementation in your domain ──
        # Horizontal + vertical traces with right-angle bends, component pads
        # Layer 1: main traces (thicker, higher opacity)
        traces_h = [0.15, 0.35, 0.55, 0.75, 0.95]
        traces_v = [0.2, 0.4, 0.6, 0.8]
        for y_frac in traces_h:
            y = s * y_frac
            x_start = s * (0.05 + (int(y_frac * 10) % 3) * 0.1)
            x_end = s * (0.95 - (int(y_frac * 7) % 3) * 0.1)
            elements += (
                f'<line x1="{x_start:.1f}" y1="{y:.1f}" x2="{x_end:.1f}" y2="{y:.1f}" '
                f'stroke="{c}" stroke-width="0.8" opacity="{opacity * 1.0}" stroke-linecap="round"/>'
            )
            # Right-angle bend to next horizontal
            if y_frac < 0.9:
                bend_x = x_end if int(y_frac * 10) % 2 == 0 else x_start
                next_y = s * (y_frac + 0.2)
                elements += (
                    f'<line x1="{bend_x:.1f}" y1="{y:.1f}" x2="{bend_x:.1f}" y2="{next_y:.1f}" '
                    f'stroke="{c}" stroke-width="0.6" opacity="{opacity * 0.7}"/>'
                )
        # Layer 2: vertical traces (thinner, lower opacity)
        for x_frac in traces_v:
            x = s * x_frac
            elements += (
                f'<line x1="{x:.1f}" y1="0" x2="{x:.1f}" y2="{s}" '
                f'stroke="{c}" stroke-width="0.3" opacity="{opacity * 0.35}"/>'
            )
        # Component pads (small squares at intersections)
        pad_positions = [
            (0.2, 0.15), (0.6, 0.15), (0.8, 0.35),
            (0.4, 0.55), (0.7, 0.55), (0.2, 0.75),
            (0.5, 0.75), (0.9, 0.95),
        ]
        for px_frac, py_frac in pad_positions:
            px, py = s * px_frac, s * py_frac
            elements += (
                f'<rect x="{px - 2:.1f}" y="{py - 2:.1f}" width="4" height="4" '
                f'fill="{c}" opacity="{opacity * 1.5}" rx="0.5"/>'
            )
            elements += (
                f'<rect x="{px - 1:.1f}" y="{py - 1:.1f}" width="2" height="2" '
                f'fill="{accent}" opacity="{opacity * 2.0}" rx="0.3"/>'
            )

    elif section_type == 3:
        # ── Constellation map — evidence connections ──
        # Fixed star positions connected by thin lines, varying star sizes
        stars = [
            (20, 25, 2.0), (55, 15, 1.5), (90, 30, 2.5), (130, 20, 1.8),
            (35, 60, 2.2), (75, 50, 1.2), (110, 65, 2.0), (145, 55, 1.5),
            (15, 95, 1.8), (50, 90, 2.5), (85, 100, 1.5), (120, 85, 2.0),
            (40, 130, 2.2), (70, 120, 1.8), (105, 135, 1.5), (140, 125, 2.0),
            (25, 150, 1.2), (60, 145, 2.0), (95, 150, 1.8), (130, 148, 1.5),
        ]
        # Draw connecting lines first (behind stars)
        connections = [
            (0, 1), (1, 2), (2, 3), (0, 4), (1, 5), (2, 6), (3, 7),
            (4, 5), (5, 6), (6, 7), (4, 8), (5, 9), (6, 10), (7, 11),
            (8, 9), (9, 10), (10, 11), (8, 12), (9, 13), (10, 14), (11, 15),
            (12, 13), (13, 14), (14, 15), (12, 16), (13, 17), (14, 18), (15, 19),
            (16, 17), (17, 18), (18, 19),
            (1, 5), (5, 9), (9, 13), (13, 17),  # vertical backbone
            (4, 6), (6, 10), (10, 14),  # diagonal
        ]
        for i, j in connections:
            x1, y1, _ = stars[i]
            x2, y2, _ = stars[j]
            elements += (
                f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
                f'stroke="{c}" stroke-width="0.4" opacity="{opacity * 0.5}"/>'
            )
        # Draw stars
        for x, y, r in stars:
            elements += (
                f'<circle cx="{x}" cy="{y}" r="{r}" '
                f'fill="{c}" opacity="{opacity * 1.5}"/>'
            )
            # Glow halo
            elements += (
                f'<circle cx="{x}" cy="{y}" r="{r * 2.5}" '
                f'fill="{c}" opacity="{opacity * 0.12}"/>'
            )

    elif section_type == 4:
        # ── Layered waveform — signal decomposition ──
        # 7 sine waves with varying amplitude, frequency, and opacity
        waves = [
            (18, 0.015, 1.0, 0.0),   # amp, freq, op_mult, phase
            (12, 0.025, 0.85, 0.8),
            (8,  0.035, 0.7,  1.6),
            (22, 0.012, 0.6,  2.4),
            (6,  0.045, 0.9,  3.2),
            (15, 0.020, 0.75, 4.0),
            (10, 0.030, 0.65, 4.8),
        ]
        for i, (amp, freq, op_mult, phase) in enumerate(waves):
            y_base = s * (i + 1) / (len(waves) + 1)
            points = []
            for x in range(0, s + 1, 3):
                y = y_base + amp * math.sin(freq * x + phase)
                points.append(f"{x},{y:.1f}")
            elements += (
                f'<polyline points="{" ".join(points)}" '
                f'fill="none" stroke="{c}" stroke-width="0.8" '
                f'opacity="{opacity * op_mult}" stroke-linecap="round"/>'
            )
            # Accent glow at wave peaks
            if i % 2 == 0:
                peak_x = int((math.pi / 2 - phase) / freq) % s
                peak_y = y_base + amp
                elements += (
                    f'<circle cx="{peak_x}" cy="{peak_y:.1f}" r="2" '
                    f'fill="{accent}" opacity="{opacity * op_mult * 0.8}"/>'
                )

    elif section_type == 5:
        # ── Hexagonal mesh with highlighted paths — cross-domain ──
        # Dense honeycomb: 2 opacity layers, 2 highlighted connection paths
        hex_size = 16
        hex_h = hex_size * 2
        hex_w = hex_size * math.sqrt(3)
        # Layer 1: background hexagons (low opacity)
        for row in range(0, int(s / (hex_h * 0.75)) + 2):
            for col in range(0, int(s / hex_w) + 2):
                cx = col * hex_w + (row % 2) * hex_w * 0.5
                cy = row * hex_h * 0.75
                pts = []
                for k in range(6):
                    angle = math.pi / 3 * k + math.pi / 6
                    px = cx + hex_size * 0.42 * math.cos(angle)
                    py = cy + hex_size * 0.42 * math.sin(angle)
                    pts.append(f"{px:.1f},{py:.1f}")
                op = opacity * 0.5 if (row + col) % 4 != 0 else opacity * 1.0
                elements += (
                    f'<polygon points="{" ".join(pts)}" '
                    f'fill="none" stroke="{c}" stroke-width="0.4" opacity="{op}"/>'
                )
        # Layer 2: highlighted path (trace between distant hexes)
        path_coords = [
            (hex_w * 0.5, hex_h * 0.375),
            (hex_w * 1.5, hex_h * 0.375),
            (hex_w * 2.0, hex_h * 1.125),
            (hex_w * 2.5, hex_h * 1.875),
            (hex_w * 3.0, hex_h * 1.875),
            (hex_w * 3.5, hex_h * 2.625),
        ]
        for i in range(len(path_coords) - 1):
            x1, y1 = path_coords[i]
            x2, y2 = path_coords[i + 1]
            elements += (
                f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                f'stroke="{accent}" stroke-width="1.2" opacity="{opacity * 1.5}" '
                f'stroke-linecap="round"/>'
            )
        # Glow nodes at path vertices
        for x, y in path_coords:
            elements += (
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" '
                f'fill="{accent}" opacity="{opacity * 0.2}"/>'
            )
            elements += (
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="1.2" '
                f'fill="{accent}" opacity="{opacity * 3.0}"/>'
            )

    elif section_type == 6:
        # ── Recursive L-system branching tree — process narrows to insight ──
        # Dense L-system with depth 5, multiple sub-branches, color fading
        elems = []  # mutable list for nested function

        def _tree(x, y, angle, depth, length, sw):
            if depth <= 0 or length < 2:
                return
            ex = x + length * math.cos(angle)
            ey = y + length * math.sin(angle)
            t = 1.0 - depth / 5.0
            op_mult = 0.5 + t * 0.8
            stroke_w = sw * (1.0 - t * 0.5)
            elems.append(
                f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{ex:.1f}" y2="{ey:.1f}" '
                f'stroke="{c}" stroke-width="{stroke_w:.2f}" '
                f'opacity="{opacity * op_mult:.3f}" stroke-linecap="round"/>'
            )
            if depth <= 2:
                elems.append(
                    f'<circle cx="{ex:.1f}" cy="{ey:.1f}" r="{2 + t * 3:.1f}" '
                    f'fill="{accent}" opacity="{opacity * 0.2:.3f}"/>'
                )
            spread = 0.4 + t * 0.2
            n_branches = 2 if depth > 2 else 3
            for i in range(n_branches):
                off = (i - (n_branches - 1) / 2) * spread / max(n_branches - 1, 1)
                _tree(ex, ey, angle + off, depth - 1, length * 0.68, stroke_w)

        _tree(mid, s * 0.92, -math.pi / 2, 5, s * 0.18, 1.0)
        elements += "".join(elems)

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{s}" height="{s}" '
        f'viewBox="0 0 {s} {s}">{elements}</svg>'
    )


def section_type_color(section_type: int, pillar: str) -> str:
    """Return hex color for a section-type left border.

    Args:
        section_type: Index 0-6.
        pillar: Domain key.
    """
    key = _brand_key(pillar)
    palette = BRAND.get(key, BRAND["aml"])
    colors = {
        0: palette["primary"],       # Overview — pillar primary
        1: palette["accent"],        # Key Findings — bright accent
        2: palette["primary"],       # Applied Scenario — pillar primary
        3: palette["primary"],       # Source Analysis — pillar primary
        4: palette["secondary"],     # Domain Breakdown — secondary
        5: palette["accent"],        # Cross-Pillar — bright accent
        6: palette["secondary"],     # Methodology — pillar secondary
    }
    return colors.get(section_type, palette["primary"])
