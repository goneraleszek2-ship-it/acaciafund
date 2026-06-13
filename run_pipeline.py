#!/usr/bin/env python3
"""Wrapper to run the image pipeline with output unbuffered."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

import json, time, traceback, hashlib
from collections import Counter
from pathlib import Path

# Unbuffer output
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

from scripts.fetch_images import (
    PROJECT_ROOT, REGISTRY_PATH, IMAGES_DIR, parse_sections, compute_break_points,
    fetch_section_images, fetch_featured_image, SECTION_TYPES, RATE_LIMIT_DELAY
)

stats = {
    'total_articles': 0, 'articles_with_images': 0,
    'total_section_slots': 0, 'filled_slots': 0,
    'backend_hits': Counter(), 'section_coverage': {},
    'relevance_scores': [], 'total_bytes': 0,
}
use_cache = True
updated_count = 0

if not REGISTRY_PATH.exists():
    print(f"Registry not found at {REGISTRY_PATH}")
    sys.exit(1)

IMAGES_DIR.mkdir(parents=True, exist_ok=True)

# Load existing content hashes
GLOBAL_CONTENT_HASHES = {}
for f in IMAGES_DIR.rglob("*"):
    if f.is_file() and f.suffix in (".jpg", ".webp", ".png", ".jpeg", ".gif"):
        try:
            md5 = hashlib.md5(f.read_bytes()).hexdigest()
            GLOBAL_CONTENT_HASHES[md5] = f.name
        except Exception:
            pass
print(f"Loaded {len(GLOBAL_CONTENT_HASHES)} existing image hashes for dedup")

registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
content_list = registry.get("content", [])
content_list.sort(key=lambda x: x.get("created_at", ""), reverse=True)
print(f"Processing {len(content_list)} articles...\n")

for idx, article in enumerate(content_list):
    slug = article.get('slug', '')
    print(f'  [{idx+1}/{len(content_list)}] {slug} … ', end='', flush=True)

    try:
        existing_images = article.get('section_images', [])
        if use_cache and existing_images:
            valid = [i for i in existing_images if i.get('image_url')]
            if valid:
                sections = parse_sections(article)
                if sections:
                    bp = compute_break_points(sections, article)
                    break_indices = {s['section_index'] for s in bp}
                    existing_indices = {s.get('section_index') for s in valid}
                    fully_covered = existing_indices >= break_indices
                else:
                    fully_covered = True

                if fully_covered:
                    feat = article.get('featured_image', '')
                    if not feat or not (PROJECT_ROOT / feat.lstrip('/')).exists():
                        fi = fetch_featured_image(article)
                        if fi:
                            article['featured_image'] = fi
                            updated_count += 1
                    print(f'✓ cached ({len(valid)} images)')
                    stats['articles_with_images'] += 1
                    stats['filled_slots'] += len(valid)
                    for si in valid:
                        stats['backend_hits'][si.get('source_api','unknown')] += 1
                        stats['relevance_scores'].append(si.get('relevance_score',0))
                    continue

        feat = article.get('featured_image', '')
        if not feat or not (PROJECT_ROOT / feat.lstrip('/')).exists():
            fi = fetch_featured_image(article)
            if fi:
                article['featured_image'] = fi

        t0 = time.time()
        section_images = fetch_section_images(article, force=False)
        elapsed = time.time() - t0

        if section_images:
            article['section_images'] = section_images
            updated_count += 1
            n = len(section_images)
            stats['articles_with_images'] += 1
            stats['filled_slots'] += n
            for si in section_images:
                stats['backend_hits'][si.get('source_api','unknown')] += 1
                stats['relevance_scores'].append(si.get('relevance_score',0))
            print(f'✓ {n} images ({elapsed:.1f}s)')
        else:
            print(f'✗ ({elapsed:.1f}s)')

        time.sleep(RATE_LIMIT_DELAY)
    except Exception as e:
        print(f'ERROR: {e}')
        traceback.print_exc()

# Save
registry['content'] = content_list
REGISTRY_PATH.write_text(json.dumps(registry, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
print(f"\nSaved {updated_count} updated articles in registry")
