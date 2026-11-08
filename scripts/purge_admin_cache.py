#!/usr/bin/env python3
"""Purge Cloudflare edge cache for admin URLs removed from the deployment.

Cloudflare Pages keeps previously cached responses for deleted admin pages.
The production origin correctly returns 404 for these paths, but the edge can
still serve stale 200 responses. This script purges those URLs after deploy so
the admin access gate observes the current deployment.

Usage:
    CLOUDFLARE_API_TOKEN=... python3 scripts/purge_admin_cache.py
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request

ADMIN_PAGES = (
    "",
    "dashboard",
    "dashboard.html",
    "login",
    "login.html",
    "gallery",
    "gallery.html",
    "articles",
    "articles.html",
    "manifest",
    "manifest.html",
    "pipeline",
    "pipeline.html",
    "quality",
    "quality.html",
    "coverage",
    "coverage.html",
    "sources",
    "sources.html",
    "curated-test",
    "curated_test.html",
    "telemetry",
    "telemetry.html",
    "ontology",
    "ontology.html",
    "feynman",
    "feynman.html",
)

DEFAULT_BASE_URLS = ("https://www.acaciafund.org", "https://acaciafund.org")
DEFAULT_ZONE = "acaciafund.org"


def admin_urls(base_url: str) -> list[str]:
    base = base_url.rstrip("/")
    return [f"{base}/admin/{page}" for page in ADMIN_PAGES]


def _api_request(
    path: str,
    token: str,
    *,
    method: str = "GET",
    payload: dict | None = None,
    timeout: float = 20,
) -> dict:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(
        f"https://api.cloudflare.com/client/v4{path}",
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "AcaciaFund-Admin-Cache-Purge/1.0",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response)


def resolve_zone_id(token: str, zone_name: str = DEFAULT_ZONE) -> str:
    configured = os.environ.get("CLOUDFLARE_ZONE_ID", "").strip()
    if configured:
        return configured
    result = _api_request(f"/zones?name={zone_name}", token)
    zones = result.get("result") or []
    if not zones:
        raise RuntimeError(f"No Cloudflare zone found for {zone_name}")
    return str(zones[0]["id"])


def purge_urls(
    token: str, zone_id: str, urls: list[str], batch_size: int = 30
) -> dict:
    result: dict = {"success": True}
    for start in range(0, len(urls), batch_size):
        batch = urls[start : start + batch_size]
        result = _api_request(
            f"/zones/{zone_id}/purge_cache",
            token,
            method="POST",
            payload={"files": batch},
        )
        if not result.get("success"):
            raise RuntimeError(f"Cloudflare purge failed: {result.get('errors')}")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", action="append", default=None)
    parser.add_argument("--zone", default=os.environ.get("CLOUDFLARE_ZONE_NAME", DEFAULT_ZONE))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    token = os.environ.get("CLOUDFLARE_API_TOKEN", "").strip()
    if not token and not args.dry_run:
        print("CLOUDFLARE_API_TOKEN is required", file=sys.stderr)
        return 1

    base_urls = args.base_url or list(DEFAULT_BASE_URLS)
    urls: list[str] = []
    for base in base_urls:
        urls.extend(admin_urls(base))

    if args.dry_run:
        print(f"Would purge {len(urls)} admin URL(s):")
        for url in urls:
            print(f"  {url}")
        return 0

    try:
        zone_id = resolve_zone_id(token, args.zone)
        purge_urls(token, zone_id, urls)
    except (urllib.error.HTTPError, urllib.error.URLError, RuntimeError, ValueError) as exc:
        print(f"Admin cache purge failed: {exc}", file=sys.stderr)
        return 1

    print(f"Purged {len(urls)} admin URL(s) from zone {zone_id}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
