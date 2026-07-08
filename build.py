#!/usr/bin/env python3
"""
Build script for AcaciaFund: converts registry.json to static HTML using Jinja2 templates.
3-category taxonomy: research | learn | knowledge
"""

import hashlib
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import time
import tomllib
import unicodedata
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote as urlquote

import pandas as pd
from jinja2 import Environment, FileSystemLoader, FileSystemBytecodeCache, select_autoescape
from PIL import Image

from config import (
    INTEREST_RECENCY_DAYS,
    INTEREST_RECENCY_WEIGHT,
    INTEREST_SQI_WEIGHT,
    OUTPUT_DIR,
    PIPELINE_STATIC_DIR,
    PLAUSIBLE_DOMAIN,
    PROJECT_ROOT,
    REGISTRY_PATH,
    SITE_DESCRIPTION,
    SITE_NAME,
    SITE_URL,
    SQI_BADGE_HIGH,
    SQI_BADGE_MED,
    SQI_DEFAULT,
    SQI_THRESHOLD_MIN,
    STATIC_DST_DIR,
    TEMPLATE_DIR,
)

# ── Asset pipeline ──
from core.assets import create_asset_manager
from core.brand import (
    BRAND,
    section_type_color,
)
from core.content import Content

# ── Page generation helpers (new modular structure) ──
from core.images.templates import generate_fallback_svg


# --- Knowledge Graph Generation ---
def generate_knowledge_graph():
    script_path = PROJECT_ROOT / "scripts" / "build_knowledge_graph.py"
    if script_path.exists():
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(f"Warning: Knowledge graph generation failed: {result.stderr}")
        else:
            print("Knowledge graph updated.")
    else:
        print("Warning: Knowledge graph script not found.")


# ── Content validation ──
from core.validator import validate_content  # noqa: E402
from core.visuals import (  # noqa: E402
    PILLAR_COLORS,
    SUBTOPIC_CATEGORIES,
    TOPIC_ICONS,
    _pick_subtopic,
    generate_og_image,
    generate_thumbnail_svg,
    render_topic_icon,
    resolve_topic_icon,
)
from schemas import RegistryData  # noqa: E402
from seed_learn import CURATED_RELATIONS  # noqa: E402
from seed_learn import PREREQUISITES as LEARN_PREREQUISITES  # noqa: E402

# ── Mem0 integration for session context and deployment logging ──
try:
    from services.mem0 import log_deployment

    MEM0_AVAILABLE = True
except ImportError:
    MEM0_AVAILABLE = False

# ── Build cache for incremental builds ──
from core.build_cache import (  # noqa: E402
    BuildCache,
    get_cache,
    get_worker_pool,
    parallel_map,
)

# ── Taxonomy generation (separate from core content) ──
from core.build_taxonomies import (  # noqa: E402
    generate_admin_pages,
    generate_feed,
    generate_pillar_pages,
    generate_search_pages,
    generate_tag_pages,
)


# ── Admin credentials from .env ──
def load_admin_credentials():
    """Load admin credentials from .env file. Exits if not set."""
    env_path = PROJECT_ROOT / ".env"
    username = os.environ.get("ADMIN_USERNAME")
    password = os.environ.get("ADMIN_PASSWORD")

    if not username or not password:
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

    if not username or not password:
        print("ERROR: ADMIN_USERNAME and ADMIN_PASSWORD must be set in .env or environment.")
        sys.exit(1)

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
        "label": "AML",
        "emoji": "🛡️",
        "color": "slate",
        "bg": "from-slate-900 to-slate-800",
        "accent": "amber",
        "text_color": "text-slate-900",
        "badge_color": "bg-amber-100 text-amber-800",
        "heading": "Anti-Money Laundering",
        "description": "Financial crime, compliance, regulation, and risk management.",
    },
    "stock": {
        "label": "Markets",
        "emoji": "📈",
        "color": "green",
        "bg": "from-green-900 to-green-800",
        "accent": "green",
        "text_color": "text-green-900",
        "badge_color": "bg-green-100 text-green-800",
        "heading": "Markets & Industry",
        "description": "Semiconductors, supply chains, AI industry, manufacturing.",
    },
    "data-engineering": {
        "label": "Data Engineering",
        "emoji": "⚙️",
        "color": "indigo",
        "bg": "from-indigo-900 to-indigo-800",
        "accent": "indigo",
        "text_color": "text-indigo-900",
        "badge_color": "bg-indigo-100 text-indigo-800",
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
        "label": "Platform",
        "icon": "⚙️",
        "color": "#6366f1",
        "bg_color": "#6366f1",
        "description": "About AcaciaFund — mission, team, contact, and site operations.",
    },
    "guide": {
        "label": "Guides",
        "icon": "🧭",
        "color": "#22c55e",
        "bg_color": "#22c55e",
        "description": "Methodology, taxonomy, and how-to guides for using the platform.",
    },
    "reference": {
        "label": "Reference",
        "icon": "📖",
        "color": "#d97706",
        "bg_color": "#d97706",
        "description": "Glossaries, tool landscapes, and technical terminology across all pillars.",
    },
    "architecture": {
        "label": "Architecture",
        "icon": "🔗",
        "color": "#a855f7",
        "bg_color": "#a855f7",
        "description": "System design, pipeline architecture, and DataOps implementation details.",
    },
}


def add_lazy_loading(html: str) -> str:
    return re.sub(r"<img(?![^>]*loading=)", '<img loading="lazy" decoding="async"', html)


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


HEADING_RE = re.compile(r"<h([23])([^>]*)>(.*?)</h\1>", re.IGNORECASE | re.DOTALL)


def extract_headings(html: str) -> tuple[str, list[dict]]:
    toc = []
    id_counts: dict[str, int] = {}

    def _repl(m):
        tag = m.group(1)
        inner = m.group(3)
        text = re.sub(r"<[^>]+>", "", inner).strip()
        base_id = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "section"
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


def find_related(posts: list, current: Content, max_items: int = 3) -> list:
    """Score relatedness by pillar match (40%), tag overlap (40%), curated relations (20%).

    Curated relations (from current.curated_relations) always appear first
    when they match a post slug in the candidate pool.
    """
    current_tags = set(t.lower() for t in current.tags)
    current_pillar = current.pillar or ""
    {r.get("slug", "") for r in (current.curated_relations or [])}

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
        "ai",
        "artificial intelligence",
        "machine learning",
        "deep learning",
        "neural",
        "llm",
        "large language model",
        "generative ai",
        "openai",
        "anthropic",
        "google gemini",
        "claude",
        "gpt",
        "transformer",
        "bert",
        "gpt-4",
        "gpt-5",
        "claude 3",
    ],
    "realtime": [
        "real-time",
        "realtime",
        "streaming",
        "stream",
        "event-driven",
        "event streaming",
        "kafka",
        "kafka streams",
        "flink",
        "spark streaming",
        "kinesis",
        "pulsar",
        "cdc",
        "change data capture",
        "debezium",
        "websockets",
        "sse",
        "server-sent events",
    ],
    "platform": [
        "platform",
        "data platform",
        "data stack",
        "data architecture",
        "cloud infrastructure",
        "kubernetes",
        "k8s",
        "docker",
        "container",
        "orchestration",
        "terraform",
        "aws",
        "azure",
        "gcp",
        "serverless",
        "infrastructure as code",
        "iac",
    ],
    # Content types (cross-pillar) - priority 2
    "tutorial": [
        "tutorial",
        "how-to",
        "guide",
        "step-by-step",
        "walkthrough",
        "beginner",
        "introductory",
        "introduction",
        "getting started",
        "learn",
        "teach",
        "educational",
        "instructional",
    ],
    "comparison": [
        "comparison",
        "compare",
        "vs",
        "versus",
        "showdown",
        "benchmark",
        "evaluation",
        "review",
        "analysis",
        "trade-off",
        "pros and cons",
        "alternatives",
    ],
    "case-study": [
        "case study",
        "real-world",
        "production",
        "implementation",
        "deployment",
        "migration",
        "migration story",
        "customer",
        "client",
        "enterprise",
        "success story",
    ],
    # AML-specific - priority 3
    "aml": [
        "aml",
        "anti-money laundering",
        "compliance",
        "regulatory",
        "regulation",
        "enforcement",
        "sanctions",
        "fatf",
        "fincen",
        "kyc",
        "know your customer",
        "kyb",
        "know your business",
        "sar",
        "suspicious activity report",
        "transaction monitoring",
        "financial crime",
        "risk assessment",
    ],
    "fraud": [
        "fraud",
        "fraud detection",
        "fraud prevention",
        "scam",
        "scam detection",
        "payment fraud",
        "chargeback",
        "chargeback fraud",
        "synthetic identity",
        "money laundering",
        "suspicious activity",
    ],
    # Security - priority 4
    "security": [
        "security",
        "cybersecurity",
        "threat detection",
        "penetration",
        "vulnerability",
        "exploit",
        "attack",
        "breach",
        "intrusion",
        "malware",
        "ransomware",
        "phishing",
        "social engineering",
        "zero trust",
        "iam",
        "identity access management",
        "firewall",
        "waf",
        "web application firewall",
        "siem",
        "security information",
        "soc",
        "security operations",
    ],
    # DevOps - priority 5
    "devops": [
        "devops",
        "ci/cd",
        "continuous integration",
        "continuous delivery",
        "continuous deployment",
        "deployment",
        "build",
        "release",
        "pipeline",
        "workflow",
        "automation",
        "infrastructure as code",
        "terraform",
        "ansible",
        "puppet",
        "chef",
        "gitops",
        "argocd",
        "tekton",
        "jenkins",
    ],
    # Analytics - priority 6
    "analytics": [
        "analytics",
        "business intelligence",
        "bi",
        "reporting",
        "dashboard",
        "visualization",
        "data visualization",
        "chart",
        "kpi",
        "metric",
        "dashboard",
        "kpi tracking",
        "power bi",
        "tableau",
        "looker",
        "metabase",
    ],
    # Monitoring - priority 7
    "monitoring": [
        "monitoring",
        "observability",
        "logging",
        "tracing",
        "metrics",
        "alerting",
        "alert",
        "incident",
        "sre",
        "site reliability engineering",
        "slo",
        "sla",
        "prometheus",
        "grafana",
        "datadog",
        "new relic",
        "opentelemetry",
        "jaeger",
        "zipkin",
        "loki",
    ],
    # Cloud - priority 8
    "cloud": [
        "cloud",
        "aws",
        "azure",
        "gcp",
        "google cloud",
        "serverless",
        "lambda",
        "cloud function",
        "cloud run",
        "ec2",
        "s3",
        "rds",
        "dynamodb",
        "firestore",
        "cloudformation",
        "cloudformation",
        "terraform",
        "multi-cloud",
        "hybrid cloud",
        "cloud native",
    ],
    # Markets-specific - priority 9
    "finance": [
        "finance",
        "trading",
        "investment",
        "portfolio",
        "stock market",
        "equities",
        "bonds",
        "derivatives",
        "valuation",
        "financial modeling",
        "quantitative",
        "algorithmic trading",
        "algo trading",
        "high frequency",
        "market making",
        "market data",
        "financial technology",
    ],
    "market": [
        "market",
        "trading",
        "market data",
        "market analysis",
        "stock",
        "equity",
        "securities",
        "exchange",
        "nasdaq",
        "nyse",
        "s&p 500",
        "dow jones",
        "market maker",
        "market structure",
        "market microstructure",
    ],
    # Data Engineering-specific - priority 10
    "pipeline": [
        "pipeline",
        "etl",
        "elt",
        "orchestration",
        "workflow",
        "dag",
        "directed acyclic graph",
        "airflow",
        "dagster",
        "prefect",
        "kubeflow",
        "temporal",
        "kedro",
        "dbt",
        "sqlmesh",
        "data pipeline",
        "pipeline orchestration",
        "workflow orchestration",
    ],
    "infrastructure": [
        "infrastructure",
        "kubernetes",
        "k8s",
        "docker",
        "container",
        "infrastructure as code",
        "iac",
        "cloud",
        "aws",
        "azure",
        "gcp",
        "serverless",
        "deployment",
        "ci/cd",
        "continuous integration",
        "continuous delivery",
    ],
    # Technical (cross-pillar) - priority 11
    "database": [
        "database",
        "db",
        "sql",
        "nosql",
        "postgresql",
        "mysql",
        "mongodb",
        "cassandra",
        "redis",
        "memcached",
        "storage",
        "data warehouse",
        "data lake",
        "lakehouse",
        "iceberg",
        "delta lake",
        "hudi",
        "parquet",
        "avro",
    ],
    "api": [
        "api",
        "api design",
        "rest",
        "graphql",
        "grpc",
        "microservice",
        "service mesh",
        "istio",
        "linkerd",
        "gateway",
        "gateway api",
        "openapi",
        "swagger",
        "integration",
        "integration pattern",
        "event-driven",
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
    text = " ".join(
        [
            *(t.lower().replace("-", " ") for t in (content.tags or [])),
            (content.title or "").lower(),
        ]
    )
    pillar = (content.pillar or "").lower()
    content_type = (content.content_type or "").lower()

    # Priority levels for scoring
    priority_map = {
        "ai": 1,
        "realtime": 1,
        "platform": 1,
        "tutorial": 2,
        "comparison": 2,
        "case-study": 2,
        "aml": 3,
        "fraud": 3,
        "security": 4,
        "devops": 5,
        "analytics": 6,
        "monitoring": 7,
        "cloud": 8,
        "finance": 9,
        "market": 9,
        "pipeline": 10,
        "infrastructure": 10,
        "database": 11,
        "api": 11,
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
        score *= 1 + priority_mult

        # Pillar-specific weighting
        if pillar == "aml" and img_name in ["aml", "fraud", "security"]:
            score *= 1.5
        elif pillar == "stock" and img_name in ["finance", "market"]:
            score *= 1.5
        elif pillar == "data-engineering" and img_name in [
            "pipeline",
            "infrastructure",
            "database",
            "api",
            "monitoring",
            "devops",
        ]:
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
    text = re.sub(r"<[^>]+>", "", html_or_text)
    words = len(text.strip().split())
    code_blocks = len(re.findall(r"<pre><code>.*?</code></pre>", html_or_text, re.DOTALL))
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
        f"</svg>"
    )


def thumbnail_key(title: str) -> str:
    return hashlib.md5(title.encode()).hexdigest()[:12]


CJK_RE = re.compile(r"[\u4e00-\u9fff\u3400-\u4dbf\uff00-\uffef]")
EMOJI_RE = re.compile(
    r"[\U0001F300-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF\u2600-\u27BF\u2B50\U0001F1E0-\U0001F1FF]"
)


MERMAID_PLACEHOLDER = "@@MERMAID_"
_mermaid_counter = 0


def sanitize_text(html: str, strip_emoji: bool = True) -> str:
    global _mermaid_counter
    html = unicodedata.normalize("NFKC", html)
    html = CJK_RE.sub("", html)
    if strip_emoji:
        html = EMOJI_RE.sub("", html)
    # Protect mermaid div content from space-collapsing (need indent for mindmap)
    global _mermaid_counter
    mermaid_map = {}

    def _save_mermaid(m):
        global _mermaid_counter
        key = f"{MERMAID_PLACEHOLDER}{_mermaid_counter}_"
        _mermaid_counter += 1
        mermaid_map[key] = m.group(0)
        return key

    html = re.sub(
        r'(<div class="mermaid"[^>]*>)(.*?)(</div>)', _save_mermaid, html, flags=re.DOTALL
    )
    html = re.sub(r"  +", " ", html)
    html = re.sub(r">\s+<", "><", html)
    for key, original in mermaid_map.items():
        html = html.replace(key, original)
    return html


DOMAIN_BREAKDOWN_RE = re.compile(
    r"<li>[^<]*?([A-Za-z]+)\s*:\s*(\d+)%\s*of sources\s*</li>",
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
        html = html.replace(m.group(0), f"<li>{domain}: {capped}% of sources</li>", 1)
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
    # Try with _s1 suffix (for blog section images)
    stem = p.stem
    ext = p.suffix if p.suffix else ".webp"
    s1_path = p.parent / f"{stem}_s1{ext}"
    if s1_path.exists():
        ref = _resolve_ref_file(s1_path)
        if ref:
            return ref
        return url.rsplit(".", 1)[0] + "_s1" + ext
    # Try alternate extensions with _s1 suffix
    for ext in (".webp", ".png", ".jpg", ".jpeg", ".svg"):
        s1_alt = p.parent / f"{stem}_s1{ext}"
        if s1_alt.exists():
            ref = _resolve_ref_file(s1_alt)
            if ref:
                return ref
            return url.rsplit(".", 1)[0] + "_s1" + ext
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


def inject_section_images(body_html: str, section_images: list[dict], article=None) -> str:
    """Insert section-level images and data visualizations into body_html.

    Wraps each section in a .section-harvester div with:
    - Colored left border for section identity
    - Context-relevant data visualization (source bar, bloom chart, radar, etc.)
    - Collapsible content via <details>/<summary>
    - Section images placed between harvesters as visual transitions

    Matches by section_index (positional: 0 = first <h2>, 1 = second, etc.)
    """
    h2_pattern = re.compile(r"(<h2[^>]*>.*?</h2>)", re.IGNORECASE | re.DOTALL)
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
            result.append("</details>")
            result.append("</div>")

            # Section image goes OUTSIDE the harvester (as transition)
            if entry:
                url = resolve_section_image(entry.get("image_url", ""))
                credit = entry.get("image_credit", "")
                alt_ = entry.get("image_alt", "") or f"Illustration for {strip_html_tag(h2_tag)}"
                w = entry.get("width", 1200)
                h = entry.get("height", 675)
                if url:
                    style_class = (
                        "section-image--full"
                        if section_idx % 2 == 0
                        else "section-image--contained"
                    )
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
                            f"{credit}</figcaption>"
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
                            f"{svg}</figure>"
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
                    style_class = (
                        "section-image--full"
                        if section_idx % 2 == 0
                        else "section-image--contained"
                    )
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
                            f"{credit}</figcaption>"
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
                            f"{svg}</figure>"
                        )
                    except Exception:
                        pass
            result.append(content)

    return "".join(result)


def strip_html_tag(tag: str) -> str:
    m = re.search(r">([^<]+)<", tag)
    return m.group(1).strip() if m else ""


def is_future_post(post) -> bool:
    """Check if a post is future-dated based on frontmatter date or created_at."""
    from datetime import date
    
    today = date.today().isoformat()
    
    # Check date_str from frontmatter (e.g., "2026-06-15")
    if getattr(post, "date_str", ""):
        if post.date_str > today:
            return True
    
    # Fallback to created_at
    if post.created_at and post.created_at > datetime.now(timezone.utc):
        return True
    
    return False


def _get_quality_metrics_with_fail_safes(metrics: dict) -> dict:
    """Apply fail-safes for quality metrics to avoid zeroed values."""
    # If Authority or Diversity equal 0.00, inject proxy base values
    if metrics.get("authority", 0) == 0.0:
        metrics["authority"] = 0.74
    if metrics.get("diversity", 0) == 0.0:
        metrics["diversity"] = 0.68
    
    # Ensure required fields exist
    if "authority" not in metrics:
        metrics["authority"] = 0.74
    if "diversity" not in metrics:
        metrics["diversity"] = 0.68
    
    return metrics


# ── Visual fingerprint: unique ident for every article ─────
PILLAR_FINGERPRINT_COLORS = {
    "aml": BRAND["aml"]["primary"],
    "stock": BRAND["markets"]["primary"],
    "data-engineering": BRAND["science"]["primary"],
    "": "#6b7280",
}

LAYER_SYMBOLS = {
    "research": (
        "path",
        '<path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" fill="none" stroke="currentColor" stroke-width="1.5"/>',
    ),
    "learn": (
        "path",
        '<path d="M4 19.5A2.5 2.5 0 016.5 17H20" fill="none" stroke="currentColor" stroke-width="1.5"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 014 19.5v-15A2.5 2.5 0 016.5 2z" fill="none" stroke="currentColor" stroke-width="1.5"/>',
    ),
    "knowledge": (
        "circle",
        '<circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" stroke-width="1.5"/><path d="M12 6v6l4 2" fill="none" stroke="currentColor" stroke-width="1.5"/>',
    ),
}

LAYER_LABELS = {"research": "Research", "learn": "Learn", "knowledge": "Knowledge"}
LAYER_ICONS = {"research": "\u25c7", "learn": "\u25c9", "knowledge": "\u25ce"}


def get_layer(url_path: str) -> str:
    if url_path.startswith("learn") or url_path.startswith("learn/"):
        return "learn"
    if url_path.startswith("knowledge") or url_path.startswith("knowledge/"):
        return "knowledge"
    return "research"


def generate_article_fingerprint(
    slug: str, title: str, pillar: str, content_type: str, tags: list
) -> str:
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
                    bars.append(
                        f'<circle cx="{cx}" cy="{ry + 6}" r="{bar_h // 4}" fill="{base_color}" opacity="{opacity}"/>'
                    )
                elif content_type == "knowledge":
                    bars.append(
                        f'<line x1="{cx - 3}" y1="{ry}" x2="{cx + 3}" y2="{ry + 12}" stroke="{base_color}" stroke-width="1.5" opacity="{opacity}"/>'
                    )
                else:
                    bars.append(
                        f'<rect x="{cx - 2}" y="{ry}" width="4" height="{bar_h}" rx="1" fill="{base_color}" opacity="{opacity}"/>'
                    )

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 32" width="120" height="32" aria-hidden="true">'
        f'<rect width="120" height="32" rx="2" fill="{base_color}" opacity="0.08"/>'
        f"{''.join(bars)}"
        f"</svg>"
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
        f"{label}"
        f"</span>"
    )


def interest_score(post, now: datetime) -> float:
    sqi = post.signals.get("avg_sqi", 0.0) if post.signals else 0.0
    age_days = (now - (post.created_at or now)).days if post.created_at else 365
    age_days = max(0, age_days)
    recency = max(0.1, 1.0 - age_days / INTEREST_RECENCY_DAYS)
    return sqi * INTEREST_SQI_WEIGHT + recency * INTEREST_RECENCY_WEIGHT


def _get_content_hash(content_item: Any) -> str:
    """Generate a hash fingerprint for a content item to detect source changes.

    Only hashes source-level fields from the registry, NOT injected/processed
    content (body_html, trending_html, etc.) which are computed during build.
    This ensures the cache skip works correctly on incremental builds.
    """
    import hashlib

    data = {
        "slug": getattr(content_item, "slug", ""),
        "title": getattr(content_item, "title", ""),
        "content_type": getattr(content_item, "content_type", ""),
        "pillar": getattr(content_item, "pillar", ""),
        "description": getattr(content_item, "description", ""),
        "tags": sorted(getattr(content_item, "tags", []) or []),
        "bloom_questions": getattr(content_item, "bloom_questions", []),
        "flashcards": getattr(content_item, "flashcards", []),
        "quality_flags": getattr(content_item, "quality_flags", []),
        "knowledge_category": getattr(content_item, "knowledge_category", ""),
        "difficulty": getattr(content_item, "difficulty", ""),
        "date_str": getattr(content_item, "date_str", ""),
    }

    json_str = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(json_str.encode()).hexdigest()[:16]


def _cleanup_partial_output(item):
    """Clean up partial output files for a failed item."""
    try:
        slug = item.slug
        if hasattr(item, "content_type") and item.content_type == "knowledge":
            clean_slug = slug[10:] if slug.startswith("knowledge/") else slug
            out_dir = OUTPUT_DIR / "knowledge" / clean_slug
            if out_dir.exists():
                shutil.rmtree(out_dir)
        elif "/" in slug:
            out_dir = OUTPUT_DIR / slug
            if out_dir.exists():
                shutil.rmtree(out_dir)
        else:
            out_file = OUTPUT_DIR / f"{slug}.html"
            if out_file.exists():
                out_file.unlink()
    except Exception:
        pass


def main():
    print("Starting AcaciaFund generator...")
    start_time = time.time()
    _timings: dict[str, float] = {}

    def _record_timing(label: str, t: float) -> None:
        _timings[label] = round(t, 3)

    # Initialize build cache and worker pool
    cache = get_cache()
    _pool = get_worker_pool()
    
    # Check for template changes — compute both content-only and full template hashes
    content_hash = cache.compute_templates_hash(TEMPLATE_DIR, content_only=True)
    full_hash = cache.compute_templates_hash(TEMPLATE_DIR, content_only=False)
    
    if cache.content_templates_hash and content_hash != cache.content_templates_hash:
        print("🔄 Content templates changed, content pages will rebuild")
    elif cache.templates_hash and full_hash != cache.templates_hash:
        print("🔄 Layout/taxonomy templates changed, taxonomies will regenerate")
    else:
        print("✅ Templates unchanged")

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

    _t0 = time.time()
    try:
        with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
            registry_data = json.load(f)
        registry = RegistryData(**registry_data)
    except Exception as e:
        print(f"Error loading registry: {e}")
        return 1
    _record_timing("registry_load", time.time() - _t0)

    # Preserve quality scores and source verification before deleting dist
    quality_scores_backup = None
    quality_scores_path = OUTPUT_DIR / "quality_scores.parquet"
    if quality_scores_path.exists():
        quality_scores_backup = quality_scores_path.read_bytes()
        quality_scores_path.unlink()

    source_verification_backup = None
    source_verification_path = OUTPUT_DIR / "source_verification.parquet"
    if source_verification_path.exists():
        source_verification_backup = source_verification_path.read_bytes()
        source_verification_path.unlink()

    trend_detection_backup = None
    trend_detection_path = OUTPUT_DIR / "trend_detection.parquet"
    if trend_detection_path.exists():
        trend_detection_backup = trend_detection_path.read_bytes()
        trend_detection_path.unlink()

    source_synthesis_backup = None
    source_synthesis_path = OUTPUT_DIR / "source_synthesis.parquet"
    if source_synthesis_path.exists():
        source_synthesis_backup = source_synthesis_path.read_bytes()
        source_synthesis_path.unlink()

    # For incremental builds, preserve existing output (don't delete).
    # Only clean on force-rebuild or when no cache exists.
    if OUTPUT_DIR.exists():
        if not cache.cache:
            shutil.rmtree(OUTPUT_DIR)
            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        # else: keep existing output, skipped items already have their files
    else:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    STATIC_DST_DIR.mkdir(parents=True, exist_ok=True)

    # Restore quality scores, source verification, trend detection, and source synthesis
    if quality_scores_backup:
        quality_scores_path.write_bytes(quality_scores_backup)
    if source_verification_backup:
        source_verification_path.write_bytes(source_verification_backup)
    if trend_detection_backup:
        trend_detection_path.write_bytes(trend_detection_backup)
    if source_synthesis_backup:
        source_synthesis_path.write_bytes(source_synthesis_backup)

    if PIPELINE_STATIC_DIR.exists():
        for item in PIPELINE_STATIC_DIR.rglob("*"):
            if item.is_file():
                rel = item.relative_to(PIPELINE_STATIC_DIR)
                dest = STATIC_DST_DIR / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, dest)

    bytecode_cache = FileSystemBytecodeCache(str(PROJECT_ROOT / ".cache" / "jinja2"))
    env = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=select_autoescape(["html", "xml"]),
        bytecode_cache=bytecode_cache,
    )
    env.filters["reading_time"] = reading_time_minutes
    env.filters["urlencode"] = lambda s: urlquote(s or "", safe="")
    env.filters["pictogram"] = pick_card_pictogram
    env.globals["resolve_topic_icon"] = resolve_topic_icon
    env.globals["render_topic_icon"] = render_topic_icon
    env.globals["_pick_subtopic"] = _pick_subtopic

    STOP_WORDS = {
        "the",
        "a",
        "an",
        "at",
        "by",
        "for",
        "in",
        "is",
        "it",
        "of",
        "on",
        "to",
        "and",
        "or",
        "with",
        "as",
        "be",
        "but",
        "not",
        "so",
        "than",
        "that",
        "this",
        "was",
        "are",
        "its",
        "from",
        "has",
        "had",
        "have",
        "been",
        "were",
        "can",
        "will",
        "would",
        "could",
        "should",
        "may",
        "might",
        "shall",
        "about",
        "into",
        "over",
        "such",
        "only",
        "also",
        "very",
        "just",
        "more",
        "some",
        "these",
        "those",
        "each",
        "both",
        "all",
        "any",
        "too",
        "much",
        "many",
        "great",
        "good",
        "new",
        "first",
        "last",
        "next",
        "other",
        "same",
        "own",
        "old",
        "high",
        "low",
        "long",
        "small",
        "large",
        "big",
        "top",
        "key",
        "main",
        "primary",
        "major",
        "brief",
        "short",
        "full",
        "clear",
        "best",
        "better",
        "most",
        "least",
    }

    def filter_entities(entities):
        result = []
        for e in entities or []:
            clean = e.strip().strip(",:;.!?()[]{}'\"-").lower()
            if len(clean) >= 3 and clean not in STOP_WORDS:
                result.append(e.strip().strip(",:;.!?()[]{}'\"-"))
        return result

    env.filters["filter_entities"] = filter_entities

    DIGEST_PATTERN = re.compile(r"--\s*[🛡️📈⚙️🧬🗓️]\s*\S+\s+\d{4}-\d{2}-\d{2}\s*$")

    def content_subtype_label(item):
        title = item.get("title", "") if isinstance(item, dict) else getattr(item, "title", "")
        if DIGEST_PATTERN.search(title):
            return ("Daily Digest", "digest")
        return ("Synthesis", "synthesis")

    env.filters["content_subtype"] = content_subtype_label

    # --- Trend Detection System ---
    trend_detection_path = PROJECT_ROOT / "dist" / "trend_detection.parquet"
    trend_detection = {}
    if trend_detection_path.exists():
        df = pd.read_parquet(trend_detection_path)
        trend_detection = {row["slug"]: row for _, row in df.iterrows()}
        print(f"  Loaded trend detection for {len(trend_detection)} articles")

    # --- Source Verification Framework ---
    source_verification_path = PROJECT_ROOT / "dist" / "source_verification.parquet"
    source_verification = {}
    if source_verification_path.exists():
        df = pd.read_parquet(source_verification_path)
        source_verification = {}
        for _, row in df.iterrows():
            evidence = row.get("evidence", [])
            if isinstance(evidence, str):
                try:
                    evidence = json.loads(evidence)
                except Exception:
                    evidence = []
            source_verification[row["slug"]] = {
                "source_score": row["source_score"],
                "source_type": row["source_type"],
                "verified": row["verified"],
                "evidence_level": row["evidence_level"],
                "evidence": evidence,
            }
        print(f"  Loaded source verification for {len(source_verification)} articles")

    # --- Source Synthesis Framework ---
    synthesis_path = PROJECT_ROOT / "dist" / "source_synthesis.parquet"
    source_synthesis = {}
    if synthesis_path.exists():
        df = pd.read_parquet(synthesis_path)
        source_synthesis = {}
        for slug, group in df.groupby("article_slug"):
            records = group.to_dict("records")
            # Convert numpy arrays back to Python lists
            for rec in records:
                if (
                    "key_insights" in rec
                    and hasattr(rec["key_insights"], "__iter__")
                    and not isinstance(rec["key_insights"], str)
                ):
                    rec["key_insights"] = list(rec["key_insights"])
            source_synthesis[slug] = records
        print(f"  Loaded source synthesis for {len(source_synthesis)} articles")

    # --- Quality Engine ---
    quality_scores_path = PROJECT_ROOT / "dist" / "quality_scores.parquet"
    quality_scores = {}
    if quality_scores_path.exists():
        df = pd.read_parquet(quality_scores_path)
        # Support both 'slug' and 'article_slug' column names
        slug_col = "article_slug" if "article_slug" in df.columns else "slug"
        quality_scores = {row[slug_col]: row for _, row in df.iterrows()}
        print(f"  Loaded quality scores for {len(quality_scores)} articles")
    else:
        # Try alternative location (if dist was just recreated)
        alt_path = PROJECT_ROOT / "dist" / "quality_scores.parquet"
        if alt_path.exists():
            df = pd.read_parquet(alt_path)
            quality_scores = {row["slug"]: row for _, row in df.iterrows()}
            print(f"  Loaded quality scores (alt path) for {len(quality_scores)} articles")

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
    # Convert dict content to Content objects
    all_content = [Content.from_dict(c) if isinstance(c, dict) else c for c in registry.content]

    # Initialize logging first (needed for validation logging)
    log_path = OUTPUT_DIR / "build_errors.log"
    logging.basicConfig(
        filename=log_path,
        level=logging.ERROR,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        filemode="w",
    )
    logger = logging.getLogger(__name__)

    # Temporal filter: drop future-dated content
    all_content = [c for c in all_content if not is_future_post(c)]
    
    # Validate content before processing (skip-and-continue mode)
    _, validation_errors, skipped_slugs = validate_content(all_content, strict=False)
    if validation_errors:
        for error in validation_errors:
            logger.warning(error)
            print(f"  [WARN] {error}")
    if skipped_slugs:
        print(f"  Skipping {len(skipped_slugs)} invalid item(s): {', '.join(skipped_slugs)}")
        all_content = [c for c in all_content if c.slug not in set(skipped_slugs)]
    if not all_content:
        print("ERROR: No valid content items remaining after validation.")
        sys.exit(1)

    _t0 = time.time()
    # Generate knowledge graph for semantic cross-linking
    generate_knowledge_graph()

    # Export cytoscape graph data for /graph/ visualization
    def export_cytograph():
        import subprocess as _sp
        script_path = PROJECT_ROOT / "scripts" / "export_graph.py"
        if script_path.exists():
            result = _sp.run(
                [sys.executable, str(script_path)],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                print(f"Warning: CytoGraph export failed: {result.stderr}")
            else:
                for line in result.stdout.strip().split("\n"):
                    print(f"  {line}")
        else:
            print("Warning: CytoGraph script not found.")

    export_cytograph()

    # Load knowledge graph for semantic cross-linking
    knowledge_graph_path = PROJECT_ROOT / "data" / "knowledge_graph.json"
    if knowledge_graph_path.exists():
        try:
            with open(knowledge_graph_path, "r") as f:
                knowledge_graph = json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load knowledge graph: {e}")
            knowledge_graph = {}
    else:
        knowledge_graph = {}
    _record_timing("graph_build", time.time() - _t0)
    # Map slug to content object for potential lookup
    __slug_to_content = {item.slug: item for item in all_content}

    failed_count = 0

    # --- Asset Pipeline (fingerprinting and minification) ---
    # Must be after build_hash is computed but before template rendering
    _t0 = time.time()
    asset_manager = create_asset_manager(STATIC_DST_DIR, build_hash)
    asset_map = asset_manager.process_directory(PIPELINE_STATIC_DIR)
    print(f"  Asset pipeline: {len(asset_map)} assets processed")
    # Add asset resolver filter to env
    env.filters["asset"] = asset_manager.resolve_path
    _record_timing("asset_pipeline", time.time() - _t0)

    # --- Incremental Build System ---
    # Load previous manifest to enable incremental builds
    # Manifest is stored in PROJECT_ROOT to persist across builds
    manifest_path = PROJECT_ROOT / ".build_manifest.json"
    previous_manifest = {}
    if manifest_path.exists():
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                previous_manifest = json.load(f)
        except Exception:
            previous_manifest = {}

    # Track which items to skip and which to process
    items_to_skip: set[str] = set()
    items_to_process: list[Any] = []

    # Precompute content hashes from SOURCE data (before any mutations)
    # This dict is reused at save time to compute the same hash for both
    # the skip check and the cache update — preventing drift from mutations.
    content_hashes: dict[str, str] = {}

    # Compute hashes in parallel, then check cache sequentially
    current_manifest: dict[str, dict] = {}
    _computed_hashes: list[str] = parallel_map(_get_content_hash, all_content, pool=_pool)
    for item, current_hash in zip(all_content, _computed_hashes):
        slug = getattr(item, "slug", "")
        if not slug:
            items_to_process.append(item)
            continue

        content_hashes[slug] = current_hash
        current_manifest[slug] = {"hash": current_hash, "processed": False}

        # Check if item can be skipped using build cache
        # First check template changes, then content hash
        if "/" in slug:
            output_path = OUTPUT_DIR / slug / "index.html"
        else:
            output_path = OUTPUT_DIR / f"{slug}.html"
            
        if slug in items_to_skip:
            continue
            
        # Use build cache for faster change detection
        # Pass the content hash (not the full JSON) for consistent comparison
        if not cache.needs_rebuild(output_path, current_hash, is_content=True):
            items_to_skip.add(slug)
            cache.update_entry(output_path, current_hash,
                             {"slug": slug, "content_type": getattr(item, "content_type", "")},
                             is_content=True)
            continue

        items_to_process.append(item)

    skipped_count = len(items_to_skip)
    print(f"  Incremental build: {skipped_count} items skipped, {len(items_to_process)} to process")

    research_items = [c for c in all_content if c.content_type == "research"]
    learn_items = [c for c in all_content if c.content_type == "learn"]
    knowledge_items = [c for c in all_content if c.content_type == "knowledge"]

    # Research articles with bloom questions, mapped to learn-like items for cross-referencing
    research_learn_items = []
    for r in research_items:
        if r.bloom_questions and r.highest_bloom > 0:
            r_diff = (
                "beginner"
                if r.highest_bloom <= 2
                else "intermediate"
                if r.highest_bloom <= 4
                else "advanced"
            )
            research_learn_items.append(
                {
                    "slug": r.slug,
                    "title": r.title,
                    "pillar": r.pillar or "",
                    "difficulty": r.difficulty or r_diff,
                    "highest_bloom": r.highest_bloom or 0,
                    "description": r.description[:200] if r.description else "",
                    "date_str": r.date_str or "",
                    "tags": r.tags,
                    "prerequisites": [],
                }
            )

    pillar_groups = group_by_pillar(research_items)

    BLOOM_NAMES = {
        1: "Remember",
        2: "Understand",
        3: "Apply",
        4: "Analyse",
        5: "Evaluate",
        6: "Create",
    }

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
    
    def write_cached_html(filepath, html_content, slug="", metadata=None):
        """Write HTML file and update build cache."""
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text(html_content, encoding="utf-8")
        if slug:
            cache.update_entry(filepath, html_content, metadata or {"slug": slug}, is_content=True)

    _t_render = time.time()
    # --- KNOWLEDGE PAGES ---
    for item in knowledge_items:
        try:
            slug = item.slug
            # Skip if already processed (incremental build)
            if slug in items_to_skip:
                print(f"  knowledge: {slug} (skipped - unchanged)")
                continue
            slug = item.slug
            clean_slug = slug[10:] if slug.startswith("knowledge/") else slug
            page_path = canonical_path(slug_to_path(clean_slug))
            out_dir = OUTPUT_DIR / "knowledge" / clean_slug
            out_dir.mkdir(parents=True, exist_ok=True)
            out_file = out_dir / "index.html"

            body = add_lazy_loading(item.body_html)
            body, toc_items = extract_headings(body)
            body = sanitize_domain_breakdown(body)
            body = inject_section_images(body, item.section_images, item)
            body = re.sub(
                r"<h2[^>]*>\s*" + re.escape(item.title.strip()) + r"\s*</h2>\s*", "", body, count=1
            )
            body = sanitize_text(body, strip_emoji=False)
            item.description = sanitize_text(item.description, strip_emoji=False)
            item.body_html = body

            kcat = KNOWLEDGE_CATEGORIES.get(item.knowledge_category, {})
            if kcat:
                kcat["slug"] = item.knowledge_category

            related_research = find_related(research_items, item, 3)
            related_learn = find_related(learn_items, item, 3)
            visual_fingerprint = generate_article_fingerprint(
                item.slug, item.title, item.pillar or "", "knowledge", item.tags
            )
            layer_badge = layer_indicator_html("knowledge", item.pillar or "")

            thumb_key = hashlib.md5(item.title.encode()).hexdigest()[:12]
            og_key = hashlib.md5(f"og_{item.title}".encode()).hexdigest()[:12]
            thumb_base = f"{SITE_URL}/static/images"
            feat_img_path = resolve_featured_image(item.featured_image or "")
            og_image_url = (
                feat_img_path if feat_img_path else f"{SITE_URL}/static/images/og_{og_key}.svg"
            )

            layer_sub = (
                item.knowledge_category.replace("_", " ").title()
                if item.knowledge_category
                else item.pillar or ""
            )
            # Quality metrics with fail-safes
            quality_metrics = _get_quality_metrics_with_fail_safes(quality_scores.get(item.slug, {}))
            quality_score = quality_metrics.get("quality_score", 0)
            quality_badge = ""
            if quality_score and quality_score >= 0.8:
                quality_badge = "★★★★★"
            elif quality_score and quality_score >= 0.7:
                quality_badge = "★★★★☆"
            elif quality_score and quality_score >= 0.6:
                quality_badge = "★★★☆☆"
            elif quality_score and quality_score >= 0.5:
                quality_badge = "★★☆☆☆"
            else:
                quality_badge = "★☆☆☆☆"

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
                            raw = (
                                opts.index(correct_val)
                                if isinstance(correct_val, str)
                                and correct_val
                                and correct_val in opts
                                else 0
                            )
                        entry = {"q": bq["question"], "options": opts, "a": raw, "type": qtype}
                        if qtype == "open-ended":
                            entry["answer_text"] = bq.get("correct", opts[raw] if opts else "")
                        k_quiz_data["questions"].append(entry)
                if k_quiz_data["questions"]:
                    k_quiz_json = json.dumps(k_quiz_data, ensure_ascii=False)

            # Trend detection
            trend_info = trend_detection.get(item.slug, {})
            trend_strength = trend_info.get("trend_strength", 0)
            adoption_level = trend_info.get("adoption_level", "mainstream")
            impact_level = trend_info.get("impact_level", "low")
            trend_categories = trend_info.get("trend_categories", "")

            # Source verification
            source_info = source_verification.get(item.slug, {})
            source_verified = source_info.get("verified", False)
            source_evidence = source_info.get("evidence", [])

            html = render_template(
                "knowledge.j2",
                content=item,
                page_path=page_path,
                jsonld=_build_jsonld(item, SITE_URL, page_path),
                toc_items=toc_items,
                kcat=kcat,
                related_research=related_research,
                related_learn=related_learn,
                visual_fingerprint=visual_fingerprint,
                layer_badge=layer_badge,
                thumbnail_base=thumb_base,
                thumbnail_key=thumbnail_key,
                og_image_url=og_image_url,
                quiz_json=k_quiz_json,
                quality_score=quality_score,
                quality_badge=quality_badge,
                source_verified=source_verified,
                source_evidence=source_evidence,
                quality_metrics=quality_metrics,
                trend_strength=trend_strength,
                adoption_level=adoption_level,
                impact_level=impact_level,
                trend_categories=trend_categories,
                source_synthesis=source_synthesis.get(item.slug, []),
                is_index=False,
                page_type="knowledge",
                layer="knowledge",
                layer_icon=LAYER_ICONS["knowledge"],
                layer_sub=layer_sub,
                **ctx_base,
            )
            out_file.write_text(html, encoding="utf-8")
            print(f"  knowledge: {out_file.relative_to(OUTPUT_DIR)}")

            # Write knowledge thumbnail SVGs + OG images (fractal engine)
            out_static = STATIC_DST_DIR / "images"
            out_static.mkdir(parents=True, exist_ok=True)
            pillar_k = item.pillar or "aml"
            scores_k = {}
            feat_k = resolve_featured_image(item.featured_image or "")
            icons_k = get_topic_icons(item.tags) if not feat_k else []
            svg_k = generate_thumbnail_svg(
                item.title,
                pillar_k,
                scores_k,
                width=600,
                height=340,
                featured_image_url=feat_k,
                layer="knowledge",
                fallback_icons=icons_k,
            )
            (out_static / f"thumb_{thumb_key}.svg").write_text(svg_k, encoding="utf-8")
            og_svg = generate_og_image(
                item.title,
                pillar_k,
                scores_k,
                featured_image_url=feat_k,
                layer="knowledge",
                fallback_icons=icons_k,
            )
            (out_static / f"og_{og_key}.svg").write_text(og_svg, encoding="utf-8")

        except Exception:
            failed_count += 1
            logger.error(f"Failed to process knowledge item {item.slug}", exc_info=True)
            _cleanup_partial_output(item)
            continue
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
    html = render_template(
        "knowledge_index.j2",
        content=_dummy(
            "Knowledge Base",
            "knowledge",
            description="AcaciaFund knowledge base: platform guides, methodology, reference glossaries, system architecture, and DataOps resources across all pillars.",
        ),
        items=knowledge_items,
        grouped=dict(grouped),
        categories=KNOWLEDGE_CATEGORIES,
        thumbnail_base=thumb_base,
        thumbnail_key=thumbnail_key,
        page_title="Knowledge Base",
        is_index=False,
        page_path="knowledge/",
        layer="knowledge",
        layer_icon=LAYER_ICONS["knowledge"],
        **ctx_base,
    )
    (knowledge_dir / "index.html").write_text(html, encoding="utf-8")
    print("  category: knowledge/index.html")

    # --- LEARN PAGES ---
    BLOOM_ORDER = {
        "remember": 1,
        "understand": 2,
        "apply": 3,
        "analyze": 4,
        "evaluate": 5,
        "create": 6,
    }
    # Apply curated relations and prerequisites from seed_learn.py
    for item in learn_items:
        slug = item.slug
        if slug in CURATED_RELATIONS:
            item.curated_relations = [{"slug": s} for s in CURATED_RELATIONS[slug]]
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
        key=lambda x: (
            DIFFICULTY_ORDER.get(x.difficulty or "beginner", 0),
            x.pillar or "",
            x.title or "",
        ),
    )
    for i, item in enumerate(learn_items):
        try:
            slug = item.slug
            # Skip if already processed (incremental build)
            if slug in items_to_skip:
                print(f"  learn: {slug} (skipped - unchanged)")
                continue
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
            # Trend detection
            trend_info = trend_detection.get(item.slug, {})
            trend_strength = trend_info.get("trend_strength", 0)
            adoption_level = trend_info.get("adoption_level", "mainstream")
            impact_level = trend_info.get("impact_level", "low")
            trend_categories = trend_info.get("trend_categories", "")

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
            body = re.sub(
                r"<h2[^>]*>\s*" + re.escape(item.title.strip()) + r"\s*</h2>\s*", "", body, count=1
            )
            body = sanitize_text(body, strip_emoji=False)
            item.description = sanitize_text(item.description, strip_emoji=False)
            item.body_html = body

            pillar = item.pillar or ""
            pconf = PILLAR_CONFIG.get(pillar) if pillar else None
            related_research = find_related(research_items, item, 3)
            related_knowledge = find_related(knowledge_items, item, 3)
            visual_fingerprint = generate_article_fingerprint(
                item.slug, item.title, pillar, "learn", item.tags
            )
            layer_badge = layer_indicator_html("learn", pillar)
            thumb_key = hashlib.md5(item.title.encode()).hexdigest()[:12]
            og_key = hashlib.md5(f"og_{item.title}".encode()).hexdigest()[:12]
            thumb_base = f"{SITE_URL}/static/images"
            feat_img_path = resolve_featured_image(item.featured_image or "")
            og_image_url = (
                feat_img_path if feat_img_path else f"{SITE_URL}/static/images/og_{og_key}.svg"
            )
            (out_static / f"og_{og_key}.svg").write_text(og_svg, encoding="utf-8")

            # Source verification
            source_info = source_verification.get(item.slug, {})
            source_verified = source_info.get("verified", False)
            source_evidence = source_info.get("evidence", [])

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

            # Quality metrics with fail-safes
            quality_metrics = _get_quality_metrics_with_fail_safes(quality_scores.get(item.slug, {}))
            quality_score = quality_metrics.get("quality_score", 0)
            quality_badge = ""
            if quality_score and quality_score >= 0.8:
                quality_badge = "★★★★★"
            elif quality_score and quality_score >= 0.7:
                quality_badge = "★★★★☆"
            elif quality_score and quality_score >= 0.6:
                quality_badge = "★★★☆☆"
            elif quality_score and quality_score >= 0.5:
                quality_badge = "★★☆☆☆"
            else:
                quality_badge = "★☆☆☆☆"

            bl_name = BLOOM_NAMES.get(item.highest_bloom or 0, "")
            layer_sub = f"Level {item.highest_bloom}: {bl_name}" if bl_name else ""
            html = render_template(
                "learn.j2",
                content=item,
                page_path=page_path,
                jsonld=_build_jsonld(item, SITE_URL, page_path),
                toc_items=toc_items,
                pconf=pconf,
                prev_lesson=prev_lesson,
                next_lesson=next_lesson,
                related_research=related_research,
                related_knowledge=related_knowledge,
                visual_fingerprint=visual_fingerprint,
                layer_badge=layer_badge,
                thumbnail_base=thumb_base,
                thumbnail_key=thumbnail_key,
                og_image_url=og_image_url,
                quiz_json=quiz_json,
                featured_image=resolve_section_image(item.featured_image),
                image_credit=item.image_credit,
                quality_score=quality_score,
                quality_badge=quality_badge,
                quality_metrics=quality_metrics,
                source_verified=source_verified,
                source_evidence=source_evidence,
                trend_strength=trend_strength,
                adoption_level=adoption_level,
                impact_level=impact_level,
                trend_categories=trend_categories,
                source_synthesis=source_synthesis.get(item.slug, []),
                is_index=False,
                layer="learn",
                layer_icon=LAYER_ICONS["learn"],
                layer_sub=layer_sub,
                **ctx_base,
            )
            out_file.write_text(html, encoding="utf-8")
            print(f"  learn: {out_file.relative_to(OUTPUT_DIR)}")

            # Write learn thumbnail SVGs + OG images (fractal engine)
            out_static = STATIC_DST_DIR / "images"
            out_static.mkdir(parents=True, exist_ok=True)
            pillar_l = item.pillar or "aml"
            scores_l = {}
            feat_l = resolve_featured_image(item.featured_image or "")
            icons_l = get_topic_icons(item.tags) if not feat_l else []
            svg_l = generate_thumbnail_svg(
                item.title,
                pillar_l,
                scores_l,
                width=600,
                height=340,
                featured_image_url=feat_l,
                layer="learn",
                fallback_icons=icons_l,
            )
            (out_static / f"thumb_{thumb_key}.svg").write_text(svg_l, encoding="utf-8")
            og_svg = generate_og_image(
                item.title,
                pillar_l,
                scores_l,
                featured_image_url=feat_l,
                layer="learn",
                fallback_icons=icons_l,
            )
            (out_static / f"og_{og_key}.svg").write_text(og_svg, encoding="utf-8")

        except Exception:
            failed_count += 1
            logger.error(f"Failed to process learn item {item.slug}", exc_info=True)
            _cleanup_partial_output(item)
            continue
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
                _bloom_num = {
                    "remember": 1,
                    "understand": 2,
                    "apply": 3,
                    "analyze": 4,
                    "evaluate": 5,
                    "create": 6,
                }.get(_bloom, 0)
                _matching = [
                    a
                    for a in learn_items
                    if a.pillar == _pkey and (a.highest_bloom or 0) == _bloom_num
                ]
                _articles = [
                    {"slug": a.slug, "title": a.title, "difficulty": a.difficulty or ""}
                    for a in sorted(_matching, key=lambda x: x.title or "")
                ]
                steps.append(
                    {
                        "bloom": _bloom,
                        "bloom_num": _bloom_num,
                        "label": _step.get("label", ""),
                        "articles": _articles,
                        "article_count": len(_articles),
                    }
                )
            learning_paths_data[_pkey] = {
                "label": _ppath.get("label", ""),
                "steps": steps,
            }

    html = render_template(
        "learn_index.j2",
        content=_dummy(
            "Learning Hub",
            "learn",
            description="Interactive lessons, tutorials, and quizzes on AML compliance, financial markets, data engineering, and DataOps — powered by Bloom taxonomy.",
        ),
        items=learn_items,
        grouped=dict(learn_grouped),
        thumbnail_base=thumb_base,
        thumbnail_key=thumbnail_key,
        page_title="Learning Hub",
        is_index=False,
        page_path="learn/",
        layer="learn",
        layer_icon=LAYER_ICONS["learn"],
        bloom_first_articles=bloom_first_articles,
        learning_paths_data=learning_paths_data,
        research_learn_items=research_learn_items,
        **ctx_base,
    )
    (learn_dir / "index.html").write_text(html, encoding="utf-8")
    print("  category: learn/index.html")

    # --- RESEARCH PAGES (blog posts) ---
    for i, item in enumerate(research_items):
        try:
            slug = item.slug
            # Skip if already processed (incremental build)
            if slug in items_to_skip:
                print(f"  research: {slug} (skipped - unchanged)")
                continue
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
            body = re.sub(
                r"<h2[^>]*>\s*" + re.escape(item.title.strip()) + r"\s*</h2>\s*", "", body, count=1
            )
            body = sanitize_text(body, strip_emoji=True)
            item.description = sanitize_text(item.description, strip_emoji=True)

            prev_post = research_items[i + 1] if i + 1 < len(research_items) else None
            next_post = research_items[i - 1] if i > 0 else None
            pillar = item.pillar or "aml"
            related = find_related(research_items, item, 3)
            related_learn = find_related(learn_items, item, 3)
            visual_fingerprint = generate_article_fingerprint(
                item.slug, item.title, pillar, "research", item.tags
            )
            layer_badge = layer_indicator_html("research", pillar)

            pconf = PILLAR_CONFIG.get(pillar, PILLAR_CONFIG["aml"])
            sqi_svg = (
                generate_sqi_badge(item.signals.get("avg_sqi", SQI_DEFAULT)) if item.signals else ""
            )
            og_key = hashlib.md5(f"og_{item.title}".encode()).hexdigest()[:12]
            feat_img_path = resolve_featured_image(item.featured_image or "")
            og_image_url = (
                feat_img_path if feat_img_path else f"{SITE_URL}/static/images/og_{og_key}.svg"
            )
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
                            raw = (
                                opts.index(correct_val)
                                if isinstance(correct_val, str)
                                and correct_val
                                and correct_val in opts
                                else 0
                            )
                        entry = {"q": bq["question"], "options": opts, "a": raw, "type": qtype}
                        if qtype == "open-ended":
                            entry["answer_text"] = bq.get("correct", opts[raw] if opts else "")
                        r_quiz_data["questions"].append(entry)
                if r_quiz_data["questions"]:
                    r_quiz_json = json.dumps(r_quiz_data, ensure_ascii=False)
            topic_sub = _pick_subtopic([item.title], pillar)
            topic_icon_html = render_topic_icon(
                topic_sub, PILLAR_COLORS.get(pillar, PILLAR_COLORS["aml"])["accent"]
            )
            html = render_template(
                "blog_post.j2",
                content=item,
                page_path=page_path,
                jsonld=_build_jsonld(item, SITE_URL, page_path),
                page_body=body,
                prev_post=prev_post,
                next_post=next_post,
                pconf=pconf,
                sqi_svg=sqi_svg,
                og_image_url=og_image_url,
                thumbnail_base=thumb_base,
                thumbnail_key=thumbnail_key,
                toc_items=toc_items,
                related_posts=related,
                related_learn=related_learn,
                related_kg=knowledge_graph.get(item.slug, []),
                visual_fingerprint=visual_fingerprint,
                layer_badge=layer_badge,
                featured_image=resolve_section_image(item.featured_image),
                image_credit=item.image_credit,
                quiz_json=r_quiz_json,
                topic_icon_html=topic_icon_html,
                layer_sub=pconf["label"],
                source_synthesis=source_synthesis.get(item.slug, []),
                **ctx_base,
            )
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
            svg_r = generate_thumbnail_svg(
                item.title,
                pillar,
                scores_r,
                width=600,
                height=340,
                featured_image_url=feat_r,
                layer="research",
                fallback_icons=icons_r,
            )
            (out_static / f"thumb_{key}.svg").write_text(svg_r, encoding="utf-8")
            og_svg = generate_og_image(
                item.title,
                pillar,
                scores_r,
                featured_image_url=feat_r,
                layer="research",
                fallback_icons=icons_r,
            )
            (out_static / f"og_{og_key}.svg").write_text(og_svg, encoding="utf-8")

        except Exception:
            failed_count += 1
            logger.error(f"Failed to process research item {item.slug}", exc_info=True)
            _cleanup_partial_output(item)
            continue
    # --- CARD THUMBNAILS — generate 200x150 thumbnails for all articles ---
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
    # Fall back to fractal thumbnail SVGs for articles without a featured image.
    # Generate on the fly if the detail-page thumbnail was skipped (incremental build).
    for article in all_content:
        if article.slug not in card_images and article.title:
            key = thumbnail_key(article.title)
            thumb_path = STATIC_DST_DIR / "images" / f"thumb_{key}.svg"
            if not thumb_path.exists():
                pillar = article.pillar or "aml"
                scores = getattr(article, "signals", None) or {"sqi": 0.5}
                if not isinstance(scores, dict):
                    scores = {"sqi": 0.5}
                fallback = get_topic_icons(getattr(article, "tags", []) or [])
                svg = generate_thumbnail_svg(
                    article.title,
                    pillar,
                    scores,
                    width=600,
                    height=340,
                    layer=getattr(article, "content_type", "research") or "research",
                    fallback_icons=fallback,
                )
                thumb_path.parent.mkdir(parents=True, exist_ok=True)
                thumb_path.write_text(svg, encoding="utf-8")
            if thumb_path.exists():
                card_images[article.slug] = f"/static/images/thumb_{key}.svg"

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
    html = render_template(
        "category_index.j2",
        content=_dummy(
            "Research",
            "research",
            description="Quality-scored research articles on AML, financial markets, and science. Automatically classified from HackerNews and arXiv using Bloom taxonomy.",
        ),
        category="research",
        items=sorted_research,
        grouped=pillar_groups,
        page_title="Research",
        is_index=False,
        page_path="research/",
        card_images=card_images,
        card_topic_icons=card_topic_icons,
        **ctx_base,
    )
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
                "slug": p.slug,
                "title": p.title or "",
                "description": p.description or "",
                "date_str": p.date_str or "",
                "content_type": p.content_type or "research",
                "pillar": p.pillar or "",
                "pillar_icon": PILLAR_EMOJIS.get(p.pillar or "", ""),
                "pillar_color": PILLAR_CONFIG.get(p.pillar or "", {}).get("color", "#6366f1"),
                "pconf_label": pconf["label"],
                "reading_time": reading_time_minutes(p.body_html or "") if p.body_html else None,
                "risk_count": len(p.quality_flags or []),
                "source_breakdown": p.source_breakdown or {},
                "featured_image": p.featured_image or "",
                "topic_icon": card_topic_icons.get(p.slug, ""),
                "pictogram": pick_card_pictogram(p) or "icon-research.svg",
                "signals": p.signals or {},
            }
            pillar_posts_data.append(post_data)

        html = render_template(
            "pillar_index.j2",
            content=_dummy(
                pconf["heading"],
                "index",
                description=pconf.get(
                    "description",
                    f"{pconf['label']} research articles — quality-scored and Bloom-classified.",
                ),
            ),
            pillar=pillar,
            pconf=pconf,
            posts=p_posts,
            is_index=False,
            page_path=f"{pillar}/",
            page_title=pconf["heading"],
            layer_sub=pconf["label"],
            thumbnail_base=f"{SITE_URL}/static/images",
            thumbnail_key=thumbnail_key,
            card_images=card_images,
            card_topic_icons=card_topic_icons,
            pillar_posts_data=pillar_posts_data,
            **ctx_base,
        )
        (out_dir / "index.html").write_text(html, encoding="utf-8")
        print(f"  pillar: {pillar}/index.html")

    # --- AML SIGNALS DASHBOARD ---
    aml_research = [p for p in research_items if p.pillar == "aml"]
    aml_learn = [item for item in learn_items if item.pillar == "aml"]
    tag_cloud: dict[str, int] = {}
    entity_cloud: dict[str, int] = {}
    source_totals: dict[str, int] = {}
    cross_pillar_links: dict[str, int] = {}
    timeline: dict[str, int] = {}
    for a in aml_research:
        for t in a.tags or []:
            tag_cloud[t] = tag_cloud.get(t, 0) + 1
        signals = a.signals or {}
        for e in signals.get("top_entities", []) or []:
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
            cross_pillar_links["data-engineering"] = (
                cross_pillar_links.get("data-engineering", 0) + 1
            )
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
    avg_sqi = sum((a.signals or {}).get("avg_sqi", 0) or 0 for a in aml_research) / max(
        len(aml_research), 1
    )
    unique_tags = set()
    for a in aml_research:
        for t in a.tags or []:
            unique_tags.add(t)
    unique_entities = set()
    for a in aml_research:
        for e in (a.signals or {}).get("top_entities", []) or []:
            unique_entities.add(e)

    aml_signals_html = render_template(
        "aml_signals.j2",
        content=_dummy(
            "AML Signals Dashboard",
            "index",
            description="Aggregated AML risk signals, entity profiles, and coverage metrics across AML articles.",
        ),
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
        is_index=False,
        page_path="aml/signals/",
        page_title="AML Signals Dashboard",
        thumbnail_base=f"{SITE_URL}/static/images",
        thumbnail_key=thumbnail_key,
        **ctx_base,
    )
    sig_dir = OUTPUT_DIR / "aml" / "signals"
    sig_dir.mkdir(parents=True, exist_ok=True)
    (sig_dir / "index.html").write_text(aml_signals_html, encoding="utf-8")
    print("  signals: aml/signals/index.html")

    # --- HOMEPAGE (filter future posts from featured/recent) ---
    published_research = [p for p in sorted_research if not is_future_post(p)]
    # Freshness cutoff: exclude articles older than 90 days from featured + recent
    ninety_days_ago = now - timedelta(days=90)
    fresh_posts = [
        p for p in published_research if not p.created_at or p.created_at >= ninety_days_ago
    ]
    featured = fresh_posts[:3] if len(fresh_posts) >= 3 else published_research[:3]
    # Hero: highest-SQI article from last 7 days
    seven_days_ago = now - timedelta(days=7)
    recent_articles = [
        p for p in published_research if p.created_at and p.created_at >= seven_days_ago
    ]
    hero_article = (
        max(recent_articles, key=lambda x: (x.signals or {}).get("avg_sqi", 0))
        if recent_articles
        else None
    )
    home_og_key = hashlib.md5(b"AcaciaFund homepage").hexdigest()[:12]
    home_og_url = f"{SITE_URL}/static/images/og_{home_og_key}.svg"

    # Homepage social proof aggregators
    unique_source_domains = set()
    unique_topic_tags = set()
    for c in all_content:
        for src in (c.source_breakdown or {}).keys():
            unique_source_domains.add(src)
        for t in c.tags or []:
            unique_topic_tags.add(t)

    # Top 3 trending by interest score (reuse sorted_research which is already scored)
    trending_slugs = set()
    for p in sorted_research[:3]:
        trending_slugs.add(p.slug)

    # Pictogram filenames for homepage research cards
    recent_pictograms = {}
    for p in fresh_posts[:6]:
        recent_pictograms[p.slug] = pick_card_pictogram(p)

    index_html = render_template(
        "index.j2",
        content=_dummy(
            "Research Synthesis & Learning",
            "index",
            description="AcaciaFund — research synthesis & experimental learning platform. Automated classification of HackerNews + arXiv content using Bloom taxonomy.",
        ),
        is_index=True,
        page_path="",
        og_image_url=home_og_url,
        featured_posts=featured,
        recent_posts=fresh_posts[:6],
        learn_items=learn_items[:6],
        knowledge_items=knowledge_items[:6],
        hero_article=hero_article,
        stat_article_count=len(all_content),
        stat_source_count=len(unique_source_domains),
        stat_topic_count=len(unique_topic_tags),
        trending_slugs=trending_slugs,
        recent_pictograms=recent_pictograms,
        thumbnail_base=f"{SITE_URL}/static/images",
        thumbnail_key=thumbnail_key,
        **ctx_base,
    )
    (OUTPUT_DIR / "index.html").write_text(index_html, encoding="utf-8")
    # Write homepage OG image
    out_static = STATIC_DST_DIR / "images"
    out_static.mkdir(parents=True, exist_ok=True)
    home_og_svg = generate_og_image(
        "AcaciaFund — Research Synthesis & Learning", "aml", {"sqi": 0.7}
    )
    (out_static / f"og_{home_og_key}.svg").write_text(home_og_svg, encoding="utf-8")
    print("  index: index.html")

    # --- /contact/ redirect to /knowledge/contact/ ---
    contact_dir = OUTPUT_DIR / "contact"
    contact_dir.mkdir(parents=True, exist_ok=True)
    (contact_dir / "index.html").write_text(
        f'<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
        f"<title>Contact — AcaciaFund</title>"
        f'<meta http-equiv="refresh" content="0;url={SITE_URL}/knowledge/contact/">'
        f'<link rel="canonical" href="{SITE_URL}/knowledge/contact/">'
        f'</head><body><p><a href="{SITE_URL}/knowledge/contact/">Contact — AcaciaFund</a></p></body></html>',
        encoding="utf-8",
    )
    print("  redirect: /contact/ → /knowledge/contact/")

    # --- /science/ redirect to /research/ ---
    science_dir = OUTPUT_DIR / "science"
    science_dir.mkdir(parents=True, exist_ok=True)
    (science_dir / "index.html").write_text(
        f'<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
        f"<title>Science — AcaciaFund</title>"
        f'<meta http-equiv="refresh" content="0;url={SITE_URL}/research/">'
        f'<link rel="canonical" href="{SITE_URL}/research/">'
        f'</head><body><p><a href="{SITE_URL}/research/">Research — AcaciaFund</a></p></body></html>',
        encoding="utf-8",
    )
    print("  redirect: /science/ → /research/")

    # --- Knowledge Graph Page (/graph/) ---
    cytograph_src = PROJECT_ROOT / "data" / "cytograph.json"
    if cytograph_src.exists():
        cytograph_dst = OUTPUT_DIR / "graph-data.json"
        cytograph_dst.write_text(cytograph_src.read_text(encoding="utf-8"), encoding="utf-8")
        try:
            graph_data = json.loads(cytograph_src.read_text(encoding="utf-8"))
            node_count = len(graph_data.get("nodes", []))
            edge_count = len(graph_data.get("edges", []))
        except Exception:
            node_count = 0
            edge_count = 0
    else:
        node_count = 0
        edge_count = 0

    graph_dir = OUTPUT_DIR / "graph"
    graph_dir.mkdir(parents=True, exist_ok=True)
    graph_html = render_template(
        "graph.j2",
        content=_dummy(
            "Knowledge Graph — AcaciaFund",
            "index",
            description="Interactive knowledge graph visualization of 98 research items, 102 semantic tags, and 228 document-to-tag relationships across the AcaciaFund knowledge repository.",
        ),
        node_count=node_count,
        edge_count=edge_count,
        is_index=False,
        page_path="graph/",
        page_title="Knowledge Graph",
        **ctx_base,
    )
    (graph_dir / "index.html").write_text(graph_html, encoding="utf-8")
    print("  graph: graph/index.html")

    # --- 404 ---
    _suggestions = sorted(all_content, key=lambda c: hashlib.md5(c.slug.encode()).hexdigest())[:3]
    html = render_template(
        "404.j2",
        content=_dummy("Page Not Found — AcaciaFund", "error"),
        is_index=False,
        page_path="404.html",
        page_type="error",
        suggestions=_suggestions,
        **ctx_base,
    )
    (OUTPUT_DIR / "404.html").write_text(html, encoding="utf-8")
    print("  error: 404.html")

    # --- TAG ARCHIVE PAGES (isolated from content cache) ---
    tag_items: dict[str, list] = defaultdict(list)
    for c in all_content:
        for t in c.tags or []:
            tag_items[t.lower().strip()].append(c)
    
    # Sort tag posts by date
    for tag_posts in tag_items.values():
        tag_posts.sort(key=lambda x: x.created_at or datetime.min, reverse=True)
    
    # Generate tag pages using isolated function
    tag_pages_count = generate_tag_pages(
        OUTPUT_DIR, tag_items, render_template, ctx_base, _dummy
    )
    if tag_items:
        print(f"  tags: {len(tag_items)} tag pages + index")

    # --- ADMIN PANEL (via build_taxonomies) ---
    from core.images.manifest import load_manifest as _load_manifest

    admin_pages_count = generate_admin_pages(
        OUTPUT_DIR, all_content, STATIC_DST_DIR, render_template, ctx_base, _dummy,
        load_admin_credentials_fn=load_admin_credentials,
        load_manifest_fn=_load_manifest,
        project_root=PROJECT_ROOT,
        section_types=SECTION_TYPES,
    )

    # --- SEARCH INDEX + PAGE (via build_taxonomies) ---
    search_pages_count = generate_search_pages(
        OUTPUT_DIR, STATIC_DST_DIR, all_content, render_template, ctx_base, _dummy,
    )

    # --- FEED (via build_taxonomies) ---
    feed_pages_count = generate_feed(
        OUTPUT_DIR, research_items, render_template, ctx_base,
        site_url=SITE_URL,
        site_name=SITE_NAME,
        now=now,
        is_future_post_fn=is_future_post,
        canonical_path_fn=canonical_path,
        slug_to_path_fn=slug_to_path,
    )

    # --- SITEMAP ---
    today = datetime.now(timezone.utc).date().isoformat()
    section_pages = list(pillar_groups) + ["research", "learn", "knowledge", "search"]
    tag_slugs = []
    for tag_slug in sorted(tag_items.keys()):
        slug_clean = re.sub(r"[^a-z0-9]+", "-", tag_slug).strip("-")
        if slug_clean:
            tag_slugs.append(slug_clean)
    sm = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    sm.append(
        f"  <url><loc>{SITE_URL}/</loc><lastmod>{today}</lastmod><changefreq>daily</changefreq><priority>1.0</priority></url>"
    )
    sm.append(
        f"  <url><loc>{SITE_URL}/tags/</loc><lastmod>{today}</lastmod><changefreq>weekly</changefreq><priority>0.4</priority></url>"
    )
    for c in all_content:
        if is_future_post(c):
            continue
        lastmod = (
            c.updated_at[:10] if c.updated_at else ""
            if c.updated_at
            else (c.created_at.date().isoformat() if c.created_at else today)
        )
        # Generate correct URL based on content type
        if c.content_type == "knowledge":
            clean_slug = c.slug[10:] if c.slug.startswith("knowledge/") else c.slug
            loc = f"{SITE_URL}/knowledge/{clean_slug}/"
        else:
            loc = slug_to_url(c.slug)
        sm.append(
            f"  <url><loc>{loc}</loc><lastmod>{lastmod}</lastmod><changefreq>monthly</changefreq><priority>0.6</priority></url>"
        )
    for p in section_pages:
        sm.append(
            f"  <url><loc>{SITE_URL}/{p}/</loc><lastmod>{today}</lastmod><changefreq>weekly</changefreq><priority>0.8</priority></url>"
        )
    for slug_clean in tag_slugs:
        sm.append(
            f"  <url><loc>{SITE_URL}/tags/{slug_clean}/</loc><lastmod>{today}</lastmod><changefreq>weekly</changefreq><priority>0.3</priority></url>"
        )
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
    _record_timing("content_rendering", time.time() - _t_render)

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
            (OUTPUT_DIR / root_file).write_text(
                root_src.read_text(encoding="utf-8"), encoding="utf-8"
            )
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
        "# Pillars: AML (anti-money laundering), Markets (market analysis), Data Engineering",
        "",
        "## Research Briefings",
    ]
    for c in all_content:
        if c.content_type in ("research",) and not is_future_post(c):
            date_str = c.created_at.strftime("%Y-%m-%d") if c.created_at else "unknown"
            sqi = c.signals.get("avg_sqi", 0) if c.signals else 0
            llms_full_lines.append(
                f"- [{date_str}] {c.title} (SQI: {sqi:.1f}) - {SITE_URL}/{c.slug}/"
            )
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
    (OUTPUT_DIR / "_headers").write_text(
        """/*
  X-Content-Type-Options: nosniff
  X-Frame-Options: DENY
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: camera=(), microphone=(), geolocation=()
  Content-Security-Policy: default-src 'self'; img-src 'self' https: data:; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; script-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'
  Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
  Cross-Origin-Opener-Policy: same-origin
  Cross-Origin-Resource-Policy: same-origin
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
""",
        encoding="utf-8",
    )

    total = len(list(OUTPUT_DIR.rglob("*.html")))
    duration = time.time() - start_time
    duration_ms = int(duration * 1000)
    print(f"Generation complete. Total pages: {total} ({duration:.2f}s)")

    # ── Mem0: Log deployment ──
    if MEM0_AVAILABLE:
        try:
            import subprocess

            commit_hash = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=str(PROJECT_ROOT), text=True
            ).strip()[:8]
            branch = subprocess.check_output(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=str(PROJECT_ROOT),
                text=True,
            ).strip()
            log_deployment(
                commit_hash=commit_hash,
                branch=branch,
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
        if c.signals
        and isinstance(c.signals, dict)
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
        "steps": _timings,
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
    build_meta_path.write_text(json.dumps(build_meta, indent=2, default=str), encoding="utf-8")
    print(f"  build-meta: build-meta.json ({build_meta_path.stat().st_size} bytes)")

    # ── LLMs.txt generation ──
    llms_lines = [f"# {SITE_NAME}", f"> {SITE_DESCRIPTION}", ""]
    llms_full_lines = [f"# {SITE_NAME} — Full Content", f"> {SITE_DESCRIPTION}", ""]
    for c in all_content:
        slug = getattr(c, "slug", None) or ""
        title = getattr(c, "title", None) or ""
        desc = (getattr(c, "description", None) or "")[:200]
        if not slug or not title:
            continue
        url = f"{SITE_URL}/{slug}/"
        llms_lines.append(f"- [{title}]({url}): {desc}")
        body_text = re.sub(r"<[^>]+>", "", getattr(c, "body_html", None) or "")
        body_text = re.sub(r"\s+", " ", body_text).strip()
        llms_full_lines.append(f"## {title}")
        llms_full_lines.append(f"> Source: {url}")
        llms_full_lines.append(f"> Tags: {', '.join(getattr(c, 'tags', None) or [])}")
        llms_full_lines.append(f"> SQI: {getattr(c, 'sqi', 0.0) or 0.0}")
        llms_full_lines.append("")
        llms_full_lines.append(body_text[:5000])
        llms_full_lines.append("")

    llms_lines.append(f"- [Knowledge Graph]({SITE_URL}/graph/): Interactive knowledge graph visualization of {len(all_content)} items")
    (OUTPUT_DIR / "llms.txt").write_text("\n".join(llms_lines), encoding="utf-8")
    (OUTPUT_DIR / "llms-full.txt").write_text("\n".join(llms_full_lines), encoding="utf-8")
    print(f"  llms: llms.txt ({len(llms_lines)} lines, {len(all_content)} items)")
    print(f"  llms: llms-full.txt ({len(llms_full_lines)} lines, {len(all_content)} items)")

    if low_sqi_items:
        log_text = "; ".join(f"{i['slug']} (SQI={i['sqi']})" for i in low_sqi_items)
        print(f"  quality gate: {len(low_sqi_items)} items below SQI {SQI_THRESHOLD_MIN}")
        print(f"    -> {log_text}")

    if failed_count > 0:
        print(f"  warnings: {failed_count} items failed during processing (see logs for details)")

    # Save manifest for incremental builds
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(current_manifest, f, indent=2)
    
    # Update cache for all processed items
    print("  Updating build cache...")
    for item in all_content:
        slug = getattr(item, "slug", "")
        if slug:
            # Handle both flat files and directory-based pages
            if "/" in slug:
                output_path = OUTPUT_DIR / slug / "index.html"
            else:
                output_path = OUTPUT_DIR / f"{slug}.html"
            
            if output_path.exists():
                # Use precomputed content hash (from before mutations) for consistency
                content_hash = content_hashes.get(slug) or _get_content_hash(item)
                cache.update_entry(output_path, content_hash,
                                 {"slug": slug, "content_type": getattr(item, "content_type", "")},
                                 is_content=True)
    
    # Save build cache with both hash types
    _t0 = time.time()
    cache.content_templates_hash = cache.compute_templates_hash(TEMPLATE_DIR, content_only=True)
    cache.templates_hash = cache.compute_templates_hash(TEMPLATE_DIR, content_only=False)
    cache.save()
    _record_timing("cache_save", time.time() - _t0)

    # Write registry index to reflect actual generated pages
    # (no local imports - use globals)
    
    registry_dir = Path("registry")
    registry_dir.mkdir(exist_ok=True)
    index_path = registry_dir / "index.json"
    
    # Count pillars from all_content
    pillar_counts = {}
    for item in all_content:
        pillar = item.pillar or "unknown"
        pillar_counts[pillar] = pillar_counts.get(pillar, 0) + 1
    
    index = {
        "manifest_type": "registry-index",
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "counts": {
            "runs": 0,
            "pages": total,
            "pillars": pillar_counts,
        },
        "latest_by_pillar": {},
        "runs": [],
        "pages": [{"content_id": item.slug, "pillar": item.pillar or "unknown", "title": item.title or "", "published_at": item.date_str or ""} for item in all_content if item.slug],
        "by_content_id": {item.slug: {"content_id": item.slug, "pillar": item.pillar or "unknown", "title": item.title or ""} for item in all_content if item.slug},
        "by_run_id": {},
        "checksum": "",
    }
    
    # Compute checksum
    def canonical_json(payload):
        return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    index["checksum"] = hashlib.sha256(canonical_json({k: v for k, v in index.items() if k != "checksum"}).encode("utf-8")).hexdigest()
    
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)
    
    print(f"  registry: index.json updated ({total} pages, {len(pillar_counts)} pillars)")

    # Print build cache stats
    cache_stats = cache.get_stats()
    print(f"\n📊 Build Cache: {cache_stats['total_entries']} entries, {cache_stats['cache_size_kb']:.1f} KB")
    
    # Print total build time
    total_time = time.time() - start_time
    if _pool is not None:
        _pool.close()

    print(f"\n✅ Build complete: {total} pages in {total_time:.2f}s ({total/total_time:.1f} pages/s)")

    return 0


def _build_jsonld(item: Any, site_url: str, page_path: str = "") -> dict[str, Any]:
    """Build JSON-LD schema.org Article dict for a content item."""
    author_name = getattr(item, "author", None) or "AcaciaFund"
    tags = getattr(item, "tags", None) or []
    sqi_val = getattr(item, "sqi", 0.0) or 0.0
    signals = getattr(item, "signals", None) or {}
    sqi_avg = signals.get("avg_sqi", 0.0) if isinstance(signals, dict) else 0.0
    source_breakdown = getattr(item, "source_breakdown", None) or {}
    sources = []
    if isinstance(source_breakdown, dict):
        for src, cnt in source_breakdown.items():
            sources.append({"@type": "Organization", "name": src, "description": f"{cnt} references"})

    schema: dict[str, Any] = {
        "@context": "https://schema.org",
        "@type": "TechArticle",
        "headline": getattr(item, "title", ""),
        "description": (getattr(item, "description", None) or "")[:300],
        "author": {"@type": "Person", "name": author_name},
        "keywords": ", ".join(tags[:10]),
        "inLanguage": "en",
        "proficiencyLevel": getattr(item, "difficulty", None) or "",
    }

    dt = getattr(item, "created_at", None)
    if dt:
        try:
            schema["datePublished"] = dt.isoformat() if hasattr(dt, "isoformat") else str(dt)
        except Exception:
            pass
    updated = getattr(item, "updated_at", None)
    if updated:
        schema["dateModified"] = str(updated)

    ds = getattr(item, "date_str", None)
    if ds:
        schema["datePublished"] = ds

    if page_path:
        schema["mainEntityOfPage"] = {"@type": "WebPage", "@id": f"{site_url}/{page_path}"}
    elif hasattr(item, "slug") and item.slug:
        schema["mainEntityOfPage"] = {"@type": "WebPage", "@id": f"{site_url}/{item.slug}/"}

    sqi_display = sqi_avg if sqi_avg > 0 else sqi_val
    if sqi_display > 0:
        schema["sqi"] = round(sqi_display, 3)
        schema["signalQualityIndex"] = round(sqi_display, 3)

    pillar = getattr(item, "pillar", None)
    if pillar:
        schema["about"] = {"@type": "Thing", "name": pillar}

    if sources:
        schema["citation"] = sources

    enriched = getattr(item, "enriched", False)
    if enriched:
        schema["semanticEnrichment"] = "completed"
        en_at = getattr(item, "enriched_at", None)
        if en_at:
            schema["semanticEnrichmentDate"] = str(en_at)

    return schema


def _dummy(title="", category="post", body_html="", description=""):
    return type(
        "obj",
        (object,),
        {
            "title": title,
            "language": "en",
            "category": category,
            "slug": "",
            "body_html": body_html,
            "description": description,
            "created_at": None,
            "updated_at": None,
            "tags": [],
            "pillar": "",
            "difficulty": "",
            "date_str": "",
            "thumbnail_svg": "",
            "og_svg": "",
            "signals": {},
            "source_breakdown": {},
            "quality_metrics": {},
            "bloom_questions": [],
            "flashcards": [],
            "trending_html": "",
            "analysis_html": "",
            "cross_pillar_html": "",
            "quality_flags": [],
            "knowledge_category": "",
            "author": "AcaciaFund",
            "sqi": 0.0,
            "enriched": False,
            "enriched_at": None,
        },
    )


if __name__ == "__main__":
    exit(main())
