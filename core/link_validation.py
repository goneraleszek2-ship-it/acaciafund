"""Shared dead-link detection for auto-ingested content and news."""

from __future__ import annotations

import concurrent.futures
import urllib.error
import urllib.request
from typing import Any

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


def filter_dead_items(
    items: list[dict[str, Any]], url_key: str = "url", workers: int = 8
) -> list[dict[str, Any]]:
    dead = dead_urls([str(item.get(url_key, "")) for item in items], workers)
    if not dead:
        return items
    return [
        item
        for item in items
        if normalize_url(str(item.get(url_key, ""))) not in dead
    ]
