# Search Index Generation

The search index is generated during build by `core/build_taxonomies.py:generate_search_pages()`.

## Function

```python
generate_search_pages(dist_dir, static_dir, all_content, render_template, ctx_base, ontology)
    -> int  # Number of search pages generated
```

## Generated Artifacts

| File | Description |
|------|-------------|
| `dist/search/index.html` | Search page rendered from `search.j2` |
| `dist/static/search-index.json` | JSON index for client-side Fuse.js |

## Index Fields

| Field | Source | Description |
|-------|--------|-------------|
| `slug` | Item slug | Internal slug |
| `title` | Item title | Searchable title |
| `content_type` | Item type | research/learn/knowledge — used for facet |
| `pillar` | Item pillar | aml/stock/data-engineering — used for facet |
| `description` | Item description | Searchable description |
| `body_truncated` | Body HTML | First 800 chars of body — searchable |
| `tags` | Item tags | Searchable tags — used for facet |
| `difficulty` | beginner/intermediate/advanced | Used for facet |
| `date_str` | Publication date | Display only |
| `reading_time` | Minutes | Display only |
| `sqi` | SQI score | Display only (badge) |
| `concept_boost` | Ontology concepts | Concept IDs for search boosting |
| `ontology_concepts` | Extracted concepts | Concept IDs for display |
| `author` | Item author | Display only |

## Empty Index Handling

If `all_content` is empty:
- Search page is still generated (renders empty state)
- `search-index.json` contains an empty array `[]`
- Returns 2 pages (search page + search index)

## Page Count

Returns the number of generated pages (2 for a standard build: search page + index).

## Ontology Integration

When an ontology manager is provided:
- Concepts are extracted from each item's body (`extract_concepts_from_text()`)
- Extracted concepts become `ontology_concepts` in the index
- Concept IDs are used for `concept_boost` scoring

> **See also:** [Client-Side Search](client-side-search.md), [Concept Boosting](concept-boosting.md)
