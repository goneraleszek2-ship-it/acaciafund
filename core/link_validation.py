"""Shared dead-link detection for auto-ingested content and news."""

from __future__ import annotations

import concurrent.futures
import re
import urllib.error
import urllib.request
from typing import Any

_HREF_RE = re.compile(r"""href\s*=\s*["']([^"']+)["']""", re.IGNORECASE)

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AcaciaFund-NewsBot/3.0 "
    "(https://www.acaciafund.org; admin@acaciafund.org)"
)


def normalize_url(url: str) -> str:
    return url.split("#", 1)[0].split("?", 1)[0].rstrip("/")


def is_dead_url(url: str, timeout: int = 6) -> bool:
    """Return True only for definitive 404/410 responses (HEAD, then GET)."""
    if not url.startswith(("http://", "https://")):
        return False
    last_code: int | None = None
    for method in ("HEAD", "GET"):
        try:
            req = urllib.request.Request(
                url,
                method=method,
                headers={"User-Agent": USER_AGENT, "Accept": "*/*"},
            )
            with urllib.request.urlopen(req, timeout=timeout):
                return False
        except urllib.error.HTTPError as exc:
            last_code = exc.code
        except Exception:
            return False
    return last_code in (404, 410)


def dead_urls(urls: list[str], workers: int = 8) -> set[str]:
    unique = sorted({normalize_url(url) for url in urls if url})
    if not unique:
        return set()
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        return {url for url, dead in zip(unique, pool.map(is_dead_url, unique)) if dead}


def extract_urls_from_html(html: str) -> list[str]:
    return _HREF_RE.findall(html or "")


def _item_urls(item: dict[str, Any], url_key: str, html_key: str | None) -> set[str]:
    urls: set[str] = set()
    raw = item.get(url_key)
    if isinstance(raw, str) and raw:
        urls.add(normalize_url(raw))
    if html_key:
        for href in extract_urls_from_html(str(item.get(html_key) or "")):
            if href:
                urls.add(normalize_url(href))
    urls.discard("")
    return urls


def filter_dead_items(
    items: list[dict[str, Any]],
    url_key: str = "url",
    html_key: str | None = None,
    workers: int = 8,
) -> list[dict[str, Any]]:
    candidates: set[str] = set()
    for item in items:
        candidates.update(_item_urls(item, url_key, html_key))
    dead = dead_urls(sorted(candidates), workers)
    if not dead:
        return items
    return [item for item in items if not (_item_urls(item, url_key, html_key) & dead)]
