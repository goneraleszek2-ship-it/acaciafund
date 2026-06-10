"""SVG template generators for Tier 3 fallback visuals.
Guarantees every section has a visual — no network fetch needed."""

import html
import math
from typing import Any

PILLAR_VISUALS = {
    "data-engineering": {
        "name": "Data Engineering",
        "primary": "#2563eb",
        "dark": "#1e3a5f",
        "darker": "#0f172a",
        "accent": "#38bdf8",
        "icon_accent": "#60a5fa",
        "label": "DATA",
    },
    "aml": {
        "name": "AML",
        "primary": "#dc2626",
        "dark": "#7f1d1d",
        "darker": "#1a0a0a",
        "accent": "#fca5a5",
        "icon_accent": "#f87171",
        "label": "AML",
    },
    "stock": {
        "name": "Markets",
        "primary": "#059669",
        "dark": "#064e3b",
        "darker": "#0a1a10",
        "accent": "#6ee7b7",
        "icon_accent": "#34d399",
        "label": "MKT",
    },
}

DEFAULT_VISUAL = PILLAR_VISUALS["data-engineering"]

SECTION_ICON_INDEX = {
    0: 0,  # overview
    1: 1,  # key_findings
    2: 2,  # applied_scenario
    3: 3,  # source_analysis
    4: 4,  # domain_breakdown
    5: 5,  # cross_pillar
    6: 6,  # methodology
}

SECTION_LABEL = {
    0: "OVERVIEW",
    1: "KEY FINDINGS",
    2: "APPLIED SCENARIO",
    3: "SOURCE ANALYSIS",
    4: "DOMAIN BREAKDOWN",
    5: "CROSS-PILLAR CONNECTIONS",
    6: "METHODOLOGY NOTES",
}

SECTION_ALT_LABEL = {
    0: "Synthesis Overview",
    1: "Core Findings",
    2: "Practical Application",
    3: "Source Analysis",
    4: "Domain Breakdown",
    5: "Cross Connections",
    6: "Methodology",
}


def _pillar_visual(pillar: str) -> dict:
    return PILLAR_VISUALS.get(pillar, DEFAULT_VISUAL)


def _icon_paths(index: int) -> str:
    """Return SVG path data for section-type icon.
    Simple geometric shapes — clean, professional, no external deps."""
    icons = [
        # 0: overview — concentric circles (eye-like)
        '<circle cx="60" cy="60" r="28" fill="none" stroke="currentColor" stroke-width="2.5" opacity="0.3"/>'
        '<circle cx="60" cy="60" r="18" fill="none" stroke="currentColor" stroke-width="2.5" opacity="0.5"/>'
        '<circle cx="60" cy="60" r="8" fill="currentColor" opacity="0.7"/>',

        # 1: key_findings — star burst
        '<path d="M60 25 L65 48 L88 48 L69 61 L75 84 L60 70 L45 84 L51 61 L32 48 L55 48 Z"'
        ' fill="currentColor" opacity="0.3"/>'
        '<circle cx="60" cy="55" r="8" fill="currentColor" opacity="0.6"/>',

        # 2: applied_scenario — play triangle
        '<path d="M40 35 L80 55 L40 75 Z" fill="currentColor" opacity="0.3"/>'
        '<circle cx="55" cy="55" r="14" fill="none" stroke="currentColor" stroke-width="2" opacity="0.5"/>',

        # 3: source_analysis — document
        '<rect x="40" y="30" width="40" height="50" rx="4" fill="none" stroke="currentColor" stroke-width="2" opacity="0.3"/>'
        '<line x1="48" y1="44" x2="72" y2="44" stroke="currentColor" stroke-width="1.5" opacity="0.5"/>'
        '<line x1="48" y1="52" x2="72" y2="52" stroke="currentColor" stroke-width="1.5" opacity="0.5"/>'
        '<line x1="48" y1="60" x2="62" y2="60" stroke="currentColor" stroke-width="1.5" opacity="0.5"/>',

        # 4: domain_breakdown — stacked bars
        '<rect x="35" y="50" width="12" height="30" rx="2" fill="currentColor" opacity="0.3"/>'
        '<rect x="51" y="38" width="12" height="42" rx="2" fill="currentColor" opacity="0.45"/>'
        '<rect x="67" y="44" width="12" height="36" rx="2" fill="currentColor" opacity="0.6"/>',

        # 5: cross_pillar — linked nodes
        '<circle cx="42" cy="55" r="10" fill="none" stroke="currentColor" stroke-width="2" opacity="0.3"/>'
        '<circle cx="78" cy="55" r="10" fill="none" stroke="currentColor" stroke-width="2" opacity="0.3"/>'
        '<circle cx="60" cy="38" r="8" fill="none" stroke="currentColor" stroke-width="2" opacity="0.3"/>'
        '<line x1="52" y1="48" x2="56" y2="43" stroke="currentColor" stroke-width="1.5" opacity="0.5"/>'
        '<line x1="68" y1="48" x2="64" y2="43" stroke="currentColor" stroke-width="1.5" opacity="0.5"/>'
        '<line x1="52" y1="60" x2="68" y2="60" stroke="currentColor" stroke-width="1.5" opacity="0.5"/>',

        # 6: methodology — funnel
        '<path d="M35 30 L85 30 L72 48 L48 48 Z" fill="currentColor" opacity="0.2"/>'
        '<path d="M45 48 L75 48 L65 62 L55 62 Z" fill="currentColor" opacity="0.35"/>'
        '<rect x="52" y="62" width="16" height="10" rx="2" fill="currentColor" opacity="0.5"/>',
    ]
    return icons[index % len(icons)]


def _decorative_dots(w: int, h: int, seed: int = 0) -> str:
    """A few subtle decorative dots in the background."""
    dots = []
    rng = random(seed)
    for _ in range(8):
        x = 40 + (next(rng) * (w - 80))
        y = 40 + (next(rng) * (h - 80))
        r = 1.5 + next(rng) * 3
        dots.append(
            f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r:.1f}" '
            f'fill="rgba(255,255,255,{0.03 + next(rng) * 0.04:.2f})"/>'
        )
    return "".join(dots)


def random(seed: int = 0):
    """Simple deterministic pseudo-random generator."""
    import random as _random
    rng = _random.Random(seed)
    while True:
        yield rng.random()


def generate_fallback_svg(section: dict, article: dict) -> str:
    """Generate an inline SVG HTML string for a section without an image.

    The SVG uses pillar colors, a section-type icon, and article metadata.
    Returns a complete <svg> element as a string.
    """
    pillar = article.get("pillar", "")
    v = _pillar_visual(pillar)
    idx = section.get("section_index", 0)
    heading = section.get("heading", "") or ""
    title = article.get("title", "")
    section_type = section.get("section_type", "")
    alt_label = SECTION_ALT_LABEL.get(idx, "")
    section_label = SECTION_LABEL.get(idx, "")

    w, h = 800, 400
    icon_html = _icon_paths(SECTION_ICON_INDEX.get(idx, 0))
    dots_html = _decorative_dots(w, h, seed=hash(title + str(idx)) & 0xFFFF)

    truncated_title = (title[:60] + "…") if len(title) > 60 else title
    truncated_heading = (heading[:40] + "…") if len(heading) > 40 else heading

    svg = (
        f'<svg class="section-fallback-svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" '
        f'style="width:100%;height:auto;display:block;border-radius:0.5rem;">'
        f'<defs>'
        f'<linearGradient id="fbsg" x1="0%" y1="0%" x2="100%" y2="100%">'
        f'<stop offset="0%" style="stop-color:{v["dark"]}"/>'
        f'<stop offset="100%" style="stop-color:{v["darker"]}"/>'
        f'</linearGradient>'
        f'</defs>'
        f'<rect width="{w}" height="{h}" fill="url(#fbsg)" rx="8"/>'
        f'<rect width="{w}" height="{h}" fill="none" stroke="{v["primary"]}" '
        f'stroke-width="1" rx="8" opacity="0.15"/>'
        f'<line x1="0" y1="0" x2="80" y2="0" stroke="{v["accent"]}" '
        f'stroke-width="3" opacity="0.3"/>'
        # decorative dots
        f'{dots_html}'
        # pillar label badge
        f'<rect x="36" y="38" width="58" height="24" rx="4" '
        f'fill="{v["primary"]}" opacity="0.25"/>'
        f'<text x="65" y="54" fill="{v["accent"]}" '
        f'font-family="system-ui,sans-serif" font-size="11" '
        f'font-weight="700" text-anchor="middle" letter-spacing="1">{v["label"]}</text>'
        # section icon
        f'<g transform="translate(0,0)" '
        f'fill="{v["icon_accent"]}" opacity="0.25">'
        f'{icon_html}'
        f'</g>'
        # section header
        f'<text x="40" y="200" fill="rgba(255,255,255,0.9)" '
        f'font-family="system-ui,sans-serif" font-size="22" '
        f'font-weight="600">{html.escape(truncated_heading)}</text>'
        # article title
        f'<text x="40" y="232" fill="rgba(255,255,255,0.4)" '
        f'font-family="system-ui,sans-serif" font-size="14">'
        f'{html.escape(truncated_title)}</text>'
        # section label at bottom-right
        f'<text x="{w - 40}" y="{h - 24}" '
        f'fill="rgba(255,255,255,0.15)" '
        f'font-family="system-ui,sans-serif" font-size="10" '
        f'text-anchor="end" letter-spacing="1">{section_label}</text>'
        # subtle bottom border accent
        f'<line x1="0" y1="{h - 2}" x2="{w}" y2="{h - 2}" '
        f'stroke="{v["accent"]}" stroke-width="2" opacity="0.15"/>'
        f'</svg>'
    )
    return svg


def generate_manifest_entry(section: dict, article: dict,
                            image_url: str, credit: str, alt: str) -> dict:
    """Build a section_image dict for a manifest entry."""
    return {
        "section_index": section.get("section_index", 0),
        "heading": section.get("heading", ""),
        "image_url": image_url,
        "image_credit": credit,
        "image_alt": alt,
        "relevance_score": 100.0,
        "source_api": "manifest",
        "width": 1200,
        "height": 675,
        "content_hash": "",
    }
