#!/usr/bin/env python3
"""
Build script for AcaciaFund: converts registry.json to static HTML using Jinja2 templates.
3-category taxonomy: research | learn | knowledge
"""

import hashlib
import json
import logging
import re
import shutil
import subprocess
import sys
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote as urlquote

import pandas as pd
import tomllib
from jinja2 import Environment, FileSystemLoader, select_autoescape

from config import (
    KNOWLEDGE_TO_PILLAR_CATEGORY,
    OUTPUT_DIR,
    PILLAR_COLORS,
    PILLAR_CONFIG,
    PILLAR_EMOJIS,
    PILLAR_NAMES,
    PILLAR_URL_MAP,
    PIPELINE_STATIC_DIR,
    PLAUSIBLE_DOMAIN,
    PROJECT_ROOT,
    REGISTRY_PATH,
    SITE_DESCRIPTION,
    SITE_NAME,
    SITE_URL,
    SQI_DEFAULT,
    SQI_THRESHOLD_MIN,
    STATIC_DST_DIR,
    TEMPLATE_DIR,
)

# ── Asset pipeline ──
from core.assets import create_asset_manager

# ── Extracted utility modules ──
from core.build_content import (
    LAYER_ICONS,
    SECTION_TYPES,
    _build_jsonld,
    _cleanup_partial_output,
    _dummy,
    _generate_page_images,
    _generate_page_svgs,
    _process_item_body,
    _serialize_quiz,
    generate_article_fingerprint,
    layer_indicator_html,
)
from core.build_images import (
    _resolve_ref_file,
    generate_card_thumbnail,
    pick_card_pictogram,
    resolve_section_image,
    thumbnail_key,
)
from core.build_quality import (
    _compute_quality,
    _compute_sqi_for_item,
    _get_content_hash,
    generate_sqi_badge,
    interest_score,
)
from core.build_utils import (
    _get_created,
    find_cross_pillar,
    find_related,
    get_topic_icons,
    group_by_pillar,
    load_admin_credentials,
    reading_time_minutes,
)
from core.content import Content

# ── Page generation helpers (new modular structure) ──
from core.learning_paths import (
    build_all_learning_paths,
    enrich_journeys_with_content,
    generate_cross_pillar_synthesis,
    generate_learning_path_context,
)
from core.schema_builder import (
    compute_cross_pillar_feynman_paths,
    compute_feynman_learning_paths,
)
from core.urls import (
    canonical_path,
    pillar_to_url,
    slug_to_fspath,
    slug_to_path,
    slug_to_url,
)


# --- Knowledge Graph Generation ---
def generate_knowledge_graph():
    script_path = PROJECT_ROOT / "scripts" / "build_knowledge_graph.py"
    if script_path.exists():
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=120,
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
    from services.mem0 import (
        log_deployment,  # pyright: ignore[reportMissingImports, reportAttributeAccessIssue]
    )

    MEM0_AVAILABLE = True
except ImportError:
    MEM0_AVAILABLE = False
    log_deployment = None  # pyright: ignore[reportAssignmentType]

# ── Build cache for incremental builds ──
from core.build_cache import (  # noqa: E402
    get_cache,
    get_worker_pool,
    parallel_map,
)

# ── Taxonomy generation (separate from core content) ──
from core.build_taxonomies import (  # noqa: E402
    generate_admin_pages,
    generate_feed,
    generate_search_pages,
    generate_tag_pages,
)

# ── Stop words loaded from external config ──
STOP_WORDS = set(json.loads((Path(__file__).parent / "config" / "stop_words.json").read_text(encoding="utf-8")))


DIFFICULTY_ORDER: dict[str, int] = {"beginner": 0, "intermediate": 1, "advanced": 2}


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
    "foundations": {
        "label": "Foundations",
        "icon": "📚",
        "color": "#0ea5e9",
        "bg_color": "#0ea5e9",
        "description": "Core concepts, theoretical frameworks, and foundational knowledge across all pillars.",
    },
    "advanced-techniques": {
        "label": "Advanced Techniques",
        "icon": "🔬",
        "color": "#ec4899",
        "bg_color": "#ec4899",
        "description": "Specialized algorithms, methods, and advanced technical implementations.",
    },
    "best-practices": {
        "label": "Best Practices",
        "icon": "✅",
        "color": "#10b981",
        "bg_color": "#10b981",
        "description": "Practical guides, optimization strategies, and implementation recommendations.",
    },
    "regulations": {
        "label": "Regulations",
        "icon": "📋",
        "color": "#f59e0b",
        "bg_color": "#f59e0b",
        "description": "Regulatory frameworks, compliance requirements, and policy analysis.",
    },
    "industry-analysis": {
        "label": "Industry Analysis",
        "icon": "📊",
        "color": "#8b5cf6",
        "bg_color": "#8b5cf6",
        "description": "Market trends, industry reports, and sector-specific analysis.",
    },
    "market-analysis": {
        "label": "Market Analysis",
        "icon": "📈",
        "color": "#06b6d4",
        "bg_color": "#06b6d4",
        "description": "Market dynamics, volatility patterns, and financial analysis frameworks.",
    },
    "strategies": {
        "label": "Strategies",
        "icon": "🎯",
        "color": "#f43f5e",
        "bg_color": "#f43f5e",
        "description": "Trading strategies, investment approaches, and tactical methodologies.",
    },
    "methodology": {
        "label": "Methodology",
        "icon": "🧪",
        "color": "#84cc16",
        "bg_color": "#84cc16",
        "description": "Research methods, backtesting frameworks, and analytical approaches.",
    },
    "tutorial-code": {
        "label": "Tutorial with Code",
        "icon": "💻",
        "color": "#14b8a6",
        "bg_color": "#14b8a6",
        "description": "Step-by-step tutorials with executable code examples and implementations.",
    },
}


def is_future_post(post) -> bool:
    """Check if a post is future-dated based on frontmatter date or created_at."""
    from datetime import date

    today = date.today()

    if getattr(post, "date_str", ""):
        try:
            post_date = post.date_str[:10]
            post_dt = date.fromisoformat(post_date)
            if post_dt > today:
                return True
        except (ValueError, TypeError):
            pass

    dt = _get_created(post)
    if dt and dt > datetime.now(timezone.utc):
        return True

    return False


def main():  # pyright: ignore[reportGeneralTypeIssues]
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
    except (OSError, json.JSONDecodeError, ValueError) as e:
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

    # Bytecode cache disabled for CI/CD compatibility
    # bytecode_cache = FileSystemBytecodeCache(str(PROJECT_ROOT / ".cache" / "jinja2"))
    env = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=select_autoescape(["html", "xml"]),
        # bytecode_cache=bytecode_cache,
    )
    env.filters["reading_time"] = reading_time_minutes
    env.filters["urlencode"] = lambda s: urlquote(s or "", safe="")
    env.filters["pictogram"] = pick_card_pictogram
    env.globals["resolve_topic_icon"] = resolve_topic_icon
    env.globals["render_topic_icon"] = render_topic_icon
    env.globals["_pick_subtopic"] = _pick_subtopic
    env.globals["slug_to_url"] = slug_to_url
    env.globals["pillar_to_url"] = pillar_to_url

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
                except (json.JSONDecodeError, TypeError):
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

    # --- Ontology Concepts ---
    ontology_path = PROJECT_ROOT / "data" / "ontology.json"
    ontology = None
    if ontology_path.exists():
        try:
            from core.ontology import OntologyManager, extract_concepts_from_text
            ontology = OntologyManager.load(ontology_path)
            # Enrich ontology with Feynman learning framework metadata
            try:
                from scripts.enrich_feynman import enrich_all_with_stubs
                enrich_all_with_stubs(ontology_path, ontology_path)
                ontology = OntologyManager.load(ontology_path)
                eli5_count = sum(
                    1 for c in ontology._concepts.values() if c.eli5_explanation
                )
                print(
                    f"  Feynman-enriched ontology: {ontology.concept_count()} "
                    f"concepts ({eli5_count} with ELI5)"
                )
            except Exception as fe:
                print(f"  Feynman enrichment skipped ({fe})")
            print(
                f"  Loaded ontology: {ontology.concept_count()} concepts, "
                f"{ontology.relation_count()} relations"
            )
        except Exception as e:
            print(f"  Ontology load failed: {e}")
            ontology = None

    # --- Inspiration Sources (external references per pillar) ---
    import tomllib as _toml
    pillars_toml_path = PROJECT_ROOT / "etc" / "pillars.toml"
    inspiration_sources = {}
    if pillars_toml_path.exists():
        with open(pillars_toml_path, "rb") as f:
            toml_data = _toml.load(f)
        inspiration_sources = toml_data.get("inspiration_sources", {})

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
    for css_file in sorted((PROJECT_ROOT / "static/css").glob("*.css")):
        css_hasher.update(css_file.read_bytes())
    for js_file in sorted((PROJECT_ROOT / "static/js").glob("*.js")):
        css_hasher.update(js_file.read_bytes())
    build_hash = css_hasher.hexdigest()[:12]
    # Convert dict/ContentItem content to Content objects
    all_content = [Content.from_dict(c if isinstance(c, dict) else c.model_dump()) for c in registry.content]

    # Initialize logging first (needed for validation logging)
    log_path = OUTPUT_DIR / "build_errors.log"
    if log_path.exists() and log_path.stat().st_size > 1_048_576:
        log_path.unlink()
    logging.basicConfig(
        filename=log_path,
        level=logging.ERROR,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        filemode="a",
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
        return 1

    # Backfill SQI for items missing it
    sqi_backfilled = 0
    for item in all_content:
        has_sqi = item.sqi is not None and item.sqi > 0
        signals_avg = (item.signals or {}).get("avg_sqi", 0) if isinstance(item.signals, dict) else 0
        if not has_sqi and signals_avg and signals_avg > 0:
            item.sqi = round(signals_avg, 3)
            sqi_backfilled += 1
        elif not has_sqi and not signals_avg:
            item.sqi = _compute_sqi_for_item(item)
            sqi_backfilled += 1
    if sqi_backfilled:
        print(f"  sqi: backfilled {sqi_backfilled} items")

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
                timeout=120,
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
            with open(knowledge_graph_path, "r", encoding="utf-8") as f:
                knowledge_graph = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            print(f"Warning: Failed to load knowledge graph: {e}")
            knowledge_graph = {}
    else:
        knowledge_graph = {}
    _record_timing("graph_build", time.time() - _t0)


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
        # Handle both flat files and directory-based pages
        fspath = slug_to_fspath(slug)
        if "/" in slug:
            output_path = OUTPUT_DIR / fspath / "index.html"
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
    # research_items/learn_items/knowledge_items counts logged implicitly via processing below

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

    # Pre-compute ontology concept sets for all items (avoid O(n²) re-extraction)
    _concept_cache: dict[str, set] = {}
    if ontology and ontology.concept_count() > 0:
        import re as _re_pre
        for item in all_content:
            tags_text = " ".join(item.tags or [])
            body_text = _re_pre.sub(r"<[^>]+>", " ", item.body_html or "")
            combined = f"{item.title or ''} {tags_text} {body_text[:800]}"
            matches = extract_concepts_from_text(combined, ontology)
            _matched: set[str] = {c.id for c, s in matches if s >= 0.35}
            for _tag in (item.tags or []):
                if ontology.get_concept(_tag):
                    _matched.add(_tag)
            _concept_cache[item.slug] = _matched

        # Persist concept→content mapping for downstream tools (audit, analytics)
        try:
            _concept_content_map_path = PROJECT_ROOT / "data" / "concept_content_map.json"
            _concept_content_map: dict[str, list[str]] = {}
            for _slug, _cids in sorted(_concept_cache.items()):
                _concept_content_map[_slug] = sorted(_cids)
            _concept_content_map_path.write_text(
                json.dumps(_concept_content_map, indent=2, sort_keys=True), encoding="utf-8"
            )
            print(f"  concept map: saved {len(_concept_content_map)} items to data/concept_content_map.json")
        except Exception as _cm_err:
            print(f"  concept map: save failed — {_cm_err}")

    # --- KNOWLEDGE PAGES ---
    for item in knowledge_items:
        try:
            slug = item.slug
            if slug in items_to_skip:
                print(f"  knowledge: {slug} (skipped - unchanged)")
                continue
            # New format: slug contains pillar prefix (e.g. "aml/knowledge/topic")
            # Platform pages stay at "knowledge/page" (no pillar prefix)
            page_path = canonical_path(slug_to_path(slug))
            out_file = OUTPUT_DIR / slug_to_fspath(slug_to_path(slug))
            out_file.parent.mkdir(parents=True, exist_ok=True)

            body, toc_items = _process_item_body(item, strip_emoji=False)

            kcat = KNOWLEDGE_CATEGORIES.get(item.knowledge_category, {})
            if kcat:
                kcat["slug"] = item.knowledge_category

            # Resolve pillar-specific subcategory from knowledge category
            pillar_subcategory = KNOWLEDGE_TO_PILLAR_CATEGORY.get(
                item.knowledge_category, {}
            ).get(item.pillar or "aml", "")

            related_research = find_related(research_items, item, 3)
            related_learn = find_related(learn_items, item, 3)
            visual_fingerprint = generate_article_fingerprint(
                item.slug, item.title, item.pillar or "", "knowledge", item.tags
            )
            layer_badge = layer_indicator_html("knowledge", item.pillar or "")

            thumb_key, og_key, feat_img_path, og_image_url, thumb_base = _generate_page_images(item, "knowledge")

            layer_sub = (
                item.knowledge_category.replace("_", " ").title()
                if item.knowledge_category
                else item.pillar or ""
            )
            quality_score, quality_badge, quality_metrics = _compute_quality(quality_scores, item.slug)
            quiz_json = _serialize_quiz(item)

            trend_info = trend_detection.get(item.slug, {})
            trend_strength = trend_info.get("trend_strength", 0)
            adoption_level = trend_info.get("adoption_level", "mainstream")
            impact_level = trend_info.get("impact_level", "low")
            trend_categories = trend_info.get("trend_categories", "")

            source_info = source_verification.get(item.slug, {})
            source_verified = source_info.get("verified", False)
            source_evidence = source_info.get("evidence", [])

            # Extract ontology concepts for this item
            ontology_concepts = []
            if ontology and ontology.concept_count() > 0:
                try:
                    tags_text = " ".join(item.tags or [])
                    title_text = item.title or ""
                    body_text = item.body_html or ""
                    import re as _re
                    body_text = _re.sub(r"<[^>]+>", " ", body_text)
                    combined = f"{title_text} {tags_text} {body_text[:500]}"
                    matches = extract_concepts_from_text(combined, ontology)
                    seen_ids = set()
                    for concept, score in matches:
                        if concept.id not in seen_ids and score >= 0.35:
                            seen_ids.add(concept.id)
                            _concept_phil_lineage = getattr(concept, "philosophical_lineage", None) or []
                            _concept_ep_status = getattr(concept, "epistemic_status", "") or ""
                            _concept_norm_basis = getattr(concept, "normative_basis", "") or ""
                            _concept_phil_sources = getattr(concept, "philosophical_sources", None) or []
                            _concept_cross_pillar = getattr(concept, "cross_pillar_analogs", None) or []
                            ontology_concepts.append({
                                "id": concept.id,
                                "label": concept.label,
                                "name": concept.label,
                                "description": concept.description,
                                "score": round(score, 2),
                                "philosophical_lineage": _concept_phil_lineage,
                                "epistemic_status": _concept_ep_status,
                                "normative_basis": _concept_norm_basis,
                                "philosophical_sources": _concept_phil_sources,
                                "cross_pillar_analogs": _concept_cross_pillar,
                                # Feynman fields
                                "eli5_explanation": getattr(concept, "eli5_explanation", None),
                                "analogy": getattr(concept, "analogy", None),
                                "concrete_example": getattr(concept, "concrete_example", None),
                                "feynman_diagram": getattr(concept, "feynman_diagram", None),
                                "gap_questions": getattr(concept, "gap_questions", []),
                                "teach_back_prompt": getattr(concept, "teach_back_prompt", None),
                                "build_exercise": getattr(concept, "build_exercise", None),
                                "feynman_difficulty": getattr(concept, "feynman_difficulty", 1),
                                "explanation_quality": getattr(concept, "explanation_quality", 0.0),
                            })
                    ontology_concepts = ontology_concepts[:8]
                except Exception:
                    pass

            # Build external references from inspiration sources
            external_references = []
            pillar_key = item.pillar or "aml"
            pillar_prefix = {"aml": "aml", "stock": "ms", "data-engineering": "de"}.get(pillar_key, "aml")
            pillar_sources = inspiration_sources.get(pillar_prefix, {})
            for src_key, src_info in pillar_sources.items():
                if isinstance(src_info, dict) and "url" in src_info:
                    external_references.append({
                        "title": src_info["name"],
                        "url": src_info["url"],
                        "description": src_info.get("description", ""),
                        "source": src_info["name"],
                        "relevance": src_info.get("relevance", 0.7),
                    })
            external_references.sort(key=lambda x: x.get("relevance", 0), reverse=True)
            external_references = external_references[:6]

            # SQI bonus for semantic enrichment (concepts + references)
            semantic_bonus = 0.0
            if ontology_concepts:
                semantic_bonus += min(0.03, len(ontology_concepts) * 0.005)
            if external_references:
                semantic_bonus += min(0.02, len(external_references) * 0.005)
            if semantic_bonus > 0:
                quality_score, quality_badge, quality_metrics = _compute_quality(quality_scores, item.slug, semantic_bonus)

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
                thumbnail_key=thumb_key,
                og_image_url=og_image_url,
                quiz_json=quiz_json,
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
                ontology_concepts=ontology_concepts,
                external_references=external_references,
                cross_pillar_items=find_cross_pillar(item, all_content, ontology, _concept_cache=_concept_cache),
                is_index=False,
                page_type="knowledge",
                layer="knowledge",
                layer_icon=LAYER_ICONS["knowledge"],
                layer_sub=layer_sub,
                pillar_subcategory=pillar_subcategory,
                **ctx_base,
            )
            out_file.write_text(html, encoding="utf-8")
            print(f"  knowledge: {out_file.relative_to(OUTPUT_DIR)}")

            _generate_page_svgs(item, "knowledge", thumb_key, og_key)

        except (ValueError, TypeError, OSError, KeyError):
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

    # Per-category knowledge landing pages
    _kc_count = 0
    for _kc_id, _kc_items in grouped.items():
        _kc_cfg = KNOWLEDGE_CATEGORIES.get(_kc_id, {})
        _kc_html = render_template(
            "knowledge_index.j2",
            content=_dummy(
                f"{_kc_cfg.get('label', _kc_id.title())} — Knowledge — AcaciaFund",
                "index",
                description=_kc_cfg.get("description", f"Knowledge category: {_kc_id}."),
            ),
            items=_kc_items,
            grouped={_kc_id: _kc_items},
            categories=KNOWLEDGE_CATEGORIES,
            thumbnail_base=thumb_base,
            thumbnail_key=thumbnail_key,
            page_title=_kc_cfg.get("label", _kc_id.title()),
            is_index=False,
            page_path=f"knowledge/{_kc_id}/",
            layer="knowledge",
            layer_icon=LAYER_ICONS["knowledge"],
            **ctx_base,
        )
        _kc_dir = knowledge_dir / _kc_id
        _kc_dir.mkdir(parents=True, exist_ok=True)
        (_kc_dir / "index.html").write_text(_kc_html, encoding="utf-8")
        _kc_count += 1
    if _kc_count:
        print(f"  knowledge-categories: {_kc_count} pages")

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
            if slug in items_to_skip:
                print(f"  learn: {slug} (skipped - unchanged)")
                continue
            page_path = canonical_path(slug_to_path(slug))
            out_file = OUTPUT_DIR / slug_to_fspath(slug_to_path(slug))

            body, toc_items = _process_item_body(item, strip_emoji=False)

            pillar = item.pillar or ""
            pconf = PILLAR_CONFIG.get(pillar) if pillar else None
            related_research = find_related(research_items, item, 3)
            related_knowledge = find_related(knowledge_items, item, 3)
            visual_fingerprint = generate_article_fingerprint(
                item.slug, item.title, pillar, "learn", item.tags
            )
            layer_badge = layer_indicator_html("learn", pillar)

            thumb_key, og_key, feat_img_path, og_image_url, thumb_base = _generate_page_images(item, "learn")

            source_info = source_verification.get(item.slug, {})
            source_verified = source_info.get("verified", False)
            source_evidence = source_info.get("evidence", [])

            # Extract ontology concepts for learn items
            ontology_concepts = []
            if ontology and ontology.concept_count() > 0:
                try:
                    tags_text = " ".join(item.tags or [])
                    title_text = item.title or ""
                    body_text = item.body_html or ""
                    body_text = re.sub(r"<[^>]+>", " ", body_text)
                    combined = f"{title_text} {tags_text} {body_text[:500]}"
                    matches = extract_concepts_from_text(combined, ontology)
                    seen_ids = set()
                    for concept, score in matches:
                        if concept.id not in seen_ids and score >= 0.35:
                            seen_ids.add(concept.id)
                            ontology_concepts.append({
                                "id": concept.id,
                                "name": concept.label,
                                "label": concept.label,
                                "description": concept.description,
                                "score": round(score, 2),
                                # Feynman fields
                                "eli5_explanation": getattr(concept, "eli5_explanation", None),
                                "analogy": getattr(concept, "analogy", None),
                                "concrete_example": getattr(concept, "concrete_example", None),
                                "feynman_diagram": getattr(concept, "feynman_diagram", None),
                                "gap_questions": getattr(concept, "gap_questions", []),
                                "teach_back_prompt": getattr(concept, "teach_back_prompt", None),
                                "build_exercise": getattr(concept, "build_exercise", None),
                                "feynman_difficulty": getattr(concept, "feynman_difficulty", 1),
                            })
                    ontology_concepts = ontology_concepts[:8]
                except Exception:
                    pass

            # Build external references for learn items
            external_references = []
            lp_key = item.pillar or "aml"
            lp_prefix = {"aml": "aml", "stock": "ms", "data-engineering": "de"}.get(lp_key, "aml")
            lp_sources = inspiration_sources.get(lp_prefix, {})
            for src_key, src_info in lp_sources.items():
                if isinstance(src_info, dict) and "url" in src_info:
                    external_references.append({
                        "title": src_info["name"],
                        "url": src_info["url"],
                        "description": src_info.get("description", ""),
                        "source": src_info["name"],
                        "relevance": src_info.get("relevance", 0.7),
                    })
            external_references.sort(key=lambda x: x.get("relevance", 0), reverse=True)
            external_references = external_references[:6]

            quiz_json = _serialize_quiz(item)
            quality_score, quality_badge, quality_metrics = _compute_quality(quality_scores, item.slug)

            bl_name = BLOOM_NAMES.get(item.highest_bloom or 0, "")
            layer_sub = f"Level {item.highest_bloom}: {bl_name}" if bl_name else ""

            # Determine prev/next only among actual lessons (exclude meta "learn" page)
            li = next((j for j, lli in enumerate(learn_lessons) if lli.slug == item.slug), None)
            prev_lesson = learn_lessons[li - 1] if li is not None and li > 0 else None
            next_lesson = learn_lessons[li + 1] if li is not None and li + 1 < len(learn_lessons) else None

            trend_info = trend_detection.get(item.slug, {})
            trend_strength = trend_info.get("trend_strength", 0)
            adoption_level = trend_info.get("adoption_level", "mainstream")
            impact_level = trend_info.get("impact_level", "low")
            trend_categories = trend_info.get("trend_categories", "")

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
                thumbnail_key=thumb_key,
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
                ontology_concepts=ontology_concepts,
                external_references=external_references,
                cross_pillar_items=find_cross_pillar(item, all_content, ontology, _concept_cache=_concept_cache),
                is_index=False,
                layer="learn",
                layer_icon=LAYER_ICONS["learn"],
                layer_sub=layer_sub,
                **ctx_base,
            )
            out_file.parent.mkdir(parents=True, exist_ok=True)
            out_file.write_text(html, encoding="utf-8")
            print(f"  learn: {out_file.relative_to(OUTPUT_DIR)}")

            _generate_page_svgs(item, "learn", thumb_key, og_key)

        except (ValueError, TypeError, OSError, KeyError):
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
            if slug in items_to_skip:
                print(f"  research: {slug} (skipped - unchanged)")
                continue
            page_path = canonical_path(slug_to_path(slug))
            out_file = OUTPUT_DIR / slug_to_fspath(slug_to_path(slug))

            body, toc_items = _process_item_body(item, strip_emoji=True)

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
            thumb_key, og_key, feat_img_path, og_image_url, thumb_base = _generate_page_images(item, "research")
            quiz_json = _serialize_quiz(item)
            topic_sub = _pick_subtopic([item.title], pillar)
            topic_icon_html = render_topic_icon(
                topic_sub, PILLAR_COLORS.get(pillar, PILLAR_COLORS["aml"])["accent"]
            )

            # Extract ontology concepts for research items
            ontology_concepts_r = []
            external_references_r = []
            if ontology and ontology.concept_count() > 0:
                try:
                    tags_text = " ".join(item.tags or [])
                    title_text = item.title or ""
                    import re as _re2
                    body_text = _re2.sub(r"<[^>]+>", " ", item.body_html or "")
                    combined = f"{title_text} {tags_text} {body_text[:500]}"
                    matches = extract_concepts_from_text(combined, ontology)
                    seen_ids = set()
                    for concept, score in matches:
                        if concept.id not in seen_ids and score >= 0.35:
                            seen_ids.add(concept.id)
                            ontology_concepts_r.append({
                                "id": concept.id,
                                "name": concept.label,
                                "description": concept.description,
                                "score": round(score, 2),
                            })
                    ontology_concepts_r = ontology_concepts_r[:8]
                except Exception:
                    pass

            pillar_prefix_r = {"aml": "aml", "stock": "ms", "data-engineering": "de"}.get(pillar, "aml")
            pillar_sources_r = inspiration_sources.get(pillar_prefix_r, {})
            for src_key, src_info in pillar_sources_r.items():
                if isinstance(src_info, dict) and "url" in src_info:
                    external_references_r.append({
                        "title": src_info["name"],
                        "url": src_info["url"],
                        "description": src_info.get("description", ""),
                        "source": src_info["name"],
                        "relevance": src_info.get("relevance", 0.7),
                    })
            external_references_r.sort(key=lambda x: x.get("relevance", 0), reverse=True)
            external_references_r = external_references_r[:6]

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
                thumbnail_key=thumb_key,
                thumbnail_key_fn=thumbnail_key,
                toc_items=toc_items,
                related_posts=related,
                related_learn=related_learn,
                related_kg=knowledge_graph.get(item.slug, []),
                visual_fingerprint=visual_fingerprint,
                layer_badge=layer_badge,
                featured_image=resolve_section_image(item.featured_image),
                image_credit=item.image_credit,
                quiz_json=quiz_json,
                topic_icon_html=topic_icon_html,
                layer_sub=pconf["label"],
                source_synthesis=source_synthesis.get(item.slug, []),
                cross_pillar_items=find_cross_pillar(item, all_content, ontology, _concept_cache=_concept_cache),
                ontology_concepts=ontology_concepts_r,
                external_references=external_references_r,
                **ctx_base,
            )
            out_file.parent.mkdir(parents=True, exist_ok=True)
            out_file.write_text(html, encoding="utf-8")
            print(f"  research: {out_file.relative_to(OUTPUT_DIR)}")

            _generate_page_svgs(item, "research", thumb_key, og_key)

        except (ValueError, TypeError, OSError, KeyError):
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
        pillar_url = pillar_to_url(pillar)
        out_dir = OUTPUT_DIR / pillar_url
        out_dir.mkdir(parents=True, exist_ok=True)
        pconf = PILLAR_CONFIG.get(pillar, PILLAR_CONFIG["aml"])

        # Glossary terms for pillar
        glossary_terms_for_pillar = []
        for item in all_content:
            if (item.content_type == "knowledge"
                    and item.knowledge_category == "reference"
                    and item.pillar == pillar):
                glossary_terms_for_pillar.append({
                    "slug": item.slug,
                    "label": (item.title or "").replace(" Glossary", ""),
                    "description": (item.description or "")[:80],
                })
        glossary_terms_for_pillar.sort(key=lambda x: x["label"])

        # Latest learn modules for pillar
        pillar_learn = [item for item in learn_items if item.pillar == pillar]
        latest_learn_for_pillar = sorted(
            pillar_learn,
            key=lambda x: x.created_at or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True,
        )[:6]
        latest_learn_for_pillar = [
            {"slug": x.slug, "title": x.title, "description": (x.description or "")[:100], "difficulty": getattr(x, "difficulty", "")}
            for x in latest_learn_for_pillar
        ]

        # Concept cloud from ontology
        concept_cloud_for_pillar = []
        if ontology and ontology.concept_count() > 0:
            all_concepts = ontology.concepts_by_pillar()
            pillar_concepts = all_concepts.get(pillar, [])
            concept_cloud_for_pillar = [
                {"label": c.label, "count": len(ontology.related_concepts(c.id))}
                for c in pillar_concepts[:15]
            ]

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
            page_description=pconf.get("description", ""),
            glossary_terms=glossary_terms_for_pillar,
            latest_learn=latest_learn_for_pillar,
            concept_cloud=concept_cloud_for_pillar,
            thumbnail_base=f"{SITE_URL}/static/images",
            thumbnail_key=thumbnail_key,
            card_images=card_images,
            card_topic_icons=card_topic_icons,
            pillar_posts_data=pillar_posts_data,
            **ctx_base,
        )
        (out_dir / "index.html").write_text(html, encoding="utf-8")
        print(f"  pillar: {pillar_url}/index.html")

        # Per-pillar-type index pages (research, learn, knowledge)
        for _ptype, _ptype_items in [("research", [p for p in research_items if p.pillar == pillar]),
                                       ("learn", [p for p in learn_items if p.pillar == pillar]),
                                       ("knowledge", [p for p in knowledge_items if p.pillar == pillar])]:
            if not _ptype_items:
                continue
            _ptype_html = render_template(
                "category_index.j2",
                content=_dummy(
                    f"{pconf['label']} {_ptype.title()} — AcaciaFund",
                    "index",
                    description=f"{_ptype.title()} articles in {pconf['label']}.",
                ),
                category=_ptype,
                items=_ptype_items,
                grouped={},
                page_title=f"{pconf['label']} {_ptype.title()}",
                is_index=False,
                page_path=f"{pillar_url}/{_ptype}/",
                **ctx_base,
            )
            _ptype_dir = out_dir / _ptype
            _ptype_dir.mkdir(parents=True, exist_ok=True)
            (_ptype_dir / "index.html").write_text(_ptype_html, encoding="utf-8")
            print(f"  pillar-{_ptype}: {pillar_url}/{_ptype}/index.html")

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
        page_path=f"{pillar_to_url('aml')}/signals/",
        page_title="Compliance Signals Dashboard",
        thumbnail_base=f"{SITE_URL}/static/images",
        thumbnail_key=thumbnail_key,
        **ctx_base,
    )
    sig_dir = OUTPUT_DIR / pillar_to_url("aml") / "signals"
    sig_dir.mkdir(parents=True, exist_ok=True)
    (sig_dir / "index.html").write_text(aml_signals_html, encoding="utf-8")
    print(f"  signals: {pillar_to_url('aml')}/signals/index.html")

    # --- MARKETS SIGNALS DASHBOARD ---
    stock_research = [p for p in research_items if p.pillar == "stock"]
    stock_learn = [item for item in learn_items if item.pillar == "stock"]
    tag_cloud = {}
    entity_cloud = {}
    source_totals = {}
    cross_pillar_links = {}
    timeline = {}
    for a in stock_research:
        for t in a.tags or []:
            tag_cloud[t] = tag_cloud.get(t, 0) + 1
        signals = a.signals or {}
        for e in signals.get("top_entities", []) or []:
            entity_cloud[e] = entity_cloud.get(e, 0) + 1
        sb = a.source_breakdown or {}
        for k, v in sb.items():
            source_totals[k] = source_totals.get(k, 0) + v
        if a.date_str:
            month = a.date_str[:7]
            timeline[month] = timeline.get(month, 0) + 1
    tag_sorted = sorted(tag_cloud.items(), key=lambda x: -x[1])
    entity_sorted = sorted(entity_cloud.items(), key=lambda x: -x[1])
    source_sorted = sorted(source_totals.items(), key=lambda x: -x[1])
    source_max = max((c for _, c in source_sorted), default=1)
    tl_sorted = sorted(timeline.items())
    tl_max = max(timeline.values()) if timeline else 1
    avg_sqi_stock = sum((a.signals or {}).get("avg_sqi", 0) or 0 for a in stock_research) / max(
        len(stock_research), 1
    )
    unique_tags = set()
    for a in stock_research:
        for t in a.tags or []:
            unique_tags.add(t)
    unique_entities = set()
    for a in stock_research:
        for e in (a.signals or {}).get("top_entities", []) or []:
            unique_entities.add(e)

    stock_signals_html = render_template(
        "aml_signals.j2",
        content=_dummy(
            "Markets & Industry Signals Dashboard",
            "index",
            description="Aggregated market signals, industry trends, and coverage metrics across Markets articles.",
        ),
        stock_count=len(stock_research),
        avg_sqi=avg_sqi_stock,
        unique_tags_count=len(unique_tags),
        unique_entities_count=len(unique_entities),
        tag_cloud=tag_sorted,
        entity_cloud=entity_sorted,
        source_totals=source_sorted,
        source_max=source_max,
        cross_pillar_summary=[],
        timeline=tl_sorted,
        timeline_max=tl_max,
        recent_articles=sorted(stock_research, key=lambda x: x.date_str or "", reverse=True)[:10],
        learn_path=stock_learn,
        is_index=False,
        page_path="stock/signals/",
        page_title="Markets & Industry Signals Dashboard",
        thumbnail_base=f"{SITE_URL}/static/images",
        thumbnail_key=thumbnail_key,
        **ctx_base,
    )
    sig_dir = OUTPUT_DIR / "markets" / "signals"
    sig_dir.mkdir(parents=True, exist_ok=True)
    (sig_dir / "index.html").write_text(stock_signals_html, encoding="utf-8")
    print("  signals: markets/signals/index.html")

    # --- DATA ENGINEERING SIGNALS DASHBOARD ---
    de_research = [p for p in research_items if p.pillar == "data-engineering"]
    de_learn = [item for item in learn_items if item.pillar == "data-engineering"]
    tag_cloud = {}
    entity_cloud = {}
    source_totals = {}
    cross_pillar_links = {}
    timeline = {}
    for a in de_research:
        for t in a.tags or []:
            tag_cloud[t] = tag_cloud.get(t, 0) + 1
        signals = a.signals or {}
        for e in signals.get("top_entities", []) or []:
            entity_cloud[e] = entity_cloud.get(e, 0) + 1
        sb = a.source_breakdown or {}
        for k, v in sb.items():
            source_totals[k] = source_totals.get(k, 0) + v
        if a.date_str:
            month = a.date_str[:7]
            timeline[month] = timeline.get(month, 0) + 1
    tag_sorted = sorted(tag_cloud.items(), key=lambda x: -x[1])
    entity_sorted = sorted(entity_cloud.items(), key=lambda x: -x[1])
    source_sorted = sorted(source_totals.items(), key=lambda x: -x[1])
    source_max = max((c for _, c in source_sorted), default=1)
    tl_sorted = sorted(timeline.items())
    tl_max = max(timeline.values()) if timeline else 1
    avg_sqi_de = sum((a.signals or {}).get("avg_sqi", 0) or 0 for a in de_research) / max(
        len(de_research), 1
    )
    unique_tags = set()
    for a in de_research:
        for t in a.tags or []:
            unique_tags.add(t)
    unique_entities = set()
    for a in de_research:
        for e in (a.signals or {}).get("top_entities", []) or []:
            unique_entities.add(e)

    de_signals_html = render_template(
        "aml_signals.j2",
        content=_dummy(
            "Data Engineering Signals Dashboard",
            "index",
            description="Aggregated data engineering signals, pipeline trends, and coverage metrics across Data Engineering articles.",
        ),
        de_count=len(de_research),
        avg_sqi=avg_sqi_de,
        unique_tags_count=len(unique_tags),
        unique_entities_count=len(unique_entities),
        tag_cloud=tag_sorted,
        entity_cloud=entity_sorted,
        source_totals=source_sorted,
        source_max=source_max,
        cross_pillar_summary=[],
        timeline=tl_sorted,
        timeline_max=tl_max,
        recent_articles=sorted(de_research, key=lambda x: x.date_str or "", reverse=True)[:10],
        learn_path=de_learn,
        is_index=False,
        page_path="data-engineering/signals/",
        page_title="Data Engineering Signals Dashboard",
        thumbnail_base=f"{SITE_URL}/static/images",
        thumbnail_key=thumbnail_key,
        **ctx_base,
    )
    sig_dir = OUTPUT_DIR / "data" / "signals"
    sig_dir.mkdir(parents=True, exist_ok=True)
    (sig_dir / "index.html").write_text(de_signals_html, encoding="utf-8")
    print("  signals: data/signals/index.html")

    # --- HOMEPAGE (filter future posts from featured/recent) ---
    published_research = [p for p in sorted_research if not is_future_post(p)]
    # Freshness cutoff: exclude articles older than 90 days from featured + recent
    ninety_days_ago = now - timedelta(days=90)
    fresh_posts = [
        p for p in published_research
        if not _get_created(p) or _get_created(p) >= ninety_days_ago
    ]
    featured = fresh_posts[:3] if len(fresh_posts) >= 3 else published_research[:3]
    # Hero: highest-SQI article from last 7 days
    seven_days_ago = now - timedelta(days=7)
    recent_articles = [
        p for p in published_research if _get_created(p) and _get_created(p) >= seven_days_ago
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

    # --- /start-here/ onboarding page ---
    start_here_html = render_template(
        "start_here.j2",
        content=_dummy(
            "Start Here — AcaciaFund",
            "index",
            description="Learn how to use AcaciaFund's Feynman Technique-based learning platform. Start with simple explanations, build understanding through analogies, and test yourself.",
        ),
        is_index=False,
        page_path="start-here/",
        page_title="Start Here",
        **ctx_base,
    )
    start_here_dir = OUTPUT_DIR / "start-here"
    start_here_dir.mkdir(parents=True, exist_ok=True)
    (start_here_dir / "index.html").write_text(start_here_html, encoding="utf-8")
    print("  start-here: start-here/index.html")

    # --- date-based archive pages ---
    _archive_items: dict[str, list] = defaultdict(list)
    for _ai in all_content:
        _ad = _get_created(_ai)
        if _ad:
            _key = _ad.strftime("%Y/%m")
            _archive_items[_key].append(_ai)
    _archive_count = 0
    for _arch_key in sorted(_archive_items, reverse=True):
        _arch_items = _archive_items[_arch_key]
        _arch_parts = _arch_key.split("/")
        _arch_year, _arch_month = _arch_parts[0], _arch_parts[1]
        _arch_label = f"{_arch_year}-{_arch_month}"
        _arch_pillar_groups: dict[str, list] = defaultdict(list)
        for _arch_item in _arch_items:
            _arch_pillar_groups[_arch_item.pillar or "unknown"].append(_arch_item)
        _arch_html = render_template(
            "category_index.j2",
            content=_dummy(
                f"Archives: {_arch_label} — AcaciaFund",
                "index",
                description=f"Articles from {_arch_label}.",
            ),
            category="archives",
            items=_arch_items,
            grouped=dict(_arch_pillar_groups),
            page_title=f"Archives: {_arch_label}",
            is_index=False,
            page_path=f"archives/{_arch_year}/{_arch_month}/",
            **ctx_base,
        )
        _arch_dir = OUTPUT_DIR / "archives" / _arch_year / _arch_month
        _arch_dir.mkdir(parents=True, exist_ok=True)
        (_arch_dir / "index.html").write_text(_arch_html, encoding="utf-8")
        _archive_count += 1
    if _archive_count > 0:
        # Master archives index
        _arch_months = sorted(set(_archive_items.keys()), reverse=True)
        _arch_index_html = render_template(
            "category_index.j2",
            content=_dummy(
                "Archives — AcaciaFund",
                "index",
                description="Browse articles by month.",
            ),
            category="archives",
            items=[],
            grouped={},
            page_title="Archives",
            is_index=False,
            page_path="archives/",
            _archive_months=[{"key": m, "label": f"{m.split('/')[0]}-{m.split('/')[1]}"} for m in _arch_months],
            **ctx_base,
        )
        archives_root = OUTPUT_DIR / "archives"
        archives_root.mkdir(parents=True, exist_ok=True)
        (archives_root / "index.html").write_text(_arch_index_html, encoding="utf-8")

        # Per-pillar archive pages
        for _pillar_key, _pillar_url in PILLAR_URL_MAP.items():
            _pillar_arch_items: dict[str, list] = defaultdict(list)
            for _ai in all_content:
                if getattr(_ai, "pillar", None) != _pillar_key:
                    continue
                _ad = _get_created(_ai)
                if _ad:
                    _pillar_arch_items[_ad.strftime("%Y/%m")].append(_ai)
            for _arch_key in sorted(_pillar_arch_items, reverse=True):
                _arch_items = _pillar_arch_items[_arch_key]
                _arch_parts = _arch_key.split("/")
                _arch_year, _arch_month = _arch_parts[0], _arch_parts[1]
                _arch_label = f"{_arch_year}-{_arch_month}"
                _arch_html = render_template(
                    "category_index.j2",
                    content=_dummy(
                        f"Archives: {_arch_label} — {_pillar_key} — AcaciaFund",
                        "index",
                        description=f"Articles from {_arch_label} in {_pillar_key}.",
                    ),
                    category="archives",
                    items=_arch_items,
                    grouped={_pillar_key: _arch_items},
                    page_title=f"Archives: {_arch_label} ({_pillar_key})",
                    is_index=False,
                    page_path=f"{_pillar_url}/archives/{_arch_year}/{_arch_month}/",
                    **ctx_base,
                )
                _arch_dir = OUTPUT_DIR / _pillar_url / "archives" / _arch_year / _arch_month
                _arch_dir.mkdir(parents=True, exist_ok=True)
                (_arch_dir / "index.html").write_text(_arch_html, encoding="utf-8")
                _archive_count += 1
        print(f"  archives: {_archive_count} monthly pages + index")
    else:
        print("  archives: none (no dated items)")

    # --- per-pillar difficulty archive pages ---
    _extra_count = 0
    for _pillar_key, _pillar_url in PILLAR_URL_MAP.items():
        for _diff in ("beginner", "intermediate", "advanced"):
            _diff_items = [c for c in all_content if getattr(c, "pillar", None) == _pillar_key
                           and (getattr(c, "difficulty", None) or "").lower() == _diff]
            if not _diff_items:
                continue
            _diff_dir = OUTPUT_DIR / _pillar_url / "difficulty" / _diff
            _diff_dir.mkdir(parents=True, exist_ok=True)
            _diff_html = render_template(
                "category_index.j2",
                content=_dummy(
                    f"{_diff.title()} Difficulty — {_pillar_key}",
                    "index",
                    description=f"{_diff.title()} difficulty content in {_pillar_key}.",
                ),
                category=_diff,
                items=_diff_items,
                page_title=f"{_diff.title()} ({_pillar_key})",
                is_index=False,
                page_path=f"{_pillar_url}/difficulty/{_diff}/",
                **ctx_base,
            )
            (_diff_dir / "index.html").write_text(_diff_html, encoding="utf-8")
            _extra_count += 1

    # --- per-pillar bloom-level archive pages ---
    _bloom_levels = {"remember": 1, "understand": 2, "apply": 3, "analyze": 4, "evaluate": 5, "create": 6}
    for _pillar_key, _pillar_url in PILLAR_URL_MAP.items():
        for _bloom_name, _bloom_val in _bloom_levels.items():
            _bloom_items = [
                c for c in all_content
                if getattr(c, "pillar", None) == _pillar_key
                and getattr(c, "highest_bloom", 0) >= _bloom_val
            ]
            if not _bloom_items:
                continue
            _bloom_dir = OUTPUT_DIR / _pillar_url / "bloom" / _bloom_name
            _bloom_dir.mkdir(parents=True, exist_ok=True)
            _bloom_html = render_template(
                "category_index.j2",
                content=_dummy(
                    f"Bloom: {_bloom_name.title()} — {_pillar_key}",
                    "index",
                    description=f"Content at {_bloom_name.title()} Bloom level in {_pillar_key}.",
                ),
                category=_bloom_name,
                items=_bloom_items,
                page_title=f"Bloom: {_bloom_name.title()} ({_pillar_key})",
                is_index=False,
                page_path=f"{_pillar_url}/bloom/{_bloom_name}/",
                **ctx_base,
            )
            (_bloom_dir / "index.html").write_text(_bloom_html, encoding="utf-8")
            _extra_count += 1

    if _extra_count:
        print(f"  extra indexes: {_extra_count} pages")

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
        f'<meta http-equiv="refresh" content="0;url={SITE_URL}/data/research/">'
        f'<link rel="canonical" href="{SITE_URL}/data/research/">'
        f'</head><body><p><a href="{SITE_URL}/data/research/">Research — AcaciaFund</a></p></body></html>',
        encoding="utf-8",
    )
    print("  redirect: /science/ → /data/research/")

    # --- /stock/ redirect to /markets/ ---
    stock_dir = OUTPUT_DIR / "stock"
    stock_dir.mkdir(parents=True, exist_ok=True)
    (stock_dir / "index.html").write_text(
        f'<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
        f"<title>Markets — AcaciaFund</title>"
        f'<meta http-equiv="refresh" content="0;url={SITE_URL}/markets/">'
        f'<link rel="canonical" href="{SITE_URL}/markets/">'
        f'</head><body><p><a href="{SITE_URL}/markets/">Markets — AcaciaFund</a></p></body></html>',
        encoding="utf-8",
    )
    print("  redirect: /stock/ → /markets/")

    # --- /aml/ redirect to /compliance/ ---
    aml_dir = OUTPUT_DIR / "aml"
    aml_dir.mkdir(parents=True, exist_ok=True)
    (aml_dir / "index.html").write_text(
        f'<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
        f"<title>Compliance — AcaciaFund</title>"
        f'<meta http-equiv="refresh" content="0;url={SITE_URL}/compliance/">'
        f'<link rel="canonical" href="{SITE_URL}/compliance/">'
        f'</head><body><p><a href="{SITE_URL}/compliance/">Compliance — AcaciaFund</a></p></body></html>',
        encoding="utf-8",
    )
    print("  redirect: /aml/ → /compliance/")

    # --- Knowledge Graph Page (/graph/) ---
    cytograph_src = PROJECT_ROOT / "data" / "cytograph.json"
    if cytograph_src.exists():
        cytograph_dst = OUTPUT_DIR / "graph-data.json"
        cytograph_data = json.loads(cytograph_src.read_text(encoding="utf-8"))
        try:
            graph_data = cytograph_data
            node_count = len(graph_data.get("nodes", []))
            edge_count = len(graph_data.get("edges", []))
        except (json.JSONDecodeError, TypeError, KeyError):
            node_count = 0
            edge_count = 0
    else:
        graph_data = {"nodes": [], "edges": []}
        node_count = 0
        edge_count = 0

    # Merge ontology concepts and relations into the cytograph
    ontology_path = PROJECT_ROOT / "data" / "ontology.json"
    if ontology_path.exists():
        try:
            from core.ontology import OntologyManager
            ontology = OntologyManager.load(ontology_path)
            if ontology.concept_count() > 0:
                graph_data = ontology.merge_into_cytograph(graph_data)
                node_count = len(graph_data.get("nodes", []))
                edge_count = len(graph_data.get("edges", []))
                print(f"  ontology: merged {ontology.concept_count()} concepts, {ontology.relation_count()} relations into graph")
        except Exception as e:
            print(f"  ontology: merge skipped ({e})")

    # Add doc↔concept edges (content items linked to ontology concepts)
    if ontology and ontology.concept_count() > 0:
        existing_edge_ids = {e["data"]["id"] for e in graph_data.get("edges", [])}
        doc_concept_edges = 0
        for _ci in all_content:
            if not _ci.tags:
                continue
            _ctext = f"{_ci.title or ''} {' '.join(_ci.tags or [])} {(_ci.body_html or '')[:500]}"
            import re as _re
            _ctext = _re.sub(r"<[^>]+>", " ", _ctext)
            try:
                _matches = extract_concepts_from_text(_ctext, ontology)
                _doc_id = f"doc:{_ci.slug}"
                for _concept, _score in _matches:
                    if _score >= 0.35:
                        _edge_id = f"doc-concept:{_ci.slug}:{_concept.id}"
                        if _edge_id not in existing_edge_ids:
                            _doc_pillar = _ci.pillar if hasattr(_ci, 'pillar') else ""
                            _concept_pillar = _concept.pillar if hasattr(_concept, 'pillar') else ""
                            graph_data.setdefault("edges", []).append({
                                "data": {
                                    "id": _edge_id,
                                    "source": _doc_id,
                                    "target": f"ont:{_concept.id}",
                                    "type": "document-concept",
                                    "strength": round(_score, 2),
                                    "sourcePillar": _doc_pillar,
                                    "targetPillar": _concept_pillar,
                                }
                            })
                            existing_edge_ids.add(_edge_id)
                            doc_concept_edges += 1
            except Exception:
                pass
        if doc_concept_edges > 0:
            edge_count = len(graph_data.get("edges", []))
            print(f"  doc-concept: {doc_concept_edges} edges added")

    # Write merged graph data
    cytograph_dst = OUTPUT_DIR / "graph-data.json"
    cytograph_dst.write_text(json.dumps(graph_data, indent=2, default=str), encoding="utf-8")

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

    # --- Review pages (dashboard + queue) ---
    _review_cards = []
    for _ri_raw in registry.content:
        _ri_dict = _ri_raw if isinstance(_ri_raw, dict) else (_ri_raw.model_dump() if hasattr(_ri_raw, 'model_dump') else {})
        _ri_fcs = _ri_dict.get("flashcards", [])
        if not _ri_fcs:
            continue
        _rpillar = _ri_dict.get("pillar", "aml")
        _slug = _ri_dict.get("slug", "")
        for _fi, _fc in enumerate(_ri_fcs):
            _card_id = f"{_slug}#{_fi}"
            _fc_term = _fc.get("term", "") or _fc.get("front", "")
            _fc_def = _fc.get("definition", "") or _fc.get("back", "")
            _review_cards.append({
                "id": _card_id,
                "term": _fc_term,
                "definition": _fc_def,
                "pillar": _rpillar,
                "slug": _slug,
            })
    _review_cards_json = json.dumps(_review_cards, ensure_ascii=False)

    review_dir = OUTPUT_DIR / "review"
    review_dir.mkdir(parents=True, exist_ok=True)
    review_html = render_template(
        "review.j2",
        content=_dummy("Review Dashboard — AcaciaFund", "index", description="Spaced repetition review dashboard for AcaciaFund learn modules."),
        flashcard_cards=_review_cards_json,
        page_path="review/",
        page_title="Review Dashboard",
        **ctx_base,
    )
    (review_dir / "index.html").write_text(review_html, encoding="utf-8")
    print(f"  review: review/index.html ({len(_review_cards)} cards)")

    queue_dir = review_dir / "queue"
    queue_dir.mkdir(parents=True, exist_ok=True)
    queue_html = render_template(
        "review_queue.j2",
        content=_dummy("Review Queue — AcaciaFund", "index", description="Review queue for spaced repetition flashcards."),
        flashcard_cards=_review_cards_json,
        page_path="review/queue/",
        page_title="Review Queue",
        **ctx_base,
    )
    (queue_dir / "index.html").write_text(queue_html, encoding="utf-8")
    print("  review: review/queue/index.html")

    # --- Concept review data for retention engine ---
    if ontology and ontology.concept_count() > 0:
        try:
            from core.retention_engine import generate_concept_review_json, save_concept_review_json
            _concept_review_items = generate_concept_review_json(ontology)
            _review_data_path = STATIC_DST_DIR / "review_concepts.json"
            save_concept_review_json(_concept_review_items, _review_data_path)
            _review_data_size = _review_data_path.stat().st_size if _review_data_path.exists() else 0
            print(f"  retention: static/review_concepts.json ({len(_concept_review_items)} concepts, {_review_data_size:,} bytes)")
        except ImportError:
            print("  retention: core.retention_engine not available — skipping")
        except Exception as _e_ret:
            print(f"  retention: error generating concept review data — {_e_ret}")

    # --- Concept detail pages ---
    if ontology and ontology.concept_count() > 0:
        # Build concept → content mapping by re-extracting from all items
        concept_content_map = {}
        for _ci in all_content:
            if not _ci.tags:
                continue
            _ctext = f"{_ci.title or ''} {' '.join(_ci.tags or [])} {(_ci.body_html or '')[:500]}"
            import re as _re
            _ctext = _re.sub(r"<[^>]+>", " ", _ctext)
            try:
                _matches = extract_concepts_from_text(_ctext, ontology)
                for _concept, _score in _matches:
                    if _score >= 0.35:
                        if _concept.id not in concept_content_map:
                            concept_content_map[_concept.id] = []
                        concept_content_map[_concept.id].append({
                            "slug": slug_to_fspath(_ci.slug),
                            "title": _ci.title,
                            "description": (_ci.description or "")[:120],
                            "pillar": _ci.pillar or "",
                            "content_type": _ci.content_type,
                            "url": f"/{slug_to_fspath(_ci.slug)}/",
                            "score": round(_score, 2),
                        })
            except Exception:
                pass

        # Compute learning paths for concept linking
        _lp_journeys = build_all_learning_paths(ontology, max_depth=3)
        if _lp_journeys:
            _lp_journeys = enrich_journeys_with_content(_lp_journeys, concept_content_map)
        else:
            _lp_journeys = {}

        # Build reverse index: concept_id → list of paths it appears in
        _concept_to_paths: dict[str, list[dict]] = {}
        for _jid, _jny in _lp_journeys.items():
            for _path in _jny.paths:
                _concept_ids = [c["id"] for c in _path.concepts]
                for _pos, _cid in enumerate(_concept_ids):
                    _entry = {
                        "journey_id": _jid,
                        "journey_label": _jny.start_label,
                        "journey_pillar": _jny.start_pillar,
                        "path_depth": _path.total_depth,
                        "position": _pos,
                        "total_in_path": len(_concept_ids),
                        "prev_id": _concept_ids[_pos - 1] if _pos > 0 else None,
                        "prev_label": _path.concepts[_pos - 1]["label"] if _pos > 0 else None,
                        "next_id": _concept_ids[_pos + 1] if _pos < len(_concept_ids) - 1 else None,
                        "next_label": _path.concepts[_pos + 1]["label"] if _pos < len(_concept_ids) - 1 else None,
                    }
                    _concept_to_paths.setdefault(_cid, []).append(_entry)

        concept_dir = OUTPUT_DIR / "concepts"
        concept_dir.mkdir(parents=True, exist_ok=True)
        _concept_count = 0
        all_concepts = ontology.concepts_by_pillar()
        for _pillar_key, _pillar_concepts in all_concepts.items():
            for _concept in _pillar_concepts:
                # Related concepts with relation type
                _related_concepts = []
                for _rel in ontology.relations_for(_concept.id):
                    _other_id = _rel.target_id if _rel.source_id == _concept.id else _rel.source_id
                    _other = ontology.get_concept(_other_id)
                    if _other:
                        _related_concepts.append({
                            "id": _other.id,
                            "label": _other.label,
                            "relation": _rel.relation_type,
                        })

                _related_items = concept_content_map.get(_concept.id, [])
                _related_items.sort(key=lambda x: x["score"], reverse=True)
                _related_items = _related_items[:12]

                # Build prerequisite/dependent lists with direction
                _prereqs = []
                _deps = []
                for _rel in ontology.relations_for(_concept.id):
                    if _rel.relation_type == "requires":
                        if _rel.source_id == _concept.id:
                            # This concept requires target → target is a prerequisite
                            _other = ontology.get_concept(_rel.target_id)
                            if _other:
                                _prereqs.append({"id": _other.id, "label": _other.label, "pillar": _other.pillar})
                        else:
                            # Source requires this concept → source is a dependent
                            _other = ontology.get_concept(_rel.source_id)
                            if _other:
                                _deps.append({"id": _other.id, "label": _other.label, "pillar": _other.pillar})

                _lp_ctx = _concept_to_paths.get(_concept.id, [])
                _has_lp = _concept.id in _lp_journeys if _lp_journeys else False
                _has_lp_ctx = len(_lp_ctx) > 0
                concept_html = render_template(
                    "concept_detail.j2",
                    content=_dummy(
                        f"{_concept.label} — AcaciaFund Concepts",
                        "index",
                        description=_concept.description or f"Concept: {_concept.label} in {_pillar_key} pillar.",
                    ),
                    concept={
                        "id": _concept.id,
                        "label": _concept.label,
                        "description": _concept.description or "",
                        "pillar": _pillar_key,
                        "category": _concept.category or "",
                        "aliases": _concept.aliases or [],
                        "philosophical_lineage": getattr(_concept, "philosophical_lineage", None) or [],
                        "epistemic_status": getattr(_concept, "epistemic_status", "") or "",
                        "normative_basis": getattr(_concept, "normative_basis", "") or "",
                        "ontological_commitment": getattr(_concept, "ontological_commitment", "") or "",
                        "temporal_ontology": getattr(_concept, "temporal_ontology", "") or "",
                        "uncertainty_class": getattr(_concept, "uncertainty_class", "") or "",
                        "governance_model": getattr(_concept, "governance_model", "") or "",
                        "philosophical_sources": getattr(_concept, "philosophical_sources", None) or [],
                        "cross_pillar_analogs": getattr(_concept, "cross_pillar_analogs", None) or [],
                        # Feynman fields
                        "eli5_explanation": getattr(_concept, "eli5_explanation", None),
                        "analogy": getattr(_concept, "analogy", None),
                        "concrete_example": getattr(_concept, "concrete_example", None),
                        "feynman_diagram": getattr(_concept, "feynman_diagram", None),
                        "gap_questions": getattr(_concept, "gap_questions", []),
                        "teach_back_prompt": getattr(_concept, "teach_back_prompt", None),
                        "build_exercise": getattr(_concept, "build_exercise", None),
                        "feynman_difficulty": getattr(_concept, "feynman_difficulty", 1),
                        "explanation_quality": getattr(_concept, "explanation_quality", 0.0),
                        "sqi": getattr(_concept, "explanation_quality", 0.0),
                    },
                    has_learning_path=_has_lp,
                    has_lp_ctx=_has_lp_ctx,
                    learning_paths=_lp_ctx,
                    related_items=_related_items,
                    related_concepts=_related_concepts,
                    prerequisites=_prereqs,
                    dependents=_deps,
                    page_path=f"concepts/{_concept.id}/",
                    **ctx_base,
                )
                _cd = concept_dir / _concept.id
                _cd.mkdir(parents=True, exist_ok=True)
                (_cd / "index.html").write_text(concept_html, encoding="utf-8")
                _concept_count += 1
        print(f"  concepts: {_concept_count} concept pages")

        # --- Render learning path pages ---
        if _lp_journeys:
            _lp_count = 0
            for _lp_id, _lp_journey in _lp_journeys.items():
                _lp_context = generate_learning_path_context(_lp_journey, PILLAR_CONFIG)
                _lp_pillar_url = pillar_to_url(_lp_journey.start_pillar)
                _lp_html = render_template(
                    "learning_path.j2",
                    content=_dummy(
                        f"{_lp_journey.start_label} — Learning Path — AcaciaFund",
                        "index",
                        description=f"Structured learning path for {_lp_journey.start_label}.",
                    ),
                    pillar_url=_lp_pillar_url,
                    **_lp_context,
                    **ctx_base,
                )
                _lp_dir = OUTPUT_DIR / "learning-paths" / _lp_id
                _lp_dir.mkdir(parents=True, exist_ok=True)
                (_lp_dir / "index.html").write_text(_lp_html, encoding="utf-8")
                _lp_count += 1
            print(f"  learning paths: {_lp_count} pages")

            # --- Learning paths index page ---
            try:
                _lp_index_entries = []
                for _jid, _jny in sorted(_lp_journeys.items()):
                    _pc = PILLAR_CONFIG.get(_jny.start_pillar, {})
                    _max_depth = max((p.total_depth for p in _jny.paths), default=1)
                    _lp_index_entries.append({
                        "id": _jid,
                        "label": _jny.start_label,
                        "pillar": _jny.start_pillar,
                        "pillar_label": _pc.get("label", _jny.start_pillar),
                        "pillar_color": _pc.get("color", "#6366f1"),
                        "pillar_url": _pc.get("url", _jny.start_pillar),
                        "path_count": len(_jny.paths),
                        "node_count": len(_jny.nodes),
                        "max_depth": _max_depth,
                        "pillar_span": max((p.pillar_span for p in _jny.paths), default=1),
                    })
                _lp_index_html = render_template(
                    "learning_paths_index.j2",
                    content=_dummy(
                        "Learning Paths — AcaciaFund",
                        "index",
                        description=f"Browse {len(_lp_index_entries)} structured learning paths across all pillars.",
                    ),
                    paths=_lp_index_entries,
                    total_paths=len(_lp_index_entries),
                    page_path="learning-paths/",
                    **ctx_base,
                )
                _lp_index_dir = OUTPUT_DIR / "learning-paths"
                _lp_index_dir.mkdir(parents=True, exist_ok=True)
                (_lp_index_dir / "index.html").write_text(_lp_index_html, encoding="utf-8")
            except Exception as _lpe:
                print(f"  learning-paths index: error — {_lpe}")

        # --- Feynman learning path pages ---
        _feynman_paths = compute_feynman_learning_paths(ontology)
        # Build concept map for template
        _feynman_concept_map = {}
        for _c in ontology._concepts.values():
            _feynman_concept_map[_c.id] = {
                "id": _c.id,
                "label": _c.label,
                "pillar": _c.pillar,
                "description": _c.description,
                "difficulty": getattr(_c, "feynman_difficulty", 1),
                "feynman_difficulty": getattr(_c, "feynman_difficulty", 1),
                "eli5_explanation": getattr(_c, "eli5_explanation", None),
                "analogy": getattr(_c, "analogy", None),
                "concrete_example": getattr(_c, "concrete_example", None),
                "gap_questions": getattr(_c, "gap_questions", []),
                "teach_back_prompt": getattr(_c, "teach_back_prompt", None),
                "build_exercise": getattr(_c, "build_exercise", None),
            }
        _feynman_count = 0
        for _fp in _feynman_paths:
            _fp_pillar_url = pillar_to_url(_fp.pillar)
            _fp_pc = PILLAR_CONFIG.get(_fp.pillar, {})
            _fp_html = render_template(
                "feynman_learning_path.j2",
                content=_dummy(
                    f"Feynman Learning Path — {_fp_pc.get('label', _fp.pillar)} — AcaciaFund",
                    "index",
                    description=(
                        f"Feynman-scaffolded learning path for "
                        f"{_fp_pc.get('label', _fp.pillar)} with "
                        f"{_fp.total_concepts} concepts across "
                        f"{len(_fp.stages)} stages."
                    ),
                ),
                stages=_fp.stages,
                total_concepts=_fp.total_concepts,
                difficulty_tiers=_fp.difficulty_tiers,
                concept_map=_feynman_concept_map,
                pillar_label=_fp_pc.get("label", _fp.pillar),
                pillar_color=_fp_pc.get("color", "#6366f1"),
                pillar_url=_fp_pillar_url,
                page_path=f"{_fp_pillar_url}/learn/feynman-path/",
                **ctx_base,
            )
            _fp_dir = OUTPUT_DIR / _fp_pillar_url / "learn" / "feynman-path"
            _fp_dir.mkdir(parents=True, exist_ok=True)
            (_fp_dir / "index.html").write_text(_fp_html, encoding="utf-8")
            _feynman_count += 1
        print(f"  feynman paths: {_feynman_count} pages")

        # --- Cross-pillar Feynman synthesis pages ---
        _cp_feynman_paths = compute_cross_pillar_feynman_paths(ontology)
        _cp_feynman_count = 0
        for _cp_fp in _cp_feynman_paths:
            _cp_pillar_url = pillar_to_url(_cp_fp.pillar)
            _cp_pc = PILLAR_CONFIG.get(_cp_fp.pillar, {})
            _cp_html = render_template(
                "feynman_cross_pillar_path.j2",
                content=_dummy(
                    f"Cross-Pillar Feynman Synthesis — {_cp_pc.get('label', _cp_fp.pillar)} — AcaciaFund",
                    "index",
                    description=(
                        f"Feynman cross-pillar analog synthesis for "
                        f"{_cp_pc.get('label', _cp_fp.pillar)} with "
                        f"{_cp_fp.total_triples} cross-domain connections."
                    ),
                ),
                triples=_cp_fp.triples,
                total_triples=_cp_fp.total_triples,
                connected_pillars=_cp_fp.connected_pillars,
                concept_map=_feynman_concept_map,
                pillar_label=_cp_pc.get("label", _cp_fp.pillar),
                pillar_color=_cp_pc.get("color", "#6366f1"),
                pillar_url=_cp_pillar_url,
                page_path=f"{_cp_pillar_url}/learn/feynman-synthesis/",
                **ctx_base,
            )
            _cp_dir = OUTPUT_DIR / _cp_pillar_url / "learn" / "feynman-synthesis"
            _cp_dir.mkdir(parents=True, exist_ok=True)
            (_cp_dir / "index.html").write_text(_cp_html, encoding="utf-8")
            _cp_feynman_count += 1
        print(f"  cross-pillar feynman paths: {_cp_feynman_count} pages")

        # --- Cross-pillar synthesis pages ---
        _synth = generate_cross_pillar_synthesis(all_content, concept_content_map, PILLAR_CONFIG, ontology)
        _synth_count = 0
        for _synth_pillar in ["aml", "stock", "data-engineering"]:
            _synth_pillar_url = pillar_to_url(_synth_pillar)
            _synth_pc = PILLAR_CONFIG.get(_synth_pillar, {})
            _synth_html = render_template(
                "pillar_synthesis.j2",
                content=_dummy(
                    f"{_synth_pc.get('label', _synth_pillar)} — Cross-Pillar Synthesis — AcaciaFund",
                    "index",
                    description=f"Cross-pillar synthesis view for {_synth_pc.get('label', _synth_pillar)}.",
                ),
                pillar=_synth_pillar,
                pillar_url=_synth_pillar_url,
                pillar_label=_synth_pc.get("label", _synth_pillar),
                pillar_color=_synth_pc.get("color", "#6366f1"),
                synthesis=_synth,
                **ctx_base,
            )
            _synth_dir = OUTPUT_DIR / _synth_pillar_url / "synthesis"
            _synth_dir.mkdir(parents=True, exist_ok=True)
            (_synth_dir / "index.html").write_text(_synth_html, encoding="utf-8")
            _synth_count += 1
        print(f"  synthesis: {_synth_count} pillar pages")

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
    from datetime import timezone as _tz
    _dt_min = datetime.min.replace(tzinfo=_tz.utc)
    def _tag_sort_key(x):
        dt = x.created_at
        if dt is None:
            return _dt_min
        if dt.tzinfo is None:
            return dt.replace(tzinfo=_tz.utc)
        return dt
    for tag_posts in tag_items.values():
        tag_posts.sort(key=_tag_sort_key, reverse=True)

    # Generate tag pages using isolated function
    tag_pages_count = generate_tag_pages(
        OUTPUT_DIR, tag_items, render_template, ctx_base, _dummy,
        pillar_url_map=PILLAR_URL_MAP,
    )
    if tag_items:
        print(f"  tags: {tag_pages_count} pages")
    else:
        print("  tags: 0 pages")

    # --- per-letter tag index pages ---
    _letter_tag_items: dict[str, list] = defaultdict(list)
    for _tag_slug in sorted(tag_items.keys()):
        _first = _tag_slug.strip().lower()[0] if _tag_slug.strip() else "?"
        _letter_tag_items[_first].append((_tag_slug, len(tag_items[_tag_slug])))
    for _letter, _ltags in sorted(_letter_tag_items.items()):
        if len(_ltags) < 2:
            continue
        _letter_tag_dir = OUTPUT_DIR / "tags" / _letter
        _letter_tag_dir.mkdir(parents=True, exist_ok=True)
        _lt_html = render_template(
            "category_index.j2",
            content=_dummy(f"Tags starting with '{_letter.upper()}'", "index",
                           description=f"All tags beginning with '{_letter.upper()}'."),
            category="tags",
            items=[],
            page_title=f"Tags: {_letter.upper()}",
            letter_tags=_ltags,
            is_index=False,
            page_path=f"tags/{_letter}/",
            **ctx_base,
        )
        (_letter_tag_dir / "index.html").write_text(_lt_html, encoding="utf-8")
        _extra_count += 1

    if _extra_count:
        print(f"  letter tag indexes: {len(_letter_tag_items)} pages")

    # --- per-item source breakdown pages ---
    _item_page_count = 0
    for _c in all_content:
        _sb = getattr(_c, "source_breakdown", None)
        if not _sb:
            continue
        _pillar_key = getattr(_c, "pillar", "")
        _pillar_url = PILLAR_URL_MAP.get(_pillar_key, _pillar_key)
        _slug_parts = getattr(_c, "slug", "").rstrip("/").split("/")
        _last_slug = _slug_parts[-1] if _slug_parts else "unknown"
        _src_dir = OUTPUT_DIR / _pillar_url / _last_slug / "sources"
        _src_dir.mkdir(parents=True, exist_ok=True)
        _src_html = render_template(
            "category_index.j2",
            content=_dummy(f"Sources: {getattr(_c, 'title', '')}", "index",
                           description=f"Source breakdown for {getattr(_c, 'title', '')}."),
            category="sources",
            items=[_c],
            page_title=f"Sources: {getattr(_c, 'title', '')}",
            is_index=False,
            page_path=f"{_pillar_url}/{_last_slug}/sources/",
            **ctx_base,
        )
        (_src_dir / "index.html").write_text(_src_html, encoding="utf-8")
        _item_page_count += 1

    # --- per-item flashcard pages ---
    for _c in all_content:
        _fc = getattr(_c, "flashcards", None) or []
        if not _fc:
            continue
        _pillar_key = getattr(_c, "pillar", "")
        _pillar_url = PILLAR_URL_MAP.get(_pillar_key, _pillar_key)
        _slug_parts = getattr(_c, "slug", "").rstrip("/").split("/")
        _last_slug = _slug_parts[-1] if _slug_parts else "unknown"
        _fc_dir = OUTPUT_DIR / _pillar_url / _last_slug / "flashcards"
        _fc_dir.mkdir(parents=True, exist_ok=True)
        _fc_html = render_template(
            "category_index.j2",
            content=_dummy(f"Flashcards: {getattr(_c, 'title', '')}", "index",
                           description=f"Flashcards for {getattr(_c, 'title', '')}."),
            category="flashcards",
            items=[_c],
            page_title=f"Flashcards: {getattr(_c, 'title', '')}",
            is_index=False,
            page_path=f"{_pillar_url}/{_last_slug}/flashcards/",
            **ctx_base,
        )
        (_fc_dir / "index.html").write_text(_fc_html, encoding="utf-8")
        _item_page_count += 1

    if _item_page_count:
        print(f"  item pages (so far): {_item_page_count} pages")

    # --- per-item details pages ---
    for _c in all_content:
        _pillar_key = getattr(_c, "pillar", "")
        _pillar_url = PILLAR_URL_MAP.get(_pillar_key, _pillar_key)
        _slug_parts = getattr(_c, "slug", "").rstrip("/").split("/")
        _last_slug = _slug_parts[-1] if _slug_parts else "unknown"
        _det_dir = OUTPUT_DIR / _pillar_url / _last_slug / "details"
        _det_dir.mkdir(parents=True, exist_ok=True)
        _det_html = render_template(
            "category_index.j2",
            content=_dummy(f"Details: {getattr(_c, 'title', '')}", "index",
                           description=f"Metadata details for {getattr(_c, 'title', '')}."),
            category="details",
            items=[_c],
            page_title=f"Details: {getattr(_c, 'title', '')}",
            is_index=False,
            page_path=f"{_pillar_url}/{_last_slug}/details/",
            **ctx_base,
        )
        (_det_dir / "index.html").write_text(_det_html, encoding="utf-8")
        _item_page_count += 1

    if _item_page_count:
        print(f"  item sub-pages: {_item_page_count} pages")

    # --- per-pillar knowledge-base tiered index pages ---
    if ontology and ontology.concept_count() > 0:
        _kb_count = 0
        for _pillar_key, _pillar_url in PILLAR_URL_MAP.items():
            _by_pillar = ontology.concepts_by_pillar()
            _concepts = _by_pillar.get(_pillar_key, [])
            if not _concepts:
                continue
            _tiers: dict[str, list] = {"foundations": [], "core": [], "advanced": [], "specialized": []}
            for _c in _concepts:
                _cat = (_c.category or "").lower()
                if _cat == "foundations":
                    _tiers["foundations"].append(_c)
                elif _cat in ("cdd-kyc", "sar-str", "regulations", "reporting", "sanctions",
                              "market-analysis", "strategies", "industry-analysis",
                              "best-practices", "architecture", "streaming"):
                    _tiers["core"].append(_c)
                elif _cat in ("advanced-techniques", "regtech", "high-frequency-trading",
                              "macro-analysis", "crypto-aml"):
                    _tiers["advanced"].append(_c)
                else:
                    _tiers["specialized"].append(_c)
            _kb_dir = OUTPUT_DIR / _pillar_url / "knowledge-base"
            _kb_dir.mkdir(parents=True, exist_ok=True)
            _kb_html = render_template(
                "knowledge_base.j2",
                content=_dummy(f"{_pillar_key.title()} Knowledge Base", "index",
                               description=f"Wiki-style knowledge base for {_pillar_key}."),
                pillar_key=_pillar_key,
                pillar_url=_pillar_url,
                pillar_label=PILLAR_CONFIG.get(_pillar_key, {}).get("label", _pillar_key.title()),
                tiers=_tiers,
                is_index=False,
                page_path=f"{_pillar_url}/knowledge-base/",
                **ctx_base,
            )
            (_kb_dir / "index.html").write_text(_kb_html, encoding="utf-8")
            _kb_count += 1
        print(f"  knowledge-base: {_kb_count} pages")

    # --- source trust dashboard ---
    _src_stats: dict[str, dict[str, int]] = defaultdict(lambda: {"total": 0, "with_evidence": 0, "high_confidence": 0})
    _src_authority = {"arxiv": {"label": "arXiv", "type": "peer-reviewed", "authority": 0.9},
                      "pubmed": {"label": "PubMed", "type": "peer-reviewed", "authority": 0.9},
                      "hn": {"label": "Hacker News", "type": "community", "authority": 0.5}}
    for _c in all_content:
        _sb = getattr(_c, "source_breakdown", None) or {}
        for _src, _cnt in _sb.items():
            _src_stats[_src]["total"] += _cnt
            _src_stats[_src]["with_evidence"] += 1
            if getattr(_c, "quality_badge", "") == "high-confidence":
                _src_stats[_src]["high_confidence"] += 1
    _src_data = []
    for _src_name, _s in sorted(_src_stats.items()):
        _meta = _src_authority.get(_src_name, {"label": _src_name, "type": "unknown", "authority": 0.3})
        _src_data.append({**_meta, "name": _src_name, **_s})
    _src_dir = OUTPUT_DIR / "sources"
    _src_dir.mkdir(parents=True, exist_ok=True)
    _src_html = render_template(
        "source_trust.j2",
        content=_dummy("Source Trust Dashboard", "index",
                       description="Source authority and trust metrics across all pillars."),
        sources=_src_data,
        authority_labels=_src_authority,
        page_title="Source Trust Dashboard",
        is_index=False,
        page_path="sources/",
        **ctx_base,
    )
    (_src_dir / "index.html").write_text(_src_html, encoding="utf-8")
    print("  source-trust: 1 page")

    # --- ADMIN PANEL (via build_taxonomies) ---
    from core.images.manifest import load_manifest as _load_manifest

    generate_admin_pages(
        OUTPUT_DIR, all_content, STATIC_DST_DIR, render_template, ctx_base, _dummy,
        load_admin_credentials_fn=load_admin_credentials,
        load_manifest_fn=_load_manifest,
        project_root=PROJECT_ROOT,
        section_types=SECTION_TYPES,
        ontology=ontology,
    )

    # --- SEARCH INDEX + PAGE (via build_taxonomies) ---
    generate_search_pages(
        OUTPUT_DIR, STATIC_DST_DIR, all_content, render_template, ctx_base, _dummy,
        ontology=ontology, concept_cache=_concept_cache,
    )

    # --- FEED (via build_taxonomies) ---
    generate_feed(
        OUTPUT_DIR, all_content, render_template, ctx_base,
        site_url=SITE_URL,
        site_name=SITE_NAME,
        now=now,
        is_future_post_fn=is_future_post,
        canonical_path_fn=canonical_path,
        slug_to_path_fn=lambda s: slug_to_fspath(slug_to_path(s)),
    )

    # --- SITEMAP ---
    today = datetime.now(timezone.utc).date().isoformat()
    section_pages = [pillar_to_url(p) for p in PILLAR_CONFIG] + ["research", "learn", "knowledge", "search"]
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

    # --- REDIRECTS (Cloudflare Pages) ---
    redirects = [
        "/aml/*  /compliance/:splat  301",
        "/aml/signals/*  /compliance/signals/:splat  301",
        "/stock/signals/*  /markets/signals/:splat  301",
        "/stock/*  /markets/:splat  301",
        "/science/*  /data/research/:splat  301",
        "/contact/*  /knowledge/contact/:splat  301",
    ]
    (OUTPUT_DIR / "_redirects").write_text("\n".join(redirects) + "\n", encoding="utf-8")
    print("  redirects: _redirects")

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

    # --- HEADERS ---

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
            commit_hash = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=str(PROJECT_ROOT), text=True, timeout=30
            ).strip()[:8]
            branch = subprocess.check_output(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=str(PROJECT_ROOT),
                text=True,
                timeout=30,
            ).strip()
            log_deployment(
                commit_hash=commit_hash,
                branch=branch,
                status="success",
                pages_generated=total,
                build_duration_ms=duration_ms,
            )
            print(f"  mem0: logged deployment {commit_hash}")
        except (OSError, ValueError) as e:
            print(f"  mem0: logging failed ({e})")

    # ── Build metrics (build-meta.json) ──
    sqi_values = []
    for c in all_content:
        sqi_val = c.sqi or 0.0
        signals_avg = (c.signals or {}).get("avg_sqi", 0.0) if isinstance(c.signals, dict) else 0.0
        effective = max(sqi_val, signals_avg)
        if effective > 0:
            sqi_values.append(effective)
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
    low_sqi_items = []
    for c in all_content:
        sqi_val = c.sqi or 0.0
        signals_avg = (c.signals or {}).get("avg_sqi", 0.0) if isinstance(c.signals, dict) else 0.0
        effective_sqi = max(sqi_val, signals_avg)
        if effective_sqi > 0 and effective_sqi < SQI_THRESHOLD_MIN:
            low_sqi_items.append({"slug": c.slug, "title": c.title[:80], "sqi": effective_sqi})
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
        url = slug_to_url(slug)
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
    manifest_path = PROJECT_ROOT / ".build_manifest.json"
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


if __name__ == "__main__":
    sys.exit(main())


