"""Contract tests for dead-link filtering in scripts/fetch_news.py."""

import email.message
import urllib.error
from unittest.mock import patch

from scripts.fetch_news import _filter_dead_items, _is_dead_url


class _Response:
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _http_error(code: int) -> urllib.error.HTTPError:
    return urllib.error.HTTPError("https://example.com/a", code, "err", email.message.Message(), None)


def test_is_dead_url_404():
    with patch("urllib.request.urlopen", side_effect=_http_error(404)):
        assert _is_dead_url("https://example.com/a") is True


def test_is_dead_url_410():
    with patch("urllib.request.urlopen", side_effect=_http_error(410)):
        assert _is_dead_url("https://example.com/a") is True


def test_is_dead_url_200():
    with patch("urllib.request.urlopen", return_value=_Response()):
        assert _is_dead_url("https://example.com/a") is False


def test_is_dead_url_blocked_is_not_dead():
    with patch("urllib.request.urlopen", side_effect=_http_error(403)):
        assert _is_dead_url("https://example.com/a") is False


def test_is_dead_url_transient_error_is_not_dead():
    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("down")):
        assert _is_dead_url("https://example.com/a") is False


def test_is_dead_url_get_success_after_head_404():
    with patch("urllib.request.urlopen", side_effect=[_http_error(404), _Response()]):
        assert _is_dead_url("https://example.com/a") is False


def test_filter_dead_items_preserves_order():
    items = [
        {"url": "https://example.com/dead"},
        {"url": "https://example.com/live"},
        {"url": "https://example.com/also-live"},
    ]

    def fake_is_dead(url: str, timeout: int = 6) -> bool:
        return url.endswith("/dead")

    with patch("scripts.fetch_news._is_dead_url", side_effect=fake_is_dead):
        kept = _filter_dead_items(items)

    assert kept == [
        {"url": "https://example.com/live"},
        {"url": "https://example.com/also-live"},
    ]
