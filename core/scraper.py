import json
import re
import time
import hashlib
import urllib.request
import urllib.error
from html.parser import HTMLParser
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

CACHE_FILE = Path(__file__).parent.parent / "static" / "api" / "scraped.json"
USER_AGENT = "AcaciaFund/3.0 (research aggregator; leszek@example.com)"
REQUEST_TIMEOUT = 15
MAX_WORKERS = 4
CACHE_TTL_DAYS = 7
MAX_TEXT_LEN = 5000


class _TextExtractor(HTMLParser):
    """Extract clean text from HTML, focusing on <p> and <article> content."""
    def __init__(self):
        super().__init__()
        self._text: list[str] = []
        self._skip = 0
        self._in_p = False
        self._p_text: list[str] = []

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag in ("script", "style", "noscript", "nav", "header", "footer"):
            self._skip += 1
        elif tag == "p" and not self._skip:
            self._in_p = True
            self._p_text = []

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in ("script", "style", "noscript", "nav", "header", "footer"):
            if self._skip:
                self._skip -= 1
        elif tag == "p" and self._in_p:
            self._in_p = False
            text = "".join(self._p_text).strip()
            if len(text) > 40 and not any(
                kw in text.lower() for kw in
                ["cookie", "privacy policy", "sign up", "subscribe", "newsletter",
                 "all rights reserved", "accept", "reject", "navigation", "menu",
                 "search", "log in", "log out", "register", "advertisement"]
            ):
                self._text.append(text)

    def handle_data(self, data):
        if self._skip:
            return
        if self._in_p:
            self._p_text.append(data.strip())

    def text(self) -> str:
        if not self._text:
            return ""
        return " ".join(self._text)


def _url_key(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()[:12]


def _load_cache() -> dict:
    if CACHE_FILE.exists():
        try:
            return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _save_cache(cache: dict):
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(
        json.dumps(cache, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )


def _fetch_article(url: str) -> str | None:
    """Fetch and extract clean text from a single article URL."""
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": USER_AGENT, "Accept": "text/html,text/plain"},
        )
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            html = resp.read().decode("utf-8", errors="replace")
        extractor = _TextExtractor()
        extractor.feed(html)
        text = extractor.text()
        if len(text) < 100:
            return None
        return text[:MAX_TEXT_LEN]
    except (urllib.error.HTTPError, urllib.error.URLError, OSError, ValueError):
        return None


def _extract_facts(text: str) -> dict:
    """Extract structured facts from article text."""
    from collections import Counter

    facts: dict = {
        "sentences": [],
        "names": [],
    }

    # Sentences — now from clean <p> text
    for m in re.finditer(r"([A-Z][^.!?]{40,250}[.!?])", text):
        s = m.group(1).strip()
        if len(s) > 40 and len(s) < 250:
            if not any(kw in s.lower() for kw in [
                "cookie", "privacy", "subscribe", "newsletter",
                "all rights", "accept", "navigation",
            ]):
                facts["sentences"].append(s)

    # Named entities: org-like multi-word phrases
    # Heuristic: contains an org-indicating word (Corp, Inc, LLC, Ltd, Bank, Fund,
    #   University, Institute, Agency, Commission, Authority, Foundation, etc.)
    #   OR follows "{Name} {Verb}" pattern suggesting a company/person
    org_indicators = {
        "bank", "fund", "capital", "corp", "inc", "llc", "ltd", "gmbh",
        "university", "institute", "school", "college", "laboratory", "lab",
        "agency", "commission", "authority", "administration", "department",
        "foundation", "society", "association", "organization", "centre",
        "center", "group", "holdings", "partners", "ventures", "studio",
        "studio", "limited", "corporation", "company", "co",
        "federal", "national", "global", "international", "european",
        "software", "systems", "technologies", "networks", "solutions",
        "platform", "protocol", "network", "alliance", "council",
        "ministry", "office", "bureau", "division", "committee",
        "republic", "kingdom", "state", "government",
        "digital", "capital", "assets", "management",
        "research", "science", "health", "defense",
    }
    for m in re.finditer(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})\b", text):
        name = m.group(1)
        tokens = name.split()
        if any(t.lower() in org_indicators for t in tokens):
            facts["names"].append(name)

    return facts


def scrape_articles(urls: list[str], max_scrape: int = 120) -> dict[str, dict]:
    """Scrape articles, return {url_key: {text, facts, url}}.
    Only scrapes up to `max_scrape` uncached articles per call.
    """
    cache = _load_cache()
    now = time.time()
    ttl = CACHE_TTL_DAYS * 86400

    # Determine which URLs need scraping
    to_scrape = []
    result: dict[str, dict] = {}
    for url in urls:
        key = _url_key(url)
        cached = cache.get(key, {})
        if cached and (now - cached.get("ts", 0)) < ttl and len(cached.get("text", "")) > 50:
            result[key] = cached
        else:
            to_scrape.append((key, url))

    if not to_scrape:
        return result

    # Only scrape first N uncached (most recent/high-priority)
    to_scrape = to_scrape[:max_scrape]

    # Scrape in parallel
    fresh: dict[str, dict] = {}
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        fut_map = {pool.submit(_fetch_article, url): (key, url) for key, url in to_scrape}
        for fut in as_completed(fut_map):
            key, url = fut_map[fut]
            try:
                text = fut.result(timeout=20)
                if text:
                    facts = _extract_facts(text)
                    entry = {
                        "url": url,
                        "text": text,
                        "facts": facts,
                        "ts": now,
                    }
                    fresh[key] = entry
                    cache[key] = entry
            except Exception:
                pass

    _save_cache(cache)
    result.update(fresh)
    return result
