#!/usr/bin/env python3
"""Backfill pluralistic validation rubric fields into registry.json.

Runs the five-track rubric (core/validation.py) over every registry content
item, persists the per-item scores and aggregate decision, and reports the
decision distribution. A rubric that cannot reject is not a rubric, so this
script is expected to produce a mix of accept / review / reject.

Usage:
    python3 scripts/backfill_validation.py            # dry-run, report only
    python3 scripts/backfill_validation.py --apply    # write registry.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.registry_io import load_registry, save_registry  # noqa: E402
from core.validation import (  # noqa: E402
    apply_validation_fields,
    validate_content_pluralistic,
)


def _distribution(result: dict) -> dict:
    overall = result.get("overall", {})
    return {
        "accept": overall.get("accepted", 0),
        "review": overall.get("reviewed", 0),
        "reject": overall.get("rejected", 0),
        "average_composite": overall.get("average_composite", 0.0),
    }


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(description="Backfill validation rubric fields")
    parser.add_argument("--registry", default=str(ROOT / "registry.json"))
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write results back to registry.json (default: dry-run).",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Emit the full rubric result as JSON to stdout.",
    )
    args = parser.parse_args(argv)

    registry_path = Path(args.registry)
    reg = load_registry(registry_path)
    items = reg.get("content", [])
    if not items:
        print(f"No content items found in {registry_path}", file=sys.stderr)
        return 1

    result = validate_content_pluralistic(items)
    updated = apply_validation_fields(items, result)

    dist = _distribution(result)
    print(f"Registry items: {len(items)}")
    print(f"Updated fields: {updated}")
    print(f"Decision distribution: {dist}")
    print("Per-track averages:")
    for track, avg in result.get("overall", {}).get("average_scores", {}).items():
        print(f"  {track}: {avg}")

    if args.report:
        print(json.dumps(result["overall"], indent=2))

    if args.apply:
        if updated != len(items):
            print(
                f"Warning: only {updated}/{len(items)} items updated; aborting write.",
                file=sys.stderr,
            )
            return 1
        save_registry(reg, registry_path)
        print(f"Wrote {registry_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
