import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import tomllib

BASE_DIR = Path(__file__).parent.parent
CONFIG_PATH = BASE_DIR / "etc" / "pillars.toml"
CONTENT_DIR = BASE_DIR / "content" / "en" / "blog"
STATIC_DIR = BASE_DIR / "static" / "images"
THUMB_DIR = STATIC_DIR / "thumbs"

ALGOLIA_URL = "https://hn.algolia.com/api/v1/search"
USER_AGENT = "AcaciaFund/3.0"
HN_DISCUSSION_URL = "https://news.ycombinator.com/item?id={}"

with open(CONFIG_PATH, "rb") as _f:
    _cfg = tomllib.load(_f)

PILLARS: dict[str, dict] = {}
for _name, _p in _cfg["pillars"].items():
    PILLARS[_name] = {
        "label": _p["label"],
        "emoji": _p["emoji"],
        "folder": BASE_DIR / _p["folder"],
        "tags": _p["tags"],
        "description": _p["description"],
        "keywords": _p["keywords"],
        "domain_scores": _p["domain_scores"],
    }

DOMAIN_TAXONOMY: dict[str, set[str]] = {}
for _cat, _domains in _cfg["domain_taxonomy"].items():
    DOMAIN_TAXONOMY[_cat] = set(_domains)

KNOWN_ENTITIES: dict[str, set[str]] = {}
for _pname, _e in _cfg["entities"].items():
    KNOWN_ENTITIES[_pname] = set(_e["values"])
ALL_ENTITIES = set().union(*KNOWN_ENTITIES.values())

ENTITY_DEFS: dict[str, str] = _cfg.get("entity_defs", {})

_SOURCE_TIER_SCORES = {
    "high": 1.0,
    "medium_high": 0.8,
    "medium": 0.6,
    "low": 0.4,
}
SOURCE_TIERS: list[tuple[re.Pattern, float]] = []
for _tier_name, _patterns in _cfg["source_tiers"].items():
    _score = _SOURCE_TIER_SCORES.get(_tier_name, 0.3)
    for _pat in _patterns:
        SOURCE_TIERS.append((re.compile(_pat), _score))

STOP_WORDS = {
    "the",
    "a",
    "an",
    "of",
    "in",
    "to",
    "for",
    "and",
    "is",
    "on",
    "that",
    "with",
    "from",
    "by",
    "at",
    "its",
    "it",
    "as",
    "are",
    "be",
    "has",
    "have",
    "was",
    "were",
    "new",
    "how",
    "why",
    "what",
    "show",
    "ask",
    "tell",
    "this",
    "we",
    "our",
    "their",
    "they",
    "not",
    "no",
    "but",
    "all",
    "about",
    "up",
    "out",
    "over",
    "after",
    "into",
    "than",
    "then",
    "also",
    "just",
    "more",
}

DOMAIN_PATTERNS: dict[str, list[tuple[re.Pattern, int]]] = {}
for _pname, _config in PILLARS.items():
    DOMAIN_PATTERNS[_pname] = [
        (re.compile(re.escape(d)), s) for d, s in _config["domain_scores"].items()
    ]

KEYWORD_PATTERNS: dict[str, list[re.Pattern]] = {}
for _pname, _config in PILLARS.items():
    KEYWORD_PATTERNS[_pname] = [
        re.compile(rf"\b{re.escape(kw)}\b", re.I) for kw in _config["keywords"]
    ]


def log(msg: str, ok: bool = True) -> None:
    prefix = "[+]" if ok else "[-]"
    print(f"{prefix} {msg}", file=sys.stderr)


def extract_domain(url: str) -> str:
    m = re.search(r"https?://([^/]+)", url)
    return m.group(1).lower() if m else ""


def categorize_domain(domain: str) -> str:
    for cat, domains in DOMAIN_TAXONOMY.items():
        if any(d in domain for d in domains):
            return cat
    return "other"


def extract_entities(text: str) -> list[str]:
    text_lower = text.lower()
    found = []
    for ent in sorted(ALL_ENTITIES, key=len, reverse=True):
        if ent.lower() in text_lower:
            found.append(ent)
    return found[:5]


def extract_themes(titles: list[str]) -> list[str]:
    words: list[str] = []
    for t in titles:
        cleaned = re.sub(r"[^a-z\s]", " ", t.lower())
        words.extend(w for w in cleaned.split() if len(w) > 3 and w not in STOP_WORDS)
    counts = Counter(words)
    return [w.capitalize() for w, _ in counts.most_common(5)]


# ── Dead-Letter Queue ──

DLQ_DIR = BASE_DIR / ".dlq"


def write_dlq(source: str, url: str, error: str, context: dict | None = None) -> None:
    """Write a failed fetch attempt to the dead-letter queue.

    Args:
        source: Source name (e.g. 'hn', 'arxiv', 'pubmed').
        url: The URL that failed.
        error: Error message.
        context: Optional metadata (params, response snippet, etc.).
    """
    DLQ_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")
    filename = f"{source}_{ts}.json"
    entry = {
        "source": source,
        "url": url,
        "error": str(error),
        "timestamp": ts,
        "context": context or {},
    }
    (DLQ_DIR / filename).write_text(json.dumps(entry, indent=2, default=str), encoding="utf-8")
    log(f"DLQ: {filename} written for {source}", ok=False)
