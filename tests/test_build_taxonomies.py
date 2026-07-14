"""Tests for core/build_taxonomies.py — taxonomy generation pipeline."""

import json
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _to_obj(d: dict):
    """Convert a dict to a SimpleNamespace for attribute access (.slug, .title, etc.)."""
    return SimpleNamespace(**d)


def _dummy_content(slug: str = "", ct: str = "", pillar: str = "") -> dict:
    return {
        "slug": slug,
        "title": f"Test {slug}",
        "content_type": ct or "research",
        "pillar": pillar or "aml",
        "tags": ["test", slug.split("/")[-1]] if slug else ["test"],
        "body_html": "<p>Body</p>",
        "description": f"Desc for {slug}" if slug else "A test",
        "date_str": "2026-07-13",
        "difficulty": "beginner",
        "reading_time": 3,
        "sqi": 0.85,
        "author": "AcaciaFund",
        "language": "en",
        "signals": {"avg_sqi": 0.85},
        "created_at": datetime(2026, 7, 13, 12, 0, 0, tzinfo=timezone.utc),
    }


def _dummy_obj(slug: str, ct: str) -> dict:
    """Matches _dummy signature used in build_taxonomies: fn(slug_or_title, content_type)."""
    return _dummy_content(slug=slug, ct=ct, pillar="aml")


def _make_items(count: int = 5) -> list:
    """Return list of SimpleNamespace items matching Content object interface."""
    pillars = ["aml", "stock", "data-engineering"]
    cts = ["research", "learn", "knowledge"]
    items = []
    for i in range(count):
        p = pillars[i % len(pillars)]
        ct = cts[i % len(cts)]
        items.append(_to_obj(_dummy_content(f"{p}/{ct}/item-{i}", ct, p)))
    return items


# ── Fixtures ──


@pytest.fixture
def mock_render():
    return MagicMock(return_value="<html>Rendered</html>")


@pytest.fixture
def ctx_base():
    return {
        "site_name": "AcaciaFund",
        "site_url": "https://www.acaciafund.org",
        "build_timestamp": "2026-07-13T00:00:00",
    }


@pytest.fixture
def tmp_dist(tmp_path):
    d = tmp_path / "dist"
    d.mkdir()
    return d


# ── Tag Pages ──


class TestGenerateTagPages:
    def test_generates_tag_index_and_pages(self, tmp_dist, mock_render, ctx_base):
        from core.build_taxonomies import generate_tag_pages

        tag_items = {
            "aml": [_dummy_content("aml/res/item-1", "research", "aml")],
            "data-engineering": [_dummy_content("de/res/item-2", "research", "data-engineering")],
            "markets": [_dummy_content("mkt/res/item-3", "research", "stock")],
        }
        count = generate_tag_pages(tmp_dist, tag_items, mock_render, ctx_base, _dummy_obj)

        assert count == 4
        assert (tmp_dist / "tags" / "index.html").exists()
        assert (tmp_dist / "tags" / "aml" / "index.html").exists()
        assert (tmp_dist / "tags" / "data-engineering" / "index.html").exists()
        assert (tmp_dist / "tags" / "markets" / "index.html").exists()

    def test_empty_tag_items_returns_zero(self, tmp_dist, mock_render, ctx_base):
        from core.build_taxonomies import generate_tag_pages

        count = generate_tag_pages(tmp_dist, {}, mock_render, ctx_base, _dummy_obj)
        assert count == 0

    def test_slug_sanitization_handles_special_chars(self, tmp_dist, mock_render, ctx_base):
        from core.build_taxonomies import generate_tag_pages

        tag_items = {"Data Quality!@#": [_dummy_content("test/item-1", "research", "data-engineering")]}
        count = generate_tag_pages(tmp_dist, tag_items, mock_render, ctx_base, _dummy_obj)
        assert count == 2
        assert (tmp_dist / "tags" / "data-quality" / "index.html").exists()

    def test_thin_tags_get_noindex(self, tmp_dist, mock_render, ctx_base):
        from core.build_taxonomies import generate_tag_pages

        tag_items = {"lonely": [_dummy_content("test/item-1", "research", "data-engineering")]}
        generate_tag_pages(tmp_dist, tag_items, mock_render, ctx_base, _dummy_obj)

        thin_call = None
        for call in mock_render.call_args_list:
            kwargs = call[1] if len(call) > 1 else {}
            if kwargs.get("robots_noindex"):
                thin_call = kwargs
        assert thin_call is not None, "Expected a call with robots_noindex=True"


# ── Admin Pages ──


class TestGenerateAdminPages:
    def test_generates_all_admin_pages(self, tmp_dist, mock_render, ctx_base):
        from core.build_taxonomies import generate_admin_pages

        items = _make_items(20)
        static_dir = tmp_dist / "static"
        static_dir.mkdir(parents=True, exist_ok=True)

        pages = generate_admin_pages(tmp_dist, items, static_dir, mock_render, ctx_base, _dummy_obj)

        assert pages > 0
        expected = [
            "login", "dashboard", "gallery", "articles", "manifest",
            "pipeline", "quality", "coverage", "sources", "telemetry",
        ]
        for name in expected:
            assert (tmp_dist / "admin" / f"{name}.html").exists(), f"Missing admin/{name}.html"
        # ontology page requires ontology arg to be passed

    def test_admin_pages_use_render_template(self, tmp_dist, mock_render, ctx_base):
        from core.build_taxonomies import generate_admin_pages

        items = _make_items(5)
        static_dir = tmp_dist / "static"
        static_dir.mkdir(parents=True, exist_ok=True)

        generate_admin_pages(tmp_dist, items, static_dir, mock_render, ctx_base, _dummy_obj)
        assert mock_render.call_count >= 10


# ── Search Pages ──


class TestGenerateSearchPages:
    def test_generates_search_index_json(self, tmp_dist, mock_render, ctx_base):
        from core.build_taxonomies import generate_search_pages

        items = _make_items(10)
        static_dir = tmp_dist / "static"
        static_dir.mkdir(parents=True, exist_ok=True)

        pages = generate_search_pages(tmp_dist, static_dir, items, mock_render, ctx_base, _dummy_obj)
        assert pages > 0

        idx_path = static_dir / "search-index.json"
        assert idx_path.exists()
        idx = json.loads(idx_path.read_text(encoding="utf-8"))
        assert len(idx) == 10
        assert all("slug" in e for e in idx)
        assert all("title" in e for e in idx)

    def test_search_index_has_correct_fields(self, tmp_dist, mock_render, ctx_base):
        from core.build_taxonomies import generate_search_pages

        items = _make_items(3)
        static_dir = tmp_dist / "static"
        static_dir.mkdir(parents=True, exist_ok=True)

        generate_search_pages(tmp_dist, static_dir, items, mock_render, ctx_base, _dummy_obj)

        idx = json.loads((static_dir / "search-index.json").read_text(encoding="utf-8"))
        entry = idx[0]
        assert "slug" in entry
        assert "title" in entry
        assert "pillar" in entry
        assert "content_type" in entry
        assert "tags" in entry
        assert "description" in entry

    def test_search_index_handles_empty_items(self, tmp_dist, mock_render, ctx_base):
        from core.build_taxonomies import generate_search_pages

        static_dir = tmp_dist / "static"
        static_dir.mkdir(parents=True, exist_ok=True)

        pages = generate_search_pages(tmp_dist, static_dir, [], mock_render, ctx_base, _dummy_obj)
        assert pages >= 1  # search page + optionally search index

        idx = json.loads((static_dir / "search-index.json").read_text(encoding="utf-8"))
        assert idx == []

    def test_search_page_rendered(self, tmp_dist, mock_render, ctx_base):
        from core.build_taxonomies import generate_search_pages

        static_dir = tmp_dist / "static"
        static_dir.mkdir(parents=True, exist_ok=True)

        generate_search_pages(tmp_dist, static_dir, _make_items(3), mock_render, ctx_base, _dummy_obj)
        assert (tmp_dist / "search" / "index.html").exists()


# ── Feed ──


class TestGenerateFeed:
    def test_generates_feed_xml(self, tmp_dist, mock_render, ctx_base):
        from core.build_taxonomies import generate_feed

        items = _make_items(5)
        pages = generate_feed(tmp_dist, items, mock_render, ctx_base)
        assert pages == 1
        assert (tmp_dist / "feed.xml").exists()

    def test_feed_handles_empty_items(self, tmp_dist, mock_render, ctx_base):
        from core.build_taxonomies import generate_feed

        pages = generate_feed(tmp_dist, [], mock_render, ctx_base)
        assert pages == 1
        assert (tmp_dist / "feed.xml").exists()

    def test_feed_render_called(self, tmp_dist, mock_render, ctx_base):
        from core.build_taxonomies import generate_feed

        generate_feed(tmp_dist, _make_items(5), mock_render, ctx_base)
        feed_file = tmp_dist / "feed.xml"
        assert feed_file.exists()
        content = feed_file.read_text(encoding="utf-8")
        assert '<?xml version="1.0"' in content
        assert "<feed" in content

    def test_feed_content_is_xml(self, tmp_dist, mock_render, ctx_base):
        from core.build_taxonomies import generate_feed

        mock_render.return_value = '<?xml version="1.0" encoding="utf-8"?><feed></feed>'
        generate_feed(tmp_dist, _make_items(3), mock_render, ctx_base)
        content = (tmp_dist / "feed.xml").read_text(encoding="utf-8")
        assert "<?xml" in content


# ── Pillar Pages ──


class TestGeneratePillarPages:
    def _pillar_groups(self, items):
        groups = {"compliance": [], "markets": [], "data": []}
        for i in items:
            p = {"aml": "compliance", "stock": "markets", "data-engineering": "data"}.get(i.pillar, "data")
            groups[p].append(i)
        return groups

    def test_generates_pillar_index_pages(self, tmp_dist, mock_render, ctx_base):
        from core.build_taxonomies import generate_pillar_pages

        groups = self._pillar_groups(_make_items(10))
        pages = generate_pillar_pages(tmp_dist, groups, mock_render, ctx_base)
        assert pages >= 3
        assert (tmp_dist / "compliance" / "index.html").exists()
        assert (tmp_dist / "markets" / "index.html").exists()
        assert (tmp_dist / "data" / "index.html").exists()

    def test_pillar_page_render_called(self, tmp_dist, mock_render, ctx_base):
        from core.build_taxonomies import generate_pillar_pages

        groups = self._pillar_groups(_make_items(15))
        generate_pillar_pages(tmp_dist, groups, mock_render, ctx_base)
        assert mock_render.call_count >= 3


# ── Integration with Live Data ──


class TestLiveBuildTaxonomies:
    def test_tag_pages_generate_with_live_registry(self, tmp_dist, mock_render, ctx_base, project_root):
        from core.build_taxonomies import generate_tag_pages

        registry_path = project_root / "registry.json"
        if not registry_path.exists():
            pytest.skip("registry.json not found")

        raw = json.loads(registry_path.read_text(encoding="utf-8"))
        items = raw.get("content", [])

        from collections import defaultdict
        tag_items = defaultdict(list)
        for item in items[:50]:
            tags = item.get("tags", [])
            if isinstance(tags, list):
                for tag in tags:
                    tag_items[tag].append(item)

        count = generate_tag_pages(tmp_dist, dict(tag_items), mock_render, ctx_base, _dummy_obj)
        assert count > 0

    def test_search_index_with_live_registry(self, tmp_dist, mock_render, ctx_base, project_root):
        from core.build_taxonomies import generate_search_pages

        registry_path = project_root / "registry.json"
        if not registry_path.exists():
            pytest.skip("registry.json not found")

        raw = json.loads(registry_path.read_text(encoding="utf-8"))
        raw_items = raw.get("content", [])
        # Convert to SimpleNamespace (generate_search_pages uses getattr for attribute access)
        items = [_to_obj(i) for i in raw_items]

        static_dir = tmp_dist / "static"
        static_dir.mkdir(parents=True, exist_ok=True)

        generate_search_pages(tmp_dist, static_dir, items, mock_render, ctx_base, _dummy_obj)

        idx = json.loads((static_dir / "search-index.json").read_text(encoding="utf-8"))
        assert len(idx) > 0
        for entry in idx:
            assert "slug" in entry
            assert "title" in entry
            assert "content_type" in entry


# ── _compute_* Helper Functions ──


class TestComputeDashboardStats:
    def test_empty_content(self):
        from core.build_taxonomies import _compute_dashboard_stats

        stats = _compute_dashboard_stats([])
        assert stats["total_articles"] == 0
        assert stats["with_images"] == 0
        assert stats["with_images_pct"] == 0
        assert stats["low_score"] == 0

    def test_counts_articles_with_images(self):
        from types import SimpleNamespace

        from core.build_taxonomies import _compute_dashboard_stats

        items = [
            SimpleNamespace(slug="a", signals={}, content_type="research", featured_image="img.jpg", source_breakdown={}),
            SimpleNamespace(slug="b", signals={}, content_type="learn", featured_image=None, source_breakdown={}),
            SimpleNamespace(slug="c", signals={"avg_score": 50}, content_type="research", featured_image=None, source_breakdown={}),
        ]
        stats = _compute_dashboard_stats(items)
        assert stats["total_articles"] == 3
        assert stats["with_images"] == 1
        assert stats["without_images"] == 2
        assert stats["low_score"] == 1

    def test_by_type_breakdown(self):
        from types import SimpleNamespace

        from core.build_taxonomies import _compute_dashboard_stats

        items = [
            SimpleNamespace(slug="a", signals={}, content_type="research", featured_image="img.jpg", source_breakdown={}),
            SimpleNamespace(slug="b", signals={}, content_type="research", featured_image=None, source_breakdown={}),
            SimpleNamespace(slug="c", signals={}, content_type="learn", featured_image="img.jpg", source_breakdown={}),
        ]
        stats = _compute_dashboard_stats(items)
        by_type = {t["type"]: t for t in stats["by_type"]}
        assert by_type["research"]["total"] == 2
        assert by_type["research"]["with_images"] == 1
        assert by_type["learn"]["total"] == 1
        assert by_type["learn"]["with_images"] == 1


class TestComputeQualityStats:
    def test_empty_content(self):
        from core.build_taxonomies import _compute_quality_stats

        qstats = _compute_quality_stats([])
        assert qstats["total_scores"] == 0
        assert qstats["avg_score"] == 0

    def test_scores_from_section_images(self):
        from types import SimpleNamespace

        from core.build_taxonomies import _compute_quality_stats

        items = [
            SimpleNamespace(
                slug="a", content_type="research",
                section_images=[
                    {"relevance_score": 85, "source_api": "unsplash", "section_index": 0},
                    {"relevance_score": 70, "source_api": "unsplash", "section_index": 1},
                ],
            ),
            SimpleNamespace(
                slug="b", content_type="learn",
                section_images=[
                    {"relevance_score": 45, "source_api": "pexels", "section_index": 0},
                ],
            ),
        ]
        qstats = _compute_quality_stats(items)
        assert qstats["total_scores"] == 3
        assert qstats["avg_score"] == pytest.approx((85 + 70 + 45) / 3, 0.1)
        assert qstats["above_70"] == 2
        assert qstats["below_40"] == 0

    def test_bucket_distribution(self):
        from types import SimpleNamespace

        from core.build_taxonomies import _compute_quality_stats

        items = [
            SimpleNamespace(
                slug="a", content_type="research",
                section_images=[{"relevance_score": s, "source_api": "unsplash", "section_index": 0}],
            )
            for s in [5, 15, 25, 35, 45, 55, 65, 75, 85, 95]
        ]
        qstats = _compute_quality_stats(items)
        assert sum(b > 0 for b in qstats["buckets"]) >= 8
        assert qstats["source_avgs"]["unsplash"] > 0


class TestComputeCoverageData:
    def test_empty_content(self):
        from core.build_taxonomies import _compute_coverage_data

        cov = _compute_coverage_data([], {})
        assert cov["heatmap"] == {}
        assert cov["by_pillar"] == {}
        assert cov["by_type"] == {}

    def test_coverage_counts(self):
        from types import SimpleNamespace

        from core.build_taxonomies import _compute_coverage_data

        items = [
            SimpleNamespace(
                slug="a", pillar="aml", content_type="research",
                section_images=[
                    {"section_index": 0, "image_url": "img1.jpg"},
                    {"section_index": 1, "image_url": ""},
                ],
            ),
            SimpleNamespace(
                slug="b", pillar="aml", content_type="research",
                section_images=[{"section_index": 0, "image_url": "img2.jpg"}],
            ),
        ]
        section_types = {0: "overview", 1: "key_findings"}
        cov = _compute_coverage_data(items, section_types)
        assert cov["by_pillar"]["aml"]["filled"] == 2
        assert cov["by_pillar"]["aml"]["total"] == 3
        assert cov["by_type"]["research"]["filled"] == 2
        assert cov["by_type"]["research"]["total"] == 3


class TestComputeSQITelemetry:
    def test_empty_content(self):
        from core.build_taxonomies import _compute_sqi_telemetry

        sqi = _compute_sqi_telemetry([])
        assert sqi["count"] == 0
        assert sqi["avg"] == 0

    def test_sqi_from_direct_attr(self):
        from types import SimpleNamespace

        from core.build_taxonomies import _compute_sqi_telemetry

        items = [
            SimpleNamespace(slug="a", sqi=0.9, signals={}, pillar="aml", content_type="research"),
            SimpleNamespace(slug="b", sqi=0.5, signals={}, pillar="aml", content_type="research"),
            SimpleNamespace(slug="c", sqi=0.1, signals={}, pillar="stock", content_type="learn"),
            SimpleNamespace(slug="d", sqi=0.3, signals={}, pillar="stock", content_type="learn"),
        ]
        sqi = _compute_sqi_telemetry(items)
        assert sqi["count"] == 4
        assert sqi["avg"] == pytest.approx((0.9 + 0.5 + 0.1 + 0.3) / 4, 0.01)
        assert sqi["above_08"] == 1
        assert sqi["below_05"] == 2

    def test_sqi_falls_back_to_signals(self):
        from types import SimpleNamespace

        from core.build_taxonomies import _compute_sqi_telemetry

        items = [
            SimpleNamespace(slug="a", sqi=None, signals={"avg_sqi": 0.75}, pillar="aml", content_type="research"),
        ]
        sqi = _compute_sqi_telemetry(items)
        assert sqi["count"] == 1
        assert sqi["avg"] == pytest.approx(0.75, 0.01)

    def test_sqi_clamps(self):
        from types import SimpleNamespace

        from core.build_taxonomies import _compute_sqi_telemetry

        items = [
            SimpleNamespace(slug="a", sqi=-0.5, signals={}, pillar="aml", content_type="research"),
            SimpleNamespace(slug="b", sqi=1.5, signals={}, pillar="aml", content_type="research"),
        ]
        sqi = _compute_sqi_telemetry(items)
        assert sqi["min"] == 0.0
        assert sqi["max"] == 1.0


class TestComputeTagTelemetry:
    def test_empty_content(self):
        from core.build_taxonomies import _compute_tag_telemetry

        tel = _compute_tag_telemetry([])
        assert tel["total_tags"] == 0
        assert tel["total_assignments"] == 0

    def test_tag_counts_and_crossover(self):
        from types import SimpleNamespace

        from core.build_taxonomies import _compute_tag_telemetry

        items = [
            SimpleNamespace(slug="a", tags=["aml", "kyc"], pillar="aml", content_type="research", date_str="2026-01-01"),
            SimpleNamespace(slug="b", tags=["aml", "data"], pillar="data-engineering", content_type="learn", date_str="2026-01-02"),
            SimpleNamespace(slug="c", tags=["kyc"], pillar="aml", content_type="knowledge", date_str="2026-01-03"),
        ]
        tel = _compute_tag_telemetry(items)
        assert tel["total_tags"] == 3
        assert tel["total_assignments"] == 5
        assert "aml" in tel["crossover_tags"]  # appears in 2 pillars

    def test_cooccurrence(self):
        from types import SimpleNamespace

        from core.build_taxonomies import _compute_tag_telemetry

        items = [
            SimpleNamespace(slug="a", tags=["a", "b"], pillar="aml", content_type="research", date_str=""),
            SimpleNamespace(slug="b", tags=["a", "b", "c"], pillar="aml", content_type="research", date_str=""),
        ]
        tel = _compute_tag_telemetry(items)
        assert len(tel["cooccurrence_edges"]) >= 1


class TestComputeEnrichmentTelemetry:
    def test_empty_content(self):
        from core.build_taxonomies import _compute_enrichment_telemetry

        enr = _compute_enrichment_telemetry([])
        assert enr["total_enriched"] == 0

    def test_counts_enriched_items(self):
        from types import SimpleNamespace

        from core.build_taxonomies import _compute_enrichment_telemetry

        items = [
            SimpleNamespace(slug="a", tags=["a", "b", "c", "d"], enriched=True),
            SimpleNamespace(slug="b", tags=["x"], enriched=False),
            SimpleNamespace(slug="c", tags=["p", "q"], enriched=True, enriched_at="2026-01-01"),
        ]
        enr = _compute_enrichment_telemetry(items)
        assert enr["total_enriched"] == 2


class TestComputeVelocityTelemetry:
    def test_empty_content(self):
        from core.build_taxonomies import _compute_velocity_telemetry

        vel = _compute_velocity_telemetry([])
        assert vel["total_months"] == 0

    def test_monthly_grouping(self):
        from datetime import datetime, timezone
        from types import SimpleNamespace

        from core.build_taxonomies import _compute_velocity_telemetry

        items = [
            SimpleNamespace(slug="a", created_at=datetime(2026, 1, 15, tzinfo=timezone.utc)),
            SimpleNamespace(slug="b", created_at=datetime(2026, 1, 20, tzinfo=timezone.utc)),
            SimpleNamespace(slug="c", created_at=datetime(2026, 2, 1, tzinfo=timezone.utc)),
        ]
        vel = _compute_velocity_telemetry(items)
        assert vel["total_months"] == 2
        months = {m["period"]: m["count"] for m in vel["monthly"]}
        assert months["2026-01"] == 2
        assert months["2026-02"] == 1


class TestComputeSourceTelemetry:
    def test_empty_content(self):
        from core.build_taxonomies import _compute_source_telemetry

        src = _compute_source_telemetry([])
        assert src["items_with_sources"] == 0

    def test_source_counts(self):
        from types import SimpleNamespace

        from core.build_taxonomies import _compute_source_telemetry

        items = [
            SimpleNamespace(slug="a", source_breakdown={"arxiv": 1, "hn": 2}, pillar="aml"),
            SimpleNamespace(slug="b", source_breakdown={}, pillar="stock"),
            SimpleNamespace(slug="c", source_breakdown={"arxiv": 1}, pillar="aml"),
        ]
        src = _compute_source_telemetry(items)
        assert src["items_with_sources"] == 2
        assert src["items_wo_sources"] == 1
        assert src["source_totals"]["arxiv"] == 2
        assert src["source_totals"]["hn"] == 2


class TestComputeTelemetry:
    def test_aggregates_all_sub_telemetry(self):
        from datetime import datetime, timezone
        from types import SimpleNamespace

        from core.build_taxonomies import _compute_telemetry

        items = [
            SimpleNamespace(
                slug="a", sqi=0.8, signals={}, pillar="aml", content_type="research",
                tags=["aml"], source_breakdown={"arxiv": 1}, enriched=True,
                created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
                section_images=[],
            ),
        ]
        tel = _compute_telemetry(items)
        assert "tag" in tel
        assert "sqi" in tel
        assert "enrichment" in tel
        assert "velocity" in tel
        assert "source" in tel
        assert tel["sqi"]["count"] == 1
        assert tel["tag"]["total_tags"] == 1


# ── Performance ──


class TestBuildTaxonomiesPerformance:
    def test_admin_page_generation_speed(self, tmp_dist, mock_render, ctx_base):
        import time

        from core.build_taxonomies import generate_admin_pages

        items = _make_items(200)
        static_dir = tmp_dist / "static"
        static_dir.mkdir(parents=True, exist_ok=True)

        start = time.perf_counter()
        pages = generate_admin_pages(tmp_dist, items, static_dir, mock_render, ctx_base, _dummy_obj)
        elapsed = time.perf_counter() - start

        assert pages > 0
        assert elapsed < 5.0, f"Admin generation too slow: {elapsed:.2f}s"

    def test_tag_generation_speed(self, tmp_dist, mock_render, ctx_base):
        import time

        from core.build_taxonomies import generate_tag_pages

        tag_items = {}
        for i in range(50):
            n_items = (i % 5) + 1
            tag_items[f"tag-{i}"] = [_dummy_content(f"test/item-{i}-{j}", "research", "data-engineering") for j in range(n_items)]

        start = time.perf_counter()
        count = generate_tag_pages(tmp_dist, tag_items, mock_render, ctx_base, _dummy_obj)
        elapsed = time.perf_counter() - start

        assert count > 0
        assert elapsed < 3.0, f"Tag generation too slow: {elapsed:.2f}s"
