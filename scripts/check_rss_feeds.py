#!/usr/bin/env python3
"""Check the health of all configured news RSS/Atom feeds.

Reports each feed's HTTP status, content type, whether the body parses as
XML, and whether it produced parseable items.  Used manually and from the
weekly source-refresh workflow to catch dying feeds early.

Usage:
    python3 scripts/check_rss_feeds.py            # check all feeds
    python3 scripts/check_rss_feeds.py --json     # machine-readable output
"""

import argparse
import json
import sys
import urllib.request
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.fetch_news import FEEDS, _http_get, _parse_rss  # noqa: E402

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AcaciaFund-NewsBot/3.0 "
        "(https://www.acaciafund.org; admin@acaciafund.org)"
    )
}


def check_feed(feed: dict[str, Any]) -> dict[str, Any]:
    url = feed["url"]
    status = 0
    content_type = ""
    try:
        req = urllib.request.Request(url, headers=HEADERS, method="HEAD")
        with urllib.request.urlopen(req, timeout=15) as resp:
            status = resp.status
            content_type = resp.headers.get("Content-Type", "")
    except Exception as e:
        if hasattr(e, "code"):
            status = e.code
        elif isinstance(e, urllib.error.HTTPError):
            status = e.code
        else:
            status = 0
    raw = _http_get(url, timeout=15) if status != 200 else None
    ok_xml = False
    item_count = 0
    if raw is None:
        raw = _http_get(url, timeout=15)
    if raw:
        parsed = _parse_rss(raw)
        item_count = len(parsed)
        ok_xml = item_count > 0
    healthy = status == 200 and ok_xml
    return {
        "name": feed["name"],
        "pillar": feed["pillar"],
        "url": url,
        "status": status,
        "content_type": content_type,
        "parseable": ok_xml,
        "item_count": item_count,
        "healthy": healthy,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Emit JSON report")
    args = parser.parse_args()

    results = [check_feed(f) for f in FEEDS]
    healthy = [r for r in results if r["healthy"]]
    dead = [r for r in results if not r["healthy"]]

    if args.json:
        payload = {
            "total": len(results),
            "healthy": len(healthy),
            "dead": len(dead),
            "feeds": results,
        }
        print(json.dumps(payload, indent=1))
    else:
        for r in results:
            mark = "OK " if r["healthy"] else "DEAD"
            print(
                f"{mark} {r['name']:24} [{r['pillar']:>4}] "
                f"status={r['status']} items={r['item_count']}"
            )
        print(f"\n{len(healthy)}/{len(results)} healthy; {len(dead)} dead/degraded")

    return 1 if dead else 0


if __name__ == "__main__":
    raise SystemExit(main())
