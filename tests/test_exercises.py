"""Tests for core/exercises.py — sandbox exercise attachment (Tier 4)."""

from __future__ import annotations

import json
import types
from pathlib import Path

from core.exercises import attach_exercises, load_exercises

SAMPLE = {
    "dataset": {"schema": "CREATE TABLE t (id INT);", "seed": "INSERT INTO t VALUES (1);"},
    "sql": [
        {
            "id": "ex1",
            "lesson_slugs": ["aml/learn/aml-basics"],
            "title": "T",
            "expected": "SELECT 1;",
        }
    ],
    "polars": [
        {
            "id": "ex2",
            "lesson_slugs": ["data/learn/sql-for-data-engineers"],
            "title": "P",
            "expected": "print('x')",
        }
    ],
    "sims": [
        {
            "id": "ex3",
            "lesson_slugs": ["aml/learn/kyc-cdd-workflows"],
            "title": "S",
            "steps": [],
        }
    ],
}


def _item(slug: str) -> types.SimpleNamespace:
    return types.SimpleNamespace(slug=slug)


def test_load_exercises(tmp_path: Path) -> None:
    p = tmp_path / "exercises.json"
    p.write_text(json.dumps(SAMPLE), encoding="utf-8")
    data = load_exercises(p)
    assert len(data["sql"]) == 1
    assert data["dataset"]["schema"].startswith("CREATE TABLE")
    assert len(data["sims"]) == 1


def test_load_exercises_missing_file(tmp_path: Path) -> None:
    data = load_exercises(tmp_path / "nope.json")
    assert data["sql"] == [] and data["polars"] == [] and data["sims"] == []
    assert data["dataset"] is None


def test_attach_by_full_slug() -> None:
    items = [_item("aml/learn/aml-basics")]
    attached = attach_exercises(items, SAMPLE)
    assert attached == 1
    assert items[0].sandbox_exercises[0]["kind"] == "sql"
    assert items[0].sandbox_exercises[0]["dataset"]["schema"]


def test_no_match_leaves_items_untouched() -> None:
    items = [_item("aml/learn/unrelated")]
    attached = attach_exercises(items, SAMPLE)
    assert attached == 0
    assert not hasattr(items[0], "sandbox_exercises")


def test_kinds_assigned_and_dataset_only_for_sql_polars() -> None:
    items = [
        _item("aml/learn/aml-basics"),
        _item("data/learn/sql-for-data-engineers"),
        _item("aml/learn/kyc-cdd-workflows"),
    ]
    attach_exercises(items, SAMPLE)
    by_slug = {i.slug: i.sandbox_exercises for i in items}
    assert by_slug["aml/learn/aml-basics"][0]["kind"] == "sql"
    assert "dataset" in by_slug["aml/learn/aml-basics"][0]
    assert by_slug["data/learn/sql-for-data-engineers"][0]["kind"] == "polars"
    assert "dataset" in by_slug["data/learn/sql-for-data-engineers"][0]
    assert by_slug["aml/learn/kyc-cdd-workflows"][0]["kind"] == "sim"
    assert "dataset" not in by_slug["aml/learn/kyc-cdd-workflows"][0]


def test_attached_data_is_json_serializable() -> None:
    items = [_item("aml/learn/aml-basics"), _item("aml/learn/kyc-cdd-workflows")]
    attach_exercises(items, SAMPLE)
    for i in items:
        json.dumps(i.sandbox_exercises)  # must not raise
