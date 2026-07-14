# CLI Commands Reference

All command-line scripts available in the project.

## Build Commands

```bash
# Build (incremental)
python3 build.py

# Build (full rebuild, no cache)
rm -rf dist .build_cache.json && python3 build.py
```

## Test Commands

```bash
# All tests
python3 -m pytest tests/ -v

# Specific test file
python3 -m pytest tests/test_ontology.py -v

# Specific test
python3 -m pytest tests/test_urls.py::test_pillar_to_url -v

# With timeout (prevents hanging)
timeout 300 python3 -m pytest tests/ -v --timeout=60
```

## Lint & Type Check

```bash
# Lint
ruff check .

# Type check
pyright
```

## Scripts

| Command | Description |
|---------|-------------|
| `python3 scripts/backfill_sqi.py` | Recompute SQI for items missing quality scores |
| `python3 scripts/build_knowledge_graph.py` | Generate knowledge graph data |
| `python3 scripts/check_links_and_sqi.py --dist-dir dist` | Check broken links + SQI audit |
| `python3 scripts/check_source_freshness.py` | HTTP HEAD check all 32 sources |
| `python3 scripts/check_source_freshness.py --update-ontology` | Check sources + update ontology |
| `python3 scripts/content_audit.py` | Content quality and coverage audit |
| `python3 scripts/deploy_cloudflare.py` | Trigger Cloudflare Pages deploy |
| `python3 scripts/enrich.py` | Content enrichment pipeline |
| `python3 scripts/execute_fixes.py` | Execute auto-fixes (experimental) |
| `python3 scripts/export_graph.py` | Export graph data to file |
| `python3 scripts/fetch_images.py` | Fetch Unsplash images for content |
| `python3 scripts/generate_content.py` | Generate content from templates |
| `python3 scripts/generate_glossaries.py` | Generate per-pillar glossary pages from ontology |
| `python3 scripts/generate_learn_modules.py` | Generate learn modules with Bloom Qs + flashcards |
| `python3 scripts/generate_mermaid_svgs_v3.py` | Generate Mermaid diagram SVGs |
| `python3 scripts/knowledge_ingester.py` | Ingest content from arXiv, HN, PubMed |
| `python3 scripts/migrate_slugs.py` | Dry-run slug migration |
| `python3 scripts/migrate_slugs.py --apply` | Apply slug migration |
| `python3 scripts/migrate_slugs.py --check` | Check for slug collisions |
| `python3 scripts/source_synthesis.py` | Source synthesis with inspiration matching |
| `python3 scripts/source_verification.py` | Source verification with domain recognition |
| `python3 scripts/test_agent_arena.py` | Test agent arena (experimental) |
| `python3 scripts/trend_detection.py` | Trend detection analysis |

## Shell Scripts

| Command | Description |
|---------|-------------|
| `bash scripts/daily_summary.sh` | Daily build and health summary |
| `bash scripts/run_ingestion_with_validation.sh` | Ingestion with validation pipeline |

## Ontology Management

```bash
# Seed and save ontology
python3 -c "
from core.ontology import OntologyManager
m = OntologyManager()
m.seed_all_pillars()
m.seed_relations()
m.save('data/ontology.json')
"

# Validate concept extraction
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
