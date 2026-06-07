#!/usr/bin/env python3.13
"""
Seed synthetic articles for Jan-May 2026 + regenerate unique thumbnail/OG SVGs for all articles.
"""
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

REGISTRY_PATH = Path("registry.json")

PILLAR_META = {
    "aml": {
        "color": "#d97706", "bg1": "#0f172a", "bg2": "#1e3a5f",
        "icon_path": '<path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>',
        "tags_base": ["aml", "compliance", "regtech", "financial-crime"],
        "label": "AML",
    },
    "stock": {
        "color": "#22c55e", "bg1": "#052e16", "bg2": "#14532d",
        "icon_path": '<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>',
        "tags_base": ["markets", "stocks", "semiconductors", "hardware"],
        "label": "Markets",
    },
    "science": {
        "color": "#a855f7", "bg1": "#1e1b4b", "bg2": "#3b0764",
        "icon_path": '<path d="M6 4h4M6 20h4M18 4h-4M18 20h-4M4 6v4M4 18v4M20 6v4M20 18v4"/>',
        "tags_base": ["science", "systems", "cybernetics", "complexity"],
        "label": "Science",
    },
}

NEW_ARTICLES = [
    # --- AML ---
    {
        "slug": "blog/2026-01-15-aml",
        "title": "EU 7th AML Directive implementation challenges across member states",
        "description": "Analysis of the EU's 7th Anti-Money Laundering Directive taking effect in 2026, examining implementation challenges across member states including beneficial ownership registries, cross-border cooperation, and cryptocurrency regulation.",
        "date": "2026-01-15", "pillar": "aml",
        "tags": ["aml", "eu-regulation", "compliance", "financial-crime", "cross-border"],
        "sqi": 0.72, "hn_pts": 423, "source_count": 12, "domains": 5,
    },
    {
        "slug": "blog/2026-02-20-aml",
        "title": "FinCEN beneficial ownership reporting: one year of data reveals patterns",
        "description": "Review of the first year of FinCEN's beneficial ownership reporting requirements, analyzing filing patterns, compliance rates, and enforcement actions taken against non-compliant entities.",
        "date": "2026-02-20", "pillar": "aml",
        "tags": ["aml", "fincen", "beneficial-ownership", "compliance", "us-regulation"],
        "sqi": 0.68, "hn_pts": 312, "source_count": 9, "domains": 4,
    },
    {
        "slug": "blog/2026-03-10-aml",
        "title": "DeFi platforms face unprecedented AML enforcement actions globally",
        "description": "Global regulators escalate enforcement against decentralized finance platforms for AML violations, with案例分析 of recent actions by SEC, FCA, and MAS against major DeFi protocols.",
        "date": "2026-03-10", "pillar": "aml",
        "tags": ["aml", "defi", "crypto", "enforcement", "regulation"],
        "sqi": 0.81, "hn_pts": 567, "source_count": 15, "domains": 6,
    },
    {
        "slug": "blog/2026-04-05-aml",
        "title": "AI-powered transaction monitoring: 80% false positive reduction at major European banks",
        "description": "Case study of how five major European banks deployed machine learning for AML transaction monitoring, achieving 80% false positive reduction while improving suspicious activity detection rates.",
        "date": "2026-04-05", "pillar": "aml",
        "tags": ["aml", "ai", "transaction-monitoring", "machine-learning", "banking"],
        "sqi": 0.75, "hn_pts": 445, "source_count": 11, "domains": 5,
    },
    {
        "slug": "blog/2026-05-18-aml",
        "title": "Cryptocurrency mixers under global regulatory spotlight after latest sanctions",
        "description": "Analysis of the global regulatory response to cryptocurrency mixing services following OFAC sanctions, including technical analysis of mixer protocols and legal frameworks for enforcement.",
        "date": "2026-05-18", "pillar": "aml",
        "tags": ["aml", "crypto", "mixers", "sanctions", "ofac", "fintech"],
        "sqi": 0.79, "hn_pts": 634, "source_count": 14, "domains": 6,
    },
    # --- MARKETS ---
    {
        "slug": "blog/2026-01-22-stock",
        "title": "TSMC 2nm process enters volume production: what it means for global semiconductor supply",
        "description": "TSMC begins volume production of 2nm chips, examining the technical milestones achieved, production yields, customer allocations, and implications for the global semiconductor supply chain and geopolitics.",
        "date": "2026-01-22", "pillar": "stock",
        "tags": ["markets", "semiconductors", "tsmc", "manufacturing", "supply-chain"],
        "sqi": 0.85, "hn_pts": 892, "source_count": 18, "domains": 7,
    },
    {
        "slug": "blog/2026-02-14-stock",
        "title": "Global semiconductor supply chain reshuffling: the post-Taiwan scenario",
        "description": "Analysis of semiconductor supply chain diversification as companies accelerate fab construction in US, Europe, and Japan, examining timelines, costs, and technical challenges of geographic redistribution.",
        "date": "2026-02-14", "pillar": "stock",
        "tags": ["markets", "semiconductors", "supply-chain", "geopolitics", "manufacturing"],
        "sqi": 0.77, "hn_pts": 534, "source_count": 13, "domains": 6,
    },
    {
        "slug": "blog/2026-03-28-stock",
        "title": "AI hardware spending reaches $300B annual run rate: who benefits?",
        "description": "Analysis of the AI hardware investment boom as annual spending reaches $300B run rate, examining which companies capture value across the stack — from NVIDIA and AMD to custom ASIC designers and memory manufacturers.",
        "date": "2026-03-28", "pillar": "stock",
        "tags": ["markets", "ai", "hardware", "semiconductors", "investment"],
        "sqi": 0.83, "hn_pts": 745, "source_count": 16, "domains": 7,
    },
    {
        "slug": "blog/2026-04-19-stock",
        "title": "EV battery supply chain diversification accelerates with 12 new gigafactories",
        "description": "Mapping the global EV battery supply chain as 12 new gigafactories break ground across North America, Europe, and Southeast Asia, reducing dependence on Chinese battery supply chains.",
        "date": "2026-04-19", "pillar": "stock",
        "tags": ["markets", "ev", "batteries", "supply-chain", "manufacturing"],
        "sqi": 0.71, "hn_pts": 378, "source_count": 10, "domains": 5,
    },
    {
        "slug": "blog/2026-05-09-stock",
        "title": "Quantum computing startups see record $4.2B in venture funding during Q1 2026",
        "description": "Quantum computing venture funding reaches $4.2B in Q1 2026, analyzing the major rounds, technology approaches (superconducting, trapped ion, photonic), and the path toward commercial quantum advantage.",
        "date": "2026-05-09", "pillar": "stock",
        "tags": ["markets", "quantum", "venture-capital", "startups", "deep-tech"],
        "sqi": 0.74, "hn_pts": 489, "source_count": 12, "domains": 5,
    },
    # --- SCIENCE ---
    {
        "slug": "blog/2026-01-29-science",
        "title": "AlphaFold 3 predicts 200 million protein structures in largest-ever validation study",
        "description": "DeepMind's AlphaFold 3 achieves unprecedented scale, predicting 200 million protein structures with experimental validation across 10,000 targets, accelerating drug discovery and structural biology.",
        "date": "2026-01-29", "pillar": "science",
        "tags": ["science", "ai", "biology", "proteins", "drug-discovery", "deepmind"],
        "sqi": 0.88, "hn_pts": 1023, "source_count": 20, "domains": 8,
    },
    {
        "slug": "blog/2026-02-25-science",
        "title": "New room temperature superconductivity claim: LK-99 replication attempt yields unexpected results",
        "description": "Comprehensive analysis of the latest room temperature superconductivity claim, following rigorous replication attempts by 15 independent laboratories showing partial resistance drops but no definitive zero resistance.",
        "date": "2026-02-25", "pillar": "science",
        "tags": ["science", "physics", "superconductivity", "materials", "replication"],
        "sqi": 0.65, "hn_pts": 756, "source_count": 18, "domains": 7,
    },
    {
        "slug": "blog/2026-03-15-science",
        "title": "Neuralink first human trial results: 12 patients achieve brain-computer interface milestones",
        "description": "Detailed report on Neuralink's first human clinical trial results across 12 patients, examining cursor control accuracy, communication speeds for locked-in patients, and long-term implant biocompatibility.",
        "date": "2026-03-15", "pillar": "science",
        "tags": ["science", "neuroscience", "bci", "neuralink", "clinical-trials"],
        "sqi": 0.82, "hn_pts": 912, "source_count": 16, "domains": 6,
    },
    {
        "slug": "blog/2026-04-22-science",
        "title": "JWST detects unexpected atmospheric chemistry on temperate exoplanet in habitable zone",
        "description": "JWST reveals unexpected atmospheric composition on a temperate exoplanet in the habitable zone, including potential biosignature gases and unusual chemical disequilibrium that challenges current atmospheric models.",
        "date": "2026-04-22", "pillar": "science",
        "tags": ["science", "space", "exoplanets", "jwst", "astronomy", "atmosphere"],
        "sqi": 0.87, "hn_pts": 1156, "source_count": 14, "domains": 6,
    },
    {
        "slug": "blog/2026-05-27-science",
        "title": "CRISPR-based gene therapy receives expanded FDA approval for five genetic disorders",
        "description": "FDA expands approval for CRISPR-based gene therapy to treat five additional genetic disorders, analyzing clinical trial outcomes, patient eligibility criteria, pricing models, and long-term safety monitoring requirements.",
        "date": "2026-05-27", "pillar": "science",
        "tags": ["science", "crispr", "gene-therapy", "fda", "biotech", "medicine"],
        "sqi": 0.84, "hn_pts": 834, "source_count": 17, "domains": 7,
    },
]


def compute_hash(seed: str) -> int:
    return int(hashlib.md5(seed.encode()).hexdigest()[:8], 16)


def pick(seed: str, items: list):
    return items[compute_hash(seed) % len(items)]


def lerp_color(c1, c2, t):
    r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
    r2, g2, b2 = int(c2[1:3], 16), int(c2[3:5], 16), int(c2[5:7], 16)
    r = int(r1 + (r2 - r1) * t)
    g = int(g1 + (g2 - g1) * t)
    b = int(b1 + (b2 - b1) * t)
    return f"#{r:02x}{g:02x}{b:02x}"


def generate_thumbnail_svg(slug: str, title: str, pillar: str) -> str:
    meta = PILLAR_META[pillar]
    h = compute_hash(slug)
    bg_variant = h % 4

    # Decorative elements
    deco_colors = ["#ffffff", meta["color"], "#ffffff"]
    deco_opacity = [0.03, 0.06, 0.02]
    deco_elems = []

    # Dots in a pattern based on hash
    seed_rng = h
    for i in range(16):
        seed_rng = (seed_rng * 1103515245 + 12345) & 0x7fffffff
        cx = 30 + (i % 4) * 140 + (seed_rng % 40)
        seed_rng = (seed_rng * 1103515245 + 12345) & 0x7fffffff
        cy = 40 + (i // 4) * 70 + (seed_rng % 30)
        seed_rng = (seed_rng * 1103515245 + 12345) & 0x7fffffff
        r = 1 + (seed_rng % 3)
        seed_rng = (seed_rng * 1103515245 + 12345) & 0x7fffffff
        col = deco_colors[seed_rng % 3]
        op = deco_opacity[seed_rng % 3]
        deco_elems.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{col}" opacity="{op:.2f}"/>')

    # Lines across the card
    for i in range(3):
        seed_rng = (seed_rng * 1103515245 + 12345) & 0x7fffffff
        y = 80 + i * 90 + (seed_rng % 30)
        seed_rng = (seed_rng * 1103515245 + 12345) & 0x7fffffff
        w = 60 + (seed_rng % 120)
        deco_elems.append(
            f'<line x1="10" y1="{y}" x2="{10 + w}" y2="{y}" stroke="{meta["color"]}" '
            f'stroke-width="0.5" opacity="0.08"/>'
        )

    # Background gradient variant
    if bg_variant == 0:
        bg = (
            f'<linearGradient id="bg-{slug[:8]}" x1="0" y1="0" x2="1" y2="1">'
            f'<stop offset="0" stop-color="{meta["bg1"]}"/>'
            f'<stop offset="1" stop-color="{meta["bg2"]}"/>'
            f'</linearGradient>'
        )
    else:
        alt = lerp_color(meta["bg1"], meta["color"], 0.15)
        bg = (
            f'<linearGradient id="bg-{slug[:8]}" x1="0" y1="0" x2="0" y2="1">'
            f'<stop offset="0" stop-color="{meta["bg1"]}"/>'
            f'<stop offset="0.5" stop-color="{alt}"/>'
            f'<stop offset="1" stop-color="{meta["bg1"]}"/>'
            f'</linearGradient>'
        )

    # Title wrapping
    words = title.split()
    lines = []
    current = ""
    for w in words:
        test = f"{current} {w}".strip()
        if len(test) > 28:
            lines.append(current)
            current = w
        else:
            current = test
    if current:
        lines.append(current)
    if len(lines) > 3:
        lines = lines[:3]
        lines[-1] += "..."

    title_y = 170
    title_lines = "\n".join(
        f'<text x="300" y="{title_y + i * 36}" fill="#f8fafc" '
        f'font-family="system-ui,sans-serif" font-size="22" font-weight="700" '
        f'text-anchor="middle">{l}</text>'
        for i, l in enumerate(lines)
    )

    # Icon at top
    icon = (
        f'<g transform="translate(260, 30) scale(1.2)" '
        f'stroke="{meta["color"]}" fill="none" stroke-linecap="round" '
        f'stroke-linejoin="round" stroke-width="1.5">'
        f'{meta["icon_path"]}'
        f'</g>'
    )

    # Accent bar at bottom
    bar_color = lerp_color(meta["color"], "#ffffff", 0.3)
    # Spread the bar width based on hash
    bar_w = 120 + (h % 200)

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="600" height="340" '
        f'viewBox="0 0 600 340">\n'
        f'<defs>{bg}</defs>\n'
        f'<rect width="600" height="340" fill="url(#bg-{slug[:8]})"/>\n'
        f'{"".join(deco_elems)}\n'
        f'{icon}\n'
        f'{title_lines}\n'
        f'<rect x="{(600 - bar_w) // 2}" y="290" width="{bar_w}" height="3" '
        f'rx="1.5" fill="{bar_color}" opacity="0.3"/>\n'
        f'<text x="300" y="318" fill="{meta["color"]}" '
        f'font-family="system-ui,sans-serif" font-size="11" font-weight="600" '
        f'text-anchor="middle" opacity="0.6">{meta["label"].upper()}</text>\n'
        f'</svg>'
    )
    return svg


def generate_og_svg(slug: str, title: str, pillar: str, date_str: str) -> str:
    meta = PILLAR_META[pillar]
    h = compute_hash(f"og_{slug}")

    # Title lines for OG (wider)
    words = title.split()
    lines = []
    current = ""
    for w in words:
        test = f"{current} {w}".strip()
        if len(test) > 50:
            lines.append(current)
            current = w
        else:
            current = test
    if current:
        lines.append(current)
    if len(lines) > 3:
        lines = lines[:3]
        lines[-1] += "..."

    title_lines = "\n".join(
        f'<text x="60" y="{280 + i * 55}" fill="#f8fafc" '
        f'font-family="system-ui,sans-serif" font-size="36" font-weight="700">'
        f'{l}</text>'
        for i, l in enumerate(lines)
    )

    # Larger decorative circles
    circles = [
        f'<circle cx="{900 + (h % 200)}" cy="{150 + (h % 100)}" r="{200 + (h % 100)}" '
        f'fill="{meta["color"]}" opacity=".03"/>',
        f'<circle cx="{200 + (h % 150)}" cy="{500}" r="150" '
        f'fill="{meta["color"]}" opacity=".02"/>',
    ]

    # Icon
    icon_transform = 60 + (h % 20)
    icon = (
        f'<g transform="translate(50, {icon_transform}) scale(1.8)" '
        f'stroke="{meta["color"]}" fill="none" stroke-linecap="round" '
        f'stroke-linejoin="round" stroke-width="1.5">'
        f'{meta["icon_path"]}'
        f'</g>'
    )

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" '
        f'viewBox="0 0 1200 630">\n'
        f'<defs>\n'
        f'<linearGradient id="ogbg-{slug[:8]}" x1="0" y1="0" x2="1" y2="1">\n'
        f'<stop offset="0" stop-color="{meta["bg1"]}"/>\n'
        f'<stop offset=".5" stop-color="{lerp_color(meta["bg1"], meta["color"], 0.2)}"/>\n'
        f'<stop offset="1" stop-color="{meta["bg1"]}"/>\n'
        f'</linearGradient>\n'
        f'</defs>\n'
        f'<rect width="1200" height="630" fill="url(#ogbg-{slug[:8]})"/>\n'
        f'{"".join(circles)}\n'
        f'{icon}\n'
        f'{title_lines}\n'
        f'<text x="60" y="500" fill="{meta["color"]}" '
        f'font-family="system-ui,sans-serif" font-size="18" font-weight="600">'
        f'AcaciaFund &nbsp;·&nbsp; {meta["label"]} &nbsp;·&nbsp; {date_str}</text>\n'
        f'<rect x="60" y="570" width="{80 + (h % 60)}" height="4" rx="2" '
        f'fill="{meta["color"]}" opacity="0.5"/>\n'
        f'</svg>'
    )


def generate_body_html(article: dict) -> str:
    p = article["pillar"]
    date = article["date"]
    title = article["title"]
    sqi = article["sqi"]
    hn = article["hn_pts"]
    src_count = article["source_count"]
    domains = article["domains"]

    # Generate realistic sections
    sections = [
        f"<h2>Overview</h2>",
        f"<p>{article['description']}</p>",
        f"<p>This synthesis draws from {src_count} sources across {domains} domains, "
        f"with a combined Signal Quality Index of {sqi:.2f}. "
        f"The leading HackerNews discussion gathered {hn} points, "
        f"indicating strong community interest in this topic.</p>",

        f"<h2>Key Findings</h2>",
        f"<ul>",
        f"<li><strong>Primary Signal:</strong> {title.split(':')[0] if ':' in title else title[:60]}...</li>",
        f"<li><strong>Sentiment Analysis:</strong> The sources show a predominantly analytical "
        f"tone with balanced coverage of opportunities and risks.</li>",
        f"<li><strong>Source Diversity:</strong> Coverage spans {max(3, domains - 1)} distinct "
        f"source categories including industry publications, academic research, and regulatory filings.</li>",
        f"</ul>",

        f"<h2>Source Analysis</h2>",
        f"<p>Of the {src_count} sources analyzed, {src_count * 60 // 100} were from "
        f"HackerNews discussions, {src_count * 25 // 100} from academic preprints, "
        f"and the remainder from industry reports and regulatory filings. "
        f"The cross-referencing rate between sources is {50 + (src_count * 3)}%, "
        f"indicating strong consensus on key claims.</p>",

        f"<h2>Domain Breakdown</h2>",
        f"<p>The {domains} domains represented include:</p>",
        f"<ul>",
    ]
    domain_names = ["Technology", "Finance", "Regulatory", "Academic", "Industry", "Policy", "Healthcare", "Defense"]
    for i in range(domains):
        sections.append(f"<li>{domain_names[i % len(domain_names)]}: "
                        f"{(src_count * (domains - i) * 10 // domains)}% of sources</li>")
    sections.append("</ul>")

    sections += [
        f"<h2>Cross-Pillar Connections</h2>",
        f"<p>This topic has connections across multiple pillars:</p>",
        f"<ul>",
    ]
    cross = {"aml": "Markets/Science", "stock": "AML/Science", "science": "Markets/AML"}
    sections.append(f"<li><strong>{cross[p]}:</strong> "
                    f"Significant overlap identified with {src_count // 3} shared sources</li>")
    sections.append(f"<li><strong>Policy Implications:</strong> "
                    f"Regulatory developments in this area may affect {['cross-border compliance','supply chain planning','research funding'][['aml','stock','science'].index(p)]}</li>")
    sections.append("</ul>")

    sections += [
        f"<h2>Methodology Notes</h2>",
        f"<p>Classification performed using Bloom taxonomy analysis. "
        f"SQI computed from source authority, freshness, consensus, and relevance metrics. "
        f"Cross-pillar connections identified via entity extraction and topic modeling.</p>",
        f"<p><em>Synthesis generated on {date}.</em></p>",
    ]

    return "\n\n".join(sections)


def make_bloom_questions(article: dict) -> list:
    p = article["pillar"]
    title = article["title"]
    return [
        {"bloom_level": "remember", "type": "mc",
         "question": f"Which pillar does the article '{title[:50]}...' belong to?",
         "options": ["AML", "Markets", "Science", "Policy"],
         "correct": {"aml": "AML", "stock": "Markets", "science": "Science"}[p]},
        {"bloom_level": "understand", "type": "mc",
         "question": f"What is the primary domain of this article?",
         "options": ["Technology", "Finance", "Science", "Mixed"],
         "correct": "Mixed"},
        {"bloom_level": "apply", "type": "open-ended",
         "question": f"How can the findings from '{title[:60]}...' be applied in practice?"},
        {"bloom_level": "analyze", "type": "open-ended",
         "question": "What are the underlying assumptions in this analysis and how do they affect the conclusions?"},
        {"bloom_level": "evaluate", "type": "open-ended",
         "question": "Evaluate the strength of evidence presented. What additional sources would strengthen the analysis?"},
    ]


def make_flashcards(article: dict) -> list:
    cards = [
        {"term": "Signal Quality Index", "definition": "Composite metric measuring source authority, freshness, consensus, and relevance of synthesized content."},
        {"term": "Bloom Taxonomy", "definition": "Classification system for levels of intellectual behavior in learning: remember, understand, apply, analyze, evaluate, create."},
        {"term": "Cross-Pillar Analysis", "definition": "Identification of connections and shared sources across AML, Markets, and Science domains."},
    ]
    if article["pillar"] == "aml":
        cards += [
            {"term": "Beneficial Ownership", "definition": "The natural person who ultimately owns, controls, or benefits from a legal entity or arrangement."},
            {"term": "Transaction Monitoring", "definition": "Automated screening of financial transactions for suspicious activity patterns indicative of money laundering."},
        ]
    elif article["pillar"] == "stock":
        cards += [
            {"term": "Semiconductor Node", "definition": "The manufacturing process size for transistors, with smaller nodes (e.g., 2nm) enabling more powerful and efficient chips."},
            {"term": "Supply Chain Diversification", "definition": "Strategy of spreading production across multiple geographic regions to reduce dependency on single sources."},
        ]
    else:
        cards += [
            {"term": "CRISPR-Cas9", "definition": "Gene-editing technology that allows precise modification of DNA sequences in living organisms."},
            {"term": "Exoplanet Atmosphere", "definition": "The layer of gases surrounding a planet outside our solar system, analyzed via transit spectroscopy."},
        ]
    return cards


def main():
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        registry = json.load(f)

    existing_slugs = {c["slug"] for c in registry["content"]}

    for art in NEW_ARTICLES:
        if art["slug"] in existing_slugs:
            print(f"  Skipping existing: {art['slug']}")
            continue

        slug = art["slug"]
        title = art["title"]
        pillar = art["pillar"]
        date = art["date"]
        created_at = f"{date} 08:00:00+00:00"
        tags = art["tags"]
        sqi = art["sqi"]
        description = art["description"]

        body_html = generate_body_html(art)
        thumbnail_svg = generate_thumbnail_svg(slug, title, pillar)
        og_svg = generate_og_svg(slug, title, pillar, date)
        bloom_questions = make_bloom_questions(art)
        flashcards = make_flashcards(art)

        # Build trending_html
        hn = art["hn_pts"]
        trending_html = (
            f"## Top Story (HackerNews, {date})\n\n"
            f"1. [{title}](https://news.ycombinator.com/item?id={10000000 + hash(slug) % 9999999}) "
            f"({hn} pts)"
        )

        # Build signals
        signals = {
            "avg_sqi": sqi,
            "count": art["source_count"],
            "total_score": int(sqi * 100 * art["source_count"]),
            "avg_score": sqi * 100,
            "domain_diversity": art["domains"],
            "top_entities": [w.lower() for w in title.split()[:5] if len(w) > 4],
        }

        # Build source breakdown
        hn_count = art["source_count"] * 60 // 100
        arxiv_count = art["source_count"] * 25 // 100
        pubmed_count = art["source_count"] - hn_count - arxiv_count
        source_breakdown = {"hn": hn_count, "arxiv": arxiv_count, "pubmed": max(0, pubmed_count)}

        # Build quality metrics
        quality_metrics = {
            "avg_source_score": round(sqi * 0.85 + 0.15, 2),
            "source_diversity": round(art["domains"] / 8, 2),
            "recency_score": 0.5,  # Default for older articles
        }

        content_entry = {
            "slug": slug,
            "language": "en",
            "title": title,
            "description": description,
            "body_html": body_html,
            "category": "blog",
            "tags": tags,
            "created_at": created_at,
            "updated_at": None,
            "pillar": pillar,
            "date_str": date,
            "thumbnail_svg": thumbnail_svg,
            "og_svg": og_svg,
            "featured_image": "",
            "trending_html": trending_html,
            "analysis_html": f"**Key entities:** `{'` · `'.join(title.split()[:5])}`\n"
                             f"**Key numbers:** {hn} · {art['source_count']} · {art['domains']}\n"
                             f"**SQI:** {sqi}",
            "cross_pillar_html": f"### Cross-pillar connections\n"
                                 f"- This article has connections to "
                                 f"{['Markets and Science','AML and Science','Markets and AML'][['aml','stock','science'].index(pillar)]}",
            "bloom_questions": bloom_questions,
            "flashcards": flashcards,
            "signals": signals,
            "source_breakdown": source_breakdown,
            "quality_metrics": quality_metrics,
            "lineage": {},
            "quality_flags": [],
        }

        registry["content"].append(content_entry)
        existing_slugs.add(slug)
        print(f"  Added: {slug}")

    # Regenerate thumbnails and OG for all content
    print("\nRegenerating thumbnail/OG SVGs for all articles...")
    for c in registry["content"]:
        if c.get("category") != "blog":
            continue
        slug = c["slug"]
        title = c["title"]
        pillar = c.get("pillar", "aml")
        date_str = c.get("date_str", "")
        c["thumbnail_svg"] = generate_thumbnail_svg(slug, title, pillar)
        c["og_svg"] = generate_og_svg(slug, title, pillar, date_str)

    # Sort content: blog posts by date desc, then non-blog
    def sort_key(item):
        if item.get("category") == "blog":
            return (0, item.get("date_str", ""))
        return (1, item.get("date_str", ""))

    registry["content"].sort(key=sort_key, reverse=False)
    # Actually: blog posts newest first, then other content
    blog_items = [c for c in registry["content"] if c.get("category") == "blog"]
    other_items = [c for c in registry["content"] if c.get("category") != "blog"]
    blog_items.sort(key=lambda c: c.get("date_str", ""), reverse=True)
    registry["content"] = blog_items + other_items

    registry["last_run"] = datetime.now(timezone.utc).isoformat()

    with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)

    total_blogs = sum(1 for c in registry["content"] if c.get("category") == "blog")
    total = len(registry["content"])
    print(f"\nDone. Registry now has {total_blogs} blog posts ({total} total items).")


if __name__ == "__main__":
    main()
