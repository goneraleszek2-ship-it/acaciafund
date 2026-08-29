"""Contract tests for scripts/backfill_registry_sqi.py."""

import copy

import pytest

from scripts.backfill_registry_sqi import (
    _backfill,
    _compute_baseline_sqi,
    _validate_registry,
)

SAMPLE = {
    "slug": "data/learn/pyspark-fundamentals",
    "title": "PySpark Fundamentals",
    "content_type": "learn",
    "pillar": "data-engineering",
    "tags": ["spark", "python"],
    "body_html": "<p>Architecture, implementation, patterns, how to, tutorial, code</p>",
    "description": "How to build streaming data pipelines with PySpark",
    "created_at": "2026-07-31T09:48:50.870030+00:00",
}


def _missing_item(**overrides):
    item = {k: (v if v is not None else "") for k, v in SAMPLE.items()}
    item.update(overrides)
    # Simulate the no-sqi, no-signals-scoring state of real missing items.
    item.setdefault("signals", {})
    item["sqi"] = None
    return item


def test_compute_baseline_is_deterministic():
    item = _missing_item()
    assert _compute_baseline_sqi(item) == _compute_baseline_sqi(item)


def test_compute_baseline_matches_build_scorer():
    from core.build_quality import _compute_sqi_for_item
    from core.content import Content

    item = _missing_item()
    canonical = Content.from_dict(item)
    assert _compute_baseline_sqi(item) == round(_compute_sqi_for_item(canonical), 3)


def test_backfill_assigns_explicit_sqi_to_missing_only():
    registry = {"content": [_missing_item(), _missing_item(signals={"avg_sqi": 0.9})]}
    registry["content"][0]["bloom_questions"] = []
    registry["content"][1]["bloom_questions"] = []
    changed = _backfill(registry)
    assert len(changed) == 2
    for item in registry["content"]:
        assert isinstance(item["sqi"], float)
        assert 0.0 <= item["sqi"] <= 1.0
    # signals.avg_sqi takes priority over the computed baseline.
    assert registry["content"][1]["sqi"] == 0.9


def test_backfill_leaves_existing_sqi_untouched():
    existing = _missing_item()
    existing["sqi"] = 0.42
    registry = {"content": [existing, _missing_item()]}
    registry["content"][1]["bloom_questions"] = []
    changed = _backfill(registry)
    assert existing["sqi"] == 0.42
    assert len(changed) == 1


def test_backfill_is_idempotent():
    registry = {"content": [_missing_item(), _missing_item()]}
    for item in registry["content"]:
        item["bloom_questions"] = []
    _backfill(registry)
    snapshot = copy.deepcopy(registry)
    assert _backfill(registry) == []
    assert registry == snapshot


def test_mutated_registry_validates_against_schemas():
    registry = {"content": [_missing_item(), _missing_item()]}
    for item in registry["content"]:
        item["bloom_questions"] = []
    _backfill(registry)
    _validate_registry(registry)  # must not raise


def test_mutated_registry_dry_run_does_not_write(tmp_path, monkeypatch):
    registry = {"content": [_missing_item()]}
    registry["content"][0]["bloom_questions"] = []

    from scripts import backfill_registry_sqi as mod

    monkeypatch.setattr(mod, "_load_registry", lambda: registry)
    written = {"registry": None}

    def fake_write(reg):
        written["registry"] = reg

    monkeypatch.setattr(mod, "_write_registry", fake_write)

    assert mod.main(["--dry-run"]) == 0
    assert written["registry"] is None  # dry-run never writes


def test_main_writes_and_reports_zero_remaining(tmp_path, monkeypatch):
    item = _missing_item()
    registry = {"content": [item]}
    expected = _compute_baseline_sqi(dict(item))
    from scripts import backfill_registry_sqi as mod

    monkeypatch.setattr(mod, "_load_registry", lambda: registry)
    written = {}

    def fake_write(reg):
        written["reg"] = reg

    monkeypatch.setattr(mod, "_write_registry", fake_write)
    monkeypatch.setattr(mod, "BACKUP_PATH", tmp_path / "registry.pre-sqi-backfill.json")

    assert mod.main([]) == 0
    assert written["reg"]["content"][0]["sqi"] == pytest.approx(expected)
