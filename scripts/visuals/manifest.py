"""Editorial image manifest — Tier 1 of visual management system.

How to override:
  1. Open scripts/visuals/manifest.json
  2. Add entry under article slug:
     {
       "blog/2026-06-10-feature-store-feast-vs-tecton": {
         "sections": [
           {
             "section_index": 1,
             "image_url": "https://images.unsplash.com/...",
             "image_credit": "Photo by ... via Unsplash (free to use)",
             "image_alt": "Feature store pipeline diagram"
           }
         ]
       }
     }
  3. On next deploy, fetch_images.py downloads and serves this image.
     The manifest wins over auto-fetched images.
"""

import json
from pathlib import Path

MANIFEST_PATH = Path(__file__).resolve().parent / "manifest.json"


def load_manifest() -> dict:
    if not MANIFEST_PATH.exists():
        return {}
    try:
        return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def get_manifest_entry(slug: str) -> list[dict] | None:
    manifest = load_manifest()
    entry = manifest.get(slug)
    if not entry or not entry.get("sections"):
        return None
    return entry["sections"]
