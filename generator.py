#!/usr/bin/env python3.13
"""
Generator for AcaciaFund: converts registry.json to static HTML using Jinja2 templates.
3-category taxonomy: research | learn | knowledge
"""
import hashlib
import json
import re
import shutil
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from schemas import RegistryData
from core.visuals import source_bar_svg, sparkline_svg, bloom_chart_svg, radar_svg, heatmap_svg, donut_svg, generate_thumbnail_svg, generate_og_image

REGISTRY_PATH = Path("registry.json")
TEMPLATE_DIR = Path("templates")
OUTPUT_DIR = Path("dist")
STATIC_SRC_DIR = Path("public")
STATIC_DST_DIR = OUTPUT_DIR / "static"
PIPELINE_STATIC_DIR = Path("static")
CONTENT_DIR = Path("content")
SITE_URL = "https://acaciafund.org"

PILLAR_CONFIG = {
    "aml": {
        "label": "AML", "emoji": "shield", "color": "slate",
        "bg": "from-slate-900 to-slate-800", "accent": "amber",
        "text_color": "text-slate-900", "badge_color": "bg-amber-100 text-amber-800",
        "heading": "Anti-Money Laundering",
        "description": "Financial crime, compliance, regulation, and risk management.",
    },
    "stock": {
        "label": "Markets", "emoji": "chart", "color": "green",
        "bg": "from-green-900 to-green-800", "accent": "green",
        "text_color": "text-green-900", "badge_color": "bg-green-100 text-green-800",
        "heading": "Markets & Industry",
        "description": "Semiconductors, supply chains, AI industry, manufacturing.",
    },
    "science": {
        "label": "Science", "emoji": "microscope", "color": "purple",
        "bg": "from-purple-900 to-purple-800", "accent": "purple",
        "text_color": "text-purple-900", "badge_color": "bg-purple-100 text-purple-800",
        "heading": "Science & Discovery",
        "description": "Biology, quantum, neuroscience, space, climate, complexity.",
    },
}
PILLAR_EMOJIS = {"aml": "shield", "stock": "chart", "science": "microscope"}
PILLAR_NAMES = {"aml": "AML", "stock": "Markets", "science": "Science"}

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


def slug_to_url(slug: str) -> str:
    return f"{SITE_URL}/{slug_to_path(slug)}"


def group_by_pillar(content_list: list) -> dict[str, list]:
    groups: dict[str, list] = defaultdict(list)
    for c in content_list:
        p = c.pillar or "aml"
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
    current_tags = set(t.lower() for t in current.tags)
    scored = []
    for p in posts:
        if p.slug == current.slug:
            continue
        overlap = len(current_tags & set(t.lower() for t in p.tags))
        if overlap > 0:
            scored.append((overlap, p))
    scored.sort(key=lambda x: -x[0])
    return [p for _, p in scored[:max_items]]


def reading_time_minutes(html_or_text: str) -> int:
    text = re.sub(r'<[^>]+>', '', html_or_text)
    words = len(text.strip().split())
    return max(1, (words + 99) // 200)


def generate_sqi_badge(sqi: float) -> str:
    color = "#22c55e" if sqi >= 0.6 else "#d97706" if sqi >= 0.35 else "#ef4444"
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


def interest_score(post, now: datetime) -> float:
    sqi = post.signals.get("avg_sqi", 0.0) if post.signals else 0.0
    age_days = (now - (post.created_at or now)).days if post.created_at else 365
    recency = max(0.1, 1.0 - age_days / 180)
    return sqi * 0.6 + recency * 0.4


def main():
    print("Starting AcaciaFund generator...")

    if not REGISTRY_PATH.exists():
        print(f"Error: {REGISTRY_PATH} not found.")
        return 1

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
    if STATIC_SRC_DIR.exists():
        for sub in {"images", "icons"}:
            src = STATIC_SRC_DIR / sub
            if src.exists():
                shutil.copytree(src, STATIC_DST_DIR / sub, dirs_exist_ok=True)

    env = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=select_autoescape(["html", "xml"]),
    )
    env.filters["reading_time"] = reading_time_minutes

    year = datetime.now(timezone.utc).year
    all_content = registry.content

    research_items = [c for c in all_content if c.content_type == "research"]
    learn_items = [c for c in all_content if c.content_type == "learn"]
    knowledge_items = [c for c in all_content if c.content_type == "knowledge"]

    pillar_groups = group_by_pillar(research_items)

    ctx_base = {
        "year": year,
        "site_url": SITE_URL,
        "plausible_domain": "",
        "pillar_config": PILLAR_CONFIG,
        "pillar_emojis": PILLAR_EMOJIS,
        "pillar_names": PILLAR_NAMES,
    }

    def render_template(template_name, **kw):
        return env.get_template(template_name).render(**kw)

    # --- KNOWLEDGE PAGES ---
    for item in knowledge_items:
        slug = item.slug
        page_path = slug_to_path(slug)
        if "/" in slug:
            out_dir = OUTPUT_DIR / slug
            out_dir.mkdir(parents=True, exist_ok=True)
            out_file = out_dir / "index.html"
        else:
            out_file = OUTPUT_DIR / f"{slug}.html"

        body = add_lazy_loading(item.body_html)
        body, toc_items = extract_headings(body)
        # Strip first h2 if it matches the article title (avoids duplicate heading)
        body = re.sub(r'<h2[^>]*>\s*' + re.escape(item.title.strip()) + r'\s*</h2>\s*', '', body, count=1)
        item.body_html = body

        kcat = KNOWLEDGE_CATEGORIES.get(item.knowledge_category, {})
        if kcat:
            kcat["slug"] = item.knowledge_category

        related_research = find_related(research_items, item, 3)
        related_learn = find_related(learn_items, item, 3)

        thumb_key = hashlib.md5(item.title.encode()).hexdigest()[:12]
        og_key = hashlib.md5(f"og_{item.title}".encode()).hexdigest()[:12]
        thumb_base = f"{SITE_URL}/static/images"
        og_image_url = f"{SITE_URL}/static/images/og_{og_key}.svg"

        html = render_template("knowledge.j2",
            content=item, page_path=page_path,
            toc_items=toc_items, kcat=kcat,
            related_research=related_research,
            related_learn=related_learn,
            thumbnail_base=thumb_base, thumbnail_key=thumbnail_key,
            og_image_url=og_image_url,
            is_index=False, page_type="knowledge", **ctx_base)
        out_file.write_text(html, encoding="utf-8")
        print(f"  knowledge: {out_file.relative_to(OUTPUT_DIR)}")

        # Write knowledge thumbnail SVGs + OG images (fractal engine)
        out_static = STATIC_DST_DIR / "images"
        out_static.mkdir(parents=True, exist_ok=True)
        pillar_k = item.pillar or "aml"
        scores_k = {"sqi": 0.5}
        svg_k = generate_thumbnail_svg(item.title, pillar_k, scores_k, width=600, height=340)
        (out_static / f"thumb_{thumb_key}.svg").write_text(svg_k, encoding="utf-8")
        og_svg = generate_og_image(item.title, pillar_k, scores_k)
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
        content=_dummy("Knowledge Base", "knowledge"),
        items=knowledge_items, grouped=dict(grouped),
        categories=KNOWLEDGE_CATEGORIES,
        thumbnail_base=thumb_base, thumbnail_key=thumbnail_key,
        is_index=False, page_path="knowledge/", **ctx_base)
    (knowledge_dir / "index.html").write_text(html, encoding="utf-8")
    print("  category: knowledge/index.html")

    # --- LEARN PAGES ---
    for item in learn_items:
        slug = item.slug
        page_path = slug_to_path(slug)
        if "/" in slug:
            out_dir = OUTPUT_DIR / slug
            out_dir.mkdir(parents=True, exist_ok=True)
            out_file = out_dir / "index.html"
        else:
            out_file = OUTPUT_DIR / f"{slug}.html"
        body = add_lazy_loading(item.body_html)
        body, toc_items = extract_headings(body)
        body = re.sub(r'<h2[^>]*>\s*' + re.escape(item.title.strip()) + r'\s*</h2>\s*', '', body, count=1)
        item.body_html = body

        pillar = item.pillar or ""
        pconf = PILLAR_CONFIG.get(pillar) if pillar else None
        related_research = find_related(research_items, item, 3)
        related_knowledge = find_related(knowledge_items, item, 3)
        thumb_key = hashlib.md5(item.title.encode()).hexdigest()[:12]
        og_key = hashlib.md5(f"og_{item.title}".encode()).hexdigest()[:12]
        thumb_base = f"{SITE_URL}/static/images"
        og_image_url = f"{SITE_URL}/static/images/og_{og_key}.svg"

        html = render_template("learn.j2",
            content=item, page_path=page_path,
            toc_items=toc_items, pconf=pconf,
            related_research=related_research,
            related_knowledge=related_knowledge,
            thumbnail_base=thumb_base, thumbnail_key=thumbnail_key,
            og_image_url=og_image_url,
            is_index=False, **ctx_base)
        out_file.write_text(html, encoding="utf-8")
        print(f"  learn: {out_file.relative_to(OUTPUT_DIR)}")

        # Write learn thumbnail SVGs + OG images (fractal engine)
        out_static = STATIC_DST_DIR / "images"
        out_static.mkdir(parents=True, exist_ok=True)
        pillar_l = item.pillar or "aml"
        scores_l = {"sqi": 0.5}
        svg_l = generate_thumbnail_svg(item.title, pillar_l, scores_l, width=600, height=340)
        (out_static / f"thumb_{thumb_key}.svg").write_text(svg_l, encoding="utf-8")
        og_svg = generate_og_image(item.title, pillar_l, scores_l)
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
    thumb_base = f"{SITE_URL}/static/images"
    html = render_template("learn_index.j2",
        content=_dummy("Learning Hub", "learn"),
        items=learn_items, grouped=dict(learn_grouped),
        thumbnail_base=thumb_base, thumbnail_key=thumbnail_key,
        is_index=False, page_path="learn/", **ctx_base)
    (learn_dir / "index.html").write_text(html, encoding="utf-8")
    print("  category: learn/index.html")

    # --- RESEARCH PAGES (blog posts) ---
    for i, item in enumerate(research_items):
        slug = item.slug
        page_path = slug_to_path(slug)
        if "/" in slug:
            out_dir = OUTPUT_DIR / slug
            out_dir.mkdir(parents=True, exist_ok=True)
            out_file = out_dir / "index.html"
        else:
            out_file = OUTPUT_DIR / f"{slug}.html"

        body = add_lazy_loading(item.body_html)
        body, toc_items = extract_headings(body)
        body = re.sub(r'<h2[^>]*>\s*' + re.escape(item.title.strip()) + r'\s*</h2>\s*', '', body, count=1)
        item.body_html = body

        prev_post = research_items[i + 1] if i + 1 < len(research_items) else None
        next_post = research_items[i - 1] if i > 0 else None
        related = find_related(research_items, item, 3)

        pillar = item.pillar or "aml"
        pconf = PILLAR_CONFIG.get(pillar, PILLAR_CONFIG["aml"])
        sqi_svg = generate_sqi_badge(item.signals.get("avg_sqi", 0.5)) if item.signals else ""
        og_key = hashlib.md5(f"og_{item.title}".encode()).hexdigest()[:12]
        og_image_url = f"{SITE_URL}/static/images/og_{og_key}.svg"
        thumb_base = f"{SITE_URL}/static/images"

        # Phase 2: Generate chart SVGs
        chart_source_bar = source_bar_svg(item.source_breakdown or {})
        chart_donut = donut_svg(item.source_breakdown or {})
        chart_bloom = bloom_chart_svg(item.bloom_questions or [])
        chart_radar = radar_svg(item.quality_metrics or {})
        sqi_trend = [0.3, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7]
        chart_sparkline = sparkline_svg(sqi_trend, color="#a855f7")
        qf = item.quality_flags or []
        chart_heatmap = heatmap_svg(
            [[1.0 if f in qf else 0.0 for f in ["validated", "diverse", "recent"]]]
            if qf else [[0.0, 0.0, 0.0]],
            row_labels=["Quality"],
            col_labels=["Validated", "Diverse", "Recent"],
        )

        html = render_template("blog_post.j2",
            content=item, page_path=page_path,
            prev_post=prev_post, next_post=next_post,
            pconf=pconf, sqi_svg=sqi_svg,
            og_image_url=og_image_url,
            thumbnail_base=thumb_base, thumbnail_key=thumbnail_key,
            toc_items=toc_items, related_posts=related,
            chart_source_bar=chart_source_bar,
            chart_donut=chart_donut,
            chart_bloom=chart_bloom,
            chart_radar=chart_radar,
            chart_sparkline=chart_sparkline,
            chart_heatmap=chart_heatmap,
            **ctx_base)
        out_file.write_text(html, encoding="utf-8")
        print(f"  research: {out_file.relative_to(OUTPUT_DIR)}")

        # Write SVGs (fractal engine — thumbnail + OG image)
        out_static = STATIC_DST_DIR / "images"
        out_static.mkdir(parents=True, exist_ok=True)
        key = hashlib.md5(item.title.encode()).hexdigest()[:12]
        scores_r = item.signals or {"sqi": 0.5}
        if not isinstance(scores_r, dict):
            scores_r = {"sqi": 0.5}
        svg_r = generate_thumbnail_svg(item.title, pillar, scores_r, width=600, height=340)
        (out_static / f"thumb_{key}.svg").write_text(svg_r, encoding="utf-8")
        og_svg = generate_og_image(item.title, pillar, scores_r)
        (out_static / f"og_{og_key}.svg").write_text(og_svg, encoding="utf-8")

    # --- RESEARCH INDEX (/research/) ---
    research_dir = OUTPUT_DIR / "research"
    research_dir.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    scored = [(interest_score(p, now), p) for p in research_items]
    scored.sort(key=lambda x: -x[0])
    sorted_research = [p for _, p in scored]
    html = render_template("category_index.j2", content=_dummy("Research", "research"),
                            category="research", items=sorted_research,
                            is_index=False, page_path="research/", **ctx_base)
    (research_dir / "index.html").write_text(html, encoding="utf-8")
    print("  category: research/index.html")

    # --- PILLAR SUB-PAGES ---
    for pillar, p_posts in pillar_groups.items():
        out_dir = OUTPUT_DIR / pillar
        out_dir.mkdir(parents=True, exist_ok=True)
        pconf = PILLAR_CONFIG.get(pillar, PILLAR_CONFIG["aml"])
        html = render_template("pillar_index.j2",
            content=_dummy(pconf['heading'], "index"), pillar=pillar, pconf=pconf,
            posts=p_posts, is_index=False, page_path=f"{pillar}/",
            thumbnail_base=f"{SITE_URL}/static/images", thumbnail_key=thumbnail_key, **ctx_base)
        (out_dir / "index.html").write_text(html, encoding="utf-8")
        print(f"  pillar: {pillar}/index.html")

    # --- HOMEPAGE ---
    featured = sorted_research[:3] if len(sorted_research) >= 3 else sorted_research
    index_html = render_template("index.j2",
        content=_dummy("AcaciaFund — Research Synthesis & Learning", "index"),
        is_index=True, page_path="",
        featured_posts=featured, recent_posts=sorted_research[:12],
        learn_items=learn_items[:6], knowledge_items=knowledge_items[:6],
        thumbnail_base=f"{SITE_URL}/static/images", thumbnail_key=thumbnail_key, **ctx_base)
    (OUTPUT_DIR / "index.html").write_text(index_html, encoding="utf-8")
    print("  index: index.html")

    # --- 404 ---
    _suggestions = sorted(all_content, key=lambda c: hashlib.md5(c.slug.encode()).hexdigest())[:3]
    html = render_template("404.j2",
        content=_dummy("Page Not Found — AcaciaFund", "error"),
        is_index=False, page_path="404.html", page_type="error",
        suggestions=_suggestions, **ctx_base)
    (OUTPUT_DIR / "404.html").write_text(html, encoding="utf-8")
    print("  error: 404.html")

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
    feed_items = []
    for post in research_items[:20]:
        path = slug_to_path(post.slug)
        desc = (post.description or post.body_html[:200])[:300]
        feed_items.append(f"""  <entry>
    <title>{post.title}</title>
    <link href="{SITE_URL}/{path}" rel="alternate" type="text/html"/>
    <id>{SITE_URL}/{path}</id>
    <updated>{(post.created_at or datetime.now(timezone.utc)).isoformat()}</updated>
    <summary>{desc}</summary>
  </entry>""")
    feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>AcaciaFund Research</title>
  <link href="{SITE_URL}/feed.xml" rel="self" type="application/atom+xml"/>
  <link href="{SITE_URL}/" rel="alternate" type="text/html"/>
  <id>{SITE_URL}/feed.xml</id>
  <updated>{datetime.now(timezone.utc).isoformat()}</updated>
  <author><name>AcaciaFund</name></author>
{chr(10).join(feed_items)}
</feed>"""
    (OUTPUT_DIR / "feed.xml").write_text(feed, encoding="utf-8")
    print("  feed: feed.xml")

    # --- SITEMAP ---
    urls = [f"{SITE_URL}/"]
    for c in all_content:
        urls.append(slug_to_url(c.slug))
    for p in list(pillar_groups) + ["research", "learn", "knowledge", "search"]:
        urls.append(f"{SITE_URL}/{p}/")
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for url in urls:
        sm.append(f"  <url><loc>{url}</loc></url>")
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
    print(f"Generation complete. Total pages: {total}")
    return 0


def _dummy(title="", category="post", body_html=""):
    return type("obj", (object,), {
        "title": title, "language": "en", "category": category, "slug": "",
        "body_html": body_html, "description": "", "created_at": None,
        "updated_at": None, "tags": [], "pillar": "", "difficulty": "",
        "date_str": "", "thumbnail_svg": "", "og_svg": "", "signals": {},
        "source_breakdown": {}, "quality_metrics": {}, "bloom_questions": [],
        "flashcards": [], "trending_html": "", "analysis_html": "",
        "cross_pillar_html": "", "quality_flags": [], "knowledge_category": "",
    })


if __name__ == "__main__":
    exit(main())
