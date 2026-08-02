"""Tests for core/brand.py — brand tokens, SVG asset generation, patterns, sparklines."""

import re

import pytest

from core.brand import (
    BRAND,
    NEUTRAL,
    PILLAR_MAP,
    brand_domain_icon,
    brand_logo_svg,
    brand_micro_icon,
    brand_pattern,
    brand_section_icon,
    brand_sparkline,
    section_type_color,
)

_SVG_TAG = re.compile(r"<svg[^>]*>")


# ── Brand tokens ──


class TestBrandTokens:
    def test_brand_has_all_pillars(self):
        for key in ("aml", "markets", "science"):
            assert key in BRAND
            for field in ("primary", "secondary", "dark", "darker", "accent", "label"):
                assert field in BRAND[key]

    def test_pillar_map_covers_content_slugs(self):
        for slug in ("aml", "stock", "data-engineering"):
            assert slug in PILLAR_MAP

    def test_neutral_tokens(self):
        for field in ("bg", "surface", "border", "text", "muted", "bone"):
            assert field in NEUTRAL

    def test_hex_colors_valid(self):
        hex_re = re.compile(r"^#[0-9a-fA-F]{6}$")
        for palette in BRAND.values():
            for v in palette.values():
                if v.startswith("#"):
                    assert hex_re.match(v), v


# ── Logo ──


class TestLogo:
    def test_logo_is_valid_svg(self):
        svg = brand_logo_svg()
        assert _SVG_TAG.search(svg)
        assert svg.startswith("<svg")
        assert svg.endswith("</svg>")

    def test_logo_size_respected(self):
        svg = brand_logo_svg(size=96)
        assert 'width="96"' in svg
        assert 'height="96"' in svg

    def test_logo_color_override(self):
        svg = brand_logo_svg(color="#ff0000")
        assert "#ff0000" in svg

    def test_logo_contains_leaf_and_nodes(self):
        svg = brand_logo_svg()
        assert "<path" in svg
        assert "<circle" in svg


# ── Domain icons ──


class TestDomainIcons:
    @pytest.mark.parametrize("pillar", ["aml", "stock", "data-engineering"])
    def test_domain_icon_pillars(self, pillar):
        svg = brand_domain_icon(pillar)
        assert _SVG_TAG.search(svg)
        assert 'viewBox="0 0 24 24"' in svg

    def test_domain_icon_unknown_pillar_falls_back(self):
        svg = brand_domain_icon("nope")
        assert _SVG_TAG.search(svg)

    def test_domain_icon_size(self):
        svg = brand_domain_icon("aml", size=48)
        assert 'width="48"' in svg

    def test_markets_icon_has_polyline(self):
        assert "<polyline" in brand_domain_icon("stock")

    def test_aml_icon_has_shield_path(self):
        svg = brand_domain_icon("aml")
        assert "M12 3L4 7" in svg

    def test_science_icon_has_circle(self):
        assert "<circle" in brand_domain_icon("data-engineering")


# ── Micro icons ──


class TestMicroIcons:
    @pytest.mark.parametrize(
        "name", ["time", "source", "difficulty", "domain", "version", "tags", "link", "calendar", "chart"]
    )
    def test_known_micro_icon(self, name):
        svg = brand_micro_icon(name)
        assert _SVG_TAG.search(svg)
        assert 'viewBox="0 0 16 16"' in svg

    def test_unknown_micro_icon_falls_back_to_time(self):
        a = brand_micro_icon("nope")
        b = brand_micro_icon("time")
        assert a == b

    def test_micro_icon_color(self):
        svg = brand_micro_icon("time", color="#123456")
        assert 'color="#123456"' in svg


# ── Patterns ──


class TestPatterns:
    @pytest.mark.parametrize("pillar", ["aml", "stock", "data-engineering"])
    def test_pattern_valid_svg(self, pillar):
        svg = brand_pattern(pillar)
        assert _SVG_TAG.search(svg)

    def test_pattern_size(self):
        svg = brand_pattern("stock", width=300, height=100)
        assert 'width="300"' in svg
        assert 'height="100"' in svg

    def test_pattern_contains_stroke(self):
        assert "stroke=" in brand_pattern("aml")

    def test_pattern_unknown_falls_back(self):
        assert "stroke=" in brand_pattern("nope")


# ── Sparklines ──


class TestSparklines:
    def test_empty_data_returns_empty(self):
        assert brand_sparkline([]) == ""
        assert brand_sparkline([1]) == ""

    def test_valid_svg(self):
        svg = brand_sparkline([1, 2, 3, 2, 4])
        assert _SVG_TAG.search(svg)
        assert "<polyline" in svg

    def test_flat_data_handled(self):
        svg = brand_sparkline([5, 5, 5, 5])
        assert _SVG_TAG.search(svg)

    def test_fill_optional(self):
        with_fill = brand_sparkline([1, 2, 3])
        without = brand_sparkline([1, 2, 3], show_fill=False)
        assert "<polygon" in with_fill
        assert "<polygon" not in without


# ── Section icons ──


class TestSectionIcons:
    def test_valid_svg(self):
        svg = brand_section_icon(3)
        assert _SVG_TAG.search(svg)

    def test_size(self):
        assert 'width="40"' in brand_section_icon(0, size=40)

    def test_color(self):
        assert 'fill="#ff0000"' in brand_section_icon(1, color="#ff0000")

    def test_unknown_index_falls_back(self):
        assert brand_section_icon(99) == brand_section_icon(0)

    def test_all_indexes_have_svg(self):
        for i in range(7):
            assert _SVG_TAG.search(brand_section_icon(i))


# ── Section colors ──


class TestSectionTypeColor:
    def test_returns_hex(self):
        assert section_type_color(0, "aml").startswith("#")

    def test_variation_across_types(self):
        colors = {section_type_color(i, "stock") for i in range(7)}
        assert len(colors) > 1

    def test_pillar_colors_differ(self):
        assert section_type_color(0, "aml") != section_type_color(0, "science")

    def test_unknown_type_falls_back(self):
        assert section_type_color(99, "aml").startswith("#")
