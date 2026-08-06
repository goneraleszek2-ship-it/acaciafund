"""Tests for core/markdown_utils.py — controlled markdown conversion + residue repair."""

from core.markdown_utils import fix_markdown_residue, md_to_html


class TestMdToHtml:
    def test_headings(self):
        html = md_to_html("## Core Concepts\n\n### Deep Dive")
        assert "<h2>Core Concepts</h2>" in html
        assert "<h3>Deep Dive</h3>" in html

    def test_bold_and_italic(self):
        html = md_to_html("**Term** *Also: alias one, alias two*")
        assert "<strong>Term</strong>" in html
        assert "<em>Also: alias one, alias two</em>" in html

    def test_bullets(self):
        html = md_to_html("- one\n- two")
        assert "<ul>" in html and "<li>one</li>" in html and "<li>two</li>" in html

    def test_link(self):
        html = md_to_html("[FATF](https://www.fatf-gafi.org/)")
        assert '<a href="https://www.fatf-gafi.org/">FATF</a>' in html

    def test_paragraphs(self):
        html = md_to_html("first paragraph\n\nsecond paragraph")
        assert "<p>first paragraph</p>" in html
        assert "<p>second paragraph</p>" in html

    def test_html_escaped(self):
        html = md_to_html("**A & B < C**")
        assert "&lt;" in html or "&amp;" in html
        assert "**" not in html

    def test_empty(self):
        assert md_to_html("") == ""
        assert md_to_html(None) == ""

    def test_glossary_like_body(self):
        md = (
            "This glossary covers key concepts.\n\n"
            "## Core Concepts\n\n"
            "**AML Surveillance** *Also: AI surveillance*\n\n"
            "## Authoritative Sources\n\n"
            "- **FATF** — guidance ([site](https://www.fatf-gafi.org/))"
        )
        html = md_to_html(md)
        assert "<h2>Core Concepts</h2>" in html
        assert "<h2>Authoritative Sources</h2>" in html
        assert "<strong>AML Surveillance</strong>" in html
        assert "<em>Also: AI surveillance</em>" in html
        assert "<li>" in html
        assert "##" not in html
        assert "**" not in html


class TestFixMarkdownResidue:
    def test_bold_and_em_inside_html(self):
        html = "<p>**AML Audit**</p><p>AML Audit *Also: AML audit*</p>"
        fixed = fix_markdown_residue(html)
        assert "<strong>AML Audit</strong>" in fixed
        assert "<em>Also: AML audit</em>" in fixed
        assert "**" not in fixed

    def test_markdown_heading_in_paragraph(self):
        html = "<p>## Wienerian Feedback Loops</p><p>content follows</p>"
        fixed = fix_markdown_residue(html)
        assert "<h2>Wienerian Feedback Loops</h2>" in fixed
        assert "<p>##" not in fixed

    def test_heading_levels(self):
        html = "<p>### Subsection</p>"
        fixed = fix_markdown_residue(html)
        assert "<h3>Subsection</h3>" in fixed

    def test_code_blocks_untouched(self):
        html = "<pre><code>schemas/**/*.proto\n**kwargs</code></pre><p>**real bold**</p>"
        fixed = fix_markdown_residue(html)
        assert "schemas/**/*.proto" in fixed
        assert "**kwargs" in fixed
        assert "<strong>real bold</strong>" in fixed

    def test_does_not_double_convert(self):
        html = "<p><strong>Already</strong> and <em>fine</em></p>"
        assert fix_markdown_residue(html) == html

    def test_empty(self):
        assert fix_markdown_residue("") == ""
        assert fix_markdown_residue(None) == ""
