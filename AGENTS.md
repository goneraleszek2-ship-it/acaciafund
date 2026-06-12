# AGENTS.md — Session State & Plan

## Build
```
python3 build.py        # Generates 376 pages into dist/
```
No lint/typecheck — pure Python + Jinja2 static site. Cloudflare Pages auto-deploys on push to `main`.

## File Conventions
- **CSS**: `static/css/custom.css` — Tailwind + custom props; pillar colors, layer variables (`--layer-*-body/badge/accent`), section-collapse/viz rules
- **Python**: `build.py` is the monolith (~1700 lines). Core helpers in `core/` (`brand.py`, `visuals.py`, `images/templates.py`). Jinja2 templates in `templates/`.
- **Templates**: `layout.j2` (base), `index.j2` (homepage), `category_index.j2` (research index), `pillar_index.j2` (pillar pages), `blog_post.j2` (article detail). Macros in `templates/macros/`.
- **Data visualizations**: zero-JS build-time SVGs from `core/visuals.py` — `source_bar_svg()`, `bloom_chart_svg()`, `radar_svg()`, `donut_svg()`, `generate_signal_meter()`. Injected as `.section-viz` inside each section-harvester.
- **JS**: `learning_hub.js` — reading progress bar, TOC scroll-spy, flashcards, quiz, section collapse (TOC link opens parent `<details>`), per-section IntersectionObserver progress tracking.

## Completed

### Phase 0 — Visual Differentiation of Content Types
- **0A**: ~~Fractal SVG patterns~~ *Replaced by data visualizations (see "D3liver" below).*
- **0B**: `use_harvesters` expanded to all content types (research, learn, knowledge).
- **0C**: Learn/knowledge thumbnail scores default to `{}`; SQI bar rendered only when `"sqi"` key exists.
- **0D**: `section_type_color` types 3 & 6 use pillar palette instead of hardcoded gray.

### Phase 1 — UI Polish
- **1E**: `<body data-layer="{{ layer }}">` + stronger background tints (`--layer-*-body`). Fixed layer default position. Added 4px colored `layer-strip` at top of page per content type.
- **1F**: Section collapse — each section wrapped in `<details open>`, heading inside `<summary>`, click to toggle. TOC links auto-open parent `<details>` via JS. Per-section IntersectionObserver progress tracking (`.section-read` class + checkmark).
- **1G**: `content_badge()` Jinja2 macro. `.content-type-badge` pill styles. Badges on homepage cards.

### "D3liver" — Data Visualizations Replace Abstract Patterns
- Removed `section_pattern_svg()` calls and `--section-pattern` CSS (6% opacity abstract decorations gone)
- Each section type now shows a real data-driven SVG chart using article's own signals:
  - **overview** → SQI meter
  - **key_findings** → Bloom taxonomy bar chart
  - **applied_scenario** → Source distribution stacked bar
  - **source_analysis** → Source donut chart
  - **domain_breakdown** → Domain diversity bar
  - **cross_pillar** → Quality metrics radar
  - **methodology** → Source score meter
- Rendered as `.section-viz` card (surface bg, border, label + chart)

## Remaining
### Phase 2 — Icon System Fixes
- Per-pillar topic-icon SVG colors (currently hardcoded to AML palette)
- Icon-based thumbnail fallback for articles without section harvesters

## Key Decisions
- Zero-JS data visualizations: all SVGs generated at build time in pure Python, no D3.js runtime
- `<details>`/`<summary>` for section collapse — no JS needed for basic toggle, accessible, semantic
- TOC links open parent `<details>` in `learning_hub.js` (so clicking a TOC anchor shows that section's content)
- `inject_section_images()` now accepts full `AcaciaContent` object (not dict) to access signals/bloom/source data
- `_article_as_dict()` helper converts Pydantic model to dict for `generate_fallback_svg()` compatibility
- Layer strip (4px fixed bar at top) provides immediate content-type identity even before user notices background tint
- Section collapse defaults to `open` so all content is visible by default