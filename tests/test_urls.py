"""Tests for URL generation, pillar mapping, and slug translation."""

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import PILLAR_URL_MAP, PILLAR_URL_REVERSE
from core.urls import (
    canonical_path,
    pillar_to_url,
    slug_to_fspath,
    slug_to_path,
    slug_to_url,
    url_to_pillar,
)


class TestPillarUrlMap:
    """Tests for the canonical PILLAR_URL_MAP in config.py."""

    def test_all_three_pillars_mapped(self):
        assert set(PILLAR_URL_MAP.keys()) == {"aml", "stock", "data-engineering"}

    def test_aml_maps_to_compliance(self):
        assert PILLAR_URL_MAP["aml"] == "compliance"

    def test_stock_maps_to_markets(self):
        assert PILLAR_URL_MAP["stock"] == "markets"

    def test_data_engineering_maps_to_data(self):
        assert PILLAR_URL_MAP["data-engineering"] == "data"

    def test_reverse_map_is_consistent(self):
        for internal, url_seg in PILLAR_URL_MAP.items():
            assert PILLAR_URL_REVERSE[url_seg] == internal

    def test_reverse_map_keys_are_url_segments(self):
        assert set(PILLAR_URL_REVERSE.keys()) == {"compliance", "markets", "data"}


class TestPillarHelpers:
    """Tests for pillar_to_url() and url_to_pillar()."""

    @pytest.mark.parametrize("pillar,expected", [
        ("aml", "compliance"),
        ("stock", "markets"),
        ("data-engineering", "data"),
    ])
    def test_pillar_to_url(self, pillar, expected):
        assert pillar_to_url(pillar) == expected

    @pytest.mark.parametrize("url_seg,expected", [
        ("compliance", "aml"),
        ("markets", "stock"),
        ("data", "data-engineering"),
    ])
    def test_url_to_pillar(self, url_seg, expected):
        assert url_to_pillar(url_seg) == expected

    def test_round_trip_pillar_to_url_to_pillar(self):
        for pillar in PILLAR_URL_MAP:
            url_seg = pillar_to_url(pillar)
            assert url_to_pillar(url_seg) == pillar

    def test_round_trip_url_to_pillar_to_url(self):
        for url_seg in PILLAR_URL_REVERSE:
            pillar = url_to_pillar(url_seg)
            assert pillar_to_url(pillar) == url_seg

    def test_unknown_pillar_passthrough(self):
        assert pillar_to_url("unknown") == "unknown"

    def test_unknown_url_passthrough(self):
        assert url_to_pillar("unknown") == "unknown"


class TestSlugToFspath:
    """Tests for slug_to_fspath() — internal slug to filesystem path."""

    @pytest.mark.parametrize("slug,expected", [
        ("aml/research/foo", "compliance/research/foo"),
        ("aml/learn/foo", "compliance/learn/foo"),
        ("aml/knowledge/foo", "compliance/knowledge/foo"),
        ("stock/research/foo", "markets/research/foo"),
        ("data-engineering/research/foo", "data/research/foo"),
        ("knowledge/about", "knowledge/about"),
        ("knowledge/faq", "knowledge/faq"),
    ])
    def test_slug_to_fspath(self, slug, expected):
        assert slug_to_fspath(slug) == expected

    def test_flat_slug_unchanged(self):
        assert slug_to_fspath("just-a-slug") == "just-a-slug"


class TestCanonicalPath:
    """Tests for canonical_path() normalization."""

    def test_strips_index_html(self):
        assert canonical_path("foo/index.html") == "foo/"

    def test_strips_html(self):
        assert canonical_path("foo.html") == "foo/"

    def test_adds_trailing_slash(self):
        assert canonical_path("foo") == "foo/"

    def test_preserves_existing_slash(self):
        assert canonical_path("foo/") == "foo/"

    def test_nested_path(self):
        assert canonical_path("compliance/research/foo/index.html") == "compliance/research/foo/"


class TestSlugToUrl:
    """Tests for slug_to_url() full URL generation."""

    def test_aml_research_uses_compliance(self):
        url = slug_to_url("aml/research/foo")
        assert "/compliance/research/foo/" in url
        assert "/aml/" not in url

    def test_stock_research_uses_markets(self):
        url = slug_to_url("stock/research/foo")
        assert "/markets/research/foo/" in url

    def test_knowledge_platform_page_unchanged(self):
        url = slug_to_url("knowledge/about")
        assert url.endswith("/knowledge/about/")

    def test_url_starts_with_site_url(self):
        from config import SITE_URL
        url = slug_to_url("aml/research/foo")
        assert url.startswith(SITE_URL)


class TestSlugUniqueness:
    """Verify no two content items produce the same output path."""

    def test_no_duplicate_output_paths(self, full_registry):
        paths = set()
        dupes = []
        for item in full_registry["content"]:
            slug = item.get("slug", "")
            if not slug:
                continue
            fspath = slug_to_fspath(slug)
            out = slug_to_path(fspath)
            if out in paths:
                dupes.append(slug)
            paths.add(out)
        assert dupes == [], f"Duplicate output paths from slugs: {dupes}"
