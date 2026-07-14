#!/usr/bin/env python3
"""
Source Synthesis Generator

Generates synthesis data from authoritative sources for each article:
- arXiv papers
- Scientific management literature
- Official documentation
- Industry reports
- Regulatory filings
- Inspiration sources from etc/pillars.toml

Output: /dist/source_synthesis.parquet + /dist/source_synthesis.json
"""

import hashlib
import json
import sys
from pathlib import Path

import pandas as pd
import tomllib

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
DIST_DIR = PROJECT_ROOT / "dist"
DIST_DIR.mkdir(exist_ok=True)

INSPIRATION_SOURCES_PATH = PROJECT_ROOT / "etc" / "pillars.toml"
ONTOLOGY_PATH = PROJECT_ROOT / "data" / "ontology.json"

PILLAR_TO_PREFIX = {"aml": "aml", "stock": "ms", "data-engineering": "de"}


def load_foundry_datasets():
    """Load Foundry datasets from Parquet files."""
    print("Loading Foundry datasets...")

    # Load source verification data (contains source metadata)
    source_ver_path = DIST_DIR / "source_verification.parquet"
    if source_ver_path.exists():
        source_df = pd.read_parquet(source_ver_path)
        print(f"  Loaded source verification: {len(source_df)} sources")
    else:
        print("  Warning: source_verification.parquet not found")
        source_df = pd.DataFrame()

    # Load quality scores
    quality_path = DIST_DIR / "quality_scores.parquet"
    if quality_path.exists():
        quality_df = pd.read_parquet(quality_path)
        print(f"  Loaded quality scores: {len(quality_df)} articles")
    else:
        print("  Warning: quality_scores.parquet not found")
        quality_df = pd.DataFrame()

    return source_df, quality_df


def load_registry():
    """Load registry.json for article metadata."""
    registry_path = PROJECT_ROOT / "registry.json"
    if registry_path.exists():
        with open(registry_path, "r") as f:
            return json.load(f)
    return {"content": []}


def load_inspiration_sources():
    """Load inspiration sources from etc/pillars.toml."""
    if not INSPIRATION_SOURCES_PATH.exists():
        return {}
    with open(INSPIRATION_SOURCES_PATH, "rb") as f:
        toml_data = tomllib.load(f)
    return toml_data.get("inspiration_sources", {})


def load_ontology_concepts():
    """Load ontology concept labels for source matching."""
    if not ONTOLOGY_PATH.exists():
        return {}
    try:
        from core.ontology import OntologyManager
        mgr = OntologyManager.load(ONTOLOGY_PATH)
        concept_map = {}
        for cid, concept in mgr._concepts.items():
            labels = [concept.label.lower()]
            labels.extend(a.lower() for a in concept.aliases)
            concept_map[cid] = {
                "label": concept.label,
                "pillar": concept.pillar,
                "keywords": labels,
            }
        return concept_map
    except Exception:
        return {}


def match_inspiration_sources(article, inspiration_sources, concept_map):
    """Match inspiration sources to an article based on pillar and concept overlap."""
    pillar = article.get("pillar", "")
    prefix = PILLAR_TO_PREFIX.get(pillar, "")
    if not prefix or prefix not in inspiration_sources:
        return []

    pillar_sources = inspiration_sources[prefix]
    article_tags = [t.lower() for t in article.get("tags", [])]
    title_lower = (article.get("title", "") or "").lower()
    body_lower = (article.get("body_html", "") or "").lower()

    # Extract ontology concepts from article text
    article_concepts = set()
    if concept_map:
        combined_text = f"{title_lower} {body_lower}"
        for cid, info in concept_map.items():
            for kw in info["keywords"]:
                if kw in combined_text:
                    article_concepts.add(cid)
                    break

    matches = []
    for src_key, src_info in pillar_sources.items():
        if not isinstance(src_info, dict) or "url" not in src_info:
            continue

        src_name_lower = src_info["name"].lower()
        src_desc_lower = src_info.get("description", "").lower()

        # Score relevance based on name/description tag overlap
        relevance = src_info.get("relevance", 0.7)
        tag_overlap = sum(1 for t in article_tags if t in src_desc_lower or t in src_name_lower)
        concept_overlap = sum(1 for c in article_concepts if c.lower() in src_desc_lower)

        # Boost relevance if article mentions source name
        name_mentioned = src_name_lower in title_lower or src_name_lower in body_lower[:1000]

        adjusted_relevance = relevance
        adjusted_relevance += min(0.1, tag_overlap * 0.03)
        adjusted_relevance += min(0.1, concept_overlap * 0.03)
        if name_mentioned:
            adjusted_relevance = min(1.0, adjusted_relevance + 0.15)

        if tag_overlap > 0 or concept_overlap > 0 or name_mentioned:
            matches.append({
                "source_key": src_key,
                "source_name": src_info["name"],
                "source_url": src_info["url"],
                "description": src_info.get("description", ""),
                "frequency": src_info.get("frequency", "monthly"),
                "base_relevance": relevance,
                "adjusted_relevance": round(min(1.0, adjusted_relevance), 3),
                "matched_concepts": list(article_concepts & {c for c in concept_map if any(
                    kw in src_desc_lower for kw in concept_map[c]["keywords"]
                )})[:5],
                "tag_overlap": tag_overlap,
                "name_mentioned": name_mentioned,
            })

    matches.sort(key=lambda x: x["adjusted_relevance"], reverse=True)
    return matches[:6]


def extract_tags_from_article(article):
    """Extract tags from article for source matching."""
    tags = article.get("tags", [])
    if article.get("pillar"):
        tags.append(article["pillar"])
    if article.get("content_type"):
        tags.append(article["content_type"])
    return [t.lower() for t in tags]


def match_sources_to_articles(source_df, registry):
    """Match sources to articles based on tags and pillars."""
    print("Matching sources to articles...")

    article_sources = {}

    for item in registry.get("content", []):
        slug = item.get("slug", "")
        if not slug:
            continue

        # Extract article tags
        article_tags = extract_tags_from_article(item)
        pillar = item.get("pillar", "aml")

        # Find matching sources
        matching_sources = []

        if len(source_df) > 0:
            for _, source in source_df.iterrows():
                source_url = str(source.get("url", "")).lower()
                source_title = str(source.get("title", "")).lower()
                source_type = source.get("source_type", "unknown")

                # Check if source is relevant to article
                is_relevant = False

                # Check for tag matches
                for tag in article_tags:
                    if tag in source_url or tag in source_title:
                        is_relevant = True
                        break

                # Check for pillar matches
                if pillar.lower() in source_url or pillar.lower() in source_title:
                    is_relevant = True

                # Check for source type relevance
                source_type_lower = str(source_type).lower()
                if "arxiv" in source_type_lower or "arxiv" in source_url:
                    is_relevant = True
                elif "github" in source_url or "gitlab" in source_url:
                    is_relevant = True
                elif "pubmed" in source_url or "science" in source_type_lower:
                    is_relevant = True
                elif "gartner" in source_url or "forrester" in source_url:
                    is_relevant = True
                elif "sec" in source_url or "fatf" in source_url:
                    is_relevant = True

                if is_relevant:
                    matching_sources.append(source.to_dict())

        if matching_sources:
            article_sources[slug] = matching_sources
            print(f"  {slug}: {len(matching_sources)} matching sources")

    return article_sources


def compute_synthesis_scores(sources, quality_df):
    """Compute synthesis scores for each source."""
    print("Computing synthesis scores...")

    results = []

    for source in sources:
        # Base scores
        credibility_score = 0.7
        relevance_score = 0.6
        quality_score = 0.65

        # Adjust based on source type
        source.get("source_type", "unknown").lower()
        source_url = str(source.get("url", "")).lower()

        # Credibility boosts
        if "arxiv" in source_url:
            credibility_score = 0.85
        elif "pubmed" in source_url:
            credibility_score = 0.90
        elif "github" in source_url or "gitlab" in source_url:
            credibility_score = 0.80
        elif "gartner" in source_url or "forrester" in source_url:
            credibility_score = 0.75
        elif "sec" in source_url or "fatf" in source_url:
            credibility_score = 0.95

        # Relevance boosts
        if "arxiv" in source_url:
            relevance_score = 0.80
        elif "pubmed" in source_url:
            relevance_score = 0.85
        elif "github" in source_url:
            relevance_score = 0.75
        elif "gartner" in source_url:
            relevance_score = 0.70
        elif "sec" in source_url:
            relevance_score = 0.90

        # Overall synthesis score
        synthesis_score = 0.4 * credibility_score + 0.35 * relevance_score + 0.25 * quality_score

        results.append(
            {
                **source,
                "synthesis_score": round(synthesis_score, 3),
                "relevance_score": round(relevance_score, 3),
                "credibility_score": round(credibility_score, 3),
            }
        )

    return results


def generate_synthesis_description(source, article_tags):
    """Generate compelling synthesis description for source."""
    source_type = source.get("source_type", "unknown").lower()
    source_url = str(source.get("url", "")).lower()

    descriptions = {
        "arxiv": f"Academic preprint providing theoretical foundation and empirical evidence for {', '.join(article_tags[:2]) if article_tags else 'this topic'}.",
        "pubmed": "Peer-reviewed medical/scientific research offering clinical evidence and data analysis.",
        "github": "Official documentation and technical specifications from the project repository.",
        "gitlab": "Official documentation and technical specifications from the project repository.",
        "gartner": "Industry analysis and market research providing strategic insights and trends.",
        "forrester": "Market research and strategic analysis for technology decision-makers.",
        "sec": "Official regulatory filings providing compliance and legal context.",
        "fatf": "International standards and regulatory guidance for financial crime prevention.",
    }

    default = "Authoritative source providing additional context and evidence for the analysis presented in this article."

    for key, desc in descriptions.items():
        if key in source_url or key in source_type:
            return desc

    return default


def extract_key_insights(source):
    """Extract 3-4 key insights from source."""
    source_type = source.get("source_type", "unknown").lower()
    source_url = str(source.get("url", "")).lower()

    insights_map = {
        "arxiv": [
            "Novel methodology or approach introduced",
            "Empirical validation of theoretical concepts",
            "Comparative analysis with existing techniques",
            "Limitations and future research directions",
        ],
        "pubmed": [
            "Clinical study findings and outcomes",
            "Statistical significance and effect sizes",
            "Patient population characteristics",
            "Recommendations for practice or further research",
        ],
        "github": [
            "Core architecture and design patterns",
            "API documentation and usage examples",
            "Contribution guidelines and best practices",
            "Known issues and roadmap",
        ],
        "gitlab": [
            "Infrastructure as code patterns",
            "CI/CD pipeline configuration",
            "Security and compliance considerations",
            "Scaling and performance guidelines",
        ],
        "gartner": [
            "Market size and growth projections",
            "Key vendor landscape analysis",
            "Adoption trends and maturity curves",
            "Strategic recommendations",
        ],
        "forrester": [
            "Technology adoption forecasts",
            "Customer behavior insights",
            "ROI calculations and cost-benefit analysis",
            "Implementation best practices",
        ],
        "sec": [
            "Regulatory requirements and compliance obligations",
            "Enforcement priorities and recent actions",
            "Risk factors and disclosure requirements",
            "Legal precedents and interpretations",
        ],
        "fatf": [
            "International standards and recommendations",
            "Risk-based approach guidance",
            "Customer due diligence requirements",
            "Emerging typologies and red flags",
        ],
    }

    default_insights = [
        "Key findings and conclusions",
        "Methodology and data sources",
        "Practical applications",
        "Limitations and caveats",
    ]

    for key, insights in insights_map.items():
        if key in source_url or key in source_type:
            return insights[:4]

    return default_insights


def generate_synthesis_data():
    """Main function to generate source synthesis data."""
    print("=" * 60)
    print("Source Synthesis Generator")
    print("=" * 60)

    # Load Foundry datasets
    source_df, quality_df = load_foundry_datasets()

    # Load inspiration sources and ontology
    inspiration_sources = load_inspiration_sources()
    concept_map = load_ontology_concepts()
    total_inspr = sum(len(v) for v in inspiration_sources.values() if isinstance(v, dict))
    print(f"  Loaded {total_inspr} inspiration sources, {len(concept_map)} ontology concepts")

    # Load registry
    registry = load_registry()
    print(f"Loaded {len(registry.get('content', []))} articles from registry")

    # Match sources to articles
    article_sources = match_sources_to_articles(source_df, registry)

    # Generate synthesis data
    print("\nGenerating synthesis data...")
    synthesis_records = []
    inspr_match_count = 0

    for slug, sources in article_sources.items():
        article_item = None
        for item in registry.get("content", []):
            if item.get("slug") == slug:
                article_item = item
                article_tags = extract_tags_from_article(item)
                break
        else:
            article_tags = []

        scored_sources = compute_synthesis_scores(sources, quality_df)

        for source in scored_sources:
            synthesis_id = hashlib.md5(f"{slug}_{source.get('url', '')}".encode()).hexdigest()[:12]

            raw_insights = extract_key_insights(source)
            key_insights = list(raw_insights) if hasattr(raw_insights, "__iter__") else raw_insights

            synthesis_record = {
                "synthesis_id": synthesis_id,
                "article_slug": slug,
                "source_type": str(source.get("source_type", "unknown")),
                "source_url": str(source.get("url", "")),
                "source_title": str(source.get("title", "Source")),
                "synthesis_score": float(source.get("synthesis_score", 0)),
                "relevance_score": float(source.get("relevance_score", 0)),
                "credibility_score": float(source.get("credibility_score", 0)),
                "synthesis_text": str(generate_synthesis_description(source, article_tags)),
                "key_insights": key_insights,
                "synthesis_category": "evidence",
                "publication_date": str(source.get("published_date", "")),
                "author_affiliation": str(source.get("author", "")),
                "source_id": str(source.get("source_id", "")),
                "domain": str(source.get("domain", "")),
                "inspiration_match": False,
                "inspiration_source": "",
                "matched_concepts": "",
            }

            synthesis_records.append(synthesis_record)

        # Add inspiration source matches as synthesis entries
        if article_item and inspiration_sources:
            inspr_matches = match_inspiration_sources(article_item, inspiration_sources, concept_map)
            for match in inspr_matches:
                inspr_match_count += 1
                inspr_id = hashlib.md5(f"{slug}_{match['source_key']}".encode()).hexdigest()[:12]
                inspr_record = {
                    "synthesis_id": inspr_id,
                    "article_slug": slug,
                    "source_type": "inspiration",
                    "source_url": match["source_url"],
                    "source_title": match["source_name"],
                    "synthesis_score": float(match["adjusted_relevance"]),
                    "relevance_score": float(match["adjusted_relevance"]),
                    "credibility_score": float(match["base_relevance"]),
                    "synthesis_text": match["description"],
                    "key_insights": ["Authoritative external source", match["description"][:100]],
                    "synthesis_category": "inspiration",
                    "publication_date": "",
                    "author_affiliation": match["source_name"],
                    "source_id": match["source_key"],
                    "domain": "",
                    "inspiration_match": True,
                    "inspiration_source": match["source_name"],
                    "matched_concepts": ",".join(match.get("matched_concepts", [])[:5]),
                }
                synthesis_records.append(inspr_record)

    # Create DataFrame
    synthesis_df = pd.DataFrame(synthesis_records)

    # Save to Parquet
    parquet_path = DIST_DIR / "source_synthesis.parquet"
    synthesis_df.to_parquet(parquet_path, index=False)
    print(f"\nSaved synthesis data to {parquet_path}")
    print(f"Total synthesis records: {len(synthesis_df)}")

    # Save to JSON
    json_path = DIST_DIR / "source_synthesis.json"
    # Convert numpy types to Python native types for JSON serialization
    json_records = []
    for rec in synthesis_records:
        json_rec = {}
        for k, v in rec.items():
            if isinstance(v, (list, tuple)):
                json_rec[k] = list(v)
            elif hasattr(v, "item"):  # numpy scalar
                json_rec[k] = v.item()
            else:
                json_rec[k] = v
        json_records.append(json_rec)

    with open(json_path, "w") as f:
        json.dump(json_records, f, indent=2, default=str)
    print(f"Saved synthesis data to {json_path}")

    # Summary statistics
    if len(synthesis_df) > 0:
        print("\nSummary Statistics:")
        print(f"  Articles with synthesis: {synthesis_df['article_slug'].nunique()}")
        print(f"  Average synthesis score: {synthesis_df['synthesis_score'].mean():.3f}")
        print(f"  Source types: {synthesis_df['source_type'].value_counts().to_dict()}")
        if inspr_match_count > 0:
            print(f"  Inspiration source matches: {inspr_match_count}")

    return synthesis_df


if __name__ == "__main__":
    generate_synthesis_data()
