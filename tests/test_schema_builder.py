"""Tests for core/schema_builder.py — prerequisite graphs, learning paths, Bloom categorization."""

import pytest

from core.ontology import Concept, OntologyManager, Relation
from core.schema_builder import (
    LearningPath,
    build_concept_dag,
    build_prerequisite_graph,
    categorize_by_bloom,
    compute_feynman_learning_paths,
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

    def test_mid_chain_is_understand(self, acyclic_manager):
        """streaming is at depth 1 from root apache-kafka → understand"""
        graph = build_prerequisite_graph(acyclic_manager)
        level = categorize_by_bloom("streaming", graph)
        assert level == "understand"

    def test_deep_node_is_evaluate(self):
        """Chain of 5 nodes (a->b->c->d->e), 'e' is at depth 4 → evaluate."""
        mgr = OntologyManager()
        for cid in ["a", "b", "c", "d", "e"]:
            mgr.add_concept(Concept(id=cid, label=f"Concept {cid}", pillar="aml"))
        for src, tgt in [("a", "b"), ("b", "c"), ("c", "d"), ("d", "e")]:
            mgr.add_relation(Relation(source_id=src, target_id=tgt, relation_type="requires"))
        graph = build_prerequisite_graph(mgr)
        level = categorize_by_bloom("e", graph)
        assert level == "evaluate", f"Got {level}"

    def test_deep_node_is_create(self):
        """Chain of 6 nodes (a->b->c->d->e->f), 'f' is at depth 5 → create."""
        mgr = OntologyManager()
        for cid in ["a", "b", "c", "d", "e", "f"]:
            mgr.add_concept(Concept(id=cid, label=f"Concept {cid}", pillar="aml"))
        for src, tgt in [("a", "b"), ("b", "c"), ("c", "d"), ("d", "e"), ("e", "f")]:
            mgr.add_relation(Relation(source_id=src, target_id=tgt, relation_type="requires"))
        graph = build_prerequisite_graph(mgr)
        level = categorize_by_bloom("f", graph)
        assert level == "create", f"Got {level}"

    def test_unknown_concept(self, acyclic_manager):
        level = categorize_by_bloom("nonexistent", build_prerequisite_graph(acyclic_manager))
        assert level == "remember"

    def test_single_node_graph(self):
        mgr = OntologyManager()
        mgr.add_concept(Concept(id="lonely", label="Lonely", pillar="aml"))
        graph = build_prerequisite_graph(mgr)
        level = categorize_by_bloom("lonely", graph)
        assert level == "remember"


# ---------------------------------------------------------------------------
# compute_feynman_learning_paths
# ---------------------------------------------------------------------------


@pytest.fixture
def feynman_manager():
    """Ontology with concepts having Feynman metadata for path testing."""
    mgr = OntologyManager()
    for cid, label, pillar, fd in [
        ("a", "Concept A", "aml", 1),
        ("b", "Concept B", "aml", 2),
        ("c", "Concept C", "aml", 3),
        ("d", "Concept D", "aml", 4),
    ]:
        c = Concept(id=cid, label=label, pillar=pillar, feynman_difficulty=fd)
        c.eli5_explanation = f"ELI5 for {label}"
        c.analogy = f"Analogy for {label}"
        c.concrete_example = f"Example for {label}"
        c.gap_questions = [f"Gap Q for {label}"]
        c.teach_back_prompt = f"Teach {label}"
        c.build_exercise = {"type": "code", "prompt": f"Build {label}", "solution": "done"}
        mgr.add_concept(c)
    return mgr


class TestFeynmanLearningPaths:
    def test_returns_per_pillar(self, feynman_manager):
        paths = compute_feynman_learning_paths(feynman_manager)
        assert len(paths) == 1  # only 'aml' pillar
        assert paths[0].pillar == "aml"

    def test_has_all_stages(self, feynman_manager):
        paths = compute_feynman_learning_paths(feynman_manager)
        stages = [s.stage_type for s in paths[0].stages]
        assert "eli5" in stages
        assert "analogy" in stages
        assert "concrete" in stages
        assert "gap_map" in stages
        assert "build" in stages
        assert "teach_back" in stages

    def test_eli5_stage_only_diff1_2(self, feynman_manager):
        """ELI5 stage should only include difficulty 1-2 concepts."""
        paths = compute_feynman_learning_paths(feynman_manager)
        eli5_stage = next(s for s in paths[0].stages if s.stage_type == "eli5")
        for cid in eli5_stage.concept_ids:
            c = feynman_manager.get_concept(cid)
            assert c is not None
            assert c.feynman_difficulty <= 2

    def test_build_stage_has_build_exercises(self, feynman_manager):
        paths = compute_feynman_learning_paths(feynman_manager)
        build_stage = next(s for s in paths[0].stages if s.stage_type == "build")
        for cid in build_stage.concept_ids:
            c = feynman_manager.get_concept(cid)
            assert c is not None
            assert c.build_exercise is not None

    def test_total_concepts(self, feynman_manager):
        paths = compute_feynman_learning_paths(feynman_manager)
        assert paths[0].total_concepts == 4  # all 4 aml concepts

    def test_difficulty_tiers(self, feynman_manager):
        paths = compute_feynman_learning_paths(feynman_manager)
        assert 1 in paths[0].difficulty_tiers
        assert 2 in paths[0].difficulty_tiers
        assert 3 in paths[0].difficulty_tiers
        assert 4 in paths[0].difficulty_tiers

    def test_all_concepts_in_at_least_one_stage(self, feynman_manager):
        paths = compute_feynman_learning_paths(feynman_manager)
        all_in_stages = set()
        for stage in paths[0].stages:
            all_in_stages.update(stage.concept_ids)
        for c in feynman_manager._concepts:
            assert c in all_in_stages, f"Concept {c} missing from all stages"

    def test_empty_ontology_returns_empty(self):
        mgr = OntologyManager()
        paths = compute_feynman_learning_paths(mgr)
        assert len(paths) == 0

    def test_concepts_without_feynman_data_handled(self):
        mgr = OntologyManager()
        mgr.add_concept(Concept(id="plain", label="Plain", pillar="aml"))
        paths = compute_feynman_learning_paths(mgr)
        # Should not crash; plain has no feynman fields but still diffs into gap_map stage
        assert len(paths) == 1

    def test_prerequisite_ordering(self, feynman_manager):
        """Add a prerequisite edge and verify topological ordering."""
        feynman_manager.add_relation(Relation(
            source_id="b", target_id="a", relation_type="requires"
        ))
        paths = compute_feynman_learning_paths(feynman_manager)
        eli5_stage = next(s for s in paths[0].stages if s.stage_type == "eli5")
        # 'a' should come before 'b' (a is prerequisite of b)
        idx_a = eli5_stage.concept_ids.index("a")
        idx_b = eli5_stage.concept_ids.index("b")
        assert idx_a < idx_b, "Prerequisite should come before dependent"


# ---------------------------------------------------------------------------
# Concept DAG (Tier 3.2)
# ---------------------------------------------------------------------------


class TestBuildConceptDag:
    def test_center_node_present(self, acyclic_manager):
        dag = build_concept_dag(acyclic_manager, "etl")
        assert dag is not None
        assert dag["center"]["id"] == "etl"
        assert any(n["id"] == "etl" for n in dag["nodes"])
        assert dag["concept_id"] == "etl"

    def test_prerequisites_upstream(self, acyclic_manager):
        dag = build_concept_dag(acyclic_manager, "etl")
        # etl requires foundations -> foundations is a prerequisite
        assert "foundations" in [n["id"] for n in dag["nodes"]]
        # the prerequisite must be positioned LEFT of the center
        center_x = next(n["x"] for n in dag["nodes"] if n["id"] == "etl")
        foundations_x = next(n["x"] for n in dag["nodes"] if n["id"] == "foundations")
        assert foundations_x < center_x
        assert dag["edges"]

    def test_dependents_downstream(self, acyclic_manager):
        dag = build_concept_dag(acyclic_manager, "etl")
        center_x = next(n["x"] for n in dag["nodes"] if n["id"] == "etl")
        # elt requires etl -> elt is a dependent of etl
        elt_x = next(n["x"] for n in dag["nodes"] if n["id"] == "elt")
        assert elt_x > center_x

    def test_two_hop_depth(self, acyclic_manager):
        dag = build_concept_dag(acyclic_manager, "apache-kafka", depth=2)
        # apache-kafka requires streaming (hop 1); streaming requires foundations (hop 2)
        node_ids = {n["id"]: n for n in dag["nodes"]}
        assert "streaming" in node_ids
        assert "foundations" in node_ids
        assert node_ids["foundations"]["x"] < node_ids["streaming"]["x"] < node_ids["apache-kafka"]["x"]

    def test_depth_limit_respected(self, acyclic_manager):
        dag = build_concept_dag(acyclic_manager, "apache-kafka", depth=1)
        # with depth=1, foundations (2 hops away) must not appear
        assert "foundations" not in [n["id"] for n in dag["nodes"]]

    def test_max_per_layer_cap_and_truncation(self):
        mgr = OntologyManager()
        for cid in [f"c{i}" for i in range(6)] + ["root"]:
            mgr.add_concept(Concept(id=cid, label=f"Concept {cid}", pillar="aml"))
        for i in range(6):
            # root requires c{i} -> c{i} are prerequisites of root
            mgr.add_relation(Relation(source_id="root", target_id=f"c{i}", relation_type="requires"))
        dag = build_concept_dag(mgr, "root", depth=1, max_per_layer=2)
        up1_ids = [n["id"] for n in dag["nodes"] if n["id"] != "root"]
        assert len(up1_ids) == 2
        assert dag["truncated"].get("up1", 0) == 4

    def test_edges_follow_real_relations(self, acyclic_manager):
        dag = build_concept_dag(acyclic_manager, "etl")
        for edge in dag["edges"]:
            # drawn edge (from -> to) means: the right-hand concept requires
            # the left-hand one, i.e. relation source == edge["to"]
            rel = next(
                r for r in acyclic_manager._relations
                if r.source_id == edge["to"] and r.target_id == edge["from"]
                and r.relation_type == "requires"
            )
            assert rel is not None

    def test_no_requires_relations_returns_none(self):
        mgr = OntologyManager()
        mgr.add_concept(Concept(id="solo", label="Solo", pillar="aml"))
        assert build_concept_dag(mgr, "solo") is None

    def test_missing_concept_returns_none(self, acyclic_manager):
        assert build_concept_dag(acyclic_manager, "does-not-exist") is None

    def test_svg_geometry_valid(self, acyclic_manager):
        dag = build_concept_dag(acyclic_manager, "etl")
        assert dag["width"] > 0 and dag["height"] > 0
        for node in dag["nodes"]:
            assert node["x"] >= 0 and node["y"] >= 0
            assert node["w"] > 0 and node["h"] > 0
        for edge in dag["edges"]:
            assert edge["d"].startswith("M ") and "C " in edge["d"]
