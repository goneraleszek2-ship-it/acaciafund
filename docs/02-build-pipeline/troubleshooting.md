# Troubleshooting

Common build issues and their solutions.

## Build Issues

### Build skips all items (incremental build not picking up changes)

**Cause:** Stale build cache with mismatched content hashes or output paths.

**Fix:**
```bash
rm -rf dist .build_cache.json && python3 build.py
```

### Build hangs or times out

**Cause:** Heavy imports (pandas, PIL, Jinja2) on slow systems, or external API calls.

**Fix:**
```bash
timeout 300 python3 build.py
```

### Tests timeout importing `build.py`

**Cause:** Tests import `build.py` which triggers pandas/jinja2/PIL imports.

**Fix:** Import from `core/urls.py` or `core/ontology.py` instead — these have no heavy dependencies. Use `python3` (not `python`).

```bash
timeout 300 python3 -m pytest tests/ -v --timeout=60
```

### "No module named 'services.mem0'" error

**Cause:** The `services/mem0/` package does not exist. It's a planned module that was never created.

**Fix:** Not a build blocker — `build.py` wraps this in try/except (line 99-104). Standalone scripts will crash.

## Output Issues

### Stale `/aml/` or `/stock/` paths in output

**Cause:** Scripts redefining `PILLAR_URL_MAP` locally instead of importing from `config.py`.

**Fix:** Check that these scripts import from `config` (not local redefinition):
- `scripts/migrate_slugs.py`
- `scripts/generate_content.py`
- `scripts/knowledge_ingester.py`

Rebuild after fixing:
```bash
rm -rf dist .build_cache.json && python3 build.py
```

### Slug collisions

**Cause:** Duplicate slugs in `registry.json` or slug migration conflicts.

**Fix:**
```bash
python3 scripts/migrate_slugs.py --check
python3 scripts/migrate_slugs.py --apply
```

### Search index is empty

**Cause:** `dist/static/search-index.json` not generated.

**Fix:**
1. Full rebuild: `rm -rf dist .build_cache.json && python3 build.py`
2. Check `dist/build-meta.json` for `search_index_entries` count
3. Check `generate_search_pages()` in `core/build_taxonomies.py`

### Admin pages not rendering

**Cause:** Admin template not extending `admin/base.html`.

**Fix:** All admin templates MUST extend `admin/base.html` (not `layout.j2` directly). Admin context requires `active_page` variable.

### Source freshness data missing

**Cause:** `data/source_health.json` doesn't exist or is outdated.

**Fix:**
```bash
python3 scripts/check_source_freshness.py --update-ontology
```

### Concept extraction too strict or too loose

**Cause:** Threshold mismatch between `build.py` and `extract_concepts_from_text()`.

**Fix:** `build.py` uses `>= 0.35` for concept cache; `extract_concepts_from_text()` default is `>= 0.5`. Adjust these thresholds.

### Build errors in logs

Check `dist/build_errors.log`:
- 0 bytes = clean build
- Non-empty = check for Jinja2 template errors, missing registry fields, or import failures

## Incremental Build Cache

| Symptom | Cause | Fix |
|---------|-------|-----|
| Items skipped but not in output | Cache paths from old project root | Delete `.build_cache.json` |
| All items rebuild every time | `URL_STRUCTURE_VERSION` mismatch | Check `config.py:URL_STRUCTURE_VERSION` |
| Partial output | Cache thinks items are current | Full rebuild |

## Known Issues

| Issue | Status | Workaround |
|-------|--------|------------|
| `services/mem0/` doesn't exist | Won't fix (planned) | Build wraps in try/except |
| `scripts/execute_fixes.py` broken import | Known bug | Run from within `scripts/` |
| `fetch_images.py` references `"science"` pillar | Cosmetic | No functional impact |
| `build.py` duplicates pillar config (lines 205-244) | Tech debt | Update both `build.py` and `config.py` |

> **See also:** [Build Overview](build-overview.md), [Incremental Build](incremental-build.md)
