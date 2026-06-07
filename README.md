<div align="center">
  <img src="https://img.shields.io/badge/status-active-22c55e?style=flat-square" alt="Status">
  <img src="https://img.shields.io/badge/python-3.13+-3776AB?logo=python&logoColor=fff&style=flat-square" alt="Python">
  <img src="https://img.shields.io/badge/jinja2-B41717?logo=jinja&logoColor=fff&style=flat-square" alt="Jinja2">
  <img src="https://img.shields.io/badge/cloudflare-pages-F38020?logo=cloudflare&logoColor=fff&style=flat-square" alt="Cloudflare">
  <img src="https://img.shields.io/badge/DataOps-enabled-6366f1?style=flat-square" alt="DataOps">
</div>

# AcaciaFund

Automated research synthesis platform — a **DataOps pipeline** that ingests, transforms, quality-gates, and serves content as a static data product.

HackerNews + arXiv → deterministic classification (Bloom taxonomy) → quality metrics (SQI) → Python-native static generator → warm, accessible, dark-mode-capable site.

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
│  • Build output: 54+ pages, validated                   │
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
| Research | 30 | Bloom-classified articles with SQI, signals, flashcards |
| Learn | 8 | Structured lessons with flashcards and code examples |
| Knowledge | 8 | Reference pages: glossary, tools landscape, system architecture |

### Pillar Coverage
| Pillar | Label | Badge Color | Research Articles |
|--------|-------|-------------|-------------------|
| AML | Shield | Amber | 8 |
| Markets | Chart | Green | 8 |
| Science | Microscope | Purple | 8 |

### Per-Article Content (Research)
- Bloom Taxonomy questions with colored level badges
- Flashcards grid (term + definition)
- Signal Analysis dashboard (article count, scores, domain diversity, entities)
- Quality metrics (source score, diversity, recency)
- Source breakdown (HN / arXiv / PubMed)
- Per-article unique fractal-thumbnail SVG (seed-based L-system tree)
- Per-article unique OG image

### Accessibility
- Skip-to-content link, `lang="en"`, ARIA labels, `role` attributes
- Keyboard `:focus-visible` indicators
- `prefers-reduced-motion` disables all animations
- Proper heading hierarchy (H1 → H2 → H3)
- Breadcrumbs with `aria-label` and `aria-current="page"`
- Accessible dropdown (`aria-expanded`, `aria-haspopup`, Escape key, click-outside)

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
- **Python 3.13** — generator
- **Pydantic** — schema validation (`schemas.py`)
- **Jinja2** — 6 templates (`layout.j2`, `blog_post.j2`, `pillar_index.j2`, `index.j2`, `category_index.j2`, `learn.j2`)
- **Markdown2** — Markdown → HTML rendering
- **Tailwind CSS 3.4.19** — utility classes (self-hosted)
- **Custom CSS** — `static/css/custom.css`
- **Inter** — self-hosted font (3 WOFF2 files)
- **Cloudflare Pages** — static hosting

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

### Regenerate Thumbnails / Seed New Articles

```bash
python3.13 seed_articles.py      # Regenerate all thumbnails + OG images
python3.13 seed_dataops.py       # Add DataOps/Engineering articles
```

---

## Project Structure

```
├── generator.py                 # Main generator (Jinja2 → static HTML)
├── schemas.py                   # Pydantic models (AcaciaContent, RegistryData)
├── registry.json                # Content registry (data catalog)
├── seed_articles.py             # Article seeding + fractal thumbnail generator
├── seed_dataops.py              # DataOps/Engineering article seeder
├── migrate_categories.py        # Content type migration scripts
├── templates/                   # Jinja2 templates
│   ├── layout.j2                # Base layout with nav, dark mode, footer
│   ├── blog_post.j2             # Research (TOC, progress bar, flashcards, signals)
│   ├── index.j2                 # Homepage (featured, categories, stack)
│   ├── category_index.j2        # Category listing (research/learn/knowledge)
│   ├── pillar_index.j2          # Pillar pages (AML/Markets/Science)
│   └── learn.j2                 # Learning hub content
├── static/
│   ├── css/
│   │   ├── custom.css           # Custom styles (colors, dark mode, a11y)
│   │   └── tailwind.min.css     # Tailwind utility classes (28KB)
│   └── fonts/
│       └── Inter-*.woff2        # Self-hosted font files
├── content/                     # Source markdown for static pages
├── public/                      # Additional static assets (images, icons)
├── services/api/                # FastAPI service (Railway-deployed)
│   ├── app/
│   │   ├── main.py              # API endpoints
│   │   └── db.py                # SQLite database
│   ├── Dockerfile
│   ├── requirements.txt
│   └── tests/
├── dist/                        # Generated output (gitignored items)
├── .github/workflows/
│   └── deploy-api.yml           # Railway API deployment
├── railway.json                 # Railway config
├── SITE-STATE.md                # Full feature inventory
├── UX-PLAN.md                   # UX evolution roadmap
└── ARCHITECTURE.md              # Target architecture blueprint
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
