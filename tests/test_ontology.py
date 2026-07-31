"""Tests for core/ontology.py — Concept, Relation, ResourceLink models and OntologyManager."""

import tempfile
from pathlib import Path

import pytest

from core.ontology import (
    CROSS_PILLAR_SEEDS,
    PILLAR_CONCEPT_SEEDS,
    PILLAR_RELATION_SEEDS,
    RELATION_TYPES,
    Concept,
    InspirationSource,
    OntologyManager,
    Relation,
    ResourceLink,
    extract_concepts_from_text,
)

# ---------------------------------------------------------------------------
# Model validation tests
# ---------------------------------------------------------------------------


class TestConceptModel:
    def test_basic_creation(self):
        c = Concept(id="test", label="Test Concept", pillar="aml")
        assert c.id == "test"
        assert c.label == "Test Concept"
        assert c.pillar == "aml"
        assert c.category == "reference"
        assert c.confidence_score == 1.0
        assert c.aliases == []
        assert c.properties == {}

    def test_with_aliases(self):
        c = Concept(
            id="kyc", label="Know Your Customer", pillar="aml",
            aliases=["KYC", "know-your-customer"],
        )
        assert len(c.aliases) == 2

    def test_confidence_bounds(self):
        with pytest.raises(Exception):
            Concept(id="t", label="T", pillar="aml", confidence_score=1.5)
        with pytest.raises(Exception):
            Concept(id="t", label="T", pillar="aml", confidence_score=-0.1)

    def test_serialization_roundtrip(self):
        c = Concept(id="test", label="Test", pillar="data-engineering",
                     properties={"tier": 1})
        d = c.model_dump()
        c2 = Concept(**d)
        assert c2.id == c.id
        assert c2.properties == c.properties


class TestRelationModel:
    def test_basic_creation(self):
        r = Relation(source_id="a", target_id="b", relation_type="requires")
        assert r.source_id == "a"
        assert r.target_id == "b"
        assert r.relation_type == "requires"
        assert r.strength == 1.0

    def test_strength_bounds(self):
        with pytest.raises(Exception):
            Relation(source_id="a", target_id="b", relation_type="x", strength=1.1)

    def test_serialization_roundtrip(self):
        r = Relation(source_id="a", target_id="b", relation_type="enables",
                     pillar="aml", evidence=["doc1"])
        d = r.model_dump()
        r2 = Relation(**d)
        assert r2.evidence == ["doc1"]


class TestResourceLinkModel:
    def test_basic_creation(self):
        rl = ResourceLink(concept_id="kyc", url="https://fatf-gafi.org", title="FATF")
        assert rl.concept_id == "kyc"
        assert rl.credibility_score == 0.5
        assert rl.access_date  # should be auto-populated

    def test_serialization_roundtrip(self):
        rl = ResourceLink(concept_id="c", url="https://x.com", source_org="Test")
        d = rl.model_dump()
        rl2 = ResourceLink(**d)
        assert rl2.source_org == "Test"


# ---------------------------------------------------------------------------
# OntologyManager tests
# ---------------------------------------------------------------------------


class TestOntologyManager:
    def test_empty_manager(self):
        mgr = OntologyManager()
        assert mgr.concept_count() == 0
        assert mgr.relation_count() == 0

    def test_add_concept(self):
        mgr = OntologyManager()
        c = Concept(id="kyc", label="KYC", pillar="aml")
        mgr.add_concept(c)
        assert mgr.concept_count() == 1
        assert mgr.get_concept("kyc") is not None

    def test_add_concept_no_overwrite(self):
        mgr = OntologyManager()
        c1 = Concept(id="kyc", label="KYC v1", pillar="aml")
        c2 = Concept(id="kyc", label="KYC v2", pillar="aml")
        mgr.add_concept(c1)
        mgr.add_concept(c2)
        c = mgr.get_concept("kyc")
        assert c is not None
        assert c.label == "KYC v1"

    def test_add_concept_overwrite(self):
        mgr = OntologyManager()
        c1 = Concept(id="kyc", label="KYC v1", pillar="aml")
        c2 = Concept(id="kyc", label="KYC v2", pillar="aml")
        mgr.add_concept(c1)
        mgr.add_concept(c2, overwrite=True)
        c = mgr.get_concept("kyc")
        assert c is not None
        assert c.label == "KYC v2"

    def test_alias_resolution(self):
        mgr = OntologyManager()
        c = Concept(id="kyc", label="Know Your Customer", pillar="aml",
                     aliases=["KYC"])
        mgr.add_concept(c)
        resolved = mgr.resolve_alias("KYC")
        assert resolved is not None
        assert resolved.id == "kyc"
        assert mgr.resolve_alias("unknown") is None

    def test_find_concepts_by_pillar(self):
        mgr = OntologyManager()
        mgr.add_concept(Concept(id="a", label="A", pillar="aml"))
        mgr.add_concept(Concept(id="b", label="B", pillar="stock"))
        mgr.add_concept(Concept(id="c", label="C", pillar="aml"))
        aml_concepts = mgr.find_concepts(pillar="aml")
        assert len(aml_concepts) == 2
        stock_concepts = mgr.find_concepts(pillar="stock")
        assert len(stock_concepts) == 1

    def test_find_concepts_by_text_query(self):
        mgr = OntologyManager()
        mgr.add_concept(Concept(id="kyc", label="Know Your Customer", pillar="aml"))
        mgr.add_concept(Concept(id="sar", label="Suspicious Activity Report", pillar="aml"))
        results = mgr.find_concepts(text_query="suspicious")
        assert len(results) == 1
        assert results[0].id == "sar"

    def test_concepts_by_pillar(self):
        mgr = OntologyManager()
        mgr.add_concept(Concept(id="a", label="A", pillar="aml"))
        mgr.add_concept(Concept(id="b", label="B", pillar="stock"))
        grouped = mgr.concepts_by_pillar()
        assert "aml" in grouped
        assert "stock" in grouped
        assert len(grouped["aml"]) == 1


class TestOntologyRelations:
    def test_add_relation(self):
        mgr = OntologyManager()
        mgr.add_concept(Concept(id="a", label="A", pillar="aml"))
        mgr.add_concept(Concept(id="b", label="B", pillar="aml"))
        mgr.add_relation(Relation(source_id="a", target_id="b", relation_type="requires"))
        assert mgr.relation_count() == 1

    def test_self_relation_rejected(self):
        mgr = OntologyManager()
        mgr.add_concept(Concept(id="a", label="A", pillar="aml"))
        mgr.add_relation(Relation(source_id="a", target_id="a", relation_type="requires"))
        assert mgr.relation_count() == 0

    def test_dedup_merge(self):
        mgr = OntologyManager()
        mgr.add_concept(Concept(id="a", label="A", pillar="aml"))
        mgr.add_concept(Concept(id="b", label="B", pillar="aml"))
        mgr.add_relation(Relation(source_id="a", target_id="b", relation_type="requires"))
        mgr.add_relation(Relation(source_id="a", target_id="b", relation_type="requires",
                                   strength=0.5, evidence=["doc1"]))
        assert mgr.relation_count() == 1
        r = mgr.outgoing_relations("a")[0]
        assert r.strength == 1.0  # kept max
        assert "doc1" in r.evidence

    def test_related_concepts(self):
        mgr = OntologyManager()
        mgr.add_concept(Concept(id="a", label="A", pillar="aml"))
        mgr.add_concept(Concept(id="b", label="B", pillar="aml"))
        mgr.add_concept(Concept(id="c", label="C", pillar="aml"))
        mgr.add_relation(Relation(source_id="a", target_id="b", relation_type="enables"))
        mgr.add_relation(Relation(source_id="c", target_id="a", relation_type="requires"))
        related = mgr.related_concepts("a")
        related_ids = {c.id for c in related}
        assert "b" in related_ids
        assert "c" in related_ids


class TestOntologyResourceLinks:
    def test_add_and_query(self):
        mgr = OntologyManager()
        mgr.add_concept(Concept(id="kyc", label="KYC", pillar="aml"))
        rl = ResourceLink(concept_id="kyc", url="https://fatf-gafi.org")
        mgr.add_resource_link(rl)
        links = mgr.resource_links_for("kyc")
        assert len(links) == 1
        assert links[0].url == "https://fatf-gafi.org"
        assert mgr.resource_links_for("unknown") == []


class TestOntologyPersistence:
    def test_save_and_load(self):
        mgr = OntologyManager()
        mgr.add_concept(Concept(id="kyc", label="KYC", pillar="aml"))
        mgr.add_concept(Concept(id="sar", label="SAR", pillar="aml"))
        mgr.add_relation(Relation(source_id="kyc", target_id="sar", relation_type="related_to"))
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "ontology.json"
            mgr.save(path)
            loaded = OntologyManager.load(path)
        assert loaded.concept_count() == 2
        assert loaded.relation_count() == 1
        assert loaded.get_concept("kyc") is not None

    def test_load_nonexistent(self):
        mgr = OntologyManager.load(Path("/nonexistent/path/ontology.json"))
        assert mgr.concept_count() == 0


class TestOntologySeeding:
    def test_seed_all_pillars(self):
        mgr = OntologyManager()
        count = mgr.seed_all_pillars()
        assert count > 0
        assert mgr.concept_count() == count
        # Each pillar should have concepts
        for pillar in ["aml", "stock", "data-engineering"]:
            concepts = mgr.find_concepts(pillar=pillar)
            assert len(concepts) > 0, f"No concepts for pillar {pillar}"

    def test_seed_relations(self):
        mgr = OntologyManager()
        mgr.seed_all_pillars()
        count = mgr.seed_relations()
        assert count > 0
        assert mgr.relation_count() == count

    def test_seed_idempotent(self):
        mgr = OntologyManager()
        mgr.seed_all_pillars()
        first_count = mgr.concept_count()
        mgr.seed_all_pillars()  # should not add duplicates
        assert mgr.concept_count() == first_count


class TestOntologyGraphExport:
    def test_to_cytograph_nodes(self):
        mgr = OntologyManager()
        mgr.add_concept(Concept(id="test", label="Test", pillar="aml"))
        nodes = mgr.to_cytograph_nodes()
        assert len(nodes) == 1
        assert nodes[0]["data"]["id"] == "ont:test"
        assert nodes[0]["data"]["type"] == "concept"

    def test_to_cytograph_edges(self):
        mgr = OntologyManager()
        mgr.add_concept(Concept(id="a", label="A", pillar="aml"))
        mgr.add_concept(Concept(id="b", label="B", pillar="aml"))
        mgr.add_relation(Relation(source_id="a", target_id="b", relation_type="requires"))
        edges = mgr.to_cytograph_edges()
        assert len(edges) == 1
        assert edges[0]["data"]["source"] == "ont:a"
        assert edges[0]["data"]["target"] == "ont:b"

    def test_merge_into_cytograph(self):
        mgr = OntologyManager()
        mgr.add_concept(Concept(id="a", label="A", pillar="aml"))
        existing = {"nodes": [{"data": {"id": "ont:a", "label": "A"}}], "edges": []}
        merged = mgr.merge_into_cytograph(existing)
        # Should not duplicate existing nodes
        assert len(merged["nodes"]) == 1


class TestOntologyPillarSummary:
    def test_pillar_summary(self):
        mgr = OntologyManager()
        mgr.seed_all_pillars()
        mgr.seed_relations()
        summary = mgr.pillar_summary()
        assert "aml" in summary
        assert summary["aml"]["concepts"] > 0
        assert summary["aml"]["relations"] > 0


class TestConceptExtraction:
    def test_extract_from_text(self):
        mgr = OntologyManager()
        mgr.seed_all_pillars()
        text = "This article covers KYC compliance and suspicious activity reporting."
        matches = extract_concepts_from_text(text, mgr)
        matched_ids = {c.id for c, _ in matches}
        assert "kyc" in matched_ids or "sar" in matched_ids

    def test_extract_empty_text(self):
        mgr = OntologyManager()
        mgr.seed_all_pillars()
        matches = extract_concepts_from_text("", mgr)
        assert matches == []

    def test_extract_no_matches(self):
        mgr = OntologyManager()
        mgr.add_concept(Concept(id="x", label="Quantum Flux", pillar="aml"))
        matches = extract_concepts_from_text("hello world", mgr)
        assert matches == []


class TestInspirationSource:
    def test_basic_creation(self):
        src = InspirationSource(
            url="https://fatf-gafi.org", name="FATF",
            frequency="weekly", relevance=0.95,
        )
        assert src.url == "https://fatf-gafi.org"
        assert src.enabled is True
        assert src.last_fetched is None


# ---------------------------------------------------------------------------
# Pillar seed data tests
# ---------------------------------------------------------------------------


class TestPillarSeedData:
    def test_all_pillars_have_seeds(self):
        for pillar in ["aml", "stock", "data-engineering"]:
            assert pillar in PILLAR_CONCEPT_SEEDS
            assert len(PILLAR_CONCEPT_SEEDS[pillar]) >= 10

    def test_concept_ids_unique_per_pillar(self):
        for pillar, seeds in PILLAR_CONCEPT_SEEDS.items():
            ids = [s["id"] for s in seeds]
            assert len(ids) == len(set(ids)), f"Duplicate IDs in {pillar}"

    def test_relation_seeds_reference_valid_concepts(self):
        all_ids = set()
        for seeds in PILLAR_CONCEPT_SEEDS.values():
            for s in seeds:
                all_ids.add(s["id"])
        for src, tgt, rtype, pillar in PILLAR_RELATION_SEEDS:
            assert src in all_ids, f"Unknown source concept: {src}"
            assert tgt in all_ids, f"Unknown target concept: {tgt}"
            assert rtype in RELATION_TYPES, f"Unknown relation type: {rtype}"

    def test_cross_pillar_seeds_reference_valid_concepts(self):
        all_ids = set()
        for seeds in PILLAR_CONCEPT_SEEDS.values():
            for s in seeds:
                all_ids.add(s["id"])
        for src, tgt, rtype in CROSS_PILLAR_SEEDS:
            assert src in all_ids, f"Unknown cross-pillar source: {src}"
            assert tgt in all_ids, f"Unknown cross-pillar target: {tgt}"
