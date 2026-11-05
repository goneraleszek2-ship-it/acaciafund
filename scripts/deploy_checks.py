#!/usr/bin/env python3
"""Post-build smoke tests for deployment verification."""

import json
import re
import sys
from pathlib import Path

errors = []
dist = Path("dist")
site_url = "https://www.acaciafund.org"

for f in ["index.html", "build-meta.json", "sitemap.xml", "feed.xml", "favicon.ico"]:
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

CANONICAL_RE = re.compile(r'<link rel="canonical" href="([^"]+)"')
missing_canonical = []
broken_canonical = []
for page in dist.rglob("*.html"):
    rel = page.relative_to(dist)
    if rel.parts and rel.parts[0] == "admin":
        continue
    html = page.read_text(encoding="utf-8", errors="ignore")
    match = CANONICAL_RE.search(html)
    if not match:
        missing_canonical.append(str(rel))
        continue
    url = match.group(1)
    if not url.startswith(site_url + "/"):
        broken_canonical.append(f"{rel}: off-site canonical {url}")
        continue
    path = url[len(site_url) :].split("#", 1)[0].split("?", 1)[0]
    rel_path = path.lstrip("/")
    if not rel_path:
        rel_path = "index.html"
    elif path.endswith("/"):
        rel_path = rel_path + "index.html"
    target = dist / rel_path
    if not target.is_file():
        broken_canonical.append(f"{rel}: canonical target missing {url}")

if missing_canonical:
    errors.append(f"{len(missing_canonical)} public page(s) missing canonical, e.g. {missing_canonical[:5]}")
if broken_canonical:
    errors.append(f"{len(broken_canonical)} broken canonical URL(s), e.g. {broken_canonical[:5]}")

if errors:
    print("Post-build smoke tests FAILED:", file=sys.stderr)
    for e in errors:
        print(f"  - {e}", file=sys.stderr)
    sys.exit(1)
else:
    print("Post-build smoke tests passed.")
