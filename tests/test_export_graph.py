"""Tests for scripts/export_graph.py — deterministic Cytoscape payloads."""

import scripts.export_graph as export_graph


def test_edges_are_sorted_per_document(tmp_path, monkeypatch):
    items = [
        {"slug": "data/research/a", "title": "A", "tags": ["zeta", "alpha", "beta"]},
        {"slug": "data/research/b", "title": "B", "tags": ["gamma", "alpha"]},
    ]
    monkeypatch.setattr(export_graph, "load_registry", lambda: items)
    monkeypatch.setattr(export_graph, "OUTPUT_PATH", tmp_path / "cytograph.json")

    graph = export_graph.build_graph()

    targets = [
        edge["data"]["target"]
        for edge in graph["edges"]
        if edge["data"]["source"] == "doc:data/research/a"
    ]
    assert targets == ["tag:alpha", "tag:beta", "tag:zeta"]


def test_tag_nodes_are_sorted(tmp_path, monkeypatch):
    items = [
        {"slug": "data/research/a", "title": "A", "tags": ["zeta", "alpha"]},
    ]
    monkeypatch.setattr(export_graph, "load_registry", lambda: items)
    monkeypatch.setattr(export_graph, "OUTPUT_PATH", tmp_path / "cytograph.json")

    graph = export_graph.build_graph()

    tag_ids = [node["data"]["id"] for node in graph["nodes"] if node["data"]["type"] == "concept"]
    assert tag_ids == ["tag:alpha", "tag:zeta"]
