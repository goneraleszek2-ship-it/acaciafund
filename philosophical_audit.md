# Philosophical Audit of AcaciaFund Codebase

## Audit Scope
- Codebase: AcaciaFund static knowledge platform (Python/Jinja2)
- Repository: /root/acaciafund
- Version: 2026-08-16 (post-Phase 2B philosophy metadata integration)
- Total registry items: 226 (across 3 pillars: compliance/aml, markets/stock, data-engineering)

## 1. Current Philosophical Commitments (Implicit, Not Explicit)

### 1.1 Empiricism (Default, Unmarked)
- **Evidence:** 32+ inspiration sources (arXiv, Hacker News, PubMed, SEC, FATF, Databricks)
- **Validation:** Pydantic schema validation in `schemas.py` → `ContentItem`
- **Quality:** SQI (Signal Quality Index) scoring, source_verified boolean
- **Test coverage:** 1218 Python tests + 5 JS suites
- **Architectural location:** 
  - `schemas.py` → `ContentItem` model (no explicit epistemic status)
  - `config.py` → `SQI_THRESHOLD_MIN = 0.65`, quality gate scripts
  - `scripts/check_source_freshness.py` → 65 source HTTP checks
  - `build.py` → content validation pipeline

**Implicit claim:** Knowledge claims are "verified" by default through source verification and SQI scoring. No alternative evidentiary standards are visible or supported.

### 1.2 Confucian/Bloom Hierarchy (Default, Unmarked)
- **Evidence:** Bloom's Taxonomy questions on learn pages (6 levels: remember→create)
- **Structure:** Prerequisite-based learning paths via `core/learning_paths.py`
- **Categorization:** 13 knowledge categories with structured progression
- **Architectural location:**
  - `build.py` → Bloom question generation and categorization
  - `seed_learn.py` → Prerequisite DAG for learning modules
  - `templates/learn.j2` → Bloom level badges with skill tooltips

**Implicit claim:** Learning must follow a hierarchical progression from foundational to advanced. Skipping levels is implicitly discouraged.

### 1.3 Systems/Network Ontology (Explicit, Enforced)
- **Evidence:** 199 ontology concepts with 447 directed relations (requires, enables, influences, etc.)
- **Structure:** Directed graph via `core/ontology.py` → `OntologyManager`
- **Validation:** `tests/test_ontology.py` (39 tests), concept extraction thresholds
- **Architectural location:**
  - `core/ontology.py` → Concept, Relation models; seed_all_pillars(), seed_relations()
  - `build.py` → build_taxonomies() generates admin, search, tag, pillar pages from ontology
  - `data/ontology.json` → Persisted state (199 concepts, 447 relations)

**Explicit claim:** Knowledge is structured as an interconnected graph of concepts. This is the "official" knowledge structure of the platform.

### 1.4 SM-2 Spaced Repetition (Explicit, Enforced)
- **Evidence:** Client-side SM-2 algorithm in `static/js/retention_engine.js`
- **Structure:** Concept review scheduling, mastery scoring, gap detection
- **Architectural location:**
  - `core/retention_engine.py` → SM-2 algorithm, gap detection, interleaving
  - `static/js/retention_engine.js` → Client-side review engine
  - `static/review_concepts.json` → Build-generated review data (199 concepts)
  - `tests/test_retention_engine.py` → 38 tests

**Explicit claim:** Knowledge decay is real and requires active maintenance through spaced repetition.

### 1.5 Static-Site First / Platonism (Explicit, Enforced)
- **Evidence:** `build.py` generates ~2,505 static pages → Cloudflare Pages, no runtime backend
- **Architectural location:**
  - `build.py` → Main generator (~3,726 lines)
  - `config.py` → `URL_STRUCTURE_VERSION = "3.0"` (bump for structural changes)
  - `scripts/deploy_cloudflare.py` → Deployment trigger

**Explicit claim:** Knowledge exists independently of observer - the static site is the "true" form, and the client-side JavaScript is merely a viewing interface.

## 2. Identified Western/Eastern Tensions (7 Conflicts)

| # | Western Pillar | Eastern Pillar | System Behavior | Conflict Source |
|---|---------------|----------------|-----------------|-----------------|
| 1 | Logical positivism (verification) | Buddhist fallibility | 855-test suite + Pydantic schema = verification as truth | `schemas.py` validation + `tests/` dominance |
| 2 | Confucian hierarchy (progression) | Zen non-dual resistance | Prerequisite DAG + learning journeys | `seed_learn.py` + `build.py` learning paths |
| 3 | Empiricism (32 sources) | Inner knowing / contemplation | Content from external sources only | `registry.json` ingestion + `scripts/fetch_news.py` |
| 4 | Linear progress narrative | Present-moment awareness | Diagnostic labeling + SM-2 tracking | `diagnostic.py` + retention engine |
| 5 | Ontological categorization | Emptiness / śūnyatā | 192 concepts + 434 relations | `ONTOLOGY.md` + `core/ontology.py` |
| 6 | Efficiency (76s build) | Diligence / repeated practice | Incremental hashing + build speed | `config.py` `URL_STRUCTURE_VERSION` + build.py |
| 7 | Knowledge as commodity | Knowledge as practice | Platform deployment + ROI language | `scripts/deploy_cloudflare.py` + mission statement |

## 3. Current Discrimination Patterns

### 3.1 Verification Gatekeeping
- **Mechanism:** Pydantic schema + test suite = content must pass validation to publish
- **Impact:** Content failing SQI < 0.65 blocked from deployment (via `scripts/enforce_quality_gate.py`)
- **Discrimination:** Content with alternative evidentiary standards (contemplative, authoritative) has no pathway

### 3.2 Hierarchical Progression Only
- **Mechanism:** Learning journeys with hard prerequisites; no "direct engagement" mode
- **Impact:** Users cannot bypass structured progression without code modification
- **Discrimination:** Users preferring non-linear or direct apprehension of knowledge

### 3.3 Empiricism as Default
- **Mechanism:** All content originates from 32+ external sources; no "inner knowing" or "contemplative" tags
- **Impact:** Users seeking contemplative or authoritative knowledge must work against system design
- **Discrimination:** Non-empirical ways of knowing are invisible, not valid

### 3.4 Efficiency Over Diligence
- **Mechanism:** ~76s full build, incremental via content hashing; "optimized" developer experience
- **Impact:** Learning requires "unsexy" repetition that efficiency-oriented design may undermine
- **Discrimination:** Users valuing diligent, repeated practice may feel the system rushes past mastery

## 4. Recommendations Summary

### 4.1 Make Implicit Explicit
Add metadata fields to make philosophical commitments visible and configurable:
- `epistemic_status`: "empirically_verified" | "theoretical" | "contemplative" | "authority_based"
- `verification_level`: "test_suite_passed" | "peer_review" | "author_consensus" | "community_vetted"
- `way_of_knowing`: "empirical" | "contemplative" | "authority" | "experiential"
- `philosophical_lineage`: lineage thinker → concept → technique mapping

### 4.2 Build Parallel Validation Tracks
Replace single validation gate with multiple, weighted tracks:
- `pydantic_schema` validation (existing)
- `python_tests` suite (existing)
- `empirical_fidelity` scoring (new)
- `coherence_score` calculation (new)
- `philosophical_consistency` check (new)
- Configuration per pillar in `config.py`

### 4.3 Enable Multiple Ways of Knowing
Add `way_of_knowing` tag to each content item, display all tags in ontology browser, support filtering without exclusion.

### 4.4 Hold Tensions, Don't Resolve
The 7 identified conflicts should be held as productive tensions through:
- User-configurable philosophical profiles
- Multiple validation tracks with adjustable weights
- Explicit labeling, not architectural coercion

## 5. Audit Recommendations for Implementation

### Priority 1: Epistemological Metadata (Phase 2.1)
Add to `schemas.py` → `ContentItem`:
- `epistemic_status` (optional, default "empirically_verified")
- `verification_level` (optional, default "test_suite_passed")
- `way_of_knowing` (optional, default "empirical")

### Priority 2: Pluralistic Validation (Phase 2.2)
Build in `core/validation/`:
- Multiple validation track calculation
- Per-pillar weight configuration in `config.py`
- Display of all track scores alongside content

### Priority 3: Ways of Knowing Browser (Phase 3.1)
- Add `way_of_knowing` to ontology concept display
- Search filter by way_of_knowing (filter, don't exclude)
- Admin interface for editing way_of_knowing per item

### Priority 4: Philosophy Versioning (Phase 4.3)
- `philosophy_version` field in `config.py`
- Change log system
- Rollback capability

## 6. Non-Goals (What This Audit Does NOT Recommend)
- Removing empirical verification (it remains a valid track, just not the only one)
- Removing Bloom hierarchy (it remains available, alongside other progression models)
- Removing ontology (it remains the core structure, with alternative taggings added)
- Philosophical relativism (the system still validates, just through multiple frameworks)

## Appendix: Mapping Table - Code → Philosophy

| Code Artifact | Western Commitment | Eastern Commitment | Currently Encodes |
|--------------|-------------------|-------------------|------------------|
| `schemas.py` ContentItem | Empiricism as default | No alternative | `source_verified: bool`, `sqi: float` |
| `core/ontology.py` | Systems graph as truth | Emptiness as ground | 199 concepts, 447 relations |
| `core/retention_engine.py` | Memory as perishable | Memory as practice (SM-2) | SM-2 algorithm, gap detection |
| `build.py` | Static site = truth | Illusion of form | ~2,505 pages, no runtime |
| `seed_learn.py` | Hierarchical progression | Non-dual direct access | Prerequisite DAG, learning paths |
| `SQI_THRESHOLD_MIN = 0.65` | Verification gate | Acceptance of uncertainty | Quality gate, badge colors |
| `PILLAR_URL_MAP` | Structured navigation | Natural information flow | `{"aml": "compliance", "stock": "markets", "data-engineering": "data"}` |