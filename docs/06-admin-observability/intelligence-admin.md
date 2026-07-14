# Intelligence Admin

Intelligence pages provide visibility into source freshness and ontology state.

## Sources Page (`admin/sources.html`)

Displays freshness status for all 32 inspiration sources:

### Overall Status Badge

| Status | Badge Color | Meaning |
|--------|-------------|---------|
| All active | Green | All 32 sources reachable |
| Some degraded | Amber | 1+ source returning 4xx |
| Some errors | Red | 1+ source unreachable |

### Per-Source Table

| Column | Description |
|--------|-------------|
| Source name | Human-readable name (e.g., "FATF") |
| URL | Source URL with link |
| Pillar | Compliance / Markets / Data |
| Status | Active (🟢) / Degraded (🟡) / Error (🔴) |
| HTTP status | Last HTTP status code |
| Last verified | Timestamp of last HEAD check |

Data source: `data/source_health.json` (loaded from static directory).

## Ontology Page (`admin/ontology.html`)

CRUD interface for ontology concepts and relations.

**Note:** Requires ontology argument to be passed to `generate_admin_pages()`. Without it, the page is not generated.

### Concept Management

When loaded, shows:
- **Total concepts** — Count from `ontology.concept_count()`
- **Total relations** — Count from `ontology.relation_count()`
- **Concept list** — All concepts with pillar, category, aliases
- **Relation list** — All relations with source → target, type, strength

### Display Sections

1. **Overview** — Concept and relation counts, pillar breakdown
2. **Concepts** — Table: ID, Label, Pillar, Category, Aliases, Confidence
3. **Relations** — Table: Source → Target, Type, Strength, Pillar
4. **Cross-pillar connections** — Relations bridging different pillars

## Data Refresh

Both pages are regenerated on each build:
- **Sources page** reads from the latest `source_health.json`
- **Ontology page** reads from the ontology object passed at build time

> **See also:** [Source Freshness](../04-ontology-knowledge-graph/source-freshness.md), [Ontology Model](../04-ontology-knowledge-graph/ontology-model.md)
