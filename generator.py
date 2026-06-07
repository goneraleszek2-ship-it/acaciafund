#!/usr/bin/env python3.13
"""
Generator for AcaciaFund: converts registry.json to static HTML using Jinja2 templates.
Produces: index.html, blog posts, pillar indices, static pages, feed.xml, sitemap.xml, robots.txt, 404.html, _headers
"""
import hashlib
import json
import re
import shutil
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from jinja2 import Environment, FileSystemLoader, select_autoescape
import markdown2

from schemas import RegistryData, AcaciaContent

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
        "label": "AML",
        "emoji": "shield",
        "color": "slate",
        "bg": "from-slate-900 to-slate-800",
        "accent": "amber",
        "text_color": "text-slate-900",
        "badge_color": "bg-amber-100 text-amber-800",
        "heading": "Anti-Money Laundering",
        "description": "Financial crime, compliance, regulation, and risk management.",
    },
    "stock": {
        "label": "Markets",
        "emoji": "chart",
        "color": "green",
        "bg": "from-green-900 to-green-800",
        "accent": "green",
        "text_color": "text-green-900",
        "badge_color": "bg-green-100 text-green-800",
        "heading": "Markets & Industry",
        "description": "Semiconductors, supply chains, AI industry, manufacturing.",
    },
    "science": {
        "label": "Science",
        "emoji": "microscope",
        "color": "purple",
        "bg": "from-purple-900 to-purple-800",
        "accent": "purple",
        "text_color": "text-purple-900",
        "badge_color": "bg-purple-100 text-purple-800",
        "heading": "Science & Discovery",
        "description": "Biology, quantum, neuroscience, space, climate, complexity.",
    },
}

PILLAR_EMOJIS = {"aml": "shield", "stock": "chart", "science": "microscope"}
PILLAR_NAMES = {"aml": "AML", "stock": "Markets", "science": "Science"}


def add_lazy_loading(html: str) -> str:
    return re.sub(r'<img(?![^>]*loading=)', '<img loading="lazy" decoding="async"', html)


def slug_to_path(slug: str) -> str:
    return f"{slug}/index.html" if "/" in slug else f"{slug}.html"


def slug_to_url(slug: str) -> str:
    return f"{SITE_URL}/{slug_to_path(slug)}"


def extract_pillar_accent(pillar: str) -> str:
    return pillar if pillar in PILLAR_CONFIG else "aml"


def group_by_pillar(content_list: list[AcaciaContent]) -> dict[str, list[AcaciaContent]]:
    groups: dict[str, list[AcaciaContent]] = defaultdict(list)
    for c in content_list:
        p = c.pillar or c.category
        groups[p].append(c)
    for g in groups.values():
        g.sort(key=lambda x: x.created_at or datetime.min, reverse=True)
    return dict(groups)


def build_static_page_html(md_path: Path) -> str:
    try:
        raw = md_path.read_text(encoding="utf-8")
    except Exception:
        return ""
    if raw.startswith("---"):
        parts = raw.split("---", 2)
        if len(parts) >= 3:
            body = parts[2].strip()
        else:
            body = raw
    else:
        body = raw
    return markdown2.markdown(body, extras=["fenced-code-blocks", "tables"])


HEADING_RE = re.compile(r'<h([23])([^>]*)>(.*?)</h\1>', re.IGNORECASE | re.DOTALL)


def extract_headings(html: str) -> tuple[str, list[dict]]:
    """Add id anchors to h2/h3 and return TOC structure [{id, text, tag}]."""
    toc = []
    id_counts: dict[str, int] = {}

    def _repl(m):
        tag = m.group(1)
        inner = m.group(3)
        text = re.sub(r'<[^>]+>', '', inner).strip()
        base_id = re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-') or f"section"
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
    """Find posts sharing most tags with current, excluding current itself."""
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
        print(f"Copied pipeline static assets")

    if STATIC_SRC_DIR.exists():
        for sub in {"images", "icons"}:
            src = STATIC_SRC_DIR / sub
            if src.exists():
                shutil.copytree(src, STATIC_DST_DIR / sub, dirs_exist_ok=True)
        print(f"Copied legacy static assets")

    env = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=select_autoescape(["html", "xml"]),
    )
    env.filters["reading_time"] = reading_time_minutes

    year = datetime.now(timezone.utc).year
    all_content = registry.content
    posts = [c for c in all_content if c.category == "blog"]
    lessons = [c for c in all_content if c.category in ("learn", "lesson")]
    pillar_groups = group_by_pillar(posts)
    latest_post = posts[0] if posts else None
    pillar_latest = {p: g[0] for p, g in pillar_groups.items() if g}

    ctx_base = {
        "year": year,
        "site_url": SITE_URL,
        "plausible_domain": "",
        "pillar_config": PILLAR_CONFIG,
        "pillar_emojis": PILLAR_EMOJIS,
        "pillar_names": PILLAR_NAMES,
    }

    # --- STATIC PAGES: about, research, scholarship, contact ---
    static_page_map = {
        "about": "en/about/index.md",
        "research": "en/research/index.md",
        "scholarship": "en/scholarship/index.md",
        "contact": "contact/index.md",
    }

    for page_name, rel_path in static_page_map.items():
        page_path = CONTENT_DIR / rel_path
        if not page_path.exists():
            continue
        body = build_static_page_html(page_path)
        dummy = _make_dummy_content(
            title=page_name.capitalize(),
            slug=page_name,
            body_html=body,
            category="page",
        )
        html = _render_page(env, dummy, page_path=f"{page_name}.html", **ctx_base)
        (OUTPUT_DIR / f"{page_name}.html").write_text(html, encoding="utf-8")
        print(f"Generated: {page_name}.html")

    # --- LEARNING PAGES ---
    for lesson in lessons:
        slug = lesson.slug
        page_path = slug_to_path(slug)
        if "/" in slug:
            out_dir = OUTPUT_DIR / slug
            out_dir.mkdir(parents=True, exist_ok=True)
            out_file = out_dir / "index.html"
        else:
            out_file = OUTPUT_DIR / f"{slug}.html"
        body = add_lazy_loading(lesson.body_html)
        ctx = dict(ctx_base, content=lesson, page_path=page_path,
                    prev_post=None, next_post=None)
        html = env.get_template("layout.j2").render(content=lesson, is_index=False,
                                                     page_path=page_path, **ctx_base)
        out_file.write_text(html, encoding="utf-8")
        print(f"Generated: {out_file.relative_to(OUTPUT_DIR)}")

    # --- BLOG POSTS ---
    for i, post in enumerate(posts):
        slug = post.slug
        page_path = slug_to_path(slug)
        if "/" in slug:
            out_dir = OUTPUT_DIR / slug
            out_dir.mkdir(parents=True, exist_ok=True)
            out_file = out_dir / "index.html"
        else:
            out_file = OUTPUT_DIR / f"{slug}.html"

        body = add_lazy_loading(post.body_html)
        body, toc_items = extract_headings(body)
        post.body_html = body

        prev_post = posts[i + 1] if i + 1 < len(posts) else None
        next_post = posts[i - 1] if i > 0 else None
        related = find_related(posts, post, 3)

        html = _render_blog_post(env, post, page_path, prev_post, next_post, related, toc_items, ctx_base)
        out_file.write_text(html, encoding="utf-8")
        print(f"Generated: {out_file.relative_to(OUTPUT_DIR)}")

        # Write SVG thumbnails/OG images
        out_static = STATIC_DST_DIR / "images"
        out_static.mkdir(parents=True, exist_ok=True)
        if post.thumbnail_svg:
            key = hashlib.md5(post.title.encode()).hexdigest()[:12]
            (out_static / f"thumb_{key}.svg").write_text(post.thumbnail_svg, encoding="utf-8")
        if post.og_svg:
            key = hashlib.md5(f"og_{post.title}".encode()).hexdigest()[:12]
            (out_static / f"og_{key}.svg").write_text(post.og_svg, encoding="utf-8")

    # --- PILLAR INDEX PAGES ---
    for pillar, p_posts in pillar_groups.items():
        out_dir = OUTPUT_DIR / pillar
        out_dir.mkdir(parents=True, exist_ok=True)
        pconf = PILLAR_CONFIG.get(pillar, PILLAR_CONFIG["aml"])
        dummy = _make_dummy_content(
            title=pconf['heading'],
            slug=pillar,
            body_html="",
            category="index",
        )
        html = _render_pillar_index(env, dummy, pillar, pconf, p_posts, ctx_base)
        (out_dir / "index.html").write_text(html, encoding="utf-8")
        print(f"Generated: {pillar}/index.html")

    # --- INDEX PAGE ---
    now = datetime.now(timezone.utc)
    scored = [(interest_score(p, now), p) for p in posts]
    scored.sort(key=lambda x: -x[0])
    index_posts = [p for _, p in scored[:12]]
    featured = index_posts[:3] if len(index_posts) >= 3 else index_posts
    index_html = _render_index(env, index_posts, featured, lessons[:6], ctx_base)
    (OUTPUT_DIR / "index.html").write_text(index_html, encoding="utf-8")
    print("Generated: index.html")

    # --- 404 PAGE ---
    dummy_404 = _make_dummy_content(
        title="Page Not Found",
        slug="404",
        body_html='<p>The page you requested does not exist. <a href="/">Return home</a></p>',
        category="error",
    )
    html_404 = env.get_template("layout.j2").render(
        content=dummy_404, is_index=False, page_path="404.html", **ctx_base
    )
    (OUTPUT_DIR / "404.html").write_text(html_404, encoding="utf-8")
    print("Generated: 404.html")

    # --- FEED ---
    feed_items = []
    for post in posts[:20]:
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
  <title>AcaciaFund Blog</title>
  <link href="{SITE_URL}/feed.xml" rel="self" type="application/atom+xml"/>
  <link href="{SITE_URL}/" rel="alternate" type="text/html"/>
  <id>{SITE_URL}/feed.xml</id>
  <updated>{datetime.now(timezone.utc).isoformat()}</updated>
  <author><name>AcaciaFund</name></author>
{chr(10).join(feed_items)}
</feed>"""
    (OUTPUT_DIR / "feed.xml").write_text(feed, encoding="utf-8")
    print("Generated: feed.xml")

    # --- SITEMAP ---
    urls = [f"{SITE_URL}/"]
    for c in all_content:
        urls.append(slug_to_url(c.slug))
    for page_name in static_page_map:
        urls.append(f"{SITE_URL}/{page_name}.html")
    for p in pillar_groups:
        urls.append(f"{SITE_URL}/{p}/")
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for url in urls:
        sm.append(f"  <url><loc>{url}</loc></url>")
    sm.append("</urlset>")
    (OUTPUT_DIR / "sitemap.xml").write_text("\n".join(sm), encoding="utf-8")
    print("Generated: sitemap.xml")

    # --- ROBOTS ---
    (OUTPUT_DIR / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n", encoding="utf-8"
    )
    print("Generated: robots.txt")

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
    print("Generated: _headers")

    total = len(list(OUTPUT_DIR.rglob("*.html")))
    print(f"Generation complete. Total pages: {total}")
    return 0


def _make_dummy_content(title="", slug="", body_html="", category="post"):
    return type("obj", (object,), {
        "title": title,
        "language": "en",
        "category": category,
        "slug": slug,
        "body_html": body_html,
        "description": "",
        "created_at": None,
        "updated_at": None,
        "tags": [],
        "pillar": "",
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
    })


def _render_page(env, content, page_path="", **ctx):
    return env.get_template("layout.j2").render(
        content=content, is_index=False, page_path=page_path, page_type="page", **ctx
    )


def _render_blog_post(env, post, page_path, prev_post, next_post, related, toc_items, ctx):
    pillar = post.pillar or "aml"
    pconf = PILLAR_CONFIG.get(pillar, PILLAR_CONFIG["aml"])
    sqi_svg = generate_sqi_badge(post.signals.get("avg_sqi", 0.5)) if post.signals else ""
    og_key = hashlib.md5(f"og_{post.title}".encode()).hexdigest()[:12]
    og_image_url = f"{SITE_URL}/static/images/og_{og_key}.svg"
    thumb_base = f"{SITE_URL}/static/images"
    ctx_full = dict(ctx, content=post, page_path=page_path,
                     prev_post=prev_post, next_post=next_post,
                     pconf=pconf, sqi_svg=sqi_svg,
                     og_image_url=og_image_url,
                     thumbnail_base=thumb_base,
                     thumbnail_key=thumbnail_key,
                     toc_items=toc_items,
                     related_posts=related)
    return env.get_template("blog_post.j2").render(**ctx_full)


def _render_pillar_index(env, content, pillar, pconf, posts, ctx):
    thumb_base = f"{ctx['site_url']}/static/images"
    ctx_full = dict(ctx, content=content, pillar=pillar, pconf=pconf, posts=posts,
                     is_index=False, page_path=f"{pillar}/",
                     thumbnail_base=thumb_base, thumbnail_key=thumbnail_key)
    return env.get_template("pillar_index.j2").render(**ctx_full)


def _render_index(env, posts, featured, lessons, ctx):
    thumb_base = f"{ctx['site_url']}/static/images"
    ctx_full = dict(ctx, recent_posts=posts, featured_posts=featured, lessons=lessons,
                     thumbnail_base=thumb_base, thumbnail_key=thumbnail_key)
    dummy = _make_dummy_content(
        title="Research Synthesis & Experimental Learning",
        slug="",
        body_html="",
        category="index",
    )
    return env.get_template("index.j2").render(content=dummy, is_index=True, page_path="", **ctx_full)


if __name__ == "__main__":
    exit(main())
