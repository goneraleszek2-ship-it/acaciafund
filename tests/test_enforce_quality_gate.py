"""Contract tests for scripts/enforce_quality_gate.py."""

import json

import pytest

from scripts.enforce_quality_gate import evaluate, load_quality


def write_build_meta(tmp_path, quality):
    meta = {"url_structure_version": "3.0", "quality": quality}
    path = tmp_path / "build-meta.json"
    path.write_text(json.dumps(meta), encoding="utf-8")
    return path


def test_load_quality_reads_block(tmp_path):
    path = write_build_meta(tmp_path, {"gate_passed": True, "gate_min_sqi": 0.65, "low_sqi_count": 0, "low_sqi_items": []})
    quality = load_quality(path)
    assert quality["gate_passed"] is True
    assert quality["low_sqi_count"] == 0


def test_load_quality_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_quality(tmp_path / "nope.json")


def test_load_quality_missing_block(tmp_path):
    path = tmp_path / "build-meta.json"
    path.write_text(json.dumps({"quality": {}}), encoding="utf-8")
    with pytest.raises(ValueError):
        load_quality(path)


def test_evaluate_pass_when_no_low_sqi():
    quality = {"gate_passed": True, "gate_min_sqi": 0.65, "low_sqi_count": 0, "low_sqi_items": []}
    assert evaluate(quality) == []


def test_evaluate_lists_offenders():
    quality = {
        "gate_passed": False,
        "gate_min_sqi": 0.65,
        "low_sqi_count": 2,
        "low_sqi_items": [
            {"slug": "data/research/a", "sqi": 0.52, "effective_sqi": 0.55},
            {"slug": "markets/research/b", "sqi": 0.61, "effective_sqi": 0.61},
        ],
    }
    offenders = evaluate(quality)
    assert len(offenders) == 2
    assert offenders[0]["slug"] == "data/research/a"


def test_evaluate_ignores_low_count_within_fail_on_budget():
    quality = {
        "gate_passed": False,
        "gate_min_sqi": 0.65,
        "low_sqi_count": 1,
        "low_sqi_items": [{"slug": "x", "sqi": 0.5}],
    }
    assert evaluate(quality, fail_on_low_sqi=1) == []


def test_evaluate_falls_back_when_items_not_listed():
    quality = {"gate_passed": False, "gate_min_sqi": 0.65, "low_sqi_count": 3, "low_sqi_items": []}
    offenders = evaluate(quality)
    assert len(offenders) == 3
    assert offenders[0]["slug"] == "(unknown)"
