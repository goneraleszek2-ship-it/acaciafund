#!/usr/bin/env python3
"""Re-fetch SVG/ai_generated sections with Unsplash (and Pixabay fallback).
Saves registry after each article to avoid data loss on interrupt."""
import os, sys, json, hashlib, time, traceback
from collections import Counter
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(line_buffering=True)

from scripts.fetch_images import (
    PROJECT_ROOT, REGISTRY_PATH, IMAGES_DIR, parse_sections, compute_break_points,
    build_section_query, search_unsplash, search_pixabay, search_pexels,
    download_image, score_result, normalize_query, generate_svg_placeholder,
    generate_alt_text, build_credit, UNSPLASH_KEY, PEXELS_KEY, PIXABAY_KEY,
    RATE_LIMIT_DELAY, MIN_SCORE, SECTION_TYPES
)

UNSPLASH_ACTIVE = bool(UNSPLASH_KEY)
PIXABAY_ACTIVE = bool(PIXABAY_KEY)
PEXELS_ACTIVE = bool(PEXELS_KEY)
print(f"Unsplash: {'✓' if UNSPLASH_ACTIVE else '✗'}  Pixabay: {'✓' if PIXABAY_ACTIVE else '✗'}  Pexels: {'✓' if PEXELS_ACTIVE else '✗'}")
print()

registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
content_list = registry.get("content", [])
content_list.sort(key=lambda x: x.get("created_at", ""), reverse=True)

total_replaced = 0
total_svg = 0

for idx, article in enumerate(content_list):
    slug = article.get('slug', '')
    existing = article.get("section_images", []) or []

    svg_sections = [s for s in existing if s.get("source_api") in ("svg_fallback", "ai_generated")]
    if not svg_sections:
        continue

    total_svg += len(svg_sections)
    print(f'[{idx+1}/{len(content_list)}] {slug} ({len(svg_sections)} svg): ', end='', flush=True)

    sections = parse_sections(article)
    sections_by_idx = {s["section_index"]: s for s in (sections or [])}

    replaced_count = 0
    for si in svg_sections:
        sec_idx = si["section_index"]
        section = sections_by_idx.get(sec_idx)
        if not section:
            continue

        query = build_section_query(section, article)
        if not query:
            continue
        query_terms, _ = normalize_query(query)

        # Try Unsplash → Pixabay → Pexels
        candidates = []
        if UNSPLASH_ACTIVE:
            try: candidates = search_unsplash(query)
            except Exception: pass
        if not candidates and PIXABAY_ACTIVE:
            try: candidates = search_pixabay(query)
            except Exception: pass
        if not candidates and PEXELS_ACTIVE:
            try: candidates = search_pexels(query)
            except Exception: pass
        if not candidates and PEXELS_ACTIVE:
            try: candidates = search_pexels(query)
            except Exception: pass
        if not candidates:
            continue

        scored = []
        for c in candidates:
            tag = "unsplash" if any("unsplash" in str(k) for k in c) else ("pixabay" if any("pixabay" in str(k) for k in c) else "pexels")
            score = score_result(c, query_terms, tag,
                                section_context=section.get("heading", ""),
                                pillar=article.get("pillar", ""))
            scored.append((score, c, tag))
        scored.sort(key=lambda x: -x[0])
        best_score, best, best_tag = scored[0]

        if best_score < MIN_SCORE:
            continue

        dest = IMAGES_DIR / f"{slug}_s{sec_idx}"
        dest.parent.mkdir(parents=True, exist_ok=True)
        ok, ext, w, h, size = download_image(best["url"], dest)
        if not ok:
            continue

        rel_path = f"/static/images/generated/{slug}_s{sec_idx}{ext}"
        si["image_url"] = rel_path
        si["image_credit"] = build_credit(best, best_tag)
        si["image_alt"] = generate_alt_text(section)
        si["relevance_score"] = float(best_score)
        si["source_api"] = best_tag
        si["width"] = w
        si["height"] = h
        si["content_hash"] = hashlib.sha256(section.get("text_content", "").encode()).hexdigest()[:16]
        replaced_count += 1
        print(f'r{sec_idx} ', end='', flush=True)
        time.sleep(RATE_LIMIT_DELAY)

    if replaced_count > 0:
        article["section_images"] = existing
        total_replaced += replaced_count
        # Save incrementally
        registry['content'] = content_list
        REGISTRY_PATH.write_text(json.dumps(registry, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
        print(f'→ saved ({replaced_count} replaced)')
    else:
        print('kept svg')

print(f"\nDone. {total_replaced}/{total_svg} SVG sections replaced with real photos")
