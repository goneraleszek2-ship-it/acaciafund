<div align="center">
  <img src="https://img.shields.io/badge/status-active-22c55e?style=flat-square" alt="Status">
  <img src="https://img.shields.io/badge/python-3.13+-3776AB?logo=python&logoColor=fff&style=flat-square" alt="Python">
  <img src="https://img.shields.io/badge/jinja2-B41717?logo=jinja&logoColor=fff&style=flat-square" alt="Jinja2">
  <img src="https://img.shields.io/badge/cloudflare-pages-F38020?logo=cloudflare&logoColor=fff&style=flat-square" alt="Cloudflare">
  <img src="https://img.shields.io/badge/DataOps-enabled-6366f1?style=flat-square" alt="DataOps">
</div>

# AcaciaFund

Automated research synthesis platform — a **DataOps pipeline** that ingests, transforms, quality-gates, and serves content as a static data product.

HackerNews + arXiv → deterministic classification (Bloom taxonomy) → quality metrics (SQI) → Python-native static generator → warm, accessible, dark-mode-capable site with 33 research articles, 15 learn lessons (+ hub), and 10 knowledge references.

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
│  │  generator   │───→│   Static     │───→ Cloudflare    │
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
│  • Build output: 60+ pages, validated                   │
└────────────────────────────────────────────────────────┘
```

### DataOps Principles Applied

| Practice | AcaciaFund Implementation |
|----------|--------------------------|
| **Version Control Everything** | `registry.json` + pipeline code under Git — every content change is a commit with audit trail |
| **Data Quality as Code** | SQI metric, quality_metrics, quality_flags — evaluated programmatically per entry |
| **CI/CD for Data** | `git push → Cloudflare Pages → python3.13 generator.py` — automated build with schema validation gate |
| **Declarative Pipeline** | Deterministic: same `registry.json` → identical output, no side effects |
| **Observability** | Structured signals per article: source breakdown, domain diversity, SQI, top entities |
| **Content Taxonomy** | 3 content types — research (Bloom-classified), learn (lessons), knowledge (reference) |
| **Modular Stack** | Python-native toolchain, open source only, zero vendor lock-in |

---

## Features

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
| Research | 33 | Bloom-classified articles with SQI, signals, flashcards, charts |
| Learn | 16 | 15 structured lessons + hub index — flashcards (CSS 3D flip), quizzes (Bloom taxonomy), progress tracking, spaced repetition |
| Knowledge | 10 | Reference pages: glossary, tools landscape, system architecture, DataOps |

### Pillar Coverage
| Pillar | Label | Badge Color | Research Articles | Learn Lessons |
|--------|-------|-------------|-------------------|---------------|
| AML | Shield | Amber | 11 | 5 |
| Markets | Chart | Green | 10 | 6 |
| Science | Microscope | Purple | 12 | 4 |

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
- Accessible dropdown (`aria-expanded`, `aria-haspopup`, Escape key, click-outside)

### Navigation & UI
- Fixed full-viewport mobile drawer with backdrop — never overlaps content
- Accessible dropdown (`aria-expanded`, `aria-haspopup`, Escape key, click-outside)
- Client-side search with vanilla JS fuzzy scoring (title > tag > description priority)
- "Surprise Me" button — picks random article from index on click
- Custom 404 page with deterministic article suggestions (hash-stable per build)

### Interactive Content
- CSS 3D flip flashcards (term → definition with tap/reveal animation)
- Accordion key concepts (click-to-expand with animated chevron in learn lessons)
- Metadata icons (clock SVG for reading time, calendar SVG for dates)

### Charts & Visuals
- Zero-JS static charts (donut, radar, heatmap, bloom, source bar) — 2x2 grid layout
- WCAG AA contrast (4.5:1+) enforced on all chart labels and indicators
- Hash-seeded fractal thumbnails with 7 types + mirror reflections + color gradients

### Infrastructure
- Zero client-side JS for content reading (JS only for UI enhancements)
- Python-native pipeline: `python3.13 generator.py`
- Cloudflare Pages auto-deploy from `main`
- Self-hosted Tailwind 3.4.19 (28KB, no CDN)
- Security headers (`X-Content-Type-Options`, `X-Frame-Options`, `Permissions-Policy`, etc.)
- Atom feed, sitemap, robots.txt, canonical URLs, JSON-LD structured data

---

## Application Stack

### Core Pipeline
- **Python 3.13** — generator + visual engine
- **Pydantic** — schema validation (`schemas.py`)
- **Jinja2** — 11 templates (`layout.j2`, `blog_post.j2`, `pillar_index.j2`, `index.j2`, `category_index.j2`, `learn.j2`, `learn_index.j2`, `knowledge.j2`, `knowledge_index.j2`, `search.j2`, `404.j2`)
- **Markdown2** — Markdown → HTML rendering
- **Tailwind CSS 3.4.19** — utility classes (self-hosted)
- **Custom CSS** — `static/css/custom.css` (flashcard flip, accordion, mobile drawer, TOC, focus mode, dark mode)
- **Inter** — self-hosted font (3 WOFF2 files)
- **Cloudflare Pages** — static hosting

### Visual Engine (`core/visuals.py`)
- **Fractal engine** — 7 types (L-tree, Sierpinski, Koch, Dragon, Fern, Spiral, Hilbert) + mirror + mist + color lerp
- **Chart engine** — 6 functions (donut, radar, heatmap, bloom, source bar, scaffold) with WCAG AA contrast
- **Topic-aware overlays** — PILLAR_PALETTES, TOPIC_ICONS, keyword tags per article

### Service Layer
- **FastAPI** (Python 3.11) — `services/api/`
- **Docker** — containerized deployment
- **Railway** — cloud runtime
- **SQLite** — progress tracking storage
- **GitHub Actions** — API deployment workflow

### Data Sources for Daily Article Discovery
- **HackerNews** (news.ycombinator.com) — tech/business/science current events
- **arXiv** (arxiv.org) — academic preprints across all domains
- **KDnuggets** — data science and ML news
- **Daily Dose of Data Science** — daily DS/ML engineering insights
- **DataOps Labs (Substack)** — DataOps, AI/ML, cloud DevOps
- **Pipeline To Insights** — data engineering interview prep and practices
- **Airbyte Blog** — data integration and DataOps best practices
- **Astronomer Blog** — Airflow and data pipeline orchestration
- **GigaOm** — data infrastructure research
- **Data Stack Hub** — open source data tool comparisons
- **Awesome DataOps / Awesome Open Source Data Engineering** — curated GitHub tool lists

---

## Quick Start

```bash
git clone https://github.com/goneraleszek2-ship-it/acaciafund.git
cd acaciafund
pip install markdown2 pydantic jinja2
python3.13 generator.py
python3 -m http.server 8000 --dir dist
```

Then open http://localhost:8000.

### Regenerate Everything

```bash
python3.13 generator.py          # Rebuild all 233 pages, fractal thumbnails, OG images, search index, feed
```

---

## Project Structure

```
├── config.py                   # Single source of truth: SITE_URL, paths, env config
├── generator.py                # Main generator (Jinja2 → 233 HTML pages)
├── schemas.py                  # Pydantic models (AcaciaContent, RegistryData)
├── registry.json               # Content registry (data catalog — 59 entries)
├── core/
│   └── visuals.py              # Visual engine: fractal (7 types), chart (6 functions), topic overlays
├── seed_articles.py            # Article seeding (legacy thumbnail generator)
├── seed_dataops.py             # DataOps/Engineering article seeder
├── migrate_categories.py       # Content type migration scripts
├── templates/                  # Jinja2 templates (11 total)
│   ├── layout.j2               # Base layout: nav, dark mode, mobile drawer, footer
│   ├── blog_post.j2            # Research: TOC, progress bar, 2x2 charts, flip flashcards
│   ├── index.j2                # Homepage: featured, 2x2 CTA grid, learn/knowledge cards
│   ├── category_index.j2       # Category listing (research/learn/knowledge)
│   ├── pillar_index.j2         # Pillar pages (AML/Markets/Science)
│   ├── learn.j2                # Learn lesson: quizzes (Bloom), flashcards (3D flip), progress
│   ├── learn_index.j2          # Learn index: difficulty-grouped, pillar progress bars, review due
│   ├── knowledge.j2            # Knowledge article: category badge, cross-references
│   ├── knowledge_index.j2      # Knowledge index: grouped by sub-category
│   ├── search.j2               # Search: input + JSON index + vanilla JS scoring
│   └── 404.j2                  # Custom 404: deterministic suggestions
├── static/
│   ├── css/
│   │   ├── custom.css          # Custom styles (colors, dark mode, flashcard flip, mobile drawer, TOC)
│   │   └── tailwind.min.css    # Tailwind utility classes (28KB)
│   ├── js/
│   │   └── search.js           # Client-side search (vanilla JS, fuzzy scoring)
│   └── fonts/
│       └── Inter-*.woff2       # Self-hosted font files
├── content/                     # Source markdown for static pages
├── services/api/                # FastAPI service (Railway-deployed)
├── tests/
│   └── astro_smoke.py           # Build output smoke tests
├── dist/                        # Generated output (233 pages, gitignored)
├── .github/workflows/
│   └── deploy-api.yml           # Railway API deployment
├── railway.json                 # Railway config
├── wrangler.toml                # Cloudflare Pages build config
├── SITE-STATE.md                # Full feature inventory
├── UX-PLAN.md                   # UX evolution roadmap
└── ARCHITECTURE.md              # Architecture blueprint
```

---

## Deployment

Push to `main` → Cloudflare Pages auto-deploys.  
Build command: `python3.13 generator.py`  
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
