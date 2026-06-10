# AcaciaFund — Site State & Feature Inventory

> **Last updated:** 2026-06-08  
> **Deployed URL:** https://www.acaciafund.org  
> **Repo:** https://github.com/goneraleszek2-ship-it/acaciafund  
> **Build:** `python3.13 build.py`  
> **Build output:** 326 HTML pages + fractal thumbnails + OG images + search index + Atom feed  
> **Host:** Cloudflare Pages (static)

---

## 1. Architecture

| Layer | Technology | Notes |
|-------|-----------|-------|
| Data source | `registry.json` | Pydantic-validated, single source of truth |
| Template engine | Jinja2 | 11 templates: `layout.j2`, `blog_post.j2`, `pillar_index.j2`, `index.j2`, `category_index.j2`, `learn.j2`, `learn_index.j2`, `knowledge.j2`, `knowledge_index.j2`, `search.j2`, `404.j2` |
| Markdown rendering | `markdown2` | With `fenced-code-blocks` and `tables` extras |
| CSS framework | Tailwind 3.4.19 (28KB local) | No CDN — self-hosted `tailwind.min.css` |
| Custom styles | `static/css/custom.css` | ~360 lines — font-face, CSS variables, dark mode, TOC, dropdown, mobile drawer (fixed), flashcard flip (3D), accordion, print styles |
| Fonts | Inter (self-hosted) | Regular, SemiBold, Bold WOFF2 (~340KB total) |
| Client JS | Inline `<script>` in templates + `static/js/search.js` | Quiz engine (score/grade/retry), flashcard shuffle, progress tracking, spaced repetition, dark mode toggle, dropdown, mobile nav, reading progress bar, TOC highlighting, focus mode (persisted), search, Surprise Me |
| Output | `dist/` (60+ HTML pages) | Cleaned and rebuilt on each generator run |

### Pipeline

```
registry.json → build.py → Jinja2 templates → dist/*.html
```

No build framework (no Astro, no Hugo). The output is ready-to-serve static HTML.

---

## 2. Pages

| Page | Route | Template | Content Source |
|------|-------|----------|----------------|
| Home | `/` | `index.j2` | Featured + latest research + learn + knowledge cards |
| Research article (×56) | `/YYYY-MM-DD-slug/` | `blog_post.j2` | `registry.json` |
| Learn lesson (×16) | `/learn/slug/` | `learn.j2` | `registry.json` |
| Learn index | `/learn/` | `learn_index.j2` | All lessons, difficulty-grouped, pillar progress bars, due-for-review |
| Knowledge article (×12) | `/knowledge/slug/` | `knowledge.j2` | `registry.json` |
| Knowledge index | `/knowledge/` | `knowledge_index.j2` | All references, sub-category grouped |
| Research index | `/research/` | `category_index.j2` | All research articles |
| AML pillar | `/aml/` | `pillar_index.j2` | Filtered entries (14 articles) |
| Markets pillar | `/stock/` | `pillar_index.j2` | Filtered entries (17 articles) |
| Data Engineering pillar | `/data-engineering/` | `pillar_index.j2` | Filtered entries (32 articles) |
| Science redirect | `/science/` → `/research/` | (meta-refresh) | Cached-visitor redirect |
| Search | `/search/` | `search.j2` | Vanilla JS fuzzy search |
| 404 | `/404.html` | `404.j2` | Deterministic suggestions |
| Feed | `/feed.xml` | — | Atom feed, last 20 published posts |
| Sitemap | `/sitemap.xml` | — | All pages |
| Robots | `/robots.txt` | — | Allow all, sitemap link |

**Total: 326 HTML pages** (56 research + 16 learn + 12 knowledge + 5 indices + 1 search + 1 404 + 1 home + 230 tag archives + 3 pillar pages + 1 redirect)

---

## 3. Visual Design

### Color System (CSS Custom Properties)

All colors live in `:root` CSS variables in `custom.css`, overridden by `.dark` class.

#### Light Mode
| Token | Value | Usage |
|-------|-------|-------|
| `--color-bg` | `#f5f0eb` | Page background (warm cream) |
| `--color-surface` | `#faf7f2` | Cards, dropdowns, nav |
| `--color-surface-hover` | `#f5f0e8` | Card hover state |
| `--color-border` | `#e5ddd4` | Borders, dividers |
| `--color-text` | `#1a1a2e` | Body text (deep navy) |
| `--color-text-secondary` | `#8b7e74` | Secondary text |
| `--color-text-muted` | `#a09488` | Muted text |
| `--color-accent` | `#1d4ed8` | Links, focus indicators |
| `--color-header-bg` | `rgba(250,247,242,0.9)` | Sticky header backdrop |
| `--color-aml` | `#c97d3e` | AML pillar accent |
| `--color-markets` | `#3a7d5c` | Markets pillar accent |
| `--color-data-engineering` | `#6366f1` | Data Engineering pillar accent |

#### Dark Mode (`.dark` class)
| Token | Value |
|-------|-------|
| `--color-bg` | `#1a1a2e` (deep navy) |
| `--color-surface` | `#1f1f36` |
| `--color-text` | `#e8e6e3` (warm off-white) |
| `--color-accent` | `#60a5fa` (blue) |

### Typography
- **Body:** Inter Regular 400, system-ui fallback
- **Headings:** Inter SemiBold 600 / Bold 700
- **Monospace:** System `ui-monospace` stack
- **Line height:** 1.6 body, 1.3 headings
- **Max article width:** 65ch (focus mode) / default prose

### Dark Mode
- FOUC-prevention: Inline `<script>` in `<head>` reads `localStorage.theme` before first paint
- Persistence: `localStorage` (`'dark'` or `'light'`); absent respects `prefers-color-scheme`
- Toggle: Moon/sun SVG button in nav bar
- Meta tags: Dual `theme-color` via `media="(prefers-color-scheme: ...)"`

---

## 4. Navigation & Accessibility

### Desktop Nav
- Sticky header with `backdrop-blur`
- Blog dropdown button with `aria-haspopup="true"`, `aria-expanded`, `role="menu"`, `role="menuitem"`
- JS toggle: click to open, click-outside to close, Escape to dismiss
- Keyboard support: `:focus-visible` rings on all interactive elements

### Mobile Nav (<640px)
- Hamburger button with `aria-expanded`
- Fixed full-viewport drawer (`position: fixed; top: 3.5rem; bottom: 0`) — never overlaps hero/headings
- Box-shadow backdrop (`0 0 0 9999px rgba(0,0,0,0.3)`)
- `slideDown` animation with `prefers-reduced-motion` respect
- Auto-closes on link click
- `aria-label="Toggle navigation menu"`

### Accessibility Features
- Skip-to-content link (first element after `<body>`, visible on focus)
- `lang="en"` on `<html>`
- ARIA labels on nav, breadcrumbs, dark toggle, mobile toggle, focus toggle
- Breadcrumbs with `aria-label="Breadcrumb"` and `aria-current="page"`
- `prefers-reduced-motion` disables all animations
- Proper heading hierarchy (H1 → H2 → H3)
- All images have `alt` text or `loading="lazy"`

### Footer
- Copyright + "Content synthesized by AcaciaFund NLP pipelines" disclosure
- Footer nav: About, Contact, Research, RSS
- `nav aria-label="Footer navigation"`

---

## 5. Post Features (blog_post.j2)

### Per-Post Elements (Research)
- Fixed reading progress bar (3px, top of viewport, accent color)
- Breadcrumb: Home / Pillar / Post Title
- Pillar badge (colored, with emoji)
- SQI score (Signal Quality Index)
- Source breakdown (HN / arXiv / PubMed counts)
- Title, date with calendar SVG icon, reading time with clock SVG icon
- Tags as pills
- Quality metrics grid (Avg Source Score, Source Diversity, Recency) — when available
- Body content with auto-generated heading IDs and anchor links
- Bloom Taxonomy Questions section (with colored level badges)
- **Interactive flip flashcards** (CSS 3D flip: term on front, definition on back, tap to reveal)
- Zero-JS static chart grid (2×2 layout: donut, radar, heatmap, bloom/bars — WCAG AA contrast)
- Signal Analysis section (article count, total points, avg score, domains, entities)
- Related posts (top 3 by tag overlap, with pillar badges)
- Cross-type cross-references (related learn + related knowledge sections)
- Previous/Next post navigation

### TOC Sidebar
- Auto-generated from h2/h3 headings via `extract_headings()` in `build.py`
- Sticky on desktop (`lg:sticky lg:top-20`)
- Active heading highlighting on scroll (JS Intersection-like via scroll listener)
- Smooth scroll on click (via `id` anchors with `scroll-margin-top`)
- Scrollable container with thin scrollbar

### Focus Mode
- Toggle button in TOC sidebar header
- Hides TOC, centers article to `max-width: 65ch`
- JS class toggle on `<body>`: `.focus-mode`

### OG Images
- Per-post SVG generated via MD5 hash of title
- Fractal mist background + decorative ellipses + dynamic radial gradient
- Unique `og_{hash}.svg` per post (36 total)
- Rendered in `<meta property="og:image">`

---

## 6. Pillar Indices (pillar_index.j2)

- Breadcrumb: Home / Pillar / Heading
- Pillar badge with emoji, heading, description, post count
- Post list with:
  - Title (linked)
  - Description (line-clamped)
  - Date, reading time, SQI
  - Source breakdown (HN, arXiv)
  - Quality / Diversity scores

---

## 7. Homepage (index.j2)

- Hero heading + tagline
- CTA buttons: "Explore Research", "Read Blog"
- Latest posts grid (2-column, up to 8 posts)
  - Pillar badge, title, date, reading time, SQI
- Learning Hub section (up to 6 items) — hidden when no lessons
- Stack badges: Python 3.13, Pydantic, Jinja2, Markdown2, Tailwind CSS, Cloudflare Pages

---

## 8. Infrastructure

### Build
```bash
python3.13 build.py
```
Dependencies: `jinja2`, `markdown2`, `pydantic`

### Deployment
- Cloudflare Pages: auto-deploys from `main` branch
- Custom domain: `acaciafund.org` (www redirects from apex)
- Build command: `python3.13 build.py`
- Output directory: `dist/`

### HTTP Headers (`_headers`)
```
/* → X-Content-Type-Options, X-Frame-Options, Referrer-Policy, Permissions-Policy
/static/* → Cache-Control: public, max-age=31536000, immutable
/*.html → Cache-Control: public, max-age=3600
/feed.xml → cache + Content-Type: application/atom+xml
/sitemap.xml → Content-Type: application/xml
```

### Feeds & Discovery
- `feed.xml` (Atom, 20 most recent posts)
- `sitemap.xml` (all URLs)
- `robots.txt` (allow all)
- Canonical URLs on all pages
- JSON-LD structured data: BlogPosting, LearningResource, WebSite
- Open Graph tags (title, description, image, type, article:published_time)

---

## 9. Content

| Pillar | Research | Learn | Knowledge | Topics |
|--------|----------|-------|-----------|--------|
| AML | 14 | 5 | 2 | Financial crime, compliance, regulation, risk, crypto, DeFi |
| Markets | 17 | 6 | 4 | Semiconductors, AI industry, manufacturing, EV, quantum |
| Data Engineering | 32 | 6 | 6 | Orchestration, quality, streaming, lakehouse, analytics, data mesh |

Total: 84 entries (56 research + 16 learn + 12 knowledge)

All content is auto-synthesized from HackerNews + arXiv sources.
Science pillar discontinued (Jun 2026). `/science/` redirects to `/research/`.

---

## 10. DevOps

- Cloudflare Pages auto-deploys static site from `main`
- GitHub Actions (`deploy-api.yml`): deploys API service to Railway on push to `main` (when `services/api/**` or `railway.json` changes)
- Deployment via git push to `main`
- `deploy.sh` exists but superseded by auto-deploy

### API Service (FastAPI — Railway)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/ping` | GET | Connectivity test |
| `/info` | GET | Runtime info (debug, CORS origins) |
| `/progress` | POST | Save reading progress `{url, done, score, ts}` |
| `/progress?url=...` | GET | Retrieve reading progress for a URL |

**Stack:** Python 3.11, FastAPI, Uvicorn, SQLite  
**Database:** SQLite at `$ACACIA_DB_PATH` (persistent volume on Railway)  
**Config:** All settings via env vars (`ACACIA_DB_PATH`, `ACACIA_CORS_ORIGINS`, `ACACIA_DEBUG`)  
**Auth:** None (public endpoints; progress tracking is anonymous)  
**CORS:** Configured for `acaciafund.org` + localhost development

---

## 11. Known Gaps & Next Steps

### Planned
- [ ] Bookmarks / "continue reading" (localStorage)
- [ ] Reading streaks + progress rings
- [ ] Citation popover on hover
- [ ] Inline retrieval prompts after sections
- [ ] Social share buttons
- [ ] Fluid typography with `clamp()`
- [ ] Focus trap in mobile nav when open
- [ ] Announce dropdown state changes to screen readers

### Performance
- [ ] Inline critical CSS
- [ ] Purge unused Tailwind classes
- [ ] Preload hero image

### Content
- [ ] Author pages
- [ ] Tag archive pages

---

## 12. File Inventory

```
.
├── config.py                 # Single source of truth: SITE_URL, paths, env constants
├── build.py                  # Main build script — 233 pages, thumbnails, OG images
├── schemas.py                # Pydantic models (AcaciaContent, RegistryData)
├── registry.json             # Content registry (59 entries: 33 research, 16 learn, 10 knowledge)
├── requirements.txt          # Dependencies
├── core/
│   ├── visuals.py            # Visual engine: fractal (7 types), chart (6 functions), topic overlays
│   └── images/               # 3-tier visual management: manifest, auto-fetch, SVG fallback
│       ├── __init__.py
│       ├── manifest.py
│       ├── manifest.json
│       └── templates.py      # Tier 3 SVG fallback generator
├── seed_articles.py          # Article seeding (legacy thumbnail gen — superseded by core/visuals.py)
├── seed_dataops.py           # DataOps/Engineering article seeder
├── migrate_categories.py     # Content type migration scripts
├── SITE-STATE.md             # This file
├── ARCHITECTURE.md           # Architecture blueprint
├── UX-PLAN.md                # UX evolution roadmap
├── deploy.sh                 # Legacy deployment script
│
├── templates/
│   ├── layout.j2             # Base layout — nav, dark mode, mobile drawer, footer
│   ├── blog_post.j2          # Research article — TOC, progress bar, 2×2 charts, flip flashcards
│   ├── index.j2              # Homepage — featured, 2×2 CTA grid, learn/knowledge cards
│   ├── category_index.j2     # Category listing (research/learn/knowledge)
│   ├── pillar_index.j2       # Pillar pages (AML/Markets/Science)
│   ├── learn.j2              # Learn lesson — accordion key concepts, flip flashcards
│   ├── learn_index.j2        # Learn index — difficulty-grouped with badges
│   ├── knowledge.j2          # Knowledge article — kcat badge, cross-references
│   ├── knowledge_index.j2    # Knowledge index — sub-category grouped
│   ├── search.j2             # Search — vanilla JS fuzzy scoring
│   └── 404.j2                # Custom 404 — deterministic suggestions
│
├── static/
│   ├── css/
│   │   ├── custom.css        # ~360 lines — CSS vars, dark mode, flashcard flip, mobile drawer, TOC
│   │   └── tailwind.min.css  # Tailwind 3.4.19 (28KB)
│   ├── js/
│   │   └── search.js         # Client-side search
│   └── fonts/
│       ├── Inter-Regular.woff2
│       ├── Inter-SemiBold.woff2
│       └── Inter-Bold.woff2
│
├── dist/                     # Generated output (326+ pages)
│   ├── index.html
│   ├── 404.html
│   ├── search/index.html
│   ├── learn/index.html
│   ├── knowledge/index.html
│   ├── research/index.html
│   ├── feed.xml
│   ├── sitemap.xml
│   ├── robots.txt
│   ├── _headers
│   ├── aml/index.html
│   ├── stock/index.html
│   ├── data-engineering/index.html
│   ├── science/index.html (→ /research/ meta-refresh redirect)
│   ├── YYYY-MM-DD-slug/index.html (×56)
│   ├── learn/slug/index.html (×16)
│   ├── knowledge/slug/index.html (×12)
│   └── static/ (copied from static/)
│
├── railway.json              # Railway deployment config
├── .github/
│   └── workflows/
│       └── deploy-api.yml    # GitHub Actions → Railway deploy
│
├── services/
│   └── api/
│       ├── Dockerfile        # Containerized FastAPI service
│       ├── requirements.txt
│       ├── .env.example
│       ├── app/
│       │   ├── __init__.py
│       │   ├── main.py       # FastAPI endpoints
│       │   └── db.py         # SQLite progress storage
│       └── tests/
│           ├── test_main.py
│           ├── test_db.py
│           └── test_progress.py
│
├── .env                      # (not committed)
├── .gitignore
└── README.md
```
