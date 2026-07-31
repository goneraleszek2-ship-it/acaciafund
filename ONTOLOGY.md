# AcaciaFund Ontology

Structured knowledge representation across three pillars: Compliance, Markets, Data Engineering.

> **Last updated:** 2026-07-30 · **Counts:** 192 concepts, 434 relations, 10 relation types.
> This is the canonical ontology reference. `docs/04-ontology-knowledge-graph/ontology-model.md` mirrors it in the sectional docs.

## Architecture

```
core/ontology.py          — Concept, Relation, ResourceLink, InspirationSource models
                           OntologyManager (add/query/seed/extract/export/persist/merge)
                           extract_concepts_from_text() keyword matcher

data/ontology.json        — Persisted ontology (192 concepts, 434 relations, philosophical
                           metadata, Feynman metadata)

etc/pillars.toml          — [inspiration_sources] per pillar (32 authoritative sources)
                           Seeded into ontology via seed_pillar() and seed_relations()

scripts/enrich_philosophy.py     — merges data/philosophy_metadata.json into ontology
scripts/validate_cross_pillar.py — bidirectional cross-pillar analog validation
scripts/audit_concept_coverage.py— concept coverage audit across all content
scripts/audit_philosophical_lineage.py — clusters concepts by philosophical lineage

build.py                  — Merges ontology into cytograph/graph-data.json
                           Extracts matching concepts for content items → concept badges
                           Loads inspiration sources → "Further Reading" section
                           Generates /concepts/{id}/ detail pages and retention data
```

## Concepts (192)

Each concept has:
- `id`: slug-style identifier (e.g., `kyc`, `delta-lake`, `factor-investing`)
- `label`: human-readable name
- `pillar`: owning pillar (`aml`, `stock`, `data-engineering`, `cross-pillar`)
- `category`: subcategory from `PILLAR_SUBCATEGORIES`
- `aliases`: alternative names for text matching
- `confidence_score`: extraction confidence (0.0–1.0)
- `source_inspiration`: originating source URL or organization
- **10 philosophical metadata fields** (Phase 2B — see below)

### Distribution

| Pillar | Concepts |
|--------|----------|
| Compliance (`aml`) | 58 |
| Markets (`stock`) | 64 |
| Data Engineering (`data-engineering`) | 70 |
| **Total** | **192** |

Example concepts: KYC, CDD, SAR, AML, CFT, sanctions, beneficial ownership, PEP, risk scoring (compliance); factor investing, momentum, value, Sharpe ratio, ESG, VaR, portfolio optimization (markets); data lake, data warehouse, ELT, ETL, Delta Lake, Iceberg, Kafka, dbt, lineage (data engineering).

### Philosophical Foundations Layer (Phase 2B)

Every concept carries 10 fields that ground it in its philosophical/epistemic context:

| Field | Description |
|-------|-------------|
| `philosophical_lineage` | Thinker → concept → technique genealogy |
| `epistemic_status` | Epistemic role: Constitutive, Instrumental, Regulatory, etc. |
| `normative_basis` | Normative theory: Kantian duty, Utilitarian, Rawlsian, etc. |
| `ontological_commitment` | What the concept presumes to exist |
| `temporal_ontology` | Time model the concept operates under |
| `uncertainty_class` | How uncertainty is represented |
| `governance_model` | Who/what governs the concept's application |
| `semantic_contract_type` | Nature of the concept's semantic contract |
| `philosophical_sources` | Primary philosophical references |
| `cross_pillar_analogs` | Same epistemic pattern in other pillars |

All 192 concepts carry `epistemic_status`; all 192 carry `cross_pillar_analogs`. Rendered on concept detail pages (`/concepts/{id}/`) via partials: `philosophical_lineage.j2`, `epistemic_badge.j2`, `normative_basis.j2`, `cross_pillar_philosophy.j2`.

### Feynman Learning Framework

Concepts are additionally enriched with Feynman-technique metadata (`data/feynman_metadata.json` via `scripts/enrich_feynman.py`), driving Feynman learning paths and cross-pillar Feynman synthesis pages.

## Relations (434)

Directed relationships between concepts. **10 relation types:**

| Type | Semantics |
|------|-----------|
| `part_of` | Hierarchical containment |
| `enables` | Capability relationship |
| `requires` | Dependency |
| `influences` | Indirect influence |
| `detects` | Detection capability |
| `regulates` | Regulatory/governance relationship |
| `supersedes` | Replacement/succession |
| `measures` | Measurement relationship |
| `implements` | Implementation of an abstraction |
| `related_to` | General association |

Each relation has `source_id`, `target_id`, `relation_type`, `strength` (0.0–1.0), and `pillar` (or `cross-pillar`). Cross-pillar relations connect concepts across domains (e.g., `kyc` → `data-governance`: `requires`; `factor-investing` → `data-pipeline`: `requires`).

Cross-pillar analogs are validated bidirectionally by `scripts/validate_cross_pillar.py`.

## Concept Extraction

`extract_concepts_from_text(text, manager)` performs lightweight keyword matching:

1. Matches text against concept labels and aliases (case-insensitive substring, word-boundary aware).
2. Returns `(concept, confidence)` tuples sorted by score.
3. Used in `build.py` to tag content with relevant ontology concepts (threshold ≥ 0.35 for the concept cache).
4. Used in `scripts/knowledge_ingester.py` during ingestion.
5. `extract_concepts_from_text()` default threshold is ≥ 0.5.

`data/concept_content_map.json` persists the concept → content mapping for audit and analytics.

## Graph Integration

Ontology concepts and relations are merged into the Cytoscape graph during build:
- Concept nodes: `ont:{id}` with `type: "concept"` and teal color
- Relation edges: `ont-rel:{i}` with `source`, `target`, `relation`, `strength`
- Merged via `OntologyManager.merge_into_cytograph()` (deduplicates by node/edge ID)
- Rendered at `/graph/` with pillar, relation-type, and layout filters

## Inspiration Sources (32)

External authoritative sources configured in `etc/pillars.toml` under `[inspiration_sources]`:

| Pillar | Sources |
|--------|---------|
| Compliance | FATF, ACAMS, FinCEN, OFAC, ECB, FCA, Egmont Group, FINTRAC, Payments.org, Chainalysis |
| Data Engineering | Databricks, Kafka, Flink, Iceberg, dbt, Dagster, Confluent, AWS, GCP, Meltano, Snowflake |
| Markets | SEC, BIS, IMF, MSCI, Bloomberg, S&P Global, Man Group, AQR, Reuters, FT, Quantocracy |

These are rendered as "Further Reading" links on knowledge pages. Freshness is checked weekly by `scripts/check_source_freshness.py` (status: active/degraded/error) and persisted to `data/source_health.json`.

## Usage

### Load and query
```python
from core.ontology import OntologyManager
mgr = OntologyManager.load("data/ontology.json")
concepts = mgr.concepts_by_pillar("aml")
related = mgr.related_concepts("kyc")
```

### Extract from text
```python
from core.ontology import extract_concepts_from_text
matches = extract_concepts_from_text(text, mgr)
for concept, score in matches:
    print(f"{concept.label}: {score:.2f}")
```

### Query philosophical metadata
```python
c = mgr.get_concept("kyc")
print(c.epistemic_status, c.normative_basis, c.philosophical_lineage)
for analog in c.cross_pillar_analogs:
    print(analog)
```

### Rebuild ontology
```python
from core.ontology import OntologyManager
mgr = OntologyManager()
mgr.seed_all_pillars()
mgr.seed_relations()
mgr.save("data/ontology.json")
```

### Export to graph
```python
cytograph = {"nodes": [], "edges": []}
cytograph = mgr.merge_into_cytograph(cytograph)
```

### Audit & validation scripts
```bash
python3 scripts/validate_cross_pillar.py            # bidirectional analog validation
python3 scripts/validate_cross_pillar.py --fix      # auto-add missing reciprocals
python3 scripts/audit_concept_coverage.py           # coverage across all content
python3 scripts/audit_philosophical_lineage.py      # cluster by lineage
```

## Retention Integration (Phase 3)

The ontology drives the portal-wide spaced-repetition system:

- `core/retention_engine.py` reviews all 192 concepts with SM-2 scheduling.
- Gap detection flags unseen, overdue (7+ days), and low-mastery (< 0.3) concepts.
- Interleaved practice mixes concepts across all 3 pillars.
- `dist/static/review_concepts.json` is generated at build time.
- Dashboards render at `/review/` (mastery) and `/review-queue/` (flashcards).
