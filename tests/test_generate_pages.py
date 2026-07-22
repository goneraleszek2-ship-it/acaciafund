"""Tests for core/generate_pages.py — pure helper functions."""

from core.generate_pages import (
    extract_headings,
    find_related,
    generate_article_fingerprint,
    generate_sqi_badge,
    get_layer,
    layer_indicator_html,
    reading_time_minutes,
    resolve_card_image,
    sanitize_domain_breakdown,
    sanitize_text,
    thumbnail_key,
)

# ── extract_headings ──


class TestExtractHeadings:
    def test_no_headings_returns_clean_html(self):
        html = "<p>Hello world</p>"
        cleaned, toc = extract_headings(html)
        assert cleaned == html
        assert toc == []

    def test_extracts_h2_headings(self):
        html = "<h2>Introduction</h2><p>Text</p>"
        cleaned, toc = extract_headings(html)
        assert len(toc) == 1
        assert toc[0]["text"] == "Introduction"
        assert toc[0]["level"] == 2
        assert toc[0]["id"] == "introduction"

    def test_extracts_h3_headings(self):
        html = "<h3>Sub Section</h3><p>Text</p>"
        cleaned, toc = extract_headings(html)
        assert len(toc) == 1
        assert toc[0]["level"] == 3

    def test_mixed_levels(self):
        html = "<h2>A</h2><h3>B</h3><h2>C</h2>"
        cleaned, toc = extract_headings(html)
        assert len(toc) == 3
        assert [h["text"] for h in toc] == ["A", "B", "C"]

    def test_heading_ids_preserved_in_cleaned_html(self):
        html = '<h2 id="intro">Intro</h2>'
        cleaned, toc = extract_headings(html)
        assert 'id="intro"' in cleaned


# ── find_related ──


class _MockPost:
    def __init__(self, slug="", tags=None, pillar="", title=""):
        self.slug = slug
        self.tags = tags or []
        self.pillar = pillar
        self.title = title


class TestFindRelated:
    def test_empty_posts_returns_empty(self):
        result = find_related([], _MockPost(slug="a", tags=["aml"]))
        assert result == []

    def test_returns_same_pillar_posts(self):
        posts = [_MockPost(slug="x", tags=["aml"], pillar="aml")]
        current = _MockPost(slug="y", tags=["aml"], pillar="aml")
        result = find_related(posts, current)
        assert result == posts

    def test_excludes_current_post(self):
        current = _MockPost(slug="self", tags=["aml"], pillar="aml")
        posts = [current, _MockPost(slug="other", tags=["aml"], pillar="aml")]
        result = find_related(posts, current)
        assert current not in result
        assert len(result) == 1

    def test_respects_max_items(self):
        posts = [_MockPost(slug=str(i), tags=["a"]) for i in range(10)]
        current = _MockPost(slug="c", tags=["a"])
        result = find_related(posts, current, max_items=3)
        assert len(result) <= 3

    def test_scored_by_tag_overlap(self):
        posts = [
            _MockPost(slug="a", tags=["aml", "kyc"]),
            _MockPost(slug="b", tags=["aml"]),
        ]
        current = _MockPost(slug="c", tags=["aml", "kyc", "cdd"])
        result = find_related(posts, current)
        assert result[0].slug == "a"


# ── reading_time_minutes ──


class TestReadingTimeMinutes:
    def test_empty_text(self):
        assert reading_time_minutes("") == 1

    def test_short_text(self):
        assert reading_time_minutes("hello world") == 1

    def test_long_text(self):
        text = "word " * 500
        assert reading_time_minutes(text) == 2  # 500 words / 200 = 2.5 → int = 2

    def test_strips_html_before_counting(self):
        html = "<p>hello</p><p>world</p>" * 100
        assert reading_time_minutes(html) >= 1


# ── sanitize_text ──


class TestSanitizeText:
    def test_plain_html_preserved(self):
        assert sanitize_text("<p>hello</p>") == "<p>hello</p>"

    def test_emoji_stripped_by_default(self):
        result = sanitize_text("<p>hello 🚀 world</p>")
        assert "🚀" not in result
        assert "hello" in result

    def test_emoji_preserved_when_strip_emoji_false(self):
        result = sanitize_text("<p>hello 🚀</p>", strip_emoji=False)
        assert "🚀" in result


# ── sanitize_domain_breakdown ──


class TestSanitizeDomainBreakdown:
    def test_no_domain_breakdown_preserved(self):
        html = "<p>content</p>"
        assert sanitize_domain_breakdown(html) == html

    def test_domain_breakdown_removed(self):
        html = '<div class="domain-breakdown">hidden</div><p>keep</p>'
        result = sanitize_domain_breakdown(html)
        assert "domain-breakdown" not in result
        assert "keep" in result


# ── generate_sqi_badge ──


class TestGenerateSqiBadge:
    def test_high_sqi(self):
        result = generate_sqi_badge(0.85)
        assert "High" in result
        assert "badge" in result.lower()

    def test_medium_sqi(self):
        result = generate_sqi_badge(0.7)
        assert "Medium" in result

    def test_low_sqi(self):
        result = generate_sqi_badge(0.4)
        assert "Low" in result

    def test_zero_sqi(self):
        result = generate_sqi_badge(0)
        assert "Low" in result

    def test_perfect_sqi(self):
        result = generate_sqi_badge(1.0)
        assert "High" in result


# ── resolve_card_image ──


class TestResolveCardImage:
    def test_absolute_path_resolved(self):
        result = resolve_card_image("/images/pic.png", "https://site.com")
        assert result == "https://site.com/images/pic.png"

    def test_relative_path_site_prepended(self):
        result = resolve_card_image("pic.png", "https://site.com")
        assert result == "https://site.com/pic.png"

    def test_empty_returns_empty(self):
        assert resolve_card_image("", "https://site.com") == ""


# ── get_layer ──


class TestGetLayer:
    def test_research_layer(self):
        assert get_layer("/compliance/research/") == "research"

    def test_learn_layer(self):
        assert get_layer("/data/learn/") == "learn"

    def test_knowledge_layer(self):
        assert get_layer("/markets/knowledge/") == "knowledge"

    def test_unknown_path_defaults_to_research(self):
        assert get_layer("/about/") == "research"

    def test_empty_path_defaults_to_research(self):
        assert get_layer("") == "research"


# ── layer_indicator_html ──


class TestLayerIndicatorHtml:
    def test_research_layer(self):
        html = layer_indicator_html("research", "aml")
        assert "span" in html
        assert "Research" in html

    def test_learn_layer(self):
        html = layer_indicator_html("learn")
        assert "Learn" in html

    def test_knowledge_layer(self):
        html = layer_indicator_html("knowledge")
        assert "Knowledge" in html

    def test_empty_content_type_defaults_to_content(self):
        html = layer_indicator_html("")
        assert "Content" in html
        assert "layer-indicator" in html


# ── generate_article_fingerprint ──


class TestGenerateArticleFingerprint:
    def test_returns_hex_string(self):
        result = generate_article_fingerprint(
            "test/slug", "Test Title", "aml", "research", ["aml"]
        )
        assert isinstance(result, str)
        assert len(result) > 0
        assert all(c in "0123456789abcdef" for c in result)

    def test_different_inputs_different_results(self):
        a = generate_article_fingerprint("a", "Title", "aml", "research", [])
        b = generate_article_fingerprint("b", "Title", "aml", "research", [])
        assert a != b


# ── thumbnail_key ──


class TestThumbnailKey:
    def test_returns_first_12_chars_of_hash(self):
        result = thumbnail_key("Hello World")
        assert isinstance(result, str)
        assert len(result) == 12
        assert all(c in "0123456789abcdef" for c in result)

    def test_different_titles_different_keys(self):
        a = thumbnail_key("Title One")
        b = thumbnail_key("Title Two")
        assert a != b
