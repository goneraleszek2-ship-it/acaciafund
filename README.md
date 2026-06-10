<div align="center">
  <img src="https://img.shields.io/badge/status-active-22c55e?style=flat-square" alt="Status">
  <img src="https://img.shields.io/badge/python-3.13+-3776AB?logo=python&logoColor=fff&style=flat-square" alt="Python">
  <img src="https://img.shields.io/badge/jinja2-B41717?logo=jinja&logoColor=fff&style=flat-square" alt="Jinja2">
  <img src="https://img.shields.io/badge/cloudflare-pages-F38020?logo=cloudflare&logoColor=fff&style=flat-square" alt="Cloudflare">
  <img src="https://img.shields.io/badge/DataOps-enabled-6366f1?style=flat-square" alt="DataOps">
</div>

# AcaciaFund

Automated research synthesis platform — a **DataOps pipeline** that ingests, transforms, quality-gates, and serves content as a static data product.

HackerNews + arXiv → deterministic classification (Bloom taxonomy) → quality metrics (SQI) → Python-native static generator → warm, accessible, dark-mode-capable site with 56 research articles, 16 learn lessons, and 12 knowledge references.

**Site:** https://www.acaciafund.org

---

## DataOps System Architecture

AcaciaFund applies **DataOps principles** across its entire content lifecycle — treating the pipeline itself as a data product:

```
┌────────────────────────────────────────────────────────┐
│                    INGESTION LAYER                      │
│  HackerNews API ──┐                                     │
│  arXiv API        ├──→ trending stories + analysis      │
│  PubMed           ┘    (manual + scheduled)             │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│                 TRANSFORMATION LAYER                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ NLP Pipeline │  │   Bloom     │  │    SQI       │  │
│  │ (entity ext, │→│  Taxonomy   │→│  Computation │  │
│  │ summarization│) │  Classifier │  │  (0.0 – 1.0) │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│                 STORAGE / CATALOG LAYER                 │
│  ┌──────────────────────────────────────────────────┐   │
│  │           registry.json (Data Catalog)            │   │
│  │  • Content metadata    • Quality metrics          │   │
│  │  • Source lineage      • Pipeline state           │   │
│  │  • Signal scores       • Taxonomy classification  │   │
│  └──────────────────────────────────────────────────┘   │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│                 SERVING LAYER                           │
│  ┌──────────────┐    ┌──────────────┐                   │
│  │    build     │───→│   Static     │───→ Cloudflare    │
│  │  .py (Jinja2)│    │  HTML Files  │    Pages (CDN)    │
│  └──────────────┘    └──────────────┘                   │
│  Serves: research/ · learn/ · knowledge/ · pillars/     │
└────────────────────────────────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│              OBSERVABILITY & QUALITY                    │
│  • SQI per article (0–1)    • Source diversity score    │
│  • Quality flags            • Cross-pillar connections  │
│  • Source breakdown (HN/arXiv/PubMed)                   │
│  • Build output: 332 pages, validated                   │
└────────────────────────────────────────────────────────┘
```

### DataOps Principles Applied

| Practice | AcaciaFund Implementation |
|----------|--------------------------|
| **Version Control Everything** | `registry.json` + pipeline code under Git — every content change is a commit with audit trail |
| **Data Quality as Code** | SQI metric, quality_metrics, quality_flags — evaluated programmatically per entry |
| **CI/CD for Data** | `git push → Cloudflare Pages → python3.13 build.py` — automated build with schema validation gate |
| **Declarative Pipeline** | Deterministic: same `registry.json` → identical output, no side effects |
| **Observability** | Structured signals per article: source breakdown, domain diversity, SQI, top entities |
| **Content Taxonomy** | 3 content types — research (Bloom-classified), learn (lessons), knowledge (reference) |
| **Modular Stack** | Python-native toolchain, open source only, zero vendor lock-in |

---

## Features

### 3-Layer Visual Identity System
- **Research (gold)** — SQI-leading cards with left-column SQI scores and source badges, gold layer indicator bar, gold nav active state, gold-bordered card layout
- **Learn (teal)** — Bloom taxonomy path visual (L1 Remember → L6 Create) with data-driven node completion, teal indicator bar, teal nav active state
- **Knowledge (blue)** — Search-enhanced category card grid (Platform/Guides/Reference/Architecture), blue indicator bar, blue nav active state
- Persistent layer indicator bar on every page (icon + label + contextual sub-text showing pillar/bloom/category)
- Per-layer CSS tokens with light/dark mode support

### 3-Tier Image Management System
- **Tier 1 (Editorial)** — `core/images/manifest.json` maps article slugs to hand-picked images; edit as JSON, no Python needed
- **Tier 2 (Auto-fetch)** — Openverse / Wikimedia / NASA / Library of Congress API backends with keyword scoring
- **Tier 3 (SVG Fallback)** — Pillar-colored inline SVGs with section-type icons; zero network, zero storage, 100% coverage invariant

### Reading Experience
- Sticky table of contents with active-heading highlighting
- Reading progress bar (fixed 3px at viewport top)
- Focus mode (hides TOC, centers content to 65ch)
- Previous/next post navigation
- Related posts by tag overlap (3-card grid with pillar badges)
- Reading time estimate on every card and post

### Visual Identity
- Warm cream palette (`#f5f0eb` background) with CSS custom properties
- Self-hosted Inter font (Regular/SemiBold/Bold WOFF2 — no Google Fonts)
- Dark mode with FOUC prevention, `localStorage` persistence, system preference fallback
- Dual `theme-color` meta tags for light/dark browser chrome

### Content Taxonomy (DataOps-aligned)
| Type | Count | Description |
|------|-------|-------------|
| Research | 56 | Bloom-classified articles with SQI, signals, flashcards, charts |
| Learn | 16 | Structured lessons + hub index — flashcards (CSS 3D flip), quizzes (Bloom taxonomy), progress tracking, spaced repetition |
| Knowledge | 12 | Reference pages: platform info, guides, glossaries, system architecture |

### Pillar Coverage
| Pillar | Research | Learn | Topics |
|--------|----------|-------|--------|
| Data Engineering | 27 | 4 | Orchestration, quality, streaming, lakehouse, analytics, data mesh |
| Markets | 21 | 7 | Semiconductors, AI industry, manufacturing, EV, quantum, finance |
| AML | 7 | 4 | Financial crime, compliance, regulation, crypto, DeFi, sanctions |

### Per-Article Content (Research)
- Bloom Taxonomy questions with colored level badges
- Flashcards grid (term + definition)
- Signal Analysis dashboard (article count, scores, domain diversity, entities)
- Quality metrics (source score, diversity, recency)
- Source breakdown (HN / arXiv / PubMed)
- Per-article unique fractal-thumbnail SVG (hash-seeded engine: 7 types — L-tree, Sierpinski, Koch, Dragon, Fern, Spiral, Hilbert)
- Mirror reflections (none/h/v/both) for diversified compositions
- Dynamic color gradients, `stroke-linecap="round"`, atmospheric mist layers
- Per-article unique OG image with fractal mist + decorative ellipses

### Accessibility
- Skip-to-content link, `lang="en"`, ARIA labels, `role` attributes
- Keyboard `:focus-visible` indicators
- `prefers-reduced-motion` disables all animations
- Proper heading hierarchy (H1 → H2 → H3)
- Breadcrumbs with `aria-label` and `aria-current="page"`

### Navigation & UI
- Fixed full-viewport mobile drawer with native `<dialog>` element (focus trap, Escape key)
- Client-side search with vanilla JS fuzzy scoring (title > tag > description priority)
- "Surprise Me" button — picks random article from index on click
- Custom 404 page with deterministic article suggestions (hash-stable per build)

### Interactive Content
- CSS 3D flip flashcards (term → definition with tap/reveal animation)
- Accordion key concepts (click-to-expand with animated chevron in learn lessons)
- Bloom taxonomy quiz engine with SM-2 spaced repetition scoring
- "Mark Complete" progress tracking (localStorage)
- Spaced repetition review scheduling

### Charts & Visuals
- Zero-JS static charts (donut, radar, heatmap, bloom, source bar) — 2x2 grid layout
- WCAG AA contrast (4.5:1+) enforced on all chart labels and indicators
- Hash-seeded fractal thumbnails with 7 types + mirror reflections + color gradients

### Infrastructure
- Zero client-side JS for content reading (JS only for UI enhancements)
- Python-native pipeline: `python3.13 build.py`
- Cloudflare Pages auto-deploy from `main`
- Self-hosted Tailwind 3.4.19 (28KB, no CDN)
- Security headers (`X-Content-Type-Options`, `X-Frame-Options`, `Permissions-Policy`, etc.)
- Atom feed, sitemap, robots.txt, canonical URLs, JSON-LD structured data

---

## Application Stack

### Core Pipeline
- **Python 3.13** — generator + visual engine
- **Pydantic** — schema validation (`schemas.py`)
- **Jinja2** — 13 templates (layout, blog_post, pillar_index, index, category_index, learn, learn_index, knowledge, knowledge_index, search, 404, aml_signals, tag_index)
- **Markdown2** — Markdown → HTML rendering
- **Tailwind CSS 3.4.19** — utility classes (self-hosted)
- **Custom CSS** — `static/css/custom.css` (~1095 lines: layer system, flashcard flip, accordion, mobile dialog, TOC, focus mode, dark mode, Bloom path, knowledge hub)
- **Inter** — self-hosted font (3 WOFF2 files)
- **Cloudflare Pages** — static hosting

### Visual Engine (`core/visuals.py`)
- **Fractal engine** — 7 types (L-tree, Sierpinski, Koch, Dragon, Fern, Spiral, Hilbert) + mirror + mist + color lerp
- **Chart engine** — 6 functions (donut, radar, heatmap, bloom, source bar, scaffold) with WCAG AA contrast
- **Topic-aware overlays** — PILLAR_PALETTES, TOPIC_ICONS, keyword tags per article

### Image Management (`core/images/`)
- **Manifest** — `manifest.json` editorial overrides (Tier 1)
- **Auto-fetch** — `scripts/fetch_images.py` queries 4 API backends (Tier 2)
- **Fallback SVGs** — `templates.py` pillar-colored inline SVGs (Tier 3)

### Service Layer
- **FastAPI** (Python 3.11) — `services/api/`
- **Docker** — containerized deployment
- **Railway** — cloud runtime
- **SQLite** — progress tracking storage
- **GitHub Actions** — API deployment workflow

### CI/CD Workflows
- `.github/workflows/deploy-pages.yml` — Build + test + deploy to Cloudflare Pages on push to `main`
- `.github/workflows/ingest.yml` — Daily scheduled content ingestion (06:00 UTC)
- `.github/workflows/deploy-api.yml` — Deploy FastAPI service to Railway

---

## Quick Start

```bash
git clone https://github.com/goneraleszek2-ship-it/acaciafund.git
cd acaciafund
pip install markdown2 pydantic jinja2 requests Pillow
python3.13 build.py
python3 -m http.server 8000 --dir dist
```

Then open http://localhost:8000.

### Regenerate Everything

```bash
python3.13 build.py          # Rebuild all 332 pages, fractal thumbnails, OG images, search index, feed
```

---

## Project Structure

```
├── config.py                   # Single source of truth: SITE_URL, paths, env config
├── build.py                    # Main build script (Jinja2 → 332 HTML pages)
├── schemas.py                  # Pydantic models (AcaciaContent, RegistryData)
├── registry.json               # Content registry (data catalog — 84 entries)
├── core/
│   ├── visuals.py              # Visual engine: fractal (7 types), chart (6 functions), topic overlays
│   └── images/                 # 3-tier visual management: manifest, auto-fetch, SVG fallback
│       ├── manifest.py
│       ├── manifest.json
│       └── templates.py
├── scripts/
│   ├── fetch_images.py         # Tier 2 auto-fetch (4 API backends)
│   ├── preflight.py            # Deployment preflight checks
│   ├── create_diagrams_page.py # System architecture knowledge page
│   └── migrate_posts_to_bundles.py
├── seed_learn.py               # Learn article seed data (pillars, difficulty, prerequisites)
├── seed_articles.py            # Legacy article seeding (superseded)
├── seed_dataops.py             # DataOps article seeder
├── migrate_categories.py       # Content type migration scripts
├── templates/                  # Jinja2 templates (13 + 4 macros + 4 partials)
│   ├── layout.j2               # Base layout: sticky header, layer indicator, nav, mobile dialog, footer
│   ├── blog_post.j2            # Research: TOC, progress bar, 2x2 charts, flip flashcards
│   ├── index.j2                # Homepage: featured, hero, learn/knowledge cards
│   ├── category_index.j2       # Category listing (research/learn/knowledge)
│   ├── pillar_index.j2         # Pillar pages (AML/Markets/Data Engineering)
│   ├── learn.j2                # Learn lesson: quizzes (Bloom), flashcards (3D flip), progress
│   ├── learn_index.j2          # Learn index: Bloom path, difficulty-grouped, pillar progress bars
│   ├── knowledge.j2            # Knowledge article: category badge, cross-references
│   ├── knowledge_index.j2      # Knowledge index: search bar, category card grid
│   ├── search.j2               # Search: input + JSON index + vanilla JS scoring
│   ├── 404.j2                  # Custom 404: deterministic suggestions
│   ├── aml_signals.j2          # AML Signals Dashboard
│   ├── tag_index.j2            # Tag archive listing
│   ├── icons/                  # Pillar SVG icons (shield, line-chart, cog)
│   ├── macros/                 # Reusable macros (breadcrumbs, pillar_badge, sqi_chip, card)
│   └── partials/               # Reusable partials (article_image, newsletter, search_palette, hero)
├── static/
│   ├── css/
│   │   ├── custom.css          # ~1095 lines: CSS vars, layer system, dark mode, flashcard flip
│   │   └── tailwind.min.css    # Tailwind 3.4.19 (28KB, local)
│   ├── js/
│   │   └── search.js           # Client-side search (vanilla JS, fuzzy scoring)
│   └── fonts/
│       └── Inter-*.woff2       # Self-hosted font files
├── tests/
│   ├── test_core.py            # Core pipeline tests (779 lines)
│   ├── test_images.py          # 3-tier image system tests (213 lines)
│   ├── test_build_meta.py      # Build metadata tests
│   ├── test_live.py            # Generated output smoke tests
│   ├── test_metadata.py        # Registry and manifest tests
│   └── test_gac.py             # GAC component tests
├── dist/                       # Generated output (332 pages, gitignored)
├── .github/workflows/
│   ├── deploy-pages.yml        # Cloudflare Pages deploy (build + test + deploy)
│   ├── ingest.yml              # Daily scheduled ingestion pipeline
│   └── deploy-api.yml          # Railway API deployment
├── services/api/               # FastAPI service (Railway-deployed)
├── app/                        # Legacy compatibility shim
├── railway.json                # Railway config
├── wrangler.toml               # Cloudflare Pages build config
├── SITE-STATE.md               # Full feature inventory
├── ARCHITECTURE.md             # Architecture blueprint
└── README.md                   # This file
```

---

## Deployment

Push to `main` → Cloudflare Pages auto-deploys.  
Build command: `python3.13 build.py`  
Output directory: `dist/`

API service deploys separately via Railway (Docker container).

---

## Design Principles

- **DataOps-first** — pipeline as data product with observability, quality gates, and CI/CD
- **Static-first** — no build framework, no JS runtime for content
- **Accessible** — WCAG 2.1 AA, keyboard nav, screen reader friendly
- **Privacy-preserving** — no analytics, no CDN fonts, no third-party requests
- **Deterministic** — same `registry.json` always produces identical output
- **Typographic** — typography as primary hierarchy carrier
- **Warm** — cream palette with deep navy text, not sterile white/blue

---

## License

MIT — Leszek Gonera · AcaciaFund
