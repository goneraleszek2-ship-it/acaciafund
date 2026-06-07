#!/usr/bin/env python3.13
"""
Migrate registry.json to 3-category taxonomy: research | learn | knowledge.
Adds static pages and learning entries to the registry.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

REGISTRY_PATH = Path("registry.json")

KNOWLEDGE_ENTRIES = [
    {
        "slug": "about",
        "title": "About AcaciaFund",
        "description": "Mission, vision, and background of the AcaciaFund research synthesis platform.",
        "category": "page",
        "content_type": "knowledge",
        "tags": ["about", "info"],
    },
    {
        "slug": "research",
        "title": "Research Overview",
        "description": "Overview of AcaciaFund's research methodology, sources, and synthesis pipeline.",
        "category": "page",
        "content_type": "knowledge",
        "tags": ["research", "methodology"],
    },
    {
        "slug": "scholarship",
        "title": "Scholarship & Grants",
        "description": "Information about AcaciaFund's scholarship program and research grants.",
        "category": "page",
        "content_type": "knowledge",
        "tags": ["scholarship", "grants"],
    },
    {
        "slug": "contact",
        "title": "Contact Us",
        "description": "Get in touch with the AcaciaFund team.",
        "category": "page",
        "content_type": "knowledge",
        "tags": ["contact"],
    },
    {
        "slug": "knowledge/glossary",
        "title": "Glossary — Research & Financial Crime Terminology",
        "description": "Definitions of key terms used across AcaciaFund research, including AML, markets, and science concepts.",
        "category": "page",
        "content_type": "knowledge",
        "tags": ["glossary", "reference"],
    },
    {
        "slug": "knowledge/faq",
        "title": "Frequently Asked Questions",
        "description": "Common questions about AcaciaFund's methodology, content, and platform.",
        "category": "page",
        "content_type": "knowledge",
        "tags": ["faq", "help"],
    },
]

LEARN_ENTRIES = [
    {
        "slug": "learn",
        "title": "Learning Hub",
        "description": "Interactive lessons, quizzes, and tutorials on AML, financial markets, and science.",
        "category": "learn",
        "content_type": "learn",
        "tags": ["learning", "hub"],
    },
    {
        "slug": "learn/aml-basics",
        "title": "AML Fundamentals — A Beginner's Guide",
        "description": "Interactive lesson covering the basics of Anti-Money Laundering: regulations, red flags, and real-world cases.",
        "category": "learn",
        "content_type": "learn",
        "tags": ["aml", "basics", "lesson"],
    },
    {
        "slug": "learn/market-analysis",
        "title": "How to Analyse Market Signals — Interactive Tutorial",
        "description": "Step-by-step tutorial on reading market signals, understanding supply chain dynamics, and evaluating industry trends.",
        "category": "learn",
        "content_type": "learn",
        "tags": ["markets", "analysis", "tutorial"],
    },
    {
        "slug": "learn/science-method",
        "title": "Scientific Reasoning in Research Synthesis",
        "description": "Lesson on evaluating scientific claims, understanding replication crises, and applying Bloom taxonomy to research analysis.",
        "category": "learn",
        "content_type": "learn",
        "tags": ["science", "methodology", "reasoning"],
    },
    {
        "slug": "learn/quiz-aml",
        "title": "AML Knowledge Check — Interactive Quiz",
        "description": "Test your understanding of AML concepts with 10 interactive quiz questions covering regulations, enforcement, and emerging risks.",
        "category": "learn",
        "content_type": "learn",
        "tags": ["aml", "quiz", "assessment"],
    },
]


def make_body_html(content_type: str, slug: str, title: str, description: str) -> str:
    if content_type == "knowledge":
        return (
            f"<h2>{title}</h2>\n"
            f"<p>{description}</p>\n"
            f"<p>This page is part of the AcaciaFund Knowledge Base —"
            f" reference documentation for the platform's research, methodology, and background.</p>\n"
            f"<p><em>Last updated: 2026-06-07</em></p>\n"
        )
    elif content_type == "learn":
        return (
            f"<h2>{title}</h2>\n"
            f"<p>{description}</p>\n"
            f"<div class=\"flashcard-grid\">\n"
            f"<div class=\"flashcard-card\"><div class=\"font-semibold\">Key Concept 1</div>"
            f"<div class=\"mt-1 text-xs\">Introduction to this topic</div></div>\n"
            f"<div class=\"flashcard-card\"><div class=\"font-semibold\">Key Concept 2</div>"
            f"<div class=\"mt-1 text-xs\">Building on foundational knowledge</div></div>\n"
            f"<div class=\"flashcard-card\"><div class=\"font-semibold\">Key Concept 3</div>"
            f"<div class=\"mt-1 text-xs\">Advanced applications</div></div>\n"
            f"</div>\n"
        )
    return f"<p>{description}</p>"


def main():
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        registry = json.load(f)

    # Track existing slugs
    existing_slugs = {c["slug"] for c in registry["content"]}

    # Set content_type on all existing blog posts → research
    for c in registry["content"]:
        if c["category"] in ("blog",) and c.get("pillar"):
            c["content_type"] = "research"
        elif c["category"] in ("learn", "lesson"):
            c["content_type"] = "learn"
        else:
            c["content_type"] = c.get("content_type", "knowledge")

    # Add knowledge entries
    for entry in KNOWLEDGE_ENTRIES:
        if entry["slug"] in existing_slugs:
            continue
        now = datetime.now(timezone.utc)
        registry["content"].append({
            "slug": entry["slug"],
            "language": "en",
            "title": entry["title"],
            "description": entry["description"],
            "body_html": make_body_html("knowledge", entry["slug"], entry["title"], entry["description"]),
            "category": entry["category"],
            "content_type": "knowledge",
            "tags": entry["tags"],
            "created_at": now.isoformat(),
            "updated_at": None,
            "pillar": "",
            "date_str": "",
            "thumbnail_svg": "",
            "og_svg": "",
            "featured_image": "",
            "trending_html": "",
            "analysis_html": "",
            "cross_pillar_html": "",
            "bloom_questions": [],
            "flashcards": [],
            "signals": {},
            "source_breakdown": {},
            "quality_metrics": {},
            "lineage": {},
            "quality_flags": [],
        })
        existing_slugs.add(entry["slug"])

    # Add learn entries
    for entry in LEARN_ENTRIES:
        if entry["slug"] in existing_slugs:
            continue
        now = datetime.now(timezone.utc)
        registry["content"].append({
            "slug": entry["slug"],
            "language": "en",
            "title": entry["title"],
            "description": entry["description"],
            "body_html": make_body_html("learn", entry["slug"], entry["title"], entry["description"]),
            "category": entry["category"],
            "content_type": "learn",
            "tags": entry["tags"],
            "created_at": now.isoformat(),
            "updated_at": None,
            "pillar": "",
            "date_str": "",
            "thumbnail_svg": "",
            "og_svg": "",
            "featured_image": "",
            "trending_html": "",
            "analysis_html": "",
            "cross_pillar_html": "",
            "bloom_questions": [],
            "flashcards": [
                {"term": "Active Learning", "definition": "Learning by doing — engaging with material through quizzes, exercises, and problems."},
                {"term": "Spaced Repetition", "definition": "Reviewing material at increasing intervals to optimize long-term retention."},
            ],
            "signals": {},
            "source_breakdown": {},
            "quality_metrics": {},
            "lineage": {},
            "quality_flags": [],
        })
        existing_slugs.add(entry["slug"])

    # Sort: research first (newest), then knowledge, then learn
    def sort_key(c):
        order = {"research": 0, "knowledge": 1, "learn": 2}
        ct = c.get("content_type", "knowledge")
        date = c.get("date_str", "") or "2000-01-01"
        return (order.get(ct, 9), date)

    registry["content"].sort(key=sort_key, reverse=True)
    # Actually research newest first, others in their groups
    research = [c for c in registry["content"] if c.get("content_type") == "research"]
    knowledge = [c for c in registry["content"] if c.get("content_type") == "knowledge"]
    learn = [c for c in registry["content"] if c.get("content_type") == "learn"]
    research.sort(key=lambda c: c.get("date_str", ""), reverse=True)
    registry["content"] = research + knowledge + learn
    registry["last_run"] = datetime.now(timezone.utc).isoformat()

    with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)

    stats = {"research": len(research), "knowledge": len(knowledge), "learn": len(learn)}
    print(f"Migration complete. Content split:")
    for ct, count in stats.items():
        print(f"  {ct}: {count}")


if __name__ == "__main__":
    main()
