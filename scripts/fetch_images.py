#!/usr/bin/env python3
"""
Fetch section-level images for AcaciaFund articles.

Pipeline: parse body_html by <h2> → compute break points by reading rhythm
→ build per-section contextual queries → query ALL backends in parallel
→ score candidates by relevance → pick best → download + WebP optimize
→ update registry.json → print ETL report.

4 backends: Openverse / NASA / Wikimedia Commons / Library of Congress
"""
import argparse
import hashlib
import json
import os
import re
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Any

import requests

# core/images is the visual management system — Tier 1 (manifest), Tier 2 (auto-fetch), Tier 3 (SVG fallback)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core.images import load_manifest, get_manifest_entry

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REGISTRY_PATH = PROJECT_ROOT / "registry.json"
IMAGES_DIR = PROJECT_ROOT / "static" / "images" / "generated"
USER_AGENT = "AcaciaFund/1.0 (image-fetcher; +https://acaciafund.org)"
RATE_LIMIT_DELAY = 0.15
MAX_WORKERS = 4
MIN_SCORE = 20
MAX_IMAGE_WIDTH = 1200
TARGET_WORDS_PER_IMAGE = 150

PILLAR_KEYWORDS = {
    "aml": "compliance regulation security audit financial crime",
    "stock": "market finance trading economy industry",
    "data-engineering": "data pipeline server architecture infrastructure",
    "science": "laboratory research experiment analysis",
}

SECTION_TYPES = {
    0: "overview",
    1: "key_findings",
    2: "applied_scenario",
    3: "source_analysis",
    4: "domain_breakdown",
    5: "cross_pillar",
    6: "methodology",
}

SECTION_QUERY_TEMPLATES = {
    "key_findings": "{entities} {pillar_context}",
    "applied_scenario": "{entities} {pillar_context}",
    "source_analysis": "{entities} {pillar_context}",
    "domain_breakdown": "{entities} {pillar_context}",
    "cross_pillar": "{entities} {pillar_context}",
    "methodology": "{entities} {pillar_context}",
}

PILLAR_CONTEXT_WORDS = {
    "aml": "compliance security financial regulation",
    "stock": "finance market trading investment",
    "data-engineering": "technology server data infrastructure",
    "science": "research laboratory analysis",
}

SECTION_PRIORITY = {
    1: "always",
    2: "always",
    3: "conditional",
    4: "conditional",
    5: "always",
    6: "conditional",
}

SECTION_WORD_MIN = {
    1: 0,
    2: 0,
    3: 120,
    4: 120,
    5: 0,
    6: 160,
}

CURATED_KNOWN = {
    # === COMPUTING & IT ===
    "eniac computer history computing": "File:ENIAC_Penn1.jpg",
    "server room data center": "File:Google data center.jpg",
    "data center server infrastructure": "File:Virginia Tech - data center.jpg",
    "semiconductor chip wafer fabrication": "File:Wafer 20110212.jpg",
    "circuit board electronics hardware": "File:Motherboard closeup.jpg",
    "programming code developer": "File:Programming code - Pair programming.jpg",
    "network cable ethernet connectivity": "File:Network switch.jpg",
    "cloud computing infrastructure": "File:Cloud computing.jpg",
    "artificial intelligence machine learning": "File:Artificial intelligence and robotics.jpg",
    "database sql query": "File:Database schema.jpg",
    "kafka streaming message queue": "File:Apache Kafka logo.png",
    "docker container kubernetes orchestration": "File:Docker logo (2013).svg",
    "python programming language": "File:Python logo and wordmark.svg",
    "git version control": "File:Git logo.svg",
    "linux operating system": "File:Tux.svg",
    "api rest http web service": "File:REST API.png",
    "cybersecurity hacking encryption": "File:Cybersecurity.jpg",
    "quantum computing": "File:Quantum computer - artist concept.jpg",

    # === FINANCE & MARKETS ===
    "nyse stock exchange trading wall street": "File:New York Stock Exchange August 2017 04.jpg",
    "treasury department government building": "File:United States Treasury Building.JPG",
    "federal reserve central bank": "File:Federal Reserve Bank Building (36344p).jpg",
    "trading floor commodities exchange": "File:Chicago Board Of Trade Building.jpg",
    "stock ticker market data": "File:Stock ticker.jpg",
    "wall street financial district": "File:Wall Street Sign.jpg",
    "bloomberg terminal finance": "File:Bloomberg Terminal.jpg",
    "stock market chart trading": "File:Stock market chart.svg",
    "cryptocurrency bitcoin blockchain": "File:Blockchain workflow.png",
    "bank vault security gold": "File:Bank vault.jpg",
    "financial audit accounting": "File:Financial audit.jpg",
    "investment portfolio diversification": "File:Investment portfolio.jpg",
    "forex currency exchange": "File:Foreign exchange market.jpg",
    "venture capital startup funding": "File:Venture capital funding.jpg",
    "pension fund retirement investing": "File:Pension fund management.jpg",
    "hedge fund quantitative trading": "File:Quantitative trading.jpg",
    "bond yield fixed income": "File:Bond market.jpg",
    "real estate investment trust": "File:Real estate investment.jpg",
    "commodities gold silver oil": "File:Commodities trading.jpg",
    "fintech digital banking": "File:Fintech digital banking.jpg",

    # === AML & COMPLIANCE ===
    "compliance regulation regulatory": "File:Us-treasury-building.jpg",
    "money laundering financial crime": "File:Money laundering prevention.jpg",
    "kyc know your customer verification": "File:KYC verification.jpg",
    "sanctions ofac embargoes": "File:OFAC sanctions compliance.jpg",
    "suspicious activity report sar": "File:SAR filing compliance.jpg",
    "beneficial ownership transparency": "File:Beneficial ownership registry.jpg",
    "anti corruption bribery": "File:Anti-corruption compliance.jpg",
    "financial intelligence unit": "File:Financial intelligence center.jpg",
    "risk assessment due diligence": "File:Risk assessment framework.jpg",
    "blockchain analytics tracing": "File:Blockchain analytics.jpg",
    "crypto mixer tumbling": "File:Cryptocurrency mixing service.jpg",
    "travel rule fatf": "File:FATF Travel Rule compliance.jpg",
    "decentralized finance defi": "File:DeFi decentralized finance.jpg",
    "stablecoin usdt usdc": "File:Stablecoin market.jpg",
    "binance crypto exchange": "File:Binance exchange.jpg",
    "wire transfer swift": "File:SWIFT payment system.jpg",

    # === DATA ENGINEERING ===
    "apache spark hadoop big data": "File:Apache Spark logo.png",
    "airflow workflow dag scheduling": "File:Apache Airflow logo.png",
    "snowflake data warehouse": "File:Snowflake logo.svg",
    "databricks lakehouse platform": "File:Databricks logo.svg",
    "dbt data build tool transformation": "File:dbt logo.svg",
    "kafka connect streaming": "File:Apache Kafka logo.png",
    "redis cache memory database": "File:Redis logo.svg",
    "elasticsearch search analytics": "File:Elasticsearch logo.svg",
    "terraform infrastructure code": "File:Terraform logo.svg",
    "grafana monitoring dashboard": "File:Grafana logo.svg",
    "prometheus monitoring": "File:Prometheus logo.svg",
    "apache flink stream processing": "File:Apache Flink logo.svg",
    "delta lake acid transactions": "File:Delta Lake logo.svg",
    "apache iceberg table format": "File:Apache Iceberg logo.svg",
    "apache hudi data lake": "File:Apache Hudi logo.svg",
    "great expectations data quality": "File:Great Expectations logo.svg",
    "prefect workflow orchestration": "File:Prefect logo.svg",
    "dagster data orchestration": "File:Dagster logo.svg",

    # === SUPPLY CHAIN & LOGISTICS ===
    "supply chain logistics shipping": "File:Container Ship at the Hai Phong International Container Terminal 03.jpg",
    "warehouse automation robotics": "File:Warehouse automation.jpg",
    "global trade import export": "File:Global trade shipping.jpg",

    # === SCIENCE & RESEARCH ===
    "laboratory research experiment": "File:Laboratory research.jpg",
    "genome dna sequencing": "File:DNA sequencing.jpg",
    "protein structure biology": "File:Protein structure visualization.jpg",
    "telescope astronomy space": "File:Telescope astronomy.jpg",
    "climate weather environmental": "File:Climate monitoring.jpg",
}

STOP_WORDS = {
    'the','this','that','from','with','into','over','which','what','when','where',
    'analysis','context','overview','findings','primary','signal','summary',
    'connections','cross','pillar','methodology','notes','classification',
    'scenario','applied','source','domain','breakdown','technology','finance',
    'regulatory','academic','industry','healthcare','defense','policy',
    'sentiment','distribution','coverage','diversity','relevance','temporal',
    'key','main','top','core','deep','next','new',
}


def strip_html(text: str) -> str:
    return re.sub(r'<[^>]+>', '', text).strip()


def word_count(text: str) -> int:
    return len(text.strip().split())


def extract_entities(text: str) -> list[str]:
    found = re.findall(r'[A-Z][a-zA-Z]+(?:\s[A-Z][a-zA-Z]+)*', text)
    seen = set()
    result = []
    for e in found:
        low = e.lower()
        if low not in seen and len(e) > 3 and low not in STOP_WORDS:
            seen.add(low)
            result.append(e)
    return result[:3]


def parse_sections(article: dict) -> list[dict]:
    body = article.get("body_html", "")
    if not body:
        return []
    h2_pattern = re.compile(r'<h2[^>]*>(.*?)</h2>\s*', re.IGNORECASE | re.DOTALL)
    parts = h2_pattern.split(body)
    sections = []
    for i in range(1, len(parts), 2):
        heading = strip_html(parts[i])
        content = parts[i + 1] if i + 1 < len(parts) else ""
        idx = (i - 1) // 2
        text_content = strip_html(content)
        entities = extract_entities(heading + " " + text_content[:200])
        sections.append({
            "section_index": idx,
            "heading": heading,
            "section_type": SECTION_TYPES.get(idx, "unknown"),
            "text_content": text_content,
            "word_count": word_count(text_content),
            "entities": entities,
        })
    return sections


def compute_break_points(sections: list[dict], article: dict) -> list[dict]:
    total_words = sum(s["word_count"] for s in sections if s["section_index"] > 0)
    target_count = max(1, round(total_words / TARGET_WORDS_PER_IMAGE))

    always = [s for s in sections if SECTION_PRIORITY.get(s["section_index"]) == "always" and s["word_count"] > 0]
    conditional = [s for s in sections if SECTION_PRIORITY.get(s["section_index"]) == "conditional"
                   and s["word_count"] >= SECTION_WORD_MIN.get(s["section_index"], 0)]

    # Fill target from always first (in order), then conditional
    selected: list[dict] = []
    for s in sorted(always, key=lambda x: x["section_index"]):
        if len(selected) < target_count:
            selected.append(s)
    if len(selected) < target_count:
        for s in sorted(conditional, key=lambda x: -x["word_count"]):
            if s not in selected and len(selected) < target_count:
                selected.append(s)

    return sorted(selected, key=lambda x: x["section_index"])


def build_section_query(section: dict, article: dict) -> str:
    title = article.get("title", "")
    tags = article.get("tags", [])
    pillar = article.get("pillar", "")
    pillar_kw = PILLAR_KEYWORDS.get(pillar, "")
    pillar_ctx = PILLAR_CONTEXT_WORDS.get(pillar, "")

    title_core = re.sub(r'^\d{4}\s+', '', title)
    title_core = re.sub(r'[:\-].*', '', title_core).strip()[:40]
    title_core = re.sub(r'\d{4}', '', title_core).strip()
    if not title_core:
        title_core = pillar_kw.split()[0] if pillar_kw else ""

    parts = [title_core]
    if tags:
        for tag in tags[:3]:
            tag_clean = tag.replace('-', ' ')
            if tag_clean.lower() not in title_core.lower():
                parts.append(tag_clean)
    query = " ".join(parts)
    terms = query.split()
    terms = [t for t in terms if len(t) > 2 and t.lower() not in STOP_WORDS]
    return " ".join(terms[:4])


def resolve_curated(article: dict) -> str | None:
    haystack = (article.get("title", "") + " " + " ".join(article.get("tags", []))).lower()
    body_text = strip_html(article.get("body_html", "")).lower()
    for phrase, filename in CURATED_KNOWN.items():
        keywords = phrase.split()
        if any(kw in haystack for kw in keywords) or any(kw in body_text for kw in keywords):
            return filename
    return None


def fetch_curated_commons(filename: str) -> dict | None:
    try:
        resp = requests.get("https://commons.wikimedia.org/w/api.php", params={
            "action": "query", "titles": filename,
            "prop": "imageinfo", "iiprop": "url|extmetadata",
            "iiurlwidth": 1200, "format": "json",
        }, headers={"User-Agent": USER_AGENT}, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        for pid, page in data.get("query", {}).get("pages", {}).items():
            if pid == "-1":
                continue
            info = page.get("imageinfo", [{}])[0]
            url = info.get("url", "")
            if not url:
                return None
            meta = info.get("extmetadata", {})
            license_name = "cc-by-sa"
            license_url = ""
            if "LicenseShortName" in meta:
                license_name = meta["LicenseShortName"].get("value", "cc-by-sa")
            if "LicenseUrl" in meta:
                license_url = meta["LicenseUrl"].get("value", "")
            artist = ""
            if "Artist" in meta:
                raw = meta["Artist"].get("value", "")
                artist = re.sub(r'<[^>]+>', '', raw).strip()[:80]
            return {
                "url": url,
                "title": page.get("title", "").replace("File:", "", 1),
                "creator": artist or "Wikimedia Commons",
                "license": license_name.lower().replace(" ", "-").replace("cc-", ""),
                "license_url": license_url,
            }
        return None
    except (requests.RequestException, json.JSONDecodeError):
        return None


def search_openverse(query: str) -> list[dict]:
    candidates = []
    try:
        resp = requests.get("https://api.openverse.engineering/v1/images/", params={
            "q": query, "license": "cc0,by", "license_type": "commercial",
            "size": "large", "aspect_ratio": "wide", "page_size": 5,
        }, headers={"User-Agent": USER_AGENT}, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        for r in data.get("results", []):
            url = r.get("url", "")
            if not url:
                continue
            candidates.append({
                "url": url,
                "title": r.get("title", ""),
                "tags": " ".join(t.get("name", "") for t in r.get("tags", [])),
                "creator": r.get("creator", ""),
                "license": r.get("license", ""),
                "license_url": r.get("license_url", ""),
                "source_api": "openverse",
            })
    except (requests.RequestException, json.JSONDecodeError):
        pass
    return candidates


def search_loc(query: str) -> list[dict]:
    candidates = []
    try:
        resp = requests.get("https://www.loc.gov/pictures/search/", params={
            "q": query, "fo": "json", "at": "pict", "c": 5, "display": "list",
        }, headers={"User-Agent": USER_AGENT}, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        for r in data.get("results", []):
            url = ""
            image_data = r.get("image", [])
            if isinstance(image_data, list) and image_data:
                url = image_data[0].get("full", "") or image_data[0].get("thumbnail", "")
            elif isinstance(image_data, dict):
                url = image_data.get("full", "") or image_data.get("thumbnail", "")
            if not url:
                continue
            candidates.append({
                "url": url,
                "title": r.get("title", ""),
                "tags": " ".join(r.get("subject", [])),
                "creator": r.get("contributor", [{}])[0].get("name", "") if r.get("contributor") else "",
                "license": "pd",
                "license_url": "https://www.loc.gov/free-to-use/",
                "source_api": "loc",
            })
    except (requests.RequestException, json.JSONDecodeError):
        pass
    return candidates


def search_nasa(query: str) -> list[dict]:
    candidates = []
    try:
        resp = requests.get("https://images-api.nasa.gov/search", params={
            "q": query, "media_type": "image",
        }, headers={"User-Agent": USER_AGENT}, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        for item in data.get("collection", {}).get("items", [])[:5]:
            links = item.get("links", [])
            if not links:
                continue
            url = links[0].get("href", "")
            if not url:
                continue
            meta = (item.get("data", [{}]) or [{}])[0]
            candidates.append({
                "url": url,
                "title": meta.get("title", ""),
                "tags": " ".join(meta.get("keywords", [])),
                "creator": "NASA",
                "license": "pd",
                "license_url": "https://www.nasa.gov/nasa-brand-center/images-and-media/",
                "source_api": "nasa",
            })
    except (requests.RequestException, json.JSONDecodeError):
        pass
    return candidates


def search_wikimedia(query: str) -> list[dict]:
    candidates = []
    try:
        sr = requests.get("https://commons.wikimedia.org/w/api.php", params={
            "action": "query", "list": "search", "srsearch": query,
            "srnamespace": 6, "srlimit": 5, "format": "json",
        }, headers={"User-Agent": USER_AGENT}, timeout=15)
        sr.raise_for_status()
        pages = sr.json().get("query", {}).get("search", [])
        if not pages:
            return candidates
        titles = "|".join(p["title"] for p in pages[:5])
        ii = requests.get("https://commons.wikimedia.org/w/api.php", params={
            "action": "query", "titles": titles, "prop": "imageinfo",
            "iiprop": "url|extmetadata", "iiurlwidth": 1200, "format": "json",
        }, headers={"User-Agent": USER_AGENT}, timeout=15)
        ii.raise_for_status()
        for pid, page in ii.json().get("query", {}).get("pages", {}).items():
            if pid == "-1":
                continue
            info = page.get("imageinfo", [{}])[0]
            url = info.get("url", "")
            if not url:
                continue
            meta = info.get("extmetadata", {})
            license_name = "cc-by-sa"
            license_url = ""
            if "LicenseShortName" in meta:
                license_name = meta["LicenseShortName"].get("value", "cc-by-sa")
            if "LicenseUrl" in meta:
                license_url = meta["LicenseUrl"].get("value", "")
            artist = ""
            if "Artist" in meta:
                raw = meta["Artist"].get("value", "")
                artist = re.sub(r'<[^>]+>', '', raw).strip()[:80]
            candidates.append({
                "url": url,
                "title": page.get("title", "").replace("File:", "", 1),
                "tags": page.get("title", "").replace("File:", "", 1),
                "creator": artist or "Wikimedia Commons",
                "license": license_name.lower().replace(" ", "-").replace("cc-", ""),
                "license_url": license_url,
                "source_api": "wikimedia",
            })
    except (requests.RequestException, json.JSONDecodeError):
        pass
    return candidates


ALL_BACKENDS: list[tuple[str, Any]] = [
    ("openverse", search_openverse),
    ("loc", search_loc),
    ("wikimedia", search_wikimedia),
    ("nasa", search_nasa),
]

# ── Optional paid/free backends (enabled via env vars) ──────────────

UNSPLASH_KEY = os.environ.get("UNSPLASH_ACCESS_KEY", "")
PEXELS_KEY = os.environ.get("PEXELS_API_KEY", "sk-1MeaqXGsG5HIVumC66vhWcsrcxk10rFeP9zaZIRfKhf8MmNIWmmhFnbnINyCrGTZ")
PIXABAY_KEY = os.environ.get("PIXABAY_API_KEY", "")


def search_unsplash(query: str) -> list[dict]:
    """Unsplash API — high-quality IT/finance photography. Free 50 req/hr."""
    if not UNSPLASH_KEY:
        return []
    candidates = []
    try:
        resp = requests.get("https://api.unsplash.com/search/photos", params={
            "query": query, "per_page": 5, "orientation": "landscape",
        }, headers={"Authorization": f"Client-ID {UNSPLASH_KEY}"}, timeout=15)
        resp.raise_for_status()
        for r in resp.json().get("results", []):
            url = r.get("urls", {}).get("regular", "")
            if not url:
                continue
            candidates.append({
                "url": url,
                "title": r.get("description", "") or r.get("alt_description", ""),
                "tags": " ".join(r.get("tags", [])),
                "creator": r.get("user", {}).get("name", ""),
                "license": "unsplash",
                "license_url": "https://unsplash.com/license",
                "source_api": "unsplash",
            })
    except (requests.RequestException, json.JSONDecodeError):
        pass
    return candidates


def search_pexels(query: str) -> list[dict]:
    """Pexels API — free 200 req/hr. Strong business/tech photos."""
    if not PEXELS_KEY:
        return []
    candidates = []
    try:
        resp = requests.get("https://api.pexels.com/v1/search", params={
            "query": query, "per_page": 5, "orientation": "landscape",
        }, headers={"Authorization": PEXELS_KEY}, timeout=15)
        resp.raise_for_status()
        for r in resp.json().get("photos", []):
            url = r.get("src", {}).get("large", "")
            if not url:
                continue
            candidates.append({
                "url": url,
                "title": r.get("alt", ""),
                "tags": query,
                "creator": r.get("photographer", ""),
                "license": "pexels",
                "license_url": "https://www.pexels.com/license/",
                "source_api": "pexels",
            })
    except (requests.RequestException, json.JSONDecodeError):
        pass
    return candidates


def search_pixabay(query: str) -> list[dict]:
    """Pixabay API — free 100 req/min. Has illustrations/vectors."""
    if not PIXABAY_KEY:
        return []
    candidates = []
    try:
        resp = requests.get("https://pixabay.com/api/", params={
            "key": PIXABAY_KEY, "q": query, "per_page": 5,
            "image_type": "photo", "orientation": "horizontal",
            "min_width": 800,
        }, timeout=15)
        resp.raise_for_status()
        for r in resp.json().get("hits", []):
            url = r.get("largeImageURL", "")
            if not url:
                continue
            candidates.append({
                "url": url,
                "title": r.get("tags", ""),
                "tags": r.get("tags", ""),
                "creator": r.get("user", ""),
                "license": "pixabay",
                "license_url": "https://pixabay.com/service/terms/",
                "source_api": "pixabay",
            })
    except (requests.RequestException, json.JSONDecodeError):
        pass
    return candidates


def generate_ai_illustration(prompt: str, dest: Path) -> tuple[bool, str, int, int, int]:
    """Pollinations.ai — free AI image generation. Fallback when no photo found."""
    try:
        safe_prompt = re.sub(r'[^a-zA-Z0-9 ]', '', prompt)[:200]
        url = f"https://gen.pollinations.ai/image/{safe_prompt}?model=flux&width=1200&height=675&nologo=true"
        resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=60)
        resp.raise_for_status()
        content = resp.content
        if not content or len(content) < 1000:
            return False, "", 0, 0, 0
        if HAS_PIL:
            img = Image.open(BytesIO(content))
            if img.mode == "RGBA":
                rgb = Image.new("RGB", img.size, (255, 255, 255))
                rgb.paste(img, mask=img.split()[3])
                img = rgb
            elif img.mode != "RGB":
                img = img.convert("RGB")
            if max(img.size) > MAX_IMAGE_WIDTH:
                ratio = MAX_IMAGE_WIDTH / max(img.size)
                new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
                img = img.resize(new_size, Image.LANCZOS)
            w, h = img.size
            output = BytesIO()
            img.save(output, format="WEBP", quality=85, method=6)
            data = output.getvalue()
            ext = ".webp"
        else:
            ct = resp.headers.get("content-type", "")
            ext = ".webp" if "webp" in ct else ".jpg"
            data = content
            w, h = 1200, 675
        dest_path = dest.with_suffix(ext)
        dest_path.write_bytes(data)
        return True, ext, w, h, len(data)
    except Exception:
        return False, "", 0, 0, 0


# ── Global dedup: track images used across all articles ──────────────
_GLOBAL_USED_URLS: set[str] = set()


def score_result(result: dict, query_terms: set[str]) -> float:
    text = (result.get("title", "") + " " + result.get("tags", "")).lower()
    if not query_terms:
        return 0.0
    matched = sum(1 for t in query_terms if t in text)
    match_score = (matched / len(query_terms)) * 100
    title_bonus = 15 if any(t in result.get("title", "").lower() for t in query_terms) else 0
    license_bonus = 10 if result.get("license") in ("pd", "cc0", "publicdomain") else 0
    return match_score + title_bonus + license_bonus


def normalize_query(query: str) -> tuple[set[str], str]:
    terms = set(re.findall(r'[a-z]+', query.lower()))
    terms.discard("the")
    terms.discard("and")
    terms.discard("for")
    terms.discard("with")
    terms.discard("from")
    terms.discard("this")
    terms.discard("that")
    return terms, " ".join(sorted(terms))


def download_image(url: str, dest: Path) -> tuple[bool, str, int, int, int]:
    try:
        resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
        resp.raise_for_status()
        content = resp.content
        if not content:
            return False, "", 0, 0, 0
        if HAS_PIL:
            img = Image.open(BytesIO(content))
            img_format = img.format or "JPEG"
            if img.mode == "RGBA":
                rgb = Image.new("RGB", img.size, (255, 255, 255))
                rgb.paste(img, mask=img.split()[3])
                img = rgb
            elif img.mode != "RGB":
                img = img.convert("RGB")
            if max(img.size) > MAX_IMAGE_WIDTH:
                ratio = MAX_IMAGE_WIDTH / max(img.size)
                new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
                img = img.resize(new_size, Image.LANCZOS)
            w, h = img.size
            output = BytesIO()
            img.save(output, format="WEBP", quality=85, method=6)
            data = output.getvalue()
            ext = ".webp"
        else:
            ct = resp.headers.get("content-type", "")
            if "png" in ct:
                ext = ".png"
            elif "gif" in ct:
                ext = ".gif"
            elif "jpeg" in ct or "jpg" in ct or "image/jpg" in ct:
                ext = ".jpg"
            elif "webp" in ct:
                ext = ".webp"
            else:
                ext = ".jpg"
            data = content
            w, h = 0, 0
        dest_path = dest.with_suffix(ext)
        dest_path.write_bytes(data)
        if not HAS_PIL and w == 0:
            try:
                img = Image.open(BytesIO(data))
                w, h = img.size
            except Exception:
                w, h = 1200, 675
        return True, ext, w, h, len(data)
    except (requests.RequestException, OSError, Exception) as e:
        return False, "", 0, 0, 0


def build_credit(result: dict, backend_name: str) -> str:
    creator = result.get("creator", "") or ""
    license_name = result.get("license", "by").upper()
    license_url = result.get("license_url", "") or ""
    backend_labels = {"openverse": "Openverse", "loc": "Library of Congress",
                      "nasa": "NASA", "wikimedia": "Wikimedia Commons",
                      "unsplash": "Unsplash", "pexels": "Pexels",
                      "pixabay": "Pixabay", "ai_generated": "AI-generated (Pollinations.ai)"}
    label = backend_labels.get(backend_name, backend_name)
    parts = [f"Photo by {creator}"] if creator else ["Photo"]
    parts.append(f"via {label} ({license_name})")
    if license_url:
        parts.append(f" — {license_url}")
    return " ".join(parts)


def generate_alt_text(section: dict) -> str:
    heading = section.get("heading", "")
    entities = section.get("entities", [])
    section_type = section.get("section_type", "")
    entity_str = " and ".join(entities[:3]) if entities else heading
    type_labels = {
        "key_findings": f"Illustration of key findings about {entity_str}",
        "applied_scenario": f"Scene related to {entity_str}",
        "source_analysis": f"Source document or archive related to {entity_str}",
        "domain_breakdown": f"Visual overview of {entity_str}",
        "cross_pillar": f"Diagram showing connections involving {entity_str}",
        "methodology": f"Research methodology visual for {entity_str}",
    }
    return type_labels.get(section_type, f"Illustration of {entity_str}")[:120]


def fetch_section_images(article: dict, force: bool = False) -> list[dict]:
    sections = parse_sections(article)
    if not sections:
        return article.get("section_images", []) or []

    break_sections = compute_break_points(sections, article)
    if not break_sections:
        return article.get("section_images", []) or []

    slug = article.get("slug", "")

    # Tier 1 — Editorial Manifest (highest priority)
    manifest_entries = get_manifest_entry(slug)
    if manifest_entries:
        manifest_results = []
        for me in manifest_entries:
            idx = me.get("section_index")
            section = next((s for s in break_sections if s["section_index"] == idx), None)
            if not section:
                continue
            dest = IMAGES_DIR / f"manifest_{slug.replace('/', '_')}_s{idx}"
            dest.parent.mkdir(parents=True, exist_ok=True)
            ok, ext, w, h, size = download_image(me["image_url"], dest)
            if ok:
                rel_path = f"/static/images/generated/manifest_{slug.replace('/', '_')}_s{idx}{ext}"
                manifest_results.append({
                    "section_index": idx,
                    "heading": section["heading"],
                    "image_url": rel_path,
                    "image_credit": me.get("image_credit", ""),
                    "image_alt": me.get("image_alt", ""),
                    "relevance_score": 100.0,
                    "source_api": "manifest",
                    "width": w,
                    "height": h,
                    "content_hash": hashlib.sha256(section.get("text_content", "").encode()).hexdigest()[:16],
                })
        if manifest_results:
            return manifest_results

    existing = {s.get("section_index") for s in (article.get("section_images", []) or [])}
    if not force and existing >= {s["section_index"] for s in break_sections}:
        return article["section_images"]

    pillar = article.get("pillar", "")
    results: list[dict] = []
    used_urls: set[str] = set()
    used_creators: set[str] = set()

    curated_file = resolve_curated(article)
    curated_done = False

    for section in break_sections:
        idx = section["section_index"]
        if not force and idx in existing:
            existing_entry = next((s for s in (article.get("section_images", []) or [])
                                  if s.get("section_index") == idx), None)
            if existing_entry:
                img_path = existing_entry.get("image_url", "")
                if img_path and (IMAGES_DIR / Path(img_path).name).exists():
                    results.append(existing_entry)
                    used_urls.add(existing_entry.get("image_url", ""))
                    used_creators.add(existing_entry.get("image_credit", "").split("via")[0].strip().lower())
                    _GLOBAL_USED_URLS.add(img_path)
                    continue

        if not curated_done and curated_file:
            curated_result = fetch_curated_commons(curated_file)
            if curated_result:
                dest = IMAGES_DIR / f"{slug}_s{idx}"
                dest.parent.mkdir(parents=True, exist_ok=True)
                ok, ext, w, h, size = download_image(curated_result["url"], dest)
                if ok:
                    rel_path = f"/static/images/generated/{slug}_s{idx}{ext}"
                    results.append({
                        "section_index": idx,
                        "heading": section["heading"],
                        "image_url": rel_path,
                        "image_credit": build_credit(curated_result, "wikimedia"),
                        "image_alt": generate_alt_text(section),
                        "relevance_score": 100.0,
                        "source_api": "curated",
                        "width": w,
                        "height": h,
                        "content_hash": hashlib.sha256(section.get("text_content", "").encode()).hexdigest()[:16],
                    })
                    used_urls.add(rel_path)
                    _GLOBAL_USED_URLS.add(rel_path)
                    used_creators.add(curated_result.get("creator", "").lower()[:30])
                    curated_done = True
                    continue

        query = build_section_query(section, article)
        query_terms, _ = normalize_query(query)
        if not query_terms:
            continue

        best: dict | None = None
        best_score = 0.0
        best_backend = ""

        all_backends = list(ALL_BACKENDS)
        if UNSPLASH_KEY:
            all_backends.append(("unsplash", search_unsplash))
        if PEXELS_KEY:
            all_backends.append(("pexels", search_pexels))
        if PIXABAY_KEY:
            all_backends.append(("pixabay", search_pixabay))

        for backend_name, search_fn in all_backends:
            try:
                candidates = search_fn(query)
                for c in candidates:
                    url = c.get("url", "")
                    creator = c.get("creator", "").lower()[:30] if c.get("creator") else ""
                    if url in used_urls or url in _GLOBAL_USED_URLS or creator in used_creators:
                        continue
                    score = score_result(c, query_terms)
                    if score > best_score:
                        c["_score"] = score
                        best = c
                        best_score = score
                        best_backend = backend_name
            except Exception:
                continue

        # Tier 3: AI fallback when no photo found
        if best is None or best_score < MIN_SCORE:
            ai_prompt = f"{query} professional illustration wide format"
            dest = IMAGES_DIR / f"{slug}_s{idx}"
            dest.parent.mkdir(parents=True, exist_ok=True)
            ok, ext, w, h, size = generate_ai_illustration(ai_prompt, dest)
            if ok:
                rel_path = f"/static/images/generated/{slug}_s{idx}{ext}"
                results.append({
                    "section_index": idx,
                    "heading": section["heading"],
                    "image_url": rel_path,
                    "image_credit": "AI-generated via Pollinations.ai (MIT)",
                    "image_alt": generate_alt_text(section),
                    "relevance_score": 50.0,
                    "source_api": "ai_generated",
                    "width": w,
                    "height": h,
                    "content_hash": hashlib.sha256(section.get("text_content", "").encode()).hexdigest()[:16],
                })
                used_urls.add(rel_path)
                _GLOBAL_USED_URLS.add(rel_path)
                continue
            continue

        dest = IMAGES_DIR / f"{slug}_s{idx}"
        dest.parent.mkdir(parents=True, exist_ok=True)
        ok, ext, w, h, size = download_image(best["url"], dest)
        if not ok:
            continue

        rel_path = f"/static/images/generated/{slug}_s{idx}{ext}"
        results.append({
            "section_index": idx,
            "heading": section["heading"],
            "image_url": rel_path,
            "image_credit": build_credit(best, best_backend),
            "image_alt": generate_alt_text(section),
            "relevance_score": round(best_score, 1),
            "source_api": best_backend,
            "width": w,
            "height": h,
            "content_hash": hashlib.sha256(section.get("text_content", "").encode()).hexdigest()[:16],
        })
        used_urls.add(rel_path)
        _GLOBAL_USED_URLS.add(rel_path)
        used_creators.add(best.get("creator", "").lower()[:30] if best.get("creator") else "")

    return results


def print_report(stats: dict):
    print()
    print("═" * 55)
    print(" Section Image Pipeline — Build Report")
    print("═" * 55)
    total = stats.get("total_articles", 0)
    with_images = stats.get("articles_with_images", 0)
    total_sections = stats.get("total_section_slots", 0)
    filled = stats.get("filled_slots", 0)
    print(f"  Articles processed:      {total}")
    print(f"  Articles with images:    {with_images} ({with_images / max(total, 1) * 100:.0f}%)")
    if total_sections:
        print(f"  Sections targeted:       {total_sections}")
        print(f"  Images placed:           {filled} ({filled / total_sections * 100:.1f}%)")
    backend_hits = stats.get("backend_hits", {})
    if backend_hits:
        print()
        print("  Backend hit rate:")
        total_hits = sum(backend_hits.values()) or 1
        for name, count in sorted(backend_hits.items(), key=lambda x: -x[1]):
            print(f"    {name:20s} {count:4d} ({count / total_hits * 100:5.1f}%)")
    section_coverage = stats.get("section_coverage", {})
    if section_coverage:
        print()
        print("  Section coverage:")
        for name, (hits, total_s) in sorted(section_coverage.items(), key=lambda x: -x[1][0]):
            pct = hits / max(total_s, 1) * 100
            bar = "█" * int(pct / 10) + "░" * (10 - int(pct / 10))
            print(f"    {name:20s} {bar} {hits:3d}/{total_s} ({pct:.0f}%)")
    scores = stats.get("relevance_scores", [])
    if scores:
        avg = sum(scores) / max(len(scores), 1)
        print(f"\n  Avg relevance score:     {avg:.1f}")
        print(f"  Above threshold (70+):  {sum(1 for s in scores if s >= 70)} ({sum(1 for s in scores if s >= 70) / max(len(scores), 1) * 100:.0f}%)")
    bandwidth = stats.get("total_bytes", 0)
    if bandwidth:
        print(f"  Total bandwidth:         {bandwidth / 1024 / 1024:.1f} MB")
    print("═" * 55)
    print()


def main():
    parser = argparse.ArgumentParser(description="Fetch section-level images for articles")
    parser.add_argument("--max", type=int, default=0, help="Max articles (0 = all)")
    parser.add_argument("--force", action="store_true", help="Re-fetch all images")
    args = parser.parse_args()

    if not REGISTRY_PATH.exists():
        print(f"Registry not found at {REGISTRY_PATH}")
        return 1

    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    content_list = registry.get("content", [])
    max_count = args.max if args.max > 0 else len(content_list)

    content_list.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    articles_to_process = content_list[:max_count]

    print(f"Processing {len(articles_to_process)} articles...")

    stats: dict[str, Any] = {
        "total_articles": len(articles_to_process),
        "articles_with_images": 0,
        "total_section_slots": 0,
        "filled_slots": 0,
        "backend_hits": Counter(),
        "section_coverage": {},
        "relevance_scores": [],
        "total_bytes": 0,
    }
    updated_count = 0

    for article in articles_to_process:
        slug = article.get("slug", "")
        print(f"  {slug} … ", end="", flush=True)

        section_images = fetch_section_images(article, force=args.force)
        if section_images:
            article["section_images"] = section_images
            updated_count += 1
            images_placed = len(section_images)
            stats["articles_with_images"] += 1
            stats["filled_slots"] += images_placed
            for si in section_images:
                backend = si.get("source_api", "unknown")
                stats["backend_hits"][backend] += 1
                score = si.get("relevance_score", 0)
                stats["relevance_scores"].append(score)
                stype = SECTION_TYPES.get(si.get("section_index", 0), "unknown")
                if stype not in stats["section_coverage"]:
                    stats["section_coverage"][stype] = [0, 0]
                stats["section_coverage"][stype][0] += 1
                img_path = si.get("image_url", "")
                if img_path:
                    fpath = PROJECT_ROOT / img_path.lstrip("/")
                    if fpath.exists():
                        stats["total_bytes"] += fpath.stat().st_size
            print(f"\u2713 {images_placed} images")
        else:
            print("\u2717")

        time.sleep(RATE_LIMIT_DELAY)

    for article in articles_to_process:
        sections = parse_sections(article)
        for s in sections:
            idx = s["section_index"]
            stype = SECTION_TYPES.get(idx, "unknown")
            if stype not in stats["section_coverage"]:
                stats["section_coverage"][stype] = [0, 0]
            stats["section_coverage"][stype][1] += 1
            if idx in (1, 2, 5):
                stats["total_section_slots"] += 1

    if updated_count > 0:
        registry["content"] = content_list
        REGISTRY_PATH.write_text(json.dumps(registry, indent=2, default=str), encoding="utf-8")
        print(f"\nUpdated {updated_count} articles in registry")
    else:
        print("\nNo articles updated")

    print_report(stats)
    return 0


if __name__ == "__main__":
    exit(main())
