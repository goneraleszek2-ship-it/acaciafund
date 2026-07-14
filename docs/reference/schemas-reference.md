# Schemas Reference

Pydantic v2 models from `schemas.py` for registry validation.

## RegistryData

Root model for `registry.json`:

```python
class RegistryData(BaseModel):
    version: str                     # Schema version string
    generated_at: str                # ISO 8601 timestamp
    content: list[ContentItem]       # All content items
```

## ContentItem

```python
class ContentItem(BaseModel):
    slug: str                        # Internal slug: {pillar}/{content_type}/{topic}
    title: str                       # Human-readable title
    content_type: str                # "research" | "learn" | "knowledge"
    pillar: str                      # "aml" | "stock" | "data-engineering"
    category: str                    # Subcategory from PILLAR_SUBCATEGORIES
    description: str                 # Short excerpt / description
    body_html: str                   # Main content (HTML or Markdown)
    tags: list[str]                  # Classification tags
    author: str                      # Author or "AcaciaFund"
    date_str: str                    # Publication date (YYYY-MM-DD)
    reading_time: int                # Estimated reading minutes
    difficulty: str                  # "beginner" | "intermediate" | "advanced"
    language: str                    # Language code (default: "en")
    sqi: float | None                # Semantic Quality Index (0.0–1.0)
    signals: SQISignals | None       # Raw SQI signal data
    created_at: str | None           # ISO 8601 datetime
    updated_at: str | None           # ISO 8601 datetime
    image_url: str | None            # Featured image URL
    image_alt: str | None            # Image alt text
    featured: bool | None            # Featured content flag
    status: str | None               # "published" | "draft" | "review"
    external_url: str | None         # Original source (ingested items)
```

### ContentItem Validation

| Field | Rule |
|-------|------|
| `content_type` | Must be `"research"`, `"learn"`, or `"knowledge"` |
| `pillar` | Must be `"aml"`, `"stock"`, or `"data-engineering"` |
| `difficulty` | Must be `"beginner"`, `"intermediate"`, or `"advanced"` |
| `sqi` | If set, must be 0.0–1.0 |
| `reading_time` | Must be > 0 |
| `slug` | No duplicates across all items |

## SQISignals

```python
class SQISignals(BaseModel):
    avg_sqi: float | None            # Aggregate SQI
    content_score: float | None      # Content quality (0.0–1.0)
    readability_score: float | None  # Readability (0.0–1.0)
    topical_score: float | None      # Topical relevance (0.0–1.0)
    recency_score: float | None      # Freshness (0.0–1.0)
    concept_overlap: float | None    # Ontology coverage (0.0–1.0)
```

## Learn Module Extensions

Learn modules extend `ContentItem` with additional fields (not strictly typed in schema, but used at build time):

| Field | Type | Description |
|-------|------|-------------|
| `prerequisites` | `list[str]` | Prerequisite learn module slugs |
| `bloom_questions` | `list[dict]` | `[{"level": "remember", "question": "..."}]` |
| `flashcards` | `list[dict]` | `[{"term": "...", "definition": "..."}]` |
| `code_examples` | `list[dict]` | `[{"language": "python", "code": "..."}]` |
