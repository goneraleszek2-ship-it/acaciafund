#!/usr/bin/env python3
"""AcaciaFund — daily automated research synthesis pipeline (enhanced)."""

import sys
from datetime import datetime, timezone

from core.data import PILLARS, log
from core.fetch import fetch_hn_stories, fetch_arxiv
from core.analyze import classify_story
from core.generate import generate_post


def inject_arxiv(pillar_stories: dict[str, list[dict]]) -> None:
    log("Pobieranie z arXiv API...")
    papers = fetch_arxiv(since_hours=72)
    log(f"Pobrano {len(papers)} pasujacych prac")
    for paper in papers:
        p = paper["pillar"]
        pillar_stories[p].append({
            "title": paper["title"],
            "url": paper["url"],
            "hn_url": "",
            "points": 0,
            "created_at": paper["published"],
            "author": "arXiv",
            "object_id": "",
        })
        log(f"  -> {p}: {paper['title'][:70]}")


def main():
    print("=" * 55, file=sys.stderr)
    log(f"AcaciaFund -- start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print("=" * 55, file=sys.stderr)

    all_stories = fetch_hn_stories(since_hours=48, min_points=2)
    log(f"Pobrano {len(all_stories)} stories z HN")

    if not all_stories:
        log("Brak danych z HN -- koncze", ok=False)
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
        f"SCIENCE={len(pillar_stories['science'])}, unclassified={unclassified}")

    inject_arxiv(pillar_stories)

    for p in PILLARS:
        hn = [s for s in pillar_stories[p] if s.get("points", 0) > 0]
        arx = [s for s in pillar_stories[p] if s.get("points", 0) == 0]
        hn.sort(key=lambda s: s["points"], reverse=True)
        pillar_stories[p] = hn[:25] + arx[:5]

    generated = 0
    for pillar, config in PILLARS.items():
        if generate_post(
            pillar, config, pillar_stories[pillar],
            all_pillar_stories=pillar_stories,
            _all_stories=all_stories,
            _unclassified=unclassified,
        ):
            generated += 1

    print("=" * 55, file=sys.stderr)
    log(f"Koniec potoku. Wygenerowano {generated} postow.")
    print("=" * 55, file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
