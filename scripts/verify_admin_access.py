#!/usr/bin/env python3
"""Verify that the deployed /admin/ surface is behind an access gate.

A protected admin surface returns a redirect (Access login) or 401/403. A 200
response means the admin dashboard is publicly reachable.

Usage:
    python3 scripts/verify_admin_access.py --base-url https://www.acaciafund.org
"""

from __future__ import annotations

import argparse
import sys
import urllib.error
import urllib.request
from urllib.parse import urljoin

DEFAULT_PATHS = ("/admin/", "/admin/dashboard.html")
PROTECTED_STATUSES = {301, 302, 303, 307, 308, 401, 403}


def classify_response(status: int, location: str = "") -> str:
    """Return protected / unprotected / error for an admin response."""
    if status in PROTECTED_STATUSES:
        return "protected"
    if status == 200:
        return "unprotected"
    if status == 404:
        return "absent"
    return "error"


def check_path(base_url: str, path: str, timeout: float = 15) -> tuple[str, int, str]:
    url = urljoin(base_url.rstrip("/") + "/", path.lstrip("/"))
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return classify_response(response.status), response.status, url
    except urllib.error.HTTPError as exc:
        location = exc.headers.get("Location", "") if exc.headers else ""
        return classify_response(exc.code, location), exc.code, url


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--timeout", type=float, default=15)
    args = parser.parse_args(argv)

    failures = []
    for path in DEFAULT_PATHS:
        result, status, url = check_path(args.base_url, path, args.timeout)
        print(f"  {result:11s} HTTP {status} {url}")
        if result not in ("protected", "absent"):
            failures.append((url, result, status))

    if failures:
        print("Admin access gate FAILED:", file=sys.stderr)
        for url, result, status in failures:
            print(f"  - {url}: {result} (HTTP {status})", file=sys.stderr)
        return 1
    print("Admin access gate OK.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
