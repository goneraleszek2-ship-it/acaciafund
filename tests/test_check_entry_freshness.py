"""Contract tests for scripts/check_entry_freshness.py tier logic."""

from datetime import date

from scripts.check_entry_freshness import (
    build_freshness_report,
    build_topic_report,
    compute_freshness,
    currency_tier,
    topic_status_summary,
    verification_anchor,
)


def item(**kw):
    base = {
        "slug": "markets/research/x",
        "title": "X",
        "content_type": "research",
        "category": "market-microstructure",
        "date_str": "2026-01-01",
    }
    base.update(kw)
    return base


def test_tier_default_timeless():
    assert currency_tier(item()) == "timeless"


def test_tier_news_categories_time_sensitive():
    for cat in ("earnings-analysis", "industry-analysis", "market-analysis"):
        assert currency_tier(item(category=cat)) == "time_sensitive"


def test_tier_explicit_field_wins():
    assert currency_tier(item(category="earnings-analysis", currency_tier="timeless")) == "timeless"
    assert currency_tier(item(currency_tier="time_sensitive")) == "time_sensitive"


def test_tier_learn_always_timeless():
    assert currency_tier(item(content_type="learn", category="earnings-analysis")) == "timeless"


def test_compute_freshness_timeless_never_decays():
    assert compute_freshness(date(2020, 1, 1), today=date(2026, 8, 1), tier="timeless") == "fresh"
    assert compute_freshness(None, tier="timeless") == "never"


def test_compute_freshness_time_sensitive_buckets():
    t = date(2026, 8, 1)
    assert compute_freshness(date(2026, 7, 20), today=t, tier="time_sensitive") == "fresh"
    assert compute_freshness(date(2026, 5, 20), today=t, tier="time_sensitive") == "stale"
    assert compute_freshness(date(2026, 1, 1), today=t, tier="time_sensitive") == "outdated"


def test_verification_anchor_uses_tier():
    old = item(category="data-quality", date_str="2025-01-01")
    assert verification_anchor(old, today=date(2026, 8, 1)) == "fresh"  # timeless
    ts = item(category="market-analysis", currency_tier="time_sensitive", date_str="2025-01-01")
    assert verification_anchor(ts, today=date(2026, 8, 1)) == "outdated"


def test_report_has_tier_fields():
    report = build_freshness_report(
        [item(slug="a", category="market-analysis"), item(slug="b", content_type="learn")],
        today=date(2026, 8, 1),
    )
    by_slug = {e["slug"]: e for e in report["entries"]}
    assert by_slug["a"]["currency_tier"] == "time_sensitive"
    assert by_slug["b"]["currency_tier"] == "timeless"
    assert report["tiers"]["time_sensitive"]["outdated"] == 1


def test_topic_report_cold_detection():
    today = date(2026, 8, 1)
    items = [
        item(slug="a", category="market-analysis", date_str="2025-01-01"),
        item(slug="b", category="market-analysis", date_str="2025-02-01"),
        item(slug="c", category="data-quality", date_str="2025-01-01"),
    ]
    report = build_topic_report(items, today=today)
    statuses = {t["category"]: t["status"] for t in report["topics"]}
    assert statuses["market-analysis"] == "cold"
    assert statuses["data-quality"] == "current"
    assert len(report["cold_topics"]) == 1
    assert report["cold_topics"][0]["oldest_slug"] == "a"


def test_topic_report_cooling_detection():
    today = date(2026, 8, 1)
    items = [
        item(slug="a", category="industry-analysis", date_str="2026-06-15"),
        item(slug="b", category="industry-analysis", date_str="2026-07-20"),
    ]
    report = build_topic_report(items, today=today)
    statuses = {t["category"]: t["status"] for t in report["topics"]}
    assert statuses["industry-analysis"] == "cooling"


def test_topic_summary_line():
    assert "1 cold, 0 cooling" in topic_status_summary(
        {"cold_topics": [{"category": "x"}], "cooling_topics": [], "topics": [1]}
    )


# ── Legacy contract suite (adapted to tier-aware API) ──


def test_none_is_never():
    assert compute_freshness(None) == "never"


def test_today_is_fresh():
    assert compute_freshness(date.today()) == "fresh"


def test_boundary_fresh_stale_time_sensitive():
    from datetime import timedelta

    t = "time_sensitive"
    assert compute_freshness(date.today() - timedelta(days=29), tier=t) == "fresh"
    assert compute_freshness(date.today() - timedelta(days=30), tier=t) == "stale"
    assert compute_freshness(date.today() - timedelta(days=89), tier=t) == "stale"
    assert compute_freshness(date.today() - timedelta(days=90), tier=t) == "outdated"


def test_parse_date_variants():
    from scripts.check_entry_freshness import parse_date

    assert parse_date("2026-01-15") == date(2026, 1, 15)
    assert parse_date("2026-01-15T10:30:00") == date(2026, 1, 15)
    assert parse_date("2026-01-15T10:30:00Z") == date(2026, 1, 15)
    assert parse_date(None) is None
    assert parse_date("") is None
    assert parse_date("not-a-date") is None


def test_review_preferred_over_verified():
    from scripts.check_entry_freshness import compute_freshness_with_review

    old = date(2020, 1, 1)
    recent = date.today()
    assert compute_freshness_with_review(old, recent) == "fresh"
    assert compute_freshness_with_review(recent, None) == "fresh"
    assert compute_freshness_with_review(None, recent) == "fresh"
    assert compute_freshness_with_review(None, None) == "never"


def test_review_older_than_verified_uses_verified():
    from datetime import timedelta

    from scripts.check_entry_freshness import compute_freshness_with_review

    recent = date.today()
    reviewed = recent - timedelta(days=120)
    assert compute_freshness_with_review(recent, reviewed) == "fresh"
    assert compute_freshness_with_review(recent, None) == "fresh"


def test_anchor_uses_most_recent_date():
    assert verification_anchor({"date_str": "2026-08-01"}) == "fresh"
    assert verification_anchor({"date_str": "2026-01-01", "currency_tier": "time_sensitive"}) == "outdated"
    assert (
        verification_anchor(
            {"date_str": "2026-01-01", "currency_tier": "time_sensitive", "last_verified": "2026-08-01"}
        )
        == "fresh"
    )
    assert (
        verification_anchor(
            {"date_str": "2026-01-01", "currency_tier": "time_sensitive", "last_reviewed": "2026-08-01"}
        )
        == "fresh"
    )
    assert verification_anchor({}) == "never"


def test_report_summary_and_entries():
    items = [
        {"slug": "a", "title": "A", "date_str": "2026-08-01", "content_type": "research", "category": "market-analysis"},
        {"slug": "b", "title": "B", "date_str": "2026-06-01", "content_type": "research", "category": "market-analysis"},
        {"slug": "c", "title": "C"},
    ]
    report = build_freshness_report(items, today=date(2026, 8, 3))
    assert report["total_items"] == 3
    assert report["summary"] == {"fresh": 1, "stale": 1, "outdated": 0, "never": 1}
    statuses = {e["slug"]: e["freshness"] for e in report["entries"]}
    assert statuses == {"a": "fresh", "b": "stale", "c": "never"}


def test_select_by_status_filters():
    from scripts.check_entry_freshness import select_by_status

    items = [
        {"slug": "a", "date_str": "2026-08-01", "content_type": "research", "category": "market-analysis"},
        {"slug": "b", "date_str": "2026-06-01", "content_type": "research", "category": "market-analysis"},
        {"slug": "c"},
    ]
    today = date(2026, 8, 3)
    assert [i["slug"] for i in select_by_status(items, ["never"], today=today)] == ["c"]
    assert [i["slug"] for i in select_by_status(items, ["stale", "outdated"], today=today)] == ["b"]
    assert [i["slug"] for i in select_by_status(items, ["fresh"], today=today)] == ["a"]

def test_mark_sets_field_on_matching_slugs():
    from scripts.check_entry_freshness import mark_items

    items = [
        {"slug": "a", "title": "A"},
        {"slug": "b", "title": "B"},
    ]
    marked = mark_items(items, ["a"], "last_verified", today=date(2026, 8, 3))
    assert len(marked) == 1
    assert items[0]["last_verified"] == "2026-08-03"
    assert "last_verified" not in items[1]
    assert marked[0]["slug"] == "a"


def test_mark_unknown_slugs_ignored():
    from scripts.check_entry_freshness import mark_items

    items = [{"slug": "a"}]
    marked = mark_items(items, ["nope"], "last_reviewed", today=date(2026, 8, 3))
    assert marked == []
