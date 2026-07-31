# AcaciaFund — Live Site Content Assessment

> **Status: Historical record** — this audit documents the 2026-07-08 production outage where ~97 blog posts returned 404.
> **Resolution:** The issues described here were resolved by the URL Structure v3.0 refactor (2026-07-10) and subsequent rebuilds. As of 2026-07-30 the site generates **2,505 pages with 0 broken internal links** and the sitemap reflects correct knowledge paths. Retained for reference and root-cause analysis.

**Date:** 2026-07-08  
**URL:** https://www.acaciafund.org/

---

## 1. Executive Summary

| Metric | Value |
|--------|-------|
| Sitemap URL count | 272 |
| Live 200 OK | 159 (58%) |
| Live 404 | 113 (42%) |
| Local registry items | 161 |
| Local build `dist/` pages | ~190 |
| Learn/knowledge deployment health | Good (100% of correct-path URLs serve 200) |
| Blog deployment health | Critical failure (97 of 99 blog posts 404) |

**P0 Issues:**
1. ~97 blog posts (98% of research content) are 404 on the live site
2. Sitemap lists 13 knowledge items at wrong URL paths

---

## 2. Live Site Audit Results

### 2.1 Pages that work (200 OK) — 159 total

| Category | Count | Notes |
|----------|-------|-------|
| `tags/*` | 108 | Tag archive pages — all working |
| `learn/*` | 30 | Learning modules — all working |
| `knowledge/*` | 13 | Knowledge base — 13 core pages working |
| `blog/*` | 2 | Only 2 blog posts survived |
| `/` | 1 | Homepage |
| `research/`, `search/` | 2 | Index/search pages |
| `aml/`, `stock/`, `data-engineering/` | 3 | Pillar section pages |

### 2.2 Pages that 404 — 113 total

| Category | Count | Notes |
|----------|-------|-------|
| `blog/*` | 97 | **All except 2** research articles — 404 |
| Top-level knowledge paths | 13 | Sitemap lists `/slug/` instead of `/knowledge/slug/` |
| `data/`, `market/` | 2 | Pillar redirect pages (maybe old URLs) |
| `docs/*` | 1 | `cybernetic-foundations` — not deployed |

### 2.3 Sitemap URL Inconsistencies

The sitemap incorrectly lists 13 knowledge items at top-level URLs. They actually live at correct paths:

| Sitemap URL (broken) | Actual URL (works) |
|---------------------|-------------------|
| `/aml-core-foundations/` | `/knowledge/aml-core-foundations/` |
| `/market-core-foundations/` | `/knowledge/market-core-foundations/` |
| `/data-core-foundations/` | `/knowledge/data-core-foundations/` |
| `/cybernetic-manifesto/` | `/knowledge/cybernetic-manifesto/` |
| `/temporal-graph-aml/` | `/knowledge/temporal-graph-aml/` |
| etc. (13 total) | etc. |

This is a **sitemap generation bug** — knowledge content items without `knowledge/` prefix in their slug break the URL mapping.

---

## 3. Registry vs. Live Content Cross-Reference

### 3.1 Learn Content — HEALTHY

- **Registry:** 29 items
- **Local dist:** 28 directories (missing `learn` meta-page index, which has a different path)
- **Live (correct path):** 29 items — **all present**
- **Coverage:** 100%

### 3.2 Knowledge Content — PARTIALLY HEALTHY

- **Registry:** 26 items
- **Local dist:** 26 directories — **all built locally**
- **Live (correct path):** 26 items — **all present** (verified via curl)
- **Sitemap listing:** Only 13 listed correctly; 13 listed at wrong paths
- **Coverage:** 100% at correct paths, but sitemap is misleading

### 3.3 Research (Blog) Content — CRITICAL FAILURE

- **Registry:** 106 items (slugs starting with `blog/...`)
- **Local dist/blog/:** **0 directories** — blog posts not built
- **Live (correct path):** **2 items** survive from prior deploy
- **Coverage:** ~2% (2/106)
- **Sitemap:** Lists 99 blog URLs, 97 of which return 404

---

## 4. Root Cause Analysis

### Build Output Misconfiguration

The `.build_cache.json` contains output paths at `/root/dist/...` but the current build outputs to `/root/acaciafund/dist/...`. This indicates:

1. **The project root moved** — at some point the codebase was relocated from `/root/` to `/root/acaciafund/`
2. **The stale cache prevents rebuild** — the incremental build system reads the old cache, sees content hashes haven't changed, and **skips** blog post generation, assuming output files already exist at the **old** paths
3. **The old output was deleted** — `dist/blog/` is empty because the old output was cleaned up

The learn and knowledge items may have been regenerated because their content changed more recently, triggering a rebuild, while the older blog posts (dating back to Jan-Jun 2026) haven't changed and are skipped.

### Specific mechanism:

In `build.py` line 1889:
```python
if not cache.needs_rebuild(output_path, current_hash, is_content=True):
    items_to_skip.add(slug)
```

If `output_path` (`/root/acaciafund/dist/blog/.../index.html`) doesn't exist (was never generated there), `needs_rebuild` returns `False` because the cache has an entry for `current_hash` (from a prior build at old path). The item gets **skipped** but the output file is **never created**.

Wait — actually, `needs_rebuild` checks if the `output_path` EXISTS on disk. If it doesn't exist, it should return True. Let me verify this is actually the logic...

Actually, looking at the `core/build_cache.py` module, the `needs_rebuild` method checks:
1. If output_path doesn't exist → needs rebuild (True)
2. If hash changed → needs rebuild (True)  
3. Otherwise → needs_rebuild = False

So if `dist/blog/` doesn't exist AND the cache has a matching hash, it should ALWAYS need rebuild. Unless the cache entry is for a completely different path.

The key insight: the cache paths are ABSOLUTE paths. So `/root/dist/blog/.../index.html` would be a different cache key than `/root/acaciafund/dist/blog/.../index.html`. The old cache entries would be ignored, and items would need rebuild.

BUT — the cache was recently regenerated. The `.build_cache.json` has `"generated_at": 1783066391.0654044` which is around July 3-4. At that time, the output was at `/root/level`. The July 8 build at 05:57 regenerated the cache. But the build-meta.json at `dist/build-meta.json` was generated at `2026-07-08T05:57:16`.

So the latest build (07:57 AM today) would have generated a new `.build_cache.json` with paths under `/root/acaciafund/dist/`. But the `.build_cache.json` I read earlier had paths under `/root/dist/`...

---

## Post-Refactor Status (2026-07-10)

### URL Structure v3.0

The site now uses a **pillar-first** URL hierarchy:

| Pillar | URL Segment | Pages |
|--------|------------|-------|
| Compliance (AML) | `/compliance/` | 60+ (research, learn, knowledge) |
| Markets (Stock) | `/markets/` | 40+ |
| Data Engineering | `/data/` | 50+ |

Platform knowledge pages remain at `/knowledge/{page}`.

### Build Metrics

| Metric | Value |
|--------|-------|
| Total pages generated | 338 |
| Build time | ~11s |
| Registry items | 187 |
| Tag pages | 129 |
| Test coverage | 90 tests (URL, redirect, smoke) |

### Redirects

- `/aml/*` → `/compliance/:splat` (301)
- `/stock/*` → `/markets/:splat` (301)
- `/science/*` → `/research/:splat` (301)
- Meta-refresh redirect at `dist/aml/index.html`

### Key Fixes Applied

1. Extracted URL helpers to `core/urls.py` (dependency-free, testable)
2. Fixed 3 scripts that locally redefined `PILLAR_URL_MAP` — now import from `config.py`
3. Fixed AML signals dashboard output path (`dist/aml/signals/` → `dist/compliance/signals/`)
4. Added `slug_to_fspath()` for internal-key-to-URL-segment translation
5. Added comprehensive test suite (90 tests, <2s)

### Documentation

- `URL_STRUCTURE.md` — URL hierarchy reference with Mermaid diagram
- `AGENTS.md` — Development guide with commands, architecture, invariants