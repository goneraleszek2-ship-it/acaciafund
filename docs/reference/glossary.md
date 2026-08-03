# Glossary

Domain-specific terminology used throughout the AcaciaFund codebase and documentation.

## A–C

| Term | Definition |
|------|------------|
| **Bloom Taxonomy** | Six-level cognitive framework: remember, understand, apply, analyze, evaluate, create. Used to scaffold learn module questions. |
| **Build Cache** | JSON file (`.build_cache.json`) storing content hashes for incremental build support. Avoids re-rendering unchanged items. |
| **Concept** | Named knowledge entity in the ontology (e.g., `kyc`, `delta-lake`, `factor-investing`). Has ID, label, pillar, category, aliases. |
| **Concept Boost** | Search ranking boost (+6) applied to items whose ontology concepts match the query. |
| **Concept Extraction** | Keyword matching of text against ontology concept labels and aliases. Used for search indexing and concept badges. |
| **Content Type** | One of `research`, `learn`, `knowledge`. Determines which template renders the item. |
| **Cross-pillar** | Content or relations that span multiple pillars. Knowledge pages and ontology relations can be cross-pillar. |
| **Cytoscape.js** | JavaScript graph visualization library used to render the knowledge graph at `/graph/`. |

## D–I

| Term | Definition |
|------|------------|
| **Facet Filter** | Search result filter by Pillar, Type, or Difficulty. Combined with AND logic. |
| **Flashcard** | Term/definition pair in learn modules. Interactive toggle card in the UI. |
| **Fuse.js** | Client-side fuzzy search library. Performs browser-based search against pre-built JSON index. |
| **Further Reading** | Links to authoritative external sources (from inspiration source data) shown on knowledge pages. |
| **Inspiration Source** | Authoritative external source URL configured in `etc/pillars.toml`. 32 total, checked weekly for freshness. |
| **Interest Score** | Combined ranking score: `0.6 × SQI + 0.4 × recency`. Used for content ordering. |
| **Internal Key** | Pillar identifier used internally: `aml`, `stock`, `data-engineering`. Translated to URL segments at build time. |

## K–O

| Term | Definition |
|------|------------|
| **Knowledge Category** | One of 13 cross-pillar categories: platform, guide, reference, architecture, foundations, advanced-techniques, best-practices, regulations, industry-analysis, market-analysis, strategies, methodology, tutorial-code. Mapped to pillar subcategories. |
| **Learn Module** | Interactive educational content with Bloom questions and flashcards. 83 total. |
| **Ontology** | Structured knowledge representation: concepts + relations + external resources. 199 concepts, 449 relations. |
| **OntologyManager** | Central class for managing the ontology: add/query/seed/extract/export/persist. |

## P–S

| Term | Definition |
|------|------------|
| **Pillar** | One of three content domains: Compliance (aml), Markets (stock), Data Engineering (data-engineering). |
| **Plausible** | Privacy-preserving web analytics. Tracks search events and result clicks without cookies. |
| **Pydantic v2** | Python data validation library used for registry schema (`schemas.py`) and ontology models (`core/ontology.py`). |
| **Quality Gate** | SQI threshold at 0.65. Items below are flagged but don't block the build. |
| **Relation** | Directed relationship between two ontology concepts. Types: part_of, enables, requires, influences, detects, regulates, supersedes, measures, implements, related_to. |
| **Research** | Content type for external article ingestion from arXiv, HN, PubMed, etc. 96 items. |
| **SQI** | Semantic Quality Index (0.0–1.0). Composite score from readability, topicality, recency, and concept coverage. |

## T–Z

| Term | Definition |
|------|------------|
| **Tag Page** | Archive page listing all items with a given tag. Generated at `/tags/{tag}/`. |
| **Taxonomy Generation** | Build phase that generates admin pages, search index, tag pages, pillar pages, and Atom feed via `core/build_taxonomies.py`. |
| **URL Segment** | The public-facing pillar URL: `compliance`, `markets`, `data`. Defined in `config.py:PILLAR_URL_MAP`. |
| **URL_STRUCTURE_VERSION** | Cache-busting version key in `config.py`. Bump to force full rebuild. Current: `"3.0"`. |
