#!/usr/bin/env python3.13
"""
Enhance learn entries: assign pillars, add difficulty metadata, generate thumbnail SVGs.
"""
import hashlib
import json
from pathlib import Path

REGISTRY_PATH = Path("registry.json")

PILLAR_MAP = {
    "learn/data-engineering-basics": "data-engineering",
    "learn/data-pipeline-architectures": "data-engineering",
    "learn/building-pipelines-dbt-dagster": "data-engineering",
    "learn/aml-basics": "aml",
    "learn/market-analysis": "stock",
    "learn/quiz-aml": "aml",
    "learn/dataops-introduction": "data-engineering",
    "learn/data-quality-engineering": "data-engineering",
    "learn/open-source-data-stack": "data-engineering",
    "learn/data-ethics-privacy": "data-engineering",
    "learn/crypto-aml": "aml",
    "learn/trade-based-ml-sanctions": "aml",
    "learn/science-method": "stock",
    "learn/semiconductor-supply-chain": "stock",
    "learn/crispr-gene-editing": "stock",
    "learn/behavioral-design-learning": "stock",
    "learn/behavioral-finance-portfolio": "stock",
    "learn/meta-analysis-statistics": "stock",
}

DIFFICULTY_MAP = {
    "learn/data-engineering-basics": "beginner",
    "learn/data-pipeline-architectures": "beginner",
    "learn/building-pipelines-dbt-dagster": "intermediate",
    "learn/aml-basics": "beginner",
    "learn/market-analysis": "intermediate",
    "learn/quiz-aml": "beginner",
    "learn/dataops-introduction": "beginner",
    "learn/data-quality-engineering": "intermediate",
    "learn/open-source-data-stack": "intermediate",
    "learn/crypto-aml": "intermediate",
    "learn/trade-based-ml-sanctions": "advanced",
    "learn/science-method": "beginner",
    "learn/semiconductor-supply-chain": "advanced",
    "learn/crispr-gene-editing": "advanced",
    "learn/behavioral-design-learning": "intermediate",
    "learn/behavioral-finance-portfolio": "advanced",
    "learn/meta-analysis-statistics": "intermediate",
    "learn/data-ethics-privacy": "intermediate",
}

CURATED_RELATIONS = {
    "learn/data-engineering-basics": [
        {"slug": "learn/data-pipeline-architectures", "type": "next", "label": "Next: pipeline architectures"},
        {"slug": "learn/dataops-introduction", "type": "next", "label": "Next: DataOps introduction"},
    ],
    "learn/data-pipeline-architectures": [
        {"slug": "learn/building-pipelines-dbt-dagster", "type": "next", "label": "Next: building with dbt and Dagster"},
        {"slug": "learn/dataops-introduction", "type": "next", "label": "Next: DataOps introduction"},
    ],
    "learn/building-pipelines-dbt-dagster": [
        {"slug": "learn/data-quality-engineering", "type": "next", "label": "Next: data quality"},
        {"slug": "learn/dataops-introduction", "type": "reinforcement", "label": "See also: DataOps principles"},
    ],
    "learn/aml-basics": [
        {"slug": "learn/quiz-aml", "type": "reinforcement", "label": "Test your AML knowledge"},
    ],
    "learn/market-analysis": [
        {"slug": "learn/quiz-aml", "type": "related", "label": "Risk assessment concepts"},
    ],
    "learn/dataops-introduction": [
        {"slug": "learn/data-engineering-basics", "type": "reinforcement", "label": "Review: data engineering basics"},
        {"slug": "learn/data-quality-engineering", "type": "next", "label": "Next: data quality"},
        {"slug": "learn/open-source-data-stack", "type": "related", "label": "Open-source tools"},
    ],
    "learn/data-quality-engineering": [
        {"slug": "learn/open-source-data-stack", "type": "next", "label": "Next: open-source stack"},
    ],
    "learn/quiz-aml": [
        {"slug": "learn/crypto-aml", "type": "next", "label": "Next: crypto AML"},
    ],
    "learn/crypto-aml": [
        {"slug": "learn/trade-based-ml-sanctions", "type": "next", "label": "Next: trade-based ML"},
    ],
    "learn/science-method": [
        {"slug": "learn/market-analysis", "type": "next", "label": "Next: market analysis"},
    ],
    "learn/behavioral-design-learning": [
        {"slug": "learn/behavioral-finance-portfolio", "type": "next", "label": "Next: behavioral portfolio"},
    ],
    "learn/meta-analysis-statistics": [
        {"slug": "learn/behavioral-finance-portfolio", "type": "reinforcement", "label": "See also: portfolio construction"},
    ],
    "learn/market-analysis": [
        {"slug": "learn/semiconductor-supply-chain", "type": "next", "label": "Next: supply chain analysis"},
        {"slug": "learn/behavioral-design-learning", "type": "related", "label": "Behavioral factors"},
    ],
    "learn/semiconductor-supply-chain": [
        {"slug": "learn/crispr-gene-editing", "type": "next", "label": "Next: gene editing investing"},
    ],
    "learn/crispr-gene-editing": [
        {"slug": "learn/behavioral-finance-portfolio", "type": "related", "label": "See also: portfolio strategy"},
    ],
    "learn/open-source-data-stack": [
        {"slug": "learn/data-ethics-privacy", "type": "next", "label": "Next: data ethics & privacy"},
    ],
}

PREREQUISITES = {
    "learn/data-engineering-basics": [],
    "learn/data-pipeline-architectures": ["learn/data-engineering-basics"],
    "learn/building-pipelines-dbt-dagster": ["learn/data-pipeline-architectures"],
    "learn/dataops-introduction": ["learn/building-pipelines-dbt-dagster"],
    "learn/data-quality-engineering": ["learn/dataops-introduction"],
    "learn/open-source-data-stack": ["learn/data-quality-engineering"],
    "learn/data-ethics-privacy": ["learn/open-source-data-stack"],
    "learn/crypto-aml": ["learn/quiz-aml"],
    "learn/trade-based-ml-sanctions": ["learn/crypto-aml"],
    "learn/market-analysis": ["learn/science-method"],
    "learn/semiconductor-supply-chain": ["learn/market-analysis"],
    "learn/crispr-gene-editing": ["learn/semiconductor-supply-chain"],
    "learn/behavioral-design-learning": ["learn/market-analysis"],
    "learn/behavioral-finance-portfolio": ["learn/behavioral-design-learning"],
    "learn/meta-analysis-statistics": ["learn/science-method"],
    "learn/quiz-aml": ["learn/aml-basics"],
}

PILLAR_COLORS = {
    "aml": {"primary": "#d97706", "secondary": "#f59e0b", "bg": "#1c1917"},
    "stock": {"primary": "#22c55e", "secondary": "#4ade80", "bg": "#052e16"},
    "data-engineering": {"primary": "#6366f1", "secondary": "#818cf8", "bg": "#1e1b4b"},
}

DIFFICULTY_EMOJI = {
    "beginner": "🌱",
    "intermediate": "📘",
    "advanced": "🔥",
}


def generate_learn_thumbnail(title: str, pillar: str) -> str:
    """Generate a simple geometric thumbnail with pillar color and a unique pattern."""
    c = PILLAR_COLORS.get(pillar, PILLAR_COLORS["stock"])
    seed = int(hashlib.md5(title.encode()).hexdigest()[:8], 16)
    import random
    rng = random.Random(seed)

    elements = []
    for _ in range(6):
        cx = rng.randint(40, 560)
        cy = rng.randint(30, 310)
        r_val = rng.randint(10, 50)
        op = round(rng.uniform(0.05, 0.2), 2)
        elements.append(
            f'<circle cx="{cx}" cy="{cy}" r="{r_val}" fill="{c["primary"]}" opacity="{op}"/>'
        )
    for _ in range(4):
        x1 = rng.randint(20, 300)
        y1 = rng.randint(20, 320)
        x2 = rng.randint(300, 580)
        y2 = rng.randint(20, 320)
        elements.append(
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{c["secondary"]}" '
            f'stroke-width="{rng.randint(1, 3)}" opacity="{round(rng.uniform(0.1, 0.3), 2)}"/>'
        )
    for _ in range(20):
        dx = rng.randint(10, 590)
        dy = rng.randint(10, 330)
        dr = rng.randint(2, 6)
        elements.append(
            f'<circle cx="{dx}" cy="{dy}" r="{dr}" fill="{c["primary"]}" '
            f'opacity="{round(rng.uniform(0.1, 0.4), 2)}"/>'
        )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="600" height="340" viewBox="0 0 600 340">
<defs>
<linearGradient id="lg-{pillar}" x1="0" y1="0" x2="1" y2="1">
<stop offset="0" stop-color="{c["bg"]}"/>
<stop offset="1" stop-color="#0a0a1a"/>
</linearGradient>
</defs>
<rect width="600" height="340" fill="url(#lg-{pillar})"/>
{"".join(elements)}
<circle cx="300" cy="170" r="140" fill="{c["primary"]}" opacity="0.04"/>
<circle cx="300" cy="170" r="80" fill="{c["secondary"]}" opacity="0.04"/>
</svg>"""


def main():
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        registry = json.load(f)

    learn_items = [c for c in registry["content"] if c.get("content_type") == "learn"]

    for item in learn_items:
        slug = item["slug"]
        if slug in PILLAR_MAP:
            pillar = PILLAR_MAP[slug]
            item["pillar"] = pillar
            item["thumbnail_svg"] = generate_learn_thumbnail(item["title"], pillar)
            item["tags"] = list(set(item.get("tags", []) + [pillar]))
        if slug in DIFFICULTY_MAP:
            item["difficulty"] = DIFFICULTY_MAP[slug]
        if slug in CURATED_RELATIONS:
            item["curated_relations"] = CURATED_RELATIONS[slug]
        if slug in PREREQUISITES:
            item["prerequisites"] = PREREQUISITES[slug]

    with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)

    print("Learn entries updated:")
    for item in learn_items:
        p = item.get("pillar", "")
        d = item.get("difficulty", "")
        cr = "yes" if item.get("curated_relations") else "no"
        pr = "yes" if item.get("prerequisites") else "no"
        print(f"  {item['slug']}: pillar={p}, difficulty={d}, thumbnail={'yes' if item.get('thumbnail_svg') else 'no'}, curated_relations={cr}, prerequisites={pr}")


if __name__ == "__main__":
    main()
