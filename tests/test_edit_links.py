"""Contract tests for core/edit_links.py (Tier 6.1 Edit-on-GitHub)."""

import json

from core.content import Content
from core.edit_links import (
    GITHUB_BASE,
    attach_edit_links,
    content_file_for_slug,
    edit_url_for_item,
    registry_line_for_slug,
)


def _registry(tmp_path, *slugs) -> str:
    path = tmp_path / "registry.json"
    # mirror the repo's serializer: json.dump(indent=2) keeps keys on own lines
    data = {"content": [{"slug": s, "title": s} for s in slugs]}
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return str(path)


def test_content_file_matches_topic(tmp_path):
    (tmp_path / "aml").mkdir()
    (tmp_path / "aml" / "temporal-graph-aml.md").write_text("# x", encoding="utf-8")
    assert content_file_for_slug("aml/research/temporal-graph-aml", tmp_path) == "aml/temporal-graph-aml.md"


def test_content_file_matches_dated_topic(tmp_path):
    (tmp_path / "aml").mkdir()
    (tmp_path / "aml" / "2026-06-29-transaction-monitoring-foundations.md").write_text("# x", encoding="utf-8")
    rel = content_file_for_slug("aml/research/transaction-monitoring-foundations", tmp_path)
    assert rel == "aml/2026-06-29-transaction-monitoring-foundations.md"


def test_content_file_case_insensitive(tmp_path):
    (tmp_path / "aml").mkdir()
    (tmp_path / "aml" / "UBO-Unwinding-Algorithms.md").write_text("# x", encoding="utf-8")
    assert content_file_for_slug("aml/research/ubo-unwinding-algorithms", tmp_path) == "aml/UBO-Unwinding-Algorithms.md"


def test_content_file_no_match_returns_none(tmp_path):
    (tmp_path / "aml").mkdir()
    (tmp_path / "aml" / "unrelated.md").write_text("# x", encoding="utf-8")
    assert content_file_for_slug("aml/research/other-topic", tmp_path) is None


def test_content_file_empty_slug():
    assert content_file_for_slug("") is None


def test_registry_line_lookup(tmp_path):
    reg = _registry(tmp_path, "aml/research/alpha", "data/learn/beta")
    lines = reg and registry_line_for_slug("data/learn/beta", __import__("pathlib").Path(reg))
    assert isinstance(lines, int) and lines > 0
    # the line must actually contain the slug
    with open(reg, encoding="utf-8") as f:
        assert "\"slug\": \"data/learn/beta\"" in f.read().splitlines()[lines - 1]


def test_registry_line_missing_slug(tmp_path):
    reg = _registry(tmp_path, "aml/research/alpha")
    assert registry_line_for_slug("nope/nope", __import__("pathlib").Path(reg)) is None


def test_edit_url_prefers_content_file(tmp_path):
    (tmp_path / "aml").mkdir()
    (tmp_path / "aml" / "core-foundations.md").write_text("# x", encoding="utf-8")
    item = Content(slug="aml/research/core-foundations", title="t", pillar="aml", content_type="research")
    link = edit_url_for_item(item, tmp_path / "registry.json")
    assert link is not None
    assert link["url"] == f"{GITHUB_BASE}/content/aml/core-foundations.md"


def test_edit_url_falls_back_to_registry_line(tmp_path):
    reg = _registry(tmp_path, "aml/research/alpha")
    item = Content(slug="aml/research/alpha", title="t", pillar="aml", content_type="research")
    link = edit_url_for_item(item, __import__("pathlib").Path(reg))
    assert link is not None
    assert link["url"].startswith(f"{GITHUB_BASE}/registry.json#L")
    assert link["path"] == "registry.json"


def test_edit_url_empty_slug_is_none(tmp_path):
    item = Content(slug="", title="t", pillar="aml", content_type="research")
    assert edit_url_for_item(item, tmp_path / "registry.json") is None


def test_attach_edit_links_counts_and_sets(tmp_path):
    reg = _registry(tmp_path, "aml/research/alpha")
    items = [Content(slug="aml/research/alpha", title="a", pillar="aml", content_type="research")]
    attached = attach_edit_links(items, __import__("pathlib").Path(reg))
    assert attached == 1
    assert items[0].edit_link is not None
    assert items[0].edit_link["path"] == "registry.json"


def test_attach_edit_links_clears_missing(tmp_path):
    items = [Content(slug="", title="a", pillar="aml", content_type="research")]
    attach_edit_links(items, tmp_path / "registry.json")
    assert items[0].edit_link is None
