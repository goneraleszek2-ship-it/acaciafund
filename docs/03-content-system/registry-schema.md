# Registry Schema

The content registry (`registry.json`) is validated against Pydantic v2 models defined in `schemas.py`.

## RegistryData (Root Model)

```python
class RegistryData(BaseModel):
    version: str                    # Schema version
    generated_at: str               # ISO timestamp of last modification
    content: list[ContentItem]      # All content items
```

## ContentItem

```python
class ContentItem(BaseModel):
    slug: str                       # {pillar}/{content_type}/{topic}
    title: str                      # Human-readable title
    content_type: str               # "research" | "learn" | "knowledge"
    pillar: str                     # "aml" | "stock" | "data-engineering"
    category: str                   # Subcategory key from PILLAR_SUBCATEGORIES
    description: str                # Short description / excerpt
    body_html: str                  # Main content body (HTML or Markdown)
    tags: list[str]                 # Classification tags
    author: str                     # Author name
    date_str: str                   # Publication date (YYYY-MM-DD)
    reading_time: int               # Estimated reading time in minutes
    difficulty: str                 # "beginner" | "intermediate" | "advanced"
    language: str                   # Language code (default: "en")
    sqi: float | None               # Semantic Quality Index (0.0–1.0)
    signals: SQISignals | None      # Raw SQI signal data
    created_at: str | None          # ISO datetime of creation
    updated_at: str | None          # ISO datetime of last update
    image_url: str | None           # Featured image URL
    image_alt: str | None           # Featured image alt text
    featured: bool | None           # Featured content flag
    status: str | None              # "published" | "draft" | "review"
    external_url: str | None        # Original source URL (for ingested items)
    # Learn-specific fields:
    prerequisites: list[str] | None  # Prerequisite learn module slugs
    bloom_questions: list[dict] | None  # Bloom taxonomy questions
    flashcards: list[dict] | None      # Key concept flashcards
    code_examples: list[dict] | None   # Code examples (data pillar)
```

## SQISignals

```python
class SQISignals(BaseModel):
    avg_sqi: float | None           # Aggregate SQI score
    content_score: float | None     # Content quality (structure, length)
    readability_score: float | None  # Readability (Flesch, Coleman-Liau)
    topical_score: float | None     # Topical relevance
    recency_score: float | None     # Freshness (days since publication)
    concept_overlap: float | None   # Ontology concept coverage
```

## Validation Rules

The validator (`core/validator.py`) enforces:

| Rule | Check |
|------|-------|
| Required fields | `slug`, `title`, `content_type`, `pillar`, `body_html` |
| `content_type` enum | Must be `research`, `learn`, or `knowledge` |
| `pillar` enum | Must be `aml`, `stock`, or `data-engineering` |
| `difficulty` enum | Must be `beginner`, `intermediate`, or `advanced` |
| Slug uniqueness | No duplicate slugs |
| Slug format | Must match `{pillar}/{content_type}/{topic}` |
| URL-unsafe chars | Slug parts must not contain URL-unsafe characters |

## Example Registry Entry

```json
{
  "slug": "aml/learn/kyc-fundamentals",
  "title": "KYC Fundamentals",
  "content_type": "learn",
  "pillar": "aml",
  "category": "cdd-kyc",
  "description": "Core principles of Know Your Customer...",
  "body_html": "<h2>Introduction</h2><p>KYC is the process...</p>",
  "tags": ["kyc", "cdd", "identity-verification", "onboarding"],
  "author": "AcaciaFund",
  "date_str": "2026-06-15",
  "reading_time": 12,
  "difficulty": "intermediate",
  "language": "en",
  "sqi": 0.85,
  "signals": {
    "avg_sqi": 0.85,
    "content_score": 0.9,
    "readability_score": 0.8,
    "topical_score": 0.85,
    "recency_score": 0.7,
    "concept_overlap": 0.75
  },
  "created_at": "2026-06-15T10:00:00+00:00",
  "featured": false,
  "status": "published",
  "prerequisites": ["aml/learn/aml-basics"],
  "bloom_questions": [
    {"level": "remember", "question": "What does KYC stand for?"},
    {"level": "understand", "question": "Explain the purpose of KYC..."}
  ],
  "flashcards": [
    {"term": "KYC", "definition": "Know Your Customer..."}
  ]
}
```

> **See also:** [Content Types](content-types.md), [Schemas Reference](../reference/schemas-reference.md)
