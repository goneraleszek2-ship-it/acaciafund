"""Unit tests for AcaciaFund core modules.

Tests cover classification, Bloom taxonomy, SQI, SVG generation,
and the data/config layer. No external API calls or network access.
"""

import json
import re
from pathlib import Path

# ── Test data ──

_SAMPLE_STORY = {
    "title": "NVIDIA announces new GPU architecture for AI training workloads",
    "url": "https://nvidia.com/news/gpu-architecture",
    "hn_url": "https://news.ycombinator.com/item?id=12345",
    "points": 342,
    "created_at": "2026-05-22T10:00:00Z",
    "author": "testuser",
    "object_id": "12345",
}

_SAMPLE_STORIES = [
    _SAMPLE_STORY,
    {
        "title": "FATF publishes new guidance on cryptocurrency regulation compliance",
        "url": "https://fatf-gafi.org/guidance-crypto",
        "hn_url": "",
        "points": 89,
        "created_at": "2026-05-22T09:00:00Z",
        "author": "crypto_watch",
        "object_id": "12346",
    },
    {
        "title": "DeepMind discovers novel protein structures using AlphaFold",
        "url": "https://nature.com/articles/deepmind-protein",
        "hn_url": "",
        "points": 512,
        "created_at": "2026-05-22T08:00:00Z",
        "author": "science_news",
        "object_id": "12347",
    },
]

_EMPTY_STORY: dict = {}
_NO_SCORE_STORY = {"title": "Random blog post about something unrelated", "points": 1}


# ══════════════════════════════════════════════
# 1. DATA LAYER TESTS
# ══════════════════════════════════════════════

def test_pillars_loaded():
    from core.data import PILLARS
    assert "aml" in PILLARS
    assert "stock" in PILLARS
    assert "data-engineering" in PILLARS
    for p in PILLARS:
        assert "label" in PILLARS[p]
        assert "emoji" in PILLARS[p]
        assert "tags" in PILLARS[p]
        assert "keywords" in PILLARS[p]


def test_domain_taxonomy():
    from core.data import DOMAIN_TAXONOMY
    assert "data-engineering" in DOMAIN_TAXONOMY
    assert "finance" in DOMAIN_TAXONOMY
    assert "regulation" in DOMAIN_TAXONOMY


def test_known_entities():
    from core.data import KNOWN_ENTITIES, ALL_ENTITIES
    assert "aml" in KNOWN_ENTITIES
    assert "stock" in KNOWN_ENTITIES
    assert "data-engineering" in KNOWN_ENTITIES
    assert "FinCEN" in KNOWN_ENTITIES["aml"]
    assert "NVIDIA" in KNOWN_ENTITIES["stock"]
    assert "Dagster" in KNOWN_ENTITIES["data-engineering"]
    assert len(ALL_ENTITIES) > 10


def test_entity_defs_loaded():
    from core.data import ENTITY_DEFS
    assert len(ENTITY_DEFS) > 30
    assert "FinCEN" in ENTITY_DEFS
    assert "NVIDIA" in ENTITY_DEFS
    assert "MIT" in ENTITY_DEFS
    assert "GDPR" in ENTITY_DEFS


def test_source_tiers():
    from core.data import SOURCE_TIERS
    assert len(SOURCE_TIERS) > 0
    gov_pat = SOURCE_TIERS[0][0]
    assert isinstance(gov_pat, re.Pattern)


def test_extract_domain():
    from core.data import extract_domain
    assert extract_domain("https://nvidia.com/news") == "nvidia.com"
    assert extract_domain("http://example.com/path") == "example.com"
    assert extract_domain("") == ""


def test_categorize_domain():
    from core.data import categorize_domain
    assert categorize_domain("dagster.io") == "data-engineering"
    assert categorize_domain("bloomberg.com") == "finance"
    assert categorize_domain("fincen.gov") == "regulation"
    assert categorize_domain("arstechnica.com") == "technology"
    assert categorize_domain("unknown.xyz") == "other"


def test_extract_entities():
    from core.data import extract_entities
    ents = extract_entities("NVIDIA and FinCEN are working on new AI compliance tools")
    assert "NVIDIA" in ents
    assert "FinCEN" in ents


def test_extract_themes():
    from core.data import extract_themes
    themes = extract_themes(["New AI breakthrough from NVIDIA", "AMD launches new chip"])
    assert len(themes) >= 2


# ══════════════════════════════════════════════
# 2. CLASSIFICATION TESTS
# ══════════════════════════════════════════════

def test_classify_aml_story():
    from core.analyze import classify_story
    results = classify_story({
        "title": "FATF new guidance on cryptocurrency AML compliance",
        "url": "https://fatf-gafi.org/report",
        "points": 50,
    })
    assert results, "Should classify AML story"
    top = max(results, key=lambda x: x[1])
    assert top[0] == "aml", f"Expected aml, got {top}"


def test_classify_stock_story():
    from core.analyze import classify_story
    results = classify_story({
        "title": "NVIDIA announces record earnings for Q2 2026",
        "url": "https://nvidia.com/earnings",
        "points": 200,
    })
    assert results, "Should classify stock story"
    top = max(results, key=lambda x: x[1])
    assert top[0] == "stock", f"Expected stock, got {top}"


def test_classify_data_engineering_story():
    from core.analyze import classify_story
    results = classify_story({
        "title": "Dagster 2.0: new data pipeline orchestration and observability features",
        "url": "https://dagster.io/blog/2.0",
        "points": 150,
    })
    assert results, "Should classify DE story"
    top = max(results, key=lambda x: x[1])
    assert top[0] == "data-engineering", f"Expected data-engineering, got {top}"


def test_classify_empty_story():
    from core.analyze import classify_story
    results = classify_story({"title": "", "url": "", "points": 0})
    assert results == []


def test_classify_multi_pillar():
    """A story about AI regulation could score for both aml and data-engineering."""
    from core.analyze import classify_story
    results = classify_story({
        "title": "SEC proposes new AI regulation framework for algorithmic trading",
        "url": "https://sec.gov/ai-framework",
        "points": 180,
    })
    assert len(results) >= 1
    # SEC domain + regulation keywords should lean aml
    top = max(results, key=lambda x: x[1])
    assert top[0] in ("aml", "stock"), f"Expected aml or stock, got {top}"


def test_build_pillar_signals():
    from core.analyze import build_pillar_signals
    signals = build_pillar_signals(_SAMPLE_STORIES, "stock")
    assert signals is not None
    assert "avg_sqi" in signals
    assert "avg_score" in signals
    assert signals["avg_score"] >= 0
    assert 0 <= signals["avg_sqi"] <= 1


def test_build_pillar_signals_empty():
    from core.analyze import build_pillar_signals
    signals = build_pillar_signals([], "aml")
    assert signals == {}  # empty stories => empty signals


# ══════════════════════════════════════════════
# 3. BLOOM TAXONOMY TESTS
# ══════════════════════════════════════════════

def test_classify_bloom_create():
    from core.analyze import classify_bloom_level_enhanced
    level = classify_bloom_level_enhanced({
        "title": "Breakthrough discovery of novel protein structure",
        "points": 300,
    })
    assert level == "create", f"Expected create, got {level}"


def test_classify_bloom_evaluate():
    from core.analyze import classify_bloom_level_enhanced
    level = classify_bloom_level_enhanced({
        "title": "New regulations for AI safety compliance framework",
        "url": "https://example.com/report",
        "points": 250,
    })
    assert level == "evaluate", f"Expected evaluate, got {level}"


def test_classify_bloom_remember():
    from core.analyze import classify_bloom_level_enhanced
    level = classify_bloom_level_enhanced({
        "title": "Company announces launch of new product",
        "points": 10,
    })
    assert level == "remember", f"Expected remember, got {level}"


def test_classify_bloom_understand():
    from core.analyze import classify_bloom_level_enhanced
    level = classify_bloom_level_enhanced({
        "title": "What is machine learning? A beginner's guide",
        "points": 5,
    })
    assert level == "understand", f"Expected understand, got {level}"


def test_level_label_en():
    from core.bloom import level_label_en
    assert level_label_en("remember") == "Remembering"
    assert level_label_en("understand") == "Understanding"
    assert level_label_en("apply") == "Applying"
    assert level_label_en("analyze") == "Analyzing"
    assert level_label_en("evaluate") == "Evaluating"
    assert level_label_en("create") == "Creating"


def test_generate_quiz_questions():
    from core.bloom import generate_quiz_questions
    questions = generate_quiz_questions(_SAMPLE_STORIES, "AML")
    assert len(questions) >= 1
    for q in questions:
        assert "question" in q
        assert "bloom_level" in q
        assert "type" in q


def test_generate_quiz_questions_empty():
    from core.bloom import generate_quiz_questions
    questions = generate_quiz_questions([], "test")
    assert questions == []


def test_generate_flashcards():
    from core.bloom import generate_flashcards
    cards = generate_flashcards(_SAMPLE_STORIES, "stock")
    assert len(cards) >= 1
    for c in cards:
        assert "term" in c
        assert "definition" in c
        assert "source_type" in c


def test_generate_flashcards_empty():
    from core.bloom import generate_flashcards
    cards = generate_flashcards([], "test")
    assert cards == []


# ══════════════════════════════════════════════
# 4. SQI SCORING TESTS
# ══════════════════════════════════════════════

def test_compute_signal_score():
    from core.score import compute_signal_score
    result = compute_signal_score(
        {"title": "Test story", "url": "https://example.com", "points": 100,
         "created_at": "2026-05-22T10:00:00Z"},
        history={},
    )
    assert "sqi" in result
    assert 0 <= result["sqi"] <= 1
    assert "engagement" in result
    assert "authority" in result
    assert "novelty" in result


def test_compute_signal_score_low():
    from core.score import compute_signal_score
    result = compute_signal_score(
        {"title": "x", "url": "", "points": 0,
         "created_at": "2026-05-20T10:00:00Z"},
        history={},
    )
    assert result["sqi"] < 0.5
    assert result["engagement"] == 0.0


def test_compute_signal_score_empty():
    from core.score import compute_signal_score
    result = compute_signal_score(
        {"title": "", "url": "", "points": 0, "created_at": ""},
        history={},
    )
    assert "sqi" in result


def test_engagement_score():
    from core.score import engagement_score
    from datetime import datetime, timezone
    now = datetime(2026, 5, 22, 12, 0, 0, tzinfo=timezone.utc)
    score = engagement_score(
        {"title": "Test", "points": 100,
         "created_at": "2026-05-22T10:00:00Z"},
        now,
    )
    assert 0 <= score <= 1


# ══════════════════════════════════════════════
# 5. SVG / VISUALS TESTS
# ══════════════════════════════════════════════

def test_generate_thumbnail_svg():
    from core.visuals import generate_thumbnail_svg
    svg = generate_thumbnail_svg(
        "Test title about AI regulation",
        "aml",
        {"sqi": 0.75},
    )
    assert svg.startswith("<svg")
    assert svg.endswith("</svg>")
    assert "aml".upper() in svg.lower() or "AML" in svg


def test_generate_thumbnail_svg_markets():
    from core.visuals import generate_thumbnail_svg
    svg = generate_thumbnail_svg(
        "Stock market analysis and semiconductor trends",
        "stock",
        {"sqi": 0.6},
    )
    assert svg.startswith("<svg")
    assert "STOCK" in svg  # badge shows pillar name


def test_generate_thumbnail_svg_data_engineering():
    from core.visuals import generate_thumbnail_svg
    svg = generate_thumbnail_svg(
        "Building real-time data pipelines with Kafka and Flink",
        "data-engineering",
        {"sqi": 0.9},
    )
    assert svg.startswith("<svg")


def test_generate_og_image():
    from core.visuals import generate_og_image
    svg = generate_og_image(
        "Test OG image for AML pillar",
        "aml",
        {"sqi": 0.8},
        "2026-05-22",
    )
    assert svg.startswith("<svg")
    assert svg.endswith("</svg>")
    assert "AcaciaFund" in svg


def test_generate_signal_meter():
    from core.visuals import generate_signal_meter
    svg = generate_signal_meter(0.75)
    assert svg.startswith("<svg")
    assert svg.endswith("</svg>")
    assert "0.75" in svg or "0.75" in svg


def test_generate_signal_meter_extremes():
    from core.visuals import generate_signal_meter
    assert generate_signal_meter(0.0) is not None
    assert generate_signal_meter(1.0) is not None
    assert generate_signal_meter(-0.5) is not None  # clamp


def test_generate_topic_badge():
    from core.visuals import generate_topic_badge
    svg = generate_topic_badge("AML", "aml", 42)
    assert svg.startswith("<svg")
    assert "AML" in svg


def test_pick_subtopic():
    from core.visuals import _pick_subtopic
    assert _pick_subtopic(["New AI chip from NVIDIA"], "stock") in (
        "semiconductor", "ai", "stock_market", "manufacturing",
    )
    assert _pick_subtopic(["New cryptocurrency regulation"], "aml") in (
        "regulation", "crypto", "fraud", "banking",
    )
    assert _pick_subtopic(["Kafka streaming pipeline optimization"], "data-engineering") in (
        "pipeline", "storage", "quality", "streaming", "infrastructure",
    )


# ══════════════════════════════════════════════
# 6. SCRAPER TESTS
# ══════════════════════════════════════════════

def test_url_key():
    from core.scraper import _url_key
    key = _url_key("https://example.com/article")
    assert isinstance(key, str)
    assert len(key) == 12  # md5 hexdigest[:12]
    assert _url_key("http://example.com/") != _url_key("https://example.com/")
    assert _url_key("") == "000000000000" or _url_key("") is not None


def test_scraper_extract_facts_empty():
    from core.scraper import _extract_facts
    result = _extract_facts("")
    assert result["sentences"] == []
    assert result["names"] == []


# ══════════════════════════════════════════════
# 7. GENERATE TESTS
# ══════════════════════════════════════════════

def test_build_trending_section():
    from core.generate import _build_trending_section
    signals = {"avg_sqi": 0.6}
    result = _build_trending_section(_SAMPLE_STORIES, signals)
    assert "NVIDIA" in result
    assert "FATF" in result
    assert "DeepMind" in result


def test_build_trending_section_empty():
    from core.generate import _build_trending_section
    result = _build_trending_section([], {})
    assert result == ""


def test_build_classification_confidence():
    from core.generate import _build_classification_confidence
    result = _build_classification_confidence(
        _SAMPLE_STORIES, "aml", _SAMPLE_STORIES, 0
    )
    assert "Classification" in result
    assert "%" in result


def test_build_classification_confidence_empty():
    from core.generate import _build_classification_confidence
    result = _build_classification_confidence([], "aml", [], 0)
    assert result == ""


def test_build_content_deep_analysis():
    from core.generate import _build_content_deep_analysis
    result = _build_content_deep_analysis(
        _SAMPLE_STORIES, {}, "stock", {"avg_sqi": 0.6}
    )
    assert isinstance(result, str)


def test_build_content_deep_analysis_with_scraped():
    from core.generate import _build_content_deep_analysis
    from core.scraper import _url_key
    scraped = {
        _url_key(_SAMPLE_STORIES[0]["url"]): {
            "text": "Some article content about NVIDIA GPU architecture.",
            "facts": {
                "sentences": ["NVIDIA announced record revenue of $30 billion"],
                "names": ["NVIDIA", "GPU"],
                "numbers": [("30", "billion")],
            },
        }
    }
    result = _build_content_deep_analysis(
        _SAMPLE_STORIES[:1], scraped, "stock", {"avg_sqi": 0.6}
    )
    assert isinstance(result, str)


# ══════════════════════════════════════════════
# 8. BLOOM KEYWORDS TESTS
# ══════════════════════════════════════════════

def test_bloom_keywords_level_patterns():
    from core.bloom_keywords import REMEMBER_KW, UNDERSTAND_KW, APPLY_KW
    from core.bloom_keywords import ANALYZE_KW, EVALUATE_KW, CREATE_KW
    assert REMEMBER_KW.search("announces new product")
    assert UNDERSTAND_KW.search("guide to basics")
    assert APPLY_KW.search("implementation guide")
    assert ANALYZE_KW.search("analysis of trends")
    assert EVALUATE_KW.search("regulation and compliance")
    assert CREATE_KW.search("novel breakthrough discovery")


def test_bloom_keywords_gov_org():
    from core.bloom_keywords import GOV_ORG_DOMAIN
    assert GOV_ORG_DOMAIN.search("https://example.gov")
    assert GOV_ORG_DOMAIN.search("https://mit.edu")
    assert not GOV_ORG_DOMAIN.search("https://example.com")


def test_bloom_keywords_arxiv():
    from core.bloom_keywords import ARXIV_DOMAIN
    assert ARXIV_DOMAIN.search("https://arxiv.org/abs/12345")
    assert not ARXIV_DOMAIN.search("https://example.com")


# ══════════════════════════════════════════════
# 9. EDGE CASES
# ══════════════════════════════════════════════

def test_classify_none_story():
    from core.analyze import classify_story
    assert classify_story({}) == []
    assert classify_story({"title": "", "points": 0, "url": ""}) == []


def test_classify_bloom_high_points_boost():
    from core.analyze import classify_bloom_level_enhanced
    level = classify_bloom_level_enhanced({
        "title": "Some minor update to software",
        "points": 500,
    })
    assert level in ("evaluate", "remember", "understand")


def test_classify_bloom_no_content():
    from core.analyze import classify_bloom_level_enhanced
    level = classify_bloom_level_enhanced({"title": "", "points": 0})
    assert level == "understand"  # default


def test_visuals_subtopic_fallback():
    from core.visuals import _pick_subtopic
    result = _pick_subtopic(["Completely unknown topic with no keywords"], "aml")
    assert result in (
        "regulation", "crypto", "fraud", "banking",
    )
    # Should return first available subtopic for the pillar


def test_visuals_subtopic_unknown_pillar():
    from core.visuals import _pick_subtopic
    result = _pick_subtopic(["Some title"], "nonexistent")
    assert result == "regulation"  # default fallback


# ══════════════════════════════════════════════
# 10. CONFIG INTEGRITY
# ══════════════════════════════════════════════

def test_pillar_config_consistency():
    from core.data import PILLARS, DOMAIN_TAXONOMY, KNOWN_ENTITIES
    for pname in ("aml", "stock", "data-engineering"):
        assert pname in PILLARS, f"Missing pillar: {pname}"
        assert pname in KNOWN_ENTITIES, f"Missing entities for: {pname}"
        assert len(KNOWN_ENTITIES[pname]) >= 10, f"Too few entities for {pname}"


def test_static_assets_exist():
    static = Path(__file__).parent.parent / "static" / "images"
    assert (static / "logo.svg").exists()
    assert (static / "favicon.svg").exists()
    assert (static / "aml-thumb.svg").exists()
    assert (static / "markets-thumb.svg").exists()
    assert (static / "data-engineering-thumb.svg").exists()
    assert (static / "about" / "about-section.svg").exists()
    assert (static / "course-panel.svg").exists()


def test_pwa_manifest():
    manifest = Path(__file__).parent.parent / "static" / "manifest.json"
    assert manifest.exists()
    data = json.loads(manifest.read_text())
    assert "name" in data
    assert "icons" in data
    assert len(data["icons"]) >= 2
