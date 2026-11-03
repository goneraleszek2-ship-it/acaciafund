"""Regression checks for the six P0 metadata corrections."""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = json.loads((ROOT / "registry.json").read_text(encoding="utf-8"))
ITEMS = {item["slug"]: item for item in REGISTRY["content"]}

EXPECTED = {
    "aml/research/aml-1": "Analysis of machine-learning approaches to AML transaction monitoring",
    "aml/research/aml-3": "Review of FinCEN's beneficial ownership reporting requirements",
    "aml/research/aml-4": "Analysis of the EU's 2024 AML package",
    "markets/research/science-5": "The LK-99 room-temperature superconductivity claim emerged in 2023",
    "markets/research/ai-regulation": "The EU AI Act has been in force since 1 August 2024",
    "data/research/dagster-2": "Deep dive into Dagster's asset-based orchestration model",
}

BANNED = [
    "7th Anti-Money Laundering Directive",
    "one year of FinCEN",
    "80% false positive",
    "five major European banks",
    "15 independent laboratories",
    "EU AI Act officially enters into force",
    "Dagster 2.0",
]


def _text(item):
    body = re.sub(r"<[^>]+>", " ", item.get("body_html") or "")
    return re.sub(r"\s+", " ", f"{item.get('description', '')} {body}")


def test_descriptions_trace_to_body():
    for slug, fragment in EXPECTED.items():
        item = ITEMS[slug]
        assert fragment in item["description"], f"description mismatch: {slug}"
        assert fragment in _text(item), f"description not traceable to body: {slug}"


def test_stale_claims_are_gone():
    for slug in EXPECTED:
        blob = _text(ITEMS[slug])
        for phrase in BANNED:
            assert phrase.lower() not in blob.lower(), f"{slug}: stale phrase {phrase!r}"
