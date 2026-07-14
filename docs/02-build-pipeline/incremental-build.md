# Incremental Build System

The incremental build system (`core/build_cache.py`) avoids re-rendering unchanged content by hashing each item and tracking output file existence.

## How It Works

1. **Content hashing:** Each item's slug + title + body_html + tags + category is hashed (SHA-256)
2. **Cache storage:** `.build_cache.json` maps `slug → hash + output_path + timestamp + version`
3. **Cache check:** `needs_rebuild(output_path, current_hash)` returns `False` if:
   - Output file exists on disk
   - Hash matches cached value
   - Version matches `URL_STRUCTURE_VERSION`
4. **Cache update:** After a successful build, the cache is updated with the new hash

## Cache File Format

```json
{
  "version": "3.0",
  "generated_at": 1783066391.065,
  "items": {
    "aml/research/suspicious-transaction-reporting": {
      "hash": "a1b2c3d4...",
      "output_path": "/root/acaciafund/dist/compliance/research/suspicious-transaction-reporting/index.html",
      "built_at": 1783066391.065,
      "version": "3.0"
    }
  }
}
```

## Force Full Rebuild

Bump `URL_STRUCTURE_VERSION` in `config.py` to invalidate all cache entries:

```python
URL_STRUCTURE_VERSION = "3.0"  # Bump to "3.1" for full rebuild
```

Or delete the cache file:

```bash
rm -rf dist .build_cache.json && python3 build.py
```

## Parallel Processing

The build uses `parallel_map` from `core/build_cache.py` to process items concurrently:

```python
from core.build_cache import get_worker_pool, parallel_map

pool = get_worker_pool(max_workers=4)
results = parallel_map(pool, process_func, items)
```

- Default: 4 workers (configurable via `MAX_WORKERS` in `core/build_cache.py`)
- Each worker processes one content item through the full render pipeline
- Shared cache, thread-safe reads/writes

## Cache Invalidation Triggers

| Change | Cache Behavior |
|--------|---------------|
| Content change (hash mismatch) | Single item rebuilt |
| `URL_STRUCTURE_VERSION` bumped | All items rebuilt |
| Cache file deleted | All items rebuilt |
| Output file deleted | Single item rebuilt |
| Template change | All items rebuilt (template hash mismatch) |

## Skipped Items

Items that pass the cache check are added to `items_to_skip` and not re-rendered. This typically reduces build time by 60-80% on subsequent builds.

> **See also:** [Build Overview](build-overview.md), [Troubleshooting](troubleshooting.md)
