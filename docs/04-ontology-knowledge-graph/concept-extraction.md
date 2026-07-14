# Concept Extraction

`extract_concepts_from_text()` performs lightweight keyword matching against ontology concepts. It's used during build to tag knowledge pages and during ingestion to identify relevant concepts.

## Function Signature

```python
extract_concepts_from_text(text: str, manager: OntologyManager, min_score: float = 0.5)
    -> list[tuple[Concept, float]]
```

## Matching Algorithm

1. **Tokenize** the input text into words and phrases
2. **Match** against concept labels and aliases (case-insensitive, word-boundary-aware)
3. **Score** each match:
   - Exact label match: 1.0
   - Alias match: 0.8 × alias confidence
   - Partial match: 0.5 × label similarity
4. **Filter** by `min_score` (default 0.5)
5. **Deduplicate** by concept ID (highest score wins)
6. **Sort** by score descending

## Thresholds

| Context | Threshold | Location |
|---------|-----------|----------|
| Inline concept cache | ≥ 0.35 | `build.py` (more lenient) |
| Default extraction | ≥ 0.50 | `core/ontology.py:extract_concepts_from_text()` |
| Knowledge page badges | ≥ 0.50 | Used during build for concept badges |

## Usage in Build

During build, `build.py` extracts concepts for knowledge items:

```python
from core.ontology import extract_concepts_from_text

# Extract concepts for a knowledge page
matches = extract_concepts_from_text(item.body_html, ontology_manager)
concept_names = [c.label for c, s in matches[:5]]  # Top 5 concepts

# Add to search index for concept boosting
item.concept_boost = [c.id for c, s in matches[:3]]
```

## Usage in Ingestion

During content ingestion, `scripts/knowledge_ingester.py` extracts concepts:

```python
matches = extract_concepts_from_text(article_text, mgr)
for concept, score in matches:
    print(f"  {concept.label}: {score:.2f}")
```

## Validation

Check for false positives in concept extraction:

```bash
python3 -c "
from core.ontology import OntologyManager, extract_concepts_from_text
m = OntologyManager.load('data/ontology.json')
tests = [
    ('streaming data pipeline', 'str should NOT match'),
    ('about our data', 'beneficial-ownership should NOT match'),
    ('Know Your Customer compliance', 'kyc SHOULD match'),
    ('suspicious transaction report filing', 'str SHOULD match'),
]
for text, desc in tests:
    result = extract_concepts_from_text(text, m)
    ids = [c.id for c, s in result]
    print(f'  {desc}: {ids}')
"
```

## Known Issues

- **Word boundary matching:** Implemented to prevent "streaming data" matching concept "data" (string containment). Uses regex word boundaries.
- **Threshold tuning:** If extraction is too strict, lower `min_score` in `extract_concepts_from_text()`. If too loose, raise it.

> **See also:** [Ontology Model](ontology-model.md), [Cytoscape Export](cytograph-export.md), [Search Concept Boosting](../05-search-discovery/concept-boosting.md)
