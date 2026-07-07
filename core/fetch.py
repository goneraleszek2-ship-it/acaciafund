import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

from .data import ALGOLIA_URL, HN_DISCUSSION_URL, USER_AGENT, log, write_dlq

CACHE_DIR = Path(__file__).parent.parent / ".cache"
CACHE_DIR.mkdir(exist_ok=True)


def _request(url: str, timeout: int = 20, max_retries: int = 3) -> str | None:
    """HTTP GET with retry and exponential backoff."""
    last_err = None
    for attempt in range(1, max_retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data: str = resp.read().decode("utf-8", errors="replace")
            if not data:
                raise OSError("Empty response")
            return data
        except (urllib.error.URLError, urllib.error.HTTPError, OSError) as e:
            last_err = e
            if attempt < max_retries:
                wait = 2**attempt
                log(f"Retry {attempt}/{max_retries} in {wait}s: {e}", ok=False)
                time.sleep(wait)
    log(f"Error after {max_retries} attempts: {last_err}", ok=False)
    return None


def _cached_request(url: str, cache_key: str, ttl_hours: int = 24) -> str | None:
    """HTTP GET z cache dyskowym."""
    cache_path = CACHE_DIR / f"{cache_key}.json"
    now = time.time()

    # check cache
    if cache_path.exists():
        age_hours = (now - cache_path.stat().st_mtime) / 3600
        if age_hours < ttl_hours:
            with open(cache_path) as f:
                cached: dict[str, Any] = json.load(f)
                if cached.get("url") == url:
                    data = cached.get("data")
                    if isinstance(data, str):
                        return data

    # fresh fetch
    data = _request(url)
    if data is not None:
        with open(cache_path, "w") as f:
            json.dump({"url": url, "ts": now, "data": data}, f)
    return data


def fetch_hn_stories(
    target_date: datetime | None = None,
    since_hours: int | None = None,
    min_points: int = 2,
    max_hits: int = 1000,
    use_cache: bool = False,
) -> list[dict]:
    """Fetch HN stories dla konkretnego dnia LUB ostatnich N godzin."""
    if target_date:
        day_start = int(
            target_date.replace(hour=0, minute=0, second=0, tzinfo=timezone.utc).timestamp()
        )
        day_end = int(
            (target_date.replace(hour=23, minute=59, second=59, tzinfo=timezone.utc)).timestamp()
        )
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
        write_dlq(
            "hn",
            url,
            "All retries exhausted",
            {"since_hours": since_hours, "min_points": min_points},
        )
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
        stories.append(
            {
                "title": title,
                "url": raw_url,
                "hn_url": hn_url,
                "points": points,
                "created_at": hit.get("created_at", ""),
                "author": hit.get("author", ""),
                "object_id": object_id,
            }
        )

    stories.sort(key=lambda s: s["points"], reverse=True)
    return stories


# ── arXiv ──

ARXIV_CATEGORIES = {
    "aml": [
        "q-fin.GN", "q-fin.RM", "cs.CY", "cs.CR", "q-fin.PM", "q-fin.EC",
        "cs.IR", "stat.AP", "q-fin.ST", "cs.SI", "cs.MA", "cs.GT",
        "q-fin.MF", "q-fin.CP", "q-fin.RM", "q-fin.TR",
    ],
    "stock": ["q-fin.ST", "q-fin.PM", "cs.AR", "cs.ET", "cs.CE", "eess.SP"],
    "data-engineering": [
        "cs.DB",
        "cs.DC",
        "cs.DS",
        "cs.IR",
        "cs.SE",
        "cs.PF",
        "cs.ET",
        "cs.LG",
        "stat.ML",
        "stat.CO",
        "stat.AP",
    ],
}

ARXIV_KEYWORDS = {
    "aml": [
        "money laundering",
        "compliance",
        "financial regulation",
        "fraud detection",
        "blockchain",
        "cryptocurrency",
        "financial crime",
        "risk management",
        "aml",
        "kyc",
        "sanctions",
        "transaction monitoring",
        "suspicious activity",
        "beneficial ownership",
        "shell company",
        "trade based money laundering",
        "entity resolution",
        "financial intelligence",
        "regtech",
        "correspondent banking",
        "travel rule",
        "virtual asset",
        "politically exposed",
        "adverse media",
        "sar filing",
        "ctr reporting",
        "watchlist screening",
    ],
    "stock": [
        "semiconductor",
        "supply chain",
        "market microstructure",
        "asset pricing",
        "volatility",
        "portfolio",
        "valuation",
        "chip",
        "supply chain resilience",
        "inventory management",
        "logistics",
        "procurement",
        "operations research",
    ],
    "data-engineering": [
        "data pipeline",
        "etl",
        "elt",
        "data lake",
        "data warehouse",
        "data lakehouse",
        "data quality",
        "data lineage",
        "data catalog",
        "data mesh",
        "data product",
        "data contract",
        "orchestration",
        "workflow",
        "dag",
        "stream processing",
        "batch processing",
        "apache spark",
        "apache flink",
        "apache kafka",
        "apache beam",
        "iceberg",
        "delta lake",
        "parquet",
        "arrow",
        "duckdb",
        "dbt",
        "dagster",
        "airflow",
        "prefect",
        "data engineering",
        "dataops",
        "mlops",
        "feature store",
        "data observability",
        "analytics engineering",
        "sql",
        "schema",
        "data platform",
    ],
}


def _parse_arxiv_xml(xml: str) -> list[dict]:
    """Parse arXiv XML into dicts using xml.etree (not regex)."""
    import xml.etree.ElementTree as ET

    ns = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
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
        title_text = title_el.text or ""
        link_text = link_el.text or ""
        summary_text = summary_el.text or "" if summary_el is not None else ""
        entries.append(
            {
                "title": re.sub(r"\s+", " ", title_text.strip()),
                "url": link_text.strip().rstrip("/"),
                "abstract": re.sub(r"\s+", " ", summary_text[:200].strip()),
                "published": (published_el.text or "").strip() if published_el is not None else "",
                "categories": categories,
            }
        )
    return entries


def fetch_arxiv(since_hours: int = 72, max_results: int = 100) -> list[dict]:
    """Fetch recent papers from arXiv API."""
    # ARXIV_CATEGORIES and ARXIV_KEYWORDS defined in this module below
    datetime.now(timezone.utc) - timedelta(hours=since_hours)
    all_cats = [c for cats in ARXIV_CATEGORIES.values() for c in cats]
    query_str = "cat:" + "+OR+cat:".join(urllib.parse.quote(c, safe="") for c in all_cats)
    url = f"http://export.arxiv.org/api/query?search_query={query_str}&sortBy=submittedDate&sortOrder=descending&max_results={max_results}"

    xml = _request(url, timeout=30)
    if xml is None:
        write_dlq(
            "arxiv",
            url,
            "All retries exhausted",
            {"since_hours": since_hours, "max_results": max_results},
        )
        return []

    parsed = _parse_arxiv_xml(xml)

    # classify
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
        papers.append(
            {
                "title": p["title"],
                "url": p["url"],
                "abstract": p["abstract"],
                "pillar": best[0],
                "score": best[1],
                "published": p["published"],
                "categories": p["categories"],
            }
        )
    papers.sort(key=lambda p: p["score"], reverse=True)
    return papers


def fetch_pubmed(since_hours: int = 168, max_results: int = 50) -> list[dict]:
    """Fetch recent biomedical papers from PubMed (free, no key required).

    NCBI Policy: Max 3 requests per second, delay between requests.
    """
    import time

    # Calculate date range
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(hours=since_hours)
    date_str = f"{start_date.strftime('%Y/%m/%d')}:{end_date.strftime('%Y/%m/%d')}[dp]"

    # Base URL for E-utilities
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"

    # Search for general biomedical topics relevant to our pillars
    # Using broad terms to capture interdisciplinary work
    query_terms = [
        "mitochondria",
        "cybernetics",
        "complex systems",
        "network theory",
        "emergence",
        "self-organization",
        "bioenergetics",
        "cognitive",
        "neuroscience",
        "artificial intelligence",
        "machine learning",
        "financial technology",
        "blockchain",
        "risk management",
    ]

    # Take a subset to avoid overly long queries
    query = " OR ".join(query_terms[:8])

    params = {
        "db": "pubmed",
        "term": f"({query}) AND ({date_str})",
        "retmax": max_results,
        "retmode": "json",
        "sort": "relevance",
    }

    # Respect NCBI rate limit: max 3 requests per second
    time.sleep(0.34)  # ~3 requests per second

    url = f"{base_url}?{urllib.parse.urlencode(params)}"
    raw = _request(url, timeout=30)

    if raw is None:
        write_dlq(
            "pubmed",
            url,
            "All retries exhausted",
            {"since_hours": since_hours, "max_results": max_results, "step": "search"},
        )
        return []

    try:
        data = json.loads(raw)
        id_list = data.get("esearchresult", {}).get("idlist", [])

        if not id_list:
            return []

        # Fetch details for the IDs
        return _fetch_pubmed_details(id_list)
    except (json.JSONDecodeError, KeyError):
        return []


def _fetch_pubmed_details(id_list: list[str]) -> list[dict]:
    """Fetch detailed records for PubMed IDs."""
    import time

    if not id_list:
        return []

    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

    # Process in batches to avoid URL length limits
    batch_size = 200
    all_papers = []

    for i in range(0, len(id_list), batch_size):
        batch_ids = id_list[i : i + batch_size]

        params = {"db": "pubmed", "id": ",".join(batch_ids), "retmode": "xml"}

        # Rate limiting
        time.sleep(0.34)

        url = f"{base_url}?{urllib.parse.urlencode(params)}"
        xml_data = _request(url, timeout=30)

        if xml_data:
            papers = _parse_pubmed_xml(xml_data)
            all_papers.extend(papers)
        else:
            write_dlq(
                "pubmed", url, "Batch fetch failed", {"step": "details", "batch_ids": batch_ids}
            )

    return all_papers


def _parse_pubmed_xml(xml: str) -> list[dict]:
    """Parse PubMed XML into standardized format."""
    try:
        root = ET.fromstring(xml)
    except ET.ParseError:
        return []

    papers = []

    for article in root.findall(".//PubmedArticle"):
        try:
            # Extract basic info
            title_elem = article.find(".//ArticleTitle")
            title = " ".join(title_elem.itertext()).strip() if title_elem is not None else ""

            # Get PMID for URL
            pmid_elem = article.find(".//PMID")
            pmid = pmid_elem.text if pmid_elem is not None else ""
            url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else ""

            # Get abstract
            abstract_elem = article.find(".//AbstractText")
            abstract = (
                " ".join(abstract_elem.itertext()).strip() if abstract_elem is not None else ""
            )

            # Get publication date
            pub_date_elem = article.find(".//PubDate")
            published = ""
            if pub_date_elem is not None:
                year_elem = pub_date_elem.find("Year")
                month_elem = pub_date_elem.find("Month")
                day_elem = pub_date_elem.find("Day")

                year = year_elem.text or "1900" if year_elem is not None else "1900"
                month = month_elem.text or "01" if month_elem is not None else "01"
                day = day_elem.text or "01" if day_elem is not None else "01"

                # Handle month names
                month_map = {
                    "Jan": "01",
                    "Feb": "02",
                    "Mar": "03",
                    "Apr": "04",
                    "May": "05",
                    "Jun": "06",
                    "Jul": "07",
                    "Aug": "08",
                    "Sep": "09",
                    "Oct": "10",
                    "Nov": "11",
                    "Dec": "12",
                }
                month = month_map.get(month, month)
                if len(month) == 1:
                    month = month.zfill(2)

                published = f"{year}-{month}-{day}"

            # Get authors
            authors = []
            for author in article.findall(".//Author"):
                lastname = author.find("LastName")
                firstname = author.find("ForeName") or author.find("Initials")
                if lastname is not None and firstname is not None:
                    authors.append(f"{firstname.text} {lastname.text}")

            author_str = ", ".join(authors[:3])  # Limit to first 3 authors
            if len(authors) > 3:
                author_str += " et al."

            if not title or not url:
                continue

            papers.append(
                {
                    "title": title,
                    "url": url,
                    "abstract": abstract[:500],  # Limit abstract length
                    "published": published,
                    "author": author_str,
                    "source": "pubmed",
                }
            )
        except Exception:
            # Skip malformed entries
            continue

    return papers


def fetch_semantic_scholar(since_hours: int = 168, max_results: int = 50) -> list[dict]:
    """Fetch papers from Semantic Scholar API.

    Searches for recent papers across AML, finance, and science domains.
    Free tier: 100 requests/day without API key.
    With SEMANTIC_SCHOLAR_API_KEY set: higher rate limits.
    """
    api_key = os.environ.get("SEMANTIC_SCHOLAR_API_KEY")
    headers = {"Accept": "application/json"}
    if api_key:
        headers["x-api-key"] = api_key

    papers: list[dict] = []
    queries = [
        "anti-money laundering compliance",
        "financial crime regulation",
        "semiconductor supply chain",
        "artificial intelligence industry",
        "quantum computing",
        "gene therapy CRISPR",
        "climate technology",
        "data engineering pipeline",
    ]
    fields = "title,url,publicationDate,authors,venue,citationCount,abstract"
    per_query = max(1, max_results // len(queries))

    for query in queries:
        url = (
            f"https://api.semanticscholar.org/graph/v1/paper/search"
            f"?query={urllib.parse.quote(query)}"
            f"&limit={per_query}"
            f"&fields={fields}"
            f"&year=2025-"
        )
        data = _cached_request(url, f"semantic_{query[:20].replace(' ', '_')}", ttl_hours=12)
        if not data:
            continue
        try:
            resp = json.loads(data)
            for paper in resp.get("data", []):
                pub_date = paper.get("publicationDate") or ""
                if pub_date:
                    try:
                        pub = datetime.fromisoformat(pub_date)
                        if (datetime.now(timezone.utc) - pub).total_seconds() > since_hours * 3600:
                            continue
                    except ValueError:
                        pass
                title = paper.get("title", "")
                if not title:
                    continue
                papers.append(
                    {
                        "title": title,
                        "url": paper.get("url", ""),
                        "published": pub_date,
                        "author": (paper.get("authors") or [{}])[0].get("name", "")
                        if paper.get("authors")
                        else "",
                        "abstract": (paper.get("abstract") or "")[:500],
                        "venue": paper.get("venue", ""),
                        "citations": paper.get("citationCount", 0),
                        "source": "semantic_scholar",
                    }
                )
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            log(f"Semantic Scholar parse error: {e}", ok=False)
            continue

    log(f"Fetched {len(papers)} papers from Semantic Scholar ({len(queries)} queries)")
    return papers[:max_results]


# Update ARXIV_CATEGORIES to include more relevant sections
# Expanding beyond current categories to capture more interdisciplinary work
