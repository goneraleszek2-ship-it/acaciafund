"""Check liveness of external references on built pages.

Scans dist/*.html for external http(s) hrefs (excluding the site's own
origin), issues HEAD requests (GET fallback) with retries, and reports
failures. Hosts listed in data/known_blocking_hosts.json are skipped
(known to block automated HEAD/GET requests) and recorded as skipped,
not failed.

    python3 scripts/check_external_links.py [--dist-dir dist] [--fail-on 0]

Writes dist/external-link-report.json with per-URL status.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

EXTERNAL_RE = re.compile(r'href="(https?://[^"]+)"')
OWN_ORIGINS = {"acaciafund.org", "www.acaciafund.org"}
BLOCKING_HOSTS_PATH = Path("data/known_blocking_hosts.json")
USER_AGENT = "AcaciaFundLinkCheck/1.0 (+https://www.acaciafund.org)"


def load_blocking_hosts() -> set[str]:
    if BLOCKING_HOSTS_PATH.exists():
        data = json.loads(BLOCKING_HOSTS_PATH.read_text(encoding="utf-8"))
        return set(data.get("hosts", []))
    return set()


def _request(url: str, method: str) -> int:
    req = urllib.request.Request(
        url, method=method, headers={"User-Agent": USER_AGENT, "Accept": "*/*"}
    )
    with urllib.request.urlopen(req, timeout=8) as resp:
        return resp.status


def check_url(url: str, blocking_hosts: set[str], retries: int = 2) -> dict:
    host = urllib.parse.urlparse(url).netloc.lower()
    if host in blocking_hosts:
        return {"url": url, "status": "skipped", "reason": f"host in {BLOCKING_HOSTS_PATH.name}"}
    last_code: int | None = None
    for attempt in range(retries + 1):
        for method in ("HEAD", "GET"):
            try:
                status = _request(url, method)
                return {"url": url, "status": "ok", "http_status": status}
            except urllib.error.HTTPError as exc:
                last_code = exc.code
            except (urllib.error.URLError, OSError, TimeoutError):
                last_code = None
                break
        if last_code is not None and last_code in (403, 405, 406, 429):
            return {"url": url, "status": "blocked", "http_status": last_code}
        if attempt < retries:
            time.sleep(1 + attempt)
    if last_code is not None and last_code >= 500:
        return {"url": url, "status": "server_error", "http_status": last_code}
    if last_code is not None:
        return {"url": url, "status": "error", "http_status": last_code}
    return {"url": url, "status": "unreachable"}


def collect_external_urls(dist_dir: Path) -> list[str]:
    seen: set[str] = set()
    for html in sorted(dist_dir.rglob("*.html")):
        text = html.read_text(encoding="utf-8", errors="ignore")
        for href in EXTERNAL_RE.findall(text):
            parsed = urllib.parse.urlparse(href)
            if not parsed.netloc:
                continue
            host = parsed.netloc.lower().split(":")[0]
            if host in OWN_ORIGINS:
                continue
            url = href.split("#", 1)[0].split("?")[0]
            if url not in seen:
                seen.add(url)
    return sorted(seen)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist-dir", default="dist", type=Path)
    parser.add_argument("--fail-on", default=0, type=int)
    parser.add_argument("--max-urls", default=0, type=int)
    args = parser.parse_args()

    blocking_hosts = load_blocking_hosts()
    urls = collect_external_urls(args.dist_dir)
    if args.max_urls:
        urls = urls[: args.max_urls]
    print(f"[external-links] checking {len(urls)} unique external URLs")

    results: list[dict] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        for result in pool.map(lambda u: check_url(u, blocking_hosts), urls):
            results.append(result)
            if result["status"] != "ok":
                print(f"  {result['status']}: {result['url']}")

    report = {
        "checked": len(results),
        "ok": sum(1 for r in results if r["status"] == "ok"),
        "skipped": sum(1 for r in results if r["status"] == "skipped"),
        "blocked": sum(1 for r in results if r["status"] == "blocked"),
        "server_error": [r for r in results if r["status"] == "server_error"],
        "unreachable": [r for r in results if r["status"] == "unreachable"],
        "error": [r for r in results if r["status"] == "error"],
        "results": results,
    }
    out = args.dist_dir / "external-link-report.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(
        f"[external-links] ok={report['ok']} skipped={report['skipped']} "
        f"blocked={report['blocked']} server_error={len(report['server_error'])} "
        f"unreachable={len(report['unreachable'])} error={len(report['error'])}"
    )
    if len(report["error"]) > args.fail_on:
        for item in report["error"]:
            print(f"  FAIL: {item['url']} ({item['status']})")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
