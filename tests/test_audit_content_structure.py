"""Tests for scripts/audit_content_structure.py — structure audit rules."""

import json

from scripts.audit_content_structure import (
    audit_item,
    count_words,
    extract_headings,
    find_markdown_residue,
    main,
)

GOOD_RESEARCH_BODY = "\n\n".join(
    f"<h2>Section {i}</h2>\n<p>" + "Content words padding padding padding padding padding padding padding padding. " * 4 + "</p>"
    for i in range(1, 6)
)


def make_item(slug="aml/research/good-item", content_type="research", body=GOOD_RESEARCH_BODY, **kw):
    item = {"slug": slug, "content_type": content_type, "title": "Good Item", "description": "d" * 50, "body_html": body}
    item.update(kw)
    return item


class TestHelpers:
    def test_count_words(self):
        assert count_words("<p>one two three</p><p>four</p>") == 4

    def test_extract_headings(self):
        body = "<h2>A</h2><p>x</p><h3>B</h3>"
        assert extract_headings(body) == [(2, "A"), (3, "B")]

    def test_markdown_residue_found(self):
        body = "<p>## Heading</p><p>**bold**</p>"
        assert find_markdown_residue(body)

    def test_markdown_residue_ignores_code(self):
        body = "<pre><code>**glob**</code></pre><p>fine text</p>"
        assert find_markdown_residue(body) == []


class TestAuditItem:
    def test_clean_research_passes(self):
        result = audit_item(make_item())
        assert result["errors"] == []
        assert result["warnings"] == []

    def test_empty_body_is_error(self):
        result = audit_item(make_item(body="   "))
        assert [e["rule"] for e in result["errors"]] == ["empty_body"]

    def test_research_three_headings_passes(self):
        body = "<h2>A</h2><p>words here</p><h2>B</h2><p>words here</p><h2>C</h2><p>words here</p>"
        result = audit_item(make_item(body=body))
        assert not any(e["rule"] == "min_h2" for e in result["errors"])

    def test_research_too_few_headings(self):
        body = "<h2>A</h2><p>words here</p><h2>B</h2><p>words here</p>"
        result = audit_item(make_item(body=body))
        assert any(e["rule"] == "min_h2" for e in result["errors"])

    def test_legacy_no_h2_exempt(self):
        body = "<p>no headings at all here</p>"
        result = audit_item(make_item(slug="data/research/celld-self-hosted-distributed-durable-objects", body=body))
        assert not any(e["rule"] == "min_h2" for e in result["errors"])
        assert any(w["rule"] == "no_h2_exempt" for w in result["warnings"])

    def test_learn_min_h2(self):
        body = "<h2>A</h2><p>words here</p><h2>B</h2><p>words here</p>"
        result = audit_item(make_item(content_type="learn", body=body))
        assert any(e["rule"] == "min_h2" for e in result["errors"])

    def test_learn_exempt_slug(self):
        body = "<h2>A</h2><p>words here</p>"
        result = audit_item(make_item(slug="data/learn/learning-hub", content_type="learn", body=body))
        assert not any(e["rule"] == "min_h2" for e in result["errors"])
        assert any(w["rule"] == "min_h2_exempt" for w in result["warnings"])

    def test_empty_section_detected(self):
        body = "<h2>One</h2><p>content content content</p><h2>Two</h2><h2>Three</h2><p>tail</p>"
        result = audit_item(make_item(body=body))
        assert any(e["rule"] == "empty_section" for e in result["errors"])

    def test_h2_then_h3_not_empty(self):
        body = "<h2>One</h2><h3>Sub</h3><p>content</p>"
        result = audit_item(make_item(body=body))
        assert not any(e["rule"] == "empty_section" for e in result["errors"])

    def test_short_overview_not_empty(self):
        body = "<h2>Overview</h2><p>Brief.</p><h2>Key Topics</h2><p>more content</p>" + GOOD_RESEARCH_BODY
        result = audit_item(make_item(body=body))
        assert not any(e["rule"] == "empty_section" for e in result["errors"])

    def test_markdown_residue_error(self):
        body = "<h2>A</h2>\n\n" + GOOD_RESEARCH_BODY + "\n<p>**stray bold**</p>"
        result = audit_item(make_item(body=body))
        assert any(e["rule"] == "markdown_residue" for e in result["errors"])

    def test_control_chars_error(self):
        body = GOOD_RESEARCH_BODY + "\x07"
        result = audit_item(make_item(body=body))
        assert any(e["rule"] == "control_chars" for e in result["errors"])

    def test_title_warning(self):
        result = audit_item(make_item(title="t" * 120))
        assert any(w["rule"] == "title_length" for w in result["warnings"])

    def test_description_warning(self):
        result = audit_item(make_item(description="d" * 400))
        assert any(w["rule"] == "description_length" for w in result["warnings"])

    def test_duplicate_heading_warning(self):
        body = "<h2>Same</h2><p>text</p><h2>Same</h2><p>more</p>" + "<h2>X</h2><p>pad</p><h2>Y</h2><p>pad</p>"
        result = audit_item(make_item(body=body))
        assert any(w["rule"] == "duplicate_heading" for w in result["warnings"])

    def test_word_count_warning(self):
        body = "<h2>A</h2><p>short body</p><h2>B</h2><p>short body</p><h2>C</h2><p>short body</p><h2>D</h2><p>short body</p>"
        result = audit_item(make_item(body=body))
        assert any(w["rule"] == "word_count" for w in result["warnings"])


class TestMain:
    def test_exit_on_errors_over_limit(self, tmp_path, monkeypatch):
        registry_path = tmp_path / "registry.json"
        registry = {"content": [make_item(body="<p>no headings at all here</p>")]}
        registry_path.write_text(json.dumps(registry), encoding="utf-8")
        report_path = tmp_path / "report.json"
        monkeypatch.setattr("scripts.audit_content_structure.REPOSITORY_ROOT", tmp_path)
        rc = main(["--registry", str(registry_path), "--report", str(report_path), "--fail-on-errors", "0"])
        assert rc == 1
        report = json.loads(report_path.read_text(encoding="utf-8"))
        assert report["error_count"] >= 1

    def test_clean_registry_passes(self, tmp_path):
        registry_path = tmp_path / "registry.json"
        registry = {"content": [make_item()]}
        registry_path.write_text(json.dumps(registry), encoding="utf-8")
        report_path = tmp_path / "report.json"
        rc = main(["--registry", str(registry_path), "--report", str(report_path)])
        assert rc == 0

    def test_missing_registry(self, tmp_path):
        assert main(["--registry", str(tmp_path / "nope.json")]) == 1
