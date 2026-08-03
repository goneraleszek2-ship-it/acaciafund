"""Tests for scripts/check_entry_freshness.py — entry freshness utilities.

Uses contract-testing approach: test function promises, not implementation.
"""

from datetime import date

from scripts.check_entry_freshness import (
    build_freshness_report,
    compute_freshness,
    compute_freshness_with_review,
    mark_items,
    parse_date,
    select_by_status,
    verification_anchor,
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


class TestVerificationAnchor:
    def test_uses_most_recent_anchor(self):
        assert verification_anchor({"date_str": "2026-08-01"}) == "fresh"
        assert verification_anchor({"date_str": "2026-01-01"}) == "outdated"
        assert verification_anchor({"date_str": "2026-01-01", "last_verified": "2026-08-01"}) == "fresh"
        assert verification_anchor({"date_str": "2026-01-01", "last_reviewed": "2026-08-01"}) == "fresh"
        assert verification_anchor({}) == "never"


class TestBuildFreshnessReport:
    def test_summary_and_entries(self):
        items = [
            {"slug": "a", "title": "A", "date_str": "2026-08-01"},
            {"slug": "b", "title": "B", "date_str": "2026-06-01"},
            {"slug": "c", "title": "C"},
        ]
        report = build_freshness_report(items, today=date(2026, 8, 3))
        assert report["total_items"] == 3
        assert report["summary"] == {"fresh": 1, "stale": 1, "outdated": 0, "never": 1}
        statuses = {e["slug"]: e["freshness"] for e in report["entries"]}
        assert statuses == {"a": "fresh", "b": "stale", "c": "never"}


class TestSelectByStatus:
    def test_filters_by_status(self):
        items = [
            {"slug": "a", "date_str": "2026-08-01"},
            {"slug": "b", "date_str": "2026-06-01"},
            {"slug": "c"},
        ]
        today = date(2026, 8, 3)
        assert [i["slug"] for i in select_by_status(items, ["never"], today=today)] == ["c"]
        assert [i["slug"] for i in select_by_status(items, ["stale", "outdated"], today=today)] == ["b"]
        assert [i["slug"] for i in select_by_status(items, ["fresh"], today=today)] == ["a"]


class TestMarkItems:
    def test_sets_field_on_matching_slugs(self):
        items = [
            {"slug": "a", "title": "A"},
            {"slug": "b", "title": "B"},
        ]
        marked = mark_items(items, ["a"], "last_verified", today=date(2026, 8, 3))
        assert len(marked) == 1
        assert items[0]["last_verified"] == "2026-08-03"
        assert "last_verified" not in items[1]
        assert marked[0]["slug"] == "a"

    def test_unknown_slugs_are_ignored(self):
        items = [{"slug": "a"}]
        marked = mark_items(items, ["nope"], "last_reviewed", today=date(2026, 8, 3))
        assert marked == []
