#!/usr/bin/env python3
"""AcaciaFund — daily automated research synthesis pipeline (enhanced)."""

import sys
from datetime import datetime, timezone
from pathlib import Path

from core.data import PILLARS, log
from core.fetch import fetch_hn_stories
from core.analyze import classify_story
from core.generate import generate_post
from core.metadata import build_run_manifest, write_json, iso_utc, write_registry_index
from core.sources import registry


def inject_external_sources(pillar_stories: dict[str, list[dict]]) -> dict[str, int]:
    """Fetch from all registry-enabled sources and distribute by pillar."""
    counts: dict[str, int] = {}

    for fetcher in registry.enabled:
        log(f"Fetching from {fetcher.name} ({fetcher.config.type})...")
        try:
            result = fetcher.fetch(since_hours=fetcher.config.schedule_hours)
        except Exception as e:
            log(f"  Failed {fetcher.name}: {e}", ok=False)
            counts[fetcher.name] = 0
            continue

        if not result.success or not result.items:
            log(f"  {fetcher.name}: {result.item_count} items (error={result.error})")
            counts[fetcher.name] = result.item_count
            continue

        counts[fetcher.name] = result.item_count
        log(f"  Fetched {result.item_count} items from {fetcher.name}")

        for item in result.items:
            p = item.get("pillar", "")
            if not p or p not in PILLARS:
                classifications = classify_story({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "points": 0,
                    "created_at": item.get("published", ""),
                    "author": item.get("author", ""),
                    "object_id": "",
                })
                if classifications:
                    p = max(classifications, key=lambda x: x[1])[0]
                else:
                    p = ""

            pillar_stories[p].append({
                "title": item.get("title", item.get("paper_url", "")),
                "url": item.get("url", item.get("paper_url", "")),
                "hn_url": item.get("hn_url", ""),
                "points": 0,
                "created_at": item.get("published", item.get("created_at", "")),
                "author": item.get("author", fetcher.name),
                "object_id": item.get("object_id", ""),
                "source": fetcher.name,
            })
            log(f"  -> {p} [{fetcher.name}]: {item.get('title', '')[:50]}")

    return counts


def main():
    print("=" * 55, file=sys.stderr)
    started_at = datetime.now(timezone.utc)
    run_id = started_at.strftime("%Y%m%dT%H%M%SZ")
    log(f"AcaciaFund -- start: {started_at.strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print("=" * 55, file=sys.stderr)

    all_stories = fetch_hn_stories(since_hours=48, min_points=2)
    log(f"Fetched {len(all_stories)} stories from HN")

    if not all_stories:
        log("No data from HN -- exiting", ok=False)
        return 1

    pillar_stories: dict[str, list[dict]] = {p: [] for p in PILLARS}
    unclassified = 0
    for story in all_stories:
        classifications = classify_story(story)
        if not classifications:
            unclassified += 1
            continue
        best = max(classifications, key=lambda x: x[1])
        pillar_stories[best[0]].append(story)

    log(f"AML={len(pillar_stories['aml'])}, STOCK={len(pillar_stories['stock'])}, "
        f"archived={len(pillar_stories[''])}, unclassified={unclassified}")

    source_counts = inject_external_sources(pillar_stories)

    for p in PILLARS:
        hn = [s for s in pillar_stories[p] if s.get("points", 0) > 0]
        arx = [s for s in pillar_stories[p] if s.get("points", 0) == 0]
        hn.sort(key=lambda s: s["points"], reverse=True)
        pillar_stories[p] = hn[:25] + arx[:5]

    generated = 0
    generated_pages: list[dict] = []
    for pillar, config in PILLARS.items():
        result = generate_post(
            pillar, config, pillar_stories[pillar],
            all_pillar_stories=pillar_stories,
            _all_stories=all_stories,
            _unclassified=unclassified,
            run_id=run_id,
        )
        if result:
            generated += 1
            bundle_name = result.parent.name
            generated_pages.append({
                "pillar": pillar,
                "path": str(result.relative_to(Path(__file__).parent)),
                "content_id": bundle_name,
                "manifest": str((result.parent / "manifest.json").relative_to(Path(__file__).parent)),
            })

    ended_at = datetime.now(timezone.utc)
    run_manifest = build_run_manifest(
        run_id=run_id,
        started_at=iso_utc(started_at),
        ended_at=iso_utc(ended_at),
        status="ok" if generated else "noop",
        source_counts={"hn": len(all_stories), **source_counts},
        generated_pages=generated_pages,
        output_count=generated,
        notes=[],
    )
    write_json(Path(__file__).parent / "registry" / "runs" / f"{run_id}.json", run_manifest)
    write_registry_index()

    print("=" * 55, file=sys.stderr)
    log(f"Pipeline complete. Generated {generated} posts.")
    print("=" * 55, file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
