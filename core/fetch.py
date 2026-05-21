import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .data import ALGOLIA_URL, USER_AGENT, HN_DISCUSSION_URL, log, extract_domain

CACHE_DIR = Path(__file__).parent.parent / ".cache"
CACHE_DIR.mkdir(exist_ok=True)


def _request(url: str, timeout: int = 20, max_retries: int = 3) -> str | None:
    """HTTP GET z retry i exponential backoff."""
    last_err = None
    for attempt in range(1, max_retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = resp.read().decode("utf-8", errors="replace")
            # slow-read guard: jeśli w 20s nie dostaliśmy całego body → timeout
            if not data:
                raise OSError("Empty response")
            return data
        except (urllib.error.URLError, urllib.error.HTTPError, OSError, json.JSONDecodeError) as e:
            last_err = e
            if attempt < max_retries:
                wait = 2 ** attempt
                log(f"Retry {attempt}/{max_retries} za {wait}s: {e}", ok=False)
                time.sleep(wait)
    log(f"Błąd po {max_retries} próbach: {last_err}", ok=False)
    return None


def _cached_request(url: str, cache_key: str, ttl_hours: int = 24) -> str | None:
    """HTTP GET z cache dyskowym."""
    cache_path = CACHE_DIR / f"{cache_key}.json"
    now = time.time()

    # sprawdź cache
    if cache_path.exists():
        age_hours = (now - cache_path.stat().st_mtime) / 3600
        if age_hours < ttl_hours:
            with open(cache_path) as f:
                cached = json.load(f)
                if cached.get("url") == url:
                    return cached.get("data")

    # fresh fetch
    data = _request(url)
    if data is not None:
        with open(cache_path, "w") as f:
            json.dump({"url": url, "ts": now, "data": data}, f)
    return data


def fetch_hn_stories(target_date: datetime | None = None,
                     since_hours: int | None = None,
                     min_points: int = 2,
                     max_hits: int = 1000,
                     use_cache: bool = False) -> list[dict]:
    """Fetch HN stories dla konkretnego dnia LUB ostatnich N godzin."""
    if target_date:
        day_start = int(target_date.replace(hour=0, minute=0, second=0, tzinfo=timezone.utc).timestamp())
        day_end = int((target_date.replace(hour=23, minute=59, second=59, tzinfo=timezone.utc)).timestamp())
        nf = f"created_at_i>={day_start},created_at_i<={day_end}"
        cache_key = f"hn_{target_date.strftime('%Y-%m-%d')}"
    elif since_hours:
        since_ts = int((datetime.now(timezone.utc) - timedelta(hours=since_hours)).timestamp())
        nf = f"created_at_i>{since_ts}"
        cache_key = f"hn_since{since_hours}h"
    else:
        return []

    params = {"query": "", "tags": "story", "hitsPerPage": max_hits, "numericFilters": nf}
    url = f"{ALGOLIA_URL}?{urllib.parse.urlencode(params)}"

    raw = _cached_request(url, cache_key, ttl_hours=24) if use_cache else _request(url)
    if raw is None:
        return []

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return []

    stories = []
    for hit in data.get("hits", []):
        title = (hit.get("title") or "").strip()
        if not title:
            continue
        points = hit.get("points", 0) or 0
        if points < min_points:
            continue
        object_id = hit.get("objectID", "")
        hn_url = HN_DISCUSSION_URL.format(object_id) if object_id else ""
        raw_url = hit.get("url") or hn_url
        stories.append({
            "title": title, "url": raw_url, "hn_url": hn_url,
            "points": points, "created_at": hit.get("created_at", ""),
            "author": hit.get("author", ""), "object_id": object_id,
        })

    stories.sort(key=lambda s: s["points"], reverse=True)
    return stories


# ── arXiv ──

ARXIV_CATEGORIES = {
    "aml": ["q-fin.GN", "q-fin.RM", "cs.CY", "cs.CR"],
    "stock": ["q-fin.ST", "q-fin.PM", "cs.AR", "cs.ET"],
    "science": ["q-bio.MN", "cs.NE", "cs.CC", "nlin.AO", "nlin.CG"],
}

ARXIV_KEYWORDS = {
    "aml": ["money laundering", "compliance", "financial regulation", "fraud detection",
            "blockchain", "cryptocurrency", "financial crime", "risk management"],
    "stock": ["semiconductor", "supply chain", "market microstructure", "asset pricing",
              "volatility", "portfolio", "valuation", "chip"],
    "science": ["mitochondria", "cybernetics", "complex systems", "network theory",
                "emergence", "self-organization", "bioenergetics", "cognitive"],
}


def _parse_arxiv_xml(xml: str) -> list[dict]:
    """Parse arXiv XML na słowniki używając xml.etree (nie regex)."""
    import xml.etree.ElementTree as ET
    ns = {"atom": "http://www.w3.org/2005/Atom",
          "arxiv": "http://arxiv.org/schemas/atom"}
    entries = []
    try:
        root = ET.fromstring(xml)
    except ET.ParseError:
        return []
    for entry in root.findall("atom:entry", ns):
        title_el = entry.find("atom:title", ns)
        summary_el = entry.find("atom:summary", ns)
        link_el = entry.find("atom:id", ns)
        published_el = entry.find("atom:published", ns)
        if title_el is None or link_el is None:
            continue
        categories = [c.get("term", "") for c in entry.findall("atom:category", ns)]
        entries.append({
            "title": re.sub(r"\s+", " ", (title_el.text or "").strip()),
            "url": (link_el.text or "").strip().rstrip("/"),
            "abstract": re.sub(r"\s+", " ", (summary_el.text or "")[:200].strip()),
            "published": (published_el.text or "").strip() if published_el is not None else "",
            "categories": categories,
        })
    return entries


def fetch_arxiv(since_hours: int = 72, max_results: int = 100) -> list[dict]:
    """Fetch recent papers z arXiv API."""
    # ARXIV_CATEGORIES i ARXIV_KEYWORDS zdefiniowane w tym module poniżej
    since = datetime.now(timezone.utc) - timedelta(hours=since_hours)
    all_cats = [c for cats in ARXIV_CATEGORIES.values() for c in cats]
    query_str = "cat:" + "+OR+cat:".join(urllib.parse.quote(c, safe="") for c in all_cats)
    url = f"http://export.arxiv.org/api/query?search_query={query_str}&sortBy=submittedDate&sortOrder=descending&max_results={max_results}"

    xml = _request(url, timeout=30)
    if xml is None:
        return []

    parsed = _parse_arxiv_xml(xml)

    # klasyfikuj
    papers = []
    for p in parsed:
        full_text = (p["title"] + " " + p["abstract"][:500]).lower()
        paper_scores = []
        for pillar, kws in ARXIV_KEYWORDS.items():
            score = sum(3 for kw in kws if kw in full_text)
            for cat in p["categories"]:
                if cat in ARXIV_CATEGORIES.get(pillar, []):
                    score += 5
            if score > 0:
                paper_scores.append((pillar, score))
        if not paper_scores:
            continue
        best = max(paper_scores, key=lambda x: x[1])
        papers.append({
            "title": p["title"],
            "url": p["url"],
            "abstract": p["abstract"],
            "pillar": best[0],
            "score": best[1],
            "published": p["published"],
            "categories": p["categories"],
        })
    papers.sort(key=lambda p: p["score"], reverse=True)
    return papers
