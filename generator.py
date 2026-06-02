#!/usr/bin/env python3.13
"""
Generator for AcaciaFund: converts registry.json to static HTML using Jinja2 template.
Produces: index.html, content pages, feed.xml, sitemap.xml, robots.txt, 404.html, _headers
"""
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from schemas import RegistryData

REGISTRY_PATH = Path("registry.json")
TEMPLATE_DIR = Path("templates")
OUTPUT_DIR = Path("dist")
STATIC_SRC_DIR = Path("public")
STATIC_DST_DIR = OUTPUT_DIR / "static"
PIPELINE_STATIC_DIR = Path("static")
SITE_URL = "https://acaciafund.org"


def add_lazy_loading(html: str) -> str:
    return re.sub(
        r'<img(?![^>]*loading=)',
        '<img loading="lazy" decoding="async"',
        html,
    )


def slug_to_path(slug: str) -> str:
    if '/' in slug:
        return f"{slug}/"
    return f"{slug}.html"


def slug_to_url(slug: str) -> str:
    return f"{SITE_URL}/{slug_to_path(slug)}"


def main():
    print("Starting AcaciaFund generator...")

    if not REGISTRY_PATH.exists():
        print(f"Error: {REGISTRY_PATH} not found. Run orchestrator.py first.")
        return 1

    try:
        with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
            registry_data = json.load(f)
        registry = RegistryData(**registry_data)
    except Exception as e:
        print(f"Error loading registry: {e}")
        return 1

    # Clean output directory first (remove old Hugo/Astro artifacts)
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    STATIC_DST_DIR.mkdir(parents=True, exist_ok=True)

    # Copy pipeline static assets (css, images)
    if PIPELINE_STATIC_DIR.exists():
        for item in PIPELINE_STATIC_DIR.rglob("*"):
            if item.is_file():
                relative_path = item.relative_to(PIPELINE_STATIC_DIR)
                dest_path = STATIC_DST_DIR / relative_path
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, dest_path)
        print(f"Copied pipeline static assets to {STATIC_DST_DIR}")

    # Copy legacy public/ assets (only specific needed files)
    if STATIC_SRC_DIR.exists():
        allowed = {'images', 'icons'}
        for subdir in allowed:
            src_sub = STATIC_SRC_DIR / subdir
            if src_sub.exists():
                dest_sub = STATIC_DST_DIR / subdir
                shutil.copytree(src_sub, dest_sub, dirs_exist_ok=True)
        print(f"Copied legacy static assets (images, icons)")

    env = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=select_autoescape(['html', 'xml']),
    )
    template = env.get_template("layout.j2")

    year = datetime.now(timezone.utc).year
    recent_posts = [c for c in registry.content if c.category == "blog"][:6]
    lessons = [c for c in registry.content if c.category == "learn"][:6]

    ctx_base = {
        "year": year,
        "site_url": SITE_URL,
        "recent_posts": recent_posts,
        "lessons": lessons,
        "plausible_domain": "",
    }

    # --- Index page ---
    index_html = template.render(
        content=type("obj", (object,), {
            "title": "AcaciaFund", "language": "en", "category": "index",
            "body_html": "", "description": "Automated research synthesis and experimental learning ecosystem. HackerNews + arXiv content classified by Bloom taxonomy.",
            "created_at": None, "updated_at": None, "tags": []
        })(),
        is_index=True,
        page_path="",
        **ctx_base,
    )
    (OUTPUT_DIR / "index.html").write_text(index_html, encoding="utf-8")
    print("Generated: index.html")

    # --- 404 page ---
    page_404 = template.render(
        content=type("obj", (object,), {
            "title": "Page Not Found", "language": "en", "category": "error",
            "body_html": "<p>The page you requested does not exist. <a href=\"/\">Return home</a></p>",
            "description": "Page not found",
            "created_at": None, "updated_at": None, "tags": []
        })(),
        is_index=False,
        page_path="404.html",
        prev_post=None,
        next_post=None,
        **ctx_base,
    )
    (OUTPUT_DIR / "404.html").write_text(page_404, encoding="utf-8")
    print("Generated: 404.html")

    # --- Content pages ---
    blog_posts = [c for c in registry.content if c.category == "blog"]
    for i, content in enumerate(registry.content):
        slug = content.slug
        page_path = slug_to_path(slug)

        if '/' in slug:
            output_dir = OUTPUT_DIR / slug
            output_dir.mkdir(parents=True, exist_ok=True)
            output_file = output_dir / "index.html"
        else:
            output_file = OUTPUT_DIR / f"{slug}.html"

        body_enhanced = add_lazy_loading(content.body_html)
        content.body_html = body_enhanced

        # Find prev/next for blog posts
        prev_post = None
        next_post = None
        if content.category == "blog":
            for j, bp in enumerate(blog_posts):
                if bp.slug == content.slug:
                    if j > 0:
                        prev_post = blog_posts[j - 1]
                    if j < len(blog_posts) - 1:
                        next_post = blog_posts[j + 1]
                    break

        try:
            html = template.render(
                content=content,
                is_index=False,
                page_path=page_path,
                prev_post=prev_post,
                next_post=next_post,
                **ctx_base,
            )
        except Exception as e:
            print(f"Error rendering template for {content.slug}: {e}")
            continue

        try:
            output_file.write_text(html, encoding="utf-8")
            print(f"Generated: {output_file.relative_to(OUTPUT_DIR)}")
        except Exception as e:
            print(f"Error writing {output_file}: {e}")

    # --- RSS/Atom feed ---
    feed_items = []
    for post in blog_posts[:20]:
        path = slug_to_path(post.slug)
        desc = post.description or post.body_html[:200]
        feed_items.append(f"""  <entry>
    <title>{post.title}</title>
    <link href="{SITE_URL}/{path}" rel="alternate" type="text/html"/>
    <id>{SITE_URL}/{path}</id>
    <updated>{post.created_at.isoformat() if post.created_at else ''}</updated>
    <summary>{desc[:300]}</summary>
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

    # --- sitemap.xml ---
    urls = [f"{SITE_URL}/"]
    for content in registry.content:
        urls.append(slug_to_url(content.slug))
    sitemap_lines = ['<?xml version="1.0" encoding="UTF-8"?>',
                     '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for url in urls:
        sitemap_lines.append(f"  <url><loc>{url}</loc></url>")
    sitemap_lines.append("</urlset>")
    (OUTPUT_DIR / "sitemap.xml").write_text("\n".join(sitemap_lines), encoding="utf-8")
    print("Generated: sitemap.xml")

    # --- robots.txt ---
    robots_txt = f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n"
    (OUTPUT_DIR / "robots.txt").write_text(robots_txt, encoding="utf-8")
    print("Generated: robots.txt")

    # --- _headers for Cloudflare Pages (allow WAVE/a11y bots) ---
    headers = """/*
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
"""
    (OUTPUT_DIR / "_headers").write_text(headers, encoding="utf-8")
    print("Generated: _headers")

    print(f"Generation complete. Total pages: {len(list(OUTPUT_DIR.rglob('*.html')))}")
    return 0


if __name__ == "__main__":
    exit(main())
