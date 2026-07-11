"""Check for broken internal links in generated HTML and report high-SQI items.

Usage:
    python3 scripts/check_links_and_sqi.py [--dist-dir dist]

Exit codes:
    0 - all links OK, no high-SQI surprises
    1 - broken links found
"""
import argparse
import json
import re
import sys
from pathlib import Path


def extract_internal_links(html: str) -> set[str]:
    """Extract href paths from HTML that look like internal links."""
    links = set()
    for match in re.finditer(r'href="(/[^"]*?)"', html):
        path = match.group(1)
        # Skip static, images, anchors, common non-page assets
        if (path.startswith("/static") or path.startswith("/images")
                or "#" in path or path in ("/favicon.ico", "/robots.txt", "/sitemap.xml")):
            continue
        # Strip query params and anchors
        path = path.split("?")[0].split("#")[0]
        links.add(path)
    return links


def check_links(dist_dir: Path) -> list[str]:
    """Check all HTML files for broken internal links."""
    html_files = list(dist_dir.rglob("*.html"))
    existing_paths = {"/"}  # Root always exists
    for f in html_files:
        rel = f.relative_to(dist_dir)
        path_str = "/" + str(rel).replace("/index.html", "").replace(".html", "")
        if path_str != "/":
            existing_paths.add(path_str)
        # Also register without trailing slash variations
        existing_paths.add(path_str.rstrip("/"))

    broken = []
    checked = 0
    for f in html_files:
        html = f.read_text(encoding="utf-8", errors="ignore")
        links = extract_internal_links(html)
        for link in links:
            checked += 1
            # Normalize
            normalized = link.rstrip("/") or "/"
            if normalized not in existing_paths:
                # Check common patterns
                if normalized + "/" in existing_paths:
                    continue
                # Skip admin pages (they're single-page apps)
                if link.startswith("/admin/"):
                    continue
                # Skip tags with special chars ($ etc) — these are slugified
                if "/tags/$" in link or "/tags/%" in link:
                    continue
                rel_file = f.relative_to(dist_dir)
                broken.append(f"{rel_file}: broken link -> {link}")

    return broken


def check_high_sqi(dist_dir: Path, threshold: float = 0.85) -> list[dict]:
    """Find pages with very high SQI scores that should be verified."""
    high_sqi = []
    for f in dist_dir.rglob("index.html"):
        html = f.read_text(encoding="utf-8", errors="ignore")
        # Look for SQI badge values
        for match in re.finditer(r'data-sqi="([\d.]+)"', html):
            sqi = float(match.group(1))
            if sqi >= threshold:
                rel = f.relative_to(dist_dir)
                high_sqi.append({
                    "file": str(rel),
                    "sqi": sqi,
                })
    return high_sqi


def check_external_references(dist_dir: Path) -> dict[str, list[str]]:
    """Extract unique external URLs referenced across the site."""
    external = {}
    for f in dist_dir.rglob("*.html"):
        html = f.read_text(encoding="utf-8", errors="ignore")
        for match in re.finditer(r'href="(https?://[^"]+)"', html):
            url = match.group(1)
            if "acaciafund.org" not in url:
                external.setdefault(url, []).append(str(f.relative_to(dist_dir)))
    return external


def main():
    parser = argparse.ArgumentParser(description="Check links and SQI")
    parser.add_argument("--dist-dir", default="dist", help="Output directory")
    parser.add_argument("--sqi-threshold", type=float, default=0.85)
    args = parser.parse_args()

    dist_dir = Path(args.dist_dir)
    if not dist_dir.exists():
        print(f"ERROR: {dist_dir} does not exist")
        sys.exit(1)

    html_count = len(list(dist_dir.rglob("*.html")))
    print(f"Checking {html_count} HTML files in {dist_dir}/")

    # Check internal links
    broken = check_links(dist_dir)
    if broken:
        print(f"\nBROKEN LINKS ({len(broken)} found):")
        for b in broken[:20]:
            print(f"  {b}")
        if len(broken) > 20:
            print(f"  ... and {len(broken) - 20} more")
    else:
        print("\nAll internal links OK")

    # Check high-SQI pages
    high_sqi = check_high_sqi(dist_dir, args.sqi_threshold)
    if high_sqi:
        print(f"\nHIGH-SQI PAGES ({len(high_sqi)} found, threshold={args.sqi_threshold}):")
        for item in sorted(high_sqi, key=lambda x: -x["sqi"])[:10]:
            print(f"  {item['file']}: SQI={item['sqi']:.3f}")
    else:
        print(f"\nNo pages above SQI threshold {args.sqi_threshold}")

    # External reference stats
    external = check_external_references(dist_dir)
    print(f"\nEXTERNAL REFERENCES: {len(external)} unique URLs across {sum(len(v) for v in external.values())} pages")

    # Write report
    report = {
        "html_count": html_count,
        "broken_count": len(broken),
        "broken_links": broken[:50],
        "high_sqi_count": len(high_sqi),
        "high_sqi_pages": sorted(high_sqi, key=lambda x: -x["sqi"])[:20],
        "external_url_count": len(external),
    }
    report_path = dist_dir / "link-check-report.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nReport written to {report_path}")

    if broken:
        sys.exit(1)


if __name__ == "__main__":
    main()
