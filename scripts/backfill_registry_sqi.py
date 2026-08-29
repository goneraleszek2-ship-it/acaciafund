"""Deterministic SQI backfill for registry.json.

Backfills explicit ``sqi`` values for content items that lack them so the
registry is self-describing and matches build-time telemetry. It reuses the
same scoring function the build uses (``core/build_quality._compute_sqi_for_item``)
and the same priority as ``build.py`` (``signals.avg_sqi`` when present, else
the computed baseline), so persisted values exactly match what ``build.py``
would compute on the next run.

Determinism: scoring runs through ``core.content.Content.from_dict`` (the exact
shape ``build.py`` evaluates) and reuses ``core.build_quality._compute_sqi_for_item``,
so persisted values are byte-identical to the first recomputation the build would
perform for an item missing ``sqi``. ``created_at`` is parsed to a timezone-aware
datetime exactly as the build does, so the freshness component is not pinned to a
baseline.

Governance: any modification is validated against ``schemas.ContentItem`` and
``schemas.RegistryData`` before it is written. The pristine registry is backed
up to ``registry.pre-sqi-backfill.json`` on first run.

Usage:
    python3 scripts/backfill_registry_sqi.py            # write backfill
    python3 scripts/backfill_registry_sqi.py --dry-run  # preview only

Idempotent: re-running after a successful write reports 0 items to backfill.
"""

import argparse
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REGISTRY_PATH = ROOT / "registry.json"
BACKUP_PATH = ROOT / "registry.pre-sqi-backfill.json"

sys.path.insert(0, str(ROOT))


def _load_registry() -> dict:
    with open(REGISTRY_PATH, encoding="utf-8") as f:
        return json.load(f)


def _compute_baseline_sqi(item: dict) -> float:
    """Run the build-time SQI scorer against the same object shape the build
    uses (``core.content.Content.from_dict``), so persisted values are exactly
    what ``build.py`` computes for the item (``core.build_quality
    _compute_sqi_for_item``, invoked from the backfill branch)."""
    from core.build_quality import _compute_sqi_for_item
    from core.content import Content

    return _compute_sqi_for_item(Content.from_dict(item))


def _validate_registry(registry: dict) -> None:
    """Ensure the (possibly mutated) registry satisfies schemas.py. Raises
    ValueError on the first invalid item."""
    from schemas import ContentItem, RegistryData

    RegistryData.model_validate(registry)
    for item in registry.get("content", []):
        ContentItem.model_validate(item)


def _write_registry(registry: dict) -> None:
    """Atomically write registry.json preserving its exact formatting
    (json.dump indent=2, ensure_ascii=False, no trailing newline)."""
    payload = json.dumps(registry, indent=2, ensure_ascii=False)
    fd, tmp_path = tempfile.mkstemp(dir=str(ROOT), suffix=".json.tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            f.write(payload)
        os.replace(tmp_path, REGISTRY_PATH)
    except BaseException:
        os.unlink(tmp_path)
        raise


def _backfill(registry: dict) -> list:
    changed: list = []
    for item in registry.get("content", []):
        if item.get("sqi"):
            continue  # present and > 0 — already explicit
        signals = item.get("signals") if isinstance(item.get("signals"), dict) else {}
        avg = signals.get("avg_sqi")
        if isinstance(avg, (int, float)) and avg > 0:
            value = round(float(avg), 3)
        else:
            value = _compute_baseline_sqi(item)
        value = max(0.0, min(1.0, round(float(value), 3)))
        item["sqi"] = value
        changed.append(item)
    return changed


def _summary(changed: list) -> None:
    values = [float(item["sqi"]) for item in changed]
    print("Backfilled {} items:".format(len(changed)))
    print(
        "  min={:.3f}  max={:.3f}  mean={:.3f}".format(
            min(values), max(values), sum(values) / len(values)
        )
    )
    by_type: dict = {}
    for item in changed:
        by_type[item.get("content_type", "?")] = by_type.get(item.get("content_type", "?"), 0) + 1
    print("  by content_type: {}".format(by_type))
    below_gate = [v for v in values if v < 0.65]
    if below_gate:
        print(
            "  WARNING: {} items backfilled below the 0.65 quality-gate floor".format(
                len(below_gate)
            )
        )
    else:
        print("  all backfilled values >= 0.65 (quality gate satisfied)")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Deterministic SQI backfill for registry.json."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="compute and report backfills without writing registry.json",
    )
    args = parser.parse_args(argv)

    registry = _load_registry()
    items = registry.get("content", [])
    missing = [item for item in items if not item.get("sqi")]
    print("registry items: {}  |  missing explicit sqi: {}".format(len(items), len(missing)))
    if not missing:
        print("No items need backfill. Nothing to do.")
        return 0

    changed = _backfill(registry)

    try:
        _validate_registry(registry)
    except Exception as exc:  # noqa: BLE001 — fail-closed before writing
        print("ERROR: mutated registry failed schema validation: {}".format(exc))
        return 2

    _summary(changed)

    if args.dry_run:
        print("--- dry-run: registry.json NOT modified ---")
        return 0

    if not BACKUP_PATH.exists():
        shutil.copy2(REGISTRY_PATH, BACKUP_PATH)
        print("Backup written: {}".format(BACKUP_PATH))
    else:
        print("Backup already exists (kept pristine copy): {}".format(BACKUP_PATH))

    _write_registry(registry)

    # Post-write confidence check: reload and re-validate.
    reloaded = _load_registry()
    try:
        _validate_registry(reloaded)
    except Exception as exc:  # noqa: BLE001
        print("ERROR: written registry failed post-write validation: {}".format(exc))
        return 2
    still_missing = [i for i in reloaded.get("content", []) if not i.get("sqi")]
    print("Written registry.json: {} items, {} still missing explicit sqi.".format(
        len(reloaded.get("content", [])), len(still_missing)
    ))
    return 0


if __name__ == "__main__":
    sys.exit(main())
