"""Tests for scripts/backfill_philosophy_version.py (version pinning)."""

from scripts.backfill_philosophy_version import backfill


def test_backfill_sets_target_on_stale_and_missing():
    registry = {
        "content": [
            {"slug": "a", "philosophy_version": "v1.0-pluralistic-2026-08"},
            {"slug": "b"},
            {"slug": "c", "philosophy_version": "v1.2-analytical-thomistic-2026-08"},
        ]
    }
    changed = backfill(registry, "v1.2-analytical-thomistic-2026-08")
    assert [slug for slug, _ in changed] == ["a", "b"]
    versions = {i["slug"]: i["philosophy_version"] for i in registry["content"]}
    assert versions["a"] == "v1.2-analytical-thomistic-2026-08"
    assert versions["b"] == "v1.2-analytical-thomistic-2026-08"
    assert versions["c"] == "v1.2-analytical-thomistic-2026-08"


def test_backfill_is_idempotent():
    target = "v1.2-analytical-thomistic-2026-08"
    registry = {"content": [{"slug": "a", "philosophy_version": target}]}
    assert backfill(registry, target) == []
    assert backfill(registry, target) == []


def test_backfill_handles_empty_registry():
    assert backfill({}, "v1.2-analytical-thomistic-2026-08") == []
    assert backfill({"content": []}, "v1.2-analytical-thomistic-2026-08") == []
