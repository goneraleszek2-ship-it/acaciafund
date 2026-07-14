# Content Model

The content registry (`registry.json`) is the single source of truth for all site content. It is validated against Pydantic schemas defined in `schemas.py`.

## Registry Schema

```python
# schemas.py — Core models
class RegistryData(BaseModel):
    version: str
    generated_at: str
    content: list[ContentItem]

class ContentItem(BaseModel):
    slug: str                    # Internal slug: {pillar}/{content_type}/{topic}
    title: str                   # Human-readable title
    content_type: str            # One of: "research", "learn", "knowledge"
    pillar: str                  # Internal key: "aml", "stock", "data-engineering"
    category: str                # Subcategory key (from PILLAR_SUBCATEGORIES)
    description: str
    body_html: str               # Main content body
    tags: list[str]
    author: str
    date_str: str                # Publication date string
    reading_time: int            # Minutes
    difficulty: str              # "beginner", "intermediate", "advanced"
    language: str                # Default: "en"
    sqi: float | None            # Semantic Quality Index (0.0–1.0)
    signals: SQISignals | None   # Raw signal data for SQI computation
    created_at: str | None       # ISO datetime
    updated_at: str | None
    image_url: str | None
    image_alt: str | None
    featured: bool | None
    status: str | None           # "published", "draft", "review"
    external_url: str | None     # Original source if ingested

class SQISignals(BaseModel):
    avg_sqi: float | None
    content_score: float | None
    readability_score: float | None
    topical_score: float | None
    recency_score: float | None
    concept_overlap: float | None
```

## Content Types

| Type | Count | Purpose |
|------|-------|---------|
| `research` | ~163 | External content from arXiv, HN, PubMed, etc. |
| `learn` | ~54 | Interactive modules with Bloom questions and flashcards |
| `knowledge` | ~43 | Platform docs, tutorials, methodology, case studies |

### Research

Research items are ingested from external sources. They use the `research.j2` template and typically have:
- External source attribution
- SQI badges
- Topic icons
- Cross-pillar connections

### Learn

Learn modules are auto-generated interactive educational content. They use the `learn.j2` template and include:
- Bloom taxonomy questions (remember → understand → apply → analyze → evaluate → create)
- Flashcards for key concepts
- Code examples (data pillar)
- Prerequisite relations (defined in `seed_learn.py`)

### Knowledge

Knowledge items are platform documentation and reference material. They use the `knowledge.j2` template and feature:
- Concept badges (from ontology matching)
- Further Reading links (from inspiration sources)
- Cross-pillar navigation

## Slug Format

Slugs use internal pillar keys and are translated at build time:

```
Internal:     aml/research/suspicious-transaction-reporting
Filesystem:   compliance/research/suspicious-transaction-reporting/index.html
URL:          /compliance/research/suspicious-transaction-reporting/

Internal:     knowledge/platform-architecture
URL:          /knowledge/platform-architecture/
```

## Validation Rules

The validator (`core/validator.py`) enforces:
- Required fields: `slug`, `title`, `content_type`, `pillar`, `body_html`
- `content_type` must be one of: `research`, `learn`, `knowledge`
- `pillar` must be one of: `aml`, `stock`, `data-engineering`
- `difficulty` must be one of: `beginner`, `intermediate`, `advanced`
- No duplicate slugs
- Slug format must match `{pillar}/{content_type}/{topic}`

> **See also:** [Schemas Reference](../reference/schemas-reference.md), [Quality Gates](../03-content-system/quality-gates.md)
