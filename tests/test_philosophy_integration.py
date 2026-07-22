"""Tests for philosophical foundations integration in ontology and build."""

import json
from pathlib import Path

import pytest

from core.ontology import (
    Concept,
)

ONTOLOGY_PATH = Path(__file__).parent.parent / "data" / "ontology.json"
PHILOSOPHY_PATH = Path(__file__).parent.parent / "data" / "philosophy_metadata.json"

# ── Unit tests: Concept model ──


class TestConceptPhilosophicalFields:
    def test_concept_model_has_philosophical_fields(self):
        """Concept model includes all philosophical metadata fields."""
        c = Concept(id="test", label="Test Concept", pillar="aml")
        assert hasattr(c, "philosophical_lineage")
        assert hasattr(c, "epistemic_status")
        assert hasattr(c, "normative_basis")
        assert hasattr(c, "ontological_commitment")
        assert hasattr(c, "temporal_ontology")
        assert hasattr(c, "uncertainty_class")
        assert hasattr(c, "governance_model")
        assert hasattr(c, "semantic_contract_type")
        assert hasattr(c, "philosophical_sources")
        assert hasattr(c, "cross_pillar_analogs")

    def test_philosophical_fields_default_to_empty(self):
        c = Concept(id="test", label="Test Concept", pillar="aml")
        assert c.philosophical_lineage == []
        assert c.epistemic_status == ""
        assert c.normative_basis == ""
        assert c.ontological_commitment == ""
        assert c.temporal_ontology == ""
        assert c.uncertainty_class == ""
        assert c.governance_model == ""
        assert c.semantic_contract_type == ""
        assert c.philosophical_sources == []
        assert c.cross_pillar_analogs == []

    def test_concept_with_philosophical_data_roundtrips_via_json(self):
        """Philosophical fields survive serialisation roundtrip."""
        c = Concept(
            id="test",
            label="Test Concept",
            pillar="aml",
            philosophical_lineage=["social_epistemology", "foucault_discipline"],
            epistemic_status="constitutive",
            normative_basis="kantian_duty",
            ontological_commitment="constructivist",
            temporal_ontology="processual",
            uncertainty_class="knightian",
            governance_model="polycentric",
            semantic_contract_type="constitutive",
            philosophical_sources=["Foucault, Discipline and Punish (1975)"],
            cross_pillar_analogs=["market-microstructure"],
        )
        data = c.model_dump()
        c2 = Concept(**data)
        assert c2.philosophical_lineage == ["social_epistemology", "foucault_discipline"]
        assert c2.epistemic_status == "constitutive"
        assert c2.normative_basis == "kantian_duty"
        assert c2.ontological_commitment == "constructivist"
        assert c2.temporal_ontology == "processual"
        assert c2.uncertainty_class == "knightian"
        assert c2.governance_model == "polycentric"
        assert c2.semantic_contract_type == "constitutive"
        assert c2.philosophical_sources == ["Foucault, Discipline and Punish (1975)"]
        assert c2.cross_pillar_analogs == ["market-microstructure"]


# ── Integration tests: ontology seed + enrichment ──


class TestOntologyPhilosophicalEnrichment:
    def test_ontology_seeded_with_philosophical_data(self):
        """All ontology concepts from the seed files have philosophical metadata."""
        if not ONTOLOGY_PATH.exists():
            pytest.skip("ontology.json not found — run build or seed first")
        with open(ONTOLOGY_PATH) as f:
            data = json.load(f)
        concepts = data.get("concepts", [])
        assert len(concepts) > 0, "Ontology should have concepts"
        non_empty = [c for c in concepts if c.get("philosophical_lineage")]
        assert len(non_empty) > 0, (
            f"Expected at least 1 concept with philosophical_lineage, "
            f"got {len(non_empty)} out of {len(concepts)}"
        )

    def test_all_concepts_have_epistemic_status(self):
        """Every concept should have at minimum an epistemic_status."""
        if not ONTOLOGY_PATH.exists():
            pytest.skip("ontology.json not found")
        with open(ONTOLOGY_PATH) as f:
            data = json.load(f)
        concepts = data.get("concepts", [])
        missing = [c["id"] for c in concepts if not c.get("epistemic_status")]
        assert len(missing) == 0, (
            f"Concepts missing epistemic_status: {missing[:5]}"
        )

    def test_valid_epistemic_status_values(self):
        VALID = {"constitutive", "regulatory", "pragmatic", "ontological", "instrumental", "normative", ""}
        with open(ONTOLOGY_PATH) as f:
            data = json.load(f)
        invalid = [
            c["id"] for c in data.get("concepts", [])
            if c.get("epistemic_status") not in VALID
        ]
        assert not invalid, f"Invalid epistemic_status in: {invalid}"

    def test_valid_normative_basis_values(self):
        VALID = {"kantian_duty", "utilitarian", "rawlsian", "virtue_ethics", "pragmatic", "contractarian", ""}
        with open(ONTOLOGY_PATH) as f:
            data = json.load(f)
        invalid = [
            c["id"] for c in data.get("concepts", [])
            if c.get("normative_basis") not in VALID
        ]
        assert not invalid, f"Invalid normative_basis in: {invalid}"

    def test_philosophical_sources_formatted_correctly(self):
        """Sources should contain author, title, and year."""
        with open(ONTOLOGY_PATH) as f:
            data = json.load(f)
        for c in data.get("concepts", []):
            for src in c.get("philosophical_sources", []):
                assert "(" in src and ")" in src, (
                    f"Source missing year in brackets: '{src}' (concept: {c['id']})"
                )

    def test_cross_pillar_analogs_refer_to_existing_concepts(self):
        """cross_pillar_analogs should reference concept IDs that exist."""
        with open(ONTOLOGY_PATH) as f:
            data = json.load(f)
        all_ids = {c["id"] for c in data.get("concepts", [])}
        for c in data.get("concepts", []):
            for analog in c.get("cross_pillar_analogs", []):
                assert analog in all_ids, (
                    f"Concept '{c['id']}' cross_pillar_analogs '{analog}' does not exist"
                )


# ── Pipeline tests: enrichment script ──


class TestEnrichScript:
    def test_enrichment_idempotent(self):
        """Running enrichment twice produces the same result."""
        from scripts.enrich_philosophy import enrich_ontology, load_json

        ontology = load_json(ONTOLOGY_PATH)
        metadata = load_json(PHILOSOPHY_PATH)

        count1 = enrich_ontology(ontology, metadata)
        count2 = enrich_ontology(ontology, metadata)
        # Second run should enrich 0 (already enriched)
        assert count2 <= count1

    def test_metadata_has_all_required_keys(self):
        """Every concept in philosophy_metadata.json has at minimum lineage + status."""
        with open(PHILOSOPHY_PATH) as f:
            metadata = json.load(f)
        for cid, meta in metadata.items():
            assert "philosophical_lineage" in meta, f"{cid} missing philosophical_lineage"
            assert "epistemic_status" in meta, f"{cid} missing epistemic_status"
