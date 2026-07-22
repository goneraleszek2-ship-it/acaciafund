#!/usr/bin/env python3
"""Post-build smoke tests for deployment verification."""

import json
import sys
from pathlib import Path

errors = []
dist = Path("dist")

for f in ["index.html", "build-meta.json", "sitemap.xml"]:
    if not (dist / f).exists():
        errors.append(f"Missing dist/{f}")

log = dist / "build_errors.log"
if log.exists() and log.read_text().strip():
    errors.append(f"build_errors.log is not empty:\n{log.read_text()[:500]}")

meta = dist / "build-meta.json"
if meta.exists():
    data = json.loads(meta.read_text())
    for key in ["page_count", "duration_seconds", "timestamp"]:
        if key not in data:
            errors.append(f"build-meta.json missing key: {key}")

if errors:
    print("Post-build smoke tests FAILED:", file=sys.stderr)
    for e in errors:
        print(f"  - {e}", file=sys.stderr)
    sys.exit(1)
else:
    print("Post-build smoke tests passed.")
