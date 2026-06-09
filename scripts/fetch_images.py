#!/usr/bin/env python3
"""
Fetch CC-licensed / public-domain images from multiple backends:
  1. Openverse (CC0/CC-BY)
  2. NASA Image Library (public domain, US government)
  3. Wikimedia Commons (CC0/CC-BY/CC-BY-SA)

Saves to static/images/generated/ and updates registry.json.
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REGISTRY_PATH = PROJECT_ROOT / "registry.json"
IMAGES_DIR = PROJECT_ROOT / "static" / "images" / "generated"
RATE_LIMIT_DELAY = 0.5
USER_AGENT = "AcaciaFund/1.0 (image-fetcher; +https://acaciafund.org)"

PILLAR_KEYWORDS = {
    "aml": "compliance regulation security audit",
    "stock": "market finance trading economy",
    "data-engineering": "data pipeline server architecture",
    "science": "laboratory research experiment analysis",
}

PILLAR_FALLBACK = {
    "aml": "abstract compliance security concept",
    "stock": "abstract market finance concept",
    "data-engineering": "abstract data technology concept",
    "science": "abstract laboratory research concept",
}


def build_query(article: dict) -> str:
    """Build a visual-metaphor search query from article title + tags + pillar."""
    title = article.get("title", "")
    tags = article.get("tags", [])
    pillar = article.get("pillar", "")
    kw = PILLAR_KEYWORDS.get(pillar, "")
    tag_str = " ".join(tags[:3]) if tags else ""
    parts = [title, kw, tag_str]
    return " ".join(p for p in parts if p)


def search_openverse(query: str, retry: int = 0) -> dict | None:
    """Search Openverse (CC0/CC-BY)."""
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
            "https://api.openverse.engineering/v1/images/",
            params=params,
            headers={"User-Agent": USER_AGENT},
            timeout=15,
        )
        if resp.status_code == 429:
            if retry < 1:
                time.sleep(3)
                return search_openverse(query, retry + 1)
            return None
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", [])
        if not results:
            return None
        for r in results:
            if r.get("license") == "cc0":
                return r
        return results[0]
    except (requests.RequestException, json.JSONDecodeError):
        return None


def search_nasa(query: str) -> dict | None:
    """Search NASA Image Library (public domain)."""
    try:
        resp = requests.get(
            "https://images-api.nasa.gov/search",
            params={"q": query, "media_type": "image"},
            headers={"User-Agent": USER_AGENT},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        items = data.get("collection", {}).get("items", [])
        if not items:
            return None
        # Find first item with a valid image URL
        for item in items:
            links = item.get("links", [])
            if not links:
                continue
            img_url = links[0].get("href", "")
            if not img_url:
                continue
            data_list = item.get("data", [{}])
            meta = data_list[0] if data_list else {}
            return {
                "url": img_url,
                "title": meta.get("title", ""),
                "creator": "NASA",
                "license": "cc0",
                "license_url": "https://www.nasa.gov/nasa-brand-center/images-and-media/",
            }
        return None
    except (requests.RequestException, json.JSONDecodeError):
        return None


def search_wikimedia(query: str) -> dict | None:
    """Search Wikimedia Commons for free-license images."""
    try:
        # Step 1: search for file pages
        sr = requests.get(
            "https://commons.wikimedia.org/w/api.php",
            params={
                "action": "query",
                "list": "search",
                "srsearch": query,
                "srnamespace": 6,
                "srlimit": 10,
                "format": "json",
            },
            headers={"User-Agent": USER_AGENT},
            timeout=15,
        )
        sr.raise_for_status()
        sr_data = sr.json()
        pages = sr_data.get("query", {}).get("search", [])
        if not pages:
            return None

        # Step 2: get image URLs for found files
        titles = "|".join(p["title"] for p in pages[:5])
        ii = requests.get(
            "https://commons.wikimedia.org/w/api.php",
            params={
                "action": "query",
                "titles": titles,
                "prop": "imageinfo",
                "iiprop": "url|extmetadata",
                "iiurlwidth": 1200,
                "format": "json",
            },
            headers={"User-Agent": USER_AGENT},
            timeout=15,
        )
        ii.raise_for_status()
        ii_data = ii.json()
        for pid, page in ii_data.get("query", {}).get("pages", {}).items():
            if pid == "-1":
                continue
            info = page.get("imageinfo", [{}])[0]
            img_url = info.get("url", "")
            if not img_url:
                continue
            meta = info.get("extmetadata", {})
            license_name = "cc-by-sa"
            license_url = ""
            if "LicenseShortName" in meta:
                license_name = meta["LicenseShortName"].get("value", license_name)
            if "LicenseUrl" in meta:
                license_url = meta["LicenseUrl"].get("value", "")
            artist = ""
            if "Artist" in meta:
                raw = meta["Artist"].get("value", "")
                artist = raw.replace("<a[^>]*>", "").replace("</a>", "").strip()[:100]
            return {
                "url": img_url,
                "title": page.get("title", "").replace("File:", "", 1),
                "creator": artist or "Wikimedia Commons",
                "license": license_name.lower().replace(" ", "-").replace("cc-", ""),
                "license_url": license_url,
            }
        return None
    except (requests.RequestException, json.JSONDecodeError):
        return None


BACKENDS = [
    ("openverse", search_openverse),
    ("nasa", search_nasa),
    ("wikimedia", search_wikimedia),
]


def fetch_featured_image(article: dict, force: bool = False) -> dict | None:
    """Fetch an image from the best available backend. Returns update dict."""
    slug = article.get("slug", "")
    if not slug:
        return None
    if article.get("featured_image", "") and not force:
        return None

    query = build_query(article)
    pillar = article.get("pillar", "")
    fallback_q = PILLAR_FALLBACK.get(pillar, "abstract concept minimalist")

    result = None
    backend_used = ""
    # Try primary query across all backends
    for name, search_fn in BACKENDS:
        result = search_fn(query)
        if result:
            backend_used = name
            break

    # Fallback: pillar-only query
    if not result:
        for name, search_fn in BACKENDS:
            result = search_fn(fallback_q)
            if result:
                backend_used = name
                break

    if not result:
        return None

    img_url = result.get("url", "")
    if not img_url:
        return None

    dest = IMAGES_DIR / slug
    dest.parent.mkdir(parents=True, exist_ok=True)
    ok, ext = download_image(img_url, dest)
    if not ok:
        return None

    rel_path = f"/static/images/generated/{slug}{ext}"
    creator = result.get("creator", "") or ""
    license_name = result.get("license", "by").upper()
    license_url = result.get("license_url", "") or ""
    backend_label = {"openverse": "Openverse", "nasa": "NASA", "wikimedia": "Wikimedia Commons"}.get(backend_used, backend_used)
    credit_parts = [f"Photo by {creator}"] if creator else ["Photo"]
    credit_parts.append(f"via {backend_label} ({license_name})")
    if license_url:
        credit_parts.append(f" — {license_url}")
    credit = " ".join(credit_parts)

    return {"featured_image": rel_path, "image_credit": credit}


def download_image(url: str, dest: Path) -> tuple[bool, str]:
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
        elif "jpeg" in content_type or "jpg" in content_type:
            ext = ".jpg"
        dest = dest.with_suffix(ext)
        dest.write_bytes(resp.content)
        return True, ext
    except (requests.RequestException, OSError):
        return False, ""


def main():
    parser = argparse.ArgumentParser(
        description="Fetch CC/public-domain images for articles from multiple backends"
    )
    parser.add_argument("--max", type=int, default=0, help="Max articles to process (0 = all)")
    args = parser.parse_args()

    if not REGISTRY_PATH.exists():
        print(f"Registry not found at {REGISTRY_PATH}")
        return 1

    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    content_list = registry.get("content", [])
    updated = 0
    max_count = args.max if args.max > 0 else len(content_list)

    candidates = [(i, a) for i, a in enumerate(content_list) if not a.get("featured_image")]
    candidates.sort(key=lambda x: x[1].get("created_at", ""), reverse=True)
    candidates = candidates[:max_count]

    print(f"Fetching images for {len(candidates)} articles (out of {len(content_list)} total)…")

    for orig_idx, article in candidates:
        slug = article.get("slug", "")
        print(f"  {slug} … ", end="", flush=True)
        update = fetch_featured_image(article)
        if update:
            content_list[orig_idx].update(update)
            updated += 1
            print(f"\u2713 {update['featured_image']}")
        else:
            print("\u2717")
        time.sleep(RATE_LIMIT_DELAY)

    if updated > 0:
        registry["content"] = content_list
        REGISTRY_PATH.write_text(json.dumps(registry, indent=2, default=str), encoding="utf-8")
        print(f"\nUpdated {updated} articles")
    else:
        print("\nNo articles updated")


if __name__ == "__main__":
    exit(main())
