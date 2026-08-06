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
