"""Tests for core/metadata.py — manifest building, validation, JSON utilities."""

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from core.metadata import (
    _type_ok,
    build_asset_manifest,
    build_story_manifest,
    build_run_manifest,
    canonical_json,
    iso_utc,
    payload_checksum,
    read_json,
    utc_now,
    validate_manifest,
    write_json,
)


class TestDateTime:
    def test_utc_now_returns_aware(self):
        dt = utc_now()
        assert dt.tzinfo is not None
        assert dt.tzinfo.utcoffset(dt) == timezone.utc.utcoffset(dt)

    def test_iso_utc_default(self):
        s = iso_utc()
        assert s.endswith("Z")
        assert "T" in s

    def test_iso_utc_with_value(self):
        dt = datetime(2026, 6, 15, 10, 0, 0, tzinfo=timezone.utc)
        s = iso_utc(dt)
        assert s == "2026-06-15T10:00:00Z"

    def test_iso_utc_naive_input(self):
        dt = datetime(2026, 6, 15, 10, 0, 0)
        s = iso_utc(dt)
        assert s.endswith("Z")


class TestJsonUtils:
    def test_canonical_json_sorted_keys(self):
        result = canonical_json({"b": 2, "a": 1})
        assert result == '{"a":1,"b":2}'

    def test_canonical_json_no_extra_whitespace(self):
        result = canonical_json({"a": 1})
        assert " " not in result

    def test_payload_checksum_deterministic(self):
        a = payload_checksum({"x": 1})
        b = payload_checksum({"x": 1})
        assert a == b

    def test_payload_checksum_changes_with_content(self):
        a = payload_checksum({"x": 1})
        b = payload_checksum({"x": 2})
        assert a != b


class TestTypeOk:
    def test_string_check(self):
        assert _type_ok("hello", "string") is True
        assert _type_ok(42, "string") is False

    def test_integer_check(self):
        assert _type_ok(42, "integer") is True
        assert _type_ok("42", "integer") is False

    def test_number_check(self):
        assert _type_ok(42, "number") is True
        assert _type_ok(3.14, "number") is True
        assert _type_ok("42", "number") is False

    def test_boolean_check(self):
        assert _type_ok(True, "boolean") is True
        assert _type_ok(False, "boolean") is True
        assert _type_ok(1, "boolean") is False

    def test_object_check(self):
        assert _type_ok({"a": 1}, "object") is True
        assert _type_ok([], "object") is False

    def test_array_check(self):
        assert _type_ok([1, 2], "array") is True
        assert _type_ok({"a": 1}, "array") is False

    def test_unknown_type(self):
        assert _type_ok("anything", "unknown_type") is True


class TestValidateManifest:
    def test_valid_manifest(self, tmp_path):
        from core.metadata import SCHEMA_DIR
        schema = {"required": ["name", "version"], "properties": {"name": {"type": "string"}, "version": {"type": "integer"}}}
        schema_path = SCHEMA_DIR / "test-schema.schema.json"
        schema_path.parent.mkdir(parents=True, exist_ok=True)
        schema_path.write_text(json.dumps(schema))
        try:
            validate_manifest({"name": "test", "version": 1}, "test-schema.schema.json")
        finally:
            schema_path.unlink()

    def test_missing_required_field(self, tmp_path):
        from core.metadata import SCHEMA_DIR
        schema = {"required": ["name"], "properties": {}}
        schema_path = SCHEMA_DIR / "missing-test.schema.json"
        schema_path.parent.mkdir(parents=True, exist_ok=True)
        schema_path.write_text(json.dumps(schema))
        try:
            with pytest.raises(ValueError, match="Missing required"):
                validate_manifest({}, "missing-test.schema.json")
        finally:
            schema_path.unlink()

    def test_invalid_constant(self, tmp_path):
        from core.metadata import SCHEMA_DIR
        schema = {"properties": {"type": {"const": "story"}}}
        schema_path = SCHEMA_DIR / "const-test.schema.json"
        schema_path.parent.mkdir(parents=True, exist_ok=True)
        schema_path.write_text(json.dumps(schema))
        try:
            with pytest.raises(ValueError, match="Invalid constant"):
                validate_manifest({"type": "wrong"}, "const-test.schema.json")
        finally:
            schema_path.unlink()

    def test_invalid_type(self, tmp_path):
        from core.metadata import SCHEMA_DIR
        schema = {"properties": {"count": {"type": "integer"}}}
        schema_path = SCHEMA_DIR / "type-test.schema.json"
        schema_path.parent.mkdir(parents=True, exist_ok=True)
        schema_path.write_text(json.dumps(schema))
        try:
            with pytest.raises(ValueError, match="Invalid type"):
                validate_manifest({"count": "not-an-int"}, "type-test.schema.json")
        finally:
            schema_path.unlink()


class TestReadWriteJson:
    def test_write_and_read(self, tmp_path):
        p = tmp_path / "test.json"
        data = {"key": "value", "num": 42}
        write_json(p, data)
        assert p.exists()
        result = read_json(p)
        assert result == data

    def test_read_missing_file(self, tmp_path):
        result = read_json(tmp_path / "nonexistent.json")
        assert result is None

    def test_read_invalid_json(self, tmp_path):
        p = tmp_path / "bad.json"
        p.write_text("{invalid")
        result = read_json(p)
        assert result is None


class TestBuildAssetManifest:
    def test_basic_manifest(self):
        asset_path = Path(__file__).parent.parent / "core" / "__init__.py"
        assert asset_path.exists()
        manifest = build_asset_manifest("test-content", "screenshot", asset_path, "https://example.com/img.png")
        assert manifest["manifest_type"] == "asset"
        assert manifest["content_id"] == "test-content"
        assert manifest["asset_type"] == "screenshot"
        assert manifest["bytes"] > 0
        assert manifest["checksum"] != ""

    def test_mime_type_inference(self):
        asset_path = Path(__file__).parent.parent / "tests" / "mime-test.pdf"
        asset_path.write_bytes(b"fake-pdf")
        try:
            manifest = build_asset_manifest("c1", "pdf", asset_path)
            assert manifest["mime_type"] == "application/pdf"
        finally:
            asset_path.unlink(missing_ok=True)


class TestBuildStoryManifest:
    def test_minimal_manifest(self):
        manifest = build_story_manifest(
            content_id="test/story",
            pillar="aml",
            title="Test Story",
            date="2026-06-15",
        )
        assert manifest["manifest_type"] == "story"
        assert manifest["content_id"] == "test/story"
        assert manifest["pillar"] == "aml"
        assert manifest["checksum"] != ""

    def test_with_all_fields(self):
        manifest = build_story_manifest(
            content_id="markets/research/test",
            pillar="stock",
            title="Market Research",
            date="2026-06-15",
            source_urls=["https://example.com"],
            story_count=3,
            signals={"avg_sqi": 0.8},
            bloom_levels=[1, 2, 3],
            questions_count=5,
            flashcards_count=10,
            assets=[{"path": "img.png"}],
            lineage={"source": "arxiv"},
            quality_flags=["needs-review"],
            source_breakdown={"arxiv": 1},
            quality_metrics={"score": 0.85},
            published_at="2026-06-16T00:00:00Z",
        )
        assert manifest["story_count"] == 3
        assert manifest["signals"]["avg_sqi"] == 0.8
        assert manifest["quality_flags"] == ["needs-review"]


class TestBuildRunManifest:
    def test_minimal_manifest(self):
        manifest = build_run_manifest(
            run_id="run-001",
            started_at="2026-06-15T10:00:00Z",
            ended_at="2026-06-15T10:30:00Z",
            status="ok",
        )
        assert manifest["manifest_type"] == "run"
        assert manifest["run_id"] == "run-001"
        assert manifest["checksum"] != ""

    def test_with_all_fields(self):
        manifest = build_run_manifest(
            run_id="run-002",
            started_at="2026-06-15T10:00:00Z",
            ended_at="2026-06-15T11:00:00Z",
            status="warn",
            source_counts={"arxiv": 10, "hn": 5},
            generated_pages=["page1", "page2"],
            output_count=2,
            notes=["some warning"],
        )
        assert manifest["output_count"] == 2
        assert manifest["source_counts"]["arxiv"] == 10
