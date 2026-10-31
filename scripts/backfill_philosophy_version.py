"""Pin each registry item's ``philosophy_version`` to ``config.PHILOSOPHY_VERSION``.

``core/provenance.py`` stamps ``config.PHILOSOPHY_VERSION`` onto items at build
time, but items created before a version bump retain the value that was current
when they were written. This script reports (and optionally applies) the drift so
the whole registry reflects a single, current philosophy version.

Usage:
    python3 scripts/backfill_philosophy_version.py --report   # dry run (default)
    python3 scripts/backfill_philosophy_version.py --apply    # writes registry.json
"""

from __future__ import annotations

import argparse
import shutil
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from config import PHILOSOPHY_VERSION  # noqa: E402
from core.registry_io import load_registry, save_registry  # noqa: E402

REGISTRY = ROOT / "registry.json"
BACKUP = ROOT / "registry.pre-philosophy-version-backfill.json"


def backfill(registry: dict, target: str) -> list[tuple[str, object]]:
    """Set ``philosophy_version`` on every content item to ``target``.

    Returns the list of ``(slug, previous_value)`` for items that changed.
    """
    changed: list[tuple[str, object]] = []
    for item in registry.get("content", []) or []:
        current = item.get("philosophy_version")
        if current != target:
            changed.append((item.get("slug", ""), current))
            item["philosophy_version"] = target
    return changed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Backfill registry philosophy_version")
    parser.add_argument("--apply", action="store_true", help="write registry.json (default: dry run)")
    parser.add_argument("--report", action="store_true", help="dry run: report drift only (default)")
    parser.add_argument("--registry", default=str(REGISTRY), help="path to registry.json")
    args = parser.parse_args(argv)

    registry = load_registry(args.registry)
    changed = backfill(registry, PHILOSOPHY_VERSION)

    print(f"philosophy_version -> {PHILOSOPHY_VERSION}")
    print(f"items changed: {len(changed)}")
    for previous, count in Counter(old for _, old in changed).most_common():
        print(f"  from {previous!r}: {count}")

    if not args.apply:
        print("dry run — pass --apply to write registry.json")
        return 0

    shutil.copy2(args.registry, BACKUP)
    save_registry(registry, args.registry)
    print(f"applied (backup: {BACKUP.name})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
