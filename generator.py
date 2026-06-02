#!/usr/bin/env python3.13
"""
Generator for AcaciaFund: converts registry.json to static HTML using Jinja2 template.
Produces: index.html, content pages, sitemap.xml, robots.txt, 404.html
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
SITE_URL = "https://acaciafund.org"


def add_lazy_loading(html: str) -> str:
    return re.sub(
        r'<img(?![^>]*loading=)',
        '<img loading="lazy" decoding="async"',
        html,
    )


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

    env = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=select_autoescape(['html', 'xml']),
    )
    template = env.get_template("layout.j2")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    STATIC_DST_DIR.mkdir(parents=True, exist_ok=True)

    if STATIC_SRC_DIR.exists():
        for item in STATIC_SRC_DIR.rglob("*"):
            if item.is_file():
                relative_path = item.relative_to(STATIC_SRC_DIR)
                dest_path = STATIC_DST_DIR / relative_path
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, dest_path)
        print(f"Copied static assets from {STATIC_SRC_DIR} to {STATIC_DST_DIR}")

    year = datetime.now(timezone.utc).year
    recent_posts = [c for c in registry.content if c.category == "blog"][:6]
    lessons = [c for c in registry.content if c.category == "learn"][:6]

    ctx_base = {
        "year": year,
        "recent_posts": recent_posts,
        "lessons": lessons,
        "plausible_domain": "",
    }

    # --- Index page ---
    index_html = template.render(
        content=type("obj", (object,), {"title": "AcaciaFund", "language": "en", "category": "index", "body_html": "", "created_at": None, "updated_at": None, "tags": []}),
        is_index=True,
        **ctx_base,
    )
    (OUTPUT_DIR / "index.html").write_text(index_html, encoding="utf-8")
    print("Generated: index.html")

    # --- 404 page ---
    page_404 = template.render(
        content=type("obj", (object,), {"title": "Page Not Found", "language": "en", "category": "error", "body_html": "<p>The page you requested does not exist. <a href=\"/\">Return home</a></p>", "created_at": None, "updated_at": None, "tags": []}),
        is_index=False,
        **ctx_base,
    )
    (OUTPUT_DIR / "404.html").write_text(page_404, encoding="utf-8")
    print("Generated: 404.html")

    # --- Content pages ---
    for content in registry.content:
        slug = content.slug
        if '/' in slug:
            output_dir = OUTPUT_DIR / slug
            output_dir.mkdir(parents=True, exist_ok=True)
            output_file = output_dir / "index.html"
        else:
            output_file = OUTPUT_DIR / f"{slug}.html"

        body_enhanced = add_lazy_loading(content.body_html)
        content.body_html = body_enhanced

        try:
            html = template.render(content=content, is_index=False, **ctx_base)
        except Exception as e:
            print(f"Error rendering template for {content.slug}: {e}")
            continue

        try:
            output_file.write_text(html, encoding="utf-8")
            print(f"Generated: {output_file.relative_to(OUTPUT_DIR)}")
        except Exception as e:
            print(f"Error writing {output_file}: {e}")

    # --- sitemap.xml ---
    urls = []
    urls.append(f"{SITE_URL}/")
    for content in registry.content:
        slug = content.slug
        path = f"{slug}/" if '/' in slug else f"{slug}.html"
        urls.append(f"{SITE_URL}/{path}")

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

    print("Generation complete.")
    return 0


if __name__ == "__main__":
    exit(main())
