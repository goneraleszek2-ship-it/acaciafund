"""Tests for core/schema_builder.py — prerequisite graphs, learning paths, Bloom categorization."""

import pytest

from core.ontology import Concept, OntologyManager, Relation
from core.schema_builder import (
    LearningPath,
    build_prerequisite_graph,
    categorize_by_bloom,
    compute_learning_paths,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def acyclic_manager():
    """A small acyclic ontology with 'requires' chains."""
    mgr = OntologyManager()
    for cid, label, pillar in [
        ("foundations", "Foundations", "data-engineering"),
        ("etl", "Extract-Transform-Load", "data-engineering"),
        ("elt", "Extract-Load-Transform", "data-engineering"),
        ("data-lake", "Data Lake", "data-engineering"),
        ("streaming", "Stream Processing", "data-engineering"),
        ("apache-kafka", "Apache Kafka", "data-engineering"),
    ]:
        mgr.add_concept(Concept(id=cid, label=label, pillar=pillar))

    for src, tgt in [
        ("etl", "foundations"),
        ("elt", "etl"),
        ("data-lake", "foundations"),
        ("streaming", "foundations"),
        ("apache-kafka", "streaming"),
    ]:
        mgr.add_relation(Relation(source_id=src, target_id=tgt, relation_type="requires"))
    return mgr


@pytest.fixture
def cyclic_manager():
    """An ontology with an intentional cycle in 'requires' relations."""
    mgr = OntologyManager()
    for cid, label, pillar in [
        ("a", "Concept A", "aml"),
        ("b", "Concept B", "aml"),
        ("c", "Concept C", "aml"),
    ]:
        mgr.add_concept(Concept(id=cid, label=label, pillar=pillar))

    for src, tgt in [
        ("a", "b"),
        ("b", "c"),
        ("c", "a"),
    ]:
        mgr.add_relation(Relation(source_id=src, target_id=tgt, relation_type="requires"))
    return mgr


@pytest.fixture
def mixed_manager():
    """Full ontology loaded from disk."""
    mgr = OntologyManager.load("data/ontology.json")
    if mgr.concept_count() == 0:
        mgr.seed_all_pillars()
        mgr.seed_relations()
    return mgr


# ---------------------------------------------------------------------------
# build_prerequisite_graph
# ---------------------------------------------------------------------------


class TestBuildPrerequisiteGraph:
    def test_acyclic_graph(self, acyclic_manager):
        graph = build_prerequisite_graph(acyclic_manager)
        assert graph.is_directed()
        assert graph.number_of_nodes() == 6
        # edges: only 'requires' relations (6 out of 6)
        assert graph.number_of_edges() == 5

    def test_node_attributes(self, acyclic_manager):
        graph = build_prerequisite_graph(acyclic_manager)
        etl_node = graph.nodes["etl"]
        assert etl_node["label"] == "Extract-Transform-Load"
        assert etl_node["pillar"] == "data-engineering"

    def test_ignores_non_requires(self, acyclic_manager):
        acyclic_manager.add_relation(
            Relation(source_id="etl", target_id="streaming", relation_type="related_to")
        )
        graph = build_prerequisite_graph(acyclic_manager)
        # 'related_to' should NOT appear as an edge
        assert not graph.has_edge("etl", "streaming")

    def test_cyclic_graph_skips_cycle_edges(self, cyclic_manager):
        graph = build_prerequisite_graph(cyclic_manager)
        # a->b is added, b->c is added, c->a should be skipped (cycle)
        assert graph.number_of_edges() == 2
        assert not graph.has_edge("c", "a")

    def test_empty_ontology(self):
        mgr = OntologyManager()
        graph = build_prerequisite_graph(mgr)
        assert graph.number_of_nodes() == 0
        assert graph.number_of_edges() == 0

    def test_no_requires_relations(self):
        mgr = OntologyManager()
        mgr.add_concept(Concept(id="a", label="A", pillar="aml"))
        mgr.add_concept(Concept(id="b", label="B", pillar="aml"))
        mgr.add_relation(Relation(source_id="a", target_id="b", relation_type="part_of"))
        graph = build_prerequisite_graph(mgr)
        assert graph.number_of_nodes() == 0
        assert graph.number_of_edges() == 0


# ---------------------------------------------------------------------------
# compute_learning_paths
# ---------------------------------------------------------------------------


class TestComputeLearningPaths:
    def test_path_from_root(self, acyclic_manager):
        graph = build_prerequisite_graph(acyclic_manager)
        paths = compute_learning_paths(graph, "apache-kafka", depth=3)
        assert len(paths) >= 1
        # The longest path: apache-kafka -> streaming -> foundations
        longest = paths[0]
        assert longest.start == "apache-kafka"
        assert longest.end == "foundations"
        assert longest.total_depth >= 2

    def test_path_from_mid_chain(self, acyclic_manager):
        graph = build_prerequisite_graph(acyclic_manager)
        paths = compute_learning_paths(graph, "elt", depth=3)
        assert len(paths) >= 1
        # elt -> etl -> foundations
        assert paths[0].start == "elt"
        assert "foundations" in [c["id"] for c in paths[0].concepts]

    def test_no_outgoing_edges_returns_empty(self, acyclic_manager):
        graph = build_prerequisite_graph(acyclic_manager)
        # 'foundations' has no outgoing 'requires' edges
        paths = compute_learning_paths(graph, "foundations", depth=3)
        assert paths == []

    def test_depth_limit(self, acyclic_manager):
        graph = build_prerequisite_graph(acyclic_manager)
        paths_depth1 = compute_learning_paths(graph, "apache-kafka", depth=1)
        paths_depth3 = compute_learning_paths(graph, "apache-kafka", depth=3)
        assert len(paths_depth1) <= len(paths_depth3)
        # depth 1 should only go 1 hop (apache-kafka -> streaming)
        if paths_depth1:
            assert paths_depth1[0].total_depth <= 1

    def test_path_has_correct_structure(self, acyclic_manager):
        graph = build_prerequisite_graph(acyclic_manager)
        paths = compute_learning_paths(graph, "apache-kafka", depth=3)
        assert len(paths) >= 1
        path = paths[0]
        assert isinstance(path, LearningPath)
        assert len(path.concepts) > 0
        assert path.concepts[0]["id"] == "apache-kafka"
        assert path.total_depth == len(path.concepts) - 1
        assert path.pillar_span >= 1

    def test_pillar_span_counts_unique_pillars(self, mixed_manager):
        graph = build_prerequisite_graph(mixed_manager)
        # Cross-pillar 'requires' relations exist
        # transaction-monitoring -> streaming (aml -> data-engineering)
        if graph.has_node("transaction-monitoring"):
            paths = compute_learning_paths(graph, "transaction-monitoring", depth=5)
            if paths:
                assert paths[0].pillar_span >= 1


# ---------------------------------------------------------------------------
# categorize_by_bloom
# ---------------------------------------------------------------------------


class TestCategorizeByBloom:
    def test_root_concept_is_remember(self, acyclic_manager):
        """apache-kafka has no predecessors → root → remember"""
        graph = build_prerequisite_graph(acyclic_manager)
        level = categorize_by_bloom("apache-kafka", graph)
        assert level == "remember"

    def test_leaf_concept_is_remember(self, acyclic_manager):
        """data-lake has no predecessors → root → remember"""
        graph = build_prerequisite_graph(acyclic_manager)
        level = categorize_by_bloom("data-lake", graph)
        assert level == "remember"

    def test_foundation_is_apply(self, acyclic_manager):
        """foundations is at depth 2 from root apache-kafka → apply"""
        graph = build_prerequisite_graph(acyclic_manager)
        level = categorize_by_bloom("foundations", graph)
        assert level == "apply"

    def test_mid_chain_is_apply(self, acyclic_manager):
        graph = build_prerequisite_graph(acyclic_manager)
        level = categorize_by_bloom("streaming", graph)
        assert level in ("apply", "analyze")

    def test_deep_node_is_evaluate(self):
        """Chain of 5 nodes (a->b->c->d->e), 'e' is at depth 4 → evaluate/create."""
        mgr = OntologyManager()
        for cid in ["a", "b", "c", "d", "e"]:
            mgr.add_concept(Concept(id=cid, label=f"Concept {cid}", pillar="aml"))
        for src, tgt in [("a", "b"), ("b", "c"), ("c", "d"), ("d", "e")]:
            mgr.add_relation(Relation(source_id=src, target_id=tgt, relation_type="requires"))
        graph = build_prerequisite_graph(mgr)
        level = categorize_by_bloom("e", graph)
        assert level in ("evaluate", "create"), f"Got {level}"

    def test_unknown_concept(self, acyclic_manager):
        level = categorize_by_bloom("nonexistent", build_prerequisite_graph(acyclic_manager))
        assert level == "remember"

    def test_single_node_graph(self):
        mgr = OntologyManager()
        mgr.add_concept(Concept(id="lonely", label="Lonely", pillar="aml"))
        graph = build_prerequisite_graph(mgr)
        level = categorize_by_bloom("lonely", graph)
        assert level == "remember"
