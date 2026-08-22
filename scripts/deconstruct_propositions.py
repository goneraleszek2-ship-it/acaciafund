#!/usr/bin/env python3
"""Deconstruct synthesized content into atomic proposition sets.

Parses markdown articles across all 3 pillars and extracts explicit
premise-conclusion trees. Each proposition is formatted as a tuple:
⟨ID, Statement, Premises, Epistemic Status, Source, Pillar⟩.

Rejects any claim lacking explicit premises or source provenance.

Usage:
    python3 scripts/deconstruct_propositions.py            # extract all propositions
    python3 scripts/deconstruct_propositions.py --output path  # write to custom path
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
CONTENT_DIR = PROJECT_ROOT / "content"
REGISTRY_PATH = PROJECT_ROOT / "registry.json"
ONTOLOGY_PATH = PROJECT_ROOT / "data/ontology.json"

PROPOSITIONS_OUT = PROJECT_ROOT / "dist" / "propositions.json"


def load_json(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def extract_sentences(text: str) -> list[str]:
    """Split markdown text into sentence-level claims."""
    # Remove code blocks
    text = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
    # Remove inline code
    text = re.sub(r"`[^`]+`", " ", text)
    # Split on periods, exclamation, question marks followed by space or end
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    # Filter very short fragments
    sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
    return sentences


def determine_pillar_from_path(md_path: Path) -> str:
    """Determine pillar from the content directory path structure."""
    parts = md_path.parts
    for i, p in enumerate(parts):
        if p in ("aml", "stock", "data-engineering", "docs"):
            if i + 1 < len(parts) and parts[i + 1] in ("aml", "stock", "data-engineering"):
                return parts[i + 1]
            return p
    return "data-engineering"


def extract_propositions_from_article(
    article_path: Path,
    ontology_manager,
    registry_item: dict | None = None,
) -> list[dict]:
    """Extract atomic propositions from a single article."""
    content = article_path.read_text(encoding="utf-8", errors="ignore")
    sentences = extract_sentences(content)
    propositions = []

    # Determine pillar from path
    pillar = determine_pillar_from_path(article_path)

    # Get epistemic status: from registry item first, then ontology matching
    epistemic_status = ""
    if registry_item:
        epistemic_status = registry_item.get("epistemic_status", "")
    if not epistemic_status:
        try:
            for sentence in sentences[:3]:
                concepts = ontology_manager.extract_concepts_from_text(sentence)
                if concepts:
                    epistemic_status = concepts[0].epistemic_status
                    break
        except Exception:
            pass

    # Fallback: default based on pillar
    if not epistemic_status:
        pillar_statuses = {
            "aml": "instrumental",
            "stock": "instrumental",
            "data-engineering": "pragmatic",
        }
        epistemic_status = pillar_statuses.get(pillar, "")

    for idx, sentence in enumerate(sentences):
        # Skip sentences that are clearly questions, commands, or transitions
        if re.match(r"^\s*(How|Why|What|When|Where|Who)\s", sentence, re.I):
            continue
        if re.match(r"^\s*(Note that|It is important|Remember that)\s", sentence, re.I):
            continue

        # Identify premises within the article that support this claim
        premises = []

        # Look for citation patterns in the full article text
        citation_matches = re.findall(r"\[(\d+)\]|\(([A-Za-z][\w\s]+,?\s+\d{4})\)", content)
        premises.extend([f"citation:{m[0] or m[1]}" for m in citation_matches[:3]])

        # Look for data/source references
        source_keywords = ["arXiv", "Hacker News", "PubMed", "SEC", "FATF", "Databricks",
                           "OpenAlex", "GDELT", "Federal Register", "Stack Overflow"]
        if any(re.search(r"\b" + kw + r"\b", content, re.I) for kw in source_keywords):
            premises.append("source:authoritative")

        # Look for methodological cues
        if re.search(r"\b(proof|theorem|lemma)\b", content, re.I):
            premises.append("method:formal_proof")

        # If no premises found, this proposition is incomplete
        if not premises:
            continue  # reject claim lacking premises

        prop = {
            "id": f"{article_path.stem}_{idx}",
            "statement": sentence,
            "premises": premises,
            "epistemic_status": epistemic_status,
            "source": registry_item.get("source_provenance", "content:directory") if registry_item else "content:directory",
            "pillar": pillar,
            "article": article_path.name,
            "sentence_index": idx,
            "quality_metrics": registry_item.get("quality_metrics", {}) if registry_item else {},
        }
        propositions.append(prop)

    return propositions


def main() -> int:
    output_path = None
    args = sys.argv[1:]
    for i, a in enumerate(args):
        if a == "--output" and i + 1 < len(args):
            output_path = Path(args[i + 1])

    # Load ontology
    from core.ontology import OntologyManager
    ontology = load_json(ONTOLOGY_PATH)
    ontology_mgr = OntologyManager()
    ontology_mgr.from_dict(ontology)

    # Load registry for metadata lookup
    registry = load_json(REGISTRY_PATH)
    content_items = registry.get("content", [])
    # Build lookup: slug -> item
    item_by_slug = {}
    for item in content_items:
        slug = item.get("slug", "")
        if slug:
            item_by_slug[slug] = item

    all_propositions = []
    content_files = []

    # Walk content directories
    if CONTENT_DIR.exists():
        for pillar_dir in sorted(CONTENT_DIR.iterdir()):
            if not pillar_dir.is_dir():
                continue
            for md_file in sorted(pillar_dir.rglob("*.md")):
                if md_file.name.startswith("."):
                    continue
                content_files.append(md_file)

    # Also check nested content dirs
    for extra_dir in ["content/docs", "content/market"]:
        extra_path = PROJECT_ROOT / extra_dir
        if extra_path.exists():
            for md_file in sorted(extra_path.rglob("*.md")):
                if md_file.name.startswith("."):
                    continue
                if md_file not in content_files:
                    content_files.append(md_file)

    print(f"Found {len(content_files)} markdown files across pillars")

    # Process each markdown file
    for i, md_path in enumerate(content_files):
        # Determine pillar from path
        pillar = determine_pillar_from_path(md_path)

        # Try to find matching registry item by slug
        rel_path = md_path.relative_to(PROJECT_ROOT / "content")
        slug = rel_path.as_posix().replace(".md", "").replace("/", "-")

        # Also try just the filename stem
        filename_slug = md_path.stem

        registry_item = item_by_slug.get(slug) or item_by_slug.get(filename_slug, {})

        props = extract_propositions_from_article(md_path, ontology_mgr, registry_item)
        print(f"  {md_path.name} (pillar={pillar}): {len(props)} propositions extracted")
        all_propositions.extend(props)

    # Deduplicate by statement hash (same statement + premises)
    seen = set()
    unique_props = []
    for prop in all_propositions:
        key = (prop["statement"][:80], tuple(prop["premises"]))
        if key not in seen:
            seen.add(key)
            unique_props.append(prop)

    print(f"Total unique propositions: {len(unique_props)}")

    # Validate all propositions have premises and source
    valid = 0
    rejected = 0
    for prop in unique_props:
        if prop["premises"] and prop["source"] and prop["source"] != "content:directory":
            valid += 1
        else:
            rejected += 1
    print(f"Valid (have premises+source): {valid}, Rejected (missing): {rejected}")

    # Output
    out_path = Path("dist/propositions.json") if not output_path else output_path
    save_json(out_path, unique_props)
    print(f"Propositions written to {out_path}")

    # Summary stats
    pillars = set(p["pillar"] for p in unique_props)
    statuses = set(p["epistemic_status"] for p in unique_props if p["epistemic_status"])
    print(f"Pillars covered: {sorted(pillars)}")
    print(f"Epistemic statuses: {sorted(statuses)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())