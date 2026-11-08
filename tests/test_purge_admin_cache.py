"""Tests for scripts/purge_admin_cache.py."""

from __future__ import annotations

import email.message
import urllib.error

import pytest

import scripts.purge_admin_cache as purge


def test_admin_urls_covers_extensionless_and_html_paths():
    urls = purge.admin_urls("https://www.acaciafund.org/")
    assert "https://www.acaciafund.org/admin/" in urls
    assert "https://www.acaciafund.org/admin/dashboard" in urls
    assert "https://www.acaciafund.org/admin/dashboard.html" in urls
    assert len(urls) == len(purge.ADMIN_PAGES)


def test_resolve_zone_id_prefers_configured_value(monkeypatch):
    monkeypatch.setenv("CLOUDFLARE_ZONE_ID", "zone-123")
    assert purge.resolve_zone_id("token") == "zone-123"


def test_resolve_zone_id_falls_back_to_pages_domain(monkeypatch):
    monkeypatch.delenv("CLOUDFLARE_ZONE_ID", raising=False)

    def fake_api(path, *args, **kwargs):
        if path.startswith("/zones"):
            return {"success": True, "result": []}
        if "/pages/projects/acaciafund/domains" in path:
            return {
                "success": True,
                "result": [
                    {"name": "www.acaciafund.org", "zone_tag": "zone-from-pages"},
                ],
            }
        raise AssertionError(path)

    monkeypatch.setattr(purge, "_api_request", fake_api)
    assert purge.resolve_zone_id("token", "acaciafund.org", "account-1") == "zone-from-pages"


def test_resolve_zone_id_falls_back_after_zone_api_401(monkeypatch):
    monkeypatch.delenv("CLOUDFLARE_ZONE_ID", raising=False)

    def fake_api(path, *args, **kwargs):
        if path.startswith("/zones"):
            raise urllib.error.HTTPError(
                "https://api.cloudflare.com/client/v4/zones", 401, "Unauthorized",
                email.message.Message(), None,
            )
        if "/pages/projects/acaciafund/domains" in path:
            return {
                "success": True,
                "result": [{"name": "acaciafund.org", "zone_tag": "zone-tag-1"}],
            }
        raise AssertionError(path)

    monkeypatch.setattr(purge, "_api_request", fake_api)
    assert purge.resolve_zone_id("token", "acaciafund.org", "account-1") == "zone-tag-1"


def test_main_requires_token(monkeypatch, capsys):
    monkeypatch.delenv("CLOUDFLARE_API_TOKEN", raising=False)
    assert purge.main([]) == 1
    assert "CLOUDFLARE_API_TOKEN is required" in capsys.readouterr().err


def test_main_dry_run_lists_urls(capsys):
    assert purge.main(["--dry-run", "--base-url", "https://example.com"]) == 0
    output = capsys.readouterr().out
    assert "https://example.com/admin/dashboard" in output
    assert "Would purge" in output


def test_purge_urls_raises_on_api_failure(monkeypatch):
    monkeypatch.setattr(
        purge,
        "_api_request",
        lambda *args, **kwargs: {"success": False, "errors": ["permission denied"]},
    )
    with pytest.raises(RuntimeError, match="permission denied"):
        purge.purge_urls("token", "zone", ["https://example.com/admin/"])
