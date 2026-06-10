"""Tests for core.brand — brand visual system SVG generators."""

import re
import pytest

from core.brand import (
    BRAND,
    NEUTRAL,
    PILLAR_MAP,
    _brand_key,
    brand_logo_svg,
    brand_domain_icon,
    brand_micro_icon,
    brand_pattern,
    brand_sparkline,
    brand_section_icon,
    SECTION_ICONS,
    _MICRO_ICONS,
)


# ── Color Tokens ──

class TestBrandTokens:
    def test_all_three_pillars_defined(self):
        assert "aml" in BRAND
        assert "markets" in BRAND
        assert "science" in BRAND

    def test_pillar_has_required_keys(self):
        for key in ("aml", "markets", "science"):
            for field in ("primary", "secondary", "dark", "darker", "accent", "label"):
                assert field in BRAND[key], f"{key} missing {field}"

    def test_colors_are_valid_hex(self):
        hex_re = re.compile(r"^#[0-9a-fA-F]{6}$")
        for key, palette in BRAND.items():
            for field, val in palette.items():
                if field != "label":
                    assert hex_re.match(val), f"{key}.{field} = {val} is not valid hex"

    def test_pillar_map_covers_all(self):
        assert PILLAR_MAP["aml"] == "aml"
        assert PILLAR_MAP["stock"] == "markets"
        assert PILLAR_MAP["data-engineering"] == "science"

    def test_brand_key_fallback(self):
        assert _brand_key("aml") == "aml"
        assert _brand_key("stock") == "markets"
        assert _brand_key("unknown") == "unknown"


# ── Logo ──

class TestBrandLogo:
    def test_returns_valid_svg(self):
        svg = brand_logo_svg(48)
        assert svg.startswith("<svg")
        assert "viewBox=\"0 0 48 48\"" in svg
        assert svg.endswith("</svg>")

    def test_custom_size(self):
        svg = brand_logo_svg(96)
        assert 'width="96"' in svg
        assert 'height="96"' in svg

    def test_custom_color(self):
        svg = brand_logo_svg(48, color="#ff0000")
        assert "#ff0000" in svg

    def test_contains_leaf_and_nodes(self):
        svg = brand_logo_svg(48)
        # Leaf paths
        assert "fill=\"url(#leaf)\"" in svg
        # Node circles
        assert "<circle" in svg
        # Edges
        assert "<line" in svg


# ── Domain Icons ──

class TestBrandDomainIcon:
    @pytest.mark.parametrize("pillar", ["aml", "stock", "data-engineering"])
    def test_returns_valid_svg(self, pillar):
        svg = brand_domain_icon(pillar, 24)
        assert svg.startswith("<svg")
        assert "viewBox=\"0 0 24 24\"" in svg
        assert svg.endswith("</svg>")

    def test_aml_has_shield(self):
        svg = brand_domain_icon("aml", 24)
        assert "<path" in svg  # Shield outline
        assert "<circle" in svg  # Network nodes

    def test_markets_has_chart(self):
        svg = brand_domain_icon("stock", 24)
        assert "<polyline" in svg  # Line chart

    def test_science_has_neuron(self):
        svg = brand_domain_icon("data-engineering", 24)
        assert "<circle" in svg  # Soma
        assert "<path" in svg  # Dendrites

    def test_custom_size(self):
        svg = brand_domain_icon("aml", 48)
        assert 'width="48"' in svg

    def test_custom_color(self):
        svg = brand_domain_icon("aml", 24, color="#ff0000")
        assert "#ff0000" in svg


# ── Micro-icons ──

class TestBrandMicroIcon:
    @pytest.mark.parametrize("name", list(_MICRO_ICONS.keys()))
    def test_returns_valid_svg(self, name):
        svg = brand_micro_icon(name, 16)
        assert svg.startswith("<svg")
        assert "viewBox=\"0 0 16 16\"" in svg
        assert svg.endswith("</svg>")

    def test_all_nine_icons_exist(self):
        expected = {"time", "source", "difficulty", "domain", "version",
                    "tags", "link", "calendar", "chart"}
        assert set(_MICRO_ICONS.keys()) == expected

    def test_custom_size(self):
        svg = brand_micro_icon("time", 20)
        assert 'width="20"' in svg

    def test_unknown_icon_falls_back_to_time(self):
        svg = brand_micro_icon("nonexistent", 16)
        # Should return the time icon
        assert svg.startswith("<svg")
        assert "circle" in svg  # Clock face


# ── Domain Patterns ──

class TestBrandPattern:
    @pytest.mark.parametrize("pillar", ["aml", "stock", "data-engineering"])
    def test_returns_valid_svg(self, pillar):
        svg = brand_pattern(pillar, 100, 100)
        assert svg.startswith("<svg")
        assert svg.endswith("</svg>")

    def test_aml_has_hexagons(self):
        svg = brand_pattern("aml", 100, 100)
        assert "<polygon" in svg  # Hexagonal mesh

    def test_markets_has_waves(self):
        svg = brand_pattern("stock", 100, 100)
        assert "<polyline" in svg  # Sine waves

    def test_science_has_branches(self):
        svg = brand_pattern("data-engineering", 100, 100)
        assert "<line" in svg  # Branching L-system

    def test_custom_dimensions(self):
        svg = brand_pattern("aml", 300, 200)
        assert 'width="300"' in svg
        assert 'height="200"' in svg

    def test_opacity_affects_output(self):
        svg_low = brand_pattern("aml", 100, 100, opacity=0.01)
        svg_high = brand_pattern("aml", 100, 100, opacity=0.5)
        # Both should produce valid SVGs with different opacity values
        assert 'opacity="0.01"' in svg_low
        assert 'opacity="0.5"' in svg_high


# ── Sparklines ──

class TestBrandSparkline:
    def test_returns_valid_svg(self):
        svg = brand_sparkline([1, 3, 2, 5, 4], "aml")
        assert svg.startswith("<svg")
        assert svg.endswith("</svg>")

    def test_contains_line_and_fill(self):
        svg = brand_sparkline([1, 3, 2, 5, 4], "aml")
        assert "<polyline" in svg  # Line
        assert "<polygon" in svg  # Area fill

    def test_empty_data_returns_empty(self):
        assert brand_sparkline([], "aml") == ""
        assert brand_sparkline([5], "aml") == ""

    def test_custom_dimensions(self):
        svg = brand_sparkline([1, 3, 2], "aml", width=120, height=48)
        assert 'width="120"' in svg
        assert 'height="48"' in svg

    def test_no_fill_option(self):
        svg = brand_sparkline([1, 3, 2], "aml", show_fill=False)
        assert "<polygon" not in svg
        assert "<polyline" in svg

    @pytest.mark.parametrize("pillar", ["aml", "stock", "data-engineering"])
    def test_pillar_colors_used(self, pillar):
        svg = brand_sparkline([1, 3, 2], pillar)
        # Should contain the mapped brand key's primary color
        key = _brand_key(pillar)
        assert BRAND[key]["primary"].lower() in svg.lower()


# ── Section Icons ──

class TestBrandSectionIcon:
    @pytest.mark.parametrize("idx", range(7))
    def test_returns_valid_svg(self, idx):
        svg = brand_section_icon(idx, 24)
        assert svg.startswith("<svg")
        assert svg.endswith("</svg>")

    def test_all_seven_defined(self):
        assert len(SECTION_ICONS) == 7

    def test_unknown_index_falls_back(self):
        svg = brand_section_icon(99, 24)
        assert svg.startswith("<svg")


# ── Integration: Fallback SVG uses brand tokens ──

class TestFallbackIntegration:
    def test_fallback_contains_pattern(self):
        from core.images.templates import generate_fallback_svg
        section = {"section_index": 0, "heading": "Overview"}
        article = {"pillar": "aml", "title": "Test Article"}
        svg = generate_fallback_svg(section, article)
        # Should contain base64-encoded pattern
        assert "base64" in svg
        assert len(svg) > 5000  # Substantial SVG with pattern

    def test_fallback_all_pillars(self):
        from core.images.templates import generate_fallback_svg
        section = {"section_index": 1, "heading": "Findings"}
        for pillar in ("aml", "stock", "data-engineering"):
            article = {"pillar": pillar, "title": f"Article about {pillar}"}
            svg = generate_fallback_svg(section, article)
            assert len(svg) > 1000, f"Fallback SVG too small for {pillar}"
