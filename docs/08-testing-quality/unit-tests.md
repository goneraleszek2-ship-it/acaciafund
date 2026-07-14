# Unit Tests

Unit tests cover core modules with no heavy dependencies on pandas/Jinja2/PIL.

## Ontology Tests (`test_ontology.py` — 39 tests)

| Test Group | Description |
|------------|-------------|
| Concept model | Creation, serialization, field validation |
| Relation model | Directed relations, strength, type |
| ResourceLink model | URL status tracking |
| InspirationSource model | Source metadata |
| OntologyManager | Add/get/resolve/query concepts and relations |
| Concept extraction | Exact/alias/partial matches, thresholds |
| Seeding | `seed_pillar()`, `seed_all_pillars()`, `seed_relations()` |
| Persistence | `save()` / `load()` roundtrip |
| Cytoscape export | `to_cytograph_nodes()`, `to_cytograph_edges()` |

## URL Tests (`test_urls.py` — 18 tests)

| Test Group | Description |
|------------|-------------|
| `pillar_to_url()` | Internal key → URL segment |
| `url_to_pillar()` | URL segment → internal key |
| `slug_to_fspath()` | Internal slug → filesystem path |
| `slug_to_url()` | Internal slug → canonical URL |
| `canonical_path()` | Path normalization |
| `slug_to_path()` | Slug → output file path |
| Edge cases | Empty slugs, missing pillars, URL-unsafe chars |

## Build Cache Tests (`test_build_cache.py` — 18 tests)

| Test Group | Description |
|------------|-------------|
| `BuildCache.needs_rebuild()` | File existence, hash change, version change |
| `BuildCache.update()` | Hash storage, timestamp recording |
| `BuildCache.save()` / `load()` | Persistence roundtrip |
| `parallel_map()` | Worker pool, result collection |
| Cache invalidation | Version bump, file deletion |

## Running Specific Tests

```bash
# Run ontology tests only
python3 -m pytest tests/test_ontology.py -v --tb=short

# Run a specific test
python3 -m pytest tests/test_urls.py::test_pillar_to_url -v

# Run tests matching a keyword
python3 -m pytest tests/ -k "ontology"
```

> **See also:** [Test Overview](test-overview.md), [Taxonomy Tests](taxonomy-tests.md)
