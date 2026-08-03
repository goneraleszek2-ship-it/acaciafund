# Knowledge Taxonomy

Knowledge items use an 11-category cross-pillar taxonomy. Each category is mapped to pillar-specific subcategories for navigation and display.

## Knowledge Categories

Defined in `build.py:KNOWLEDGE_CATEGORIES`:

| Category | Description | Example |
|----------|-------------|---------|
| `methodology` | Research methods and frameworks | "Cybernetic Manifesto" |
| `tooling` | Tools and software references | "Data Pipeline Tools" |
| `architecture` | System design and patterns | "Platform Architecture" |
| `tutorial` | Step-by-step guides | "Getting Started with dbt" |
| `reference` | Technical reference material | "API Reference" |
| `tutorial-code` | Code-focused tutorials | "Python for Data Engineering" |
| `case-study` | Real-world examples | "AML Case Study: Danske Bank" |
| `benchmark` | Performance comparisons | "Stream Processing Benchmarks" |
| `comparison` | Technology/approach comparisons | "Airflow vs Prefect vs Dagster" |
| `deep-dive` | In-depth analysis | "Deep Dive: Order Book Dynamics" |
| `landscape` | Market/industry overviews | "Data Engineering Landscape 2026" |

## Category-to-Pillar Mapping

Each knowledge category is mapped to a pillar-specific subcategory for breadcrumb display and navigation:

```python
KNOWLEDGE_TO_PILLAR_CATEGORY = {
    "platform": {
        "aml": "regtech",
        "stock": "market-microstructure",
        "data-engineering": "platform-engineering"
    },
    "guide": {
        "aml": "cdd-kyc",
        "stock": "trading-strategies",
        "data-engineering": "pipeline-architecture"
    },
    "reference": {
        "aml": "regulations",
        "stock": "market-microstructure",
        "data-engineering": "data-governance"
    },
    # ... 8 more categories
}
```

## Category Coverage

13 cross-pillar knowledge categories (defined in `build.py:KNOWLEDGE_CATEGORIES`). Categories with at least one item generate populated landing pages; categories without items generate placeholder landing pages so all `/knowledge/{cat}/` URLs resolve.

**Current state:** All 13 categories resolve to landing pages (7 populated — platform 4, reference 3, foundations 9, guide 3, architecture 3, regulations 1, industry-analysis 3 — and 6 placeholder as of 2026-08-03). Placeholder: advanced-techniques, best-practices, market-analysis, strategies, methodology, tutorial-code. (Counts verified from `dist/knowledge/*/index.html` item cards. The 3 pillar timeline pages were moved from reference → industry-analysis on 2026-08-03.)

## Pillar Subcategories Reference

For a complete list of pillar subcategories with labels and icons, see [Pillar System](../01-architecture/pillars.md).

> **See also:** [Pillar System](../01-architecture/pillars.md), [Content Types](content-types.md)
