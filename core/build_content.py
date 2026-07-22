"""Content processing utilities extracted from build.py.

Page generation helpers, article processing, image/SVG generation,
JSON-LD, quiz serialization, and content rendering for the AcaciaFund build pipeline.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import shutil
from typing import Any

from config import (
    OUTPUT_DIR,
    PILLAR_FINGERPRINT_COLORS,
    SITE_URL,
    SQI_DEFAULT,
    STATIC_DST_DIR,
)
from core.brand import section_type_color
from core.build_images import resolve_featured_image, resolve_section_image
from core.build_utils import (
    add_lazy_loading,
    extract_headings,
    get_topic_icons,
    sanitize_domain_breakdown,
    sanitize_text,
    strip_html_tag,
)
from core.images.templates import generate_fallback_svg
from core.urls import slug_to_fspath, slug_to_path
from core.visuals import generate_og_image, generate_thumbnail_svg

SECTION_TYPES = {
    0: "overview",
    1: "key_findings",
    2: "applied_scenario",
    3: "source_analysis",
    4: "domain_breakdown",
    5: "cross_pillar",
    6: "methodology",
}

LAYER_SYMBOLS = {
    "research": (
        "path",
        '<path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" fill="none" stroke="currentColor" stroke-width="1.5"/>',
    ),
    "learn": (
        "path",
        '<path d="M4 19.5A2.5 2.5 0 016.5 17H20" fill="none" stroke="currentColor" stroke-width="1.5"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 014 19.5v-15A2.5 2.5 0 016.5 2z" fill="none" stroke="currentColor" stroke-width="1.5"/>',
    ),
    "knowledge": (
        "circle",
        '<circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" stroke-width="1.5"/><path d="M12 6v6l4 2" fill="none" stroke="currentColor" stroke-width="1.5"/>',
    ),
}

LAYER_LABELS = {"research": "Research", "learn": "Learn", "knowledge": "Knowledge"}
LAYER_ICONS = {"research": "\u25c7", "learn": "\u25c9", "knowledge": "\u25ce"}


def _get_article_attr(article, key: str, default=None):
    """Helper: get attribute from AcaciaContent or key from dict."""
    if article is None:
        return default
    if isinstance(article, dict):
        return article.get(key, default)
    return getattr(article, key, default)


def _article_as_dict(article):
    """Convert article (AcaciaContent or dict) to a plain dict."""
    if article is None:
        return {}
    if isinstance(article, dict):
        return article
    return article.dict()


def get_layer(url_path: str) -> str:
    if url_path.startswith("learn") or url_path.startswith("learn/"):
        return "learn"
    if url_path.startswith("knowledge") or url_path.startswith("knowledge/"):
        return "knowledge"
    return "research"


def generate_article_fingerprint(
    slug: str, title: str, pillar: str, content_type: str, tags: list
) -> str:
    """Generate a unique SVG ident for an article - a mini tartan-like pattern.

    The fingerprint is derived from:
      - Pillar -> base color
      - Content type -> pattern style (bars/dots/diagonals)
      - Title hash -> pattern permutation
      - Tags -> number of columns
    """
    h = int(hashlib.md5((slug + title).encode()).hexdigest()[:6], 16)
    base_color = PILLAR_FINGERPRINT_COLORS.get(pillar, "#6366f1")
    column_count = 3 + (h % 5)
    row_count = 3 + ((h >> 8) % 3)

    bars = []
    for col in range(column_count):
        cx = 4 + col * (120 // column_count)
        bar_h = 5 + ((h >> (col * 4)) % 10)
        for row in range(row_count):
            if (h >> (col + row * 7)) & 1:
                ry = 4 + row * (28 // row_count)
                opacity = 0.3 + ((h >> (col * 3 + row * 2)) % 5) * 0.14
                if content_type == "learn":
                    bars.append(
                        f'<circle cx="{cx}" cy="{ry + 6}" r="{bar_h // 4}" fill="{base_color}" opacity="{opacity}"/>'
                    )
                elif content_type == "knowledge":
                    bars.append(
                        f'<line x1="{cx - 3}" y1="{ry}" x2="{cx + 3}" y2="{ry + 12}" stroke="{base_color}" stroke-width="1.5" opacity="{opacity}"/>'
                    )
                else:
                    bars.append(
                        f'<rect x="{cx - 2}" y="{ry}" width="4" height="{bar_h}" rx="1" fill="{base_color}" opacity="{opacity}"/>'
                    )

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 32" width="120" height="32" aria-hidden="true">'
        f'<rect width="120" height="32" rx="2" fill="{base_color}" opacity="0.08"/>'
        f"{''.join(bars)}"
        f"</svg>"
    )


def layer_indicator_html(content_type: str, pillar: str = "") -> str:
    """Small visual badge showing which layer (research/learn/knowledge) the user is in."""
    sym_type, sym_path = LAYER_SYMBOLS.get(content_type, LAYER_SYMBOLS["research"])
    label = LAYER_LABELS.get(content_type, "Research")
    color = PILLAR_FINGERPRINT_COLORS.get(pillar, "#6366f1")
    return (
        f'<span class="inline-flex items-center gap-1.5 px-2 py-1 text-xs font-medium rounded" '
        f'style="background:{color}14;color:{color};border:1px solid {color}33">'
        f'<svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" aria-hidden="true">{sym_path}</svg>'
        f"{label}"
        f"</span>"
    )


def inject_section_images(body_html: str, section_images: list[dict], article=None) -> str:
    """Insert section-level images and data visualizations into body_html.

    Wraps each section in a .section-harvester div with:
    - Colored left border for section identity
    - Context-relevant data visualization (source bar, bloom chart, radar, etc.)
    - Collapsible content via <details>/<summary>
    - Section images placed between harvesters as visual transitions

    Matches by section_index (positional: 0 = first <h2>, 1 = second, etc.)
    """
    h2_pattern = re.compile(r"(<h2[^>]*>.*?</h2>)", re.IGNORECASE | re.DOTALL)
    parts = h2_pattern.split(body_html)
    if not parts:
        return body_html

    img_map: dict[int, dict] = {}
    if section_images:
        for si in section_images:
            idx = si.get("section_index")
            if idx is not None:
                img_map[idx] = si

    content_type = _get_article_attr(article, "content_type", "research")
    pillar = _get_article_attr(article, "pillar", "aml")
    use_harvesters = content_type in ("research", "learn", "knowledge")

    result: list[str] = [parts[0]]

    for i in range(1, len(parts), 2):
        h2_tag = parts[i]
        content = parts[i + 1] if i + 1 < len(parts) else ""
        section_idx = (i - 1) // 2

        entry = img_map.get(section_idx)
        section_type = SECTION_TYPES.get(section_idx, "overview")

        if use_harvesters:
            pillar_color = section_type_color(section_idx, pillar)

            result.append(
                f'<div class="section-harvester" data-section="{section_type}" '
                f'style="--section-color:{pillar_color}">'
            )
            result.append('<details class="section-collapse" open>')
            result.append(f'<summary class="section-summary">{h2_tag}</summary>')
            result.append(f'<div class="section-body">{content}</div>')
            result.append("</details>")
            result.append("</div>")

            if entry:
                url = resolve_section_image(entry.get("image_url", ""))
                credit = entry.get("image_credit", "")
                alt_ = entry.get("image_alt", "") or f"Illustration for {strip_html_tag(h2_tag)}"
                w = entry.get("width", 1200)
                h = entry.get("height", 675)
                if url:
                    style_class = (
                        "section-image--full"
                        if section_idx % 2 == 0
                        else "section-image--contained"
                    )
                    figure_style = "background:var(--color-bg);border:1px solid var(--color-border)"
                    caption_id = f"sec-caption-{section_idx}" if credit else ""
                    aria_attr = f' aria-describedby="{caption_id}"' if credit else ""
                    f = [
                        f'<figure class="section-image {style_class} my-6 rounded-lg overflow-hidden"',
                        f' style="{figure_style}"{aria_attr}>',
                        f'<img src="{url}" alt="{alt_}" width="{w}" height="{h}"',
                        ' loading="lazy" decoding="async"',
                        ' class="w-full h-auto object-cover">',
                    ]
                    if credit:
                        f.append(
                            f'<figcaption id="{caption_id}" class="px-3 py-1.5 text-xs"'
                            ' style="color:var(--color-text-muted);border-top:1px solid var(--color-border)">'
                            f"{credit}</figcaption>"
                        )
                    f.append("</figure>")
                    result.append("".join(f))
                elif article:
                    section = {"section_index": section_idx, "heading": strip_html_tag(h2_tag)}
                    article_dict = _article_as_dict(article)
                    try:
                        svg = generate_fallback_svg(section, article_dict)
                        result.append(
                            f'<figure class="section-image section-image--full section-fallback my-6 rounded-lg overflow-hidden"'
                            f' style="background:var(--color-bg);border:1px solid var(--color-border)">'
                            f"{svg}</figure>"
                        )
                    except (ValueError, TypeError, OSError):
                        pass
        else:
            result.append(h2_tag)
            if entry:
                url = resolve_section_image(entry.get("image_url", ""))
                credit = entry.get("image_credit", "")
                alt_ = entry.get("image_alt", "") or f"Illustration for {strip_html_tag(h2_tag)}"
                w = entry.get("width", 1200)
                h = entry.get("height", 675)
                if url:
                    style_class = (
                        "section-image--full"
                        if section_idx % 2 == 0
                        else "section-image--contained"
                    )
                    figure_style = "background:var(--color-bg);border:1px solid var(--color-border)"
                    caption_id = f"sec-caption-{section_idx}" if credit else ""
                    aria_attr = f' aria-describedby="{caption_id}"' if credit else ""
                    f = [
                        f'<figure class="section-image {style_class} my-6 rounded-lg overflow-hidden"',
                        f' style="{figure_style}"{aria_attr}>',
                        f'<img src="{url}" alt="{alt_}" width="{w}" height="{h}"',
                        ' loading="lazy" decoding="async"',
                        ' class="w-full h-auto object-cover">',
                    ]
                    if credit:
                        f.append(
                            f'<figcaption id="{caption_id}" class="px-3 py-1.5 text-xs"'
                            ' style="color:var(--color-text-muted);border-top:1px solid var(--color-border)">'
                            f"{credit}</figcaption>"
                        )
                    f.append("</figure>")
                    result.append("".join(f))
                elif article:
                    section = {"section_index": section_idx, "heading": strip_html_tag(h2_tag)}
                    article_dict = _article_as_dict(article)
                    try:
                        svg = generate_fallback_svg(section, article_dict)
                        result.append(
                            f'<figure class="section-image section-image--full section-fallback my-6 rounded-lg overflow-hidden"'
                            f' style="background:var(--color-bg);border:1px solid var(--color-border)">'
                            f"{svg}</figure>"
                        )
                    except (ValueError, TypeError, OSError):
                        pass
            result.append(content)

    return "".join(result)


def _process_item_body(item, strip_emoji: bool = False) -> tuple[str, list]:
    """Process item body HTML: lazy loading, headings, sanitization.
    Returns (processed_html, toc_items). Also mutates item.body_html and item.description.
    """
    body = add_lazy_loading(item.body_html)
    body, toc_items = extract_headings(body)
    body = sanitize_domain_breakdown(body)
    body = inject_section_images(body, item.section_images, item)
    body = re.sub(
        r"<h2[^>]*>\s*" + re.escape(item.title.strip()) + r"\s*</h2>\s*", "", body, count=1
    )
    body = sanitize_text(body, strip_emoji=strip_emoji)
    item.description = sanitize_text(item.description, strip_emoji=strip_emoji)
    item.body_html = body
    return body, toc_items


def _generate_page_images(item, layer: str) -> tuple[str, str, str, str, str]:
    """Generate thumbnail key, OG key, featured image path, OG URL, and thumb base URL."""
    thumb_key = hashlib.md5(item.title.encode()).hexdigest()[:12]
    og_key = hashlib.md5(f"og_{item.title}".encode()).hexdigest()[:12]
    thumb_base = f"{SITE_URL}/static/images"
    feat_img_path = resolve_featured_image(item.featured_image or "")
    og_image_url = (
        feat_img_path if feat_img_path else f"{SITE_URL}/static/images/og_{og_key}.svg"
    )
    return thumb_key, og_key, feat_img_path, og_image_url, thumb_base


def _generate_page_svgs(item, layer: str, thumb_key: str, og_key: str) -> None:
    """Generate and write thumbnail and OG image SVGs for a content item."""
    out_static = STATIC_DST_DIR / "images"
    out_static.mkdir(parents=True, exist_ok=True)
    pillar = item.pillar or "aml"
    scores = item.signals or {"sqi": SQI_DEFAULT}
    if not isinstance(scores, dict):
        scores = {"sqi": SQI_DEFAULT}
    feat = resolve_featured_image(item.featured_image or "")
    icons = get_topic_icons(item.tags) if not feat else []
    svg_thumb = generate_thumbnail_svg(
        item.title, pillar, scores, width=600, height=340,
        featured_image_url=feat, layer=layer, fallback_icons=icons,
    )
    (out_static / f"thumb_{thumb_key}.svg").write_text(svg_thumb, encoding="utf-8")
    svg_og = generate_og_image(
        item.title, pillar, scores, featured_image_url=feat,
        layer=layer, fallback_icons=icons,
    )
    (out_static / f"og_{og_key}.svg").write_text(svg_og, encoding="utf-8")


def _cleanup_partial_output(item):
    """Clean up partial output files for a failed item."""
    slug = None
    try:
        slug = item.slug
        out_path = OUTPUT_DIR / slug_to_fspath(slug_to_path(slug))
        if out_path.is_dir():
            shutil.rmtree(out_path)
        elif out_path.exists():
            out_path.unlink()
    except (OSError, shutil.Error) as e:
        logger = logging.getLogger(__name__)
        logger.warning(f"Cleanup failed for {slug}: {e}")


def _serialize_quiz(item) -> str:
    """Serialize bloom questions into a JSON string for the quiz JS."""
    if not item.bloom_questions:
        return ""
    quiz_data = {"questions": []}
    for bq in item.bloom_questions[:10]:
        if isinstance(bq, dict) and "question" in bq:
            qtype = bq.get("type", "mc")
            opts = bq.get("options", [])
            raw = bq.get("answer") if "answer" in bq else None
            if raw is None:
                correct_val = bq.get("correct", "")
                if isinstance(correct_val, str) and correct_val and opts:
                    raw = opts.index(correct_val) if correct_val in opts else 0
                else:
                    raw = 0
            entry = {"q": bq["question"], "options": opts, "a": raw, "type": qtype}
            if qtype == "open-ended":
                entry["answer_text"] = bq.get("correct", opts[raw] if opts else "")
            quiz_data["questions"].append(entry)
    if quiz_data["questions"]:
        return json.dumps(quiz_data, ensure_ascii=False)
    return ""


def _build_jsonld(item: Any, site_url: str, page_path: str = "") -> dict[str, Any]:
    """Build JSON-LD schema.org Article dict for a content item."""
    author_name = getattr(item, "author", None) or "AcaciaFund"
    tags = getattr(item, "tags", None) or []
    sqi_val = getattr(item, "sqi", 0.0) or 0.0
    signals = getattr(item, "signals", None) or {}
    sqi_avg = signals.get("avg_sqi", 0.0) if isinstance(signals, dict) else 0.0
    source_breakdown = getattr(item, "source_breakdown", None) or {}
    sources = []
    if isinstance(source_breakdown, dict):
        for src, cnt in source_breakdown.items():
            sources.append({"@type": "Organization", "name": src, "description": f"{cnt} references"})

    schema: dict[str, Any] = {
        "@context": "https://schema.org",
        "@type": "TechArticle",
        "headline": getattr(item, "title", ""),
        "description": (getattr(item, "description", None) or "")[:300],
        "author": {"@type": "Person", "name": author_name},
        "keywords": ", ".join(tags[:10]),
        "inLanguage": "en",
        "proficiencyLevel": getattr(item, "difficulty", None) or "",
    }

    dt = getattr(item, "created_at", None)
    if dt:
        try:
            schema["datePublished"] = dt.isoformat() if hasattr(dt, "isoformat") else str(dt)
        except (ValueError, TypeError, AttributeError):
            pass
    updated = getattr(item, "updated_at", None)
    if updated:
        schema["dateModified"] = str(updated)

    ds = getattr(item, "date_str", None)
    if ds:
        schema["datePublished"] = ds

    if page_path:
        schema["mainEntityOfPage"] = {"@type": "WebPage", "@id": f"{site_url}/{page_path}"}
    elif hasattr(item, "slug") and item.slug:
        schema["mainEntityOfPage"] = {"@type": "WebPage", "@id": f"{site_url}/{item.slug}/"}

    sqi_display = sqi_avg if sqi_avg > 0 else sqi_val
    if sqi_display > 0:
        schema["sqi"] = round(sqi_display, 3)
        schema["signalQualityIndex"] = round(sqi_display, 3)

    pillar = getattr(item, "pillar", None)
    if pillar:
        schema["about"] = {"@type": "Thing", "name": pillar}

    if sources:
        schema["citation"] = sources

    enriched = getattr(item, "enriched", False)
    if enriched:
        schema["semanticEnrichment"] = "completed"
        en_at = getattr(item, "enriched_at", None)
        if en_at:
            schema["semanticEnrichmentDate"] = str(en_at)

    return schema


def _dummy(title="", category="post", body_html="", description=""):
    return type(
        "obj",
        (object,),
        {
            "title": title,
            "language": "en",
            "category": category,
            "slug": "",
            "body_html": body_html,
            "description": description,
            "created_at": None,
            "updated_at": None,
            "tags": [],
            "pillar": "",
            "difficulty": "",
            "date_str": "",
            "thumbnail_svg": "",
            "og_svg": "",
            "signals": {},
            "source_breakdown": {},
            "quality_metrics": {},
            "bloom_questions": [],
            "flashcards": [],
            "trending_html": "",
            "analysis_html": "",
            "cross_pillar_html": "",
            "quality_flags": [],
            "knowledge_category": "",
            "author": "AcaciaFund",
            "sqi": 0.0,
            "enriched": False,
            "enriched_at": None,
        },
    )
