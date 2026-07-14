# Client-Side Search

Search is entirely client-side using **Fuse.js** (`static/js/search.js`). There is no server-side search endpoint — the search index is pre-built as JSON and searched in the browser.

## Architecture

```
Page load → fetch /static/search-index.json → initialize Fuse.js
User types → debounce 200ms → Fuse.js search → render results
```

## Search Index

Generated at build time by `core/build_taxonomies.py:generate_search_pages()`.

**File:** `dist/static/search-index.json`

Each entry:

```json
{
  "slug": "aml/research/suspicious-transaction-reporting",
  "title": "Suspicious Transaction Reporting",
  "content_type": "research",
  "pillar": "aml",
  "description": "Overview of STR filing requirements...",
  "body_truncated": "The filing process involves...",
  "tags": ["sar", "str", "aml"],
  "difficulty": "intermediate",
  "date_str": "2026-06-15",
  "reading_time": 12,
  "sqi": 0.85,
  "concept_boost": ["sar", "str", "suspicious-activity-report"],
  "ontology_concepts": ["str", "aml"],
  "author": "AcaciaFund"
}
```

## Scoring Weights

| Field | Weight |
|-------|--------|
| `title` | +10 |
| `ontology_concepts` | +6 |
| `tags` | +4 |
| `description` | +2 |

Concept boost (`concept_boost`) provides additional relevance for items with matching ontology concepts.

## Facet Filters

Three facet filters with URL synchronization:

| Filter | Values | URL Param |
|--------|--------|-----------|
| Pillar | Compliance, Markets, Data | `?f_pillar=` |
| Type | Research, Learn, Knowledge | `?f_type=` |
| Difficulty | Beginner, Intermediate, Advanced | `?f_difficulty=` |

- Filters combine with AND logic
- URL sync via `?q=` + facet params (200ms debounce)
- Reset button clears all filters

## Keyboard Navigation

| Key | Action |
|-----|--------|
| `/` | Focus search input |
| `↑` / `↓` | Navigate results |
| `Enter` | Open selected result |
| `Esc` | Clear input / blur |

## Result Rendering

Each result card shows:
- Pillar pill (colored: amber/green/blue)
- Content type label (Research/Learn/Knowledge)
- Difficulty badge
- Date string
- SQI badge (colored by quality)
- Concept badges (from ontology_concepts)
- Tags (up to 3)

## Plausible Analytics

Search events are sent to Plausible (when configured):

```javascript
plausible('search', { props: { query: '...', results: N }})
plausible('search_result_click', { props: { query: '...', slug: '...' }})
```

Configured via `config.py:PLAUSIBLE_DOMAIN`.

> **See also:** [Search Index Generation](search-index.md), [Concept Boosting](concept-boosting.md)
