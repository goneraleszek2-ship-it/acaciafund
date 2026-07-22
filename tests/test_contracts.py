"""Contract tests — validate module interfaces conform to expected signatures.

MOSA Principle: Open interfaces with defined contracts.
Each test checks that a module exports what it promises (signatures, types, keys).
"""

import inspect

from config import (
    PILLAR_COLORS,
    PILLAR_CONFIG,
    PILLAR_EMOJIS,
    PILLAR_FINGERPRINT_COLORS,
    PILLAR_NAMES,
    PILLAR_SUBCATEGORIES,
    PILLAR_URL_MAP,
    PILLAR_URL_REVERSE,
)

# ── Config schema contract ──
#
# PILLAR_URL_MAP must be a complete bidirectional mapping of all pillars


class TestPillarUrlMapContract:
    def test_all_pillars_have_urls(self):
        expected = {"aml", "stock", "data-engineering"}
        assert set(PILLAR_URL_MAP.keys()) == expected

    def test_reverse_mapping_is_bijection(self):
        for k, v in PILLAR_URL_MAP.items():
            assert PILLAR_URL_REVERSE[v] == k
        assert len(PILLAR_URL_MAP) == len(PILLAR_URL_REVERSE)

    def test_urls_are_valid_path_segments(self):
        for url in PILLAR_URL_MAP.values():
            assert "/" not in url
            assert url.isascii()
            assert len(url) > 0


# PILLAR_CONFIG must have all 3 pillars with required keys


class TestPillarConfigContract:
    REQUIRED_KEYS = {"label", "url", "emoji", "color", "bg", "accent", "heading", "description"}

    def test_all_pillars_present(self):
        assert set(PILLAR_CONFIG.keys()) == {"aml", "stock", "data-engineering"}

    def test_each_pillar_has_all_required_keys(self):
        for pillar, cfg in PILLAR_CONFIG.items():
            missing = self.REQUIRED_KEYS - set(cfg.keys())
            assert not missing, f"{pillar} missing keys: {missing}"

    def test_urls_match_url_map(self):
        for pillar, cfg in PILLAR_CONFIG.items():
            assert cfg["url"] == PILLAR_URL_MAP[pillar]


# PILLAR_NAMES / PILLAR_EMOJIS must match PILLAR_CONFIG


class TestPillarDerivedDictsContract:
    def test_names_match_config_labels(self):
        for pillar in PILLAR_NAMES:
            assert PILLAR_NAMES[pillar] == PILLAR_CONFIG[pillar]["label"]

    def test_emojis_match_config(self):
        for pillar in PILLAR_EMOJIS:
            assert PILLAR_EMOJIS[pillar] == PILLAR_CONFIG[pillar]["emoji"]


# PILLAR_COLORS must have all 3 pillars with required color keys


class TestPillarColorsContract:
    REQUIRED_COLOR_KEYS = {"bg", "fg", "text", "accent"}

    def test_all_pillars_present(self):
        assert set(PILLAR_COLORS.keys()) == {"aml", "stock", "data-engineering"}

    def test_each_color_has_required_keys(self):
        for pillar, colors in PILLAR_COLORS.items():
            missing = self.REQUIRED_COLOR_KEYS - set(colors.keys())
            assert not missing, f"{pillar} missing color keys: {missing}"

    def test_values_are_valid_hex_colors(self):
        for pillar, colors in PILLAR_COLORS.items():
            for key, val in colors.items():
                assert val.startswith("#"), f"{pillar}.{key}={val!r} not a hex color"
                assert len(val) in (4, 7, 9), f"{pillar}.{key}={val!r} wrong length"


# PILLAR_FINGERPRINT_COLORS must cover all pillars + fallback


class TestFingerprintColorsContract:
    def test_all_pillars_plus_fallback(self):
        assert set(PILLAR_FINGERPRINT_COLORS.keys()) == {"aml", "stock", "data-engineering", ""}

    def test_values_are_hex_colors(self):
        for val in PILLAR_FINGERPRINT_COLORS.values():
            assert val.startswith("#")
            assert len(val) in (4, 7)


# PILLAR_SUBCATEGORIES must have all pillars with 12-15 subcategories


class TestPillarSubcategoriesContract:
    def test_all_pillars_present(self):
        assert set(PILLAR_SUBCATEGORIES.keys()) == {"aml", "stock", "data-engineering"}

    def test_each_pillar_has_12_to_15_subcategories(self):
        for pillar, cats in PILLAR_SUBCATEGORIES.items():
            n = len(cats)
            assert 12 <= n <= 15, f"{pillar} has {n} subcategories (expected 12-15)"

    def test_each_subcategory_has_required_fields(self):
        required = {"label", "icon", "description"}
        for pillar, cats in PILLAR_SUBCATEGORIES.items():
            for cat_name, cat_data in cats.items():
                missing = required - set(cat_data.keys())
                assert not missing, f"{pillar}/{cat_name} missing: {missing}"


# ── Module interface contracts ──
#
# Core modules must export expected functions with compatible signatures


class _Contract:
    """Helper: check that a module exports expected functions."""

    def __init__(self, module):
        self.module = module

    def exports(self, name: str) -> bool:
        return hasattr(self.module, name)

    def signature(self, name: str) -> inspect.Signature:
        return inspect.signature(getattr(self.module, name))

    def has_param(self, fn: str, param: str) -> bool:
        return param in self.signature(fn).parameters


# core/urls.py contract


class TestCoreUrlsContract:
    def test_exports_required_functions(self):
        from core import urls
        for fn in ("slug_to_path", "slug_to_fspath", "canonical_path", "slug_to_url", "pillar_to_url", "url_to_pillar"):
            assert hasattr(urls, fn), f"core.urls missing: {fn}"

    def test_pillar_to_url_is_bijection(self):
        from core.urls import pillar_to_url, url_to_pillar
        for pillar in ("aml", "stock", "data-engineering"):
            url = pillar_to_url(pillar)
            assert url_to_pillar(url) == pillar


# core/ontology.py contract


class TestCoreOntologyContract:
    def test_exports_required_classes(self):
        from core.ontology import Concept, OntologyManager, Relation, ResourceLink
        assert all(cls is not None for cls in [Concept, Relation, ResourceLink, OntologyManager])

    def test_ontology_manager_has_core_methods(self):
        from core.ontology import OntologyManager
        required = {"add_concept", "get_concept", "concepts_by_pillar", "add_relation", "relations_for", "seed_all_pillars", "seed_relations", "save", "load"}
        for method in required:
            assert hasattr(OntologyManager, method), f"OntologyManager missing: {method}"


# core/compositor.py contract


class TestCoreCompositorContract:
    def test_exports_all_renderers(self):
        from core.compositor import (
            auto_compose,
            render_timeline,
        )
        assert callable(render_timeline)
        assert callable(auto_compose)

    def test_each_renderer_accepts_empty_list(self):
        from core.compositor import (
            render_comparisons,
            render_connections,
            render_entity_badges,
            render_flow,
            render_key_numbers,
            render_timeline,
        )
        for renderer in (render_timeline, render_flow, render_comparisons, render_entity_badges, render_key_numbers, render_connections):
            assert renderer([]) == "", f"{renderer.__name__}([]) should return ''"


# scripts/check_source_freshness.py contract


class TestCheckSourceFreshnessContract:
    def test_exports_compute_staleness(self):
        from scripts.check_source_freshness import compute_staleness
        assert callable(compute_staleness)

    def test_compute_staleness_contract(self):
        from scripts.check_source_freshness import compute_staleness
        assert compute_staleness(None) is None
        assert compute_staleness("") is None
        assert compute_staleness("bad-date") is None
