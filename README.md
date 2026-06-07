<div align="center">
  <img src="https://img.shields.io/badge/status-active-22c55e?style=flat-square" alt="Status">
  <img src="https://img.shields.io/badge/python-3.13+-3776AB?logo=python&logoColor=fff&style=flat-square" alt="Python">
  <img src="https://img.shields.io/badge/jinja2-B41717?logo=jinja&logoColor=fff&style=flat-square" alt="Jinja2">
  <img src="https://img.shields.io/badge/cloudflare-pages-F38020?logo=cloudflare&logoColor=fff&style=flat-square" alt="Cloudflare">
  <img src="https://img.shields.io/badge/WCAG_2.1_AA-005A9C?style=flat-square" alt="WCAG">
</div>

# AcaciaFund

Automated research synthesis blog — static-first, privacy-preserving, psychologically-informed reading experience.

HackerNews + arXiv → deterministic classification (Bloom taxonomy) → Python-native static generator → warm, accessible, dark-mode-capable site.

**Site:** https://www.acaciafund.org

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

### Pillar Taxonomy
| Pillar | Label | Badge Color | Posts |
|--------|-------|-------------|-------|
| AML | Shield | Amber | 4 |
| Markets | Chart | Green | 4 |
| Science | Microscope | Purple | 4 |

### Accessibility
- Skip-to-content link, `lang="en"`, ARIA labels, `role` attributes
- Keyboard `:focus-visible` indicators
- `prefers-reduced-motion` disables all animations
- Proper heading hierarchy (H1 → H2 → H3)
- Breadcrumbs with `aria-label` and `aria-current="page"`
- Accessible dropdown (`aria-expanded`, `aria-haspopup`, Escape key, click-outside)

### Per-Post Content
- Bloom Taxonomy questions with colored level badges
- Flashcards grid (term + definition)
- Signal Analysis dashboard (article count, scores, domain diversity, entities)
- Quality metrics (source score, diversity, recency)
- Source breakdown (HN / arXiv / PubMed)
- Tags, date, pillar badge, SQI score
- Per-post OG images (unique SVG per title)

### Infrastructure
- Zero client-side JS for content reading (JS only for UI enhancements)
- Python-native pipeline: `python3.13 generator.py`
- Cloudflare Pages auto-deploy from `main`
- Self-hosted Tailwind 3.4.19 (28KB, no CDN)
- Security headers (`X-Content-Type-Options`, `X-Frame-Options`, `Permissions-Policy`, etc.)
- Atom feed, sitemap, robots.txt, canonical URLs, JSON-LD structured data

---

## Architecture

```
registry.json ─→ generator.py ─→ Jinja2 templates ─→ dist/*.html
                                              ↑
                                    static/css/, static/fonts/
```

### Stack
- **Python 3.13** — generator
- **Pydantic** — schema validation (`schemas.py`)
- **Jinja2** — 4 templates (`layout.j2`, `blog_post.j2`, `pillar_index.j2`, `index.j2`)
- **Markdown2** — Markdown → HTML rendering
- **Tailwind CSS 3.4.19** — utility classes (self-hosted)
- **Custom CSS** — `static/css/custom.css` (~270 lines)
- **Inter** — self-hosted font (3 WOFF2 files)
- **Cloudflare Pages** — static hosting

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

---

## Project Structure

```
├── generator.py              # Main generator
├── schemas.py                # Pydantic models
├── registry.json             # Content registry (single source of truth)
├── templates/                # Jinja2 templates
│   ├── layout.j2             # Base layout with nav, dark mode, footer
│   ├── blog_post.j2          # Blog post with TOC, progress bar, related
│   ├── pillar_index.j2       # Pillar listing pages
│   └── index.j2              # Homepage
├── static/
│   ├── css/
│   │   ├── custom.css        # Custom styles (colors, dark mode, a11y)
│   │   └── tailwind.min.css  # Tailwind utility classes (28KB)
│   └── fonts/
│       └── Inter-*.woff2     # Self-hosted font files
├── content/                  # Source markdown for static pages
├── public/                   # Additional static assets
├── dist/                     # Generated output (gitignored items)
├── SITE-STATE.md             # Full feature inventory
├── UX-PLAN.md                # UX evolution roadmap
└── ARCHITECTURE.md           # Target architecture blueprint
```

---

## Deployment

Push to `main` → Cloudflare Pages auto-deploys.  
Build command: `python3.13 generator.py`  
Output directory: `dist/`

---

## Design Principles

- **Static-first** — no build framework, no JS runtime for content
- **Accessible** — WCAG 2.1 AA, keyboard nav, screen reader friendly
- **Privacy-preserving** — no analytics, no CDN fonts, no third-party requests
- **Deterministic** — same `registry.json` always produces identical output
- **Typographic** — typography as primary hierarchy carrier
- **Warm** — cream palette with deep navy text, not sterile white/blue

---

## License

MIT — Leszek Gonera · AcaciaFund
