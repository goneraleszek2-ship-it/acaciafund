"""Tests for scripts/check_source_freshness.py — freshness checking utilities.

Uses contract-testing approach: test function promises, not implementation.
"""

from datetime import datetime, timedelta, timezone
from email.message import Message
from unittest.mock import patch

from scripts.check_source_freshness import (
    _RETRIES,
    _request_with_retry,
    compute_staleness,
)

# ── compute_staleness ──
#
# Contract:
#   compute_staleness(last_verified: str | None) -> int | None
#   - None input → None
#   - ISO datetime string → days since that datetime (int)
#   - Invalid/unparseable string → None


class TestComputeStaleness:
    def test_none_returns_none(self):
        assert compute_staleness(None) is None

    def test_empty_string_returns_none(self):
        assert compute_staleness("") is None

    def test_today_returns_0(self):
        now = datetime.now(timezone.utc).isoformat()
        assert compute_staleness(now) == 0

    def test_yesterday_returns_1(self):
        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        assert compute_staleness(yesterday) == 1

    def test_week_ago_returns_7(self):
        week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        assert compute_staleness(week_ago) == 7

    def test_year_ago_returns_365_or_366(self):
        year_ago = (datetime.now(timezone.utc) - timedelta(days=365)).isoformat()
        result = compute_staleness(year_ago)
        assert result in (365, 366)

    def test_bad_format_returns_none(self):
        assert compute_staleness("not-a-date") is None

    def test_epoch_returns_large_number(self):
        epoch = datetime(2020, 1, 1, tzinfo=timezone.utc).isoformat()
        result = compute_staleness(epoch)
        assert result is not None
        assert result > 365

    def test_naive_datetime_is_treated_as_utc(self):
        naive = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat(timespec="seconds")
        if "+" in naive or "Z" in naive:
            naive = naive.split("+")[0]
        result = compute_staleness(naive)
        assert result == 2


# ── _request_with_retry ──
#
# Contract:
#   _request_with_retry(url, method, timeout) -> (response, error)
#   - Success → (response, None)
#   - Non-transient HTTP error (4xx/5xx not in transient set) → return immediately
#   - Transient status (429, 5xx) or connection error → retry up to _RETRIES times


class TestRequestWithRetry:
    def test_success_returns_response_no_retry(self):
        with patch("scripts.check_source_freshness._request", return_value=("RESP", None)) as mock:
            resp, err = _request_with_retry("http://x", "GET", 10)
        assert resp == "RESP"
        assert err is None
        assert mock.call_count == 1

    def test_non_transient_http_error_no_retry(self):
        from urllib.error import HTTPError

        err = HTTPError("http://x", 403, "Forbidden", Message(), None)
        with patch("scripts.check_source_freshness._request", return_value=(None, err)) as mock:
            resp, returned_err = _request_with_retry("http://x", "GET", 10)
        assert resp is None
        assert returned_err is err
        assert mock.call_count == 1

    def test_transient_error_retries_then_gives_up(self):
        err = OSError("boom")
        with patch("scripts.check_source_freshness._request", return_value=(None, err)) as mock, patch(
            "scripts.check_source_freshness.time.sleep"
        ):
            resp, returned_err = _request_with_retry("http://x", "GET", 10)
        assert resp is None
        assert returned_err is err
        assert mock.call_count == _RETRIES + 1

    def test_transient_http_status_retries(self):
        from urllib.error import HTTPError

        err = HTTPError("http://x", 429, "Too Many Requests", Message(), None)
        with patch("scripts.check_source_freshness._request", return_value=(None, err)) as mock, patch(
            "scripts.check_source_freshness.time.sleep"
        ):
            resp, returned_err = _request_with_retry("http://x", "GET", 10)
        assert resp is None
        assert returned_err is err
        assert mock.call_count == _RETRIES + 1

    def test_recovers_on_second_attempt(self):
        calls = {"n": 0}

        def flaky(url, method, timeout):
            calls["n"] += 1
            if calls["n"] == 1:
                return None, OSError("rate-limited")
            return "RESP", None

        with patch("scripts.check_source_freshness._request", side_effect=flaky) as mock, patch(
            "scripts.check_source_freshness.time.sleep"
        ):
            resp, err = _request_with_retry("http://x", "GET", 10)
        assert resp == "RESP"
        assert err is None
        assert mock.call_count == 2
