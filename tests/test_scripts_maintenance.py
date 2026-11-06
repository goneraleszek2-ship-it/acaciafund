"""Tests for maintenance scripts: description trimming, CMS API, previews, tags."""

import json

import pytest

import scripts.cms_api as cms_api
from scripts.fix_orphan_tags import levenshtein, normalize, slugify, title_case
from scripts.serve_cms import build_preview_html
from scripts.trim_descriptions import trim_description
from scripts.verify_admin_access import classify_response


class TestTrimDescription:
    def test_short_description_unchanged(self):
        assert trim_description("Short text.", 303) == "Short text."

    def test_prefers_complete_sentence(self):
        text = "First sentence is here. " + ("Second sentence is long. " * 30)
        trimmed = trim_description(text, 120)
        assert len(trimmed) <= 120
        assert trimmed.startswith("First sentence is here.")

    def test_adds_ellipsis_when_cutting_mid_sentence(self):
        text = "word " * 100
        trimmed = trim_description(text, 60)
        assert len(trimmed) <= 60
        assert trimmed.endswith("…")

    def test_never_exceeds_limit(self):
        text = "x" * 1000
        assert len(trim_description(text, 303)) <= 303


class TestAdminAccess:
    def test_redirect_is_protected(self):
        assert classify_response(302, "https://acaciafund.cloudflareaccess.com/") == "protected"

    def test_auth_errors_are_protected(self):
        assert classify_response(401) == "protected"
        assert classify_response(403) == "protected"

    def test_public_dashboard_is_unprotected(self):
        assert classify_response(200) == "unprotected"

    def test_missing_and_server_errors(self):
        assert classify_response(404) == "missing"
        assert classify_response(503) == "error"


class TestFixOrphanTags:
    def test_levenshtein(self):
        assert levenshtein("kitten", "sitting") == 3
        assert levenshtein("same", "same") == 0

    def test_slugify(self):
        assert slugify("  Anti-Money Laundering!  ") == "anti-money-laundering"

    def test_normalize_and_title_case(self):
        assert normalize("Anti-Money  Laundering") == "anti money  laundering"
        assert title_case("anti-money-laundering") == "Anti Money Laundering"


class TestPreviewHtml:
    def test_escapes_untrusted_fields(self):
        html = build_preview_html(
            {
                "title": "<script>alert(1)</script>",
                "description": "<b>desc</b>",
                "body_html": "<p>body</p>",
                "pillar": "aml",
                "content_type": "research",
            }
        )
        assert "<script>alert(1)</script>" not in html
        assert "&lt;script&gt;" in html
        assert "&lt;b&gt;desc&lt;/b&gt;" in html

    def test_includes_labels(self):
        html = build_preview_html({"title": "T", "pillar": "stock", "content_type": "learn"})
        assert "Markets / Learn" in html


@pytest.fixture
def cms(tmp_path, monkeypatch):
    registry = tmp_path / "registry.json"
    registry.write_text(
        json.dumps(
            {
                "content": [
                    {
                        "slug": "aml/research/a",
                        "title": "Alpha AML",
                        "description": "transaction monitoring",
                        "body_html": "<p>body</p>",
                        "pillar": "aml",
                        "content_type": "research",
                        "tags": ["aml"],
                        "date_str": "2026-01-01",
                        "difficulty": "beginner",
                    },
                    {
                        "slug": "aml/learn/b",
                        "title": "Beta AML",
                        "description": "kyc guide",
                        "body_html": "",
                        "pillar": "aml",
                        "content_type": "learn",
                        "tags": [],
                        "date_str": "2026-02-01",
                    },
                    {
                        "slug": "stock/research/c",
                        "title": "Gamma Markets",
                        "description": "market structure",
                        "body_html": "<p>b</p>",
                        "pillar": "stock",
                        "content_type": "research",
                        "tags": ["markets"],
                        "date_str": "2026-03-01",
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(cms_api, "REGISTRY_BACKUP_DIR", tmp_path / "backups")
    monkeypatch.setattr(cms_api, "VERSIONS_DIR", tmp_path / "versions")
    return cms_api.CMS(registry_path=registry)


class TestCMS:
    def test_list_filters_and_search(self, cms):
        page, total = cms.list(pillar="aml")
        assert total == 2
        page, total = cms.list(search="kyc")
        assert total == 1 and page[0]["slug"] == "aml/learn/b"
        page, total = cms.list(limit=1, offset=1)
        assert total == 3 and len(page) == 1

    def test_get(self, cms):
        assert cms.get("aml/research/a")["title"] == "Alpha AML"
        assert cms.get("nope") is None

    def test_create_update_delete(self, cms):
        created = cms.create({"slug": "data/learn/new", "title": "New"})
        assert created["pillar"] == "aml"
        assert cms.get("data/learn/new") is not None
        with pytest.raises(ValueError):
            cms.create({"slug": "data/learn/new", "title": "Dup"})

        updated = cms.update("data/learn/new", {"title": "Renamed", "tags": ["x"]})
        assert updated["title"] == "Renamed"
        assert cms.list_versions("data/learn/new")

        assert cms.delete("data/learn/new") is True
        assert cms.delete("data/learn/new") is False
        assert cms.get("data/learn/new") is None

    def test_restore_version(self, cms):
        cms.update("aml/research/a", {"title": "Changed"})
        versions = cms.list_versions("aml/research/a")
        assert versions
        restored = cms.restore_version("aml/research/a", versions[0]["timestamp"])
        assert restored["title"] == "Alpha AML"

    def test_stats(self, cms):
        stats = cms.stats()
        assert stats["total"] == 3
        assert stats["by_pillar"]["aml"] == 2
        assert stats["with_body"] == 2
