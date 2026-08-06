"""Tests for scripts/remediate_content_structure.py — sectionizing and residue fixes."""

import json

from scripts.remediate_content_structure import (
    remediate_registry,
    sectionize_body,
    strip_leading_title,
)

LEAD_BODY = (
    "<p>Intro paragraph with enough words to count as the overview text here.</p>"
    "<p><strong>First topic.</strong> Body text for the first topic section.</p>"
    "<p><strong>Second topic.</strong> Body text for the second topic section.</p>"
    "<p>Trailing citation: <a href='https://example.com'>source</a>.</p>"
)


class TestSectionizeBody:
    def test_creates_overview_and_sections(self):
        out = sectionize_body(LEAD_BODY)
        assert "<h2>Overview</h2>" in out
        assert "<h2>First topic</h2>" in out
        assert "<h2>Second topic</h2>" in out
        assert out.count("<h2>") == 3

    def test_no_double_paragraph_wrap(self):
        assert "<p><p>" not in sectionize_body(LEAD_BODY)

    def test_preserves_trailing_citation(self):
        out = sectionize_body(LEAD_BODY)
        assert "Trailing citation" in out
        assert "example.com" in out

    def test_drops_trailing_period_from_heading(self):
        out = sectionize_body(LEAD_BODY)
        assert "<h2>First topic</h2>" in out
        assert "<h2>First topic.</h2>" not in out

    def test_empty_body(self):
        assert sectionize_body("") == ""
        assert sectionize_body("   ") == ""

    def test_no_strong_leads(self):
        body = "<p>Just a plain paragraph with several words in it.</p>"
        out = sectionize_body(body)
        assert "<h2>Overview</h2>" in out
        assert out.count("<h2>") == 1

    def test_content_preserved_total(self):
        out = sectionize_body(LEAD_BODY)
        for fragment in ("Intro paragraph", "Body text for the first", "Body text for the second"):
            assert fragment in out


class TestStripLeadingTitle:
    def test_strips_h1_title(self):
        body = "<h1>The Title</h1>\n\n<p>content follows</p>"
        assert strip_leading_title(body, "The Title") == "\n\n<p>content follows</p>"

    def test_strips_markdown_hash_title(self):
        body = "<p># The Title</p><p>content follows</p>"
        out = strip_leading_title(body, "The Title")
        assert "# The Title" not in out
        assert "content follows" in out

    def test_untouched_when_title_absent(self):
        body = "<p>nothing to strip here</p>"
        assert strip_leading_title(body, "Missing") == body


class TestRemediateRegistry:
    def test_sectionizes_configured_slugs(self):
        registry = {
            "content": [
                {
                    "slug": "data/research/sqlite-in-production-optimizing-wal-mode-concurrency-and-vfs",
                    "content_type": "research",
                    "title": "T",
                    "body_html": LEAD_BODY,
                },
                {
                    "slug": "data/research/other-item",
                    "content_type": "research",
                    "title": "T",
                    "body_html": "<h2>Already fine</h2><p>words here plenty enough.</p>",
                },
            ]
        }
        changes = remediate_registry(registry)
        slugs = {c["slug"] for c in changes}
        assert slugs == {"data/research/sqlite-in-production-optimizing-wal-mode-concurrency-and-vfs"}
        item = registry["content"][0]
        assert "<h2>Overview</h2>" in item["body_html"]
        other = registry["content"][1]
        assert other["body_html"] == "<h2>Already fine</h2><p>words here plenty enough.</p>"

    def test_fixes_markdown_residue_slugs(self):
        registry = {
            "content": [
                {
                    "slug": "data/knowledge/cybernetic-foundations",
                    "content_type": "knowledge",
                    "title": "Cybernetic Foundations",
                    "body_html": "<p>## A Section</p><p>**bold** text here</p>",
                }
            ]
        }
        changes = remediate_registry(registry)
        assert changes and changes[0]["fix"] == "markdown_residue"
        body = registry["content"][0]["body_html"]
        assert "<h2>A Section</h2>" in body
        assert "<strong>bold</strong>" in body

    def test_no_changes_when_clean(self):
        registry = {"content": [{"slug": "x", "content_type": "research", "title": "T", "body_html": "<h2>A</h2><p>words</p>"}]}
        assert remediate_registry(registry) == []

    def test_roundtrip_json_serializable(self, tmp_path):
        registry = {"content": [{"slug": "data/research/the-development-pipeline-is-a-production-system",
                                 "content_type": "research", "title": "T", "body_html": LEAD_BODY}]}
        remediate_registry(registry)
        path = tmp_path / "out.json"
        path.write_text(json.dumps(registry), encoding="utf-8")
        assert json.loads(path.read_text(encoding="utf-8"))["content"][0]["body_html"]
