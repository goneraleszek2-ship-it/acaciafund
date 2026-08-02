"""Tests for core/visuals.py — topic icon resolution, subtopic picking, SVG generation."""

import re

from core.visuals import (
    SUBTOPIC_CATEGORIES,
    TOPIC_ICONS,
    _extract_topic_words,
    _hex_to_rgb,
    _lerp_color,
    _pick_subtopic,
    _rgb_to_hex,
    generate_og_image,
    generate_thumbnail_svg,
    get_brand_topic_slugs,
    render_topic_icon,
    resolve_topic_icon,
)

_SVG_TAG = re.compile(r"<svg[^>]*>")


class TestResolveTopicIcon:
    def test_abstract_icon_returns_path(self):
        path = resolve_topic_icon("regulation")
        assert path and "<path" in path

    def test_unknown_key_returns_none(self):
        assert resolve_topic_icon("does-not-exist") is None

    def test_brand_icon_resolves(self):
        path = resolve_topic_icon("python")
        assert path and "<path" in path

    def test_brand_slugs_registered(self):
        slugs = get_brand_topic_slugs()
        assert "python" in slugs
        assert "kafka" in slugs or "apachekafka" in slugs


class TestRenderTopicIcon:
    def test_abstract_uses_stroke(self):
        rendered = render_topic_icon("regulation")
        assert rendered.startswith("<g")
        assert "stroke=\"currentColor\"" in rendered

    def test_brand_uses_fill(self):
        rendered = render_topic_icon("python")
        assert 'fill="currentColor"' in rendered

    def test_unknown_returns_empty(self):
        assert render_topic_icon("nope") == ""


class TestTopicIconsRegistry:
    def test_entries_have_required_keys(self):
        for key, entry in TOPIC_ICONS.items():
            assert entry["type"] in ("abstract", "brand")
            if entry["type"] == "abstract":
                assert "paths" in entry
            else:
                assert "slug" in entry

    def test_pillar_subtopics_cover_all(self):
        for pillar, subs in SUBTOPIC_CATEGORIES.items():
            assert subs, f"{pillar} has no subtopics"
            for sub, keywords in subs.items():
                assert keywords, f"{pillar}/{sub} has no keywords"
                assert sub in TOPIC_ICONS, f"{pillar}/{sub} missing icon"


class TestPickSubtopic:
    def test_brand_keyword_wins(self):
        assert _pick_subtopic(["Building a Kafka streaming pipeline"], "data-engineering") == "apachekafka"

    def test_aml_regulation(self):
        assert _pick_subtopic(["New regulatory guidance for banks"], "aml") == "regulation"

    def test_stock_ai(self):
        assert _pick_subtopic(["Transformer architecture advances"], "stock") == "ai"

    def test_openai_brand_icon_preferred(self):
        assert _pick_subtopic(["OpenAI launches new model"], "stock") == "openai"

    def test_unknown_pillar_default(self):
        assert _pick_subtopic(["anything"], "nope") == "regulation"

    def test_stock_market(self):
        assert _pick_subtopic(["Earnings and valuation updates"], "stock") == "stock_market"


class TestExtractTopicWords:
    def test_returns_capitalized_words(self):
        words = _extract_topic_words(["Kubernetes Deployment and Docker Networking"], n=5)
        assert "Kubernetes" in words
        assert "Docker" in words

    def test_skips_stopwords(self):
        words = _extract_topic_words(["This With From Over More New First"], n=10)
        assert not words

    def test_respects_n(self):
        words = _extract_topic_words(["Alpha Beta Gamma Delta Epsilon Zeta"], n=3)
        assert len(words) <= 3


class TestColorHelpers:
    def test_hex_to_rgb(self):
        assert _hex_to_rgb("#ff0080") == (255, 0, 128)

    def test_rgb_to_hex(self):
        assert _rgb_to_hex(255, 0, 128) == "#ff0080"

    def test_lerp_roundtrip(self):
        assert _lerp_color("#000000", "#ffffff", 0.0) == "#000000"
        assert _lerp_color("#000000", "#ffffff", 1.0) == "#ffffff"

    def test_lerp_clamps(self):
        assert _lerp_color("#000000", "#ffffff", -1.0) == "#000000"
        assert _lerp_color("#000000", "#ffffff", 2.0) == "#ffffff"


class TestGenerateThumbnail:
    def test_returns_valid_svg(self):
        svg = generate_thumbnail_svg("Kubernetes in production", "data-engineering", {"sqi": 0.8})
        assert svg.startswith("<svg")
        assert svg.endswith("</svg>")
        assert _SVG_TAG.search(svg)

    def test_deterministic(self):
        kwargs = dict(title="Same title for thumb", pillar="aml", scores={"sqi": 0.5})
        assert generate_thumbnail_svg(**kwargs) == generate_thumbnail_svg(**kwargs)

    def test_sqi_bar_present(self):
        svg = generate_thumbnail_svg("Title", "stock", {"sqi": 0.6})
        assert "rect" in svg

    def test_featured_image_layer(self):
        svg = generate_thumbnail_svg(
            "Title", "stock", {"sqi": 0.5}, featured_image_url="https://example.com/img.jpg"
        )
        assert "<image" in svg


class TestGenerateOgImage:
    def test_returns_valid_svg(self):
        svg = generate_og_image("Market analysis report title", "stock", {"sqi": 0.7}, "2026-07-01")
        assert svg.startswith("<svg")
        assert svg.endswith("</svg>")

    def test_contains_title_text(self):
        title = "Quarterly volatility review"
        svg = generate_og_image(title, "stock", {"sqi": 0.5})
        assert title in svg

    def test_deterministic(self):
        kwargs = dict(title="Same og title", pillar="aml", scores={"sqi": 0.5}, date_str="2026-01-01")
        assert generate_og_image(**kwargs) == generate_og_image(**kwargs)
