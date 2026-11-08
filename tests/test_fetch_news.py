"""Contract tests for shared dead-link filtering in ingestion pipelines."""

import email.message
import urllib.error
from unittest.mock import patch

from core.link_validation import filter_dead_items, is_dead_url, normalize_url


class _Response:
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _http_error(code: int) -> urllib.error.HTTPError:
    return urllib.error.HTTPError("https://example.com/a", code, "err", email.message.Message(), None)


def test_is_dead_url_404():
    with patch("urllib.request.urlopen", side_effect=_http_error(404)):
        assert is_dead_url("https://example.com/a") is True


def test_is_dead_url_410():
    with patch("urllib.request.urlopen", side_effect=_http_error(410)):
        assert is_dead_url("https://example.com/a") is True


def test_is_dead_url_200():
    with patch("urllib.request.urlopen", return_value=_Response()):
        assert is_dead_url("https://example.com/a") is False


def test_is_dead_url_blocked_is_not_dead():
    with patch("urllib.request.urlopen", side_effect=_http_error(403)):
        assert is_dead_url("https://example.com/a") is False


def test_is_dead_url_transient_error_is_not_dead():
    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("down")):
        assert is_dead_url("https://example.com/a") is False


def test_is_dead_url_get_success_after_head_404():
    with patch("urllib.request.urlopen", side_effect=[_http_error(404), _Response()]):
        assert is_dead_url("https://example.com/a") is False


def test_normalize_url_strips_query_fragment_and_trailing_slash():
    assert normalize_url("https://example.com/a/?q=1#frag") == "https://example.com/a"


def test_filter_dead_items_preserves_order():
    items = [
        {"url": "https://example.com/dead"},
        {"url": "https://example.com/live"},
        {"url": "https://example.com/also-live"},
    ]

    with patch("core.link_validation.dead_urls", return_value={"https://example.com/dead"}):
        kept = filter_dead_items(items)

    assert kept == [
        {"url": "https://example.com/live"},
        {"url": "https://example.com/also-live"},
    ]


def test_filter_dead_items_source_url_key():
    items = [
        {"source_url": "https://example.com/dead"},
        {"source_url": "https://example.com/live"},
    ]

    with patch("core.link_validation.dead_urls", return_value={"https://example.com/dead"}):
        kept = filter_dead_items(items, url_key="source_url")

    assert kept == [{"source_url": "https://example.com/live"}]
