#!/usr/bin/env python3
"""Verify that the deployed /admin/ surface is behind an access gate.

A protected admin surface returns a Cloudflare Access redirect, 401, or 403.
A 200 response means the admin dashboard is publicly reachable; a 404 means it
is absent. Same-site redirects (for example Pages `.html` normalization) are
followed before classifying the response.

Usage:
    python3 scripts/verify_admin_access.py --base-url https://www.acaciafund.org
"""

from __future__ import annotations

import argparse
import sys
import urllib.error
import urllib.request
from urllib.parse import urljoin, urlsplit

DEFAULT_PATHS = ("/admin/", "/admin/dashboard.html")
AUTH_STATUSES = {401, 403}
REDIRECT_STATUSES = {301, 302, 303, 307, 308}
MAX_REDIRECTS = 5


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


_OPENER = urllib.request.build_opener(
    urllib.request.ProxyHandler({}),
    _NoRedirectHandler,
)


def _is_access_redirect(location: str) -> bool:
    """Return True when a Location header points at a Cloudflare Access gate."""
    parsed = urlsplit(location)
    host = (parsed.hostname or "").lower()
    return "cloudflareaccess.com" in host or "/cdn-cgi/access/" in parsed.path


def classify_response(status: int, location: str = "") -> str:
    """Return protected / unprotected / absent / redirect / error."""
    if status in AUTH_STATUSES:
        return "protected"
    if status in REDIRECT_STATUSES:
        if not location:
            return "error"
        return "protected" if _is_access_redirect(location) else "redirect"
    if status == 200:
        return "unprotected"
    if status == 404:
        return "absent"
    return "error"


def check_path(base_url: str, path: str, timeout: float = 15) -> tuple[str, int, str]:
    url = urljoin(base_url.rstrip("/") + "/", path.lstrip("/"))
    for _ in range(MAX_REDIRECTS + 1):
        request = urllib.request.Request(
            url, headers={"User-Agent": "AcaciaFund-Admin-Access-Check/1.0"}
        )
        try:
            with _OPENER.open(request, timeout=timeout) as response:
                return classify_response(response.status), response.status, url
        except urllib.error.HTTPError as exc:
            location = exc.headers.get("Location", "") if exc.headers else ""
            result = classify_response(exc.code, location)
            if result != "redirect":
                return result, exc.code, url
            next_url = urljoin(url, location)
            if urlsplit(next_url).hostname != urlsplit(url).hostname:
                return "protected", exc.code, url
            url = next_url
    return "error", 0, url


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
