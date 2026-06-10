#!/usr/bin/env python3.13
"""
Build script for AcaciaFund: converts registry.json to static HTML using Jinja2 templates.
3-category taxonomy: research | learn | knowledge
"""
import hashlib
import json
import os
import re
import shutil
import time
import unicodedata
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape
from urllib.parse import quote as urlquote

from schemas import RegistryData
from core.visuals import generate_thumbnail_svg, generate_og_image, TOPIC_ICONS, SUBTOPIC_CATEGORIES
from core.images import generate_fallback_svg

from seed_learn import CURATED_RELATIONS, PREREQUISITES as LEARN_PREREQUISITES
from config import (
    PROJECT_ROOT, SITE_URL, SITE_NAME, SITE_DESCRIPTION, PLAUSIBLE_DOMAIN,
    REGISTRY_PATH, TEMPLATE_DIR, OUTPUT_DIR,
    STATIC_DST_DIR, PIPELINE_STATIC_DIR, CONTENT_DIR,
    SQI_THRESHOLD_MIN, SQI_BADGE_HIGH, SQI_BADGE_MED, SQI_DEFAULT,
    INTEREST_SQI_WEIGHT, INTEREST_RECENCY_WEIGHT, INTEREST_RECENCY_DAYS,
)

def get_topic_icons(tags: list[str]) -> list[str]:
    """Map article tags to TOPIC_ICONS SVG path data, returning up to 3 matches."""
    if not tags:
        return []
    lower_tags = {t.lower() for t in tags}
    matched = []
    seen = set()
    for tag in lower_tags:
        if tag in TOPIC_ICONS and tag not in seen:
            matched.append(TOPIC_ICONS[tag])
            seen.add(tag)
            if len(matched) >= 3:
                break
    if len(matched) < 3:
        for subs in SUBTOPIC_CATEGORIES.values():
            for key, keywords in subs.items():
                if key in seen:
                    continue
                if lower_tags & keywords:
                    if key in TOPIC_ICONS:
                        matched.append(TOPIC_ICONS[key])
                        seen.add(key)
                        if len(matched) >= 3:
                            break
            if len(matched) >= 3:
                break
    if len(matched) < 3:
        for tag in lower_tags:
            for tkey in TOPIC_ICONS:
                if tkey in seen:
                    continue
                if tkey in tag or tag in tkey:
                    matched.append(TOPIC_ICONS[tkey])
                    seen.add(tkey)
                    if len(matched) >= 3:
                        break
            if len(matched) >= 3:
                break
    return matched


PILLAR_CONFIG = {
    "aml": {
        "label": "AML", "emoji": "🛡️", "color": "slate",
        "bg": "from-slate-900 to-slate-800", "accent": "amber",
        "text_color": "text-slate-900", "badge_color": "bg-amber-100 text-amber-800",
        "heading": "Anti-Money Laundering",
        "description": "Financial crime, compliance, regulation, and risk management.",
    },
    "stock": {
        "label": "Markets", "emoji": "📈", "color": "green",
        "bg": "from-green-900 to-green-800", "accent": "green",
        "text_color": "text-green-900", "badge_color": "bg-green-100 text-green-800",
        "heading": "Markets & Industry",
        "description": "Semiconductors, supply chains, AI industry, manufacturing.",
    },
    "data-engineering": {
        "label": "Data Engineering", "emoji": "⚙️", "color": "indigo",
        "bg": "from-indigo-900 to-indigo-800", "accent": "indigo",
        "text_color": "text-indigo-900", "badge_color": "bg-indigo-100 text-indigo-800",
        "heading": "Data Engineering & Infrastructure",
        "description": "Data pipelines, orchestration, quality engineering, streaming, storage, and analytics infrastructure.",
    },
}
PILLAR_EMOJIS = {"aml": "🛡️", "stock": "📈", "data-engineering": "⚙️"}
PILLAR_NAMES = {"aml": "AML", "stock": "Markets", "data-engineering": "Data Engineering"}
DIFFICULTY_ORDER = {"beginner": 0, "intermediate": 1, "advanced": 2}

KNOWLEDGE_CATEGORIES = {
    "platform": {
        "label": "Platform", "icon": "⚙️", "color": "#6366f1", "bg_color": "#6366f1",
        "description": "About AcaciaFund — mission, team, contact, and site operations.",
    },
    "guide": {
        "label": "Guides", "icon": "🧭", "color": "#22c55e", "bg_color": "#22c55e",
        "description": "Methodology, taxonomy, and how-to guides for using the platform.",
    },
    "reference": {
        "label": "Reference", "icon": "📖", "color": "#d97706", "bg_color": "#d97706",
        "description": "Glossaries, tool landscapes, and technical terminology across all pillars.",
    },
    "architecture": {
        "label": "Architecture", "icon": "🔗", "color": "#a855f7", "bg_color": "#a855f7",
        "description": "System design, pipeline architecture, and DataOps implementation details.",
    },
}


def add_lazy_loading(html: str) -> str:
    return re.sub(r'<img(?![^>]*loading=)', '<img loading="lazy" decoding="async"', html)


def slug_to_path(slug: str) -> str:
    return f"{slug}/index.html" if "/" in slug else f"{slug}.html"


def canonical_path(slug_or_path: str) -> str:
    """Normalize a path for canonical URLs: strip /index.html, enforce trailing slash."""
    path = slug_or_path.replace("/index.html", "/").replace(".html", "/")
    if not path.endswith("/"):
        path += "/"
    return path


def slug_to_url(slug: str) -> str:
    return f"{SITE_URL}/{canonical_path(slug_to_path(slug))}"


def group_by_pillar(content_list: list) -> dict[str, list]:
    groups: dict[str, list] = defaultdict(list)
    for c in content_list:
        p = c.pillar
        if not p:
            continue
        groups[p].append(c)
    for g in groups.values():
        g.sort(key=lambda x: x.created_at or datetime.min, reverse=True)
    return dict(groups)


HEADING_RE = re.compile(r'<h([23])([^>]*)>(.*?)</h\1>', re.IGNORECASE | re.DOTALL)


def extract_headings(html: str) -> tuple[str, list[dict]]:
    toc = []
    id_counts: dict[str, int] = {}
    def _repl(m):
        tag = m.group(1)
        inner = m.group(3)
        text = re.sub(r'<[^>]+>', '', inner).strip()
        base_id = re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-') or "section"
        if base_id in id_counts:
            id_counts[base_id] += 1
            id_str = f"{base_id}-{id_counts[base_id]}"
        else:
            id_counts[base_id] = 0
            id_str = base_id
        toc.append({"id": id_str, "text": text, "tag": f"h{tag}"})
        return f'<h{tag} id="{id_str}">{inner}</h{tag}>'
    html = HEADING_RE.sub(_repl, html)
    return html, toc


def find_related(posts: list, current: object, max_items: int = 3) -> list:
    """Score relatedness by pillar match (40%), tag overlap (40%), curated relations (20%).

    Curated relations (from current.curated_relations) always appear first
    when they match a post slug in the candidate pool.
    """
    current_tags = set(t.lower() for t in current.tags)
    current_pillar = current.pillar or ""
    curated_slugs = {r.get("slug", "") for r in (current.curated_relations or [])}

    scored: list[tuple[float, object]] = []
    seen_slugs: set[str] = set()

    # Phase 1: Curated relations (always included if post exists in pool)
    for r in current.curated_relations or []:
        rslug = r.get("slug", "")
        if not rslug:
            continue
        for p in posts:
            if p.slug == rslug and p.slug != current.slug:
                scored.append((2.0, p))
                seen_slugs.add(p.slug)
                break

    # Phase 2: Algorithmic scoring for remaining candidates
    for p in posts:
        if p.slug == current.slug or p.slug in seen_slugs:
            continue
        pillar_match = 1.0 if p.pillar and p.pillar == current_pillar else 0.0
        tag_overlap = len(current_tags & set(t.lower() for t in p.tags))
        tag_score = min(tag_overlap / max(len(current_tags), 1), 1.0)
        score = pillar_match * 0.4 + tag_score * 0.4
        if score > 0:
            scored.append((score, p))
    scored.sort(key=lambda x: -x[0])
    return [p for _, p in scored[:max_items]]


def reading_time_minutes(html_or_text: str) -> int:
    text = re.sub(r'<[^>]+>', '', html_or_text)
    words = len(text.strip().split())
    code_blocks = len(re.findall(r'<pre><code>.*?</code></pre>', html_or_text, re.DOTALL))
    code_penalty_sec = code_blocks * 30
    minutes = (words / 150) + (code_penalty_sec / 60)
    return max(2, round(minutes)) if words > 100 else max(1, round(minutes))


def generate_sqi_badge(sqi: float) -> str:
    color = "#22c55e" if sqi >= SQI_BADGE_HIGH else "#d97706" if sqi >= SQI_BADGE_MED else "#ef4444"
    w = 160
    bar_w = int(min(1.0, max(0, sqi)) * w)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="20" viewBox="0 0 {w} 20">'
        f'<rect width="{w}" height="8" y="6" rx="4" fill="#e2e8f0"/>'
        f'<rect width="{bar_w}" height="8" y="6" rx="4" fill="{color}"/>'
        f'<circle cx="{max(8, bar_w)}" cy="10" r="6" fill="{color}"/>'
        f'<text x="{w + 6}" y="14" fill="#64748b" font-size="11" font-family="system-ui,sans-serif">{sqi:.3f}</text>'
        f'</svg>'
    )


def thumbnail_key(title: str) -> str:
    return hashlib.md5(title.encode()).hexdigest()[:12]


CJK_RE = re.compile(r'[\u4e00-\u9fff\u3400-\u4dbf\uff00-\uffef]')
EMOJI_RE = re.compile(r'[\U0001F300-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF\u2600-\u27BF\u2B50\U0001F1E0-\U0001F1FF]')


MERMAID_PLACEHOLDER = "@@MERMAID_"
_mermaid_counter = 0

def sanitize_text(html: str, strip_emoji: bool = True) -> str:
    global _mermaid_counter
    html = unicodedata.normalize('NFKC', html)
    html = CJK_RE.sub('', html)
    if strip_emoji:
        html = EMOJI_RE.sub('', html)
    # Protect mermaid div content from space-collapsing (need indent for mindmap)
    global _mermaid_counter
    mermaid_map = {}
    def _save_mermaid(m):
        global _mermaid_counter
        key = f"{MERMAID_PLACEHOLDER}{_mermaid_counter}_"
        _mermaid_counter += 1
        mermaid_map[key] = m.group(0)
        return key
    html = re.sub(r'(<div class="mermaid"[^>]*>)(.*?)(</div>)', _save_mermaid, html, flags=re.DOTALL)
    html = re.sub(r'  +', ' ', html)
    html = re.sub(r'>\s+<', '><', html)
    for key, original in mermaid_map.items():
        html = html.replace(key, original)
    return html


DOMAIN_BREAKDOWN_RE = re.compile(
    r'<li>[^<]*?([A-Za-z]+)\s*:\s*(\d+)%\s*of sources\s*</li>',
    re.IGNORECASE,
)


def sanitize_domain_breakdown(html: str) -> str:
    """Normalize domain breakdown percentages so they sum to exactly 100."""
    matches = list(DOMAIN_BREAKDOWN_RE.finditer(html))
    if not matches:
        return html
    total_pct = sum(int(m.group(2)) for m in matches)
    if total_pct <= 100:
        return html
    rescaled = []
    for m in matches:
        domain = m.group(1)
        orig = int(m.group(2))
        capped = max(1, round(orig * 100 / total_pct))
        rescaled.append((domain, capped))
    diff = sum(r[1] for r in rescaled) - 100
    if diff != 0:
        idx = max(range(len(rescaled)), key=lambda i: rescaled[i][1])
        d, v = rescaled[idx]
        rescaled[idx] = (d, max(1, v - diff))
    for m, (domain, capped) in zip(matches, rescaled):
        html = html.replace(m.group(0), f'<li>{domain}: {capped}% of sources</li>', 1)
    return html


def inject_section_images(body_html: str, section_images: list[dict],
                           article: dict | None = None) -> str:
    """Insert section-level images into body_html after matching <h2> headings.

    Tier 1: Editorial manifest images (already resolved by fetch pipeline)
    Tier 2: Auto-fetched images from registry
    Tier 3: Inline SVG fallback generated from article + section context

    Matches by section_index (positional: 0 = first <h2>, 1 = second, etc.)
    """
    h2_pattern = re.compile(r'(<h2[^>]*>.*?</h2>)', re.IGNORECASE | re.DOTALL)
    parts = h2_pattern.split(body_html)
    if not parts:
        return body_html

    img_map: dict[int, dict] = {}
    if section_images:
        for si in section_images:
            idx = si.get("section_index")
            if idx is not None:
                img_map[idx] = si

    result: list[str] = [parts[0]]

    for i in range(1, len(parts), 2):
        h2_tag = parts[i]
        content = parts[i + 1] if i + 1 < len(parts) else ""
        section_idx = (i - 1) // 2
        result.append(h2_tag)

        entry = img_map.get(section_idx)

        if entry:
            url = entry.get("image_url", "")
            credit = entry.get("image_credit", "")
            alt_ = entry.get("image_alt", "")
            w = entry.get("width", 1200)
            h = entry.get("height", 675)
            style_class = "section-image--full" if section_idx % 2 == 0 else "section-image--contained"
            figure_style = "background:var(--color-bg);border:1px solid var(--color-border)"
            f = [
                f'<figure class="section-image {style_class} my-6 rounded-lg overflow-hidden"',
                f' style="{figure_style}">',
                f'<img src="{url}" alt="{alt_}" width="{w}" height="{h}"',
                ' loading="lazy" decoding="async"',
                ' class="w-full h-auto object-cover">',
            ]
            if credit:
                f.append(
                    '<figcaption class="px-3 py-1.5 text-xs"'
                    ' style="color:var(--color-text-muted);border-top:1px solid var(--color-border)">'
                    f'{credit}</figcaption>'
                )
            f.append("</figure>")
            result.append("".join(f))
        elif article:
            # Tier 3: generate inline SVG fallback
            section = {
                "section_index": section_idx,
                "heading": strip_html_tag(h2_tag),
            }
            try:
                svg = generate_fallback_svg(section, article)
                result.append(
                    f'<figure class="section-image section-image--full section-fallback my-6 rounded-lg overflow-hidden"'
                    f' style="background:var(--color-bg);border:1px solid var(--color-border)">'
                    f'{svg}</figure>'
                )
            except Exception:
                pass

        result.append(content)

    return "".join(result)


def strip_html_tag(tag: str) -> str:
    m = re.search(r'>([^<]+)<', tag)
    return m.group(1).strip() if m else ""


def is_future_post(post) -> bool:
    return bool(post.created_at and post.created_at > datetime.now(timezone.utc))


# ── Visual fingerprint: unique ident for every article ─────
PILLAR_FINGERPRINT_COLORS = {
    "aml": "#c97d3e", "stock": "#3a7d5c", "data-engineering": "#6366f1",
    "": "#6b7280",
}

LAYER_SYMBOLS = {
    "research": ("path", '<path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" fill="none" stroke="currentColor" stroke-width="1.5"/>'),
    "learn": ("path", '<path d="M4 19.5A2.5 2.5 0 016.5 17H20" fill="none" stroke="currentColor" stroke-width="1.5"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 014 19.5v-15A2.5 2.5 0 016.5 2z" fill="none" stroke="currentColor" stroke-width="1.5"/>'),
    "knowledge": ("circle", '<circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" stroke-width="1.5"/><path d="M12 6v6l4 2" fill="none" stroke="currentColor" stroke-width="1.5"/>'),
}

LAYER_LABELS = {"research": "Research", "learn": "Learn", "knowledge": "Knowledge"}
LAYER_ICONS = {"research": "\u25c7", "learn": "\u25c9", "knowledge": "\u25ce"}


def get_layer(url_path: str) -> str:
    if url_path.startswith("learn") or url_path.startswith("learn/"):
        return "learn"
    if url_path.startswith("knowledge") or url_path.startswith("knowledge/"):
        return "knowledge"
    return "research"


def generate_article_fingerprint(slug: str, title: str, pillar: str, content_type: str, tags: list) -> str:
    """Generate a unique SVG ident for an article — a mini tartan-like pattern.

    The fingerprint is derived from:
      - Pillar → base color
      - Content type → pattern style (bars/dots/diagonals)
      - Title hash → pattern permutation
      - Tags → number of columns
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
                    bars.append(f'<circle cx="{cx}" cy="{ry + 6}" r="{bar_h // 4}" fill="{base_color}" opacity="{opacity}"/>')
                elif content_type == "knowledge":
                    bars.append(f'<line x1="{cx - 3}" y1="{ry}" x2="{cx + 3}" y2="{ry + 12}" stroke="{base_color}" stroke-width="1.5" opacity="{opacity}"/>')
                else:
                    bars.append(f'<rect x="{cx - 2}" y="{ry}" width="4" height="{bar_h}" rx="1" fill="{base_color}" opacity="{opacity}"/>')

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 32" width="120" height="32" aria-hidden="true">'
        f'<rect width="120" height="32" rx="2" fill="{base_color}" opacity="0.08"/>'
        f'{"".join(bars)}'
        f'</svg>'
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
        f'{label}'
        f'</span>'
    )


def interest_score(post, now: datetime) -> float:
    sqi = post.signals.get("avg_sqi", 0.0) if post.signals else 0.0
    age_days = (now - (post.created_at or now)).days if post.created_at else 365
    age_days = max(0, age_days)
    recency = max(0.1, 1.0 - age_days / INTEREST_RECENCY_DAYS)
    return sqi * INTEREST_SQI_WEIGHT + recency * INTEREST_RECENCY_WEIGHT


def main():
    start_time = time.time()
    print("Starting AcaciaFund generator...")

    if not REGISTRY_PATH.exists():
        print(f"Error: {REGISTRY_PATH} not found.")
        return 1

    # Archive previous registry before loading (versioning)
    archive_dir = PROJECT_ROOT / ".registry-archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    if REGISTRY_PATH.exists():
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        archive_path = archive_dir / f"registry_{ts}.json"
        shutil.copy2(REGISTRY_PATH, archive_path)
        # Keep only last 20 archives
        archives = sorted(archive_dir.glob("registry_*.json"), reverse=True)
        for old in archives[20:]:
            old.unlink()
        print(f"  registry archived: {archive_path.name}")

    try:
        with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
            registry_data = json.load(f)
        registry = RegistryData(**registry_data)
    except Exception as e:
        print(f"Error loading registry: {e}")
        return 1

    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    STATIC_DST_DIR.mkdir(parents=True, exist_ok=True)

    if PIPELINE_STATIC_DIR.exists():
        for item in PIPELINE_STATIC_DIR.rglob("*"):
            if item.is_file():
                rel = item.relative_to(PIPELINE_STATIC_DIR)
                dest = STATIC_DST_DIR / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, dest)
    env = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=select_autoescape(["html", "xml"]),
    )
    env.filters["reading_time"] = reading_time_minutes
    env.filters["urlencode"] = lambda s: urlquote(s or '', safe='')

    now = datetime.now(timezone.utc)
    year = now.year
    registry_bytes = REGISTRY_PATH.read_bytes() if REGISTRY_PATH.exists() else b""
    # Include CSS file hashes in build_hash so CSS changes bust CDN cache
    css_hasher = hashlib.md5()
    css_hasher.update(registry_bytes)
    for css_file in sorted(Path("static/css").glob("*.css")):
        css_hasher.update(css_file.read_bytes())
    build_hash = css_hasher.hexdigest()[:12]
    all_content = registry.content

    research_items = [c for c in all_content if c.content_type == "research"]
    learn_items = [c for c in all_content if c.content_type == "learn"]
    knowledge_items = [c for c in all_content if c.content_type == "knowledge"]

    pillar_groups = group_by_pillar(research_items)

    BLOOM_NAMES = {1: "Remember", 2: "Understand", 3: "Apply", 4: "Analyse", 5: "Evaluate", 6: "Create"}

    ctx_base = {
        "build_hash": build_hash,
        "year": year,
        "site_url": SITE_URL,
        "plausible_domain": PLAUSIBLE_DOMAIN,
        "pillar_config": PILLAR_CONFIG,
        "pillar_emojis": PILLAR_EMOJIS,
        "pillar_names": PILLAR_NAMES,
        "site_description": SITE_DESCRIPTION,
    }

    def render_template(template_name, **kw):
        return env.get_template(template_name).render(**kw)

    # --- KNOWLEDGE PAGES ---
    for item in knowledge_items:
        slug = item.slug
        page_path = canonical_path(slug_to_path(slug))
        if "/" in slug:
            out_dir = OUTPUT_DIR / slug
            out_dir.mkdir(parents=True, exist_ok=True)
            out_file = out_dir / "index.html"
        else:
            out_file = OUTPUT_DIR / f"{slug}.html"

        body = add_lazy_loading(item.body_html)
        body, toc_items = extract_headings(body)
        body = re.sub(r'<h2[^>]*>\s*' + re.escape(item.title.strip()) + r'\s*</h2>\s*', '', body, count=1)
        body = sanitize_domain_breakdown(body)
        body = sanitize_text(body, strip_emoji=False)
        item.description = sanitize_text(item.description, strip_emoji=False)
        item.body_html = body

        kcat = KNOWLEDGE_CATEGORIES.get(item.knowledge_category, {})
        if kcat:
            kcat["slug"] = item.knowledge_category

        related_research = find_related(research_items, item, 3)
        related_learn = find_related(learn_items, item, 3)
        visual_fingerprint = generate_article_fingerprint(item.slug, item.title, item.pillar or "", "knowledge", item.tags)
        layer_badge = layer_indicator_html("knowledge", item.pillar or "")

        thumb_key = hashlib.md5(item.title.encode()).hexdigest()[:12]
        og_key = hashlib.md5(f"og_{item.title}".encode()).hexdigest()[:12]
        thumb_base = f"{SITE_URL}/static/images"
        og_image_url = f"{SITE_URL}/static/images/og_{og_key}.svg"

        layer_sub = item.knowledge_category.replace("_", " ").title() if item.knowledge_category else item.pillar or ""
        html = render_template("knowledge.j2",
            content=item, page_path=page_path,
            toc_items=toc_items, kcat=kcat,
            related_research=related_research,
            related_learn=related_learn,
            visual_fingerprint=visual_fingerprint, layer_badge=layer_badge,
            thumbnail_base=thumb_base, thumbnail_key=thumbnail_key,
            og_image_url=og_image_url,
            is_index=False, page_type="knowledge", layer="knowledge",
            layer_icon=LAYER_ICONS["knowledge"], layer_sub=layer_sub, **ctx_base)
        out_file.write_text(html, encoding="utf-8")
        print(f"  knowledge: {out_file.relative_to(OUTPUT_DIR)}")

        # Write knowledge thumbnail SVGs + OG images (fractal engine)
        out_static = STATIC_DST_DIR / "images"
        out_static.mkdir(parents=True, exist_ok=True)
        pillar_k = item.pillar or "aml"
        scores_k = {"sqi": SQI_DEFAULT}
        feat_k = item.featured_image or ""
        icons_k = get_topic_icons(item.tags) if not feat_k else []
        svg_k = generate_thumbnail_svg(item.title, pillar_k, scores_k, width=600, height=340,
                                       featured_image_url=feat_k, layer="knowledge",
                                       fallback_icons=icons_k)
        (out_static / f"thumb_{thumb_key}.svg").write_text(svg_k, encoding="utf-8")
        og_svg = generate_og_image(item.title, pillar_k, scores_k,
                                   featured_image_url=feat_k, layer="knowledge",
                                   fallback_icons=icons_k)
        (out_static / f"og_{og_key}.svg").write_text(og_svg, encoding="utf-8")

    # --- KNOWLEDGE INDEX (sub-category grouped) ---
    knowledge_dir = OUTPUT_DIR / "knowledge"
    knowledge_dir.mkdir(parents=True, exist_ok=True)
    grouped: dict[str, list] = defaultdict(list)
    for k in knowledge_items:
        cat = k.knowledge_category or "reference"
        grouped[cat].append(k)
    for g in grouped.values():
        g.sort(key=lambda x: x.title or "")
    thumb_base = f"{SITE_URL}/static/images"
    html = render_template("knowledge_index.j2",
        content=_dummy("Knowledge Base", "knowledge",
                       description="AcaciaFund knowledge base: platform guides, methodology, reference glossaries, system architecture, and DataOps resources across all pillars."),
        items=knowledge_items, grouped=dict(grouped),
        categories=KNOWLEDGE_CATEGORIES,
        thumbnail_base=thumb_base, thumbnail_key=thumbnail_key,
        page_title="Knowledge Base",
        is_index=False, page_path="knowledge/",
        layer="knowledge", layer_icon=LAYER_ICONS["knowledge"],
        **ctx_base)
    (knowledge_dir / "index.html").write_text(html, encoding="utf-8")
    print("  category: knowledge/index.html")

    # --- LEARN PAGES ---
    BLOOM_ORDER = {"remember": 1, "understand": 2, "apply": 3, "analyze": 4, "evaluate": 5, "create": 6}
    # Apply curated relations and prerequisites from seed_learn.py
    for item in learn_items:
        slug = item.slug
        if slug in CURATED_RELATIONS:
            item.curated_relations = CURATED_RELATIONS[slug]
        if slug in LEARN_PREREQUISITES:
            item.prerequisites = LEARN_PREREQUISITES[slug]

    # Compute highest Bloom level from bloom_questions (must be done before article rendering)
    for l_item in learn_items:
        if l_item.bloom_questions:
            max_lvl = 0
            for q in l_item.bloom_questions:
                bl = q.get("bloom_level", "")
                lvl = BLOOM_ORDER.get(bl, 0)
                if lvl > max_lvl:
                    max_lvl = lvl
            l_item.highest_bloom = max_lvl
        else:
            l_item.highest_bloom = 0

    learn_lessons = sorted(
        [li for li in learn_items if li.slug != "learn"],
        key=lambda x: (DIFFICULTY_ORDER.get(x.difficulty or "beginner", 0), x.pillar or "", x.title or ""),
    )
    for i, item in enumerate(learn_items):
        # Determine prev/next only among actual lessons (exclude meta "learn" page)
        li = None
        for j, lli in enumerate(learn_lessons):
            if lli.slug == item.slug:
                li = j
                break
        if li is not None:
            prev_lesson = learn_lessons[li - 1] if li > 0 else None
            next_lesson = learn_lessons[li + 1] if li + 1 < len(learn_lessons) else None
        else:
            prev_lesson = None
            next_lesson = None
        slug = item.slug
        page_path = canonical_path(slug_to_path(slug))
        if "/" in slug:
            out_dir = OUTPUT_DIR / slug
            out_dir.mkdir(parents=True, exist_ok=True)
            out_file = out_dir / "index.html"
        else:
            out_file = OUTPUT_DIR / f"{slug}.html"
        body = add_lazy_loading(item.body_html)
        body, toc_items = extract_headings(body)
        body = re.sub(r'<h2[^>]*>\s*' + re.escape(item.title.strip()) + r'\s*</h2>\s*', '', body, count=1)
        body = sanitize_domain_breakdown(body)
        body = sanitize_text(body, strip_emoji=False)
        body = inject_section_images(body, item.section_images,
                                       article={"pillar": item.pillar, "title": item.title, "slug": item.slug})
        item.description = sanitize_text(item.description, strip_emoji=False)
        item.body_html = body


        pillar = item.pillar or ""
        pconf = PILLAR_CONFIG.get(pillar) if pillar else None
        related_research = find_related(research_items, item, 3)
        related_knowledge = find_related(knowledge_items, item, 3)
        visual_fingerprint = generate_article_fingerprint(item.slug, item.title, pillar, "learn", item.tags)
        layer_badge = layer_indicator_html("learn", pillar)
        thumb_key = hashlib.md5(item.title.encode()).hexdigest()[:12]
        og_key = hashlib.md5(f"og_{item.title}".encode()).hexdigest()[:12]
        thumb_base = f"{SITE_URL}/static/images"
        og_image_url = f"{SITE_URL}/static/images/og_{og_key}.svg"

        # Serialize quiz data for learning_hub.js
        quiz_json = ""
        if item.bloom_questions:
            quiz_data = {"questions": []}
            for bq in item.bloom_questions[:10]:
                if isinstance(bq, dict) and "question" in bq:
                    opts = bq.get("options", [])
                    answer = bq.get("answer", 0)
                    quiz_data["questions"].append({"q": bq["question"], "options": opts, "a": answer})
            if quiz_data["questions"]:
                quiz_json = json.dumps(quiz_data, ensure_ascii=False)

        bl_name = BLOOM_NAMES.get(item.highest_bloom or 0, "")
        layer_sub = f"Level {item.highest_bloom}: {bl_name}" if bl_name else ""
        html = render_template("learn.j2",
            content=item, page_path=page_path,
            toc_items=toc_items, pconf=pconf,
            prev_lesson=prev_lesson, next_lesson=next_lesson,
            related_research=related_research,
            related_knowledge=related_knowledge,
            visual_fingerprint=visual_fingerprint, layer_badge=layer_badge,
            thumbnail_base=thumb_base, thumbnail_key=thumbnail_key,
            og_image_url=og_image_url, quiz_json=quiz_json,
            featured_image=item.featured_image,
            image_credit=item.image_credit,
            is_index=False, layer="learn",
            layer_icon=LAYER_ICONS["learn"], layer_sub=layer_sub, **ctx_base)
        out_file.write_text(html, encoding="utf-8")
        print(f"  learn: {out_file.relative_to(OUTPUT_DIR)}")

        # Write learn thumbnail SVGs + OG images (fractal engine)
        out_static = STATIC_DST_DIR / "images"
        out_static.mkdir(parents=True, exist_ok=True)
        pillar_l = item.pillar or "aml"
        scores_l = {"sqi": SQI_DEFAULT}
        feat_l = item.featured_image or ""
        icons_l = get_topic_icons(item.tags) if not feat_l else []
        svg_l = generate_thumbnail_svg(item.title, pillar_l, scores_l, width=600, height=340,
                                       featured_image_url=feat_l, layer="learn",
                                       fallback_icons=icons_l)
        (out_static / f"thumb_{thumb_key}.svg").write_text(svg_l, encoding="utf-8")
        og_svg = generate_og_image(item.title, pillar_l, scores_l,
                                   featured_image_url=feat_l, layer="learn",
                                   fallback_icons=icons_l)
        (out_static / f"og_{og_key}.svg").write_text(og_svg, encoding="utf-8")

    # --- LEARN INDEX (difficulty-grouped) ---
    learn_dir = OUTPUT_DIR / "learn"
    learn_dir.mkdir(parents=True, exist_ok=True)
    learn_grouped: dict[str, list] = defaultdict(list)
    for l_item in learn_items:
        diff = l_item.difficulty or "beginner"
        learn_grouped[diff.capitalize()].append(l_item)
    for g in learn_grouped.values():
        g.sort(key=lambda x: x.title or "")
    bloom_first_articles: dict[int, str] = {}
    for l_item in learn_items:
        bl = l_item.highest_bloom or 0
        if bl > 0 and bl not in bloom_first_articles:
            bloom_first_articles[bl] = l_item.slug
    thumb_base = f"{SITE_URL}/static/images"
    html = render_template("learn_index.j2",
        content=_dummy("Learning Hub", "learn",
                       description="Interactive lessons, tutorials, and quizzes on AML compliance, financial markets, science, and DataOps — powered by Bloom taxonomy."),
        items=learn_items, grouped=dict(learn_grouped),
        thumbnail_base=thumb_base, thumbnail_key=thumbnail_key,
        page_title="Learning Hub",
        is_index=False, page_path="learn/",
        layer="learn", layer_icon=LAYER_ICONS["learn"],
        bloom_first_articles=bloom_first_articles,
        **ctx_base)
    (learn_dir / "index.html").write_text(html, encoding="utf-8")
    print("  category: learn/index.html")

    # --- RESEARCH PAGES (blog posts) ---
    for i, item in enumerate(research_items):
        slug = item.slug
        page_path = canonical_path(slug_to_path(slug))
        if "/" in slug:
            out_dir = OUTPUT_DIR / slug
            out_dir.mkdir(parents=True, exist_ok=True)
            out_file = out_dir / "index.html"
        else:
            out_file = OUTPUT_DIR / f"{slug}.html"

        body = add_lazy_loading(item.body_html)
        body, toc_items = extract_headings(body)
        body = re.sub(r'<h2[^>]*>\s*' + re.escape(item.title.strip()) + r'\s*</h2>\s*', '', body, count=1)
        body = sanitize_domain_breakdown(body)
        body = sanitize_text(body, strip_emoji=True)
        body = inject_section_images(body, item.section_images,
                                       article={"pillar": item.pillar, "title": item.title, "slug": item.slug})
        item.description = sanitize_text(item.description, strip_emoji=True)

        prev_post = research_items[i + 1] if i + 1 < len(research_items) else None
        next_post = research_items[i - 1] if i > 0 else None
        pillar = item.pillar or "aml"
        related = find_related(research_items, item, 3)
        related_learn = find_related(learn_items, item, 3)
        visual_fingerprint = generate_article_fingerprint(item.slug, item.title, pillar, "research", item.tags)
        layer_badge = layer_indicator_html("research", pillar)

        pconf = PILLAR_CONFIG.get(pillar, PILLAR_CONFIG["aml"])
        sqi_svg = generate_sqi_badge(item.signals.get("avg_sqi", SQI_DEFAULT)) if item.signals else ""
        og_key = hashlib.md5(f"og_{item.title}".encode()).hexdigest()[:12]
        og_image_url = f"{SITE_URL}/static/images/og_{og_key}.svg"
        thumb_base = f"{SITE_URL}/static/images"

        html = render_template("blog_post.j2",
            content=item, page_path=page_path, page_body=body,
            prev_post=prev_post, next_post=next_post,
            pconf=pconf, sqi_svg=sqi_svg,
            og_image_url=og_image_url,
            thumbnail_base=thumb_base, thumbnail_key=thumbnail_key,
            toc_items=toc_items, related_posts=related,
            related_learn=related_learn,
            visual_fingerprint=visual_fingerprint, layer_badge=layer_badge,
            featured_image=item.featured_image,
            image_credit=item.image_credit,
            layer_sub=pconf["label"], **ctx_base)
        out_file.write_text(html, encoding="utf-8")
        print(f"  research: {out_file.relative_to(OUTPUT_DIR)}")

        # Write SVGs (fractal engine — thumbnail + OG image)
        out_static = STATIC_DST_DIR / "images"
        out_static.mkdir(parents=True, exist_ok=True)
        key = hashlib.md5(item.title.encode()).hexdigest()[:12]
        scores_r = item.signals or {"sqi": SQI_DEFAULT}
        if not isinstance(scores_r, dict):
            scores_r = {"sqi": SQI_DEFAULT}
        feat_r = item.featured_image or ""
        icons_r = get_topic_icons(item.tags) if not feat_r else []
        svg_r = generate_thumbnail_svg(item.title, pillar, scores_r, width=600, height=340,
                                       featured_image_url=feat_r, layer="research",
                                       fallback_icons=icons_r)
        (out_static / f"thumb_{key}.svg").write_text(svg_r, encoding="utf-8")
        og_svg = generate_og_image(item.title, pillar, scores_r,
                                   featured_image_url=feat_r, layer="research",
                                   fallback_icons=icons_r)
        (out_static / f"og_{og_key}.svg").write_text(og_svg, encoding="utf-8")

    # --- RESEARCH INDEX (/research/) ---
    research_dir = OUTPUT_DIR / "research"
    research_dir.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    scored = [(interest_score(p, now), p) for p in research_items]
    scored.sort(key=lambda x: -x[0])
    sorted_research = [p for _, p in scored]
    html = render_template("category_index.j2",
        content=_dummy("Research", "research",
                       description="Quality-scored research articles on AML, financial markets, and science. Automatically classified from HackerNews and arXiv using Bloom taxonomy."),
        category="research", items=sorted_research,
        page_title="Research",
        is_index=False, page_path="research/", **ctx_base)
    (research_dir / "index.html").write_text(html, encoding="utf-8")
    print("  category: research/index.html")

    # --- PILLAR SUB-PAGES ---
    for pillar in PILLAR_CONFIG:
        p_posts = pillar_groups.get(pillar, [])
        out_dir = OUTPUT_DIR / pillar
        out_dir.mkdir(parents=True, exist_ok=True)
        pconf = PILLAR_CONFIG.get(pillar, PILLAR_CONFIG["aml"])
        html = render_template("pillar_index.j2",
            content=_dummy(pconf['heading'], "index",
                           description=pconf.get("description", f"{pconf['label']} research articles — quality-scored and Bloom-classified.")),
            pillar=pillar, pconf=pconf,
            posts=p_posts, is_index=False, page_path=f"{pillar}/",
            page_title=pconf["heading"],
            layer_sub=pconf["label"],
            thumbnail_base=f"{SITE_URL}/static/images", thumbnail_key=thumbnail_key, **ctx_base)
        (out_dir / "index.html").write_text(html, encoding="utf-8")
        print(f"  pillar: {pillar}/index.html")

    # --- AML SIGNALS DASHBOARD ---
    aml_research = [p for p in research_items if p.pillar == "aml"]
    aml_learn = [l for l in learn_items if l.pillar == "aml"]
    tag_cloud: dict[str, int] = {}
    entity_cloud: dict[str, int] = {}
    source_totals: dict[str, int] = {}
    cross_pillar_links: dict[str, int] = {}
    timeline: dict[str, int] = {}
    for a in aml_research:
        for t in (a.tags or []):
            tag_cloud[t] = tag_cloud.get(t, 0) + 1
        signals = a.signals or {}
        for e in (signals.get("top_entities", []) or []):
            entity_cloud[e] = entity_cloud.get(e, 0) + 1
        sb = a.source_breakdown or {}
        for k, v in sb.items():
            source_totals[k] = source_totals.get(k, 0) + v
        cross = a.cross_pillar_html or ""
        if "stock" in cross.lower() or "markets" in cross.lower():
            cross_pillar_links["stock"] = cross_pillar_links.get("stock", 0) + 1
        if "science" in cross.lower():
            cross_pillar_links["science"] = cross_pillar_links.get("science", 0) + 1
        if "data-engineering" in cross.lower() or "data engineering" in cross.lower():
            cross_pillar_links["data-engineering"] = cross_pillar_links.get("data-engineering", 0) + 1
        if a.date_str:
            month = a.date_str[:7]
            timeline[month] = timeline.get(month, 0) + 1
    tag_sorted = sorted(tag_cloud.items(), key=lambda x: -x[1])
    entity_sorted = sorted(entity_cloud.items(), key=lambda x: -x[1])
    source_sorted = sorted(source_totals.items(), key=lambda x: -x[1])
    source_max = max((c for _, c in source_sorted), default=1)
    cp_sorted = sorted(cross_pillar_links.items(), key=lambda x: -x[1])
    tl_sorted = sorted(timeline.items())
    tl_max = max(timeline.values()) if timeline else 1
    avg_sqi = sum((a.signals or {}).get("avg_sqi", 0) or 0 for a in aml_research) / max(len(aml_research), 1)
    unique_tags = set()
    for a in aml_research:
        for t in (a.tags or []):
            unique_tags.add(t)
    unique_entities = set()
    for a in aml_research:
        for e in ((a.signals or {}).get("top_entities", []) or []):
            unique_entities.add(e)

    aml_signals_html = render_template("aml_signals.j2",
        content=_dummy("AML Signals Dashboard", "index",
                       description="Aggregated AML risk signals, entity profiles, and coverage metrics across AML articles."),
        aml_count=len(aml_research),
        avg_sqi=avg_sqi,
        unique_tags_count=len(unique_tags),
        unique_entities_count=len(unique_entities),
        tag_cloud=tag_sorted,
        entity_cloud=entity_sorted,
        source_totals=source_sorted,
        source_max=source_max,
        cross_pillar_summary=cp_sorted,
        timeline=tl_sorted,
        timeline_max=tl_max,
        recent_articles=sorted(aml_research, key=lambda x: x.date_str or "", reverse=True)[:10],
        learn_path=aml_learn,
        is_index=False, page_path="aml/signals/",
        page_title="AML Signals Dashboard",
        thumbnail_base=f"{SITE_URL}/static/images", thumbnail_key=thumbnail_key, **ctx_base)
    sig_dir = OUTPUT_DIR / "aml" / "signals"
    sig_dir.mkdir(parents=True, exist_ok=True)
    (sig_dir / "index.html").write_text(aml_signals_html, encoding="utf-8")
    print("  signals: aml/signals/index.html")

    # --- HOMEPAGE (filter future posts from featured/recent) ---
    published_research = [p for p in sorted_research if not is_future_post(p)]
    # Freshness cutoff: exclude articles older than 90 days from featured + recent
    ninety_days_ago = now - timedelta(days=90)
    fresh_posts = [p for p in published_research if not p.created_at or p.created_at >= ninety_days_ago]
    featured = fresh_posts[:3] if len(fresh_posts) >= 3 else published_research[:3]
    # Hero: highest-SQI article from last 7 days
    seven_days_ago = now - timedelta(days=7)
    recent_articles = [p for p in published_research if p.created_at and p.created_at >= seven_days_ago]
    hero_article = max(recent_articles, key=lambda x: (x.signals or {}).get("avg_sqi", 0)) if recent_articles else None
    home_og_key = hashlib.md5(b"AcaciaFund homepage").hexdigest()[:12]
    home_og_url = f"{SITE_URL}/static/images/og_{home_og_key}.svg"
    index_html = render_template("index.j2",
        content=_dummy("Research Synthesis & Learning", "index",
                       description="AcaciaFund — research synthesis & experimental learning platform. Automated classification of HackerNews + arXiv content using Bloom taxonomy."),
        is_index=True, page_path="",
        og_image_url=home_og_url,
        featured_posts=featured, recent_posts=fresh_posts[:12],
        learn_items=learn_items[:6], knowledge_items=knowledge_items[:6],
        hero_article=hero_article,
        thumbnail_base=f"{SITE_URL}/static/images", thumbnail_key=thumbnail_key, **ctx_base)
    (OUTPUT_DIR / "index.html").write_text(index_html, encoding="utf-8")
    # Write homepage OG image
    out_static = STATIC_DST_DIR / "images"
    out_static.mkdir(parents=True, exist_ok=True)
    home_og_svg = generate_og_image("AcaciaFund — Research Synthesis & Learning", "aml", {"sqi": 0.7})
    (out_static / f"og_{home_og_key}.svg").write_text(home_og_svg, encoding="utf-8")
    print("  index: index.html")

    # --- /contact/ redirect to /knowledge/contact/ ---
    contact_dir = OUTPUT_DIR / "contact"
    contact_dir.mkdir(parents=True, exist_ok=True)
    (contact_dir / "index.html").write_text(
        f'<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
        f'<title>Contact — AcaciaFund</title>'
        f'<meta http-equiv="refresh" content="0;url={SITE_URL}/knowledge/contact/">'
        f'<link rel="canonical" href="{SITE_URL}/knowledge/contact/">'
        f'</head><body><p><a href="{SITE_URL}/knowledge/contact/">Contact — AcaciaFund</a></p></body></html>',
        encoding="utf-8")
    print("  redirect: /contact/ → /knowledge/contact/")

    # --- /science/ redirect to /research/ ---
    science_dir = OUTPUT_DIR / "science"
    science_dir.mkdir(parents=True, exist_ok=True)
    (science_dir / "index.html").write_text(
        f'<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
        f'<title>Science — AcaciaFund</title>'
        f'<meta http-equiv="refresh" content="0;url={SITE_URL}/research/">'
        f'<link rel="canonical" href="{SITE_URL}/research/">'
        f'</head><body><p><a href="{SITE_URL}/research/">Research — AcaciaFund</a></p></body></html>',
        encoding="utf-8")
    print("  redirect: /science/ → /research/")

    # --- 404 ---
    _suggestions = sorted(all_content, key=lambda c: hashlib.md5(c.slug.encode()).hexdigest())[:3]
    html = render_template("404.j2",
        content=_dummy("Page Not Found — AcaciaFund", "error"),
        is_index=False, page_path="404.html", page_type="error",
        suggestions=_suggestions, **ctx_base)
    (OUTPUT_DIR / "404.html").write_text(html, encoding="utf-8")
    print("  error: 404.html")

    # --- TAG ARCHIVE PAGES ---
    tag_items: dict[str, list] = defaultdict(list)
    for c in all_content:
        for t in (c.tags or []):
            tag_items[t.lower().strip()].append(c)
    tags_dir = OUTPUT_DIR / "tags"
    tags_dir.mkdir(parents=True, exist_ok=True)
    for tag_slug, tag_posts in sorted(tag_items.items()):
        tag_slug_clean = re.sub(r'[^a-z0-9]+', '-', tag_slug).strip('-')
        if not tag_slug_clean:
            continue
        tag_posts.sort(key=lambda x: x.created_at or datetime.min, reverse=True)
        thin = len(tag_posts) < 3
        tag_out = tags_dir / tag_slug_clean / "index.html"
        tag_out.parent.mkdir(parents=True, exist_ok=True)
        html = render_template("tag_index.j2",
            content=_dummy(f"Tag: {tag_slug}", "tag"),
            tag=tag_slug, items=tag_posts,
            is_index=False, page_path=f"tags/{tag_slug_clean}/",
            robots_noindex=thin, **ctx_base)
        tag_out.write_text(html, encoding="utf-8")
    if tag_items:
        tag_out = tags_dir / "index.html"
        html = render_template("tag_index.j2",
            content=_dummy("Tags", "tag"),
            tag="", items=[], all_tags=sorted(tag_items.keys()),
            is_index=False, page_path="tags/", **ctx_base)
        tag_out.write_text(html, encoding="utf-8")
        print(f"  tags: {len(tag_items)} tag pages + index")

    # --- SEARCH INDEX ---
    search_index = []
    for c in all_content:
        search_index.append({
            "title": c.title,
            "description": (c.description or "")[:300],
            "slug": c.slug,
            "pillar": c.pillar or "",
            "content_type": c.content_type or "",
            "tags": c.tags or [],
            "date_str": c.date_str or "",
            "difficulty": c.difficulty or "",
        })
    (STATIC_DST_DIR / "search-index.json").write_text(
        json.dumps(search_index, ensure_ascii=False), encoding="utf-8")
    print("  search: search-index.json (" + str(len(search_index)) + " entries)")

    # --- SEARCH PAGE ---
    search_dir = OUTPUT_DIR / "search"
    search_dir.mkdir(parents=True, exist_ok=True)
    html = render_template("search.j2",
        content=_dummy("Search — AcaciaFund", "search"),
        is_index=False, page_path="search/", **ctx_base)
    (search_dir / "index.html").write_text(html, encoding="utf-8")
    print("  search: search/index.html")

    # --- FEED ---
    published_for_feed = [p for p in research_items if not is_future_post(p)]
    feed_candidates = [p.created_at for p in published_for_feed[:20] if p.created_at]
    feed_updated = max(feed_candidates).isoformat() if feed_candidates else now.isoformat()
    feed_items = []
    for post in published_for_feed[:20]:
        path = canonical_path(slug_to_path(post.slug))
        desc = (post.description or post.body_html[:200])[:300]
        post_updated = (post.created_at or now).isoformat()
        feed_items.append(f"""  <entry>
    <title>{post.title}</title>
    <link href="{SITE_URL}/{path}" rel="alternate" type="text/html"/>
    <id>{SITE_URL}/{path}</id>
    <updated>{post_updated}</updated>
    <summary>{desc}</summary>
  </entry>""")
    feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>AcaciaFund Research</title>
  <link href="{SITE_URL}/feed.xml" rel="self" type="application/atom+xml"/>
  <link href="{SITE_URL}/" rel="alternate" type="text/html"/>
  <id>{SITE_URL}/feed.xml</id>
  <updated>{feed_updated}</updated>
  <author><name>{SITE_NAME}</name></author>
{chr(10).join(feed_items)}
</feed>"""
    (OUTPUT_DIR / "feed.xml").write_text(feed, encoding="utf-8")
    print("  feed: feed.xml")

    # --- SITEMAP ---
    today = datetime.now(timezone.utc).date().isoformat()
    section_pages = list(pillar_groups) + ["research", "learn", "knowledge", "search"]
    tag_slugs = []
    for tag_slug in sorted(tag_items.keys()):
        slug_clean = re.sub(r'[^a-z0-9]+', '-', tag_slug).strip('-')
        if slug_clean:
            tag_slugs.append(slug_clean)
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    sm.append(f'  <url><loc>{SITE_URL}/</loc><lastmod>{today}</lastmod><changefreq>daily</changefreq><priority>1.0</priority></url>')
    sm.append(f'  <url><loc>{SITE_URL}/tags/</loc><lastmod>{today}</lastmod><changefreq>weekly</changefreq><priority>0.4</priority></url>')
    for c in all_content:
        if is_future_post(c):
            continue
        lastmod = c.updated_at.date().isoformat() if c.updated_at else (c.created_at.date().isoformat() if c.created_at else today)
        sm.append(f'  <url><loc>{slug_to_url(c.slug)}</loc><lastmod>{lastmod}</lastmod><changefreq>monthly</changefreq><priority>0.6</priority></url>')
    for p in section_pages:
        sm.append(f'  <url><loc>{SITE_URL}/{p}/</loc><lastmod>{today}</lastmod><changefreq>weekly</changefreq><priority>0.8</priority></url>')
    for slug_clean in tag_slugs:
        sm.append(f'  <url><loc>{SITE_URL}/tags/{slug_clean}/</loc><lastmod>{today}</lastmod><changefreq>weekly</changefreq><priority>0.3</priority></url>')
    sm.append("</urlset>")
    (OUTPUT_DIR / "sitemap.xml").write_text("\n".join(sm), encoding="utf-8")

    # --- ROBOTS ---
    (OUTPUT_DIR / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n", encoding="utf-8")

    # --- HEADERS ---
    (OUTPUT_DIR / "_headers").write_text("""/*
  X-Content-Type-Options: nosniff
  X-Frame-Options: DENY
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: camera=(), microphone=(), geolocation=()

/static/*
  Cache-Control: public, max-age=31536000, immutable

/*.html
  Cache-Control: public, max-age=3600

/feed.xml
  Cache-Control: public, max-age=3600
  Content-Type: application/atom+xml; charset=utf-8

/sitemap.xml
  Content-Type: application/xml; charset=utf-8
""", encoding="utf-8")

    total = len(list(OUTPUT_DIR.rglob("*.html")))
    duration = time.time() - start_time
    print(f"Generation complete. Total pages: {total} ({duration:.2f}s)")

    # ── Build metrics (build-meta.json) ──
    sqi_values = [
        c.signals.get("avg_sqi", 0.0)
        for c in all_content
        if c.signals and isinstance(c.signals, dict) and "avg_sqi" in c.signals
    ]
    sqi_sorted = sorted(sqi_values) if sqi_values else [0.0]
    n_sqi = len(sqi_sorted)
    sqi_min = sqi_sorted[0] if n_sqi > 0 else 0.0
    sqi_max = sqi_sorted[-1] if n_sqi > 0 else 0.0
    sqi_avg = round(sum(sqi_sorted) / n_sqi, 3) if n_sqi > 0 else 0.0
    sqi_median = sqi_sorted[n_sqi // 2] if n_sqi > 0 else 0.0
    sqi_q1 = sqi_sorted[n_sqi // 4] if n_sqi > 3 else sqi_min
    sqi_q3 = sqi_sorted[3 * n_sqi // 4] if n_sqi > 3 else sqi_max

    # Source-type aggregation across all content
    source_counts: dict[str, int] = defaultdict(int)
    for c in all_content:
        if c.source_breakdown:
            for src, cnt in c.source_breakdown.items():
                source_counts[src] += cnt

    # Soft quality gate: flag low-SQI items without excluding them
    low_sqi_items = [
        {"slug": c.slug, "title": c.title[:80], "sqi": c.signals.get("avg_sqi", 0.0)}
        for c in all_content
        if c.signals and isinstance(c.signals, dict)
        and c.signals.get("avg_sqi", SQI_DEFAULT) < SQI_THRESHOLD_MIN
    ]
    low_sqi_items.sort(key=lambda x: x["sqi"])

    # Content type counts
    content_type_counts: dict[str, int] = defaultdict(int)
    for c in all_content:
        ct = c.content_type or "unknown"
        content_type_counts[ct] += 1

    build_meta = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "duration_seconds": round(duration, 2),
        "page_count": total,
        "registry_hash": build_hash,
        "sqi": {
            "min": round(sqi_min, 3),
            "max": round(sqi_max, 3),
            "avg": sqi_avg,
            "median": round(sqi_median, 3),
            "q1": round(sqi_q1, 3),
            "q3": round(sqi_q3, 3),
            "sample_count": n_sqi,
        },
        "sources": {
            "last_build": datetime.now(timezone.utc).isoformat(),
            "source_type_counts": dict(source_counts),
        },
        "content_counts": dict(content_type_counts),
        "quality": {
            "gate_min_sqi": SQI_THRESHOLD_MIN,
            "gate_passed": len(low_sqi_items) == 0,
            "low_sqi_count": len(low_sqi_items),
            "low_sqi_items": low_sqi_items,
        },
    }

    build_meta_path = OUTPUT_DIR / "build-meta.json"
    build_meta_path.write_text(
        json.dumps(build_meta, indent=2, default=str), encoding="utf-8"
    )
    print(f"  build-meta: build-meta.json ({build_meta_path.stat().st_size} bytes)")

    if low_sqi_items:
        log_text = "; ".join(f"{i['slug']} (SQI={i['sqi']})" for i in low_sqi_items)
        print(f"  quality gate: {len(low_sqi_items)} items below SQI {SQI_THRESHOLD_MIN}")
        print(f"    -> {log_text}")

    return 0


def _dummy(title="", category="post", body_html="", description=""):
    return type("obj", (object,), {
        "title": title, "language": "en", "category": category, "slug": "",
        "body_html": body_html, "description": description, "created_at": None,
        "updated_at": None, "tags": [], "pillar": "", "difficulty": "",
        "date_str": "", "thumbnail_svg": "", "og_svg": "", "signals": {},
        "source_breakdown": {}, "quality_metrics": {}, "bloom_questions": [],
        "flashcards": [], "trending_html": "", "analysis_html": "",
        "cross_pillar_html": "", "quality_flags": [], "knowledge_category": "",
    })


if __name__ == "__main__":
    exit(main())
