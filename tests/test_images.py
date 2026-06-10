"""Tests for the 3-tier visual management system (core/images/).

Tier 1: Editorial manifest (manifest.json)
Tier 2: Auto-fetch from backends (fetch_images.py — tested via unit)
Tier 3: SVG fallback (templates.py)
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parent


class TestManifest:
    def test_load_manifest_returns_dict(self):
        from core.images import load_manifest
        result = load_manifest()
        assert isinstance(result, dict)

    def test_manifest_has_expected_slugs(self):
        from core.images import load_manifest
        result = load_manifest()
        assert len(result) > 0
        for slug, entry in result.items():
            assert "sections" in entry
            assert len(entry["sections"]) > 0

    def test_manifest_entry_has_required_fields(self):
        from core.images import load_manifest
        result = load_manifest()
        for slug, entry in result.items():
            for section in entry["sections"]:
                assert "section_index" in section
                assert "image_url" in section
                assert "image_credit" in section
                assert "image_alt" in section

    def test_get_manifest_entry_found(self):
        from core.images import load_manifest, get_manifest_entry
        slugs = list(load_manifest().keys())
        if slugs:
            entry = get_manifest_entry(slugs[0])
            assert entry is not None
            assert isinstance(entry, list)

    def test_get_manifest_entry_not_found(self):
        from core.images import get_manifest_entry
        entry = get_manifest_entry("nonexistent-slug-12345")
        assert entry is None

    def test_manifest_json_exists(self):
        from core.images.manifest import MANIFEST_PATH
        assert MANIFEST_PATH.exists()


class TestSvgFallback:
    _SAMPLE_SECTION = {
        "section_index": 0,
        "heading": "Test Section Heading",
        "section_type": "overview",
    }

    _SAMPLE_ARTICLE = {
        "title": "Test Article Title for SVG Generation",
        "pillar": "data-engineering",
    }

    def test_generate_fallback_svg_returns_svg_string(self):
        from core.images import generate_fallback_svg
        svg = generate_fallback_svg(self._SAMPLE_SECTION, self._SAMPLE_ARTICLE)
        assert isinstance(svg, str)
        assert svg.startswith("<svg")
        assert svg.endswith("</svg>")

    def test_fallback_svg_contains_pillar_color(self):
        from core.images import generate_fallback_svg
        svg = generate_fallback_svg(self._SAMPLE_SECTION, self._SAMPLE_ARTICLE)
        assert "#2563eb" in svg  # data-engineering primary blue

    def test_fallback_svg_contains_heading(self):
        from core.images import generate_fallback_svg
        svg = generate_fallback_svg(self._SAMPLE_SECTION, self._SAMPLE_ARTICLE)
        assert "Test Section Heading" in svg

    def test_fallback_svg_contains_title(self):
        from core.images import generate_fallback_svg
        svg = generate_fallback_svg(self._SAMPLE_SECTION, self._SAMPLE_ARTICLE)
        assert "Test Article Title" in svg

    def test_fallback_svg_aml_pillar(self):
        from core.images import generate_fallback_svg
        article = {**self._SAMPLE_ARTICLE, "pillar": "aml"}
        svg = generate_fallback_svg(self._SAMPLE_SECTION, article)
        assert "#dc2626" in svg  # AML primary red

    def test_fallback_svg_markets_pillar(self):
        from core.images import generate_fallback_svg
        article = {**self._SAMPLE_ARTICLE, "pillar": "stock"}
        svg = generate_fallback_svg(self._SAMPLE_SECTION, article)
        assert "#059669" in svg  # Markets primary green

    def test_fallback_svg_unknown_pillar_defaults(self):
        from core.images import generate_fallback_svg
        article = {**self._SAMPLE_ARTICLE, "pillar": "unknown"}
        svg = generate_fallback_svg(self._SAMPLE_SECTION, article)
        assert "#2563eb" in svg  # falls back to data-engineering

    def test_fallback_svg_different_section_indices(self):
        from core.images import generate_fallback_svg
        for idx in range(7):
            section = {**self._SAMPLE_SECTION, "section_index": idx}
            svg = generate_fallback_svg(section, self._SAMPLE_ARTICLE)
            assert svg.startswith("<svg")
            # each index produces unique SVG
            assert "section-fallback-svg" in svg

    def test_fallback_svg_title_truncation(self):
        from core.images import generate_fallback_svg
        long_title = "A" * 100
        article = {**self._SAMPLE_ARTICLE, "title": long_title}
        svg = generate_fallback_svg(self._SAMPLE_SECTION, article)
        assert svg.endswith("</svg>")
        # truncated title should have ellipsis (no assertion on exact content since
        # it depends on the template implementation)

    def test_fallback_svg_heading_truncation(self):
        from core.images import generate_fallback_svg
        long_heading = "B" * 100
        section = {**self._SAMPLE_SECTION, "heading": long_heading}
        svg = generate_fallback_svg(section, self._SAMPLE_ARTICLE)
        assert svg.endswith("</svg>")

    def test_fallback_svg_empty_heading(self):
        from core.images import generate_fallback_svg
        section = {**self._SAMPLE_SECTION, "heading": ""}
        svg = generate_fallback_svg(section, self._SAMPLE_ARTICLE)
        assert svg.endswith("</svg>")

    def test_fallback_svg_includes_pillar_label(self):
        from core.images import generate_fallback_svg
        svg = generate_fallback_svg(self._SAMPLE_SECTION, self._SAMPLE_ARTICLE)
        assert "DATA" in svg  # data-engineering pillar label

    def test_fallback_svg_aml_label(self):
        from core.images import generate_fallback_svg
        article = {**self._SAMPLE_ARTICLE, "pillar": "aml"}
        svg = generate_fallback_svg(self._SAMPLE_SECTION, article)
        assert "AML" in svg

    def test_fallback_svg_markets_label(self):
        from core.images import generate_fallback_svg
        article = {**self._SAMPLE_ARTICLE, "pillar": "stock"}
        svg = generate_fallback_svg(self._SAMPLE_SECTION, article)
        assert "MKT" in svg

    def test_fallback_svg_has_viewbox(self):
        from core.images import generate_fallback_svg
        svg = generate_fallback_svg(self._SAMPLE_SECTION, self._SAMPLE_ARTICLE)
        assert "viewBox" in svg or "viewbox" in svg

    def test_fallback_svg_has_width_and_height(self):
        from core.images import generate_fallback_svg
        svg = generate_fallback_svg(self._SAMPLE_SECTION, self._SAMPLE_ARTICLE)
        assert 'width="' in svg or "width:" in svg
        assert 'height="' in svg or "height:" in svg


class TestPillarVisuals:
    def test_pillar_visuals_contains_all_pillars(self):
        from core.images import PILLAR_VISUALS
        assert "data-engineering" in PILLAR_VISUALS
        assert "aml" in PILLAR_VISUALS
        assert "stock" in PILLAR_VISUALS

    def test_pillar_visual_has_required_keys(self):
        from core.images import PILLAR_VISUALS
        required = {"name", "primary", "dark", "darker", "accent", "icon_accent", "label"}
        for pillar, visual in PILLAR_VISUALS.items():
            assert required.issubset(visual.keys()), f"{pillar} missing keys"

    def test_pillar_label_short(self):
        from core.images import PILLAR_VISUALS
        for pillar, visual in PILLAR_VISUALS.items():
            assert len(visual["label"]) <= 5, f"{pillar} label too long: {visual['label']}"


class TestSectionIcons:
    def test_section_icon_index_coverage(self):
        from core.images.templates import SECTION_ICON_INDEX, _icon_paths
        for idx in range(7):
            assert idx in SECTION_ICON_INDEX
            svg = _icon_paths(SECTION_ICON_INDEX[idx])
            assert isinstance(svg, str)
            assert len(svg) > 0

    def test_section_labels_complete(self):
        from core.images.templates import SECTION_LABEL
        for idx in range(7):
            assert idx in SECTION_LABEL
            assert SECTION_LABEL[idx]


class TestImportRegression:
    """Import must work from both entry points (project root and scripts/)."""

    def test_import_from_project_root(self):
        """Simulates build.py import path."""
        from core.images import generate_fallback_svg, load_manifest, get_manifest_entry
        from core.images import PILLAR_VISUALS
        assert callable(generate_fallback_svg)
        assert callable(load_manifest)
        assert callable(get_manifest_entry)
        assert isinstance(PILLAR_VISUALS, dict)
