# AcaciaFund — Site State & Feature Inventory

> **Last updated:** 2026-06-07  
> **Deployed URL:** https://www.acaciafund.org  
> **Repo:** https://github.com/goneraleszek2-ship-it/acaciafund  
> **Generator:** `python3.13 generator.py`  
> **Host:** Cloudflare Pages (static)

---

## 1. Architecture

| Layer | Technology | Notes |
|-------|-----------|-------|
| Data source | `registry.json` | Pydantic-validated, single source of truth |
| Template engine | Jinja2 | 4 templates: `layout.j2`, `blog_post.j2`, `pillar_index.j2`, `index.j2` |
| Markdown rendering | `markdown2` | With `fenced-code-blocks` and `tables` extras |
| CSS framework | Tailwind 3.4.19 (28KB local) | No CDN — self-hosted `tailwind.min.css` |
| Custom styles | `static/css/custom.css` | ~270 lines — font-face, CSS variables, dark mode, TOC, dropdown, mobile nav, print styles |
| Fonts | Inter (self-hosted) | Regular, SemiBold, Bold WOFF2 (~340KB total) |
| Client JS | Inline `<script>` in templates | Dark mode toggle, dropdown, mobile nav, reading progress bar, TOC highlighting, focus mode |
| Output | `dist/` (21 HTML pages) | Cleaned and rebuilt on each generator run |

### Pipeline

```
registry.json → generator.py → Jinja2 templates → dist/*.html
```

No build framework (no Astro, no Hugo). The output is ready-to-serve static HTML.

---

## 2. Pages

| Page | Route | Template | Content Source |
|------|-------|----------|----------------|
| Home | `/` | `index.j2` | First 8 posts + first 6 lessons |
| Blog post (×12) | `/blog/YYYY-MM-DD-slug/` | `blog_post.j2` | `registry.json` |
| AML pillar | `/aml/` | `pillar_index.j2` | Filtered posts |
| Markets pillar | `/stock/` | `pillar_index.j2` | Filtered posts |
| Science pillar | `/science/` | `pillar_index.j2` | Filtered posts |
| About | `/about.html` | `layout.j2` | `content/en/about/index.md` |
| Research | `/research.html` | `layout.j2` | `content/en/research/index.md` |
| Scholarship | `/scholarship.html` | `layout.j2` | `content/en/scholarship/index.md` |
| Contact | `/contact.html` | `layout.j2` | `content/contact/index.md` |
| 404 | `/404.html` | `layout.j2` | Hardcoded in generator |
| Feed | `/feed.xml` | — | Atom feed, last 20 posts |
| Sitemap | `/sitemap.xml` | — | All pages |
| Robots | `/robots.txt` | — | Allow all, sitemap link |

**Total: 21 HTML pages** (12 blog posts + 3 pillar indices + 4 static pages + 1 index + 1 404)

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
| `--color-science` | `#5b5ea6` | Science pillar accent |

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
- Slide-down panel with pillar sub-links
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

### Per-Post Elements
- Fixed reading progress bar (3px, top of viewport, accent color)
- Breadcrumb: Home / Pillar / Post Title
- Pillar badge (colored, with emoji)
- SQI score (Signal Quality Index, 3 decimal places)
- Source breakdown (HN / arXiv / PubMed counts)
- Title, date, reading time ("N min read")
- Tags as pills
- Quality metrics grid (Avg Source Score, Source Diversity, Recency) — when available
- Body content with auto-generated heading IDs and anchor links
- Bloom Taxonomy Questions section (with colored level badges)
- Flashcards grid (up to 12, term + definition preview)
- Signal Analysis section (article count, total points, avg score, domains, entities)
- Related posts (top 3 by tag overlap, with pillar badges)
- Previous/Next post navigation

### TOC Sidebar
- Auto-generated from h2/h3 headings via `extract_headings()` in `generator.py`
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
- Unique `og_{hash}.svg` per post
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
python3.13 generator.py
```
Dependencies: `jinja2`, `markdown2`, `pydantic`

### Deployment
- Cloudflare Pages: auto-deploys from `main` branch
- Custom domain: `acaciafund.org` (www redirects from apex)
- Build command: `python3.13 generator.py`
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

| Pillar | Posts | Topics |
|--------|-------|--------|
| AML | 8 | Financial crime, compliance, regulation, risk, crypto, DeFi |
| Markets | 9 | Semiconductors, AI industry, manufacturing, EV, quantum |
| Science | 9 | Biology, quantum, neuroscience, space, climate, gene therapy |

Total: 27 blog posts (Jan 2026 — present)

All posts are auto-synthesized from HackerNews + arXiv sources.

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

### Planned (Week 4)
- [ ] Client-side search (Pagefind or JSON index + Fuse.js)
- [ ] "Surprise Me" serendipity button
- [ ] Trending by pillar (reader count)
- [ ] Custom 404 with post suggestions
- [ ] Full responsive nav polish

### Post-Week 4
- [ ] Bookmarks / "continue reading" (localStorage)
- [ ] Reading streaks + progress rings
- [ ] Citation popover on hover
- [ ] Inline retrieval prompts after sections
- [ ] Social share buttons
- [ ] SVG sprite sheet
- [ ] Fluid typography with `clamp()`

### Accessibility
- [ ] WCAG 2.1 AA audit
- [ ] Focus trap in mobile nav when open
- [ ] Announce dropdown state changes to screen readers

### Performance
- [ ] Inline critical CSS
- [ ] Purge unused Tailwind classes
- [ ] Preload hero image

### Content
- [ ] Add Learning Hub lessons (currently empty)
- [ ] Author pages
- [ ] Tag archive pages

---

## 12. File Inventory

```
.
├── generator.py              # Main generator (478 lines)
├── schemas.py                # Pydantic models (AcaciaContent, RegistryData)
├── registry.json             # Content registry (12 blog posts)
├── requirements.txt          # Dependencies
├── SITE-STATE.md             # This file
├── ARCHITECTURE.md           # Target architecture blueprint
├── UX-PLAN.md                # UX evolution roadmap
├── deploy.sh                 # Legacy deployment script
│
├── templates/
│   ├── layout.j2             # Base layout (213 lines)
│   ├── blog_post.j2          # Blog post page (245 lines)
│   ├── pillar_index.j2       # Pillar listing (59 lines)
│   └── index.j2              # Homepage (81 lines)
│
├── static/
│   ├── css/
│   │   ├── custom.css        # Custom styles (~270 lines)
│   │   └── tailwind.min.css  # Tailwind 3.4.19 (28KB)
│   ├── fonts/
│   │   ├── Inter-Regular.woff2
│   │   ├── Inter-SemiBold.woff2
│   │   └── Inter-Bold.woff2
│   └── js/
│       └── (reserved for future enhancements)
│
├── content/
│   ├── en/
│   │   ├── about/index.md
│   │   ├── research/index.md
│   │   └── scholarship/index.md
│   └── contact/index.md
│
├── public/                   # Legacy static assets (images, icons)
│   └── images/
│       └── favicon.svg
│
├── dist/                     # Generated output
│   ├── index.html
│   ├── 404.html
│   ├── about.html
│   ├── research.html
│   ├── scholarship.html
│   ├── contact.html
│   ├── feed.xml
│   ├── sitemap.xml
│   ├── robots.txt
│   ├── _headers
│   ├── aml/index.html
│   ├── stock/index.html
│   ├── science/index.html
│   ├── blog/
│   │   └── YYYY-MM-DD-slug/index.html (×12)
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
