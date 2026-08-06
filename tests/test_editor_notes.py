"""Contract tests for core/editor_notes.py."""

import json

from core.editor_notes import attach_editor_notes, load_editor_notes


class Dummy:
    def __init__(self, slug):
        self.slug = slug
        self.editor_note = None


def test_load_editor_notes_missing_file(tmp_path):
    assert load_editor_notes(tmp_path / "nope.json") == {}


def test_load_editor_notes_malformed(tmp_path):
    p = tmp_path / "n.json"
    p.write_text("{not json", encoding="utf-8")
    assert load_editor_notes(p) == {}


def test_load_editor_notes_filters_blank_notes(tmp_path):
    p = tmp_path / "n.json"
    p.write_text(json.dumps({"a": {"note": "hello"}, "b": {"note": ""}, "c": {"note": None}}), encoding="utf-8")
    notes = load_editor_notes(p)
    assert notes == {"a": {"note": "hello"}}


def test_attach_by_full_slug(tmp_path):
    p = tmp_path / "n.json"
    p.write_text(json.dumps({"markets/research/x": {"note": "n"}}), encoding="utf-8")
    items = [Dummy("markets/research/x"), Dummy("markets/research/y")]
    assert attach_editor_notes(items, path=p) == 1
    assert items[0].editor_note == {"note": "n"}
    assert items[1].editor_note is None


def test_attach_by_topic_segment(tmp_path):
    p = tmp_path / "n.json"
    p.write_text(json.dumps({"x": {"note": "n"}}), encoding="utf-8")
    items = [Dummy("markets/research/x")]
    assert attach_editor_notes(items, path=p) == 1
    assert items[0].editor_note == {"note": "n"}


def test_attach_no_notes_is_noop(tmp_path):
    items = [Dummy("a")]
    assert attach_editor_notes(items, notes={}) == 0
    assert items[0].editor_note is None
