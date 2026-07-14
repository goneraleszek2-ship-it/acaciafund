#!/usr/bin/env python3
"""Deployment preflight for AcaciaFund.

Validates registry metadata, runs governance gate (content density & semantics),
and optionally runs usability checks. Exits with code 1 on ANY failure.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def run(cmd: list[str], cwd: Path = ROOT) -> None:
    subprocess.run(cmd, cwd=str(cwd), check=True)


def validate_registry(write_index: bool = True) -> None:
    from core.metadata import load_registry_index, write_registry_index

    if write_index:
        write_registry_index()
    index = load_registry_index()
    if index.get("manifest_type") != "registry-index":
        raise SystemExit("registry index is missing or invalid")

    counts = index.get("counts", {})
    if counts.get("pages", 0) <= 0:
        raise SystemExit("registry index contains no story pages")


def run_governance_gate(content_dir: str = "content") -> int:
    """Run governance_gate.py and return its exit code."""
    from scripts.governance_gate import print_report, run_governance_check

    results = run_governance_check(content_dir)
    failure_count = print_report(results)
    if failure_count > 0:
        print(f"BLOCKED: {failure_count} article(s) failed governance gate")
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="AcaciaFund deployment preflight")
    parser.add_argument(
        "--no-write-registry", action="store_true", help="Do not rewrite registry/index.json"
    )
    parser.add_argument(
        "--build-site", action="store_true", help="Run Python generator (placeholder)"
    )
    parser.add_argument("--usability", action="store_true", help="Run tests/usability.py")
    parser.add_argument(
        "--skip-governance", action="store_true", help="Skip content governance gate"
    )
    parser.add_argument(
        "--governance-dir", default="content",
        help="Content directory for governance scan (default: content)"
    )
    args = parser.parse_args()

    validate_registry(write_index=not args.no_write_registry)

    if not args.skip_governance:
        gov_result = run_governance_gate(args.governance_dir)
        if gov_result != 0:
            return 1

    if args.build_site:
        print("--build-site: generator run would go here")

    if args.usability:
        run([sys.executable, "tests/usability.py"])

    print("preflight: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
