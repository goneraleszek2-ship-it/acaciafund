"""Enrich ontology concepts with Feynman learning framework metadata.

Reads feynman_metadata.json and merges Feynman-specific fields
(eli5_explanation, analogy, concrete_example, etc.) into ontology.json.
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.ontology import OntologyManager  # noqa: E402

logger = logging.getLogger(__name__)

FEYNMAN_FIELDS = {
    "eli5_explanation",
    "analogy",
    "concrete_example",
    "feynman_diagram",
    "gap_questions",
    "teach_back_prompt",
    "build_exercise",
    "feynman_difficulty",
    "explanation_quality",
}


def enrich_feynman(
    ontology_path: str | Path,
    feynman_path: str | Path,
    output_path: str | Path | None = None,
) -> int:
    """Merge Feynman metadata into ontology.

    Args:
        ontology_path: Path to ontology.json
        feynman_path: Path to feynman_metadata.json
        output_path: Where to save enriched ontology (defaults to ontology_path)

    Returns:
        Number of concepts enriched.
    """
    manager = OntologyManager.load(ontology_path)

    with open(feynman_path) as f:
        feynman_data: Dict[str, Dict[str, Any]] = json.load(f)

    enriched = 0
    for concept_id, feynman_fields in feynman_data.items():
        concept = manager.get_concept(concept_id)
        if not concept:
            logger.warning("Concept '%s' not found in ontology — skipping", concept_id)
            continue

        for field, value in feynman_fields.items():
            if field in FEYNMAN_FIELDS:
                setattr(concept, field, value)

        enriched += 1

    save_path = Path(output_path or ontology_path)
    manager.save(save_path)
    logger.info(
        "Enriched %d concepts with Feynman metadata → %s",
        enriched,
        save_path,
    )
    return enriched


def generate_feynman_stub(
    concept_id: str, label: str, description: str, category: str,
) -> Dict[str, Any]:
    """Generate starter Feynman fields for a concept without manual metadata.

    Creates content from existing concept metadata (category, pillar, description).
    """
    cat_clean = category.replace("-", " ")
    desc = description or f"A core concept in {cat_clean}."
    desc_trunc = desc[:250] if len(desc) > 250 else desc

    # Derive analogy from category domain
    domain_analogies = {
        "cdd-kyc": "like checking IDs at a border crossing",
        "sar-str": "like a smoke alarm that triggers when something unusual happens",
        "risk-assessment": "like an insurance adjuster evaluating risk factors",
        "sanctions": "like a no-fly list for financial transactions",
        "transaction-monitoring": "like a security camera watching a bank vault 24/7",
        "regtech": "like a robotic process assistant automating compliance paperwork",
        "advanced-techniques": "like a master craftsman using specialized tools",
        "regulations": "like a rulebook that everyone in the game must follow",
        "foundations": "like the foundation of a building — invisible but load-bearing",
        "market-analysis": "like a weather forecast for financial markets",
        "strategies": "like a chess player thinking several moves ahead",
        "industry-analysis": "like a medical diagnosis of an entire industry",
        "architecture": "like a blueprint for a complex machine",
        "best-practices": "like a maintenance checklist for a power plant",
        "crypto-aml": "like a digital border patrol for virtual currencies",
    }
    analogy_base = domain_analogies.get(category, "like a specialized tool in a toolbox")

    # Derive build exercise type from category
    build_types = {
        "cdd-kyc": "checklist",
        "sar-str": "flowchart",
        "risk-assessment": "matrix",
        "sanctions": "code",
        "transaction-monitoring": "code",
        "regtech": "code",
        "advanced-techniques": "code",
        "regulations": "diagram",
        "foundations": "diagram",
        "market-analysis": "calc",
        "strategies": "calc",
        "industry-analysis": "diagram",
        "architecture": "diagram",
        "best-practices": "checklist",
        "crypto-aml": "code",
    }
    build_type = build_types.get(category, "diagram")

    return {
        "eli5_explanation": (
            f"{label} is a concept in {cat_clean}. "
            f"In simple terms, {desc_trunc[:200]}"
        ),
        "analogy": (
            f"Think of {label} {analogy_base} — "
            f"it helps you handle {cat_clean} tasks more effectively."
        ),
        "concrete_example": (
            f"Consider a scenario where {label} applies: "
            f"{desc_trunc[:200]}..."
        ),
        "gap_questions": [
            f"What are the key components or steps involved in {label}?",
            f"Can you explain {label} without using jargon?",
            f"What happens if {label} is not applied correctly?",
            f"How does {label} relate to other concepts in {cat_clean}?",
        ],
        "teach_back_prompt": (
            f"Explain {label} as if teaching a colleague who is new to "
            f"{cat_clean}. Cover: what it is, how it works, and why it matters."
        ),
        "build_exercise": {
            "type": build_type,
            "prompt": (
                f"Create a {build_type} that demonstrates {label} in "
                f"a real-world {cat_clean} scenario. "
                f"Walk through your design decisions."
            ),
            "solution": (
                f"A {build_type} for {label} should include: "
                f"1. The core components of {concept_id.replace('-', ' ')} "
                f"2. How they interact "
                f"3. Expected outcomes or outputs"
            ),
        },
        "feynman_difficulty": 2,
        "explanation_quality": 0.3,
    }


def enrich_all_with_stubs(ontology_path: str | Path, output_path: str | Path | None = None) -> int:
    """Enrich ALL ontology concepts, generating stubs for those without metadata."""
    manager = OntologyManager.load(ontology_path)

    feynman_path = Path(ontology_path).parent / "feynman_metadata.json"
    if feynman_path.exists():
        with open(feynman_path) as f:
            feynman_data: Dict[str, Dict[str, Any]] = json.load(f)
    else:
        feynman_data = {}

    enriched = 0
    for concept in manager._concepts.values():
        feynman_fields = feynman_data.get(concept.id, {})
        if not feynman_fields or all(
            getattr(concept, field, None) is None
            for field in FEYNMAN_FIELDS
        ):
            feynman_fields = generate_feynman_stub(
                concept.id, concept.label, concept.description, concept.category,
            )

        for field, value in feynman_fields.items():
            if field in FEYNMAN_FIELDS:
                setattr(concept, field, value)

        enriched += 1

    save_path = Path(output_path or ontology_path)
    manager.save(save_path)
    logger.info(
        "Enriched %d concepts with Feynman metadata (stubs included) -> %s",
        enriched, save_path,
    )
    return enriched


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    ontology_path = Path(__file__).parent.parent / "data" / "ontology.json"
    feynman_path = Path(__file__).parent.parent / "data" / "feynman_metadata.json"
    output_path = Path(__file__).parent.parent / "data" / "ontology.json"

    if "--all" in sys.argv:
        count = enrich_all_with_stubs(ontology_path, output_path)
    else:
        count = enrich_feynman(ontology_path, feynman_path, output_path)

    print(f"Done — enriched {count} concepts.")
