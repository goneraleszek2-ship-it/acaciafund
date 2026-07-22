#!/usr/bin/env python3
"""
Auto-generate per-pillar glossary pages from ontology concepts and inspiration sources.

Creates /knowledge/{pillar}-glossary/ pages with:
- Concept definitions from the ontology
- Inspiration source links
- Cross-references between concepts

Output: Updates registry.json with new glossary entries.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import tomllib

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

ONTOLOGY_PATH = PROJECT_ROOT / "data" / "ontology.json"
REGISTRY_PATH = PROJECT_ROOT / "registry.json"
INSPIRATION_PATH = PROJECT_ROOT / "etc" / "pillars.toml"

PILLAR_META = {
    "aml": {
        "title": "Compliance Glossary",
        "slug": "compliance/glossary",
        "pillar": "aml",
        "description": "Key terms and definitions for AML, KYC, CFT, and financial compliance — sourced from FATF, ACAMS, FinCEN, and OFAC guidance.",
        "tags": ["compliance", "aml", "glossary", "reference", "knowledge"],
        "knowledge_category": "reference",
    },
    "stock": {
        "title": "Markets Glossary",
        "slug": "markets/glossary",
        "pillar": "stock",
        "description": "Key terms and definitions for financial markets, quantitative analysis, and portfolio management — sourced from SEC, BIS, AQR, and MSCI research.",
        "tags": ["markets", "finance", "glossary", "reference", "knowledge"],
        "knowledge_category": "reference",
    },
    "data-engineering": {
        "title": "Data Engineering Glossary",
        "slug": "data/glossary",
        "pillar": "data-engineering",
        "description": "Key terms and definitions for data engineering, DataOps, and analytics — sourced from Databricks, Apache, dbt, and cloud provider documentation.",
        "tags": ["data-engineering", "dataops", "glossary", "reference", "knowledge"],
        "knowledge_category": "reference",
    },
}


def load_ontology():
    """Load the ontology manager."""
    from core.ontology import OntologyManager
    if not ONTOLOGY_PATH.exists():
        return None
    return OntologyManager.load(ONTOLOGY_PATH)


def load_inspiration_sources():
    """Load inspiration sources from pillars.toml."""
    if not INSPIRATION_PATH.exists():
        return {}
    with open(INSPIRATION_PATH, "rb") as f:
        return tomllib.load(f).get("inspiration_sources", {})


def load_registry():
    """Load the content registry."""
    if REGISTRY_PATH.exists():
        with open(REGISTRY_PATH) as f:
            return json.load(f)
    return {"content": [], "pipeline_stages": {}}


def save_registry(registry):
    """Save the content registry."""
    with open(REGISTRY_PATH, "w") as f:
        json.dump(registry, f, indent=2, default=str)


def generate_glossary_body(pillar_key, concepts, relations, sources):
    """Generate Markdown body for a glossary page."""
    lines = []

    # Introduction
    lines.append(f"This glossary covers key concepts in {PILLAR_META[pillar_key]['title'].replace(' Glossary', '').lower()} as used across AcaciaFund's research, learning materials, and knowledge base.")
    lines.append("")

    # Concepts section
    lines.append("## Core Concepts")
    lines.append("")
    for concept in sorted(concepts, key=lambda c: c.label):
        aliases_text = ""
        if concept.aliases:
            aliases_text = f" *Also: {', '.join(concept.aliases)}*"
        lines.append(f"**{concept.label}**")
        lines.append("")
        if concept.description:
            lines.append(f"{concept.description}{aliases_text}")
        else:
            lines.append(f"{concept.label}{aliases_text}")
        lines.append("")

    # Relations section
    if relations:
        lines.append("## Relationships")
        lines.append("")
        # Group by source concept
        rel_by_source = {}
        for r in relations:
            src_label = next((c.label for c in concepts if c.id == r.source_id), r.source_id)
            tgt_label = next((c.label for c in concepts if c.id == r.target_id), r.target_id)
            rel_by_source.setdefault(src_label, []).append((r.relation_type, tgt_label))
        for src, rels in sorted(rel_by_source.items()):
            rel_strs = [f"{rtype} **{tgt}**" for rtype, tgt in rels]
            lines.append(f"- {src}: {', '.join(rel_strs)}")
        lines.append("")

    # Sources section
    if sources:
        lines.append("## Authoritative Sources")
        lines.append("")
        for src_name, src_info in sorted(sources.items()):
            if isinstance(src_info, dict) and "url" in src_info:
                lines.append(f"- **{src_info['name']}** — {src_info.get('description', '')} ([{src_info['url']}]({src_info['url']}))")
        lines.append("")

    return "\n".join(lines)


def main():
    print("=" * 60)
    print("Glossary Generator")
    print("=" * 60)

    ontology = load_ontology()
    if not ontology:
        print("  No ontology found. Skipping glossary generation.")
        return

    inspiration_sources = load_inspiration_sources()
    registry = load_registry()
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    existing_slugs = {item.get("slug") for item in registry.get("content", [])}
    new_glossaries = []

    for pillar_key, meta in PILLAR_META.items():
        print(f"\n  Generating {meta['title']}...")

        all_concepts = ontology.concepts_by_pillar()
        concepts = all_concepts.get(pillar_key, [])
        relations = [r for r in ontology._relations if r.pillar == pillar_key]
        pillar_prefix = {"aml": "aml", "stock": "ms", "data-engineering": "de"}.get(pillar_key, "")
        sources = inspiration_sources.get(pillar_prefix, {})

        if not concepts:
            print(f"    No concepts for {pillar_key}, skipping")
            continue

        body = generate_glossary_body(pillar_key, concepts, relations, sources)

        glossary_item = {
            "slug": meta["slug"],
            "title": meta["title"],
            "pillar": meta["pillar"],
            "content_type": "knowledge",
            "knowledge_category": meta["knowledge_category"],
            "tags": meta["tags"],
            "description": meta["description"],
            "date": now_str,
            "author": "AcaciaFund",
            "body_md": body,
            "body_html": f"<p>{meta['description']}</p>\n\n{body.replace(chr(10)*2, '</p><p>').replace(chr(10), '<br>')}",
            "bloom_questions": [
                {"level": "remember", "question": f"What are the core concepts in {meta['title'].replace(' Glossary', '')}?"},
                {"level": "understand", "question": "How do the concepts in this glossary relate to each other?"},
                {"level": "apply", "question": "How would you use these terms when analyzing a real-world scenario?"},
            ],
            "source_inspiration": True,
            "auto_generated": True,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "concept_count": len(concepts),
        }

        if meta["slug"] in existing_slugs:
            # Update existing entry
            for i, item in enumerate(registry["content"]):
                if item.get("slug") == meta["slug"]:
                    registry["content"][i] = glossary_item
                    print(f"    Updated existing: {meta['slug']}")
                    break
        else:
            registry["content"].append(glossary_item)
            existing_slugs.add(meta["slug"])
            print(f"    Created new: {meta['slug']}")

        print(f"    {len(concepts)} concepts, {len(relations)} relations, {len(sources) if isinstance(sources, dict) else 0} sources")
        new_glossaries.append(meta["slug"])

    # Update pipeline_stages
    if isinstance(registry.get("pipeline_stages"), dict):
        registry["pipeline_stages"]["glossary_generated"] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "count": len(new_glossaries),
            "slugs": new_glossaries,
        }

    save_registry(registry)
    print(f"\n  Registry updated: {len(new_glossaries)} glossary entries")


if __name__ == "__main__":
    main()
