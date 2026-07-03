"""Page generation helpers for AcaciaFund build pipeline.

This module contains functions for generating individual pages (research, learn, knowledge)
from registry data. It's designed to be imported and used by build.py.
"""

import json
from collections import defaultdict
from typing import Any

from jinja2 import Environment

from config import (
    OUTPUT_DIR,
    STATIC_DST_DIR,
)
from core.visuals import generate_og_image, generate_thumbnail_svg


def get_topic_icons(tags: list[str]) -> list[str]:
    """Map article tags to resolved SVG path data, returning up to 3 matches."""
    if not tags:
        return []
    lower_tags = {t.lower() for t in tags}
    matched: list[str] = []
    seen: set[str] = set()

    # Import TOPIC_ICONS locally to avoid circular import
    from core.visuals import SUBTOPIC_CATEGORIES, TOPIC_ICONS

    for tag in lower_tags:
        if tag in TOPIC_ICONS and tag not in seen:
            from core.visuals import resolve_topic_icon

            path = resolve_topic_icon(tag)
            if path:
                matched.append(path)
                seen.add(tag)
                if len(matched) >= 3:
                    break
    if len(matched) < 3:
        for subs in SUBTOPIC_CATEGORIES.values():
            for key, keywords in subs.items():
                if key in seen:
                    continue
                if lower_tags & keywords:
                    from core.visuals import resolve_topic_icon

                    path = resolve_topic_icon(key)
                    if path:
                        matched.append(path)
                        seen.add(key)
                        if len(matched) >= 3:
                            break
    return matched


# ─────────────────────────────────────────────
# 1. PAGE GENERATION HELPERS
# ─────────────────────────────────────────────


def render_template(env: Environment, template_name: str, **kw) -> str:
    """Render a Jinja2 template with the given context."""
    return env.get_template(template_name).render(**kw)


def extract_headings(html: str) -> tuple[str, list[dict]]:
    """Extract headings from HTML and return cleaned HTML with TOC items."""
    import re

    toc_items: list[dict] = []
    pattern = r"<h(?P<level>[23])[^>]*>(?P<content>.*?)</h\1>"

    def replace_heading(match) -> str:
        level = int(match.group("level"))
        content = match.group("content")
        text = re.sub(r"<[^>]+>", "", content).strip()
        slug = re.sub(r"[^a-z0-9]+", "-", text.lower())
        slug = re.sub(r"-+", "-", slug).strip("-")

        toc_items.append({"level": level, "text": text, "id": slug})

        return f'<h{level} id="{slug}">{content}</h{level}>'

    cleaned = re.sub(pattern, replace_heading, html)
    return cleaned, toc_items


def find_related(posts: list, current: Any, max_items: int = 3) -> list:
    """Find related posts based on tag overlap."""
    current_tags = set(getattr(current, "tags", []) or [])
    if not current_tags:
        return []

    scored: list[tuple[Any, int]] = []
    current_slug = getattr(current, "slug", "")

    for post in posts:
        if getattr(post, "slug", "") == current_slug:
            continue
        post_tags = set(getattr(post, "tags", []) or [])
        overlap = current_tags & post_tags
        if overlap:
            scored.append((post, len(overlap)))

    scored.sort(key=lambda x: x[1], reverse=True)
    return [post for post, _ in scored[:max_items]]


def reading_time_minutes(html_or_text: str) -> int:
    """Calculate reading time in minutes based on word count."""
    import re

    text = re.sub(r"<[^>]+>", " ", html_or_text)
    words = len(text.split())
    return max(1, words // 200)


def sanitize_text(html: str, strip_emoji: bool = True) -> str:
    """Sanitize HTML text."""
    import re

    if strip_emoji:
        html = re.sub(r"[\U00010000-\U0010ffff]", "", html)
    return html.strip()


def sanitize_domain_breakdown(html: str) -> str:
    """Sanitize domain breakdown section."""
    import re

    return re.sub(
        r'<div[^>]*class="[^"]*domain-breakdown[^"]*"[^>]*>.*?</div>', "", html, flags=re.DOTALL
    )


def generate_sqi_badge(sqi: float) -> str:
    """Generate SQI badge HTML."""
    if sqi >= 0.8:
        return '<span class="sqi-badge high">High</span>'
    elif sqi >= 0.6:
        return '<span class="sqi-badge medium">Medium</span>'
    else:
        return '<span class="sqi-badge low">Low</span>'


def resolve_card_image(raw_path: str, site_url: str) -> str:
    """Resolve card image path to URL."""
    if not raw_path:
        return ""

    if raw_path.startswith("/"):
        return f"{site_url}{raw_path}"
    return f"{site_url}/{raw_path}"


def get_layer(url_path: str) -> str:
    """Determine layer from URL path."""
    if "/learn/" in url_path:
        return "learn"
    elif "/knowledge/" in url_path:
        return "knowledge"
    elif "/aml/" in url_path or "/stock/" in url_path or "/data-engineering/" in url_path:
        return "research"
    return "research"


# ─────────────────────────────────────────────
# 1b. ADDITIONAL HELPERS (from build.py)
# ─────────────────────────────────────────────


def layer_indicator_html(content_type: str, pillar: str = "") -> str:
    """Generate layer indicator HTML."""
    layer_names = {"research": "Research", "learn": "Learn", "knowledge": "Knowledge"}
    layer_emojis = {"research": "●", "learn": "◎", "knowledge": "●"}
    layer_name = layer_names.get(content_type, "Content")
    layer_emoji = layer_emojis.get(content_type, "●")
    pillar_text = f" - {pillar}" if pillar else ""
    return f'<span class="layer-indicator">{layer_emoji} {layer_name}{pillar_text}</span>'


def generate_article_fingerprint(
    slug: str, title: str, pillar: str, content_type: str, tags: list
) -> str:
    """Generate a visual fingerprint for an article."""
    import hashlib

    hash_input = f"{slug}:{title}:{pillar}:{content_type}:{','.join(sorted(tags or []))}"
    return hashlib.md5(hash_input.encode()).hexdigest()[:12]


def thumbnail_key(title: str) -> str:
    """Generate thumbnail key from title."""
    import hashlib

    return hashlib.md5(title.encode()).hexdigest()[:12]


# ─────────────────────────────────────────────
# 2. PAGE GENERATORS
# ─────────────────────────────────────────────


def generate_knowledge_page(
    item: Any,
    env: Environment,
    research_items: list,
    learn_items: list,
    quality_scores: dict,
    trend_detection: dict,
    source_verification: dict,
    source_synthesis: dict,
    site_url: str,
    pillar_config: dict,
    pillar_emojis: dict,
    pillar_names: dict,
    layer_icons: dict,
    build_hash: str,
    year: int,
) -> str:
    """Generate a single knowledge page."""

    # Prepare content
    body = item.body_html
    body, toc_items = extract_headings(body)
    body = sanitize_domain_breakdown(body)
    body = sanitize_text(body, strip_emoji=False)
    item.description = sanitize_text(item.description, strip_emoji=False)

    # Category info
    kcat = pillar_config.get(item.knowledge_category, {})
    if kcat:
        kcat["slug"] = item.knowledge_category

    # Related content
    related_research = find_related(research_items, item, 3)
    related_learn = find_related(learn_items, item, 3)

    # Visuals
    visual_fingerprint = generate_article_fingerprint(
        item.slug, item.title, item.pillar or "", "knowledge", item.tags
    )
    layer_badge = layer_indicator_html("knowledge", item.pillar or "")

    thumb_key_val = thumbnail_key(item.title)
    og_key = f"og_{thumb_key_val}"

    # Layer subtext
    layer_sub = (
        item.knowledge_category.replace("_", " ").title()
        if item.knowledge_category
        else item.pillar or ""
    )

    # Quality metrics
    quality_metrics = quality_scores.get(item.slug, {})
    quality_score = quality_metrics.get("quality_score", 0)
    quality_badge = generate_sqi_badge(quality_score)

    # Quiz data
    k_quiz_json = ""
    if item.bloom_questions:
        k_quiz_data: dict[str, list] = {"questions": []}
        for bq in item.bloom_questions[:10]:
            if isinstance(bq, dict) and "question" in bq:
                qtype = bq.get("type", "mc")
                opts = bq.get("options", [])
                raw = bq.get("answer") if "answer" in bq else None
                if raw is None:
                    correct_val = bq.get("correct", "")
                    raw = (
                        opts.index(correct_val)
                        if isinstance(correct_val, str) and correct_val and correct_val in opts
                        else 0
                    )
                entry = {"q": bq["question"], "options": opts, "a": raw, "type": qtype}
                if qtype == "open-ended":
                    entry["answer_text"] = bq.get("correct", opts[raw] if opts else "")
                k_quiz_data["questions"].append(entry)
        if k_quiz_data["questions"]:
            k_quiz_json = json.dumps(k_quiz_data, ensure_ascii=False)

    # Trend detection
    trend_info = trend_detection.get(item.slug, {})
    trend_strength = trend_info.get("trend_strength", 0)
    adoption_level = trend_info.get("adoption_level", "mainstream")
    impact_level = trend_info.get("impact_level", "low")
    trend_categories = trend_info.get("trend_categories", "")

    # Source verification
    source_info = source_verification.get(item.slug, {})
    source_verified = source_info.get("verified", False)
    source_evidence = source_info.get("evidence", [])

    # Render page
    page_path = f"/knowledge/{item.slug}/"
    html = render_template(
        env,
        "knowledge.j2",
        content=item,
        page_path=page_path,
        toc_items=toc_items,
        kcat=kcat,
        related_research=related_research,
        related_learn=related_learn,
        visual_fingerprint=visual_fingerprint,
        layer_badge=layer_badge,
        thumbnail_base=f"{site_url}/static/images",
        thumbnail_key=thumb_key_val,
        og_image_url=f"{site_url}/static/images/og_{og_key}.svg",
        quiz_json=k_quiz_json,
        quality_score=quality_score,
        quality_badge=quality_badge,
        source_verified=source_verified,
        source_evidence=source_evidence,
        quality_metrics=quality_metrics,
        trend_strength=trend_strength,
        adoption_level=adoption_level,
        impact_level=impact_level,
        trend_categories=trend_categories,
        source_synthesis=source_synthesis.get(item.slug, []),
        is_index=False,
        page_type="knowledge",
        layer="knowledge",
        layer_icon=layer_icons["knowledge"],
        layer_sub=layer_sub,
        build_hash=build_hash,
        year=year,
        site_url=site_url,
        pillar_config=pillar_config,
        pillar_emojis=pillar_emojis,
        pillar_names=pillar_names,
    )

    # Write page
    slug = item.slug
    if "/" in slug:
        out_dir = OUTPUT_DIR / slug
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / "index.html"
    else:
        out_file = OUTPUT_DIR / f"{slug}.html"

    out_file.write_text(html, encoding="utf-8")

    # Write thumbnails and OG images
    out_static = STATIC_DST_DIR / "images"
    out_static.mkdir(parents=True, exist_ok=True)
    pillar_k = item.pillar or "aml"
    scores_k: dict[str, Any] = {}
    feat_k = item.featured_image or ""
    icons_k = get_topic_icons(item.tags) if not feat_k else []

    svg_k = generate_thumbnail_svg(
        item.title,
        pillar_k,
        scores_k,
        width=600,
        height=340,
        featured_image_url=feat_k,
        layer="knowledge",
        fallback_icons=icons_k,
    )
    (out_static / f"thumb_{thumb_key_val}.svg").write_text(svg_k, encoding="utf-8")

    og_svg = generate_og_image(
        item.title,
        pillar_k,
        scores_k,
        featured_image_url=feat_k,
        layer="knowledge",
        fallback_icons=icons_k,
    )
    (out_static / f"og_{og_key}.svg").write_text(og_svg, encoding="utf-8")

    return str(out_file.relative_to(OUTPUT_DIR))


def generate_learn_page(
    item: Any,
    env: Environment,
    research_items: list,
    pillar_config: dict,
    pillar_emojis: dict,
    pillar_names: dict,
    layer_icons: dict,
    site_url: str,
    build_hash: str,
    year: int,
) -> str:
    """Generate a single learn page."""
    # Prepare content
    body = item.body_html
    body, toc_items = extract_headings(body)
    body = sanitize_text(body, strip_emoji=False)
    item.description = sanitize_text(item.description, strip_emoji=False)

    # Visuals
    visual_fingerprint = generate_article_fingerprint(
        item.slug, item.title, item.pillar or "", "learn", item.tags
    )
    layer_badge = layer_indicator_html("learn", item.pillar or "")

    thumb_key_val = thumbnail_key(item.title)
    og_key = f"og_{thumb_key_val}"

    # Layer subtext
    layer_sub = item.difficulty.replace("_", " ").title() if item.difficulty else item.pillar or ""

    # Render page
    page_path = f"/learn/{item.slug}/"
    html = render_template(
        env,
        "learn.j2",
        content=item,
        page_path=page_path,
        toc_items=toc_items,
        visual_fingerprint=visual_fingerprint,
        layer_badge=layer_badge,
        thumbnail_base=f"{site_url}/static/images",
        thumbnail_key=thumb_key_val,
        og_image_url=f"{site_url}/static/images/og_{og_key}.svg",
        layer_icon=layer_icons["learn"],
        layer_sub=layer_sub,
        build_hash=build_hash,
        year=year,
        site_url=site_url,
        pillar_config=pillar_config,
        pillar_emojis=pillar_emojis,
        pillar_names=pillar_names,
    )

    # Write page
    slug = item.slug
    if "/" in slug:
        out_dir = OUTPUT_DIR / "learn" / slug
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / "index.html"
    else:
        out_file = OUTPUT_DIR / "learn" / f"{slug}.html"

    out_file.write_text(html, encoding="utf-8")

    # Write thumbnails and OG images
    out_static = STATIC_DST_DIR / "images"
    out_static.mkdir(parents=True, exist_ok=True)
    pillar_l = item.pillar or "aml"
    scores_l: dict[str, float] = {}
    feat_l = item.featured_image or ""
    icons_l = get_topic_icons(item.tags) if not feat_l else []

    svg_l = generate_thumbnail_svg(
        item.title,
        pillar_l,
        scores_l,
        width=600,
        height=340,
        featured_image_url=feat_l,
        layer="learn",
        fallback_icons=icons_l,
    )
    (out_static / f"thumb_{thumb_key_val}.svg").write_text(svg_l, encoding="utf-8")

    og_svg = generate_og_image(
        item.title,
        pillar_l,
        scores_l,
        featured_image_url=feat_l,
        layer="learn",
        fallback_icons=icons_l,
    )
    (out_static / f"og_{og_key}.svg").write_text(og_svg, encoding="utf-8")

    return str(out_file.relative_to(OUTPUT_DIR))


def generate_research_page(
    item: Any,
    env: Environment,
    pillar_config: dict,
    pillar_emojis: dict,
    pillar_names: dict,
    layer_icons: dict,
    site_url: str,
    build_hash: str,
    year: int,
) -> str:
    """Generate a single research page."""
    # Prepare content
    body = item.body_html
    body, toc_items = extract_headings(body)
    body = sanitize_text(body, strip_emoji=False)
    item.description = sanitize_text(item.description, strip_emoji=False)

    # Visuals
    visual_fingerprint = generate_article_fingerprint(
        item.slug, item.title, item.pillar or "", "research", item.tags
    )
    layer_badge = layer_indicator_html("research", item.pillar or "")

    thumb_key_val = thumbnail_key(item.title)
    og_key = f"og_{thumb_key_val}"

    # Layer subtext
    layer_sub = item.pillar or ""

    # Render page
    page_path = f"/{item.slug}/"
    html = render_template(
        env,
        "blog_post.j2",
        content=item,
        page_path=page_path,
        toc_items=toc_items,
        visual_fingerprint=visual_fingerprint,
        layer_badge=layer_badge,
        thumbnail_base=f"{site_url}/static/images",
        thumbnail_key=thumb_key_val,
        og_image_url=f"{site_url}/static/images/og_{og_key}.svg",
        layer_icon=layer_icons["research"],
        layer_sub=layer_sub,
        build_hash=build_hash,
        year=year,
        site_url=site_url,
        pillar_config=pillar_config,
        pillar_emojis=pillar_emojis,
        pillar_names=pillar_names,
    )

    # Write page
    slug = item.slug
    out_dir = OUTPUT_DIR / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "index.html"

    out_file.write_text(html, encoding="utf-8")

    # Write thumbnails and OG images
    out_static = STATIC_DST_DIR / "images"
    out_static.mkdir(parents=True, exist_ok=True)
    pillar_r = item.pillar or "aml"
    scores_r: dict[str, float] = {}
    feat_r = item.featured_image or ""
    icons_r = get_topic_icons(item.tags) if not feat_r else []

    svg_r = generate_thumbnail_svg(
        item.title,
        pillar_r,
        scores_r,
        width=600,
        height=340,
        featured_image_url=feat_r,
        layer="research",
        fallback_icons=icons_r,
    )
    (out_static / f"thumb_{thumb_key_val}.svg").write_text(svg_r, encoding="utf-8")

    og_svg = generate_og_image(
        item.title,
        pillar_r,
        scores_r,
        featured_image_url=feat_r,
        layer="research",
        fallback_icons=icons_r,
    )
    (out_static / f"og_{og_key}.svg").write_text(og_svg, encoding="utf-8")

    return str(out_file.relative_to(OUTPUT_DIR))


# ─────────────────────────────────────────────
# 3. INDEX GENERATORS
# ─────────────────────────────────────────────


def generate_knowledge_index(
    knowledge_items: list,
    env: Environment,
    pillar_config: dict,
    pillar_emojis: dict,
    pillar_names: dict,
    layer_icons: dict,
    site_url: str,
    build_hash: str,
    year: int,
) -> str:
    """Generate knowledge index page."""
    # Group by category
    grouped: dict[str, list] = defaultdict(list)
    for item in knowledge_items:
        cat = item.knowledge_category or "other"
        grouped[cat].append(item)

    # Render page
    html = render_template(
        env,
        "knowledge_index.j2",
        knowledge_items=knowledge_items,
        grouped=dict(grouped),
        pillar_config=pillar_config,
        pillar_emojis=pillar_emojis,
        pillar_names=pillar_names,
        layer_icon=layer_icons["knowledge"],
        build_hash=build_hash,
        year=year,
        site_url=site_url,
    )

    # Write page
    out_file = OUTPUT_DIR / "knowledge" / "index.html"
    out_file.write_text(html, encoding="utf-8")

    return str(out_file.relative_to(OUTPUT_DIR))


def generate_learn_index(
    learn_items: list,
    env: Environment,
    pillar_config: dict,
    pillar_emojis: dict,
    pillar_names: dict,
    layer_icons: dict,
    site_url: str,
    build_hash: str,
    year: int,
) -> str:
    """Generate learn index page."""
    # Group by difficulty
    grouped: dict[str, list] = defaultdict(list)
    for item in learn_items:
        diff = item.difficulty or "beginner"
        grouped[diff].append(item)

    # Render page
    html = render_template(
        env,
        "learn_index.j2",
        learn_items=learn_items,
        grouped=dict(grouped),
        pillar_config=pillar_config,
        pillar_emojis=pillar_emojis,
        pillar_names=pillar_names,
        layer_icon=layer_icons["learn"],
        build_hash=build_hash,
        year=year,
        site_url=site_url,
    )

    # Write page
    out_file = OUTPUT_DIR / "learn" / "index.html"
    out_file.write_text(html, encoding="utf-8")

    return str(out_file.relative_to(OUTPUT_DIR))


def generate_research_index(
    research_items: list,
    env: Environment,
    pillar_config: dict,
    pillar_emojis: dict,
    pillar_names: dict,
    layer_icons: dict,
    site_url: str,
    build_hash: str,
    year: int,
) -> str:
    """Generate research index page."""
    # Group by pillar
    grouped: dict[str, list] = defaultdict(list)
    for item in research_items:
        pillar = item.pillar or "aml"
        grouped[pillar].append(item)

    # Render page
    html = render_template(
        env,
        "category_index.j2",
        research_items=research_items,
        grouped=dict(grouped),
        pillar_config=pillar_config,
        pillar_emojis=pillar_emojis,
        pillar_names=pillar_names,
        layer_icon=layer_icons["research"],
        build_hash=build_hash,
        year=year,
        site_url=site_url,
    )

    # Write page
    out_file = OUTPUT_DIR / "research" / "index.html"
    out_file.write_text(html, encoding="utf-8")

    return str(out_file.relative_to(OUTPUT_DIR))
