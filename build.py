#!/usr/bin/env python3
"""
Build script for AcaciaFund: converts registry.json to static HTML using Jinja2 templates.
3-category taxonomy: research | learn | knowledge
"""
import hashlib
import json
import os
import re
import shutil
import time
import tomllib
import unicodedata
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from PIL import Image

from jinja2 import Environment, FileSystemLoader, select_autoescape
from urllib.parse import quote as urlquote

from schemas import RegistryData
from core.visuals import generate_thumbnail_svg, generate_og_image, resolve_topic_icon, render_topic_icon, _pick_subtopic, TOPIC_ICONS, SUBTOPIC_CATEGORIES, PILLAR_COLORS
from core.images import generate_fallback_svg
from core.brand import BRAND, brand_domain_icon, brand_micro_icon, brand_logo_svg, section_type_color

from seed_learn import CURATED_RELATIONS, PREREQUISITES as LEARN_PREREQUISITES
from config import (
    PROJECT_ROOT, SITE_URL, SITE_NAME, SITE_DESCRIPTION, PLAUSIBLE_DOMAIN,
    REGISTRY_PATH, TEMPLATE_DIR, OUTPUT_DIR,
    STATIC_DST_DIR, PIPELINE_STATIC_DIR, CONTENT_DIR,
    SQI_THRESHOLD_MIN, SQI_BADGE_HIGH, SQI_BADGE_MED, SQI_DEFAULT,
    INTEREST_SQI_WEIGHT, INTEREST_RECENCY_WEIGHT, INTEREST_RECENCY_DAYS,
)

# ── Mem0 integration for session context and deployment logging ──
try:
    from services.mem0 import log_deployment, save_insight
    MEM0_AVAILABLE = True
except ImportError:
    MEM0_AVAILABLE = False

# ── Admin credentials from .env ──
def load_admin_credentials():
    """Load admin credentials from .env file."""
    env_path = PROJECT_ROOT / ".env"
    username = "admin"
    password = "admin"
    
    if env_path.exists():
        try:
            content = env_path.read_text()
            for line in content.split("\n"):
                line = line.strip()
                if line.startswith("#") or not line:
                    continue
                if "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip()
                    if key == "ADMIN_USERNAME":
                        username = value
                    elif key == "ADMIN_PASSWORD":
                        password = value
        except Exception:
            pass
    
    return username, password

def get_topic_icons(tags: list[str]) -> list[str]:
    """Map article tags to resolved SVG path data, returning up to 3 matches."""
    if not tags:
        return []
    lower_tags = {t.lower() for t in tags}
    matched = []
    seen = set()
    for tag in lower_tags:
        if tag in TOPIC_ICONS and tag not in seen:
            path = resolve_topic_icon(tag)
            if path:
                matched.append(path)
                seen.add(tag)
                if len(matched) >= 3:
                    break
    if len(matched) < 3:
        for subs in SUBTOPIC_CATEGORIES.values():
            for key, keywords in subs.items():
                if key in seen:
                    continue
                if lower_tags & keywords:
                    path = resolve_topic_icon(key)
                    if path:
                        matched.append(path)
                        seen.add(key)
                        if len(matched) >= 3:
                            break
            if len(matched) >= 3:
                break
    if len(matched) < 3:
        for tag in lower_tags:
            for tkey in TOPIC_ICONS:
                if tkey in seen:
                    continue
                if tkey in tag or tag in tkey:
                    path = resolve_topic_icon(tkey)
                    if path:
                        matched.append(path)
                        seen.add(tkey)
                        if len(matched) >= 3:
                            break
            if len(matched) >= 3:
                break
    return matched


PILLAR_CONFIG = {
    "aml": {
        "label": "AML", "emoji": "🛡️", "color": "slate",
        "bg": "from-slate-900 to-slate-800", "accent": "amber",
        "text_color": "text-slate-900", "badge_color": "bg-amber-100 text-amber-800",
        "heading": "Anti-Money Laundering",
        "description": "Financial crime, compliance, regulation, and risk management.",
    },
    "stock": {
        "label": "Markets", "emoji": "📈", "color": "green",
        "bg": "from-green-900 to-green-800", "accent": "green",
        "text_color": "text-green-900", "badge_color": "bg-green-100 text-green-800",
        "heading": "Markets & Industry",
        "description": "Semiconductors, supply chains, AI industry, manufacturing.",
    },
    "data-engineering": {
        "label": "Data Engineering", "emoji": "⚙️", "color": "indigo",
        "bg": "from-indigo-900 to-indigo-800", "accent": "indigo",
        "text_color": "text-indigo-900", "badge_color": "bg-indigo-100 text-indigo-800",
        "heading": "Data Engineering & Infrastructure",
        "description": "Data pipelines, orchestration, quality engineering, streaming, storage, and analytics infrastructure.",
    },
}
PILLAR_EMOJIS = {"aml": "🛡️", "stock": "📈", "data-engineering": "⚙️"}
PILLAR_NAMES = {"aml": "AML", "stock": "Markets", "data-engineering": "Data Engineering"}
DIFFICULTY_ORDER = {"beginner": 0, "intermediate": 1, "advanced": 2}

# Section type mapping (positional index → semantic type)
SECTION_TYPES = {
    0: "overview",
    1: "key_findings",
    2: "applied_scenario",
    3: "source_analysis",
    4: "domain_breakdown",
    5: "cross_pillar",
    6: "methodology",
}

KNOWLEDGE_CATEGORIES = {
    "platform": {
        "label": "Platform", "icon": "⚙️", "color": "#6366f1", "bg_color": "#6366f1",
        "description": "About AcaciaFund — mission, team, contact, and site operations.",
    },
    "guide": {
        "label": "Guides", "icon": "🧭", "color": "#22c55e", "bg_color": "#22c55e",
        "description": "Methodology, taxonomy, and how-to guides for using the platform.",
    },
    "reference": {
        "label": "Reference", "icon": "📖", "color": "#d97706", "bg_color": "#d97706",
        "description": "Glossaries, tool landscapes, and technical terminology across all pillars.",
    },
    "architecture": {
        "label": "Architecture", "icon": "🔗", "color": "#a855f7", "bg_color": "#a855f7",
        "description": "System design, pipeline architecture, and DataOps implementation details.",
    },
}


def add_lazy_loading(html: str) -> str:
    return re.sub(r'<img(?![^>]*loading=)', '<img loading="lazy" decoding="async"', html)


def slug_to_path(slug: str) -> str:
    return f"{slug}/index.html" if "/" in slug else f"{slug}.html"


def canonical_path(slug_or_path: str) -> str:
    """Normalize a path for canonical URLs: strip /index.html, enforce trailing slash."""
    path = slug_or_path.replace("/index.html", "/").replace(".html", "/")
    if not path.endswith("/"):
        path += "/"
    return path


def slug_to_url(slug: str) -> str:
    return f"{SITE_URL}/{canonical_path(slug_to_path(slug))}"


def group_by_pillar(content_list: list) -> dict[str, list]:
    groups: dict[str, list] = defaultdict(list)
    for c in content_list:
        p = c.pillar
        if not p:
            continue
        groups[p].append(c)
    for g in groups.values():
        g.sort(key=lambda x: x.created_at or datetime.min, reverse=True)
    return dict(groups)


HEADING_RE = re.compile(r'<h([23])([^>]*)>(.*?)</h\1>', re.IGNORECASE | re.DOTALL)


def extract_headings(html: str) -> tuple[str, list[dict]]:
    toc = []
    id_counts: dict[str, int] = {}
    def _repl(m):
        tag = m.group(1)
        inner = m.group(3)
        text = re.sub(r'<[^>]+>', '', inner).strip()
        base_id = re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-') or "section"
        if base_id in id_counts:
            id_counts[base_id] += 1
            id_str = f"{base_id}-{id_counts[base_id]}"
        else:
            id_counts[base_id] = 0
            id_str = base_id
        toc.append({"id": id_str, "text": text, "tag": f"h{tag}"})
        return f'<h{tag} id="{id_str}">{inner}</h{tag}>'
    html = HEADING_RE.sub(_repl, html)
    return html, toc


def find_related(posts: list, current: object, max_items: int = 3) -> list:
    """Score relatedness by pillar match (40%), tag overlap (40%), curated relations (20%).

    Curated relations (from current.curated_relations) always appear first
    when they match a post slug in the candidate pool.
    """
    current_tags = set(t.lower() for t in current.tags)
    current_pillar = current.pillar or ""
    curated_slugs = {r.get("slug", "") for r in (current.curated_relations or [])}

    scored: list[tuple[float, object]] = []
    seen_slugs: set[str] = set()

    # Phase 1: Curated relations (always included if post exists in pool)
    for r in current.curated_relations or []:
        rslug = r.get("slug", "")
        if not rslug:
            continue
        for p in posts:
            if p.slug == rslug and p.slug != current.slug:
                scored.append((2.0, p))
                seen_slugs.add(p.slug)
                break

    # Phase 2: Algorithmic scoring for remaining candidates
    for p in posts:
        if p.slug == current.slug or p.slug in seen_slugs:
            continue
        pillar_match = 1.0 if p.pillar and p.pillar == current_pillar else 0.0
        tag_overlap = len(current_tags & set(t.lower() for t in p.tags))
        tag_score = min(tag_overlap / max(len(current_tags), 1), 1.0)
        score = pillar_match * 0.4 + tag_score * 0.4
        if score > 0:
            scored.append((score, p))
    scored.sort(key=lambda x: -x[0])
    return [p for _, p in scored[:max_items]]


CARD_PICTOGRAM_KEYWORDS = {
    # Core concepts (cross-pillar) - priority 1
    "ai": [
        "ai", "artificial intelligence", "machine learning", "deep learning",
        "neural", "llm", "large language model", "generative ai",
        "openai", "anthropic", "google gemini", "claude", "gpt",
        "transformer", "bert", "gpt-4", "gpt-5", "claude 3",
    ],
    "realtime": [
        "real-time", "realtime", "streaming", "stream",
        "event-driven", "event streaming", "kafka", "kafka streams",
        "flink", "spark streaming", "kinesis", "pulsar",
        "cdc", "change data capture", "debezium",
        "websockets", "sse", "server-sent events",
    ],
    "platform": [
        "platform", "data platform", "data stack", "data architecture",
        "cloud infrastructure", "kubernetes", "k8s",
        "docker", "container", "orchestration", "terraform",
        "aws", "azure", "gcp", "serverless",
        "infrastructure as code", "iac",
    ],
    # Content types (cross-pillar) - priority 2
    "tutorial": [
        "tutorial", "how-to", "guide", "step-by-step", "walkthrough",
        "beginner", "introductory", "introduction", "getting started",
        "learn", "teach", "educational", "instructional",
    ],
    "comparison": [
        "comparison", "compare", "vs", "versus", "showdown",
        "benchmark", "evaluation", "review", "analysis",
        "trade-off", "pros and cons", "alternatives",
    ],
    "case-study": [
        "case study", "real-world", "production",
        "implementation", "deployment", "migration", "migration story",
        "customer", "client", "enterprise", "success story",
    ],
    # AML-specific - priority 3
    "aml": [
        "aml", "anti-money laundering", "compliance", "regulatory",
        "regulation", "enforcement", "sanctions", "fatf", "fincen",
        "kyc", "know your customer", "kyb", "know your business",
        "sar", "suspicious activity report", "transaction monitoring",
        "financial crime", "risk assessment",
    ],
    "fraud": [
        "fraud", "fraud detection", "fraud prevention",
        "scam", "scam detection", "payment fraud",
        "chargeback", "chargeback fraud", "synthetic identity",
        "money laundering", "suspicious activity",
    ],
    # Security - priority 4
    "security": [
        "security", "cybersecurity", "threat detection", "penetration",
        "vulnerability", "exploit", "attack", "breach", "intrusion",
        "malware", "ransomware", "phishing", "social engineering",
        "zero trust", "iam", "identity access management",
        "firewall", "waf", "web application firewall",
        "siem", "security information", "soc", "security operations",
    ],
    # DevOps - priority 5
    "devops": [
        "devops", "ci/cd", "continuous integration", "continuous delivery",
        "continuous deployment", "deployment", "build", "release",
        "pipeline", "workflow", "automation", "infrastructure as code",
        "terraform", "ansible", "puppet", "chef",
        "gitops", "argocd", "tekton", "jenkins",
    ],
    # Analytics - priority 6
    "analytics": [
        "analytics", "business intelligence", "bi", "reporting",
        "dashboard", "visualization", "data visualization", "chart",
        "kpi", "metric", "dashboard", "kpi tracking",
        "power bi", "tableau", "looker", "metabase",
    ],
    # Monitoring - priority 7
    "monitoring": [
        "monitoring", "observability", "logging", "tracing",
        "metrics", "alerting", "alert", "incident",
        "sre", "site reliability engineering", "slo", "sla",
        "prometheus", "grafana", "datadog", "new relic",
        "opentelemetry", "jaeger", "zipkin", "loki",
    ],
    # Cloud - priority 8
    "cloud": [
        "cloud", "aws", "azure", "gcp", "google cloud",
        "serverless", "lambda", "cloud function", "cloud run",
        "ec2", "s3", "rds", "dynamodb", "firestore",
        "cloudformation", "cloudformation", "terraform",
        "multi-cloud", "hybrid cloud", "cloud native",
    ],
    # Markets-specific - priority 9
    "finance": [
        "finance", "trading", "investment", "portfolio",
        "stock market", "equities", "bonds", "derivatives",
        "valuation", "financial modeling", "quantitative",
        "algorithmic trading", "algo trading", "high frequency",
        "market making", "market data", "financial technology",
    ],
    "market": [
        "market", "trading", "market data", "market analysis",
        "stock", "equity", "securities", "exchange",
        "nasdaq", "nyse", "s&p 500", "dow jones",
        "market maker", "market structure", "market microstructure",
    ],
    # Data Engineering-specific - priority 10
    "pipeline": [
        "pipeline", "etl", "elt", "orchestration", "workflow",
        "dag", "directed acyclic graph", "airflow", "dagster", "prefect",
        "kubeflow", "temporal", "kedro", "dbt", "sqlmesh",
        "data pipeline", "pipeline orchestration", "workflow orchestration",
    ],
    "infrastructure": [
        "infrastructure", "kubernetes", "k8s", "docker", "container",
        "infrastructure as code", "iac",
        "cloud", "aws", "azure", "gcp", "serverless",
        "deployment", "ci/cd", "continuous integration", "continuous delivery",
    ],
    # Technical (cross-pillar) - priority 11
    "database": [
        "database", "db", "sql", "nosql", "postgresql", "mysql",
        "mongodb", "cassandra", "redis", "memcached",
        "storage", "data warehouse", "data lake", "lakehouse",
        "iceberg", "delta lake", "hudi", "parquet", "avro",
    ],
    "api": [
        "api", "api design", "rest", "graphql", "grpc",
        "microservice", "service mesh", "istio", "linkerd",
        "gateway", "gateway api", "openapi", "swagger",
        "integration", "integration pattern", "event-driven",
    ],
}

_PICTOGRAM_PILLAR_DEFAULTS = {
    "aml": "aml.svg",
    "stock": "finance.svg",
    "data-engineering": "pipeline.svg",
}

_PICTOGRAM_CONTENT_TYPE_FALLBACK = {
    "research": "icon-research.svg",
    "learn": "icon-learn.svg",
    "knowledge": "icon-knowledge.svg",
}

def pick_card_pictogram(content) -> str | None:
    """Pick the most relevant pictogram based on title, tags, pillar, and content type.
    
    Uses scoring system with priority levels to find best match:
    - Priority 1: Core concepts (ai, realtime, platform)
    - Priority 2: Content types (tutorial, comparison, case-study)
    - Priority 3: AML-specific (aml, fraud)
    - Priority 4-8: New categories (security, devops, analytics, monitoring, cloud)
    - Priority 9-11: Markets & Data Engineering (finance, market, pipeline, infrastructure, database, api)
    """
    text = " ".join([
        *(t.lower().replace("-", " ") for t in (content.tags or [])),
        (content.title or "").lower(),
    ])
    pillar = (content.pillar or "").lower()
    content_type = (content.content_type or "").lower()
    
    # Priority levels for scoring
    priority_map = {
        "ai": 1, "realtime": 1, "platform": 1,
        "tutorial": 2, "comparison": 2, "case-study": 2,
        "aml": 3, "fraud": 3,
        "security": 4, "devops": 5, "analytics": 6, "monitoring": 7, "cloud": 8,
        "finance": 9, "market": 9,
        "pipeline": 10, "infrastructure": 10,
        "database": 11, "api": 11,
    }
    
    # First pass: exact keyword matches with priority (backward compatible)
    for priority in range(1, 12):
        for img_name, keywords in CARD_PICTOGRAM_KEYWORDS.items():
            if priority_map.get(img_name) != priority:
                continue
            for kw in keywords:
                if kw.lower() in text:
                    return f"{img_name}.svg"
    
    # Second pass: use scoring for better matching
    scores = {}
    for img_name, keywords in CARD_PICTOGRAM_KEYWORDS.items():
        score = 0
        for kw in keywords:
            if kw.lower() in text:
                # Base score for keyword match
                score += 10
                # Bonus for exact phrase matches
                if kw.lower() == text.strip():
                    score += 50
                # Bonus for multi-word keyword matches
                if len(kw.split()) > 1 and kw.lower() in text:
                    score += 20
        
        # Priority multiplier (higher priority = higher base score)
        priority_mult = (12 - priority_map.get(img_name, 6)) * 0.5
        score *= (1 + priority_mult)
        
        # Pillar-specific weighting
        if pillar == "aml" and img_name in ["aml", "fraud", "security"]:
            score *= 1.5
        elif pillar == "stock" and img_name in ["finance", "market"]:
            score *= 1.5
        elif pillar == "data-engineering" and img_name in ["pipeline", "infrastructure", "database", "api", "monitoring", "devops"]:
            score *= 1.5
        
        # Content type weighting
        if content_type == "learn" and img_name == "tutorial":
            score *= 1.3
        
        if score > 0:
            scores[img_name] = score
    
    if scores:
        best_match = max(scores.items(), key=lambda x: x[1])
        return f"{best_match[0]}.svg"
    
    # Fallback to pillar defaults
    if pillar in _PICTOGRAM_PILLAR_DEFAULTS:
        return _PICTOGRAM_PILLAR_DEFAULTS[pillar]
    
    # Content type fallback
    if content_type in _PICTOGRAM_CONTENT_TYPE_FALLBACK:
        return _PICTOGRAM_CONTENT_TYPE_FALLBACK[content_type]
    
    return "icon-research.svg"


def reading_time_minutes(html_or_text: str) -> int:
    text = re.sub(r'<[^>]+>', '', html_or_text)
    words = len(text.strip().split())
    code_blocks = len(re.findall(r'<pre><code>.*?</code></pre>', html_or_text, re.DOTALL))
    code_penalty_sec = code_blocks * 30
    minutes = (words / 150) + (code_penalty_sec / 60)
    return max(2, round(minutes)) if words > 100 else max(1, round(minutes))


def generate_sqi_badge(sqi: float) -> str:
    color = "#22c55e" if sqi >= SQI_BADGE_HIGH else "#d97706" if sqi >= SQI_BADGE_MED else "#ef4444"
    w = 160
    bar_w = int(min(1.0, max(0, sqi)) * w)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="20" viewBox="0 0 {w} 20">'
        f'<rect width="{w}" height="8" y="6" rx="4" fill="#e2e8f0"/>'
        f'<rect width="{bar_w}" height="8" y="6" rx="4" fill="{color}"/>'
        f'<circle cx="{max(8, bar_w)}" cy="10" r="6" fill="{color}"/>'
        f'<text x="{w + 6}" y="14" fill="#64748b" font-size="11" font-family="system-ui,sans-serif">{sqi:.3f}</text>'
        f'</svg>'
    )


def thumbnail_key(title: str) -> str:
    return hashlib.md5(title.encode()).hexdigest()[:12]


CJK_RE = re.compile(r'[\u4e00-\u9fff\u3400-\u4dbf\uff00-\uffef]')
EMOJI_RE = re.compile(r'[\U0001F300-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF\u2600-\u27BF\u2B50\U0001F1E0-\U0001F1FF]')


MERMAID_PLACEHOLDER = "@@MERMAID_"
_mermaid_counter = 0

def sanitize_text(html: str, strip_emoji: bool = True) -> str:
    global _mermaid_counter
    html = unicodedata.normalize('NFKC', html)
    html = CJK_RE.sub('', html)
    if strip_emoji:
        html = EMOJI_RE.sub('', html)
    # Protect mermaid div content from space-collapsing (need indent for mindmap)
    global _mermaid_counter
    mermaid_map = {}
    def _save_mermaid(m):
        global _mermaid_counter
        key = f"{MERMAID_PLACEHOLDER}{_mermaid_counter}_"
        _mermaid_counter += 1
        mermaid_map[key] = m.group(0)
        return key
    html = re.sub(r'(<div class="mermaid"[^>]*>)(.*?)(</div>)', _save_mermaid, html, flags=re.DOTALL)
    html = re.sub(r'  +', ' ', html)
    html = re.sub(r'>\s+<', '><', html)
    for key, original in mermaid_map.items():
        html = html.replace(key, original)
    return html


DOMAIN_BREAKDOWN_RE = re.compile(
    r'<li>[^<]*?([A-Za-z]+)\s*:\s*(\d+)%\s*of sources\s*</li>',
    re.IGNORECASE,
)


def sanitize_domain_breakdown(html: str) -> str:
    """Normalize domain breakdown percentages so they sum to exactly 100."""
    matches = list(DOMAIN_BREAKDOWN_RE.finditer(html))
    if not matches:
        return html
    total_pct = sum(int(m.group(2)) for m in matches)
    if total_pct <= 100:
        return html
    rescaled = []
    for m in matches:
        domain = m.group(1)
        orig = int(m.group(2))
        capped = max(1, round(orig * 100 / total_pct))
        rescaled.append((domain, capped))
    diff = sum(r[1] for r in rescaled) - 100
    if diff != 0:
        idx = max(range(len(rescaled)), key=lambda i: rescaled[i][1])
        d, v = rescaled[idx]
        rescaled[idx] = (d, max(1, v - diff))
    for m, (domain, capped) in zip(matches, rescaled):
        html = html.replace(m.group(0), f'<li>{domain}: {capped}% of sources</li>', 1)
    return html


def _resolve_ref_file(p: Path) -> str:
    """If p is a REF: pointer file, return the URL of the original image."""
    if p.exists() and p.is_file():
        try:
            content = p.read_text(encoding="utf-8").strip()
            if content.startswith("REF:"):
                original_name = content[4:]
                original_path = p.parent / original_name
                if original_path.exists():
                    rel = str(original_path.relative_to(PROJECT_ROOT))
                    return f"{SITE_URL}/{rel}"
        except Exception:
            pass
    return ""


def resolve_featured_image(raw_path: str) -> str:
    """Resolve featured_image path to absolute URL, trying multiple extensions."""
    if not raw_path:
        return ""
    p = Path(PROJECT_ROOT / raw_path.lstrip("/"))
    # Try original path
    if p.exists():
        ref = _resolve_ref_file(p)
        if ref:
            return ref
        return f"{SITE_URL}{raw_path}" if raw_path.startswith("/") else f"{SITE_URL}/{raw_path}"
    # Try alternate extensions: .webp, .png, .jpg, .jpeg, .svg
    stem = p.stem
    for ext in (".webp", ".png", ".jpg", ".jpeg", ".svg"):
        alt = p.parent / f"{stem}{ext}"
        if alt.exists():
            ref = _resolve_ref_file(alt)
            if ref:
                return ref
            resolved = raw_path.rsplit("/", 1)[0] + "/" + alt.name
            return f"{SITE_URL}{resolved}" if resolved.startswith("/") else f"{SITE_URL}/{resolved}"
    # Try _s1 variant with extensions
    for ext in (".webp", ".png", ".jpg", ".jpeg", ".svg"):
        s1_path = p.parent / f"{stem}_s1{ext}"
        if s1_path.exists():
            ref = _resolve_ref_file(s1_path)
            if ref:
                return ref
            resolved = raw_path.rsplit("/", 1)[0] + "/" + s1_path.name
            return f"{SITE_URL}{resolved}" if resolved.startswith("/") else f"{SITE_URL}/{resolved}"
    return ""


def resolve_section_image(url: str) -> str:
    """Resolve section image URL, trying alternate extensions if file missing."""
    if not url:
        return ""
    p = Path(PROJECT_ROOT / url.lstrip("/"))
    if p.exists():
        ref = _resolve_ref_file(p)
        if ref:
            return ref
        return url
    for ext in (".webp", ".png", ".jpg", ".jpeg", ".svg"):
        alt = p.with_suffix(ext)
        if alt.exists():
            ref = _resolve_ref_file(alt)
            if ref:
                return ref
            return url.rsplit(".", 1)[0] + ext
    return ""


def generate_card_thumbnail(source_url: str, slug: str) -> str:
    """Generate a 200x150 card thumbnail from a featured image. Returns URL path or empty string."""
    if not source_url:
        return ""
    raw = source_url.lstrip("/")
    src = Path(PROJECT_ROOT / raw)
    if not src.exists() or src.stat().st_size == 0:
        return ""
    # Follow REF: pointers (dedup symlinks from fetch_images.py)
    try:
        ref = _resolve_ref_file(src)
        if ref:
            resolved = Path(PROJECT_ROOT / ref.lstrip("/").replace(f"{SITE_URL}/", "", 1))
            if resolved.exists():
                src = resolved
    except Exception:
        pass
    prefix = source_url.rsplit("/", 1)[0]
    stem = src.stem
    ext = src.suffix if src.suffix else ".webp"
    thumb_name = f"{stem}_card{ext}"
    thumb_path = src.parent / thumb_name
    thumb_url = f"{prefix}/{thumb_name}"
    if not thumb_path.exists() or src.stat().st_mtime > thumb_path.stat().st_mtime:
        try:
            img = Image.open(src)
            img.thumbnail((200, 150), Image.LANCZOS)
            img.save(thumb_path, optimize=True)
        except Exception as e:
            print(f"  WARNING: card thumbnail failed for {slug}: {e}")
            return ""
    return thumb_url


def generate_missing_ai_image(url: str) -> str:
    """Generate a simple AI fallback SVG for missing section images."""
    if not url:
        return ""
    p = Path(PROJECT_ROOT / url.lstrip("/"))
    if p.exists():
        return url
    # Generate a simple gradient SVG as placeholder
    slug = url.split("/")[-1].rsplit(".", 1)[0]
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="675" viewBox="0 0 1200 675">
      <defs>
        <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" style="stop-color:#1a1a2e;stop-opacity:1" />
          <stop offset="100%" style="stop-color:#16213e;stop-opacity:1" />
        </linearGradient>
      </defs>
      <rect width="1200" height="675" fill="url(#bg)"/>
      <text x="600" y="337" font-family="monospace" font-size="16" fill="#4cc9f0" text-anchor="middle">{slug}</text>
    </svg>"""
    svg_path = p.with_suffix(".svg")
    svg_path.parent.mkdir(parents=True, exist_ok=True)
    svg_path.write_text(svg)
    return url.rsplit(".", 1)[0] + ".svg"


def _get_article_attr(article, key: str, default=None):
    """Helper: get attribute from AcaciaContent or key from dict."""
    if article is None:
        return default
    if isinstance(article, dict):
        return article.get(key, default)
    return getattr(article, key, default)


def _article_as_dict(article):
    """Convert article (AcaciaContent or dict) to a plain dict."""
    if article is None:
        return {}
    if isinstance(article, dict):
        return article
    return article.dict()





def inject_section_images(body_html: str, section_images: list[dict],
                           article=None) -> str:
    """Insert section-level images and data visualizations into body_html.

    Wraps each section in a .section-harvester div with:
    - Colored left border for section identity
    - Context-relevant data visualization (source bar, bloom chart, radar, etc.)
    - Collapsible content via <details>/<summary>
    - Section images placed between harvesters as visual transitions

    Matches by section_index (positional: 0 = first <h2>, 1 = second, etc.)
    """
    h2_pattern = re.compile(r'(<h2[^>]*>.*?</h2>)', re.IGNORECASE | re.DOTALL)
    parts = h2_pattern.split(body_html)
    if not parts:
        return body_html

    img_map: dict[int, dict] = {}
    if section_images:
        for si in section_images:
            idx = si.get("section_index")
            if idx is not None:
                img_map[idx] = si

    content_type = _get_article_attr(article, "content_type", "research")
    pillar = _get_article_attr(article, "pillar", "aml")
    use_harvesters = content_type in ("research", "learn", "knowledge")

    result: list[str] = [parts[0]]

    for i in range(1, len(parts), 2):
        h2_tag = parts[i]
        content = parts[i + 1] if i + 1 < len(parts) else ""
        section_idx = (i - 1) // 2

        entry = img_map.get(section_idx)
        section_type = SECTION_TYPES.get(section_idx, "overview")

        if use_harvesters:
            pillar_color = section_type_color(section_idx, pillar)

            # Collapsible section: summary = heading, details = content
            result.append(
                f'<div class="section-harvester" data-section="{section_type}" '
                f'style="--section-color:{pillar_color}">'
            )
            result.append('<details class="section-collapse" open>')
            result.append(f'<summary class="section-summary">{h2_tag}</summary>')
            result.append(f'<div class="section-body">{content}</div>')
            result.append('</details>')
            result.append('</div>')

            # Section image goes OUTSIDE the harvester (as transition)
            if entry:
                url = resolve_section_image(entry.get("image_url", ""))
                credit = entry.get("image_credit", "")
                alt_ = entry.get("image_alt", "") or f"Illustration for {strip_html_tag(h2_tag)}"
                w = entry.get("width", 1200)
                h = entry.get("height", 675)
                if url:
                    style_class = "section-image--full" if section_idx % 2 == 0 else "section-image--contained"
                    figure_style = "background:var(--color-bg);border:1px solid var(--color-border)"
                    caption_id = f"sec-caption-{section_idx}" if credit else ""
                    aria_attr = f' aria-describedby="{caption_id}"' if credit else ""
                    f = [
                        f'<figure class="section-image {style_class} my-6 rounded-lg overflow-hidden"',
                        f' style="{figure_style}"{aria_attr}>',
                        f'<img src="{url}" alt="{alt_}" width="{w}" height="{h}"',
                        ' loading="lazy" decoding="async"',
                        ' class="w-full h-auto object-cover">',
                    ]
                    if credit:
                        f.append(
                            f'<figcaption id="{caption_id}" class="px-3 py-1.5 text-xs"'
                            ' style="color:var(--color-text-muted);border-top:1px solid var(--color-border)">'
                            f'{credit}</figcaption>'
                        )
                    f.append("</figure>")
                    result.append("".join(f))
                elif article:
                    section = {"section_index": section_idx, "heading": strip_html_tag(h2_tag)}
                    article_dict = _article_as_dict(article)
                    try:
                        svg = generate_fallback_svg(section, article_dict)
                        result.append(
                            f'<figure class="section-image section-image--full section-fallback my-6 rounded-lg overflow-hidden"'
                            f' style="background:var(--color-bg);border:1px solid var(--color-border)">'
                            f'{svg}</figure>'
                        )
                    except Exception:
                        pass
        else:
            # No harvester wrapping — original flat behavior
            result.append(h2_tag)
            if entry:
                url = resolve_section_image(entry.get("image_url", ""))
                credit = entry.get("image_credit", "")
                alt_ = entry.get("image_alt", "") or f"Illustration for {strip_html_tag(h2_tag)}"
                w = entry.get("width", 1200)
                h = entry.get("height", 675)
                if url:
                    style_class = "section-image--full" if section_idx % 2 == 0 else "section-image--contained"
                    figure_style = "background:var(--color-bg);border:1px solid var(--color-border)"
                    caption_id = f"sec-caption-{section_idx}" if credit else ""
                    aria_attr = f' aria-describedby="{caption_id}"' if credit else ""
                    f = [
                        f'<figure class="section-image {style_class} my-6 rounded-lg overflow-hidden"',
                        f' style="{figure_style}"{aria_attr}>',
                        f'<img src="{url}" alt="{alt_}" width="{w}" height="{h}"',
                        ' loading="lazy" decoding="async"',
                        ' class="w-full h-auto object-cover">',
                    ]
                    if credit:
                        f.append(
                            f'<figcaption id="{caption_id}" class="px-3 py-1.5 text-xs"'
                            ' style="color:var(--color-text-muted);border-top:1px solid var(--color-border)">'
                            f'{credit}</figcaption>'
                        )
                    f.append("</figure>")
                    result.append("".join(f))
                elif article:
                    section = {"section_index": section_idx, "heading": strip_html_tag(h2_tag)}
                    article_dict = _article_as_dict(article)
                    try:
                        svg = generate_fallback_svg(section, article_dict)
                        result.append(
                            f'<figure class="section-image section-image--full section-fallback my-6 rounded-lg overflow-hidden"'
                            f' style="background:var(--color-bg);border:1px solid var(--color-border)">'
                            f'{svg}</figure>'
                        )
                    except Exception:
                        pass
            result.append(content)

    return "".join(result)


def strip_html_tag(tag: str) -> str:
    m = re.search(r'>([^<]+)<', tag)
    return m.group(1).strip() if m else ""


def is_future_post(post) -> bool:
    return bool(post.created_at and post.created_at > datetime.now(timezone.utc))


# ── Visual fingerprint: unique ident for every article ─────
PILLAR_FINGERPRINT_COLORS = {
    "aml": BRAND["aml"]["primary"],
    "stock": BRAND["markets"]["primary"],
    "data-engineering": BRAND["science"]["primary"],
    "": "#6b7280",
}

LAYER_SYMBOLS = {
    "research": ("path", '<path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" fill="none" stroke="currentColor" stroke-width="1.5"/>'),
    "learn": ("path", '<path d="M4 19.5A2.5 2.5 0 016.5 17H20" fill="none" stroke="currentColor" stroke-width="1.5"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 014 19.5v-15A2.5 2.5 0 016.5 2z" fill="none" stroke="currentColor" stroke-width="1.5"/>'),
    "knowledge": ("circle", '<circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" stroke-width="1.5"/><path d="M12 6v6l4 2" fill="none" stroke="currentColor" stroke-width="1.5"/>'),
}

LAYER_LABELS = {"research": "Research", "learn": "Learn", "knowledge": "Knowledge"}
LAYER_ICONS = {"research": "\u25c7", "learn": "\u25c9", "knowledge": "\u25ce"}


def get_layer(url_path: str) -> str:
    if url_path.startswith("learn") or url_path.startswith("learn/"):
        return "learn"
    if url_path.startswith("knowledge") or url_path.startswith("knowledge/"):
        return "knowledge"
    return "research"


def generate_article_fingerprint(slug: str, title: str, pillar: str, content_type: str, tags: list) -> str:
    """Generate a unique SVG ident for an article — a mini tartan-like pattern.

    The fingerprint is derived from:
      - Pillar → base color
      - Content type → pattern style (bars/dots/diagonals)
      - Title hash → pattern permutation
      - Tags → number of columns
    """
    h = int(hashlib.md5((slug + title).encode()).hexdigest()[:6], 16)
    base_color = PILLAR_FINGERPRINT_COLORS.get(pillar, "#6366f1")
    column_count = 3 + (h % 5)
    row_count = 3 + ((h >> 8) % 3)

    bars = []
    for col in range(column_count):
        cx = 4 + col * (120 // column_count)
        bar_h = 5 + ((h >> (col * 4)) % 10)
        for row in range(row_count):
            if (h >> (col + row * 7)) & 1:
                ry = 4 + row * (28 // row_count)
                opacity = 0.3 + ((h >> (col * 3 + row * 2)) % 5) * 0.14
                if content_type == "learn":
                    bars.append(f'<circle cx="{cx}" cy="{ry + 6}" r="{bar_h // 4}" fill="{base_color}" opacity="{opacity}"/>')
                elif content_type == "knowledge":
                    bars.append(f'<line x1="{cx - 3}" y1="{ry}" x2="{cx + 3}" y2="{ry + 12}" stroke="{base_color}" stroke-width="1.5" opacity="{opacity}"/>')
                else:
                    bars.append(f'<rect x="{cx - 2}" y="{ry}" width="4" height="{bar_h}" rx="1" fill="{base_color}" opacity="{opacity}"/>')

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 32" width="120" height="32" aria-hidden="true">'
        f'<rect width="120" height="32" rx="2" fill="{base_color}" opacity="0.08"/>'
        f'{"".join(bars)}'
        f'</svg>'
    )


def layer_indicator_html(content_type: str, pillar: str = "") -> str:
    """Small visual badge showing which layer (research/learn/knowledge) the user is in."""
    sym_type, sym_path = LAYER_SYMBOLS.get(content_type, LAYER_SYMBOLS["research"])
    label = LAYER_LABELS.get(content_type, "Research")
    color = PILLAR_FINGERPRINT_COLORS.get(pillar, "#6366f1")
    return (
        f'<span class="inline-flex items-center gap-1.5 px-2 py-1 text-xs font-medium rounded" '
        f'style="background:{color}14;color:{color};border:1px solid {color}33">'
        f'<svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" aria-hidden="true">{sym_path}</svg>'
        f'{label}'
        f'</span>'
    )


def interest_score(post, now: datetime) -> float:
    sqi = post.signals.get("avg_sqi", 0.0) if post.signals else 0.0
    age_days = (now - (post.created_at or now)).days if post.created_at else 365
    age_days = max(0, age_days)
    recency = max(0.1, 1.0 - age_days / INTEREST_RECENCY_DAYS)
    return sqi * INTEREST_SQI_WEIGHT + recency * INTEREST_RECENCY_WEIGHT


def main():
    start_time = time.time()
    print("Starting AcaciaFund generator...")

    if not REGISTRY_PATH.exists():
        print(f"Error: {REGISTRY_PATH} not found.")
        return 1

    # Archive previous registry before loading (versioning)
    archive_dir = PROJECT_ROOT / ".registry-archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    if REGISTRY_PATH.exists():
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        archive_path = archive_dir / f"registry_{ts}.json"
        shutil.copy2(REGISTRY_PATH, archive_path)
        # Keep only last 20 archives
        archives = sorted(archive_dir.glob("registry_*.json"), reverse=True)
        for old in archives[20:]:
            old.unlink()
        print(f"  registry archived: {archive_path.name}")

    try:
        with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
            registry_data = json.load(f)
        registry = RegistryData(**registry_data)
    except Exception as e:
        print(f"Error loading registry: {e}")
        return 1

    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    STATIC_DST_DIR.mkdir(parents=True, exist_ok=True)

    if PIPELINE_STATIC_DIR.exists():
        for item in PIPELINE_STATIC_DIR.rglob("*"):
            if item.is_file():
                rel = item.relative_to(PIPELINE_STATIC_DIR)
                dest = STATIC_DST_DIR / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, dest)
    env = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=select_autoescape(["html", "xml"]),
    )
    env.filters["reading_time"] = reading_time_minutes
    env.filters["urlencode"] = lambda s: urlquote(s or '', safe='')
    env.filters["pictogram"] = pick_card_pictogram

    now = datetime.now(timezone.utc)
    year = now.year
    registry_bytes = REGISTRY_PATH.read_bytes() if REGISTRY_PATH.exists() else b""
    # Include CSS file hashes in build_hash so CSS changes bust CDN cache
    css_hasher = hashlib.md5()
    css_hasher.update(registry_bytes)
    for css_file in sorted(Path("static/css").glob("*.css")):
        css_hasher.update(css_file.read_bytes())
    for js_file in sorted(Path("static/js").glob("*.js")):
        css_hasher.update(js_file.read_bytes())
    build_hash = css_hasher.hexdigest()[:12]
    all_content = registry.content

    research_items = [c for c in all_content if c.content_type == "research"]
    learn_items = [c for c in all_content if c.content_type == "learn"]
    knowledge_items = [c for c in all_content if c.content_type == "knowledge"]

    # Research articles with bloom questions, mapped to learn-like items for cross-referencing
    research_learn_items = []
    for r in research_items:
        if r.bloom_questions and r.highest_bloom > 0:
            r_diff = "beginner" if r.highest_bloom <= 2 else "intermediate" if r.highest_bloom <= 4 else "advanced"
            research_learn_items.append({
                "slug": r.slug,
                "title": r.title,
                "pillar": r.pillar or "",
                "difficulty": r.difficulty or r_diff,
                "highest_bloom": r.highest_bloom or 0,
                "description": r.description[:200] if r.description else "",
                "date_str": r.date_str or "",
                "tags": r.tags,
                "prerequisites": [],
            })

    pillar_groups = group_by_pillar(research_items)

    BLOOM_NAMES = {1: "Remember", 2: "Understand", 3: "Apply", 4: "Analyse", 5: "Evaluate", 6: "Create"}

    def resolve_card_image(raw_path: str) -> str:
        """Resolve card image path to URL, handling REF: pointers."""
        if not raw_path:
            return ""
        p = Path(PROJECT_ROOT / raw_path.lstrip("/"))
        ref = _resolve_ref_file(p)
        if ref:
            return ref
        return f"{SITE_URL}{raw_path}" if raw_path.startswith("/") else f"{SITE_URL}/{raw_path}"

    ctx_base = {
        "build_hash": build_hash,
        "year": year,
        "site_url": SITE_URL,
        "plausible_domain": PLAUSIBLE_DOMAIN,
        "pillar_config": PILLAR_CONFIG,
        "pillar_emojis": PILLAR_EMOJIS,
        "pillar_names": PILLAR_NAMES,
        "site_description": SITE_DESCRIPTION,
        "resolve_card_image": resolve_card_image,
    }

    def render_template(template_name, **kw):
        return env.get_template(template_name).render(**kw)

    # --- KNOWLEDGE PAGES ---
    for item in knowledge_items:
        slug = item.slug
        page_path = canonical_path(slug_to_path(slug))
        if "/" in slug:
            out_dir = OUTPUT_DIR / slug
            out_dir.mkdir(parents=True, exist_ok=True)
            out_file = out_dir / "index.html"
        else:
            out_file = OUTPUT_DIR / f"{slug}.html"

        body = add_lazy_loading(item.body_html)
        body, toc_items = extract_headings(body)
        body = sanitize_domain_breakdown(body)
        body = inject_section_images(body, item.section_images, item)
        body = re.sub(r'<h2[^>]*>\s*' + re.escape(item.title.strip()) + r'\s*</h2>\s*', '', body, count=1)
        body = sanitize_text(body, strip_emoji=False)
        item.description = sanitize_text(item.description, strip_emoji=False)
        item.body_html = body

        kcat = KNOWLEDGE_CATEGORIES.get(item.knowledge_category, {})
        if kcat:
            kcat["slug"] = item.knowledge_category

        related_research = find_related(research_items, item, 3)
        related_learn = find_related(learn_items, item, 3)
        visual_fingerprint = generate_article_fingerprint(item.slug, item.title, item.pillar or "", "knowledge", item.tags)
        layer_badge = layer_indicator_html("knowledge", item.pillar or "")

        thumb_key = hashlib.md5(item.title.encode()).hexdigest()[:12]
        og_key = hashlib.md5(f"og_{item.title}".encode()).hexdigest()[:12]
        thumb_base = f"{SITE_URL}/static/images"
        feat_img_path = resolve_featured_image(item.featured_image or "")
        og_image_url = feat_img_path if feat_img_path else f"{SITE_URL}/static/images/og_{og_key}.svg"

        layer_sub = item.knowledge_category.replace("_", " ").title() if item.knowledge_category else item.pillar or ""
        # Serialize quiz data for knowledge articles too
        k_quiz_json = ""
        if item.bloom_questions:
            k_quiz_data = {"questions": []}
            for bq in item.bloom_questions[:10]:
                if isinstance(bq, dict) and "question" in bq:
                    qtype = bq.get("type", "mc")
                    opts = bq.get("options", [])
                    raw = bq.get("answer") if "answer" in bq else None
                    if raw is None:
                        correct_val = bq.get("correct", "")
                        raw = opts.index(correct_val) if isinstance(correct_val, str) and correct_val and correct_val in opts else 0
                    entry = {"q": bq["question"], "options": opts, "a": raw, "type": qtype}
                    if qtype == "open-ended":
                        entry["answer_text"] = bq.get("correct", opts[raw] if opts else "")
                    k_quiz_data["questions"].append(entry)
            if k_quiz_data["questions"]:
                k_quiz_json = json.dumps(k_quiz_data, ensure_ascii=False)
        html = render_template("knowledge.j2",
            content=item, page_path=page_path,
            toc_items=toc_items, kcat=kcat,
            related_research=related_research,
            related_learn=related_learn,
            visual_fingerprint=visual_fingerprint, layer_badge=layer_badge,
            thumbnail_base=thumb_base, thumbnail_key=thumbnail_key,
            og_image_url=og_image_url,
            quiz_json=k_quiz_json,
            is_index=False, page_type="knowledge", layer="knowledge",
            layer_icon=LAYER_ICONS["knowledge"], layer_sub=layer_sub, **ctx_base)
        out_file.write_text(html, encoding="utf-8")
        print(f"  knowledge: {out_file.relative_to(OUTPUT_DIR)}")

        # Write knowledge thumbnail SVGs + OG images (fractal engine)
        out_static = STATIC_DST_DIR / "images"
        out_static.mkdir(parents=True, exist_ok=True)
        pillar_k = item.pillar or "aml"
        scores_k = {}
        feat_k = resolve_featured_image(item.featured_image or "")
        icons_k = get_topic_icons(item.tags) if not feat_k else []
        svg_k = generate_thumbnail_svg(item.title, pillar_k, scores_k, width=600, height=340,
                                       featured_image_url=feat_k, layer="knowledge",
                                       fallback_icons=icons_k)
        (out_static / f"thumb_{thumb_key}.svg").write_text(svg_k, encoding="utf-8")
        og_svg = generate_og_image(item.title, pillar_k, scores_k,
                                   featured_image_url=feat_k, layer="knowledge",
                                   fallback_icons=icons_k)
        (out_static / f"og_{og_key}.svg").write_text(og_svg, encoding="utf-8")

    # --- KNOWLEDGE INDEX (sub-category grouped) ---
    knowledge_dir = OUTPUT_DIR / "knowledge"
    knowledge_dir.mkdir(parents=True, exist_ok=True)
    grouped: dict[str, list] = defaultdict(list)
    for k in knowledge_items:
        cat = k.knowledge_category or "reference"
        grouped[cat].append(k)
    for g in grouped.values():
        g.sort(key=lambda x: x.title or "")
    thumb_base = f"{SITE_URL}/static/images"
    html = render_template("knowledge_index.j2",
        content=_dummy("Knowledge Base", "knowledge",
                       description="AcaciaFund knowledge base: platform guides, methodology, reference glossaries, system architecture, and DataOps resources across all pillars."),
        items=knowledge_items, grouped=dict(grouped),
        categories=KNOWLEDGE_CATEGORIES,
        thumbnail_base=thumb_base, thumbnail_key=thumbnail_key,
        page_title="Knowledge Base",
        is_index=False, page_path="knowledge/",
        layer="knowledge", layer_icon=LAYER_ICONS["knowledge"],
        **ctx_base)
    (knowledge_dir / "index.html").write_text(html, encoding="utf-8")
    print("  category: knowledge/index.html")

    # --- LEARN PAGES ---
    BLOOM_ORDER = {"remember": 1, "understand": 2, "apply": 3, "analyze": 4, "evaluate": 5, "create": 6}
    # Apply curated relations and prerequisites from seed_learn.py
    for item in learn_items:
        slug = item.slug
        if slug in CURATED_RELATIONS:
            item.curated_relations = CURATED_RELATIONS[slug]
        if slug in LEARN_PREREQUISITES:
            item.prerequisites = LEARN_PREREQUISITES[slug]

    # Compute highest Bloom level from bloom_questions (must be done before article rendering)
    for l_item in learn_items:
        if l_item.bloom_questions:
            max_lvl = 0
            for q in l_item.bloom_questions:
                bl = q.get("bloom_level", "")
                lvl = BLOOM_ORDER.get(bl, 0)
                if lvl > max_lvl:
                    max_lvl = lvl
            l_item.highest_bloom = max_lvl
        else:
            l_item.highest_bloom = 0

    learn_lessons = sorted(
        [li for li in learn_items if li.slug != "learn"],
        key=lambda x: (DIFFICULTY_ORDER.get(x.difficulty or "beginner", 0), x.pillar or "", x.title or ""),
    )
    for i, item in enumerate(learn_items):
        # Determine prev/next only among actual lessons (exclude meta "learn" page)
        li = None
        for j, lli in enumerate(learn_lessons):
            if lli.slug == item.slug:
                li = j
                break
        if li is not None:
            prev_lesson = learn_lessons[li - 1] if li > 0 else None
            next_lesson = learn_lessons[li + 1] if li + 1 < len(learn_lessons) else None
        else:
            prev_lesson = None
            next_lesson = None
        slug = item.slug
        page_path = canonical_path(slug_to_path(slug))
        if "/" in slug:
            out_dir = OUTPUT_DIR / slug
            out_dir.mkdir(parents=True, exist_ok=True)
            out_file = out_dir / "index.html"
        else:
            out_file = OUTPUT_DIR / f"{slug}.html"
        body = add_lazy_loading(item.body_html)
        body, toc_items = extract_headings(body)
        body = sanitize_domain_breakdown(body)
        body = inject_section_images(body, item.section_images, item)
        body = re.sub(r'<h2[^>]*>\s*' + re.escape(item.title.strip()) + r'\s*</h2>\s*', '', body, count=1)
        body = sanitize_text(body, strip_emoji=False)
        item.description = sanitize_text(item.description, strip_emoji=False)
        item.body_html = body


        pillar = item.pillar or ""
        pconf = PILLAR_CONFIG.get(pillar) if pillar else None
        related_research = find_related(research_items, item, 3)
        related_knowledge = find_related(knowledge_items, item, 3)
        visual_fingerprint = generate_article_fingerprint(item.slug, item.title, pillar, "learn", item.tags)
        layer_badge = layer_indicator_html("learn", pillar)
        thumb_key = hashlib.md5(item.title.encode()).hexdigest()[:12]
        og_key = hashlib.md5(f"og_{item.title}".encode()).hexdigest()[:12]
        thumb_base = f"{SITE_URL}/static/images"
        feat_img_path = resolve_featured_image(item.featured_image or "")
        og_image_url = feat_img_path if feat_img_path else f"{SITE_URL}/static/images/og_{og_key}.svg"
        (out_static / f"og_{og_key}.svg").write_text(og_svg, encoding="utf-8")

        # Serialize quiz data for learning_hub.js
        quiz_json = ""
        if item.bloom_questions:
            quiz_data = {"questions": []}
            for bq in item.bloom_questions[:10]:
                if isinstance(bq, dict) and "question" in bq:
                    qtype = bq.get("type", "mc")
                    opts = bq.get("options", [])
                    # Normalize answer: supports both "answer" (int) and "correct" (string value)
                    raw = bq.get("answer") if "answer" in bq else None
                    if raw is None:
                        correct_val = bq.get("correct", "")
                        if isinstance(correct_val, str) and correct_val and opts:
                            raw = opts.index(correct_val) if correct_val in opts else 0
                        else:
                            raw = 0
                    entry = {"q": bq["question"], "options": opts, "a": raw, "type": qtype}
                    if qtype == "open-ended":
                        entry["answer_text"] = bq.get("correct", opts[raw] if opts else "")
                    quiz_data["questions"].append(entry)
            if quiz_data["questions"]:
                quiz_json = json.dumps(quiz_data, ensure_ascii=False)

        bl_name = BLOOM_NAMES.get(item.highest_bloom or 0, "")
        layer_sub = f"Level {item.highest_bloom}: {bl_name}" if bl_name else ""
        html = render_template("learn.j2",
            content=item, page_path=page_path,
            toc_items=toc_items, pconf=pconf,
            prev_lesson=prev_lesson, next_lesson=next_lesson,
            related_research=related_research,
            related_knowledge=related_knowledge,
            visual_fingerprint=visual_fingerprint, layer_badge=layer_badge,
            thumbnail_base=thumb_base, thumbnail_key=thumbnail_key,
            og_image_url=og_image_url, quiz_json=quiz_json,
            featured_image=resolve_section_image(item.featured_image),
            image_credit=item.image_credit,
            is_index=False, layer="learn",
            layer_icon=LAYER_ICONS["learn"], layer_sub=layer_sub, **ctx_base)
        out_file.write_text(html, encoding="utf-8")
        print(f"  learn: {out_file.relative_to(OUTPUT_DIR)}")

        # Write learn thumbnail SVGs + OG images (fractal engine)
        out_static = STATIC_DST_DIR / "images"
        out_static.mkdir(parents=True, exist_ok=True)
        pillar_l = item.pillar or "aml"
        scores_l = {}
        feat_l = resolve_featured_image(item.featured_image or "")
        icons_l = get_topic_icons(item.tags) if not feat_l else []
        svg_l = generate_thumbnail_svg(item.title, pillar_l, scores_l, width=600, height=340,
                                       featured_image_url=feat_l, layer="learn",
                                       fallback_icons=icons_l)
        (out_static / f"thumb_{thumb_key}.svg").write_text(svg_l, encoding="utf-8")
        og_svg = generate_og_image(item.title, pillar_l, scores_l,
                                   featured_image_url=feat_l, layer="learn",
                                   fallback_icons=icons_l)
        (out_static / f"og_{og_key}.svg").write_text(og_svg, encoding="utf-8")

    # --- LEARN INDEX (difficulty-grouped) ---
    learn_dir = OUTPUT_DIR / "learn"
    learn_dir.mkdir(parents=True, exist_ok=True)
    learn_grouped: dict[str, list] = defaultdict(list)
    for l_item in learn_items:
        diff = l_item.difficulty or "beginner"
        learn_grouped[diff.capitalize()].append(l_item)
    for g in learn_grouped.values():
        g.sort(key=lambda x: x.title or "")
    bloom_first_articles: dict[int, str] = {}
    for l_item in learn_items:
        bl = l_item.highest_bloom or 0
        if bl > 0 and bl not in bloom_first_articles:
            bloom_first_articles[bl] = l_item.slug
    thumb_base = f"{SITE_URL}/static/images"

    # Load learning paths from pillars.toml
    toml_path = Path(__file__).parent / "etc" / "pillars.toml"
    learning_paths_data = {}
    if toml_path.exists():
        with open(toml_path, "rb") as _tf:
            _toml_cfg = tomllib.load(_tf)
        for _pkey, _ppath in _toml_cfg.get("learning_paths", {}).items():
            steps = []
            for _step in _ppath.get("steps", []):
                _bloom = _step.get("bloom", "")
                _bloom_num = {"remember": 1, "understand": 2, "apply": 3,
                              "analyze": 4, "evaluate": 5, "create": 6}.get(_bloom, 0)
                _matching = [a for a in learn_items
                             if a.pillar == _pkey and (a.highest_bloom or 0) == _bloom_num]
                _articles = [{"slug": a.slug, "title": a.title, "difficulty": a.difficulty or ""}
                             for a in sorted(_matching, key=lambda x: x.title or "")]
                steps.append({
                    "bloom": _bloom,
                    "bloom_num": _bloom_num,
                    "label": _step.get("label", ""),
                    "articles": _articles,
                    "article_count": len(_articles),
                })
            learning_paths_data[_pkey] = {
                "label": _ppath.get("label", ""),
                "steps": steps,
            }

    html = render_template("learn_index.j2",
        content=_dummy("Learning Hub", "learn",
                       description="Interactive lessons, tutorials, and quizzes on AML compliance, financial markets, science, and DataOps — powered by Bloom taxonomy."),
        items=learn_items, grouped=dict(learn_grouped),
        thumbnail_base=thumb_base, thumbnail_key=thumbnail_key,
        page_title="Learning Hub",
        is_index=False, page_path="learn/",
        layer="learn", layer_icon=LAYER_ICONS["learn"],
        bloom_first_articles=bloom_first_articles,
        learning_paths_data=learning_paths_data,
        research_learn_items=research_learn_items,
        **ctx_base)
    (learn_dir / "index.html").write_text(html, encoding="utf-8")
    print("  category: learn/index.html")

    # --- RESEARCH PAGES (blog posts) ---
    for i, item in enumerate(research_items):
        slug = item.slug
        page_path = canonical_path(slug_to_path(slug))
        if "/" in slug:
            out_dir = OUTPUT_DIR / slug
            out_dir.mkdir(parents=True, exist_ok=True)
            out_file = out_dir / "index.html"
        else:
            out_file = OUTPUT_DIR / f"{slug}.html"

        body = add_lazy_loading(item.body_html)
        body, toc_items = extract_headings(body)
        body = sanitize_domain_breakdown(body)
        body = inject_section_images(body, item.section_images, item)
        body = re.sub(r'<h2[^>]*>\s*' + re.escape(item.title.strip()) + r'\s*</h2>\s*', '', body, count=1)
        body = sanitize_text(body, strip_emoji=True)
        item.description = sanitize_text(item.description, strip_emoji=True)

        prev_post = research_items[i + 1] if i + 1 < len(research_items) else None
        next_post = research_items[i - 1] if i > 0 else None
        pillar = item.pillar or "aml"
        related = find_related(research_items, item, 3)
        related_learn = find_related(learn_items, item, 3)
        visual_fingerprint = generate_article_fingerprint(item.slug, item.title, pillar, "research", item.tags)
        layer_badge = layer_indicator_html("research", pillar)

        pconf = PILLAR_CONFIG.get(pillar, PILLAR_CONFIG["aml"])
        sqi_svg = generate_sqi_badge(item.signals.get("avg_sqi", SQI_DEFAULT)) if item.signals else ""
        og_key = hashlib.md5(f"og_{item.title}".encode()).hexdigest()[:12]
        feat_img_path = resolve_featured_image(item.featured_image or "")
        og_image_url = feat_img_path if feat_img_path else f"{SITE_URL}/static/images/og_{og_key}.svg"
        thumb_base = f"{SITE_URL}/static/images"
        # Serialize quiz data for research articles
        r_quiz_json = ""
        if item.bloom_questions:
            r_quiz_data = {"questions": []}
            for bq in item.bloom_questions[:10]:
                if isinstance(bq, dict) and "question" in bq:
                    qtype = bq.get("type", "mc")
                    opts = bq.get("options", [])
                    raw = bq.get("answer") if "answer" in bq else None
                    if raw is None:
                        correct_val = bq.get("correct", "")
                        raw = opts.index(correct_val) if isinstance(correct_val, str) and correct_val and correct_val in opts else 0
                    entry = {"q": bq["question"], "options": opts, "a": raw, "type": qtype}
                    if qtype == "open-ended":
                        entry["answer_text"] = bq.get("correct", opts[raw] if opts else "")
                    r_quiz_data["questions"].append(entry)
            if r_quiz_data["questions"]:
                r_quiz_json = json.dumps(r_quiz_data, ensure_ascii=False)
        topic_sub = _pick_subtopic([item.title], pillar)
        topic_icon_html = render_topic_icon(topic_sub, PILLAR_COLORS.get(pillar, PILLAR_COLORS["aml"])["accent"])
        html = render_template("blog_post.j2",
            content=item, page_path=page_path, page_body=body,
            prev_post=prev_post, next_post=next_post,
            pconf=pconf, sqi_svg=sqi_svg,
            og_image_url=og_image_url,
            thumbnail_base=thumb_base, thumbnail_key=thumbnail_key,
            toc_items=toc_items, related_posts=related,
            related_learn=related_learn,
            visual_fingerprint=visual_fingerprint, layer_badge=layer_badge,
            featured_image=resolve_section_image(item.featured_image),
            image_credit=item.image_credit,
            quiz_json=r_quiz_json,
            topic_icon_html=topic_icon_html,
            layer_sub=pconf["label"], **ctx_base)
        out_file.write_text(html, encoding="utf-8")
        print(f"  research: {out_file.relative_to(OUTPUT_DIR)}")

        # Write SVGs (fractal engine — thumbnail + OG image)
        out_static = STATIC_DST_DIR / "images"
        out_static.mkdir(parents=True, exist_ok=True)
        key = hashlib.md5(item.title.encode()).hexdigest()[:12]
        scores_r = item.signals or {"sqi": SQI_DEFAULT}
        if not isinstance(scores_r, dict):
            scores_r = {"sqi": SQI_DEFAULT}
        feat_r = resolve_featured_image(item.featured_image or "")
        icons_r = get_topic_icons(item.tags) if not feat_r else []
        svg_r = generate_thumbnail_svg(item.title, pillar, scores_r, width=600, height=340,
                                       featured_image_url=feat_r, layer="research",
                                       fallback_icons=icons_r)
        (out_static / f"thumb_{key}.svg").write_text(svg_r, encoding="utf-8")
        og_svg = generate_og_image(item.title, pillar, scores_r,
                                   featured_image_url=feat_r, layer="research",
                                   fallback_icons=icons_r)
        (out_static / f"og_{og_key}.svg").write_text(og_svg, encoding="utf-8")

    # --- CARD THUMBNAILS — generate 200x150 thumbnails for all articles with featured_image ---
    card_images: dict[str, str] = {}
    if (PIPELINE_STATIC_DIR / "images" / "generated").exists():
        for article in all_content:
            if article.featured_image:
                img = generate_card_thumbnail(article.featured_image, article.slug)
                if img:
                    card_images[article.slug] = img
        # Ensure thumbnails are also in dist/ (static copy happened before thumbnail gen)
        gen_src = PIPELINE_STATIC_DIR / "images" / "generated"
        gen_dst = STATIC_DST_DIR / "images" / "generated"
        for card_file in gen_src.rglob("*_card.*"):
            if card_file.is_file():
                rel = card_file.relative_to(gen_src)
                dest = gen_dst / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(card_file, dest)

    # --- TOPIC ICONS FOR RESEARCH CARDS ---
    card_topic_icons: dict[str, str] = {}
    for article in research_items:
        sub = _pick_subtopic([article.title], article.pillar or "aml")
        accent = PILLAR_COLORS.get(article.pillar or "aml", PILLAR_COLORS["aml"])["accent"]
        html_icon = render_topic_icon(sub, accent)
        if html_icon:
            card_topic_icons[article.slug] = html_icon

    # --- RESEARCH INDEX (/research/) ---
    research_dir = OUTPUT_DIR / "research"
    research_dir.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    scored = [(interest_score(p, now), p) for p in research_items]
    scored.sort(key=lambda x: -x[0])
    sorted_research = [p for _, p in scored]
    html = render_template("category_index.j2",
        content=_dummy("Research", "research",
                       description="Quality-scored research articles on AML, financial markets, and science. Automatically classified from HackerNews and arXiv using Bloom taxonomy."),
        category="research", items=sorted_research,
        page_title="Research",
        is_index=False, page_path="research/", card_images=card_images,
        card_topic_icons=card_topic_icons, **ctx_base)
    (research_dir / "index.html").write_text(html, encoding="utf-8")
    print("  category: research/index.html")

    # --- PILLAR SUB-PAGES ---
    for pillar in PILLAR_CONFIG:
        p_posts = pillar_groups.get(pillar, [])
        out_dir = OUTPUT_DIR / pillar
        out_dir.mkdir(parents=True, exist_ok=True)
        pconf = PILLAR_CONFIG.get(pillar, PILLAR_CONFIG["aml"])
        # Prepare posts data for JavaScript
        pillar_posts_data = []
        for p in p_posts:
            post_data = {
                'slug': p.slug,
                'title': p.title or '',
                'description': p.description or '',
                'date_str': p.date_str or '',
                'content_type': p.content_type or 'research',
                'pillar': p.pillar or '',
                'pillar_icon': PILLAR_EMOJIS.get(p.pillar or '', ''),
                'pillar_color': PILLAR_CONFIG.get(p.pillar or '', {}).get('color', '#6366f1'),
                'pconf_label': pconf['label'],
                'reading_time': reading_time_minutes(p.body_html or '') if p.body_html else None,
                'risk_count': len(p.quality_flags or []),
                'source_breakdown': p.source_breakdown or {},
                'featured_image': p.featured_image or '',
                'topic_icon': card_topic_icons.get(p.slug, ''),
                'pictogram': pick_card_pictogram(p) or 'icon-research.svg',
                'signals': p.signals or {}
            }
            pillar_posts_data.append(post_data)
        
        html = render_template("pillar_index.j2",
            content=_dummy(pconf['heading'], "index",
                           description=pconf.get("description", f"{pconf['label']} research articles — quality-scored and Bloom-classified.")),
            pillar=pillar, pconf=pconf,
            posts=p_posts, is_index=False, page_path=f"{pillar}/",
            page_title=pconf["heading"],
            layer_sub=pconf["label"],
            thumbnail_base=f"{SITE_URL}/static/images", thumbnail_key=thumbnail_key,
            card_images=card_images, card_topic_icons=card_topic_icons,
            pillar_posts_data=pillar_posts_data, **ctx_base)
        (out_dir / "index.html").write_text(html, encoding="utf-8")
        print(f"  pillar: {pillar}/index.html")

    # --- AML SIGNALS DASHBOARD ---
    aml_research = [p for p in research_items if p.pillar == "aml"]
    aml_learn = [l for l in learn_items if l.pillar == "aml"]
    tag_cloud: dict[str, int] = {}
    entity_cloud: dict[str, int] = {}
    source_totals: dict[str, int] = {}
    cross_pillar_links: dict[str, int] = {}
    timeline: dict[str, int] = {}
    for a in aml_research:
        for t in (a.tags or []):
            tag_cloud[t] = tag_cloud.get(t, 0) + 1
        signals = a.signals or {}
        for e in (signals.get("top_entities", []) or []):
            entity_cloud[e] = entity_cloud.get(e, 0) + 1
        sb = a.source_breakdown or {}
        for k, v in sb.items():
            source_totals[k] = source_totals.get(k, 0) + v
        cross = a.cross_pillar_html or ""
        if "stock" in cross.lower() or "markets" in cross.lower():
            cross_pillar_links["stock"] = cross_pillar_links.get("stock", 0) + 1
        if "science" in cross.lower():
            cross_pillar_links["science"] = cross_pillar_links.get("science", 0) + 1
        if "data-engineering" in cross.lower() or "data engineering" in cross.lower():
            cross_pillar_links["data-engineering"] = cross_pillar_links.get("data-engineering", 0) + 1
        if a.date_str:
            month = a.date_str[:7]
            timeline[month] = timeline.get(month, 0) + 1
    tag_sorted = sorted(tag_cloud.items(), key=lambda x: -x[1])
    entity_sorted = sorted(entity_cloud.items(), key=lambda x: -x[1])
    source_sorted = sorted(source_totals.items(), key=lambda x: -x[1])
    source_max = max((c for _, c in source_sorted), default=1)
    cp_sorted = sorted(cross_pillar_links.items(), key=lambda x: -x[1])
    tl_sorted = sorted(timeline.items())
    tl_max = max(timeline.values()) if timeline else 1
    avg_sqi = sum((a.signals or {}).get("avg_sqi", 0) or 0 for a in aml_research) / max(len(aml_research), 1)
    unique_tags = set()
    for a in aml_research:
        for t in (a.tags or []):
            unique_tags.add(t)
    unique_entities = set()
    for a in aml_research:
        for e in ((a.signals or {}).get("top_entities", []) or []):
            unique_entities.add(e)

    aml_signals_html = render_template("aml_signals.j2",
        content=_dummy("AML Signals Dashboard", "index",
                       description="Aggregated AML risk signals, entity profiles, and coverage metrics across AML articles."),
        aml_count=len(aml_research),
        avg_sqi=avg_sqi,
        unique_tags_count=len(unique_tags),
        unique_entities_count=len(unique_entities),
        tag_cloud=tag_sorted,
        entity_cloud=entity_sorted,
        source_totals=source_sorted,
        source_max=source_max,
        cross_pillar_summary=cp_sorted,
        timeline=tl_sorted,
        timeline_max=tl_max,
        recent_articles=sorted(aml_research, key=lambda x: x.date_str or "", reverse=True)[:10],
        learn_path=aml_learn,
        is_index=False, page_path="aml/signals/",
        page_title="AML Signals Dashboard",
        thumbnail_base=f"{SITE_URL}/static/images", thumbnail_key=thumbnail_key, **ctx_base)
    sig_dir = OUTPUT_DIR / "aml" / "signals"
    sig_dir.mkdir(parents=True, exist_ok=True)
    (sig_dir / "index.html").write_text(aml_signals_html, encoding="utf-8")
    print("  signals: aml/signals/index.html")

    # --- HOMEPAGE (filter future posts from featured/recent) ---
    published_research = [p for p in sorted_research if not is_future_post(p)]
    # Freshness cutoff: exclude articles older than 90 days from featured + recent
    ninety_days_ago = now - timedelta(days=90)
    fresh_posts = [p for p in published_research if not p.created_at or p.created_at >= ninety_days_ago]
    featured = fresh_posts[:3] if len(fresh_posts) >= 3 else published_research[:3]
    # Hero: highest-SQI article from last 7 days
    seven_days_ago = now - timedelta(days=7)
    recent_articles = [p for p in published_research if p.created_at and p.created_at >= seven_days_ago]
    hero_article = max(recent_articles, key=lambda x: (x.signals or {}).get("avg_sqi", 0)) if recent_articles else None
    home_og_key = hashlib.md5(b"AcaciaFund homepage").hexdigest()[:12]
    home_og_url = f"{SITE_URL}/static/images/og_{home_og_key}.svg"
    index_html = render_template("index.j2",
        content=_dummy("Research Synthesis & Learning", "index",
                       description="AcaciaFund — research synthesis & experimental learning platform. Automated classification of HackerNews + arXiv content using Bloom taxonomy."),
        is_index=True, page_path="",
        og_image_url=home_og_url,
        featured_posts=featured, recent_posts=fresh_posts[:12],
        learn_items=learn_items[:6], knowledge_items=knowledge_items[:6],
        hero_article=hero_article,
        thumbnail_base=f"{SITE_URL}/static/images", thumbnail_key=thumbnail_key, **ctx_base)
    (OUTPUT_DIR / "index.html").write_text(index_html, encoding="utf-8")
    # Write homepage OG image
    out_static = STATIC_DST_DIR / "images"
    out_static.mkdir(parents=True, exist_ok=True)
    home_og_svg = generate_og_image("AcaciaFund — Research Synthesis & Learning", "aml", {"sqi": 0.7})
    (out_static / f"og_{home_og_key}.svg").write_text(home_og_svg, encoding="utf-8")
    print("  index: index.html")

    # --- /contact/ redirect to /knowledge/contact/ ---
    contact_dir = OUTPUT_DIR / "contact"
    contact_dir.mkdir(parents=True, exist_ok=True)
    (contact_dir / "index.html").write_text(
        f'<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
        f'<title>Contact — AcaciaFund</title>'
        f'<meta http-equiv="refresh" content="0;url={SITE_URL}/knowledge/contact/">'
        f'<link rel="canonical" href="{SITE_URL}/knowledge/contact/">'
        f'</head><body><p><a href="{SITE_URL}/knowledge/contact/">Contact — AcaciaFund</a></p></body></html>',
        encoding="utf-8")
    print("  redirect: /contact/ → /knowledge/contact/")

    # --- /science/ redirect to /research/ ---
    science_dir = OUTPUT_DIR / "science"
    science_dir.mkdir(parents=True, exist_ok=True)
    (science_dir / "index.html").write_text(
        f'<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
        f'<title>Science — AcaciaFund</title>'
        f'<meta http-equiv="refresh" content="0;url={SITE_URL}/research/">'
        f'<link rel="canonical" href="{SITE_URL}/research/">'
        f'</head><body><p><a href="{SITE_URL}/research/">Research — AcaciaFund</a></p></body></html>',
        encoding="utf-8")
    print("  redirect: /science/ → /research/")

    # --- 404 ---
    _suggestions = sorted(all_content, key=lambda c: hashlib.md5(c.slug.encode()).hexdigest())[:3]
    html = render_template("404.j2",
        content=_dummy("Page Not Found — AcaciaFund", "error"),
        is_index=False, page_path="404.html", page_type="error",
        suggestions=_suggestions, **ctx_base)
    (OUTPUT_DIR / "404.html").write_text(html, encoding="utf-8")
    print("  error: 404.html")

    # --- TAG ARCHIVE PAGES ---
    tag_items: dict[str, list] = defaultdict(list)
    for c in all_content:
        for t in (c.tags or []):
            tag_items[t.lower().strip()].append(c)
    tags_dir = OUTPUT_DIR / "tags"
    tags_dir.mkdir(parents=True, exist_ok=True)
    for tag_slug, tag_posts in sorted(tag_items.items()):
        tag_slug_clean = re.sub(r'[^a-z0-9]+', '-', tag_slug).strip('-')
        if not tag_slug_clean:
            continue
        tag_posts.sort(key=lambda x: x.created_at or datetime.min, reverse=True)
        thin = len(tag_posts) < 3
        tag_out = tags_dir / tag_slug_clean / "index.html"
        tag_out.parent.mkdir(parents=True, exist_ok=True)
        html = render_template("tag_index.j2",
            content=_dummy(f"Tag: {tag_slug}", "tag"),
            tag=tag_slug, items=tag_posts,
            is_index=False, page_path=f"tags/{tag_slug_clean}/",
            robots_noindex=thin, **ctx_base)
        tag_out.write_text(html, encoding="utf-8")
    if tag_items:
        tag_out = tags_dir / "index.html"
        html = render_template("tag_index.j2",
            content=_dummy("Tags", "tag"),
            tag="", items=[], all_tags=sorted(tag_items.keys()),
            is_index=False, page_path="tags/", **ctx_base)
        tag_out.write_text(html, encoding="utf-8")
        print(f"  tags: {len(tag_items)} tag pages + index")

    # --- ADMIN PANEL ---
    admin_dir = OUTPUT_DIR / "admin"
    admin_dir.mkdir(parents=True, exist_ok=True)
    
    # Image and article counts
    image_count = len(list(STATIC_DST_DIR.glob("images/generated/**/*.webp")))
    article_count = len(all_content)
    
    # Calculate stats for dashboard
    articles_with_images = sum(1 for c in all_content if c.featured_image)
    articles_needing_images = article_count - articles_with_images
    low_score_sections = sum(1 for c in all_content if (c.signals or {}).get("avg_score", 100) < 70)
    orphan_images = 0  # Would need to check which images are actually used
    svg_fallbacks = 0  # Count articles using SVG fallbacks
    manifest_entries = 0  # Count manifest overrides
    
    # Count by content type
    by_type_list = []
    by_type_dict = defaultdict(lambda: {"total": 0, "with_images": 0, "without_images": 0})
    for c in all_content:
        ct = c.content_type or "unknown"
        by_type_dict[ct]["total"] += 1
        if c.featured_image:
            by_type_dict[ct]["with_images"] += 1
        else:
            by_type_dict[ct]["without_images"] += 1
    for ct, data in sorted(by_type_dict.items()):
        by_type_list.append({"type": ct, "total": data["total"], "with_images": data["with_images"], "without_images": data["without_images"]})
    
    # Count by source
    by_source_dict = defaultdict(int)
    for c in all_content:
        sb = c.source_breakdown or {}
        for src, count in sb.items():
            by_source_dict[src] += count
    by_source = dict(by_source_dict)
    
    stats = {
        "total_images": image_count,
        "total_articles": article_count,
        "with_images": articles_with_images,
        "without_images": articles_needing_images,
        "with_images_pct": round(articles_with_images / article_count * 100, 1) if article_count > 0 else 0,
        "low_score": low_score_sections,
        "low_score_sections": low_score_sections,
        "orphan_images": orphan_images,
        "svg_fallbacks": svg_fallbacks,
        "manifest_entries": manifest_entries,
        "by_type": by_type_list,
        "by_source": by_source,
    }
    
    # Dashboard - pass stats fields directly
    html = render_template("admin/dashboard.html",
        content=_dummy("Admin Dashboard", "admin"),
        active_page="dashboard",
        image_count=image_count,
        article_count=article_count,
        stats_total_images=stats["total_images"],
        stats_total_articles=stats["total_articles"],
        stats_with_images=stats["with_images"],
        stats_without_images=stats["without_images"],
        stats_with_images_pct=stats["with_images_pct"],
        stats_low_score=stats["low_score"],
        stats_orphan_images=stats["orphan_images"],
        stats_svg_fallbacks=stats["svg_fallbacks"],
        stats_manifest_entries=stats["manifest_entries"],
        stats_by_type=stats["by_type"],
        stats_by_source=stats["by_source"],
        **ctx_base)
    (admin_dir / "index.html").write_text(html, encoding="utf-8")
    
    # Gallery
    html = render_template("admin/gallery.html",
        content=_dummy("Image Gallery", "admin"),
        active_page="gallery",
        image_count=image_count,
        article_count=article_count,
        **ctx_base)
    (admin_dir / "gallery.html").write_text(html, encoding="utf-8")
    
    # Articles
    html = render_template("admin/article_list.html",
        content=_dummy("Articles", "admin"),
        active_page="articles",
        image_count=image_count,
        article_count=article_count,
        articles=all_content,
        **ctx_base)
    (admin_dir / "articles.html").write_text(html, encoding="utf-8")
    
    # Load admin credentials from .env
    admin_username, admin_password = load_admin_credentials()
    
    # Redirect index to login
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="refresh" content="0;url=login.html">
    <title>Redirecting...</title>
</head>
<body>
    <p>Redirecting to login page...</p>
    <script>
        window.location.href = 'login.html';
    </script>
</body>
</html>"""
    (admin_dir / "index.html").write_text(html, encoding="utf-8")
    
    # Login
    html = render_template("admin/login.html",
        content=_dummy("Admin Login", "admin"),
        admin_username=admin_username,
        admin_password=admin_password,
        **ctx_base)
    (admin_dir / "login.html").write_text(html, encoding="utf-8")
    
    print("  admin: login, dashboard, gallery, articles")

    # --- SEARCH INDEX ---
    search_index = []
    for c in all_content:
        search_index.append({
            "title": c.title,
            "description": (c.description or "")[:300],
            "slug": c.slug,
            "pillar": c.pillar or "",
            "content_type": c.content_type or "",
            "tags": c.tags or [],
            "date_str": c.date_str or "",
            "difficulty": c.difficulty or "",
        })
    (STATIC_DST_DIR / "search-index.json").write_text(
        json.dumps(search_index, ensure_ascii=False), encoding="utf-8")
    print("  search: search-index.json (" + str(len(search_index)) + " entries)")

    # --- SEARCH PAGE ---
    search_dir = OUTPUT_DIR / "search"
    search_dir.mkdir(parents=True, exist_ok=True)
    html = render_template("search.j2",
        content=_dummy("Search — AcaciaFund", "search"),
        is_index=False, page_path="search/", **ctx_base)
    (search_dir / "index.html").write_text(html, encoding="utf-8")
    print("  search: search/index.html")

    # --- FEED ---
    published_for_feed = [p for p in research_items if not is_future_post(p)]
    feed_candidates = [p.created_at for p in published_for_feed[:20] if p.created_at]
    feed_updated = max(feed_candidates).isoformat() if feed_candidates else now.isoformat()
    feed_items = []
    for post in published_for_feed[:20]:
        path = canonical_path(slug_to_path(post.slug))
        desc = (post.description or post.body_html[:200])[:300]
        post_updated = (post.created_at or now).isoformat()
        feed_items.append(f"""  <entry>
    <title>{post.title}</title>
    <link href="{SITE_URL}/{path}" rel="alternate" type="text/html"/>
    <id>{SITE_URL}/{path}</id>
    <updated>{post_updated}</updated>
    <summary>{desc}</summary>
  </entry>""")
    feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>AcaciaFund Research</title>
  <link href="{SITE_URL}/feed.xml" rel="self" type="application/atom+xml"/>
  <link href="{SITE_URL}/" rel="alternate" type="text/html"/>
  <id>{SITE_URL}/feed.xml</id>
  <updated>{feed_updated}</updated>
  <author><name>{SITE_NAME}</name></author>
{chr(10).join(feed_items)}
</feed>"""
    (OUTPUT_DIR / "feed.xml").write_text(feed, encoding="utf-8")
    print("  feed: feed.xml")

    # --- SITEMAP ---
    today = datetime.now(timezone.utc).date().isoformat()
    section_pages = list(pillar_groups) + ["research", "learn", "knowledge", "search"]
    tag_slugs = []
    for tag_slug in sorted(tag_items.keys()):
        slug_clean = re.sub(r'[^a-z0-9]+', '-', tag_slug).strip('-')
        if slug_clean:
            tag_slugs.append(slug_clean)
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    sm.append(f'  <url><loc>{SITE_URL}/</loc><lastmod>{today}</lastmod><changefreq>daily</changefreq><priority>1.0</priority></url>')
    sm.append(f'  <url><loc>{SITE_URL}/tags/</loc><lastmod>{today}</lastmod><changefreq>weekly</changefreq><priority>0.4</priority></url>')
    for c in all_content:
        if is_future_post(c):
            continue
        lastmod = c.updated_at.date().isoformat() if c.updated_at else (c.created_at.date().isoformat() if c.created_at else today)
        sm.append(f'  <url><loc>{slug_to_url(c.slug)}</loc><lastmod>{lastmod}</lastmod><changefreq>monthly</changefreq><priority>0.6</priority></url>')
    for p in section_pages:
        sm.append(f'  <url><loc>{SITE_URL}/{p}/</loc><lastmod>{today}</lastmod><changefreq>weekly</changefreq><priority>0.8</priority></url>')
    for slug_clean in tag_slugs:
        sm.append(f'  <url><loc>{SITE_URL}/tags/{slug_clean}/</loc><lastmod>{today}</lastmod><changefreq>weekly</changefreq><priority>0.3</priority></url>')
    sm.append("</urlset>")
    (OUTPUT_DIR / "sitemap.xml").write_text("\n".join(sm), encoding="utf-8")

    # --- ROBOTS ---
    # NOTE: Cloudflare Pages injects its own robots.txt rules at CDN level.
    # Our rules come AFTER Cloudflare's, so first-match-wins means Cloudflare's
    # Disallow rules take precedence. To fix AI crawler access, disable
    # "AI Scrapers and Crawlers" in Cloudflare Dashboard > Security > Bots.
    robots_txt = f"""User-agent: *
Allow: /

Sitemap: {SITE_URL}/sitemap.xml
"""
    (OUTPUT_DIR / "robots.txt").write_text(robots_txt, encoding="utf-8")

    # --- Copy llms.txt to site root (geo-checker expects /llms.txt) ---
    llms_src = STATIC_DST_DIR / "llms.txt"
    if llms_src.exists():
        (OUTPUT_DIR / "llms.txt").write_text(llms_src.read_text(encoding="utf-8"), encoding="utf-8")
    # --- Copy ai-plugin.json to .well-known ---
    ai_plugin_src = STATIC_DST_DIR / ".well-known" / "ai-plugin.json"
    if ai_plugin_src.exists():
        ai_plugin_dst = OUTPUT_DIR / ".well-known" / "ai-plugin.json"
        ai_plugin_dst.parent.mkdir(parents=True, exist_ok=True)
        ai_plugin_dst.write_text(ai_plugin_src.read_text(encoding="utf-8"), encoding="utf-8")
    # --- Copy skill.md and agent-permissions.json to root ---
    for root_file in ("skill.md", "agent-permissions.json"):
        root_src = STATIC_DST_DIR / root_file
        if root_src.exists():
            (OUTPUT_DIR / root_file).write_text(root_src.read_text(encoding="utf-8"), encoding="utf-8")
    # --- Copy auth.md to dist root ---
    auth_src = STATIC_DST_DIR / "auth.md"
    if auth_src.exists():
        (OUTPUT_DIR / "auth.md").write_text(auth_src.read_text(encoding="utf-8"), encoding="utf-8")
    # --- Copy .well-known agent-readiness files ---
    well_known_files = [
        (".well-known", "api-catalog"),
        (".well-known", "oauth-protected-resource"),
        (".well-known", "oauth-authorization-server"),
        (".well-known/mcp", "server-card.json"),
        (".well-known/agent-skills", "index.json"),
    ]
    for subdir, fname in well_known_files:
        src = STATIC_DST_DIR / subdir / fname
        if src.exists():
            dst = OUTPUT_DIR / subdir / fname
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")

    # --- LLMs-full.txt (comprehensive content index for AI crawlers) ---
    llms_full_lines = [
        "# AcaciaFund - Full Content Index",
        "# Research synthesis and experimental learning platform",
        "# All content is freely available for non-commercial educational use",
        "",
        "## Content Overview",
        f"# Total articles: {len([c for c in all_content if not is_future_post(c)])}",
        f"# Total learn lessons: {len([c for c in all_content if c.content_type == 'learn' and not is_future_post(c)])}",
        f"# Pillars: AML (anti-money laundering), Markets (market analysis), Data Engineering",
        "",
        "## Research Briefings",
    ]
    for c in all_content:
        if c.content_type in ("research",) and not is_future_post(c):
            date_str = c.created_at.strftime("%Y-%m-%d") if c.created_at else "unknown"
            sqi = c.signals.get("avg_sqi", 0) if c.signals else 0
            llms_full_lines.append(f"- [{date_str}] {c.title} (SQI: {sqi:.1f}) - {SITE_URL}/{c.slug}/")
    llms_full_lines.append("")
    llms_full_lines.append("## Learn Lessons")
    for c in all_content:
        if c.content_type == "learn" and not is_future_post(c):
            diff = getattr(c, "difficulty", "intermediate")
            llms_full_lines.append(f"- [{diff}] {c.title} - {SITE_URL}/{c.slug}/")
    llms_full_lines.append("")
    llms_full_lines.append("## Tags")
    for tag_slug in sorted(tag_items.keys()):
        count = len(tag_items[tag_slug])
        llms_full_lines.append(f"- {tag_slug} ({count} articles)")
    llms_full_lines.append("")
    llms_full_lines.append("---")
    llms_full_lines.append(f"Generated: {now.isoformat()}")
    llms_full_lines.append(f"Source: {SITE_URL}")
    (OUTPUT_DIR / "llms-full.txt").write_text("\n".join(llms_full_lines), encoding="utf-8")

    # --- HEADERS ---
    (OUTPUT_DIR / "_headers").write_text("""/*
  X-Content-Type-Options: nosniff
  X-Frame-Options: DENY
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: camera=(), microphone=(), geolocation=()
  Link: </.well-known/api-catalog>; rel="api-catalog"
  Link: </.well-known/mcp/server-card.json>; rel="mcp-server-card"
  Link: </.well-known/agent-skills/index.json>; rel="agent-skills"
  Link: </llms.txt>; rel="service-doc"; title="LLM Overview"
  Link: </llms-full.txt>; rel="service-desc"; title="Full LLM Content"
  Link: </auth.md>; rel="auth-md"

/static/*
  Cache-Control: public, max-age=31536000, immutable

/*.html
  Cache-Control: public, max-age=3600

/feed.xml
  Cache-Control: public, max-age=3600
  Content-Type: application/atom+xml; charset=utf-8

/sitemap.xml
  Content-Type: application/xml; charset=utf-8

/llms-full.txt
  Cache-Control: public, max-age=3600
  Content-Type: text/plain; charset=utf-8

/static/llms.txt
  Cache-Control: public, max-age=3600
  Content-Type: text/plain; charset=utf-8

/.well-known/api-catalog
  Content-Type: application/linkset+json
  Cache-Control: public, max-age=3600

/.well-known/oauth-protected-resource
  Content-Type: application/json
  Cache-Control: public, max-age=3600

/.well-known/oauth-authorization-server
  Content-Type: application/json
  Cache-Control: public, max-age=3600

/.well-known/mcp/server-card.json
  Content-Type: application/json
  Cache-Control: public, max-age=3600

/.well-known/agent-skills/index.json
  Content-Type: application/json
  Cache-Control: public, max-age=3600

/auth.md
  Content-Type: text/markdown; charset=utf-8
  Cache-Control: public, max-age=3600
""", encoding="utf-8")

    total = len(list(OUTPUT_DIR.rglob("*.html")))
    duration = time.time() - start_time
    duration_ms = int(duration * 1000)
    print(f"Generation complete. Total pages: {total} ({duration:.2f}s)")

    # ── Mem0: Log deployment ──
    if MEM0_AVAILABLE:
        try:
            import subprocess
            commit_hash = subprocess.check_output(
                ["git", "rev-parse", "HEAD"],
                cwd=str(PROJECT_ROOT),
                text=True
            ).strip()[:8]
            log_deployment(
                commit_hash=commit_hash,
                status="success",
                pages_generated=total,
                build_duration_ms=duration_ms,
            )
            print(f"  mem0: logged deployment {commit_hash}")
        except Exception as e:
            print(f"  mem0: logging failed ({e})")

    # ── Build metrics (build-meta.json) ──
    sqi_values = [
        c.signals.get("avg_sqi", 0.0)
        for c in all_content
        if c.signals and isinstance(c.signals, dict) and "avg_sqi" in c.signals
    ]
    sqi_sorted = sorted(sqi_values) if sqi_values else [0.0]
    n_sqi = len(sqi_sorted)
    sqi_min = sqi_sorted[0] if n_sqi > 0 else 0.0
    sqi_max = sqi_sorted[-1] if n_sqi > 0 else 0.0
    sqi_avg = round(sum(sqi_sorted) / n_sqi, 3) if n_sqi > 0 else 0.0
    sqi_median = sqi_sorted[n_sqi // 2] if n_sqi > 0 else 0.0
    sqi_q1 = sqi_sorted[n_sqi // 4] if n_sqi > 3 else sqi_min
    sqi_q3 = sqi_sorted[3 * n_sqi // 4] if n_sqi > 3 else sqi_max

    # Source-type aggregation across all content
    source_counts: dict[str, int] = defaultdict(int)
    for c in all_content:
        if c.source_breakdown:
            for src, cnt in c.source_breakdown.items():
                source_counts[src] += cnt

    # Soft quality gate: flag low-SQI items without excluding them
    low_sqi_items = [
        {"slug": c.slug, "title": c.title[:80], "sqi": c.signals.get("avg_sqi", 0.0)}
        for c in all_content
        if c.signals and isinstance(c.signals, dict)
        and c.signals.get("avg_sqi", SQI_DEFAULT) < SQI_THRESHOLD_MIN
    ]
    low_sqi_items.sort(key=lambda x: x["sqi"])

    # Content type counts
    content_type_counts: dict[str, int] = defaultdict(int)
    for c in all_content:
        ct = c.content_type or "unknown"
        content_type_counts[ct] += 1

    build_meta = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "duration_seconds": round(duration_ms / 1000, 2),
        "page_count": total,
        "registry_hash": build_hash,
        "sqi": {
            "min": round(sqi_min, 3),
            "max": round(sqi_max, 3),
            "avg": sqi_avg,
            "median": round(sqi_median, 3),
            "q1": round(sqi_q1, 3),
            "q3": round(sqi_q3, 3),
            "sample_count": n_sqi,
        },
        "sources": {
            "last_build": datetime.now(timezone.utc).isoformat(),
            "source_type_counts": dict(source_counts),
        },
        "content_counts": dict(content_type_counts),
        "quality": {
            "gate_min_sqi": SQI_THRESHOLD_MIN,
            "gate_passed": len(low_sqi_items) == 0,
            "low_sqi_count": len(low_sqi_items),
            "low_sqi_items": low_sqi_items,
        },
    }

    build_meta_path = OUTPUT_DIR / "build-meta.json"
    build_meta_path.write_text(
        json.dumps(build_meta, indent=2, default=str), encoding="utf-8"
    )
    print(f"  build-meta: build-meta.json ({build_meta_path.stat().st_size} bytes)")

    if low_sqi_items:
        log_text = "; ".join(f"{i['slug']} (SQI={i['sqi']})" for i in low_sqi_items)
        print(f"  quality gate: {len(low_sqi_items)} items below SQI {SQI_THRESHOLD_MIN}")
        print(f"    -> {log_text}")

    return 0


def _dummy(title="", category="post", body_html="", description=""):
    return type("obj", (object,), {
        "title": title, "language": "en", "category": category, "slug": "",
        "body_html": body_html, "description": description, "created_at": None,
        "updated_at": None, "tags": [], "pillar": "", "difficulty": "",
        "date_str": "", "thumbnail_svg": "", "og_svg": "", "signals": {},
        "source_breakdown": {}, "quality_metrics": {}, "bloom_questions": [],
        "flashcards": [], "trending_html": "", "analysis_html": "",
        "cross_pillar_html": "", "quality_flags": [], "knowledge_category": "",
    })


if __name__ == "__main__":
    exit(main())
