"""Contract tests for scripts/check_external_links.py."""

import json
import urllib.error
from pathlib import Path
from unittest.mock import patch

from scripts.check_external_links import (
    check_url,
    collect_external_urls,
    load_blocking_hosts,
)


def make_dist(tmp_path):
    dist = tmp_path / "dist"
    (dist / "data" / "research").mkdir(parents=True)
    (dist / "data" / "research" / "index.html").write_text(
        '<a href="https://external.example/doc">x</a>'
        '<a href="/internal/page">y</a>'
        '<a href="https://www.acaciafund.org/other">z</a>'
        '<a href="https://blocked.test/doc">b</a>',
        encoding="utf-8",
    )
    return dist


def test_collect_external_urls_filters_internal_and_own_origin(tmp_path):
    dist = make_dist(tmp_path)
    urls = collect_external_urls(dist)
    assert urls == ["https://blocked.test/doc", "https://external.example/doc"]


def test_load_blocking_hosts_missing_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert load_blocking_hosts() == set()


def test_load_blocking_hosts_reads_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    host_file = Path("data/known_blocking_hosts.json")
    host_file.parent.mkdir(exist_ok=True)
    host_file.write_text(json.dumps({"hosts": ["blocked.test"]}), encoding="utf-8")
    assert load_blocking_hosts() == {"blocked.test"}


def test_check_url_ok(monkeypatch):
    def fake_urlopen(req, timeout=8):
        class Resp:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

        return Resp()

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    result = check_url("https://ok.example/a", set())
    assert result["status"] == "ok"
    assert result["http_status"] == 200


def test_check_url_skips_quarantined_host():
    result = check_url("https://blocked.test/a", {"blocked.test"})
    assert result["status"] == "skipped"


def test_check_url_get_fallback_after_head_405(monkeypatch):
    def fake_urlopen(req, timeout=8):
        if req.method == "HEAD":
            raise urllib.error.HTTPError(req.full_url, 405, "Method Not Allowed", {}, None)

        class Resp:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

        return Resp()

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    result = check_url("https://example.test/a", set())
    assert result["status"] == "ok"


def test_check_url_get_fallback_after_head_404(monkeypatch):
    def fake_urlopen(req, timeout=8):
        if req.method == "HEAD":
            raise urllib.error.HTTPError(req.full_url, 404, "Not Found", {}, None)

        class Resp:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

        return Resp()

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    result = check_url("https://example.test/a", set())
    assert result["status"] == "ok"


def test_check_url_error_status():
    class Resp:
        status = 404

    with patch("urllib.request.urlopen", side_effect=urllib.error.HTTPError("u", 404, "nf", {}, None)):
        result = check_url("https://gone.test/a", set())
    assert result["status"] == "error"
    assert result["http_status"] == 404


def test_check_url_unreachable_after_retries(monkeypatch):
    def fail(*args, **kwargs):
        raise urllib.error.URLError("down")

    monkeypatch.setattr("urllib.request.urlopen", fail)
    result = check_url("https://down.test/a", set(), retries=1)
    assert result["status"] == "unreachable"
