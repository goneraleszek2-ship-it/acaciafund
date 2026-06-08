#!/usr/bin/env python3.13
"""
Enhance learn entries: assign pillars, add difficulty metadata, generate thumbnail SVGs.
"""
import hashlib
import json
from pathlib import Path

REGISTRY_PATH = Path("registry.json")

PILLAR_MAP = {
    "learn/aml-basics": "aml",
    "learn/market-analysis": "stock",
    "learn/quiz-aml": "aml",
    "learn/dataops-introduction": "data-engineering",
    "learn/data-quality-engineering": "data-engineering",
    "learn/open-source-data-stack": "data-engineering",
    "learn/data-ethics-privacy": "data-engineering",
}

DIFFICULTY_MAP = {
    "learn/aml-basics": "beginner",
    "learn/market-analysis": "intermediate",
    "learn/quiz-aml": "beginner",
    "learn/dataops-introduction": "beginner",
    "learn/data-quality-engineering": "intermediate",
    "learn/open-source-data-stack": "intermediate",
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
    # Random circles
    for _ in range(6):
        cx = rng.randint(40, 560)
        cy = rng.randint(30, 310)
        r_val = rng.randint(10, 50)
        op = round(rng.uniform(0.05, 0.2), 2)
        elements.append(
            f'<circle cx="{cx}" cy="{cy}" r="{r_val}" fill="{c["primary"]}" opacity="{op}"/>'
        )
    # Random lines
    for _ in range(4):
        x1 = rng.randint(20, 300)
        y1 = rng.randint(20, 320)
        x2 = rng.randint(300, 580)
        y2 = rng.randint(20, 320)
        elements.append(
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{c["secondary"]}" '
            f'stroke-width="{rng.randint(1, 3)}" opacity="{round(rng.uniform(0.1, 0.3), 2)}"/>'
        )
    # Small dots
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

    with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)

    print("Learn entries updated:")
    for item in learn_items:
        p = item.get("pillar", "")
        d = item.get("difficulty", "")
        print(f"  {item['slug']}: pillar={p}, difficulty={d}, thumbnail={'yes' if item.get('thumbnail_svg') else 'no'}")


if __name__ == "__main__":
    main()
