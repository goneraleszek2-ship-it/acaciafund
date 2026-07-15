"""Tests for core/build_taxonomies.py — tag, admin, search, feed, pillar pages."""

import json
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import ANY, MagicMock

import pytest

from core.build_taxonomies import (
    _compute_coverage_data,
    _compute_dashboard_stats,
    _compute_enrichment_telemetry,
    _compute_quality_stats,
    _compute_source_telemetry,
    _compute_sqi_telemetry,
    _compute_tag_telemetry,
    _compute_telemetry,
    _compute_velocity_telemetry,
    generate_admin_pages,
    generate_feed,
    generate_pillar_pages,
    generate_search_pages,
    generate_tag_pages,
)


def _make_item(**kwargs):
    """Create a simple object with given attributes (like Content)."""
    defaults = {
        "slug": "test/slug",
        "title": "Test Title",
        "pillar": "aml",
        "content_type": "research",
        "tags": [],
        "body_html": "",
        "description": "",
        "featured_image": None,
        "date_str": "",
        "sqi": None,
        "signals": None,
        "source_breakdown": None,
        "section_images": None,
        "enriched": False,
        "enriched_at": None,
        "created_at": None,
        "difficulty": "",
        "reading_time": 0,
        "knowledge_category": "",
    }
    defaults.update(kwargs)
    return type("MockContent", (object,), defaults)()


def _dummy(title="", category="post", body_html="", description=""):
    """Minimal _dummy equivalent from build.py."""
    return type("obj", (object,), {
        "title": title, "language": "en", "category": category,
        "slug": "", "body_html": body_html, "description": description,
        "created_at": None, "updated_at": None, "tags": [], "pillar": "",
        "difficulty": "", "date_str": "", "thumbnail_svg": "", "og_svg": "",
        "signals": {},
    })()


# ── _compute_dashboard_stats ──

class TestComputeDashboardStats:
    def test_empty_content(self):
        stats = _compute_dashboard_stats([])
        assert stats["total_articles"] == 0
        assert stats["with_images_pct"] == 0

    def test_single_item_no_image(self):
        stats = _compute_dashboard_stats([_make_item(slug="a")])
        assert stats["total_articles"] == 1
        assert stats["with_images"] == 0
        assert stats["by_type"][0]["type"] == "research"

    def test_single_item_with_image(self):
        stats = _compute_dashboard_stats([_make_item(slug="a", featured_image="/img/a.png")])
        assert stats["with_images"] == 1

    def test_unknown_content_type(self):
        stats = _compute_dashboard_stats([_make_item(slug="a", content_type=None)])
        assert stats["by_type"][0]["type"] == "unknown"

    def test_source_breakdown_aggregation(self):
        items = [
            _make_item(slug="a", source_breakdown={"arxiv": 1}),
            _make_item(slug="b", source_breakdown={"arxiv": 1, "hn": 2}),
        ]
        stats = _compute_dashboard_stats(items)
        assert stats["by_source"]["arxiv"] == 2
        assert stats["by_source"]["hn"] == 2

    def test_low_score_signals(self):
        items = [
            _make_item(slug="a", signals={"avg_score": 50}),
            _make_item(slug="b", signals={"avg_score": 90}),
        ]
        stats = _compute_dashboard_stats(items)
        assert stats["low_score_sections"] == 1


# ── _compute_quality_stats ──

class TestComputeQualityStats:
    def test_empty_content(self):
        qs = _compute_quality_stats([])
        assert qs["total_scores"] == 0
        assert qs["avg_score"] == 0

    def test_scores_from_section_images(self):
        items = [_make_item(slug="a", section_images=[
            {"relevance_score": 85, "source_api": "unsplash", "section_index": 0},
            {"relevance_score": 60, "source_api": "unsplash", "section_index": 1},
        ])]
        qs = _compute_quality_stats(items)
        assert qs["total_scores"] == 2
        assert qs["avg_score"] == 72.5
        assert qs["above_70"] == 1
        assert qs["below_40"] == 0

    def test_zero_score_ignored(self):
        items = [_make_item(slug="a", section_images=[
            {"relevance_score": 0, "source_api": "unsplash", "section_index": 0},
            {"relevance_score": 80, "source_api": "unsplash", "section_index": 1},
        ])]
        qs = _compute_quality_stats(items)
        assert qs["total_scores"] == 1

    def test_source_averages(self):
        items = [_make_item(slug="a", section_images=[
            {"relevance_score": 90, "source_api": "a", "section_index": 0},
            {"relevance_score": 70, "source_api": "b", "section_index": 0},
        ])]
        qs = _compute_quality_stats(items)
        assert "a" in qs["source_avgs"]
        assert "b" in qs["source_avgs"]


# ── _compute_coverage_data ──

class TestComputeCoverageData:
    def test_empty_content(self):
        cd = _compute_coverage_data([], {})
        assert cd["heatmap"] == {}
        assert cd["by_pillar"] == {}

    def test_section_images_counted(self):
        section_types = {0: "overview"}
        items = [_make_item(slug="a", pillar="aml", content_type="research",
                            section_images=[{"section_index": 0, "image_url": "/img/a.png"}])]
        cd = _compute_coverage_data(items, section_types)
        assert cd["by_pillar"]["aml"]["filled"] == 1
        assert cd["by_pillar"]["aml"]["total"] == 1

    def test_unfilled_not_counted(self):
        section_types = {0: "overview"}
        items = [_make_item(slug="a", pillar="aml", content_type="research",
                            section_images=[{"section_index": 0, "image_url": ""}])]
        cd = _compute_coverage_data(items, section_types)
        assert cd["by_pillar"]["aml"]["filled"] == 0
        assert cd["by_pillar"]["aml"]["total"] == 1


# ── _compute_tag_telemetry ──

class TestComputeTagTelemetry:
    def test_empty_content(self):
        tt = _compute_tag_telemetry([])
        assert tt["total_tags"] == 0
        assert tt["crossover_tags"] == {}

    def test_tag_counts_and_cooccurrence(self):
        items = [
            _make_item(slug="a", tags=["aml", "kyc"], pillar="aml", content_type="research"),
            _make_item(slug="b", tags=["aml", "kyc"], pillar="aml", content_type="knowledge"),
        ]
        tt = _compute_tag_telemetry(items)
        assert tt["total_tags"] == 2
        assert tt["top_tags"][0] == ("aml", 2)
        assert len(tt["cooccurrence_edges"]) == 1
        assert tt["cooccurrence_edges"][0]["weight"] == 2

    def test_crossover_tags(self):
        items = [
            _make_item(slug="a", tags=["data-quality"], pillar="aml"),
            _make_item(slug="b", tags=["data-quality"], pillar="stock"),
        ]
        tt = _compute_tag_telemetry(items)
        assert "data-quality" in tt["crossover_tags"]

    def test_date_tracking(self):
        items = [_make_item(slug="a", tags=["ml"], date_str="2026-06-01")]
        tt = _compute_tag_telemetry(items)
        assert tt["total_assignments"] == 1


# ── _compute_sqi_telemetry ──

class TestComputeSqiTelemetry:
    def test_empty_content(self):
        sqi = _compute_sqi_telemetry([])
        assert sqi["count"] == 0

    def test_direct_sqi(self):
        items = [_make_item(slug="a", sqi=0.85)]
        sqi = _compute_sqi_telemetry(items)
        assert sqi["avg"] == 0.85
        assert sqi["above_08"] == 1

    def test_signals_fallback(self):
        items = [_make_item(slug="a", sqi=None, signals={"avg_sqi": 0.75})]
        sqi = _compute_sqi_telemetry(items)
        assert sqi["avg"] == 0.75

    def test_missing_sqi_defaults(self):
        items = [_make_item(slug="a", sqi=None, signals=None)]
        sqi = _compute_sqi_telemetry(items)
        assert sqi["avg"] == 0.5

    def test_sqi_clamped(self):
        items = [_make_item(slug="a", sqi=1.5)]
        sqi = _compute_sqi_telemetry(items)
        assert sqi["max"] <= 1.0

    def test_pillar_averages(self):
        items = [
            _make_item(slug="a", sqi=0.9, pillar="aml"),
            _make_item(slug="b", sqi=0.7, pillar="stock"),
            _make_item(slug="c", sqi=0.8, pillar="aml"),
        ]
        sqi = _compute_sqi_telemetry(items)
        assert sqi["pillar_avgs"]["aml"]["avg"] == 0.85
        assert sqi["pillar_avgs"]["stock"]["avg"] == 0.7


# ── _compute_enrichment_telemetry ──

class TestComputeEnrichmentTelemetry:
    def test_all_deterministic(self):
        items = [_make_item(slug="a", tags=["aml"]), _make_item(slug="b", tags=["kyc"])]
        et = _compute_enrichment_telemetry(items)
        assert et["deterministic_likely"] == 2
        assert et["llm_likely"] == 0

    def test_llm_likely_with_many_tags(self):
        items = [_make_item(slug="a", tags=["a", "b", "c", "d", "e"])]
        et = _compute_enrichment_telemetry(items)
        assert et["llm_likely"] == 1

    def test_enriched_by_flag(self):
        items = [_make_item(slug="a", enriched=True)]
        et = _compute_enrichment_telemetry(items)
        assert et["total_enriched"] == 1

    def test_enriched_by_at(self):
        items = [_make_item(slug="a", enriched=False, enriched_at="2026-07-14T00:00:00Z")]
        et = _compute_enrichment_telemetry(items)
        assert et["total_enriched"] == 1


# ── _compute_velocity_telemetry ──

class TestComputeVelocityTelemetry:
    def test_empty(self):
        vt = _compute_velocity_telemetry([])
        assert vt["total_months"] == 0

    def test_monthly_grouping(self):
        items = [
            _make_item(slug="a", created_at=datetime(2026, 6, 1, tzinfo=timezone.utc)),
            _make_item(slug="b", created_at=datetime(2026, 6, 15, tzinfo=timezone.utc)),
            _make_item(slug="c", created_at=datetime(2026, 7, 1, tzinfo=timezone.utc)),
        ]
        vt = _compute_velocity_telemetry(items)
        assert vt["total_months"] == 2
        june = [m for m in vt["monthly"] if m["period"] == "2026-06"]
        assert len(june) == 1
        assert june[0]["count"] == 2

    def test_no_datetime_ignored(self):
        items = [_make_item(slug="a", created_at=None)]
        vt = _compute_velocity_telemetry(items)
        assert vt["total_months"] == 0


# ── _compute_source_telemetry ──

class TestComputeSourceTelemetry:
    def test_empty(self):
        st = _compute_source_telemetry([])
        assert st["source_totals"] == {}

    def test_source_aggregation(self):
        items = [
            _make_item(slug="a", source_breakdown={"arxiv": 1}, pillar="aml"),
            _make_item(slug="b", source_breakdown={"hn": 2}, pillar="stock"),
        ]
        st = _compute_source_telemetry(items)
        assert st["source_totals"]["arxiv"] == 1
        assert st["source_totals"]["hn"] == 2
        assert st["source_by_pillar"]["stock"]["hn"] == 2
        assert st["items_with_sources"] == 2


# ── _compute_telemetry (aggregator) ──

class TestComputeTelemetry:
    def test_returns_all_keys(self):
        items = [_make_item(slug="a", tags=["aml"], sqi=0.8, pillar="aml")]
        t = _compute_telemetry(items)
        assert "tag" in t
        assert "sqi" in t
        assert "enrichment" in t
        assert "velocity" in t
        assert "source" in t


# ── generate_tag_pages ──

class TestGenerateTagPages:
    def test_generates_tag_pages(self, tmp_path):
        output_dir = tmp_path / "site"
        render_template = MagicMock(return_value="<html>tag</html>")
        tag_items = {"aml": [_make_item(slug="a")], "kyc": [_make_item(slug="b")]}
        pages = generate_tag_pages(output_dir, tag_items, render_template, {}, _dummy)
        assert pages == 3  # 2 tags + 1 index
        assert (output_dir / "tags" / "aml" / "index.html").exists()
        assert (output_dir / "tags" / "kyc" / "index.html").exists()
        assert (output_dir / "tags" / "index.html").exists()

    def test_thin_tag_gets_noindex(self, tmp_path):
        output_dir = tmp_path / "site"
        render_template = MagicMock(return_value="<html>thin</html>")
        tag_items = {"thin": [_make_item(slug="a")]}
        generate_tag_pages(output_dir, tag_items, render_template, {}, _dummy)
        first_call_kwargs = render_template.call_args_list[0][1]
        assert first_call_kwargs.get("robots_noindex") is True

    def test_empty_no_index(self, tmp_path):
        output_dir = tmp_path / "site"
        pages = generate_tag_pages(output_dir, {}, MagicMock(), {}, _dummy)
        assert pages == 0

    def test_slug_cleaning(self, tmp_path):
        output_dir = tmp_path / "site"
        render_template = MagicMock(return_value="<html>c</html>")
        tag_items = {"AML/KYC Compliance": [_make_item(slug="a")]}
        generate_tag_pages(output_dir, tag_items, render_template, {}, _dummy)
        assert (output_dir / "tags" / "aml-kyc-compliance" / "index.html").exists()


# ── generate_search_pages ──

class TestGenerateSearchPages:
    def test_search_index_and_page(self, tmp_path):
        output_dir = tmp_path / "site"
        static_dir = tmp_path / "static"
        static_dir.mkdir(parents=True)
        render_template = MagicMock(return_value="<html>search</html>")
        items = [_make_item(slug="a", title="Test", description="Desc", pillar="aml",
                            content_type="research", tags=["aml"], sqi=0.85)]
        pages = generate_search_pages(output_dir, static_dir, items, render_template, {}, _dummy)
        assert pages == 2
        assert (static_dir / "search-index.json").exists()

    def test_search_index_content(self, tmp_path):
        output_dir = tmp_path / "site"
        static_dir = tmp_path / "static"
        static_dir.mkdir(parents=True)
        items = [_make_item(slug="a", title="Test", description="Desc", pillar="aml",
                            content_type="research", tags=["aml"], sqi=0.85)]
        render_template = MagicMock(return_value="<html>search</html>")
        generate_search_pages(output_dir, static_dir, items, render_template, {}, _dummy)
        idx = json.loads((static_dir / "search-index.json").read_text())
        assert len(idx) == 1
        assert idx[0]["title"] == "Test"

    def test_search_concept_enrichment(self, tmp_path):
        output_dir = tmp_path / "site"
        static_dir = tmp_path / "static"
        static_dir.mkdir(parents=True)
        items = [_make_item(slug="a", title="Test")]
        concept_cache = {"a": {"concept-1"}}

        class FakeOntology:
            _concepts = {"concept-1": type("c", (object,), {"id": "concept-1", "label": "Concept One"})}

        render_template = MagicMock(return_value="<html>search</html>")
        pages = generate_search_pages(output_dir, static_dir, items, render_template, {}, _dummy,
                                       ontology=FakeOntology(), concept_cache=concept_cache)
        idx = json.loads((static_dir / "search-index.json").read_text())
        assert "Concept One" in idx[0]["ontology_concepts"]
        assert idx[0]["concept_boost"] > 0

    def test_empty_slug_skipped(self, tmp_path):
        output_dir = tmp_path / "site"
        static_dir = tmp_path / "static"
        static_dir.mkdir(parents=True)
        items = [_make_item(slug=None), _make_item(slug="valid")]
        render_template = MagicMock(return_value="<html>search</html>")
        generate_search_pages(output_dir, static_dir, items, render_template, {}, _dummy)
        idx = json.loads((static_dir / "search-index.json").read_text())
        assert len(idx) == 1


# ── generate_feed ──

class TestGenerateFeed:
    def test_generates_feed(self, tmp_path):
        output_dir = tmp_path / "site"
        output_dir.mkdir(parents=True, exist_ok=True)
        items = [
            _make_item(slug="a", title="Post A", description="Desc A",
                       created_at=datetime(2026, 6, 1, tzinfo=timezone.utc),
                       tags=["aml"], content_type="research", pillar="aml"),
        ]
        pages = generate_feed(output_dir, items, MagicMock(), {},
                              site_url="https://example.com", site_name="Test",
                              now=datetime(2026, 6, 15, tzinfo=timezone.utc))
        assert pages == 1
        feed = (output_dir / "feed.xml").read_text()
        assert "Post A" in feed
        assert "https://example.com" in feed
        assert 'pillar:aml' in feed
        assert 'type:research' in feed

    def test_feed_content(self, tmp_path):
        output_dir = tmp_path / "site"
        output_dir.mkdir(parents=True, exist_ok=True)
        items = [
            _make_item(slug="a", title="Alpha", description="",
                       body_html="<p>Body content here</p>",
                       created_at=datetime(2026, 6, 1, tzinfo=timezone.utc)),
        ]
        generate_feed(output_dir, items, MagicMock(), {},
                      site_url="https://x.com", site_name="X",
                      now=datetime(2026, 6, 15, tzinfo=timezone.utc))
        feed = (output_dir / "feed.xml").read_text()
        assert "Body content here" in feed

    def test_html_stripped_from_feed_desc(self, tmp_path):
        output_dir = tmp_path / "site"
        output_dir.mkdir(parents=True, exist_ok=True)
        items = [
            _make_item(slug="a", title="Test", description="<b>bold</b> text",
                       created_at=datetime(2026, 6, 1, tzinfo=timezone.utc)),
        ]
        generate_feed(output_dir, items, MagicMock(), {},
                      site_url="https://x.com", site_name="X",
                      now=datetime(2026, 6, 15, tzinfo=timezone.utc))
        feed = (output_dir / "feed.xml").read_text()
        assert "<b>" not in feed
        assert "bold text" in feed


# ── generate_pillar_pages ──

class TestGeneratePillarPages:
    def test_generates_pillar_pages(self, tmp_path):
        output_dir = tmp_path / "site"
        render_template = MagicMock(return_value="<html>pillar</html>")
        groups = {"compliance": [_make_item(slug="a")], "markets": [_make_item(slug="b")]}
        pages = generate_pillar_pages(output_dir, groups, render_template, {})
        assert pages == 2
        assert (output_dir / "compliance" / "index.html").exists()
        assert (output_dir / "markets" / "index.html").exists()

    def test_empty_groups(self, tmp_path):
        pages = generate_pillar_pages(tmp_path / "site", {}, MagicMock(), {})
        assert pages == 0


# ── generate_admin_pages (selected tests) ──

class TestGenerateAdminPages:
    def test_dashboard_page(self, tmp_path):
        output_dir = tmp_path / "site"
        static_dir = tmp_path / "static"
        static_dir.mkdir(parents=True)
        render_template = MagicMock(return_value="<html>dashboard</html>")
        items = [_make_item(slug="a", title="Test")]
        pages = generate_admin_pages(output_dir, items, static_dir, render_template, {}, _dummy)
        assert pages >= 1
        assert (output_dir / "admin" / "dashboard.html").exists()

    def test_login_page_with_default_creds(self, tmp_path):
        output_dir = tmp_path / "site"
        static_dir = tmp_path / "static"
        static_dir.mkdir(parents=True)
        render_template = MagicMock(return_value="<html>login</html>")
        items = [_make_item(slug="a")]
        generate_admin_pages(
            output_dir, items, static_dir, render_template, {}, _dummy,
            load_admin_credentials_fn=lambda: ("admin", "admin"),
        )
        render_template.assert_any_call(
            "admin/login.html",
            content=ANY,
            admin_username="admin",
            admin_password="admin",
        )

    def test_quality_page(self, tmp_path):
        output_dir = tmp_path / "site"
        static_dir = tmp_path / "static"
        static_dir.mkdir(parents=True)
        render_template = MagicMock(return_value="<html>quality</html>")
        items = [_make_item(slug="a", section_images=[{"relevance_score": 85, "source_api": "u", "section_index": 0}])]
        generate_admin_pages(output_dir, items, static_dir, render_template, {}, _dummy)
        assert (output_dir / "admin" / "quality.html").exists()

    def test_redirect_index(self, tmp_path):
        output_dir = tmp_path / "site"
        static_dir = tmp_path / "static"
        static_dir.mkdir(parents=True)
        render_template = MagicMock(return_value='<html><meta http-equiv="refresh" content="0;url=dashboard.html"></html>')
        generate_admin_pages(output_dir, [], static_dir, render_template, {}, _dummy)
        idx = (output_dir / "admin" / "index.html").read_text()
        assert "redirect" in idx.lower()

    def test_sources_from_pillars_toml_fallback(self, tmp_path):
        output_dir = tmp_path / "site"
        static_dir = tmp_path / "static"
        static_dir.mkdir(parents=True)
        # Create a minimal pillars.toml
        etc_dir = tmp_path / "etc"
        etc_dir.mkdir(parents=True)
        (etc_dir / "pillars.toml").write_text(
            '[inspiration_sources]\n[inspiration_sources.aml]\n[inspiration_sources.aml.ssrn]\nname = "SSRN"\nurl = "https://ssrn.com"\nrelevance = 0.9\n'
        )
        render_template = MagicMock(return_value="<html>sources</html>")
        generate_admin_pages(output_dir, [], static_dir, render_template, {}, _dummy,
                             project_root=tmp_path)
        # sources.html should have been generated
        assert (output_dir / "admin" / "sources.html").exists()
