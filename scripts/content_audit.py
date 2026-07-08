#!/usr/bin/env python3
"""Live-site content audit for acaciafund.org.

Crawls the deployed sitemap, fetches each content page, runs technical and
editorial checks, and writes a JSON result file for report synthesis.

Usage:  python scripts/content_audit.py
"""

import json
import re
import sys
import time
import uuid
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import lxml.html
import requests

SITE = "https://www.acaciafund.org"
SITEMAP_URL = f"{SITE}/sitemap.xml"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
REGISTRY_PATH = PROJECT_ROOT / "registry.json"
BUILD_META_PATH = PROJECT_ROOT / "dist" / "build-meta.json"
OUTPUT_PATH = PROJECT_ROOT / "tmp" / "audit_results.json"
MAX_WORKERS = 6
REQUEST_TIMEOUT = 15
USER_AGENT = "AcaciaAudit/1.0 (content assessment bot)"

CACHE_DIR = PROJECT_ROOT / "tmp" / "audit_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": USER_AGENT})
SESSION.headers.update({"Accept": "text/html,application/xhtml+xml,application/xml"})

# URLs to exclude from deep analysis (archive/listing pages)
EXCLUDE_URLS = {
    "/",
    "/tags/",
    "/search/",
    "/graph/",
    "/research/",
    "/learn/",
    "/knowledge/",
}


def _fetch(url: str) -> str | None:
    """Fetch a URL and return text, with caching to disk."""
    cache_key = uuid.uuid5(uuid.NAMESPACE_URL, url).hex
    cache_path = CACHE_DIR / cache_key
    if cache_path.exists():
        return cache_path.read_text(encoding="utf-8")
    try:
        resp = SESSION.get(url, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        text = resp.text
        cache_path.write_text(text, encoding="utf-8")
        return text
    except requests.RequestException as e:
        print(f"  [WARN] Failed to fetch {url}: {e}", file=sys.stderr)
        return None


def _maybe_int(v: Any) -> int | None:
    try:
        return int(v)
    except (ValueError, TypeError):
        return None


def parse_sitemap(xml_text: str) -> list[str]:
    """Extract all <loc> URLs from sitemap XML."""
    return re.findall(r"<loc>(.*?)</loc>", xml_text)


def classify_url(url: str) -> dict[str, str | bool]:
    """Classify a URL into content_type, pillar, and excludability."""
    path = url.replace(SITE, "").rstrip("/")
    p = path.lower()

    is_excluded = path in EXCLUDE_URLS or p.startswith("/tags/")

    if path.startswith("/blog/") or path.startswith("/knowledge/"):
        # Knowledge pages and blog posts
        ct = "knowledge" if path.startswith("/knowledge/") else "research"
    elif path.startswith("/learn/"):
        ct = "learn"
    elif path.startswith("/docs/"):
        ct = "docs"
    elif path in ("/cybernetic-manifesto", "/cybernetic-manifesto/"):
        ct = "manifesto"
    elif p.startswith("/aml-core-foundations") or p.startswith("/market-core-foundations") or p.startswith("/data-core-foundations"):
        ct = "foundations"
    elif p.startswith("/graph"):
        ct = "graph"
    else:
        ct = "other"

    # Pillar inference from URL
    if "/aml" in p or "aml" in p.split("/"):
        pillar = "aml"
    elif "/stock" in p or "/market" in p or "stock" in p:
        pillar = "markets"
    elif "/data" in p or "data-engin" in p or "arrow" in p or "debezium" in p or "flink" in p:
        pillar = "data-engineering"
    elif "/science" in p:
        pillar = "science"
    else:
        pillar = "unknown"

    return {"content_type": ct, "pillar": pillar, "excluded": is_excluded}


def extract_meta(html_text: str, url: str) -> dict[str, Any]:
    """Extract metadata from an HTML page."""
    doc = lxml.html.fromstring(html_text.encode())
    result: dict[str, Any] = {"url": url}

    # Title
    title_el = doc.find(".//title")
    result["title"] = (title_el.text or "").strip() if title_el is not None else ""
    result["title_length"] = len(result["title"])

    # Meta description
    desc = doc.xpath("//meta[@name='description']/@content")
    result["meta_description"] = desc[0].strip() if desc else ""
    result["meta_description_length"] = len(result["meta_description"])

    # Canonical
    canon = doc.xpath("//link[@rel='canonical']/@href")
    result["canonical"] = canon[0] if canon else ""

    # OG image
    ogi = doc.xpath("//meta[@property='og:image']/@content")
    result["og_image"] = ogi[0] if ogi else ""
    result["og_image_has"] = bool(result["og_image"])

    # JSON-LD count
    jsonld = doc.xpath("//script[@type='application/ld+json']")
    result["jsonld_count"] = len(jsonld)

    # Body text extraction
    body = doc.find(".//body")
    body_text = ""
    if body is not None:
        for tag in (".//script", ".//style", ".//nav", ".//footer", ".//header"):
            for el in body.findall(tag):
                el.drop_tree()
        body_text = re.sub(r"\s+", " ", (body.text_content() or "")).strip()
    result["body_text_sample"] = body_text[:500]
    result["word_count"] = len(body_text.split())

    # Date found in page
    date_match = re.search(r"(\d{4}-\d{2}-\d{2})", body_text)
    result["date_found"] = date_match.group(1) if date_match else ""

    # Artifact/hallucination scan
    result["has_unrendered_template"] = bool(re.search(r"\{\{.*?\}\}", body_text))
    result["has_placeholder"] = bool(
        re.search(r"(?i)\b(todo|tbd|lorem ipsum|\[placeholder\]|\[todo\]|under construction)\b", body_text)
    )

    # Internal links
    internal_links: set[str] = set()
    external_links: set[str] = set()
    for a in doc.iterfind(".//a"):
        href = a.get("href", "").strip()
        if not href or href.startswith("#") or href.startswith("mailto:"):
            continue
        if href.startswith(SITE):
            href = href.replace(SITE, "")
        if href.startswith("/"):
            internal_links.add(href.rstrip("/"))
        elif href.startswith("http"):
            external_links.add(href)
    result["internal_links"] = sorted(internal_links)
    result["external_links"] = sorted(external_links)

    return result


def load_registry_lookup() -> dict[str, dict[str, Any]]:
    """Build slug → metadata lookup from local registry.json."""
    if not REGISTRY_PATH.exists():
        print("  [WARN] registry.json not found, skipping registry cross-ref")
        return {}
    raw = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    lookup: dict[str, dict[str, Any]] = {}
    for item in raw.get("content", []):
        slug = item.get("slug", "")
        if not slug:
            continue
        lookup[slug] = {
            "slug": slug,
            "title": item.get("title", ""),
            "content_type": item.get("content_type", ""),
            "pillar": item.get("pillar", ""),
            "tags": item.get("tags", []),
            "date_str": item.get("date_str", ""),
            "signals": item.get("signals", {}),
        }
    return lookup


def load_build_meta() -> dict[str, Any]:
    if BUILD_META_PATH.exists():
        return json.loads(BUILD_META_PATH.read_text(encoding="utf-8"))
    return {}


def slug_from_url(url: str) -> str:
    path = url.replace(SITE, "").strip("/")
    return path


def main() -> None:
    print("=== AcaciaFund Live Content Audit ===", file=sys.stderr)

    sitemap_xml = _fetch(SITEMAP_URL)
    if not sitemap_xml:
        print("FATAL: Could not fetch sitemap.", file=sys.stderr)
        sys.exit(1)

    all_urls = parse_sitemap(sitemap_xml)
    print(f"Sitemap: {len(all_urls)} URLs", file=sys.stderr)

    # Classify
    classified = [(u, classify_url(u)) for u in all_urls]
    content_urls = [u for u, c in classified if not c["excluded"]]
    excluded_urls = [u for u, c in classified if c["excluded"]]
    print(f"Content URLs: {len(content_urls)}, Excluded: {len(excluded_urls)}", file=sys.stderr)

    # Load local cross-references
    registry_lookup = load_registry_lookup()
    build_meta = load_build_meta()
    print(f"Registry entries: {len(registry_lookup)}", file=sys.stderr)

    # Fetch all content pages concurrently
    pages: list[dict[str, Any]] = []
    fetched = 0
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        fut_map = {pool.submit(_fetch, url): url for url in content_urls}
        for fut in as_completed(fut_map):
            url = fut_map[fut]
            html = fut.result()
            fetched += 1
            if fetched % 25 == 0:
                print(f"  Fetched {fetched}/{len(content_urls)}", file=sys.stderr)
            if html is None:
                pages.append({"url": url, "fetch_error": True})
                continue
            meta = extract_meta(html, url)
            pages.append(meta)

    print(f"Fetched: {fetched} pages", file=sys.stderr)

    # ── Analysis ──────────────────────────────────────────────────
    results: dict[str, Any] = {
        "scan_timestamp": datetime.now(timezone.utc).isoformat(),
        "sitemap_url_count": len(all_urls),
        "content_url_count": len(content_urls),
        "excluded_url_count": len(excluded_urls),
        "pages_fetched": len(pages),
        "fetch_errors": [p["url"] for p in pages if p.get("fetch_error")],
        "registry_entry_count": len(registry_lookup),
    }

    good_pages = [p for p in pages if not p.get("fetch_error")]

    # Build URL→page lookup
    url_to_page: dict[str, dict] = {p["url"]: p for p in good_pages}

    # 1. Content type / pillar counts
    ct_counts: Counter = Counter()
    pillar_counts: Counter = Counter()
    for p in good_pages:
        cls = classify_url(p["url"])
        ct_counts[cls["content_type"]] += 1
        pillar_counts[cls["pillar"]] += 1
    results["content_type_counts"] = dict(ct_counts.most_common())
    results["pillar_counts"] = dict(pillar_counts.most_common())

    # 2. Registry reconciliation
    deployed_slugs = {slug_from_url(p["url"]) for p in good_pages}
    registry_slugs = set(registry_lookup.keys())
    results["registry_not_deployed"] = sorted(registry_slugs - deployed_slugs)
    results["deployed_not_in_registry"] = sorted(
        deployed_slugs - registry_slugs - {""}  # homepage
    )

    # 3. Duplicate detection — by normalized title
    title_groups: dict[str, list[dict]] = defaultdict(list)
    for p in good_pages:
        norm = re.sub(r"[^a-z0-9]+", " ", p.get("title", "").lower()).strip()
        if len(norm) > 20:
            title_groups[norm].append(p)
    duplicates_by_title = {k: v for k, v in title_groups.items() if len(v) > 1}
    results["duplicates_by_title"] = {
        k: [{"url": p["url"], "title": p.get("title", "")} for p in v]
        for k, v in duplicates_by_title.items()
    }

    # 4. Duplicate detection — by body hash (first 800 chars)
    body_groups: dict[str, list[dict]] = defaultdict(list)
    for p in good_pages:
        body = p.get("body_text_sample", "")[:800]
        h = re.sub(r"\s+", "", body)
        if len(h) > 100:
            body_groups[h].append(p)
    # Only keep meaningful duplicates
    duplicates_by_body = {}
    for h, group in body_groups.items():
        distinct_urls = {p["url"] for p in group}
        if len(distinct_urls) > 1 and h:
            duplicates_by_body[h[:20]] = [
                {"url": p["url"], "title": p.get("title", "")} for p in group
            ]
    results["duplicates_by_body"] = duplicates_by_body

    # 5. SEO/metadata gaps
    seo_issues: list[dict[str, Any]] = []
    for p in good_pages:
        issues: list[str] = []
        t = p.get("title", "")
        if not t:
            issues.append("missing_title")
        elif len(t) > 65:
            issues.append(f"title_too_long:{len(t)}")
        elif len(t) < 15:
            issues.append(f"title_too_short:{len(t)}")
        if not p.get("meta_description"):
            issues.append("missing_meta_description")
        elif len(p.get("meta_description", "")) > 160:
            issues.append(f"meta_desc_too_long:{len(p['meta_description'])}")
        if not p.get("canonical"):
            issues.append("missing_canonical")
        if not p.get("og_image_has"):
            issues.append("missing_og_image")
        if p.get("jsonld_count", 0) == 0:
            issues.append("missing_jsonld")
        if issues:
            seo_issues.append({"url": p["url"], "title": t[:80], "issues": issues})
    results["seo_issues_count"] = len(seo_issues)
    results["seo_issues"] = seo_issues

    # 6. Word count / depth
    depth_tiers: dict[str, list[str]] = {"thin": [], "short": [], "adequate": [], "long": []}
    for p in good_pages:
        wc = p.get("word_count", 0)
        if wc < 200:
            depth_tiers["thin"].append(p["url"])
        elif wc < 500:
            depth_tiers["short"].append(p["url"])
        elif wc < 1500:
            depth_tiers["adequate"].append(p["url"])
        else:
            depth_tiers["long"].append(p["url"])
    results["depth_tiers"] = {k: {"count": len(v), "urls": v} for k, v in depth_tiers.items()}

    # 7. Template artifacts
    artifact_pages = [p["url"] for p in good_pages if p.get("has_unrendered_template")]
    placeholder_pages = [p["url"] for p in good_pages if p.get("has_placeholder")]
    results["unrendered_template_pages"] = artifact_pages
    results["placeholder_pages"] = placeholder_pages

    # 8. Freshness
    fresh: list[dict] = []
    stale: list[dict] = []
    for p in good_pages:
        d = p.get("date_found", "")
        if not d:
            continue
        try:
            dt = datetime.strptime(d, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            age = (datetime.now(timezone.utc) - dt).days
            entry = {"url": p["url"], "title": p.get("title", "")[:80], "date": d, "age_days": age}
            if age > 90:
                stale.append(entry)
            fresh.append(entry)
        except ValueError:
            pass
    results["freshness_total_dated"] = len(fresh)
    results["stale_over_90d"] = stale
    results["stale_count"] = len(stale)

    # 9. Broken internal links (check live)
    all_internal: dict[str, set[str]] = {}
    for p in good_pages:
        for link in p.get("internal_links", []):
            all_internal.setdefault(link, set()).add(p["url"])

    def _check_link(l: str) -> dict | None:
        if l.startswith("//") or not l.startswith("/"):
            return None
        full = f"{SITE}{l}"
        try:
            r = SESSION.head(full, timeout=10, allow_redirects=True)
            if r.status_code >= 400:
                return {"link": l, "status": r.status_code, "referrers": sorted(all_internal.get(l, []))}
        except requests.RequestException:
            return {"link": l, "status": -1, "referrers": sorted(all_internal.get(l, []))}
        return None

    print("  Checking internal links (HEAD)…", file=sys.stderr)
    broken_links: list[dict] = []
    links_to_check = sorted(all_internal.keys())
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        fut_map2 = {pool.submit(_check_link, l): l for l in links_to_check}
        for fut in as_completed(fut_map2):
            result = fut.result()
            if result is not None:
                broken_links.append(result)
    results["broken_links"] = broken_links
    results["broken_link_count"] = len(broken_links)

    # 10. Orphan pages
    referenced: set[str] = set()
    for p in good_pages:
        for link in p.get("internal_links", []):
            referenced.add(link)
    all_content_paths: set[str] = set()
    for p in good_pages:
        path = p["url"].replace(SITE, "").rstrip("/")
        if path:
            all_content_paths.add(path)
    orphan_paths = sorted(all_content_paths - referenced - {""})
    results["orphan_pages"] = orphan_paths
    results["orphan_count"] = len(orphan_paths)

    # 11. Registry metadata cross-ref
    registry_xref: dict[str, Any] = {"missing_in_registry": [], "pillar_mismatches": []}
    for p in good_pages:
        slug = slug_from_url(p["url"])
        reg = registry_lookup.get(slug)
        if reg is None:
            # Check without leading section
            alt_slug = slug.split("/", 1)[-1] if "/" in slug else slug
            reg = registry_lookup.get(alt_slug)
        if reg:
            cls = classify_url(p["url"])
            if cls["pillar"] != "unknown" and reg.get("pillar", ""):
                if cls["pillar"] != reg["pillar"]:
                    registry_xref["pillar_mismatches"].append(
                        {"url": p["url"], "url_pillar": cls["pillar"], "registry_pillar": reg["pillar"]}
                    )
        else:
            registry_xref["missing_in_registry"].append(p["url"])
    results["registry_cross_ref"] = registry_xref

    # 12. SQI from build-meta
    results["build_meta"] = {
        "duration_seconds": build_meta.get("duration_seconds"),
        "page_count": build_meta.get("page_count"),
        "sqi": build_meta.get("sqi"),
        "low_sqi_count": build_meta.get("quality", {}).get("low_sqi_count", 0),
        "low_sqi_items": build_meta.get("quality", {}).get("low_sqi_items", []),
    }

    # Write results
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
    print(f"\nResults written to {OUTPUT_PATH}", file=sys.stderr)

    # Print summary
    print(f"\n{'='*60}", file=sys.stderr)
    print("SUMMARY:", file=sys.stderr)
    print(f"  Content pages fetched: {len(good_pages)}", file=sys.stderr)
    print(f"  Fetch errors: {len(results['fetch_errors'])}", file=sys.stderr)

    # De-dupe groups
    dedupe_total = len(results.get("duplicates_by_title", {}))
    print(f"  Duplicate title groups: {dedupe_total}", file=sys.stderr)

    # De-dupe via body hash (only show body-hash duplicates not caught by title)
    dual_dedupes = 0
    dup_body_keys = set()
    for k, group in results.get("duplicates_by_body", {}).items():
        urls = {e["url"] for e in group}
        already = set()
        for dt_group in results.get("duplicates_by_title", {}).values():
            already.update(e["url"] for e in dt_group)
        if urls - already:
            dual_dedupes += 1
            dup_body_keys.update(urls)
    print(f"  Additional body-hash duplicate groups: {dual_dedupes}", file=sys.stderr)

    print(f"  SEO issues: {results['seo_issues_count']}", file=sys.stderr)
    print(f"  Broken internal links: {len(broken_links)}", file=sys.stderr)
    print(f"  Orphan pages: {len(orphan_paths)}", file=sys.stderr)
    print(f"  Stale (>90d): {len(stale)}", file=sys.stderr)
    print(f"  Thin pages (<200 words): {len(depth_tiers['thin'])}", file=sys.stderr)
    print(f"  Unrendered template artifacts: {len(artifact_pages)}", file=sys.stderr)
    print(f"  Placeholder text: {len(placeholder_pages)}", file=sys.stderr)
    print(f"{'='*60}", file=sys.stderr)


if __name__ == "__main__":
    main()
