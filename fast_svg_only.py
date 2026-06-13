#!/usr/bin/env python3
"""Fast SVG-only image filler — no API calls, just SVG placeholders."""
import os, sys, json, hashlib, time, traceback
from collections import Counter
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(line_buffering=True)

from scripts.fetch_images import (
    PROJECT_ROOT, REGISTRY_PATH, IMAGES_DIR, parse_sections, compute_break_points,
    generate_svg_placeholder, build_section_query, SECTION_TYPES,
    TARGET_WORDS_PER_IMAGE, SECTION_WORD_MIN
)

print(f"TARGET_WORDS_PER_IMAGE={TARGET_WORDS_PER_IMAGE}, SECTION_WORD_MIN={SECTION_WORD_MIN}")
print()

registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
content_list = registry.get("content", [])
content_list.sort(key=lambda x: x.get("created_at", ""), reverse=True)

stats = {"updated": 0, "existing_kept": 0, "new_svg": 0, "skipped": 0}

for idx, article in enumerate(content_list):
    slug = article.get('slug', '')
    print(f'  [{idx+1}/{len(content_list)}] {slug} … ', end='', flush=True)

    try:
        sections = parse_sections(article)
        if not sections:
            print('no sections')
            stats["skipped"] += 1
            continue

        bp = compute_break_points(sections, article)
        if not bp:
            print('no break points')
            stats["skipped"] += 1
            continue

        existing = {s.get("section_index") for s in (article.get("section_images", []) or [])}
        existing_list = list(article.get("section_images", []) or [])
        new_results = []
        used_urls = set()

        # Keep existing images
        for ex in existing_list:
            idx_e = ex.get("section_index")
            if idx_e in {s["section_index"] for s in bp}:
                new_results.append(ex)
                stats["existing_kept"] += 1
            else:
                # Keep non-break images too (orphans)
                new_results.append(ex)
                stats["existing_kept"] += 1

        # For each break section, add SVG if missing
        added = 0
        for section in bp:
            sec_idx = section["section_index"]
            if sec_idx in existing:
                continue

            query = build_section_query(section, article) or "illustration"
            dest = IMAGES_DIR / f"{slug}_s{sec_idx}"
            dest.parent.mkdir(parents=True, exist_ok=True)

            ok, ext, w, h, size = generate_svg_placeholder(query, dest)
            if not ok:
                continue

            rel_path = f"/static/images/generated/{slug}_s{sec_idx}{ext}"
            new_results.append({
                "section_index": sec_idx,
                "heading": section["heading"],
                "image_url": rel_path,
                "image_credit": "SVG Placeholder (AcaciaFund)",
                "image_alt": f"Illustration of {section['heading']}",
                "relevance_score": 50.0,
                "source_api": "svg_fallback",
                "width": w,
                "height": h,
                "content_hash": hashlib.sha256(section.get("text_content", "").encode()).hexdigest()[:16],
            })
            added += 1
            stats["new_svg"] += 1

        if added > 0:
            article["section_images"] = new_results
            stats["updated"] += 1

        print(f'✓ {len(new_results)} images (+{added} svg)')
    except Exception as e:
        print(f'ERROR: {e}')
        traceback.print_exc()

# Save
registry['content'] = content_list
REGISTRY_PATH.write_text(json.dumps(registry, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
print(f"\nDone. {stats}")
print(f"Total images: {sum(len(c.get('section_images',[])) for c in content_list)}")
