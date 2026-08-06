# Content Types

AcaciaFund has three content types: **Research**, **Learn**, and **Knowledge**. Each type uses a different Jinja2 template and serves a distinct purpose in the content taxonomy.

## Research (102 items)

**Template:** `research.j2`
**Purpose:** External content ingestion and synthesis from authoritative sources.

**Sources:** arXiv, HackerNews, PubMed, SEC EDGAR, SSRN, NBER

**Key features:**
- External source attribution and links
- SQI quality badges
- Topic icons (up to 3 per item)
- Cross-pillar connection suggestions
- Reading time estimates
- Difficulty indicators

**Rendering pipeline:**
```
body_html → clean HTML → extract headings → inject section images
→ render template → write output
```

## Learn (83 items)

**Template:** `learn.j2`
**Purpose:** Interactive educational modules using Bloom's taxonomy.

**Key features:**
- **Bloom questions** — 3-5 questions per module across 6 cognitive levels:
  - `remember`: Recall facts
  - `understand`: Explain concepts
  - `apply`: Use in scenarios
  - `analyze`: Break down and compare
  - `evaluate`: Critically assess
  - `create`: Design and construct
- **Flashcards** — 2-4 key term/definition pairs per module
- **Prerequisites** — Sequential learning paths (defined in `seed_learn.py`)
- **Code examples** (data pillar only)
- **SQI badges**

**Generation:** Auto-generated via `scripts/generate_learn_modules.py`

## Knowledge (41 items)

**Template:** `knowledge.j2`
**Purpose:** Platform documentation, methodology, architecture decisions.

**Key features:**
- **Concept badges** — Ontology concepts matched via `extract_concepts_from_text()`
- **Further Reading** — Links to authoritative sources from inspiration source data
- **Cross-pillar navigation** — Connections to related content in other pillars

**Cross-pillar categories:**
Knowledge items use 13 cross-pillar categories (defined in `build.py:KNOWLEDGE_CATEGORIES`):
`platform`, `guide`, `reference`, `architecture`, `foundations`, `advanced-techniques`, `best-practices`, `regulations`, `industry-analysis`, `market-analysis`, `strategies`, `methodology`, `tutorial-code`

These are resolved to pillar-specific subcategories via `config.py:KNOWLEDGE_TO_PILLAR_CATEGORY`. Categories with no items still get a landing page at `/knowledge/{cat}/`.

## Rendering Differences

| Aspect | Research | Learn | Knowledge |
|--------|----------|-------|-----------|
| Template | `research.j2` | `learn.j2` | `knowledge.j2` |
| SQI badge | Yes | Yes | Yes |
| Topic icons | Yes (up to 3) | No | No |
| Bloom questions | No | Yes (3-5) | No |
| Flashcards | No | Yes (2-4) | No |
| Code examples | No | Yes (data only) | No |
| Concept badges | No | No | Yes |
| Further Reading | No | No | Yes |
| Prerequisites | No | Yes | No |
| Cross-pillar links | Yes | No | Yes |
| External source link | Yes | No | No |

> **See also:** [Registry Schema](registry-schema.md), [Learn Modules](learn-modules.md), [Knowledge Taxonomy](knowledge-taxonomy.md)
