#!/usr/bin/env python3
"""AcaciaFund — daily automated research synthesis pipeline (enhanced)."""

import sys
from datetime import datetime, timezone
from pathlib import Path

from core.data import PILLARS, log
from core.fetch import fetch_hn_stories, fetch_arxiv, fetch_pubmed
from core.analyze import classify_story
from core.generate import generate_post
from core.metadata import build_run_manifest, write_json, iso_utc, write_registry_index


def inject_external_sources(pillar_stories: dict[str, list[dict]]) -> dict[str, int]:
    """Fetch from external sources (arXiv, PubMed, etc.) and distribute by pillar."""
    counts = {"arxiv": 0, "pubmed": 0}
    
    # Fetch arXiv papers
    log("Fetching from arXiv API...")
    arxiv_papers = fetch_arxiv(since_hours=72)
    counts["arxiv"] = len(arxiv_papers)
    log(f"Fetched {len(arxiv_papers)} matching papers from arXiv")
    for paper in arxiv_papers:
        p = paper["pillar"]
        pillar_stories[p].append({
            "title": paper["title"],
            "url": paper["url"],
            "hn_url": "",
            "points": 0,
            "created_at": paper["published"],
            "author": "arXiv",
            "object_id": "",
            "source": "arxiv"
        })
        log(f"  -> {p} [arXiv]: {paper['title'][:50]}")
    
    # Fetch PubMed papers
    log("Fetching from PubMed...")
    pubmed_papers = fetch_pubmed(since_hours=168)
    counts["pubmed"] = len(pubmed_papers)
    log(f"Fetched {len(pubmed_papers)} matching papers from PubMed")
    for paper in pubmed_papers:
        # Classify PubMed papers using existing logic
        classifications = classify_story({
            "title": paper["title"],
            "url": paper["url"],
            "points": 0,  # PubMed doesn't have points
            "created_at": paper["published"],
            "author": paper.get("author", ""),
            "object_id": ""
        })
        if classifications:
            best = max(classifications, key=lambda x: x[1])
            p = best[0]
        else:
            # Default to archived (unclassified)
            p = ""
        
        pillar_stories[p].append({
            "title": paper["title"],
            "url": paper["url"],
            "hn_url": "",
            "points": 0,
            "created_at": paper["published"],
            "author": paper.get("author", "PubMed"),
            "object_id": "",
            "source": "pubmed"
        })
        log(f"  -> {p} [PubMed]: {paper['title'][:50]}")
    
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
        source_counts={
            "hn": len(all_stories),
            "arxiv": source_counts.get("arxiv", 0),
            "pubmed": source_counts.get("pubmed", 0),
        },
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
