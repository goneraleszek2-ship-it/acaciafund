"""Enforce the build-time quality gate for CI.

Reads dist/build-meta.json and fails (exit 1) when more than
--fail-on-low-sqi items fall below the gate's SQI floor. The build
already computes quality.gate_passed / quality.low_sqi_items; this
script turns that signal into a hard, loggable CI step.

    python3 scripts/enforce_quality_gate.py [--build-meta dist/build-meta.json]
                                            [--fail-on-low-sqi 0]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def load_quality(build_meta: Path) -> dict:
    if not build_meta.exists():
        raise FileNotFoundError(f"build meta not found: {build_meta}")
    data = json.loads(build_meta.read_text(encoding="utf-8"))
    quality = data.get("quality") or {}
    if "gate_passed" not in quality:
        raise ValueError("build-meta.json has no quality.gate_passed block")
    return quality


def evaluate(quality: dict, fail_on_low_sqi: int = 0) -> list[dict]:
    low_sqi_count = int(quality.get("low_sqi_count", 0))
    low_sqi_items = quality.get("low_sqi_items", []) or []
    if low_sqi_count <= fail_on_low_sqi:
        return []
    if low_sqi_items:
        return list(low_sqi_items[: min(low_sqi_count, len(low_sqi_items))])
    return [
        {"slug": "(unknown)", "sqi": None, "effective_sqi": None}
        for _ in range(low_sqi_count)
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-meta", default="dist/build-meta.json", type=Path)
    parser.add_argument("--fail-on-low-sqi", default=0, type=int)
    args = parser.parse_args()

    try:
        quality = load_quality(args.build_meta)
    except (FileNotFoundError, ValueError) as exc:
        print(f"[quality-gate] ERROR: {exc}")
        return 2

    min_sqi = quality.get("gate_min_sqi", 0.65)
    gate_passed = quality.get("gate_passed", False)
    low_sqi_count = int(quality.get("low_sqi_count", 0))
    print(
        f"[quality-gate] SQI floor {min_sqi}: gate_passed={gate_passed}, "
        f"low_sqi_count={low_sqi_count}"
    )

    offenders = evaluate(quality, args.fail_on_low_sqi)
    if offenders:
        print(f"[quality-gate] FAIL: {len(offenders)} items below SQI {min_sqi}:")
        for item in offenders:
            slug = item.get("slug", "(unknown)")
            sqi = item.get("sqi") or item.get("effective_sqi")
            print(f"  - {slug} (SQI={sqi})")
        return 1
    print("[quality-gate] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
