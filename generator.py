#!/usr/bin/env python3.13
"""
Generator for AcaciaFund: converts registry.json to static HTML using Jinja2 template.
"""
import json
import os
import shutil
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape

from schemas import RegistryData

# Configuration
REGISTRY_PATH = Path("registry.json")
TEMPLATE_DIR = Path("templates")
OUTPUT_DIR = Path("dist")
STATIC_SRC_DIR = Path("public")  # Directory for static assets (images, favicon, etc.)
STATIC_DST_DIR = OUTPUT_DIR / "static"

def main():
    """Main function to run the generator."""
    print("Starting AcaciaFund generator...")

    # Load registry
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

    # Setup Jinja2 environment
    env = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=select_autoescape(['html', 'xml'])
    )
    template = env.get_template("layout.j2")

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    STATIC_DST_DIR.mkdir(parents=True, exist_ok=True)

    # Copy static assets from public/ to dist/static/
    if STATIC_SRC_DIR.exists():
        for item in STATIC_SRC_DIR.rglob("*"):
            if item.is_file():
                relative_path = item.relative_to(STATIC_SRC_DIR)
                dest_path = STATIC_DST_DIR / relative_path
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, dest_path)
        print(f"Copied static assets from {STATIC_SRC_DIR} to {STATIC_DST_DIR}")
    else:
        print(f"Warning: Static source directory {STATIC_SRC_DIR} does not exist.")

    # Generate pages for each content item
    for content in registry.content:
        # Determine the output path: dist/{slug}/index.html for sections, or dist/{slug}.html for pages?
        # We'll use a simple approach: for slugs that contain a slash, we treat as nested.
        # For simplicity, we'll output to dist/{slug}.html (if slug has no slash) or dist/{slug}/index.html (if slug has slash).
        # But note: we want to avoid duplicate index.html in nested directories? We'll follow common practice.
        slug = content.slug
        if '/' in slug:
            # Nested path: create a directory and put index.html inside
            output_dir = OUTPUT_DIR / slug
            output_dir.mkdir(parents=True, exist_ok=True)
            output_file = output_dir / "index.html"
        else:
            # Top-level file: output as {slug}.html
            output_file = OUTPUT_DIR / f"{slug}.html"

        # Render the template
        try:
            html = template.render(content=content)
        except Exception as e:
            print(f"Error rendering template for {content.slug}: {e}")
            continue

        # Write the file
        try:
            output_file.write_text(html, encoding="utf-8")
            print(f"Generated: {output_file.relative_to(OUTPUT_DIR)}")
        except Exception as e:
            print(f"Error writing {output_file}: {e}")
            continue

    # Generate a sitemap.xml? Optional, but we can skip for now.

    print("Generation complete.")
    return 0

if __name__ == "__main__":
    exit(main())