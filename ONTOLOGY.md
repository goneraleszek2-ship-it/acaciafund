# AcaciaFund Ontology

Structured knowledge representation across three pillars: Compliance, Markets, Data Engineering.

## Architecture

```
core/ontology.py          — Concept, Relation, ResourceLink, InspirationSource models
                           OntologyManager (add/query/seed/extract/export/persist/merge)
                           extract_concepts_from_text() keyword matcher

data/ontology.json        — Persisted ontology (created on first build or ingestion)

etc/pillars.toml          — [inspiration_sources] per pillar (32 authoritative sources)
                           Seeded into ontology via seed_pillar() and seed_relations()

build.py                  — Merges ontology into cytograph/graph-data.json
                           Extracts matching concepts for knowledge items → concept badges
                           Loads inspiration sources → "Further Reading" section
```

## Concepts

Each concept has:
- `id`: slug-style identifier (e.g., `kyc`, `delta-lake`, `factor-investing`)
- `label`: human-readable name
- `pillar`: owning pillar (`aml`, `stock`, `data-engineering`, `cross-pillar`)
- `aliases`: alternative names for text matching
- `confidence_score`: extraction confidence (0.0–1.0)
- `source_inspiration`: originating source URL or organization

### Seeded Concepts (48)

| Pillar | Concepts |
|--------|----------|
| Compliance (aml) | 16 — KYC, CDD, SAR, AML, CFT, sanctions, beneficial ownership, PEP, risk scoring, etc. |
| Markets (stock) | 16 — factor investing, momentum, value, Sharpe ratio, ESG, VaR, portfolio optimization, etc. |
| Data Engineering | 16 — data lake, data warehouse, ELT, ETL, Delta Lake, Iceberg, Kafka, dbt, lineage, etc. |

## Relations

Directed relationships between concepts:
- `part_of`: hierarchical containment
- `enables`: capability relationship
- `mitigates`: risk/compliance relationship
- `requires`: dependency
- `competes_with`: alternative/comparison

### Cross-Pillar Relations (8)
- `kyc` → `data-governance`: requires
- `aml` → `data-lake`: enables
- `sanctions` → `real-time-processing`: requires
- `factor-investing` → `data-pipeline`: requires
- `portfolio-optimization` → `data-warehouse`: requires
- `risk-scoring` → `machine-learning`: enables
- `market-surveillance` → `stream-processing`: requires
- `regulatory-reporting` → `data-lake`: requires

## Concept Extraction

`extract_concepts_from_text(text, manager)` performs lightweight keyword matching:
1. Matches text against concept labels and aliases (case-insensitive substring)
2. Returns `(concept, confidence)` tuples sorted by score
3. Used in `build.py` to tag knowledge pages with relevant ontology concepts
4. Used in `scripts/knowledge_ingester.py` during ingestion

## Graph Integration

Ontology concepts and relations are merged into the Cytoscape graph during build:
- Concept nodes: `ont:{id}` with `type: "concept"` and teal color
- Relation edges: `ont-rel:{i}` with `source`, `target`, `relation`, `strength`
- Merged via `OntologyManager.merge_into_cytograph()` (deduplicates by node/edge ID)

## Inspiration Sources (32)

External authoritative sources configured in `etc/pillars.toml` under `[inspiration_sources]`:

| Pillar | Sources |
|--------|---------|
| Compliance | FATF, ACAMS, FinCEN, OFAC, ECB, FCA, Egmont Group, FINTRAC, Payments.org, Chainalysis |
| Data Engineering | Databricks, Kafka, Flink, Iceberg, dbt, Dagster, Confluent, AWS, GCP, Meltano, Snowflake |
| Markets | SEC, BIS, IMF, MSCI, Bloomberg, S&P Global, Man Group, AQR, Reuters, FT, Quantocracy |

These are rendered as "Further Reading" links on knowledge pages.

## Usage

### Load and query
```python
from core.ontology import OntologyManager
mgr = OntologyManager.load("data/ontology.json")
concepts = mgr.find_concepts_by_pillar("aml")
related = mgr.related_concepts("kyc")
```

### Extract from text
```python
from core.ontology import extract_concepts_from_text
matches = extract_concepts_from_text(text, mgr)
for concept, score in matches:
    print(f"{concept.label}: {score:.2f}")
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
