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
        f'  <rect width="{width}" height="6" y="5" rx="3" fill="#e2e8f0"/>'
        f'  <rect width="{bar_w}" height="6" y="5" rx="3" fill="{color}"/>'
        f'  <circle cx="{max(6, bar_w)}" cy="8" r="5" fill="{color}"/>'
        f'  <text x="{width + 8}" y="13" fill="#64748b" font-family="system-ui,sans-serif" font-size="11">{sqi:.2f}</text>'
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
