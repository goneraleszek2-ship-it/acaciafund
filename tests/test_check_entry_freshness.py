"""Tests for scripts/check_entry_freshness.py — entry freshness utilities.

Uses contract-testing approach: test function promises, not implementation.
"""

from datetime import date

from scripts.check_entry_freshness import (
    compute_freshness,
    compute_freshness_with_review,
    parse_date,
)


class TestComputeFreshness:
    def test_none_is_never(self):
        assert compute_freshness(None) == "never"

    def test_today_is_fresh(self):
        assert compute_freshness(date.today()) == "fresh"

    def test_30_days_ago_is_fresh(self):
        assert compute_freshness(date(2020, 1, 1)) == "outdated"

    def test_boundary_fresh_stale(self):
        from datetime import timedelta

        assert compute_freshness(date.today() - timedelta(days=29)) == "fresh"
        assert compute_freshness(date.today() - timedelta(days=30)) == "stale"
        assert compute_freshness(date.today() - timedelta(days=89)) == "stale"
        assert compute_freshness(date.today() - timedelta(days=90)) == "outdated"


class TestParseDate:
    def test_ymd(self):
        assert parse_date("2026-01-15") == date(2026, 1, 15)

    def test_iso_datetime(self):
        assert parse_date("2026-01-15T10:30:00") == date(2026, 1, 15)

    def test_iso_datetime_z(self):
        assert parse_date("2026-01-15T10:30:00Z") == date(2026, 1, 15)

    def test_none_and_empty(self):
        assert parse_date(None) is None
        assert parse_date("") is None

    def test_bad_format(self):
        assert parse_date("not-a-date") is None


class TestComputeFreshnessWithReview:
    def test_review_preferred_over_verified(self):
        old = date(2020, 1, 1)
        recent = date.today()
        assert compute_freshness_with_review(old, recent) == "fresh"
        assert compute_freshness_with_review(recent, None) == "fresh"
        assert compute_freshness_with_review(None, recent) == "fresh"
        assert compute_freshness_with_review(None, None) == "never"

    def test_review_older_than_verified_uses_verified(self):
        from datetime import timedelta

        recent = date.today()
        reviewed = recent - timedelta(days=120)
        assert compute_freshness_with_review(recent, reviewed) == "fresh"
        assert compute_freshness_with_review(recent, None) == "fresh"
