#!/usr/bin/env python3
"""
Offline internal link auditor for the AcaciaFund static site.

Outputs:
  - Console summary (total links, broken count)
  - JSON report at data/broken_links.json (for the repair step)
"""

import json
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse

DIST_DIR = Path("/root/acaciafund/dist")
REPORT_PATH = Path("/root/acaciafund/data/broken_links.json")

# Known static redirects (source -> target)
REDIRECTS = {
    "/science/": "/data/research/",
    "/contact/": "/knowledge/contact/",
}

# Base site URL (used only for external link detection)
SITE_URL = (
    "https://acaciafund.example.com"  # placeholder; actual value not used for same-origin check
)


def read_text(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def extract_links(html: str, base_url: str) -> list[str]:
    """Return list of raw href values from <a> and <link> tags."""
    # Simple regex – sufficient for our controlled templates
    pattern = r'<(?:a|link)[^>]*\bhref=["\']([^"\']*)["\'][^>]*>'
    return re.findall(pattern, html, flags=re.IGNORECASE)


def normalize_link(link: str, page_url: str) -> str | None:
    """
    Resolve a link to an absolute path within the site.
    Returns None for external (non‑same‑origin) links or mailto: etc.
    """
    if not link or link.startswith(("mailto:", "tel:", "javascript:")):
        return None
    # Absolute URL?
    if link.startswith(("http://", "https://")):
        parsed = urlparse(link)
        # Treat as internal only if same netloc as SITE_URL
        if parsed.netloc == urlparse(SITE_URL).netloc:
            # treat as path only
            path = parsed.path
            if parsed.query:
                path += "?" + parsed.query
            return path.lstrip("/")
        return None
    # Root‑relative
    if link.startswith("/"):
        # Apply static redirects
        for src, dst in REDIRECTS.items():
            if link.startswith(src):
                link = dst + link[len(src) :]
                break
        # Ensure trailing slash for directory‑like paths unless a file extension
        if not link.endswith("/") and "." not in link.split("/")[-1]:
            link += "/"
        return link.lstrip("/")  # relative to site root
    # Relative to current page
    if not link.startswith(("./", "../")):
        link = "./" + link
    resolved = urljoin(page_url, link)
    # Normalize again (remove ../, ./)
    while "/../" in resolved:
        # Remove the segment before ../
        _ = re.split(r"(/?)", resolved, maxsplit=1)
        # Simpler: use regex substitution
        resolved = re.sub(r"[^/]+/\.\./", "", resolved)
    resolved = resolved.replace("./", "")
    if not resolved.endswith("/") and "." not in resolved.split("/")[-1]:
        resolved += "/"
    return resolved


def is_valid_path(link_path: str) -> bool:
    """
    Check whether the resolved link corresponds to an existing file.
    We treat a path ending with '/' as a directory → look for index.html.
    """
    if link_path.endswith("/"):
        target = DIST_DIR / (link_path + "index.html")
    else:
        target = DIST_DIR / link_path
    return target.is_file()


def audit() -> dict:
    broken = []
    total = 0
    for html_file in DIST_DIR.rglob("*.html"):
        rel = html_file.relative_to(DIST_DIR)
        page_url = "/" + str(rel)  # e.g. /blog/post.html
        html = read_text(html_file)
        for raw in extract_links(html, page_url):
            total += 1
            norm = normalize_link(raw, page_url)
            if norm is None:
                # external – ignore
                continue
            if not is_valid_path(norm):
                broken.append(
                    {
                        "source_file": str(rel),
                        "source_url": page_url,
                        "broken_link": raw,
                        "resolved_path": norm,
                    }
                )
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        json.dumps(
            {
                "total_internal_links": total,
                "broken_count": len(broken),
                "broken_links": broken,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    # Console summary
    print("\n=== Internal Link Audit ===")
    print(f"Scanned {len(list(DIST_DIR.rglob('*.html')))} HTML files")
    print(f"Total internal links examined: {total}")
    print(f"Broken links: {len(broken)}")
    if broken:
        print("\nFirst 10 broken entries:")
        for entry in broken[:10]:
            print(
                f"  [{entry['source_file']}] → {entry['broken_link']} (resolves to {entry['resolved_path']})"
            )
    else:
        print("\n✅ No broken internal links found.")
    return {
        "total_internal_links": total,
        "broken_count": len(broken),
        "broken_links": broken,
    }


if __name__ == "__main__":
    audit()
