"""Tests for core/learning_paths.py."""
import pytest

from core.learning_paths import (
    LearningJourney,
    PathNode,
    build_all_learning_paths,
    enrich_journeys_with_content,
    generate_cross_pillar_synthesis,
    generate_learning_path_context,
)
from core.ontology import Concept, OntologyManager, Relation
from core.schema_builder import LearningPath


@pytest.fixture
def manager():
    """Ontology with a small DAG: a->b->c."""
    mgr = OntologyManager()
    for cid, label, pillar in [
        ("a", "Concept A", "aml"),
        ("b", "Concept B", "stock"),
        ("c", "Concept C", "data-engineering"),
        ("d", "Concept D", "aml"),
    ]:
        mgr.add_concept(Concept(id=cid, label=label, pillar=pillar))
    mgr.add_relation(Relation(source_id="a", target_id="b", relation_type="requires"))
    mgr.add_relation(Relation(source_id="b", target_id="c", relation_type="requires"))
    return mgr


@pytest.fixture
def manager_no_relations():
    mgr = OntologyManager()
    mgr.add_concept(Concept(id="x", label="Concept X", pillar="aml"))
    return mgr


def test_build_paths_from_dag(manager):
    journeys = build_all_learning_paths(manager, max_depth=3)
    assert "a" in journeys
    j = journeys["a"]
    assert j.start_label == "Concept A"
    assert len(j.paths) >= 1
    assert j.paths[0].concepts[-1]["id"] == "c"
    assert len(j.nodes) == 3  # a, b, c


def test_no_paths_for_leaf_node(manager):
    journeys = build_all_learning_paths(manager, max_depth=3)
    assert "c" not in journeys  # leaf — no successors


def test_no_relations_yields_no_journeys(manager_no_relations):
    journeys = build_all_learning_paths(manager_no_relations, max_depth=3)
    assert len(journeys) == 0


def test_max_depth_limits_path_length(manager):
    journeys = build_all_learning_paths(manager, max_depth=1)
    j = journeys["a"]
    # With depth=1 from 'a', we only reach 'b', not 'c'
    assert all(p.total_depth <= 1 for p in j.paths)
    node_ids = {n.concept_id for n in j.nodes}
    assert "b" in node_ids
    assert "c" not in node_ids  # too deep


def test_enrich_journeys_with_content(manager):
    journeys = build_all_learning_paths(manager, max_depth=3)
    concept_content_map = {
        "a": [{"slug": "aml/research/a", "title": "A Research", "pillar": "aml", "content_type": "research"}],
        "b": [{"slug": "stock/learn/b", "title": "B Learn", "pillar": "stock", "content_type": "learn"}],
    }
    enriched = enrich_journeys_with_content(journeys, concept_content_map)
    j = enriched["a"]
    node_a = [n for n in j.nodes if n.concept_id == "a"][0]
    node_b = [n for n in j.nodes if n.concept_id == "b"][0]
    assert len(node_a.content["research"]) == 1
    assert len(node_b.content["learn"]) == 1
    assert len(node_a.content["learn"]) == 0


def test_generate_context_returns_dict(manager):
    journeys = build_all_learning_paths(manager, max_depth=3)
    pillar_config = {"aml": {"color": "#123456", "label": "AML"}}
    context = generate_learning_path_context(journeys["a"], pillar_config)
    assert context["journey_label"] == "Concept A"
    assert context["pillar_color"] == "#123456"
    assert context["start_concept_id"] == "a"
    assert context["path_count"] >= 1
    assert context["total_nodes"] == 3


def test_generate_cross_pillar_synthesis():
    class FakeItem:
        def __init__(self, slug, pillar, date_str, tags=None):
            self.slug = slug
            self.pillar = pillar
            self.date_str = date_str
            self.tags = tags or []
            self.title = slug
            self.description = ""
            self.body_html = ""
            self.content_type = "research"
            self.difficulty = ""
    all_content = [
        FakeItem("a1", "aml", "2026-01-15"),
        FakeItem("a2", "aml", "2026-02-10"),
        FakeItem("s1", "stock", "2026-01-20"),
        FakeItem("d1", "data-engineering", "2026-03-05"),
    ]
    concept_content_map = {
        "aml-risk": [
            {"pillar": "aml", "slug": "a1"},
            {"pillar": "stock", "slug": "s1"},
        ],
    }
    synthesis = generate_cross_pillar_synthesis(all_content, concept_content_map, {})
    assert synthesis["total_bridges"] == 1
    assert "aml-risk" in synthesis["bridges"]
    assert synthesis["bridges"]["aml-risk"]["span"] == 2
    assert len(synthesis["timeline"]) >= 3
    assert synthesis["pillar_counts"]["aml"] == 2


def test_path_node_auto_fields():
    node = PathNode(concept_id="x", label="X", pillar="aml", bloom_level="remember")
    assert node.content == {}


def test_learning_journey_construct():
    lp = LearningPath(concepts=[{"id": "a"}, {"id": "b"}])
    j = LearningJourney(start_concept_id="a", start_label="A", start_pillar="aml", paths=[lp], nodes=[])
    assert j.start_label == "A"
    assert len(j.paths) == 1
