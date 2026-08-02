#!/usr/bin/env python3
"""
Source Freshness Checker

Checks HTTP status of inspiration sources from pillars.toml and writes
a source_health.json report to dist/. Optional: updates data/ontology.json
with last_verified/status fields on InspirationSource objects.

Usage:
    python3 scripts/check_source_freshness.py [--update-ontology]
"""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from http.client import HTTPResponse
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import tomllib

PROJECT_ROOT = Path(__file__).parent.parent
PILLARS_TOML = PROJECT_ROOT / "etc" / "pillars.toml"
ONTOLOGY_JSON = PROJECT_ROOT / "data" / "ontology.json"
DIST_DIR = PROJECT_ROOT / "dist"
DATA_DIR = PROJECT_ROOT / "data"
HEALTH_OUT = DIST_DIR / "source_health.json"
HEALTH_PERSIST = DATA_DIR / "source_health.json"

# Staleness thresholds (days)
FRESH_DAYS = 30
DEGRADED_DAYS = 90


def load_inspiration_sources() -> list[dict]:
    """Load inspiration sources from pillars.toml."""
    if not PILLARS_TOML.exists():
        print(f"ERROR: {PILLARS_TOML} not found")
        return []

    with open(PILLARS_TOML, "rb") as f:
        data = tomllib.load(f)

    sources = []
    insp = data.get("inspiration_sources", {})
    for pillar_key, pillar_sources in insp.items():
        if not isinstance(pillar_sources, dict):
            continue
        for src_key, src_info in pillar_sources.items():
            if isinstance(src_info, dict) and "url" in src_info:
                sources.append({
                    "key": f"{pillar_key}.{src_key}",
                    "pillar": pillar_key,
                    "name": src_info.get("name", src_key),
                    "url": src_info["url"],
                    "frequency": src_info.get("frequency", "weekly"),
                    "relevance": src_info.get("relevance", 0.5),
                })
    return sources


def _request(url: str, method: str, timeout: int) -> tuple[HTTPResponse | None, Exception | None]:
    """Single HTTP request; returns (response, error)."""
    req = Request(url, method=method, headers={
        "User-Agent": "AcaciaFund-SourceChecker/1.0",
        "Accept": "*/*",
    })
    try:
        return urlopen(req, timeout=timeout), None
    except Exception as e:  # noqa: BLE001 - HTTPError, URLError, TimeoutError, OSError
        return None, e


# Status codes that commonly mean "we reject HEAD requests / bot traffic" but
# that respond fine to GET — falling back avoids false-positive degradation.
_HEAD_REJECT_CODES = {400, 401, 403, 405, 406, 501}


def check_url(url: str, timeout: int = 15) -> dict:
    """Check URL health via HEAD, falling back to GET when HEAD is rejected."""
    result = {
        "http_status": None,
        "latency_ms": None,
        "error": None,
        "status": "unknown",
    }
    start = time.monotonic()

    resp, err = _request(url, "HEAD", timeout)
    if resp is None:
        if isinstance(err, HTTPError):
            result["http_status"] = err.code
            result["error"] = str(err)
        else:
            result["error"] = str(err) if err else "unknown error"
        # HEAD blocked / unsupported → retry with GET
        http_status = result.get("http_status")
        if isinstance(http_status, int) and http_status in _HEAD_REJECT_CODES:
            resp, err = _request(url, "GET", timeout)
            if resp is None:
                if isinstance(err, HTTPError):
                    result["http_status"] = err.code
                    result["error"] = f"{result['error']}; GET: {err}"
                else:
                    result["error"] = f"{result['error']}; GET: {err}"
            else:
                result["http_status"] = resp.status
                result["error"] = "HEAD blocked; verified via GET"
                resp.close()
    else:
        result["http_status"] = resp.status
        resp.close()

    result["latency_ms"] = int((time.monotonic() - start) * 1000)
    status = result.get("http_status")
    if isinstance(status, int) and 200 <= status < 400:
        result["status"] = "active"
    elif isinstance(status, int) and 400 <= status < 500:
        result["status"] = "degraded"
    else:
        result["status"] = "error"
    return result


def compute_staleness(last_verified: str | None) -> int | None:
    """Return days since last_verified, or None if never verified."""
    if not last_verified:
        return None
    try:
        last = datetime.fromisoformat(last_verified)
        # Treat naive timestamps as UTC to compare against aware 'now'
        if last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)
        delta = datetime.now(timezone.utc) - last
        return max(delta.days, 0)
    except (ValueError, TypeError):
        return None


def load_prior_verified() -> dict[str, str]:
    """Load last_verified per source key from the persisted health report."""
    prior: dict[str, str] = {}
    if not HEALTH_PERSIST.exists():
        return prior
    try:
        data = json.loads(HEALTH_PERSIST.read_text(encoding="utf-8"))
        for src in data.get("sources", []):
            key = src.get("key")
            last = src.get("last_verified")
            if key and last:
                prior[key] = last
    except (OSError, ValueError, json.JSONDecodeError):
        pass
    return prior


def main():
    update_ontology = "--update-ontology" in sys.argv

    print("=" * 60)
    print("Source Freshness Checker")
    print("=" * 60)

    sources = load_inspiration_sources()
    if not sources:
        print("No inspiration sources found.")
        return

    print(f"\nChecking {len(sources)} inspiration sources...\n")

    prior_verified = load_prior_verified()
    now = datetime.now(timezone.utc).isoformat()

    results = []
    active = 0
    degraded = 0
    error = 0

    for src in sources:
        health = check_url(src["url"])
        last_verified = prior_verified.get(src["key"])
        staleness = compute_staleness(last_verified)

        entry = {
            **src,
            **health,
            # Only bump last_verified on a successful check; keep the prior
            # timestamp on failure so staleness reflects real decay.
            "last_verified": now if health["status"] == "active" else (last_verified or now),
            "staleness_days": staleness,
        }
        results.append(entry)

        icon = {"active": "🟢", "degraded": "🟡", "error": "🔴"}.get(health["status"], "⚪")
        latency = f"{health['latency_ms']}ms" if health["latency_ms"] else "—"
        print(f"  {icon} {src['name']:30s} {health['http_status'] or '—':>4} {latency:>7}  {health['status']}")

        if health["status"] == "active":
            active += 1
        elif health["status"] == "degraded":
            degraded += 1
        else:
            error += 1

        time.sleep(0.3)  # Rate limit

    # Summary
    total = len(results)
    print(f"\n{'─' * 60}")
    print(f"  Total: {total}  Active: {active}  Degraded: {degraded}  Error: {error}")
    fresh_pct = round(active / total * 100) if total else 0
    print(f"  Freshness: {fresh_pct}%")
    print()

    # Write report
    report = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "total": total,
        "active": active,
        "degraded": degraded,
        "error": error,
        "freshness_pct": fresh_pct,
        "sources": results,
    }

    DIST_DIR.mkdir(parents=True, exist_ok=True)
    HEALTH_OUT.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    HEALTH_PERSIST.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(f"Report written to {HEALTH_OUT}")
    print(f"Persistent copy at {HEALTH_PERSIST}")

    # Optionally update ontology
    if update_ontology and ONTOLOGY_JSON.exists():
        onto = json.loads(ONTOLOGY_JSON.read_text(encoding="utf-8"))
        # Update inspiration sources with freshness data
        if "inspiration_sources" not in onto:
            onto["inspiration_sources"] = []
        # Merge freshness into existing or append
        existing_keys = {s.get("key") for s in onto["inspiration_sources"]}
        for entry in results:
            if entry["key"] in existing_keys:
                for i, s in enumerate(onto["inspiration_sources"]):
                    if s.get("key") == entry["key"]:
                        onto["inspiration_sources"][i]["last_verified"] = entry["last_verified"]
                        onto["inspiration_sources"][i]["status"] = entry["status"]
                        onto["inspiration_sources"][i]["http_status"] = entry["http_status"]
                        break
            else:
                onto["inspiration_sources"].append({
                    "key": entry["key"],
                    "pillar": entry["pillar"],
                    "name": entry["name"],
                    "url": entry["url"],
                    "last_verified": entry["last_verified"],
                    "status": entry["status"],
                    "http_status": entry["http_status"],
                })
        ONTOLOGY_JSON.write_text(json.dumps(onto, indent=2, default=str), encoding="utf-8")
        print(f"Updated {ONTOLOGY_JSON}")


if __name__ == "__main__":
    main()
