"""Tests for scripts/purge_admin_cache.py."""

from __future__ import annotations

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
