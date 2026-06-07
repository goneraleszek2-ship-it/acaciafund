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


def generate_thumbnail_svg(title: str, pillar: str, scores: dict,
                           width: int = 600, height: int = 340) -> str:
    """Generate a content-aware SVG thumbnail for a blog post.

    The thumbnail uses the article's topic, pillar palette, and signal data
    to create a unique, non-generic visual.
    """
    pal = PILLAR_COLORS.get(pillar, PILLAR_COLORS["aml"])
    sub = _pick_subtopic([title], pillar)
    icon_path = TOPIC_ICONS.get(sub, TOPIC_ICONS["regulation"])
    words = _extract_topic_words([title], 3)

    # Create a unique but deterministic pattern from the title
    h = _content_hash(title)
    offset1 = int(h[:4], 16) % 100
    offset2 = int(h[4:8], 16) % 100
    offset3 = int(h[8:12], 16) % 100

    sqi = scores.get("sqi", 0.5)
    bar_w = int(sqi * 200)

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        f'  <defs>',
        f'    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">',
        f'      <stop offset="0" stop-color="{pal["bg"]}"/>',
        f'      <stop offset="1" stop-color="{pal["fg"]}"/>',
        f'    </linearGradient>',
        f'    <radialGradient id="glow" cx="{30 + offset1 % 40}%" cy="{30 + offset2 % 40}%">',
        f'      <stop offset="0" stop-color="{pal["accent"]}" stop-opacity="0.15"/>',
        f'      <stop offset="1" stop-color="{pal["bg"]}" stop-opacity="0"/>',
        f'    </radialGradient>',
        f'  </defs>',
        f'  <rect width="{width}" height="{height}" fill="url(#bg)"/>',
        f'  <rect width="{width}" height="{height}" fill="url(#glow)"/>',
        "",
        f'  <!-- Decorative grid dots -->',
    ]

    # Decorative dots pattern
    for i in range(8):
        for j in range(5):
            dx = (offset3 + i * 17 + j * 31) % 100
            dy = (offset1 + i * 23 + j * 7) % 100
            opacity = 0.05 + ((i + j) % 5) * 0.03
            lines.append(
                f'  <circle cx="{20 + dx * 6}" cy="{30 + dy * 6}" r="1.5" fill="{pal["accent"]}" opacity="{opacity}"/>'
            )

    lines.append("")
    lines.append(f'  <!-- Topic icon -->')
    lines.append(f'  <g transform="translate(40, 50) scale(1.4)" stroke="{pal["accent"]}" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    lines.append(f'    {icon_path}')
    lines.append(f'  </g>')

    lines.append("")
    lines.append(f'  <!-- Topic words as floating tags -->')
    for i, w in enumerate(words[:3]):
        x = 40 + (offset2 + i * 37) % 200
        y = 200 + i * 40
        lines.append(
            f'  <text x="{x}" y="{y}" fill="{pal["accent"]}" font-family="system-ui,sans-serif" '
            f'font-size="14" font-weight="600" opacity="0.4">{w}</text>'
        )

    lines.append("")
    lines.append(f'  <!-- SQI bar -->')
    lines.append(f'  <text x="40" y="260" fill="{pal["accent"]}" font-family="system-ui,sans-serif" font-size="11" font-weight="600" opacity="0.6">SIGNAL QUALITY</text>')
    lines.append(f'  <rect x="40" y="270" width="200" height="4" rx="2" fill="{pal["text"]}" opacity="0.1"/>')
    lines.append(f'  <rect x="40" y="270" width="{bar_w}" height="4" rx="2" fill="{pal["accent"]}" opacity="0.8"/>')
    lines.append(f'  <text x="250" y="274" fill="{pal["accent"]}" font-family="system-ui,sans-serif" font-size="12" font-weight="700">{sqi:.2f}</text>')

    lines.append("")
    lines.append(f'  <!-- Category badge -->')
    lines.append(f'  <rect x="40" y="290" width="80" height="24" rx="4" fill="{pal["accent"]}" opacity="0.2"/>')
    lines.append(f'  <text x="80" y="306" text-anchor="middle" fill="{pal["accent"]}" font-family="system-ui,sans-serif" font-size="11" font-weight="700" text-transform="uppercase">{pillar.upper()}</text>')

    lines.append(f'</svg>')
    return "\n".join(lines)


def generate_og_image(title: str, pillar: str, scores: dict,
                      date_str: str = "") -> str:
    """Generate a social sharing OG image SVG with the article title."""
    pal = PILLAR_COLORS.get(pillar, PILLAR_COLORS["aml"])
    sub = _pick_subtopic([title], pillar)
    icon_path = TOPIC_ICONS.get(sub, TOPIC_ICONS["regulation"])

    # Wrap title text
    words = title.split()
    lines_text = []
    line = ""
    for w in words:
        if len(line + w) > 40:
            lines_text.append(line.strip())
            line = w + " "
        else:
            line += w + " "
    lines_text.append(line.strip())
    title_lines = lines_text[:4]

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630">',
        f'  <defs>',
        f'    <linearGradient id="ogbg" x1="0" y1="0" x2="1" y2="1">',
        f'      <stop offset="0" stop-color="{pal["bg"]}"/>',
        f'      <stop offset=".5" stop-color="{pal["fg"]}"/>',
        f'      <stop offset="1" stop-color="{pal["bg"]}"/>',
        f'    </linearGradient>',
        f'    <radialGradient id="ogglow" cx="70%" cy="50%">',
        f'      <stop offset="0" stop-color="{pal["accent"]}" stop-opacity=".08"/>',
        f'      <stop offset="1" stop-color="#000" stop-opacity="0"/>',
        f'    </radialGradient>',
        f'  </defs>',
        f'  <rect width="1200" height="630" fill="url(#ogbg)"/>',
        f'  <rect width="1200" height="630" fill="url(#ogglow)"/>',
        "",
        f'  <!-- Decorative circles -->',
        f'  <circle cx="1000" cy="150" r="300" fill="{pal["accent"]}" opacity=".03"/>',
        f'  <circle cx="200" cy="500" r="200" fill="{pal["accent"]}" opacity=".02"/>',
        f'  <circle cx="1100" cy="400" r="150" fill="{pal["accent"]}" opacity=".04"/>',
        "",
        f'  <!-- Icon -->',
        f'  <g transform="translate(50, 50) scale(1.8)" stroke="{pal["accent"]}" fill="none" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5">',
        f'    {icon_path}',
        f'  </g>',
    ]

    # Title lines
    y = 260
    for tl in title_lines:
        parts.append(
            f'  <text x="50" y="{y}" fill="{pal["text"]}" font-family="system-ui,sans-serif" '
            f'font-size="{44 if len(tl) < 35 else 36}" font-weight="700">'
            f'{tl.replace("&", "&amp;").replace("<", "&lt;")}</text>'
        )
        y += 52

    parts.extend([
        "",
        f'  <!-- Meta -->',
        f'  <text x="50" y="500" fill="{pal["accent"]}" font-family="system-ui,sans-serif" font-size="18" font-weight="600">AcaciaFund &nbsp;·&nbsp; {pillar.upper()}',
        f'{" &nbsp;·&nbsp; " + date_str if date_str else ""}</text>',
        f'  <text x="50" y="540" fill="{pal["text"]}" font-family="system-ui,sans-serif" font-size="14" opacity="0.5">Codzienna synteza badan — AML, rynki, nauka</text>',
        f'  <rect x="50" y="570" width="{int(min(1.0, scores.get("sqi", 0.5)) * 200)}" height="4" rx="2" fill="{pal["accent"]}" opacity="0.8"/>',
        f'</svg>',
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
