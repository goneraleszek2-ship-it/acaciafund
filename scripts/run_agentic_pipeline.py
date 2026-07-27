"""
Orchestrator for the agentic pipeline.

Runs one or all agent phases (enrich, research, learn, glossary, synthesis)
against registry items, ontology concepts, or specified topics.

Usage:
    python scripts/run_agentic_pipeline.py --phase enrich --max-items 10
    python scripts/run_agentic_pipeline.py --phase research --pillar aml --topic "transaction monitoring"
    python scripts/run_agentic_pipeline.py --phase learn --max-items 5
    python scripts/run_agentic_pipeline.py --phase glossary
    python scripts/run_agentic_pipeline.py --phase synthesis --topic "AI for AML" --sources 3
    python scripts/run_agentic_pipeline.py --phase all
    python scripts/run_agentic_pipeline.py --phase all --dry-run
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

from loguru import logger
from rich import print as rprint
from rich.console import Console
from rich.table import Table

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.agents import (
    EnrichmentAgent,
    GlossaryAgent,
    LearnModuleGenerator,
    ResearcherAgent,
    SynthesisAgent,
)

REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
REGISTRY_PATH = REPOSITORY_ROOT / "registry.json"
ONTOLOGY_PATH = REPOSITORY_ROOT / "data" / "ontology.json"

console = Console()


def load_registry() -> list[dict[str, Any]]:
    if not REGISTRY_PATH.exists():
        logger.error(f"Registry not found: {REGISTRY_PATH}")
        return []
    data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    return data.get("content", [])


def load_ontology() -> dict[str, Any] | None:
    if not ONTOLOGY_PATH.exists():
        logger.warning(f"Ontology not found: {ONTOLOGY_PATH}")
        return None
    return json.loads(ONTOLOGY_PATH.read_text(encoding="utf-8"))


def save_registry(content: list[dict[str, Any]]):
    data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    data["content"] = content
    data["last_updated"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    REGISTRY_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


# ── Pipeline Phases ──


def run_enrichment(items: list[dict[str, Any]], max_items: int, dry_run: bool) -> int:
    agent = EnrichmentAgent()
    unenriched = [i for i in items if not i.get("enriched")]
    target = unenriched[:max_items]
    if not target:
        logger.info("No unenriched items to process")
        return 0
    logger.info(f"Enrichment: {len(target)} items (of {len(unenriched)} unenriched)")
    if dry_run:
        logger.info(f"  Would enrich: {[i['slug'] for i in target]}")
        return len(target)
    results = agent.enrich_batch(target, max_items=max_items)
    for item, result in zip(target, results):
        item["enriched"] = True
        item["enriched_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        item["sqi"] = result.sqi_score
        saved_tags: set[str] = set(item.get("tags", []))
        for t in result.tags:
            saved_tags.add(t.tag)
        item["tags"] = sorted(saved_tags)
    save_registry(items)
    logger.info(f"Enriched {len(results)} items")
    return len(results)


def run_research(pillar: str, topic: str, max_items: int, dry_run: bool) -> int:
    agent = ResearcherAgent()
    logger.info(f"Research: pillar={pillar}, topic={topic}, max={max_items}")
    if dry_run:
        logger.info(f"  Would research {max_items} items on '{topic}' in {pillar}")
        return max_items
    results = agent.research_topic(pillar=pillar, topic=topic, max_items=max_items)
    if not results:
        logger.warning("No research items generated")
        return 0
    registry_items = load_registry()
    new_count = 0
    for r in results:
        entry = {
            "slug": r.pillar + "/research/" + r.title.lower().replace(" ", "-")[:80],
            "title": r.title,
            "description": r.description,
            "body_html": r.body_html,
            "pillar": r.pillar,
            "content_type": "research",
            "tags": r.tags,
            "difficulty": r.difficulty,
            "concepts": r.concepts,
            "sources": [s.model_dump() for s in r.sources],
            "findings": [f.model_dump() for f in r.findings],
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "language": "en",
            "category": "daily",
            "enriched": False,
        }
        registry_items.append(entry)
        new_count += 1
        logger.info(f"  Created: {entry['slug']}")
    save_registry(registry_items)
    logger.info(f"Added {new_count} research items")
    return new_count


def run_learn_modules(max_items: int, dry_run: bool) -> int:
    agent = LearnModuleGenerator()
    registry_items = load_registry()
    existing_slugs = {i["slug"] for i in registry_items}
    ontology_data = load_ontology()
    if not ontology_data:
        logger.error("Ontology required for learn module generation")
        return 0
    concepts = ontology_data.get("concepts", [])
    topics = []
    for c in concepts:
        slug = c.get("id", "")
        pillar = c.get("pillar", "aml")
        label = c.get("label", slug)
        candidate = f"{pillar}/learn/{slug}"
        if candidate not in existing_slugs:
            topics.append({"slug": slug, "pillar": pillar, "title": f"Learn: {label}"})
            existing_slugs.add(candidate)
        if len(topics) >= max_items:
            break
    if not topics:
        logger.info("No new learn modules to generate (all concepts covered)")
        return 0
    logger.info(f"Learn modules: {len(topics)} new topics from ontology")
    if dry_run:
        logger.info(f"  Would generate: {[t['slug'] for t in topics]}")
        return len(topics)
    results = agent.generate_batch(topics)
    for module, spec in zip(results, topics):
        entry = {
            "slug": f"{spec['pillar']}/learn/{spec['slug']}",
            "title": module.title,
            "description": module.description,
            "body_html": "".join(f"<h2>{s.heading}</h2>{s.content}" for s in module.sections),
            "pillar": spec["pillar"],
            "content_type": "learn",
            "tags": module.tags,
            "difficulty": module.difficulty,
            "prerequisites": module.prerequisites,
            "bloom_questions": [q.model_dump() for q in module.bloom_questions],
            "flashcards": [f.model_dump() for f in module.flashcards],
            "sections": [s.model_dump() for s in module.sections],
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "language": "en",
            "category": "daily",
            "enriched": False,
        }
        registry_items.append(entry)
        logger.info(f"  Generated: {entry['slug']}")
    save_registry(registry_items)
    logger.info(f"Generated {len(results)} learn modules")
    return len(results)


def run_glossary(dry_run: bool) -> int:
    agent = GlossaryAgent()
    ontology_data = load_ontology()
    if not ontology_data:
        logger.error("Ontology required for glossary generation")
        return 0
    concepts = ontology_data.get("concepts", [])
    logger.info(f"Glossary: {len(concepts)} ontology concepts")
    if dry_run:
        concepts_sample = [c.get("id", "") for c in concepts[:5]]
        logger.info(f"  Would generate entries for: {concepts_sample}...")
        return len(concepts)
    specs = [{"concept": c.get("id", ""), "pillar": c.get("pillar", "aml")} for c in concepts]
    results = agent.generate_batch(specs)
    entries = [r.model_dump() for r in results if r]
    out_path = REPOSITORY_ROOT / "data" / "glossary_entries.json"
    out_path.write_text(json.dumps(entries, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info(f"Generated {len(entries)} glossary entries -> {out_path}")
    return len(entries)


def run_synthesis(topic: str, pillar: str, max_sources: int, dry_run: bool) -> int:
    agent = SynthesisAgent()
    registry_items = load_registry()
    candidates = [i for i in registry_items if i.get("pillar") == pillar and len(i.get("body_html", "")) > 200]
    import random
    random.shuffle(candidates)
    sources = [
        {"url": i.get("source_url", ""), "title": i.get("title", ""), "content": i.get("body_html", "")[:3000]}
        for i in candidates[:max_sources]
    ]
    logger.info(f"Synthesis: topic='{topic}', pillar={pillar}, {len(sources)} sources")
    if dry_run:
        logger.info(f"  Would synthesize {topic} from {len(sources)} sources")
        return 1
    result = agent.synthesize(topic=topic, pillar=pillar, sources=sources, max_sources=max_sources)
    if not result:
        logger.warning("Synthesis returned no result")
        return 0
    out_path = REPOSITORY_ROOT / "data" / "synthesis_results.json"
    existing = []
    if out_path.exists():
        existing = json.loads(out_path.read_text(encoding="utf-8"))
    existing.append(result.model_dump())
    out_path.write_text(json.dumps(existing, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info(f"Synthesis result saved -> {out_path}")
    return 1


# ── CLI ──


def main():
    parser = argparse.ArgumentParser(description="Agentic content pipeline orchestrator")
    parser.add_argument("--phase", choices=["enrich", "research", "learn", "glossary", "synthesis", "all"], default="all")
    parser.add_argument("--pillar", default="aml", help="Target pillar (aml, stock, data-engineering)")
    parser.add_argument("--topic", default="", help="Topic for research or synthesis")
    parser.add_argument("--max-items", type=int, default=10, help="Max items to process per phase")
    parser.add_argument("--max-sources", type=int, default=5, help="Max sources for synthesis")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be done without executing")
    parser.add_argument("--save", action="store_true", default=True, help="Save results to registry")
    args = parser.parse_args()

    start = time.time()
    rprint(f"[bold blue]Agentic Pipeline[/bold blue]: phase=[cyan]{args.phase}[/cyan], dry_run=[yellow]{args.dry_run}[/yellow]")

    items = load_registry() if args.phase in ("enrich", "all", "research", "synthesis") else []
    total = 0
    results_log: list[tuple[str, int, float]] = []

    def run(name: str, func):
        nonlocal total
        t0 = time.time()
        count = func()
        elapsed = time.time() - t0
        if count:
            rprint(f"  [green]✔[/green] [bold]{name}[/bold]: {count} items in {elapsed:.1f}s")
        else:
            rprint(f"  [yellow]–[/yellow] {name}: 0 items")
        results_log.append((name, count, elapsed))
        total += count

    if args.phase in ("enrich", "all"):
        run("enrich", lambda: run_enrichment(items, args.max_items, args.dry_run))

    if args.phase in ("research", "all"):
        topic = args.topic or "emerging technologies"
        run("research", lambda: run_research(args.pillar, topic, args.max_items, args.dry_run))

    if args.phase in ("learn", "all"):
        run("learn", lambda: run_learn_modules(args.max_items, args.dry_run))

    if args.phase in ("glossary", "all"):
        run("glossary", lambda: run_glossary(args.dry_run))

    if args.phase in ("synthesis", "all"):
        topic = args.topic or "cross-pillar synthesis"
        run("synthesis", lambda: run_synthesis(topic, args.pillar, args.max_sources, args.dry_run))

    elapsed = time.time() - start
    table = Table(title=f"Pipeline Summary ({elapsed:.1f}s)")
    table.add_column("Phase", style="cyan")
    table.add_column("Items", justify="right")
    table.add_column("Time", justify="right")
    for name, count, dur in results_log:
        table.add_row(name, str(count), f"{dur:.1f}s")
    table.add_row("[bold]Total[/bold]", str(total), f"{elapsed:.1f}s")
    console.print(table)


if __name__ == "__main__":
    main()
