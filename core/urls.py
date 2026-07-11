"""Pure URL helper functions for AcaciaFund.

These functions map between internal pillar keys, URL segments, filesystem paths,
and canonical URLs. They are dependency-free (only imports config.py) so they can
be imported safely by tests without triggering heavy module-level computation.
"""

import re

from config import PILLAR_URL_MAP, PILLAR_URL_REVERSE, SITE_URL


def slug_to_path(slug: str) -> str:
    """Convert a slug to an output file path (e.g. 'foo/bar' → 'foo/bar/index.html')."""
    return f"{slug}/index.html" if "/" in slug else f"{slug}.html"


def slug_to_fspath(slug: str) -> str:
    """Map internal slug to filesystem path using URL segments.

    e.g. 'aml/research/foo' → 'compliance/research/foo'
         'aml/learn/foo'    → 'compliance/learn/foo'
         'knowledge/foo'    → 'knowledge/foo' (unchanged)
    """
    parts = slug.split("/", 1)
    if len(parts) == 2:
        url_pillar = PILLAR_URL_MAP.get(parts[0], parts[0])
        return f"{url_pillar}/{parts[1]}"
    return slug


def canonical_path(slug_or_path: str) -> str:
    """Normalize a path for canonical URLs: strip /index.html, enforce trailing slash."""
    path = slug_or_path.replace("/index.html", "/").replace(".html", "/")
    if not path.endswith("/"):
        path += "/"
    return path


def slug_to_url(slug: str) -> str:
    """Convert a slug to a full canonical URL."""
    return f"{SITE_URL}/{canonical_path(slug_to_path(slug_to_fspath(slug)))}"


def pillar_to_url(pillar: str) -> str:
    """Map internal pillar key to URL segment (e.g. 'stock' → 'markets')."""
    return PILLAR_URL_MAP.get(pillar, pillar)


def url_to_pillar(url_seg: str) -> str:
    """Map URL segment back to internal pillar key (e.g. 'markets' → 'stock')."""
    return PILLAR_URL_REVERSE.get(url_seg, url_seg)
