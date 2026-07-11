# AGENTS.md — AcaciaFund Development Guide

## Quick Commands

```bash
# Build (full rebuild, clears cache)
rm -rf dist .build_cache.json && python3 build.py

# Build (incremental, uses cache)
python3 build.py

# Tests
python3 -m pytest tests/ -v

# Lint
ruff check .

# Type check
pyright

# Migration (dry-run)
python3 scripts/migrate_slugs.py

# Migration (apply)
python3 scripts/migrate_slugs.py --apply

# Migration (check only)
python3 scripts/migrate_slugs.py --check
```

## Architecture

### Pillar System

Three pillars, each with a URL segment:

| Internal Key | URL Segment | Label |
|---|---|---|
| `aml` | `compliance` | Compliance |
| `stock` | `markets` | Markets |
| `data-engineering` | `data` | Data Engineering |

**Single source of truth:** `config.py` → `PILLAR_URL_MAP`

### URL Hierarchy

```
/{pillar_url}/research/{topic}
/{pillar_url}/learn/{topic}
/{pillar_url}/knowledge/{topic}
/knowledge/{platform-page}   (cross-pillar)
```

### Key Files

| File | Purpose |
|---|---|
| `config.py` | `PILLAR_URL_MAP`, `PILLAR_URL_REVERSE`, site config |
| `build.py` | Main build script — imports from `core/urls.py` |
| `core/urls.py` | Pure URL helpers (lightweight, testable) |
| `core/build_cache.py` | Incremental build cache |
| `schemas.py` | Pydantic models for registry validation |
| `registry.json` | Content registry (187 items) |
| `scripts/migrate_slugs.py` | Slug migration tool |

## Invariants

1. **Never redefine `PILLAR_URL_MAP` locally.** Always `from config import PILLAR_URL_MAP`. Scripts that redefine it create divergence with the build.

2. **Slugs in `registry.json` use internal keys.** The build translates them via `slug_to_fspath()` in `core/urls.py`.

3. **`core/urls.py` has no heavy dependencies.** It only imports from `config.py`. This makes it safe for tests to import without triggering pandas/jinja2/PIL.

4. **Platform knowledge pages stay at `/knowledge/`.** Only domain-specific knowledge gets pillar prefixes.

5. **URL_STRUCTURE_VERSION in `config.py` must be bumped** when slug structure changes (forces full cache rebuild).

## Troubleshooting

### Build skips all items (incremental build not picking up changes)
- Check `.build_cache.json` — if version doesn't match, cache auto-clears
- Delete `.build_cache.json` and rebuild: `rm -rf dist .build_cache.json && python3 build.py`

### Tests timeout importing `build.py`
- `build.py` imports pandas/jinja2/PIL. Tests should import from `core/urls.py` instead.
- Use `python3` (not `python`) — the Termux `python` may lack dependencies.

### Stale `/aml/` paths in output
- Check that `scripts/migrate_slugs.py`, `scripts/generate_content.py`, and `scripts/knowledge_ingester.py` import from `config` (not local redefinition).
- Rebuild after fixing: `rm -rf dist .build_cache.json && python3 build.py`

### Slug collisions
- Run `python3 scripts/migrate_slugs.py --check` to validate
- The migration script auto-resolves collisions with numeric suffixes
