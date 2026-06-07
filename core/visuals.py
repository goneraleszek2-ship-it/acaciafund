"""Content-aware SVG visual generation for AcaciaFund blog posts.

Generates dynamic, topic-derived visuals for blog cards, OG images,
and in-post data bars — replacing static category-only thumbnails.
"""

import hashlib
import math
import re
import random
from datetime import datetime
from pathlib import Path
from typing import Optional

STATIC_DIR = Path(__file__).parent.parent / "static" / "images"
STATIC_DIR.mkdir(parents=True, exist_ok=True)

PILLAR_PALETTES = {
    "aml":     {"primary": "#1e3a5f", "secondary": "#2d5a8e", "accent": "#d97706", "bg": "#0f172a"},
    "stock":   {"primary": "#166534", "secondary": "#15803d", "accent": "#22c55e", "bg": "#052e16"},
    "science": {"primary": "#7e22ce", "secondary": "#a855f7", "accent": "#c084fc", "bg": "#3b0764"},
}

TOPIC_ICONS = {
    # AML
    "regulation":     '<path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>',
    "compliance":     '<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M9 12l2 2 4-4"/>',
    "crypto":         '<circle cx="12" cy="12" r="10"/><path d="M12 6v12M9 9h6l-3 6-3-6z"/>',
    "fraud":          '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><circle cx="12" cy="12" r="3"/>',
    "banking":        '<rect x="2" y="8" width="20" height="14" rx="2"/><path d="M12 2L2 8h20L12 2z"/><path d="M8 14v4M12 14v4M16 14v4"/>',
    # Markets
    "semiconductor":  '<path d="M6 6h12v12H6z"/><path d="M8 8h8v8H8z"/><path d="M10 10h4v4h-4z"/>',
    "ai":             '<circle cx="12" cy="12" r="10"/><path d="M12 8v8M8 12h8"/><circle cx="12" cy="12" r="3"/>',
    "stock_market":   '<path d="M2 20h20M6 16l4-4 4 4 4-8" fill="none" stroke-width="2"/>',
    "startup":        '<path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M12 22V12"/>',
    "manufacturing":  '<path d="M4 4h16v16H4z"/><circle cx="12" cy="12" r="4"/><path d="M12 8v8M8 12h8"/>',
    # Science
    "dna":            '<path d="M8 2c0 0 0 20 8 20M16 2c0 0 0 20-8 20M8 12h8" fill="none" stroke-width="1.5"/>',
    "quantum":        '<circle cx="12" cy="12" r="3" fill="none" stroke-width="2"/><circle cx="16" cy="8" r="1.5"/><circle cx="16" cy="16" r="1.5"/><circle cx="8" cy="8" r="1.5"/><circle cx="8" cy="16" r="1.5"/><path d="M12 3v2M12 19v2M3 12h2M19 12h2"/>',
    "brain":          '<path d="M12 2C8 2 4 5 4 10c0 3 2 5 2 5s0 5 6 5 6-5 6-5 2-2 2-5c0-5-4-8-8-8z" fill="none" stroke-width="2"/><path d="M9 10h6M10.5 12h3M10 8h4"/>',
    "space":          '<circle cx="12" cy="12" r="10" fill="none" stroke-width="2"/><path d="M2 12h20M12 2a16 16 0 010 20 16 16 0 010-20z"/><ellipse cx="12" cy="12" rx="4" ry="10"/>',
    "climate":        '<circle cx="12" cy="12" r="10" fill="none" stroke-width="2"/><path d="M12 2a8 8 0 000 16"/><path d="M8 6l2 2M16 6l-2 2"/>',
}

SUBTOPIC_CATEGORIES: dict[str, dict[str, set[str]]] = {
    "aml": {
        "regulation": {"regulation", "regulatory", "regulate", "compliance", "law", "legal",
                       "proposal", "guidance", "directive", "policy", "rulling"},
        "crypto": {"crypto", "cryptocurrency", "bitcoin", "ethereum", "blockchain",
                   "digital asset", "token", "defi", "exchange"},
        "fraud": {"fraud", "scam", "money laundering", "sanctions", "illicit",
                  "suspicious", "ransomware", "phishing", "cybercrime"},
        "banking": {"bank", "banking", "fintech", "payment", "lending",
                    "financial", "credit", "capital", "institution"},
    },
    "stock": {
        "semiconductor": {"semiconductor", "chip", "foundry", "fab", "nvidia", "tsmc",
                          "asml", "intel", "amd", "processor", "gpu"},
        "ai": {"ai", "artificial intelligence", "machine learning", "deep learning",
               "neural", "llm", "openai", "anthropic", "google"},
        "stock_market": {"stock", "market", "nasdaq", "s&p", "valuation", "earnings",
                         "ipo", "trading", "investment"},
        "manufacturing": {"supply chain", "manufacturing", "production", "factory",
                          "industry", "industrial", "logistics"},
    },
    "science": {
        "dna": {"dna", "gene", "genetic", "crispr", "biology", "cell", "protein",
                "mitochondria", "genome"},
        "quantum": {"quantum", "qubit", "superposition", "entanglement"},
        "brain": {"brain", "neuron", "neuroscience", "cognitive", "consciousness",
                  "mind", "mental"},
        "space": {"space", "nasa", "esa", "rocket", "satellite", "cosmos",
                  "astronomy", "planet", "star"},
        "climate": {"climate", "energy", "solar", "renewable", "carbon",
                    "emission", "temperature", "environment"},
        "complexity": {"complexity", "emergence", "network", "system", "cybernetics",
                       "self-organization", "antifragile"},
    },
}

PILLAR_COLORS = {
    "aml":     {"bg": "#0f172a", "fg": "#1e3a5f",  "text": "#f8fafc", "accent": "#d97706"},
    "stock":   {"bg": "#052e16", "fg": "#166534",  "text": "#f0fdf4", "accent": "#22c55e"},
    "science": {"bg": "#3b0764", "fg": "#7e22ce",  "text": "#faf5ff", "accent": "#c084fc"},
}


def _content_hash(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()


def _pick_subtopic(titles: list[str], pillar: str) -> str:
    """Pick the most relevant subtopic/icon based on article titles."""
    text = " ".join(titles).lower()
    subs = SUBTOPIC_CATEGORIES.get(pillar, {})
    best_sub = list(subs.keys())[0] if subs else "regulation"
    best_score = 0
    for sub, keywords in subs.items():
        score = sum(2 if kw in text else 0 for kw in keywords)
        if score > best_score:
            best_score = score
            best_sub = sub
    return best_sub


def _extract_topic_words(titles: list[str], n: int = 5) -> list[str]:
    """Extract the most meaningful topic words from titles."""
    text = " ".join(titles)
    words = re.findall(r"[A-Z][a-z]{3,}", text)
    stop = {"This", "That", "With", "From", "What", "How", "Why", "When",
            "After", "Before", "Into", "Over", "Also", "Just", "More",
            "Very", "New", "First", "Last", "Next", "They", "Them", "Their"}
    words = [w for w in words if w not in stop]
    from collections import Counter
    counts = Counter(words)
    return [w for w, _ in counts.most_common(n)]


# ────────────── Fractal Engine ──────────────

def _hex_to_rgb(h: str) -> tuple:
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _rgb_to_hex(r: int, g: int, b: int) -> str:
    return f"#{max(0, min(255, r)):02x}{max(0, min(255, g)):02x}{max(0, min(255, b)):02x}"


def _lerp_color(c1: str, c2: str, t: float) -> str:
    r1, g1, b1 = _hex_to_rgb(c1)
    r2, g2, b2 = _hex_to_rgb(c2)
    t = max(0.0, min(1.0, t))
    return _rgb_to_hex(
        int(r1 + (r2 - r1) * t),
        int(g1 + (g2 - g1) * t),
        int(b1 + (b2 - b1) * t),
    )


def _hsv_to_hex(h: float, s: float, v: float) -> str:
    h = h % 360
    c = v * s
    x = c * (1 - abs((h / 60) % 2 - 1))
    m = v - c
    if h < 60:
        r, g, b = c, x, 0
    elif h < 120:
        r, g, b = x, c, 0
    elif h < 180:
        r, g, b = 0, c, x
    elif h < 240:
        r, g, b = 0, x, c
    elif h < 300:
        r, g, b = x, 0, c
    else:
        r, g, b = c, 0, x
    return _rgb_to_hex(int((r + m) * 255), int((g + m) * 255), int((b + m) * 255))


def _det_rand(seed: int, i: int = 0) -> float:
    """Deterministic pseudo-random from seed + index."""
    h = hashlib.md5(f"{seed}:{i}".encode()).hexdigest()
    return int(h[:8], 16) / 0xffffffff


def _det_rand_range(seed: int, i: int, lo: float, hi: float) -> float:
    return lo + _det_rand(seed, i) * (hi - lo)


def _det_rand_int(seed: int, i: int, lo: int, hi: int) -> int:
    return int(_det_rand(seed, i) * (hi - lo + 1)) + lo


# ───── Fractal Type: L-System Tree ─────

def _fractal_tree(elems: list, seed: int, pal: dict, w: int, h: int,
                  cx: float, cy: float, trunk: float, depth: int,
                  mirror_x: bool, mirror_y: bool, seq: list):
    """Recursive L-system branching tree with rounded caps and color transitions."""
    angle = -90 + _det_rand_range(seed, seq[0], -15, 15)
    seq[0] += 1
    spread = 20 + _det_rand_range(seed, seq[0], 10, 40)
    seq[0] += 1
    ratio = 0.62 + _det_rand_range(seed, seq[0], 0, 0.18)
    seq[0] += 1
    lean = _det_rand_range(seed, seq[0], -10, 10)
    seq[0] += 1

    def _branch(x, y, a, length, d):
        if d <= 0 or length < 3:
            return
        rad = math.radians(a)
        ex = x + length * math.cos(rad)
        ey = y + length * math.sin(rad)
        t = 1.0 - d / depth
        sw = max(0.5, 3.0 * t)
        op = 0.15 + 0.5 * t
        color = _lerp_color(pal["fg"], pal["accent"], t * 0.7)
        elems.append(
            f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{ex:.1f}" y2="{ey:.1f}" '
            f'stroke="{color}" stroke-width="{sw:.1f}" opacity="{op:.2f}" '
            f'stroke-linecap="round"/>'
        )
        if d <= 2 and t > 0.3:
            glow_r = 2 + t * 8
            elems.append(
                f'<circle cx="{ex:.1f}" cy="{ey:.1f}" r="{glow_r:.0f}" '
                f'fill="{pal["accent"]}" opacity="{op * 0.15:.2f}"/>'
            )
        n = 2 + _det_rand_int(seed, d * 10 + int(x + y), 2, 3)
        for i in range(n):
            off = (i - (n - 1) / 2) * spread / (n - 1) if n > 1 else 0
            child_a = a + off + lean * (1 - t)
            child_l = length * (ratio + _det_rand_range(seed, d * 100 + i * 10, -0.05, 0.05))
            _branch(ex, ey, child_a, child_l, d - 1)

    _branch(cx, cy, angle, trunk, depth)


# ───── Fractal Type: Sierpinski Triangle ─────

def _fractal_sierpinski(elems: list, seed: int, pal: dict, w: int, h: int,
                        x1: float, y1: float, x2: float, y2: float,
                        x3: float, y3: float, depth: int, seq: list):
    """Recursive Sierpinski triangle with color fills and rounded lines."""
    if depth <= 0:
        t = _det_rand(seed, seq[0])
        seq[0] += 1
        c = _lerp_color(pal["fg"], pal["accent"], t)
        op = 0.08 + t * 0.15
        elems.append(
            f'<polygon points="{x1:.1f},{y1:.1f} {x2:.1f},{y2:.1f} {x3:.1f},{y3:.1f}" '
            f'fill="{c}" opacity="{op:.2f}" stroke="{pal["accent"]}" '
            f'stroke-width="0.5" stroke-linecap="round" stroke-linejoin="round"/>'
        )
        return
    mx1 = (x1 + x2) / 2
    my1 = (y1 + y2) / 2
    mx2 = (x2 + x3) / 2
    my2 = (y2 + y3) / 2
    mx3 = (x3 + x1) / 2
    my3 = (y3 + y1) / 2
    _fractal_sierpinski(elems, seed, pal, w, h, x1, y1, mx1, my1, mx3, my3, depth - 1, seq)
    _fractal_sierpinski(elems, seed, pal, w, h, mx1, my1, x2, y2, mx2, my2, depth - 1, seq)
    _fractal_sierpinski(elems, seed, pal, w, h, mx3, my3, mx2, my2, x3, y3, depth - 1, seq)


# ───── Fractal Type: Koch Snowflake ─────

def _fractal_koch(elems: list, seed: int, pal: dict, w: int, h: int,
                  x1: float, y1: float, x2: float, y2: float,
                  depth: int, seq: list, hue_offset: float = 0):
    """Recursive Koch curve with dynamic hue-shifted coloring."""
    if depth <= 0:
        t = _det_rand(seed, seq[0])
        seq[0] += 1
        c = _lerp_color(pal["fg"], pal["accent"], t * 0.8)
        sw = 0.8 + t * 1.5
        op = 0.2 + t * 0.4
        elems.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="{c}" stroke-width="{sw:.1f}" opacity="{op:.2f}" '
            f'stroke-linecap="round"/>'
        )
        return
    dx = (x2 - x1) / 3
    dy = (y2 - y1) / 3
    p1x = x1 + dx
    p1y = y1 + dy
    p2x = x1 + dx * 2
    p2y = y1 + dy * 2
    angle = math.radians(60)
    p3x = p1x + (dx * math.cos(angle) - dy * math.sin(angle))
    p3y = p1y + (dx * math.sin(angle) + dy * math.cos(angle))
    _fractal_koch(elems, seed, pal, w, h, x1, y1, p1x, p1y, depth - 1, seq, hue_offset)
    _fractal_koch(elems, seed, pal, w, h, p1x, p1y, p3x, p3y, depth - 1, seq, hue_offset + 20)
    _fractal_koch(elems, seed, pal, w, h, p3x, p3y, p2x, p2y, depth - 1, seq, hue_offset - 20)
    _fractal_koch(elems, seed, pal, w, h, p2x, p2y, x2, y2, depth - 1, seq, hue_offset)


# ───── Fractal Type: Dragon Curve ─────

def _fractal_dragon(elems: list, seed: int, pal: dict, w: int, h: int,
                    x1: float, y1: float, x2: float, y2: float,
                    depth: int, seq: list, sign: float = 1):
    """Recursive dragon curve with rounded segments and color shift."""
    if depth <= 0:
        t = _det_rand(seed, seq[0])
        seq[0] += 1
        c = _lerp_color(pal["fg"], pal["accent"], t)
        sw = 0.5 + t * 2.0
        op = 0.1 + t * 0.4
        elems.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="{c}" stroke-width="{sw:.1f}" opacity="{op:.2f}" '
            f'stroke-linecap="round"/>'
        )
        return
    mx = (x1 + x2) / 2 + (y2 - y1) / 2 * sign
    my = (y1 + y2) / 2 - (x2 - x1) / 2 * sign
    _fractal_dragon(elems, seed, pal, w, h, x1, y1, mx, my, depth - 1, seq, 1)
    _fractal_dragon(elems, seed, pal, w, h, x2, y2, mx, my, depth - 1, seq, -1)


# ───── Fractal Type: Barnsley Fern (IFS) ─────

def _fractal_fern(elems: list, seed: int, pal: dict, w: int, h: int,
                  seq: list, count: int = 300):
    """Barnsley fern IFS rendered as rounded dots with color gradient."""
    x, y = 0.0, 0.0
    for i in range(count):
        r = _det_rand(seed, seq[0] + i)
        seq[0] += 1
        if r < 0.01:
            nx, ny = 0.0, 0.16 * y
        elif r < 0.86:
            nx, ny = 0.85 * x + 0.04 * y, -0.04 * x + 0.85 * y + 1.6
        elif r < 0.93:
            nx, ny = 0.2 * x - 0.26 * y, 0.23 * x + 0.22 * y + 1.6
        else:
            nx, ny = -0.15 * x + 0.28 * y, 0.26 * x + 0.24 * y + 0.44
        x, y = nx, ny
        px = w / 2 + x * (w / 12)
        py = h * 0.92 - y * (h / 12)
        t = i / count
        c = _lerp_color(pal["accent"], pal["fg"], t)
        op = 0.15 + t * 0.3
        r_size = 0.8 + t * 1.5
        elems.append(
            f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{r_size:.1f}" '
            f'fill="{c}" opacity="{op:.2f}"/>'
        )


# ───── Fractal Type: Spiraling Circles ─────

def _fractal_spiral(elems: list, seed: int, pal: dict, w: int, h: int,
                    cx: float, cy: float, seq: list, turns: int = 8):
    """Golden-ratio spiral of nested circles with color transitions."""
    angle_step = 137.5  # golden angle
    shrink = 0.92 + _det_rand_range(seed, seq[0], 0, 0.06)
    seq[0] += 1
    r = min(w, h) * 0.08
    for i in range(turns * 8):
        angle = math.radians(i * angle_step)
        nx = cx + i * 2.5 * math.cos(angle)
        ny = cy + i * 2.5 * math.sin(angle)
        if nx < 0 or nx > w or ny < 0 or ny > h:
            continue
        radius = max(1.0, r * (shrink ** i))
        t = i / (turns * 8)
        c = _lerp_color(pal["accent"], pal["fg"], t)
        op = 0.05 + t * 0.2
        elems.append(
            f'<circle cx="{nx:.1f}" cy="{ny:.1f}" r="{radius:.1f}" '
            f'fill="none" stroke="{c}" stroke-width="0.8" opacity="{op:.2f}"/>'
        )
        if i % 3 == 0:
            inner_r = radius * 0.4
            inner_c = _lerp_color(pal["fg"], pal["accent"], 1 - t)
            elems.append(
                f'<circle cx="{nx:.1f}" cy="{ny:.1f}" r="{inner_r:.1f}" '
                f'fill="{inner_c}" opacity="{op * 0.5:.2f}"/>'
            )


# ───── Fractal Type: Hilbert Curve ─────

def _fractal_hilbert(elems: list, seed: int, pal: dict, w: int, h: int,
                     x: float, y: float, xi: float, xj: float,
                     yi: float, yj: float, depth: int, seq: list):
    """Recursive Hilbert space-filling curve with color gradient."""
    if depth <= 0:
        t = _det_rand(seed, seq[0])
        seq[0] += 1
        nx = x + (xi + yi) / 2
        ny = y + (xj + yj) / 2
        c = _lerp_color(pal["fg"], pal["accent"], t)
        sw = 0.5 + t * 2.0
        op = 0.15 + t * 0.35
        elems.append(
            f'<circle cx="{nx:.1f}" cy="{ny:.1f}" r="{sw:.1f}" '
            f'fill="{c}" opacity="{op:.2f}"/>'
        )
        return
    _fractal_hilbert(elems, seed, pal, w, h, x, y, yi / 2, yj / 2, xi / 2, xj / 2, depth - 1, seq)
    _fractal_hilbert(elems, seed, pal, w, h, x + xi / 2, y + xj / 2, xi / 2, xj / 2, yi / 2, yj / 2, depth - 1, seq)
    _fractal_hilbert(elems, seed, pal, w, h, x + xi / 2 + yi / 2, y + xj / 2 + yj / 2, xi / 2, xj / 2, yi / 2, yj / 2, depth - 1, seq)
    _fractal_hilbert(elems, seed, pal, w, h, x + xi / 2 + yi, y + xj / 2 + yj, -yi / 2, -yj / 2, -xi / 2, -xj / 2, depth - 1, seq)


# ───── Mirror helper ─────

def _mirror_elements(elems: list, mirror_x: bool, mirror_y: bool,
                     w: int, h: int) -> list:
    """Duplicate elements with mirror transformations."""
    if not mirror_x and not mirror_y:
        return elems
    out = list(elems)
    for el in elems:
        m = el
        if mirror_x:
            m = m.replace(f'x1="', f'x1="{-1 if "x1" in m else ""}')
            # Simple approach: wrap in <use> with transform
        if mirror_y:
            m = m.replace(f'y1="', f'y1="')
    return out


def _generate_mist(seed: int, pal: dict, w: int, h: int, count: int,
                   seq: list) -> list:
    """Generate atmospheric mist particles."""
    elems = []
    for i in range(count):
        x = _det_rand_range(seed, seq[0] + i, 0, w)
        y = _det_rand_range(seed, seq[0] + i + 100, 0, h)
        r = _det_rand_range(seed, seq[0] + i + 200, 1, 6)
        op = _det_rand_range(seed, seq[0] + i + 300, 0.01, 0.08)
        c = _lerp_color(pal["accent"], pal["text"], _det_rand(seed, seq[0] + i + 400))
        elems.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" '
            f'fill="{c}" opacity="{op:.2f}"/>'
        )
    seq[0] += count + 500
    return elems


def generate_thumbnail_svg(title: str, pillar: str, scores: dict,
                           width: int = 600, height: int = 340) -> str:
    """Generate a unique fractal-based SVG thumbnail for a blog post.

    Uses 7 fractal types, mirroring, dynamic color transitions, and
    atmospheric effects — each image is uniquely derived from the title hash.
    """
    pal = PILLAR_COLORS.get(pillar, PILLAR_COLORS["aml"])
    sub = _pick_subtopic([title], pillar)
    icon_path = TOPIC_ICONS.get(sub, TOPIC_ICONS["regulation"])
    words = _extract_topic_words([title], 3)
    h = _content_hash(title)
    seed = int(h[:12], 16)
    seq = [0]

    # Fractal type (0-6)
    ftype = _det_rand_int(seed, seq[0], 0, 6)
    seq[0] += 1

    # Mirror modes: 0=none, 1=h, 2=v, 3=both
    mirror_mode = _det_rand_int(seed, seq[0], 0, 3)
    seq[0] += 1
    mirror_x = mirror_mode in (1, 3)
    mirror_y = mirror_mode in (2, 3)

    # Background gradient variant
    bg_v = _det_rand_int(seed, seq[0], 0, 3)
    seq[0] += 1
    color_tint = _lerp_color(pal["bg"], pal["accent"], 0.08 + _det_rand(seed, seq[0]) * 0.1)
    seq[0] += 1

    if bg_v == 0:
        bg = (f'<linearGradient id="bg-{h[:8]}" x1="0" y1="0" x2="1" y2="1">'
              f'<stop offset="0" stop-color="{pal["bg"]}"/>'
              f'<stop offset="0.5" stop-color="{color_tint}"/>'
              f'<stop offset="1" stop-color="{pal["fg"]}"/>'
              f'</linearGradient>')
    elif bg_v == 1:
        bg = (f'<radialGradient id="bg-{h[:8]}" cx="{30 + _det_rand_int(seed, seq[0], 0, 40)}%" '
              f'cy="{30 + _det_rand_int(seed, seq[0] + 1, 0, 40)}%">'
              f'<stop offset="0" stop-color="{color_tint}"/>'
              f'<stop offset="1" stop-color="{pal["bg"]}"/>'
              f'</radialGradient>')
        seq[0] += 2
    else:
        c2 = _lerp_color(pal["bg"], pal["accent"], 0.18)
        bg = (f'<linearGradient id="bg-{h[:8]}" x1="0" y1="1" x2="1" y2="0">'
              f'<stop offset="0" stop-color="{pal["bg"]}"/>'
              f'<stop offset="0.4" stop-color="{color_tint}"/>'
              f'<stop offset="0.7" stop-color="{c2}"/>'
              f'<stop offset="1" stop-color="{pal["fg"]}"/>'
              f'</linearGradient>')

    # Radial accent glow
    glow_cx = _det_rand_int(seed, seq[0], 20, 80)
    glow_cy = _det_rand_int(seed, seq[0] + 1, 20, 80)
    seq[0] += 2
    glow_op = 0.08 + _det_rand(seed, seq[0]) * 0.12
    seq[0] += 1

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"'
        f' viewBox="0 0 {width} {height}">',
        '<defs>',
        bg,
        (f'<radialGradient id="glow-{h[:8]}" cx="{glow_cx}%" cy="{glow_cy}%">'
         f'<stop offset="0" stop-color="{pal["accent"]}" stop-opacity="{glow_op:.2f}"/>'
         f'<stop offset="1" stop-color="{pal["bg"]}" stop-opacity="0"/>'
         f'</radialGradient>'),
        '</defs>',
        f'<rect width="{width}" height="{height}" fill="url(#bg-{h[:8]})"/>',
        f'<rect width="{width}" height="{height}" fill="url(#glow-{h[:8]})"/>',
    ]

    # Mist layer 1 (background)
    mist1 = _generate_mist(seed, pal, width, height,
                           15 + _det_rand_int(seed, seq[0], 0, 10), seq)
    seq[0] += 1
    lines.extend(mist1)

    # Fractal elements
    fractal_elems = []
    cx, cy = width // 2, height // 2

    if ftype == 0:
        # L-System Tree — grows from bottom-center with optional mirror branches
        tree_x = width / 2 + (_det_rand_range(seed, seq[0], -40, 40))
        tree_y = height * 0.92
        trunk = 60 + _det_rand_range(seed, seq[0] + 1, 30, 80)
        depth = _det_rand_int(seed, seq[0] + 2, 4, 6)
        seq[0] += 3
        _fractal_tree(fractal_elems, seed, pal, width, height,
                       tree_x, tree_y, trunk, depth, mirror_x, mirror_y, seq)
        if mirror_x:
            _fractal_tree(fractal_elems, seed + 999, pal, width, height,
                           width - tree_x, tree_y, trunk, depth, False, False, seq)

    elif ftype == 1:
        # Sierpinski Triangle
        size = min(width, height) * 0.7
        depth = _det_rand_int(seed, seq[0], 3, 5)
        seq[0] += 1
        ox = (width - size) / 2
        oy = (height - size) / 2
        _fractal_sierpinski(fractal_elems, seed, pal, width, height,
                            ox + size / 2, oy,
                            ox, oy + size,
                            ox + size, oy + size,
                            depth, seq)
        if mirror_x:
            _fractal_sierpinski(fractal_elems, seed + 999, pal, width, height,
                                width - (ox + size / 2), oy,
                                width - ox, oy + size,
                                width - (ox + size), oy + size,
                                depth, seq)

    elif ftype == 2:
        # Koch Snowflake (3 sides)
        size = min(width, height) * 0.55
        depth = _det_rand_int(seed, seq[0], 2, 4)
        seq[0] += 1
        cx_k = width / 2
        cy_k = height / 2 - size * 0.2
        r_k = size
        for i in range(3):
            a1 = math.radians(60 + i * 120)
            a2 = math.radians(60 + (i + 1) * 120)
            x1 = cx_k + r_k * math.cos(a1)
            y1 = cy_k + r_k * math.sin(a1)
            x2 = cx_k + r_k * math.cos(a2)
            y2 = cy_k + r_k * math.sin(a2)
            _fractal_koch(fractal_elems, seed + i, pal, width, height,
                          x1, y1, x2, y2, depth, seq, i * 30)
        if mirror_x:
            seq[0] += 10
            _fractal_koch(fractal_elems, seed + 999, pal, width, height,
                          width - x1, y1, width - x2, y2, depth, seq, 0)

    elif ftype == 3:
        # Dragon Curve
        depth = _det_rand_int(seed, seq[0], 6, 9)
        seq[0] += 1
        start_x = width * _det_rand_range(seed, seq[0], 0.1, 0.4)
        start_y = height * _det_rand_range(seed, seq[0] + 1, 0.2, 0.8)
        end_x = width * _det_rand_range(seed, seq[0] + 2, 0.6, 0.9)
        end_y = height * _det_rand_range(seed, seq[0] + 3, 0.2, 0.8)
        seq[0] += 4
        _fractal_dragon(fractal_elems, seed, pal, width, height,
                        start_x, start_y, end_x, end_y, depth, seq)
        if mirror_x:
            _fractal_dragon(fractal_elems, seed + 999, pal, width, height,
                            width - start_x, start_y, width - end_x, end_y,
                            depth, seq)

    elif ftype == 4:
        # Barnsley Fern
        count = 200 + _det_rand_int(seed, seq[0], 0, 200)
        seq[0] += 1
        _fractal_fern(fractal_elems, seed, pal, width, height, seq, count)
        if mirror_x:
            _fractal_fern(fractal_elems, seed + 999, pal, width, height, seq, count)

    elif ftype == 5:
        # Spiraling Circles
        turns = _det_rand_int(seed, seq[0], 5, 10)
        seq[0] += 1
        _fractal_spiral(fractal_elems, seed, pal, width, height,
                        width / 2, height / 2, seq, turns)

    else:
        # Hilbert Curve (as point cloud)
        depth = _det_rand_int(seed, seq[0], 3, 5)
        seq[0] += 1
        size = min(width, height) * 0.5
        ox = (width - size) / 2
        oy = (height - size) / 2
        _fractal_hilbert(fractal_elems, seed, pal, width, height,
                         ox, oy, size, 0, 0, size, depth, seq)
        if mirror_x:
            _fractal_hilbert(fractal_elems, seed + 999, pal, width, height,
                             width - ox - size, oy, -size, 0, 0, size, depth, seq)

    lines.extend(fractal_elems)

    # Mist layer 2 (foreground, over fractal)
    mist2 = _generate_mist(seed + 1000, pal, width, height,
                           8 + _det_rand_int(seed, seq[0], 0, 8), seq)
    seq[0] += 1
    lines.extend(mist2)

    # Topic icon (bottom-left)
    icon_x = 14 + _det_rand_int(seed, seq[0], 0, 20)
    icon_y = height - 56 + _det_rand_int(seed, seq[0] + 1, 0, 10)
    icon_scale = 0.5 + _det_rand(seed, seq[0] + 2) * 0.3
    seq[0] += 3
    lines.extend([
        f'<g transform="translate({icon_x:.0f}, {icon_y:.0f}) scale({icon_scale:.2f})"'
        f' stroke="{pal["accent"]}" fill="none" stroke-linecap="round"'
        f' stroke-linejoin="round" stroke-width="1.5" opacity="0.35">',
        f'  {icon_path}',
        f'</g>',
    ])

    # Topic words as floating tags (bottom-right)
    for i, w in enumerate(words[:2]):
        tx = width - 80 + _det_rand_int(seed, seq[0] + i, -30, 30)
        ty = height - 30 + i * 18
        op = 0.15 + _det_rand(seed, seq[0] + i + 10) * 0.15
        lines.append(
            f'<text x="{tx:.0f}" y="{ty:.0f}" fill="{pal["accent"]}"'
            f' font-family="system-ui,sans-serif" font-size="11" font-weight="600"'
            f' opacity="{op:.2f}">{w}</text>'
        )
    seq[0] += 20

    # SQI indicator bar (subtle, bottom-center)
    sqi = scores.get("sqi", 0.5)
    bar_w = max(2, int(sqi * (width * 0.3)))
    bar_y = height - 10
    lines.append(
        f'<rect x="{width / 2 - width * 0.15:.0f}" y="{bar_y}"'
        f' width="{width * 0.3:.0f}" height="2" rx="1" fill="{pal["text"]}" opacity="0.06"/>'
    )
    lines.append(
        f'<rect x="{width / 2 - width * 0.15:.0f}" y="{bar_y}"'
        f' width="{bar_w}" height="2" rx="1" fill="{pal["accent"]}" opacity="0.4"/>'
    )

    # Pillar label (subtle, bottom-center near SQI)
    lines.append(
        f'<text x="{width / 2 + width * 0.15 + 6:.0f}" y="{bar_y + 10}"'
        f' fill="{pal["accent"]}" font-family="system-ui,sans-serif"'
        f' font-size="8" font-weight="600" opacity="0.25">{pillar.upper()}</text>'
    )

    lines.append('</svg>')
    return "\n".join(lines)


def generate_og_image(title: str, pillar: str, scores: dict,
                      date_str: str = "") -> str:
    """Generate a social sharing OG image SVG with the article title and fractal backing."""
    pal = PILLAR_COLORS.get(pillar, PILLAR_COLORS["aml"])
    sub = _pick_subtopic([title], pillar)
    icon_path = TOPIC_ICONS.get(sub, TOPIC_ICONS["regulation"])
    h = _content_hash(title)
    seed = int(h[:12], 16)
    seq = [0]

    # Wrap title text
    words_t = title.split()
    lines_text = []
    line = ""
    for w in words_t:
        if len(line + w) > 40:
            lines_text.append(line.strip())
            line = w + " "
        else:
            line += w + " "
    lines_text.append(line.strip())
    title_lines = lines_text[:4]

    # Dynamic background with fractal elements
    bg_v = _det_rand_int(seed, seq[0], 0, 2)
    seq[0] += 1
    c_tint = _lerp_color(pal["bg"], pal["accent"], 0.12)

    if bg_v == 0:
        bg = (f'<linearGradient id="ogbg" x1="0" y1="0" x2="1" y2="1">'
              f'<stop offset="0" stop-color="{pal["bg"]}"/>'
              f'<stop offset=".5" stop-color="{c_tint}"/>'
              f'<stop offset="1" stop-color="{pal["fg"]}"/>'
              f'</linearGradient>')
    else:
        bg = (f'<radialGradient id="ogbg" cx="{40 + _det_rand_int(seed, seq[0], 0, 30)}%"'
              f' cy="{40 + _det_rand_int(seed, seq[0] + 1, 0, 30)}%">'
              f'<stop offset="0" stop-color="{c_tint}"/>'
              f'<stop offset="1" stop-color="{pal["bg"]}"/>'
              f'</radialGradient>')
        seq[0] += 2

    # Decorative fractal circles
    circles = []
    for i in range(6):
        r_x = 80 + _det_rand_int(seed, seq[0] + i * 3, 0, 200)
        r_y = 80 + _det_rand_int(seed, seq[0] + i * 3 + 1, 0, 150)
        cx_c = _det_rand_int(seed, seq[0] + i * 3 + 2, 100, 1100)
        cy_c = _det_rand_int(seed, seq[0] + i * 3 + 3, 50, 550)
        op_c = 0.015 + _det_rand(seed, seq[0] + i * 3 + 4) * 0.03
        circles.append(
            f'<ellipse cx="{cx_c}" cy="{cy_c}" rx="{r_x}" ry="{r_y}"'
            f' fill="{pal["accent"]}" opacity="{op_c:.2f}"/>'
        )
    seq[0] += 20

    # Subtle fractal mist overlay
    mist = _generate_mist(seed, pal, 1200, 630, 20, seq)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630">',
        '<defs>', bg, '</defs>',
        f'<rect width="1200" height="630" fill="url(#ogbg)"/>',
    ] + circles + mist + [
        f'<!-- Icon -->',
        f'<g transform="translate(50, 50) scale(1.8)" stroke="{pal["accent"]}"'
        f' fill="none" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5">',
        f'  {icon_path}',
        f'</g>',
    ]

    # Title lines
    y = 260
    for tl in title_lines:
        parts.append(
            f'<text x="50" y="{y}" fill="{pal["text"]}" font-family="system-ui,sans-serif"'
            f' font-size="{44 if len(tl) < 35 else 36}" font-weight="700">'
            f'{tl.replace("&", "&amp;").replace("<", "&lt;")}</text>'
        )
        y += 52

    # Meta info with accent glow bar
    sqi = scores.get("sqi", 0.5)
    parts.extend([
        f'<text x="50" y="500" fill="{pal["accent"]}" font-family="system-ui,sans-serif"'
        f' font-size="18" font-weight="600">AcaciaFund &nbsp;·&nbsp; {pillar.upper()}'
        f'{" &nbsp;·&nbsp; " + date_str if date_str else ""}</text>',
        f'<text x="50" y="540" fill="{pal["text"]}" font-family="system-ui,sans-serif"'
        f' font-size="14" opacity="0.5">Codzienna synteza badan — AML, rynki, nauka</text>',
        f'<rect x="50" y="570" width="{int(min(1.0, sqi) * 200)}" height="4" rx="2"'
        f' fill="{pal["accent"]}" opacity="0.8"/>',
        '</svg>',
    ])

    return "\n".join(parts)


def generate_topic_badge(name: str, pillar: str, count: int = 0) -> str:
    """Generate a small SVG badge for a topic/category."""
    pal = PILLAR_COLORS.get(pillar, PILLAR_COLORS["aml"])
    w = max(60, len(name) * 8 + 24)
    count_text = f" ({count})" if count else ""
    total_w = w + (len(count_text) * 8 if count_text else 0)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{total_w}" height="28" viewBox="0 0 {total_w} 28">'
        f'  <rect width="{total_w}" height="28" rx="14" fill="{pal["fg"]}"/>'
        f'  <text x="14" y="18" fill="{pal["text"]}" font-family="system-ui,sans-serif" font-size="12" '
        f'font-weight="600">{name}{count_text}</text>'
        f'</svg>'
    )


def generate_signal_meter(sqi: float, width: int = 200) -> str:
    """Generate an SVG signal quality meter bar."""
    bar_w = int(min(1.0, max(0, sqi)) * width)
    color = "#22c55e" if sqi >= 0.6 else "#d97706" if sqi >= 0.35 else "#ef4444"
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="16" viewBox="0 0 {width} 16">'
        f'  <rect width="{width}" height="6" y="5" rx="3" fill="var(--color-border, #e2e8f0)"/>'
        f'  <rect width="{bar_w}" height="6" y="5" rx="3" fill="{color}"/>'
        f'  <circle cx="{max(6, bar_w)}" cy="8" r="5" fill="{color}"/>'
        f'  <text x="{width + 8}" y="13" fill="var(--color-text-secondary, #475569)" font-family="system-ui,sans-serif" font-size="11">{sqi:.2f}</text>'
        f'</svg>'
    )


def generate_all_thumbnails(pillar_stories: dict[str, list[dict]],
                             pillar_signals: dict[str, dict]) -> dict[str, str]:
    """Generate thumbnails for all stories across all pillars."""
    results: dict[str, str] = {}
    for pillar, stories in pillar_stories.items():
        for story in stories:
            title = story.get("title", "")
            key = hashlib.md5(title.encode()).hexdigest()[:12]
            scores = {"sqi": 0.5}
            signals = pillar_signals.get(pillar, {})
            if signals:
                scores["sqi"] = signals.get("avg_sqi", 0.5)
            svg = generate_thumbnail_svg(title, pillar, scores)
            fname = f"thumb_{key}.svg"
            fpath = STATIC_DIR / fname
            fpath.write_text(svg, encoding="utf-8")
            results[title] = f"/images/{fname}"
    return results


def generate_post_thumbnail_block(title: str, pillar: str, scores: dict) -> str:
    """Generate a complete HTML block with inline SVG for embedding in post content."""
    svg = generate_thumbnail_svg(title, pillar, scores, width=800, height=400)
    return f'<div class="post-visual">{svg}</div>'


# ──────────────────────────────────────────────
# Phase 2: Zero-JS SVG Chart Engine
# ──────────────────────────────────────────────

SOURCE_COLORS = {"hn": "#f59e0b", "arxiv": "#3b82f6", "pubmed": "#22c55e"}
SOURCE_LABELS = {"hn": "HN", "arxiv": "arXiv", "pubmed": "PubMed"}
BLOOM_COLORS = {
    "remember": "#60a5fa", "understand": "#4ade80", "apply": "#fbbf24",
    "analyze": "#a78bfa", "evaluate": "#f87171", "create": "#818cf8",
}
BLOOM_LABELS = ["remember", "understand", "apply", "analyze", "evaluate", "create"]


def source_bar_svg(breakdown: dict, width: int = 280, height: int = 80) -> str:
    """Horizontal stacked bar showing HN / arXiv / PubMed source proportions."""
    total = sum(breakdown.get(k, 0) for k in ("hn", "arxiv", "pubmed")) or 1
    bar_x = 50
    bar_w = width - bar_x - 10
    bar_h = 20
    y = 10
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        f'<rect width="{width}" height="{height}" fill="none"/>',
    ]
    x = bar_x
    for key in ("hn", "arxiv", "pubmed"):
        val = breakdown.get(key, 0)
        if val <= 0:
            continue
        seg_w = max(2, int(val / total * bar_w))
        c = SOURCE_COLORS.get(key, "#94a3b8")
        label = SOURCE_LABELS.get(key, key)
        parts.append(f'<rect x="{x}" y="{y}" width="{seg_w}" height="{bar_h}" rx="3" fill="{c}" opacity="0.9"/>')
        parts.append(f'<text x="{x + 6}" y="{y + 14}" fill="#fff" font-family="system-ui,sans-serif" font-size="10" font-weight="600">{label} {val}</text>')
        x += seg_w
    # Scale ticks
    for pct in (0, 25, 50, 75, 100):
        tx = bar_x + int(pct / 100 * bar_w)
        parts.append(f'<line x1="{tx}" y1="{y + bar_h + 2}" x2="{tx}" y2="{y + bar_h + 6}" stroke="var(--color-text-muted, #94a3b8)" stroke-width="0.5"/>')
        parts.append(f'<text x="{tx}" y="{y + bar_h + 16}" text-anchor="middle" fill="var(--color-text-secondary, #475569)" font-family="system-ui,sans-serif" font-size="7">{pct}%</text>')
    parts.append('</svg>')
    return "\n".join(parts)


def sparkline_svg(values: list[float], color: str = "#22c55e",
                  width: int = 160, height: int = 40) -> str:
    """Mini sparkline chart for trends (e.g. SQI across articles)."""
    if not values:
        values = [0]
    n = len(values)
    pad = 4
    vw = width - pad * 2
    vh = height - pad * 2
    mn, mx = min(values), max(values)
    rng = mx - mn if mx != mn else 1
    pts = []
    for i, v in enumerate(values):
        px = pad + (i / max(n - 1, 1)) * vw
        py = pad + vh - ((v - mn) / rng) * vh
        pts.append(f"{px:.1f},{py:.1f}")
    polyline = " ".join(pts)
    # Area fill
    area_pts = f"{pad},{pad + vh} {polyline} {pad + vw},{pad + vh}"
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
        f'<rect width="{width}" height="{height}" fill="none"/>'
        f'<polygon points="{area_pts}" fill="{color}" opacity="0.1"/>'
        f'<polyline points="{polyline}" fill="none" stroke="{color}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>'
        f'<circle cx="{pts[-1].split(",")[0]}" cy="{pts[-1].split(",")[1]}" r="2.5" fill="{color}"/>'
        f'</svg>'
    )


def bloom_chart_svg(questions: list, width: int = 280, height: int = 180) -> str:
    """Horizontal bar chart showing question count per Bloom taxonomy level."""
    counts = {level: 0 for level in BLOOM_LABELS}
    for q in questions:
        level = (q.get("bloom_level") or "").lower()
        if level in counts:
            counts[level] += 1
    max_count = max(counts.values()) or 1
    bar_h = 18
    gap = 6
    chart_top = 10
    label_w = 80
    bar_max_w = width - label_w - 20
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        f'<rect width="{width}" height="{height}" fill="none"/>',
    ]
    for i, level in enumerate(BLOOM_LABELS):
        y = chart_top + i * (bar_h + gap)
        c = BLOOM_COLORS.get(level, "#94a3b8")
        cnt = counts[level]
        bar_w = max(2, int(cnt / max_count * bar_max_w))
        parts.append(f'<text x="{label_w - 4}" y="{y + bar_h - 4}" text-anchor="end" fill="var(--color-text-secondary, #475569)" font-family="system-ui,sans-serif" font-size="9" font-weight="500">{level}</text>')
        parts.append(f'<rect x="{label_w}" y="{y}" width="{bar_w}" height="{bar_h}" rx="3" fill="{c}" opacity="0.85"/>')
        if bar_w > 20:
            parts.append(f'<text x="{label_w + 6}" y="{y + bar_h - 4}" fill="#fff" font-family="system-ui,sans-serif" font-size="9" font-weight="600">{cnt}</text>')
        else:
            parts.append(f'<text x="{label_w + bar_w + 4}" y="{y + bar_h - 4}" fill="{c}" font-family="system-ui,sans-serif" font-size="9" font-weight="600">{cnt}</text>')
    parts.append('</svg>')
    return "\n".join(parts)


def radar_svg(metrics: dict, width: int = 180, height: int = 180) -> str:
    """3-axis radar (triangle) for quality metrics: source_score, diversity, recency."""
    cx, cy = width // 2, height // 2
    radius = min(cx, cy) - 20
    # Three axes at 0°, 120°, 240°
    angles = [0, 120, 240]
    keys = ["avg_source_score", "source_diversity", "recency_score"]
    labels = ["Source Score", "Diversity", "Recency"]
    vals = []
    for k in keys:
        v = metrics.get(k, 0)
        if isinstance(v, (int, float)):
            vals.append(max(0.0, min(1.0, v)))
        else:
            vals.append(0.0)

    def pol(x, y):
        return f"{cx + radius * math.cos(math.radians(a)):.1f},{cy + radius * math.sin(math.radians(a)):.1f}"

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        f'<rect width="{width}" height="{height}" fill="none"/>',
    ]
    # Background triangles
    for ring in (0.25, 0.5, 0.75, 1.0):
        pts = []
        for a in angles:
            r = radius * ring
            x = cx + r * math.cos(math.radians(a))
            y = cy + r * math.sin(math.radians(a))
            pts.append(f"{x:.1f},{y:.1f}")
        parts.append(f'<polygon points="{" ".join(pts)}" fill="none" stroke="#2d2d4a" stroke-width="0.5" opacity="0.3"/>')
    # Axis lines
    for a, lbl in zip(angles, labels):
        x2 = cx + radius * math.cos(math.radians(a))
        y2 = cy + radius * math.sin(math.radians(a))
        lx = cx + (radius + 14) * math.cos(math.radians(a))
        ly = cy + (radius + 14) * math.sin(math.radians(a))
        parts.append(f'<line x1="{cx}" y1="{cy}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#2d2d4a" stroke-width="0.5" opacity="0.4"/>')
        parts.append(f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="middle" dominant-baseline="middle" fill="var(--color-text-secondary, #475569)" font-family="system-ui,sans-serif" font-size="8">{lbl}</text>')
    # Data triangle
    pts = []
    for a, v in zip(angles, vals):
        r = radius * v
        x = cx + r * math.cos(math.radians(a))
        y = cy + r * math.sin(math.radians(a))
        pts.append(f"{x:.1f},{y:.1f}")
    parts.append(f'<polygon points="{" ".join(pts)}" fill="#a855f7" opacity="0.2" stroke="#a855f7" stroke-width="1.5" stroke-linejoin="round"/>')
    for p in pts:
        parts.append(f'<circle cx="{p.split(",")[0]}" cy="{p.split(",")[1]}" r="3" fill="#a855f7"/>')
    # Center value labels
    for a, v in zip(angles, vals):
        r2 = radius * v * 0.6
        if r2 < 20:
            r2 = radius * v + 16
        lx = cx + r2 * math.cos(math.radians(a))
        ly = cy + r2 * math.sin(math.radians(a))
        parts.append(f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="middle" dominant-baseline="middle" fill="#c084fc" font-family="system-ui,sans-serif" font-size="8" font-weight="600">{v:.2f}</text>')
    parts.append('</svg>')
    return "\n".join(parts)


def heatmap_svg(data: list[list[float]], row_labels: list[str] | None = None,
                col_labels: list[str] | None = None,
                cell_size: int = 28, gap: int = 2) -> str:
    """Simple grid heatmap. Values in [0,1] determine color intensity."""
    if not data or not data[0]:
        return '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20"></svg>'
    rows = len(data)
    cols = len(data[0])
    label_w = 60 if row_labels else 0
    header_h = 16 if col_labels else 0
    w = label_w + cols * (cell_size + gap) + 4
    h = header_h + rows * (cell_size + gap) + 4
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">',
        f'<rect width="{w}" height="{h}" fill="none"/>',
    ]
    for i, row in enumerate(data):
        for j, val in enumerate(row):
            x = label_w + j * (cell_size + gap)
            y = header_h + i * (cell_size + gap)
            clamped = max(0.0, min(1.0, val))
            r = int(15 + clamped * 200)
            g = int(15 + (1 - clamped) * 200)
            fill = f"rgb({r},{g},{240 - int(clamped * 100)})"
            parts.append(f'<rect x="{x}" y="{y}" width="{cell_size}" height="{cell_size}" rx="3" fill="{fill}" opacity="0.85"/>')
            parts.append(f'<text x="{x + cell_size // 2}" y="{y + cell_size // 2 + 1}" text-anchor="middle" dominant-baseline="middle" fill="#fff" font-family="system-ui,sans-serif" font-size="8" font-weight="600">{val:.1f}</text>')
    if row_labels:
        for i, lbl in enumerate(row_labels):
            y = header_h + i * (cell_size + gap) + cell_size // 2 + 1
            parts.append(f'<text x="{label_w - 4}" y="{y}" text-anchor="end" dominant-baseline="middle" fill="var(--color-text-secondary, #475569)" font-family="system-ui,sans-serif" font-size="8">{lbl}</text>')
    if col_labels:
        for j, lbl in enumerate(col_labels):
            x = label_w + j * (cell_size + gap) + cell_size // 2
            parts.append(f'<text x="{x}" y="{header_h - 4}" text-anchor="middle" fill="var(--color-text-secondary, #475569)" font-family="system-ui,sans-serif" font-size="8">{lbl}</text>')
    parts.append('</svg>')
    return "\n".join(parts)


def donut_svg(breakdown: dict, width: int = 140, height: int = 140) -> str:
    """Donut chart showing source proportions (HN, arXiv, PubMed)."""
    total = sum(breakdown.get(k, 0) for k in ("hn", "arxiv", "pubmed")) or 1
    cx, cy = width // 2, height // 2
    r = min(cx, cy) - 8
    inner_r = r * 0.6
    keys = [k for k in ("hn", "arxiv", "pubmed") if breakdown.get(k, 0) > 0]
    if not keys:
        keys = ["hn"]
    vals = [breakdown.get(k, 0) for k in keys]
    colors = [SOURCE_COLORS.get(k, "#94a3b8") for k in keys]
    # SVG arc helper: returns arc path from start_angle to end_angle
    def arc_path(cx, cy, r, a1, a2):
        a1r = math.radians(a1)
        a2r = math.radians(a2)
        x1 = cx + r * math.cos(a1r)
        y1 = cy + r * math.sin(a1r)
        x2 = cx + r * math.cos(a2r)
        y2 = cy + r * math.sin(a2r)
        large = 1 if (a2 - a1) > 180 else 0
        return f"M {cx},{cy} L {x1:.1f},{y1:.1f} A {r},{r} 0 {large},1 {x2:.1f},{y2:.1f} Z"

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        f'<rect width="{width}" height="{height}" fill="none"/>',
    ]
    start = 0
    for val, c in zip(vals, colors):
        angle = val / total * 360
        end = start + angle
        if angle > 0.5:
            parts.append(f'<path d="{arc_path(cx, cy, r, start, end)}" fill="{c}" opacity="0.85"/>')
        start = end

    # Inner circle (creates donut hole) with legend
    parts.append(f'<circle cx="{cx}" cy="{cy}" r="{inner_r}" fill="var(--color-bg, #0f172a)"/>')
    parts.append(f'<text x="{cx}" y="{cy - 2}" text-anchor="middle" dominant-baseline="middle" fill="var(--color-text, #e8e6e3)" font-family="system-ui,sans-serif" font-size="14" font-weight="700">{total}</text>')
    parts.append(f'<text x="{cx}" y="{cy + 12}" text-anchor="middle" dominant-baseline="middle" fill="var(--color-text-secondary, #475569)" font-family="system-ui,sans-serif" font-size="7">sources</text>')
    # Legend below
    ly = height - 12
    lx_start = 10
    lx = lx_start
    for key in ("hn", "arxiv", "pubmed"):
        val = breakdown.get(key, 0)
        if val <= 0:
            continue
        c = SOURCE_COLORS.get(key, "#94a3b8")
        parts.append(f'<rect x="{lx}" y="{ly - 4}" width="8" height="8" rx="1" fill="{c}"/>')
        parts.append(f'<text x="{lx + 10}" y="{ly + 2}" fill="var(--color-text-secondary, #475569)" font-family="system-ui,sans-serif" font-size="8">{SOURCE_LABELS.get(key, key)}</text>')
        lx += 50
    parts.append('</svg>')
    return "\n".join(parts)
