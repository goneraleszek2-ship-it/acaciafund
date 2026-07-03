"""Image-to-article semantic validation layer.

Ensures every fetched image has demonstrable semantic overlap with its
target article before the path is committed to the registry. If validation
fails, the asset is rejected and the pipeline falls back to fractal SVG
generation.
"""

from __future__ import annotations

import re
from pathlib import Path

_STOP_WORDS: set[str] = {
    "the",
    "this",
    "that",
    "from",
    "with",
    "into",
    "over",
    "which",
    "what",
    "when",
    "where",
    "analysis",
    "context",
    "overview",
    "findings",
    "primary",
    "signal",
    "summary",
    "connections",
    "cross",
    "pillar",
    "methodology",
    "notes",
    "classification",
    "scenario",
    "applied",
    "source",
    "domain",
    "breakdown",
    "technology",
    "finance",
    "regulatory",
    "academic",
    "industry",
    "healthcare",
    "defense",
    "policy",
    "sentiment",
    "distribution",
    "coverage",
    "diversity",
    "relevance",
    "temporal",
    "key",
    "main",
    "top",
    "core",
    "deep",
    "next",
    "new",
    "for",
    "and",
    "are",
    "but",
    "not",
    "you",
    "all",
    "can",
    "had",
    "her",
    "was",
    "one",
    "our",
    "out",
    "has",
    "his",
    "how",
    "its",
    "may",
    "now",
    "old",
    "see",
    "way",
    "who",
    "did",
    "get",
    "let",
    "say",
    "she",
    "too",
    "use",
    "also",
    "just",
    "than",
    "them",
    "been",
    "have",
    "more",
    "some",
    "very",
    "your",
    "about",
    "would",
    "there",
    "their",
    "these",
    "other",
    "could",
    "after",
    "first",
    "being",
    "under",
    "between",
}


def extract_article_terms(article: dict) -> set[str]:
    """Extract meaningful, non-stop-word terms from slug, tags, and title.

    Returns a set of lower-cased, stripped terms that can be compared
    against an image file stem for overlap.
    """
    slug: str = article.get("slug", "")
    tags: list[str] = article.get("tags", [])
    title: str = article.get("title", "")

    terms: set[str] = set()

    for part in slug.lower().replace("/", " ").replace("-", " ").split():
        part = part.strip()
        if part and len(part) > 2 and part not in _STOP_WORDS:
            terms.add(part)

    for tag in tags:
        for word in tag.lower().replace("-", " ").replace("_", " ").split():
            word = word.strip()
            if word and len(word) > 2 and word not in _STOP_WORDS:
                terms.add(word)

    for w in re.findall(r"[A-Z][a-z]{2,}", title):
        wl = w.lower()
        if wl not in _STOP_WORDS:
            terms.add(wl)

    return terms


def validate_image_for_article(article: dict, image_url: str) -> bool:
    """Verify semantic overlap between an image file stem and the article.

    At least one meaningful (non-stop-word) term extracted from the
    article's slug, tags, or title must appear verbatim in the image
    filename stem.

    Returns ``True`` when the image is acceptable, ``False`` when it
    should be rejected (deleted from disk, ``featured_image = ""``).
    """
    if not image_url:
        return False

    stem = Path(image_url).stem.lower()

    article_terms = extract_article_terms(article)
    if not article_terms:
        return True  # nothing to compare -> allow (edge case)

    return any(term in stem for term in article_terms)
