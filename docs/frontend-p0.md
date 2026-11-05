# Frontend P0 — Assessment and Decisions

> Scope: restore public frontend correctness only. SEO, performance, and
> accessibility are deferred. Admin is reported, not fixed, in P0.

## Verdict

The public frontend is feature-rich but not release-reliable. Three P0 issues
break major features on the live site:

1. The CSP blocks inline scripts and third-party CDN libraries.
2. The design-system CSS is syntactically invalid, its layer order is wrong, and
   vendor CSS/`@font-face` imports are ignored.
3. Several JS modules derive asset URLs from unhashed script names, so nested
   pages request missing assets.

## Evidence

### CSP vs. templates

- CSP is generated at `build.py:3760-3764` and served live with
  `script-src 'self'`.
- Inline theme bootstrap: `templates/layout.j2:21` (all pages).
- Graph loads Cytoscape from unpkg and runs inline init:
  `templates/graph.j2:84-88`.
- Pyodide/sql.js load from jsDelivr/unpkg:
  `static/js/pyodide_sandbox.js:6-8`, `static/js/sql_sandbox.js:50-53`.
- Review, review queue, study, citation copy, learning path, and console use
  inline scripts: `templates/review.j2:113`,
  `templates/review_queue.j2:44`, `templates/study.j2:71`,
  `templates/partials/citation_export.j2:58`,
  `templates/learning_path.j2:138`, `templates/console.j2:309`.
- Plausible is loaded from `https://plausible.io/js/script.js`
  (`config.py` `PLAUSIBLE_DOMAIN`).
- Cloudflare Pages injects `https://static.cloudflareinsights.com` at the edge;
  this is also currently blocked by `script-src 'self'`.

### CSS

- `static/css/design-system.css:7` opens `@layer components` before the
  `@import`s at lines 27/30. Browsers ignore `@import` after a rule block, so
  Pico CSS and `@font-face` are not applied.
- `.container` exists only in Pico; without it, pages lose max-width and
  horizontal padding.
- `:root` at line 95 closes at line 100; typography tokens at lines 101-110 are
  outside a rule and a stray `}` appears at line 111. `--text-*` is undefined.
- A second stray `}` appears at line 667; the stylesheet is not parseable as a
  whole.
- The layer order declaration at line 27 comes after the first `components`
  block, so `components` is ordered first instead of last.

### Hashed assets

- `static/js/review_badge.js:27`, `pillar_rail.js:77`, `diagnostic.js:81`,
  `study_dashboard.js:78`, and `adaptive.js:105` look for unhashed script names.
  The build emits `app.<hash>.js`, `pillar_rail.<hash>.js`, etc., so the prefix
  is empty and relative fetches 404 on nested pages.
- This breaks review badges, pillar-rail due counts, diagnostic questions,
  study-dashboard upcoming cards, and adaptive recommendations.

### Quiz payloads

- `core/build_content.py:370` serializes quiz data with `json.dumps`;
  `templates/learn.j2:112` injects it into a single-quoted `data-quiz='...'`.
  Apostrophes (for example “Snowflake's”) terminate the attribute. At least 30
  learn pages are affected.

### Stale descriptions / JSON-LD

These registry descriptions still carry claims corrected in the article bodies:

- `aml/research/aml-1`: 80% false-positive reduction at five major European banks.
- `aml/research/aml-3`: first year of FinCEN BOI reporting and enforcement actions.
- `aml/research/aml-4`: 7th AML Directive taking effect in 2026.
- `markets/research/science-5`: 15 independent laboratories.
- `markets/research/ai-regulation`: EU AI Act enters into force in 2026.
- `data/research/dagster-2`: Dagster 2.0.

Descriptions feed `<meta name="description">` and `_build_jsonld`
(`core/build_content.py:395`), so structured data is also stale.

### Admin exposure (report only)

`dist/admin/` is deployed. `https://www.acaciafund.org/admin/` returns 200 and
redirects to `login`; `https://www.acaciafund.org/admin/dashboard` also returns
200. No Cloudflare Access challenge was observed on the dashboard request.
Admin inline scripts remain broken under CSP; this is reported, not fixed in P0.

## Decisions

### CSP

Static host, no nonces.

- Externalize public inline JS.
- Keep the theme bootstrap inline and add its SHA-256 hash at build time in the
  CSP generator.
- Self-host Cytoscape and sql.js.
- Pyodide: path-scope
  `https://cdn.jsdelivr.net/pyodide/<version>/full/` in both `script-src` and
  `connect-src`. Pin the version in one constant shared by the CSP generator and
  the loader.
- Never allowlist unpkg or jsDelivr `/npm/` packages.
- `plausible.io` path-scoped:
  - `script-src https://plausible.io/js/`
  - `connect-src https://plausible.io/api/event`
- Allow Cloudflare's existing edge analytics beacon (or disable it in the
  Cloudflare dashboard):
  - `script-src https://static.cloudflareinsights.com`
  - `connect-src https://cloudflareinsights.com`
- Add `'wasm-unsafe-eval'` for sql.js and Pyodide.
- If Pyodide still requires eval, isolate sandbox pages with a path-specific
  CSP; do not loosen the site-wide policy.
- Add `worker-src 'self' blob:` if Playwright shows Pyodide workers require it.
- `connect-src` adds a Railway/API origin only if a frontend caller exists.
  None has been found in templates or JS.

### CSS build

- Do not reorder runtime `@import`s only.
- Add a Python CSS inliner/linter. It must:
  - verify balanced braces and `@import` before all rules;
  - wrap `layer(x)` imports in `@layer x { ... }` so vendor CSS does not beat
    every layered rule;
  - rewrite relative `url()`s to `/static/...` for the new build directory;
  - emit the bundled CSS to a build directory consumed by the asset pipeline.
- Fix source CSS before bundling: token block, stray braces, layer order, and
  the early `components` block.
- Capture side-by-side PNGs at 390px and 1280px for ten templates before and
  after the CSS change.

### Playwright

- Python `pytest-playwright`, Chromium only.
- Markers: `e2e` (off by default) and `slow`.
- Gate test fails on:
  - CSP console violations;
  - `pageerror`;
  - same-origin 4xx/5xx responses.
- Known 404 allowlist, each tagged with the P1 item that removes it:
  - `/favicon.ico` — P1 favicon;
  - `_400w`/`_800w` image variants — P1 responsive images.
- `BASE_URL` environment variable so the same spec runs against production.
- Pyodide sandbox is a separate `@slow` spec, non-blocking (third-party CDN and
  ~10 MB download). sql.js remains in the gate.
- Commit 2 adds the gate with `continue-on-error: true`; the final P0 commit
  makes it blocking.

### Commit order

1. `docs: add frontend P0 assessment and CSP decisions`
2. `test: add Playwright frontend CSP smoke gate` (non-blocking)
3. `fix: bundle CSS and repair cascade/token syntax`
4. `fix: correct CSP, asset base, and review badge fetch`
5. `fix: make quiz payloads JSON-safe`
6. `fix: refresh stale descriptions and enable frontend gate`

## Deferred (must not be lost)

- **SEO:** ~~fix `page_path` to use `slug_to_fspath` before emitting canonical/OG
  tags; add a build assertion that every canonical URL resolves in `dist/`;
  Open Graph/Twitter tags; thin-tag `noindex`~~ — **done 2026-11-05**
  (`scripts/deploy_checks.py` enforces canonical coverage/resolution).
  Remaining: sitemap coverage audit and per-page description length.
- **Feed:** ~~sort by date~~ — **done 2026-11-05** (newest first, feed
  `updated` reflects newest entry).
- **Favicon/manifest:** ~~`/favicon.ico` 404s; no manifest/theme-color~~ —
  **done 2026-11-05** (generated multi-size ICO, SVG icon, web manifest,
  theme-color).
- **Performance:** review badge still fetches 410 KB + 104 KB for returning
  users; ship a due-count manifest next. Workspace page is 3.3 MB; scholar 671
  KB; review/study ~290 KB.
- **Responsive images:** ~~remove `srcset` for SVGs and stop emitting variants
  that do not exist~~ — **done 2026-11-05** (`responsive_srcset` only emits
  URLs when both raster variants exist; e2e allowlist is empty). Existing
  raster images serve the original until re-fetched with variants.
- **Accessibility:** ~~label newsletter/teachback/build inputs; add
  `aria-current`/`aria-modal`; graph fallback; fix multi-h1 pages~~ —
  **done 2026-11-05**. Remaining: light-mode pillar-accent contrast and a
  visible focus-mode exit.
- **Admin:** externalize/hash admin inline scripts and confirm Access in front
  of `dist/admin/`.
- **Tests later:** Lighthouse/axe/visual regression and HTML validation arrive
  with Node in Phase 4.

## Acceptance criteria

- Playwright P0 smoke: no CSP violations, no console errors, no same-origin
  404s outside the tagged allowlist.
- CSS inliner/linter passes; bundled CSS contains no unresolved `@import` and
  parses as balanced.
- Theme CSP hash matches the inline bootstrap.
- Graph, review, study, diagnostic, quiz, and sql.js sandbox work under CSP.
- Pyodide smoke is either green or documented as the isolated slow spec.
- Build succeeds with 0 errors; Python and JS tests pass.
- The six corrected descriptions exactly match sentences in the corrected
  bodies, quoted in the commit message.

## Implementation status (2026-11-03, updated 2026-11-05)

P0 changes plus the SEO/feed/favicon follow-ups are implemented on `main`. The Playwright smoke gate is blocking in
`deploy.yml`; the local proot/ARM environment cannot launch Chromium (SIGTRAP),
so screenshots must be produced by CI or a supported Chromium host:
`python scripts/capture_frontend_screens.py --out /tmp/frontend-p0-screens/after`
(use `--base-url https://www.acaciafund.org` for a production capture).
