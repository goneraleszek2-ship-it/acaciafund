"""Backfill OpenAlex citation metadata for registry items carrying DOIs.

Queries the OpenAlex works API (keyless, ~10 req/s allowed) for each item
with a DOI and no recorded OpenAlex metadata, persisting:

- ``cited_by_count``: how many times OpenAlex records the work being cited
- ``openalex_id``: canonical OpenAlex work ID (https://openalex.org/W...)
- ``openalex_not_found``: set when OpenAlex has no record for the DOI

The registry is backed up to ``registry.pre-openalex-backfill.json`` on apply.
Builds remain offline-safe: the script is run as a maintenance step, and all
data is baked into ``registry.json`` before any build.

Run:
    python3 scripts/backfill_openalex.py [--dry-run] [--refresh] [--sleep S]

Options:
    --dry-run   report what would change without writing
    --refresh   refetch items that already have OpenAlex metadata
    --sleep S   seconds between API calls (default 0.15, ~6 req/s)
"""

import argparse
import json
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

REPO_ROOT = Path(__file__).resolve().parent.parent
REGISTRY_PATH = REPO_ROOT / "registry.json"
BACKUP_PATH = REPO_ROOT / "registry.pre-openalex-backfill.json"
OPENALEX_API = "https://api.openalex.org/works/doi:{}"
USER_AGENT = "AcaciaFund/1.0 (maintenance backfill; mailto:acaciafund@example.invalid)"


def fetch_openalex_work(doi: str, timeout: float = 15.0) -> dict | None:
    """Fetch an OpenAlex work for a DOI. Returns parsed JSON or None on error.

    Raises no exceptions: 404 (not found) returns None, network errors are
    swallowed after being reported by the caller.
    """
    url = OPENALEX_API.format(quote(doi, safe=""))
    request = Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        if exc.code == 404:
            return None
        print(f"  [http {exc.code}] {doi}")
        return None
    except (URLError, TimeoutError, OSError) as exc:
        print(f"  [network error] {doi}: {exc}")
        return None


def apply_work_to_item(item: dict, work: dict | None) -> bool:
    """Merge OpenAlex metadata into a registry item. Returns True if changed."""
    if work is None:
        if not item.get("openalex_not_found"):
            item["openalex_not_found"] = True
            item.pop("openalex_id", None)
            item.pop("cited_by_count", None)
            return True
        return False

    changed = False
    cited = work.get("cited_by_count")
    oa_id = work.get("id")
    if isinstance(cited, int) and cited >= 0 and item.get("cited_by_count") != cited:
        item["cited_by_count"] = cited
        changed = True
    if oa_id and item.get("openalex_id") != oa_id:
        item["openalex_id"] = oa_id
        changed = True
    if item.get("openalex_not_found"):
        item["openalex_not_found"] = False
        changed = True
    return changed


def backfill(items: list[dict], dry_run: bool = True, refresh: bool = False, sleep_s: float = 0.15) -> tuple[int, int]:
    """Run the OpenAlex backfill over registry items. Returns (fetched, changed)."""
    fetched = 0
    changed = 0
    for item in items:
        doi = item.get("doi")
        if not doi:
            continue
        if not refresh and (item.get("openalex_id") or item.get("openalex_not_found")):
            continue

        work = fetch_openalex_work(doi)
        fetched += 1
        if dry_run:
            status = work.get("cited_by_count", "not-found") if work else "not-found"
            print(f"  would set {item.get('slug')}: cited_by_count={status}")
        elif apply_work_to_item(item, work):
            changed += 1
            if work:
                print(f"  {item.get('slug')}: cited_by_count={work.get('cited_by_count')}")
            else:
                print(f"  {item.get('slug')}: not found in OpenAlex")
        if sleep_s > 0:
            time.sleep(sleep_s)
    return fetched, changed


def main() -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "OpenAlex backfill").splitlines()[0])
    parser.add_argument("--dry-run", action="store_true", help="report without writing")
    parser.add_argument("--refresh", action="store_true", help="refetch items with existing metadata")
    parser.add_argument("--sleep", type=float, default=0.15, help="seconds between API calls")
    args = parser.parse_args()

    if not REGISTRY_PATH.exists():
        print(f"ERROR: {REGISTRY_PATH} not found")
        return 1

    with open(REGISTRY_PATH, encoding="utf-8") as f:
        registry = json.load(f)
    items = registry.get("content", [])

    fetched, changed = backfill(items, dry_run=args.dry_run, refresh=args.refresh, sleep_s=args.sleep)
    mode = "[dry-run] " if args.dry_run else ""
    print(f"{mode}OpenAlex backfill: fetched {fetched}, changed {changed} of {len(items)} items")

    if changed and not args.dry_run:
        # ensure_ascii=False keeps literal unicode (matches the repo's format);
        # the registry already contains non-ASCII characters (em-dashes etc.)
        serialized = json.dumps(registry, indent=2, ensure_ascii=False)
        BACKUP_PATH.write_text(serialized, encoding="utf-8")
        with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
            f.write(serialized)
        print(f"Registry written; backup at {BACKUP_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
