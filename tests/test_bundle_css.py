"""Contract tests for the build-time CSS inliner/linter."""

from pathlib import Path

import pytest

from scripts import bundle_css as mod


def test_lint_valid_css():
    assert mod.lint_css("@layer a, b;\n@import url('x.css') layer(a);\n@layer a { .x { color: red; } }") == []


def test_lint_unmatched_brace():
    errors = mod.lint_css(".x { color: red;")
    assert any("unclosed" in e for e in errors)


def test_lint_import_after_rule():
    errors = mod.lint_css(".x { color: red; }\n@import url('x.css') layer(a);")
    assert any("@import after" in e for e in errors)


def test_bundle_inlines_and_wraps_layer(tmp_path, monkeypatch):
    static = tmp_path / "static"
    css_dir = static / "css"
    vendor = css_dir / "vendor"
    vendor.mkdir(parents=True)
    (vendor / "fonts.css").write_text(
        "@font-face { font-family: X; src: url('../fonts/x.woff2') format('woff2'); }",
        encoding="utf-8",
    )
    source = css_dir / "design-system.css"
    source.write_text(
        "@layer reset, tokens, base, components, utilities, overrides;\n"
        "@import url('vendor/fonts.css') layer(tokens);\n"
        "@layer tokens { :root { --x: 1; } }\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "STATIC", static)
    output = css_dir / "build" / "design-system.css"

    mod.bundle_css(source, output)
    bundled = output.read_text(encoding="utf-8")
    assert "@import" not in bundled
    assert "@layer tokens {" in bundled
    assert "url('/static/css/fonts/x.woff2')" in bundled
    assert mod.lint_css(bundled) == []


def test_bundle_rejects_import_after_rule(tmp_path, monkeypatch):
    static = tmp_path / "static"
    css_dir = static / "css"
    css_dir.mkdir(parents=True)
    source = css_dir / "design-system.css"
    source.write_text(
        ".x { color: red; }\n@import url('vendor/fonts.css') layer(tokens);",
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "STATIC", static)
    with pytest.raises(ValueError, match="@import after"):
        mod.bundle_css(source, css_dir / "build" / "design-system.css")
