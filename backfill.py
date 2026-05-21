#!/usr/bin/env python3
"""AcaciaFund — backfill historical daily posts."""

import sys
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone

from core.data import PILLARS, log, extract_themes
from core.fetch import fetch_hn_stories
from core.analyze import classify_story
from core.generate import generate_post


def process_day(target_date: datetime) -> int:
    """Fetch, classify & generate posts for one day. Returns # generated."""
    date_str = target_date.strftime("%Y-%m-%d")
    log(f"\n--- {date_str} ---")

    stories = fetch_hn_stories(target_date=target_date, min_points=2, use_cache=True)
    if not stories:
        log(f"Brak danych dla {date_str} — pomijam", ok=False)
        return 0
    log(f"Pobrano {len(stories)} stories")

    pillar_stories: dict[str, list[dict]] = {p: [] for p in PILLARS}
    unclassified = 0
    for story in stories:
        classifications = classify_story(story)
        if not classifications:
            unclassified += 1
            continue
        best = max(classifications, key=lambda x: x[1])
        pillar_stories[best[0]].append(story)

    log(f"AML={len(pillar_stories['aml'])}, STOCK={len(pillar_stories['stock'])}, SCIENCE={len(pillar_stories['science'])}, ?={unclassified}")

    for p in PILLARS:
        ps = pillar_stories[p]
        ps.sort(key=lambda s: s["points"], reverse=True)
        pillar_stories[p] = ps[:30]

    generated = 0
    for pillar, config in PILLARS.items():
        if generate_post(pillar, config, pillar_stories[pillar], target_date, pillar_stories):
            generated += 1
    return generated


def main():
    parser = argparse.ArgumentParser(description="Backfill historical AcaciaFund posts")
    parser.add_argument("--days", type=int, default=30, help="Liczba dni wstecz")
    parser.add_argument("--workers", type=int, default=3, help="Równoległe wątki (domyślnie 3)")
    args = parser.parse_args()

    today = datetime.now(timezone.utc)
    print("=" * 55, file=sys.stderr)
    log(f"AcaciaFund Backfill — {args.days} dni, {args.workers} wątków")
    print("=" * 55, file=sys.stderr)

    dates = [today - timedelta(days=d) for d in range(args.days, 0, -1)]
    total = 0

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(process_day, d): d for d in dates}
        for f in as_completed(futures):
            try:
                total += f.result()
            except Exception as e:
                log(f"Błąd dla {futures[f].strftime('%Y-%m-%d')}: {e}", ok=False)

    print("=" * 55, file=sys.stderr)
    log(f"Backfill zakończony. Wygenerowano {total} postów.")
    print("=" * 55, file=sys.stderr)


if __name__ == "__main__":
    main()
