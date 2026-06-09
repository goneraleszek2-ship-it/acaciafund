#!/usr/bin/env python3
"""
Fetch CC-licensed images from Openverse API for articles without featured_image.
Saves to static/images/generated/ and updates registry.json.
"""
import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path
from urllib.parse import quote

import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REGISTRY_PATH = PROJECT_ROOT / "registry.json"
IMAGES_DIR = PROJECT_ROOT / "static" / "images" / "generated"
OPENVERSE_API = "https://api.openverse.engineering/v1/images/"
RATE_LIMIT_DELAY = 1.1  # seconds between requests
USER_AGENT = "AcaciaFund/1.0 (image-fetcher; +https://acaciafund.org)"
MAX_RETRY_ON_429 = 1


def build_query(article: dict) -> str:
    """Build a visual-metaphor search query from article title + tags + pillar."""
    title = article.get("title", "")
    tags = article.get("tags", [])
    pillar = article.get("pillar", "")
    pillar_keywords = {
        "aml": "compliance regulation security audit",
        "stock": "market finance trading economy",
        "data-engineering": "data pipeline server architecture",
        "science": "laboratory research experiment analysis",
    }
    kw = pillar_keywords.get(pillar, "")
    tag_str = " ".join(tags[:3]) if tags else ""
    parts = [title, kw, tag_str]
    return " ".join(p for p in parts if p)


def search_openverse(query: str, retry: int = 0) -> dict | None:
    """Search Openverse for the best CC image."""
    params = {
        "q": query,
        "license": "cc0,by",
        "license_type": "commercial",
        "size": "large",
        "aspect_ratio": "wide",
        "page_size": 5,
    }
    try:
        resp = requests.get(
            OPENVERSE_API,
            params=params,
            headers={"User-Agent": USER_AGENT},
            timeout=15,
        )
        if resp.status_code == 429:
            if retry < MAX_RETRY_ON_429:
                print(f"429, retrying… ", end="")
                time.sleep(3)
                return search_openverse(query, retry + 1)
            print(f"rate limited (429) ", end="")
            return None
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", [])
        if not results:
            return None
        # Prefer CC0 over CC-BY
        for r in results:
            if r.get("license") == "cc0":
                return r
        return results[0]
    except (requests.RequestException, json.JSONDecodeError) as e:
        print(f"  openverse error: {e}")
        return None


def download_image(url: str, dest: Path) -> bool:
    """Download image from URL to destination path."""
    try:
        resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
        resp.raise_for_status()
        content_type = resp.headers.get("content-type", "")
        ext = ".jpg"
        if "png" in content_type:
            ext = ".png"
        elif "webp" in content_type:
            ext = ".webp"
        elif "gif" in content_type:
            ext = ".gif"
        dest = dest.with_suffix(ext)
        dest.write_bytes(resp.content)
        return True, ext
    except (requests.RequestException, OSError) as e:
        print(f"  download failed: {e}")
        return False, ""


def fetch_images_for_article(article: dict, force: bool = False) -> dict | None:
    """Fetch an image for a single article. Returns update dict or None."""
    slug = article.get("slug", "")
    if not slug:
        return None
    existing = article.get("featured_image", "")
    if existing and not force:
        return None  # already has image

    # Build query with visual metaphors
    query = build_query(article)
    result = search_openverse(query)
    if not result:
        # Retry with fallback query (pillar-only)
        pillar = article.get("pillar", "")
        pillar_fallback = {
            "aml": "abstract compliance security concept",
            "stock": "abstract market finance concept",
            "data-engineering": "abstract data technology concept",
            "science": "abstract laboratory research concept",
        }
        fallback_q = pillar_fallback.get(pillar, "abstract concept minimalist")
        result = search_openverse(fallback_q)
        if not result:
            return None

    img_url = result.get("url", "")
    if not img_url:
        return None

    # Ensure output dir exists
    dest = IMAGES_DIR / slug
    dest.parent.mkdir(parents=True, exist_ok=True)
    ok, ext = download_image(img_url, dest)
    if not ok:
        return None

    rel_path = f"/static/images/generated/{slug}{ext}"
    creator = result.get("creator", "")
    license_name = result.get("license", "by").upper()
    license_url = result.get("license_url", "")
    credit_parts = [f"Photo by {creator}"] if creator else ["Photo"]
    credit_parts.append(f"via Openverse ({license_name})")
    if license_url:
        credit_parts.append(f" — {license_url}")
    credit = " ".join(credit_parts)

    return {
        "featured_image": rel_path,
        "image_credit": credit,
    }


def main():
    parser = argparse.ArgumentParser(description="Fetch CC images from Openverse for articles")
    parser.add_argument("--max", type=int, default=0, help="Max articles to process (0 = all)")
    args = parser.parse_args()

    if not REGISTRY_PATH.exists():
        print(f"Registry not found at {REGISTRY_PATH}")
        return 1

    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    content_list = registry.get("content", [])
    updated = 0
    skipped = 0
    max_count = args.max if args.max > 0 else len(content_list)

    # Process most recent articles first (by created_at, newest first)
    candidates = [(i, a) for i, a in enumerate(content_list) if not a.get("featured_image")]
    candidates.sort(key=lambda x: x[1].get("created_at", ""), reverse=True)
    candidates = candidates[:max_count]

    print(f"Fetching images for {len(candidates)} articles (out of {len(content_list)} total)…")

    for orig_idx, article in candidates:
        slug = article.get("slug", "")
        print(f"  {slug} … ", end="", flush=True)
        update = fetch_images_for_article(article)
        if update:
            content_list[orig_idx].update(update)
            updated += 1
            print(f"✓ {update['featured_image']}")
        else:
            print("✗")
        time.sleep(RATE_LIMIT_DELAY)

    if updated > 0:
        registry["content"] = content_list
        REGISTRY_PATH.write_text(
            json.dumps(registry, indent=2, default=str), encoding="utf-8"
        )
        print(f"\nUpdated {updated} articles ({skipped} already had images)")
    else:
        print(f"\nNo articles updated ({skipped} already had images)")


if __name__ == "__main__":
    exit(main())
