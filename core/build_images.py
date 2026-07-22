"""Image utilities extracted from build.py.

Pictogram selection, image resolution, thumbnail generation, and
other image-related helpers used by the AcaciaFund build pipeline.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from PIL import Image

from config import PROJECT_ROOT, SITE_URL


VISUAL_RULES = json.loads((Path(__file__).parent.parent / "config" / "visual_rules.json").read_text(encoding="utf-8"))
CARD_PICTOGRAM_KEYWORDS = VISUAL_RULES["card_pictogram_keywords"]
_PICTOGRAM_PILLAR_DEFAULTS = VISUAL_RULES["pictogram_pillar_defaults"]
_PICTOGRAM_CONTENT_TYPE_FALLBACK = VISUAL_RULES["pictogram_content_type_fallback"]


def pick_card_pictogram(content) -> str | None:
    """Pick the most relevant pictogram based on title, tags, pillar, and content type.

    Uses scoring system with priority levels to find best match:
    - Priority 1: Core concepts (ai, realtime, platform)
    - Priority 2: Content types (tutorial, comparison, case-study)
    - Priority 3: AML-specific (aml, fraud)
    - Priority 4-8: New categories (security, devops, analytics, monitoring, cloud)
    - Priority 9-11: Markets & Data Engineering (finance, market, pipeline, infrastructure, database, api)
    """
    text = " ".join(
        [
            *(t.lower().replace("-", " ") for t in (content.tags or [])),
            (content.title or "").lower(),
        ]
    )
    pillar = (content.pillar or "").lower()
    content_type = (content.content_type or "").lower()

    priority_map = VISUAL_RULES["priority_map"]

    for priority in range(1, 12):
        for img_name, keywords in CARD_PICTOGRAM_KEYWORDS.items():
            if priority_map.get(img_name) != priority:
                continue
            for kw in keywords:
                if kw.lower() in text:
                    return f"{img_name}.svg"

    scores = {}
    for img_name, keywords in CARD_PICTOGRAM_KEYWORDS.items():
        score = 0
        for kw in keywords:
            if kw.lower() in text:
                score += 10
                if kw.lower() == text.strip():
                    score += 50
                if len(kw.split()) > 1 and kw.lower() in text:
                    score += 20

        priority_mult = (12 - priority_map.get(img_name, 6)) * 0.5
        score *= 1 + priority_mult

        if pillar == "aml" and img_name in ["aml", "fraud", "security"]:
            score *= 1.5
        elif pillar == "stock" and img_name in ["finance", "market"]:
            score *= 1.5
        elif pillar == "data-engineering" and img_name in [
            "pipeline",
            "infrastructure",
            "database",
            "api",
            "monitoring",
            "devops",
        ]:
            score *= 1.5

        if content_type == "learn" and img_name == "tutorial":
            score *= 1.3

        if score > 0:
            scores[img_name] = score

    if scores:
        best_match = max(scores.items(), key=lambda x: x[1])
        return f"{best_match[0]}.svg"

    if pillar in _PICTOGRAM_PILLAR_DEFAULTS:
        return _PICTOGRAM_PILLAR_DEFAULTS[pillar]

    if content_type in _PICTOGRAM_CONTENT_TYPE_FALLBACK:
        return _PICTOGRAM_CONTENT_TYPE_FALLBACK[content_type]

    return "icon-research.svg"


def _resolve_ref_file(p: Path) -> str:
    """If p is a REF: pointer file, return the URL of the original image."""
    if p.exists() and p.is_file():
        try:
            content = p.read_text(encoding="utf-8").strip()
            if content.startswith("REF:"):
                original_name = content[4:]
                original_path = p.parent / original_name
                if original_path.exists():
                    rel = str(original_path.relative_to(PROJECT_ROOT))
                    return f"{SITE_URL}/{rel}"
        except (OSError, UnicodeDecodeError):
            pass
    return ""


def resolve_featured_image(raw_path: str) -> str:
    """Resolve featured_image path to absolute URL, trying multiple extensions."""
    if not raw_path:
        return ""
    p = Path(PROJECT_ROOT / raw_path.lstrip("/"))
    if p.exists():
        ref = _resolve_ref_file(p)
        if ref:
            return ref
        return f"{SITE_URL}{raw_path}" if raw_path.startswith("/") else f"{SITE_URL}/{raw_path}"
    stem = p.stem
    for ext in (".webp", ".png", ".jpg", ".jpeg", ".svg"):
        alt = p.parent / f"{stem}{ext}"
        if alt.exists():
            ref = _resolve_ref_file(alt)
            if ref:
                return ref
            resolved = raw_path.rsplit("/", 1)[0] + "/" + alt.name
            return f"{SITE_URL}{resolved}" if resolved.startswith("/") else f"{SITE_URL}/{resolved}"
    for ext in (".webp", ".png", ".jpg", ".jpeg", ".svg"):
        s1_path = p.parent / f"{stem}_s1{ext}"
        if s1_path.exists():
            ref = _resolve_ref_file(s1_path)
            if ref:
                return ref
            resolved = raw_path.rsplit("/", 1)[0] + "/" + s1_path.name
            return f"{SITE_URL}{resolved}" if resolved.startswith("/") else f"{SITE_URL}/{resolved}"
    return ""


def resolve_section_image(url: str) -> str:
    """Resolve section image URL, trying alternate extensions if file missing."""
    if not url:
        return ""
    p = Path(PROJECT_ROOT / url.lstrip("/"))
    if p.exists():
        ref = _resolve_ref_file(p)
        if ref:
            return ref
        return url
    for ext in (".webp", ".png", ".jpg", ".jpeg", ".svg"):
        alt = p.with_suffix(ext)
        if alt.exists():
            ref = _resolve_ref_file(alt)
            if ref:
                return ref
            return url.rsplit(".", 1)[0] + ext
    stem = p.stem
    ext = p.suffix if p.suffix else ".webp"
    s1_path = p.parent / f"{stem}_s1{ext}"
    if s1_path.exists():
        ref = _resolve_ref_file(s1_path)
        if ref:
            return ref
        return url.rsplit(".", 1)[0] + "_s1" + ext
    for ext in (".webp", ".png", ".jpg", ".jpeg", ".svg"):
        s1_alt = p.parent / f"{stem}_s1{ext}"
        if s1_alt.exists():
            ref = _resolve_ref_file(s1_alt)
            if ref:
                return ref
            return url.rsplit(".", 1)[0] + "_s1" + ext
    return ""


def generate_card_thumbnail(source_url: str, slug: str) -> str:
    """Generate a 200x150 card thumbnail from a featured image. Returns URL path or empty string."""
    if not source_url:
        return ""
    raw = source_url.lstrip("/")
    src = Path(PROJECT_ROOT / raw)
    if src.suffix.lower() == ".svg":
        return source_url
    if not src.exists() or src.stat().st_size == 0:
        return ""
    try:
        ref = _resolve_ref_file(src)
        if ref:
            resolved = Path(PROJECT_ROOT / ref.lstrip("/").replace(f"{SITE_URL}/", "", 1))
            if resolved.exists():
                src = resolved
    except (OSError, AttributeError):
        pass
    prefix = source_url.rsplit("/", 1)[0]
    stem = src.stem
    ext = src.suffix if src.suffix else ".webp"
    thumb_name = f"{stem}_card{ext}"
    thumb_path = src.parent / thumb_name
    thumb_url = f"{prefix}/{thumb_name}"
    if not thumb_path.exists() or src.stat().st_mtime > thumb_path.stat().st_mtime:
        try:
            with Image.open(src) as img:
                img.thumbnail((200, 150), Image.Resampling.LANCZOS)
                img.save(thumb_path, optimize=True)
        except (OSError, ValueError) as e:
            print(f"  WARNING: card thumbnail failed for {slug}: {e}")
            return ""
    return thumb_url


def generate_missing_ai_image(url: str) -> str:
    """Generate a simple AI fallback SVG for missing section images."""
    if not url:
        return ""
    p = Path(PROJECT_ROOT / url.lstrip("/"))
    if p.exists():
        return url
    slug = url.split("/")[-1].rsplit(".", 1)[0]
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="675" viewBox="0 0 1200 675">
      <defs>
        <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" style="stop-color:#1a1a2e;stop-opacity:1" />
          <stop offset="100%" style="stop-color:#16213e;stop-opacity:1" />
        </linearGradient>
      </defs>
      <rect width="1200" height="675" fill="url(#bg)"/>
      <text x="600" y="337" font-family="monospace" font-size="16" fill="#4cc9f0" text-anchor="middle">{slug}</text>
    </svg>"""
    svg_path = p.with_suffix(".svg")
    svg_path.parent.mkdir(parents=True, exist_ok=True)
    svg_path.write_text(svg, encoding="utf-8")
    return url.rsplit(".", 1)[0] + ".svg"


def thumbnail_key(title: str) -> str:
    return hashlib.md5(title.encode()).hexdigest()[:12]
