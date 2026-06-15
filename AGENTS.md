# AGENTS.md — Session State & Plan

## Mem0 Context (Auto-Generated)

### Current Session
- **Session ID**: session_abc123
- **Task**: Integrate Mem0 for session context management
- **Status**: Active

### Recent Deployments
- `006d1e0` (2026-06-15): 376 pages, 12.0s build time

### Key Insights
- **Decision**: Self-hosted SQLite for Mem0 (no API costs, full control)
- **Bug Fix**: Mermaid syntax errors fixed (emojis removed, multi-line nodes collapsed)
- **Context**: Diagrams rebuild - HTML generation pipeline needs update

### Quick Navigation
- [Query Mem0](#query-mem0)
- [Recent Deployments](#recent-deployments)
- [Technical Insights](#technical-insights)

## Build
```
python3 build.py        # Generates 376 pages into dist/ (~12s)
```
No lint/typecheck — pure Python + Jinja2 static site. Cloudflare Pages auto-deploys on push to `main`.

## File Conventions
- **CSS**: `static/css/custom.css` — Tailwind + custom props; pillar colors layer variables (`--layer-*-body/strip/badge/accent`), section-collapse rules
- **Python**: `build.py` (~1700 lines). Core helpers in `core/` (`brand.py`, `visuals.py`). Jinja2 templates in `templates/`.
- **Templates**: `layout.j2` (base), `index.j2` (homepage), `category_index.j2` (research index), `pillar_index.j2` (pillar pages), `blog_post.j2` (article detail). Macros in `templates/macros/`.
- **JS**: `learning_hub.js` — reading progress bar, TOC scroll-spy, flashcards, quiz, section collapse (TOC link opens parent `<details>`), per-section IntersectionObserver progress tracking.

## Completed

### Phase 0 — Visual Differentiation of Content Types
- **0B**: `use_harvesters` expanded to all content types (research, learn, knowledge).
- **0C**: Learn/knowledge thumbnail scores default to `{}`; SQI bar rendered only when `"sqi"` key exists.
- **0D**: `section_type_color` types 3 & 6 use pillar palette instead of hardcoded gray.

### Phase 1 — UI Polish
- **1E**: `<body data-layer="{{ layer }}">` + background tints (`--layer-*-body`). Fixed layer default position (moved before `<body>`). Added 4px colored `layer-strip` fixed bar at page top.
- **1F**: Section collapse — each section wrapped in `<details open>`, heading inside `<summary>`, click to toggle. TOC links auto-open parent `<details>` via JS. Per-section IntersectionObserver progress tracking (`.section-read` class + checkmark).
- **1G**: `content_badge()` Jinja2 macro. `.content-type-badge` pill styles. Badges on homepage cards.

### Phase 2 — Per-Pillar Topic Icons with Brand SVGs
- Changed icon `<g>` from `fill="none" stroke="{accent}"` to `color="{accent}"` with per-element `fill="currentColor"` or `stroke="currentColor"`
- All 14 abstract icons (regulation, compliance, crypto, fraud, banking, semiconductor, ai, stock_market, startup, manufacturing, dna, quantum, brain, space, climate) updated to `fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"`
- Added 11 brand icons from Simple Icons: kafka, kubernetes, terraform, docker, python, postgresql, snowflake, git, github, apachespark, tensorflow, pytorch
- `BRAND_ICON_KEYWORDS` dict in `core/visuals.py` maps tech keywords to brand icon names; checked first by `_pick_subtopic()` before falling back to general subtopic matching
- SVG thumbnail `color` attribute set from `PILLAR_COLORS[pillar]["accent"]` — icons inherit pillar color
- Tree branching reduced to 3-4 children, depth capped to 3-5

### Fractal Bloat Fix (2026-06-12)
- **Tree branching**: `n = 1 + randint(2,3)` = 3-4 children/node (was `2 + randint(2,3)` = 4-5). Reduces node count ~2× at each level.
- **Tree depth**: `_det_rand_int(..., 3, 5)` (was `..., 4, 6`). Combined with branching fix, worst-case tree went from ~2372 lines + ~2252 circles per tree → ~457 lines + ~432 circles per tree (with mirror, from ~9248 total → ~902 total elements).
- Mirror mode retained for Sierpinski, Koch, and rings (compact fractals where doubling adds visual structure without bloat). Removed for dragon, fern, and hilbert.
- Build: ~12s (was 76s). Max thumbnail: 1063 lines (was 8364). Huge files (≥50KB): 12 (was 25). Small files (≤12KB): 56 (was 66).

### Research Card Pictograms + SQI Hiding (2026-06-12)
- **SQI removed** from cards (`pillar_index.j2`, `category_index.j2`), article header (`blog_post.j2`), and quality metrics section
- **`sqi-bar`/`sqi-bar-fill` CSS classes renamed** to `progress-bar`/`progress-bar-fill` (they were progress bars, not SQI display)
- **`pick_card_pictogram()`** function in `build.py` maps article tags to topic pictograms: `crypto.svg` (crypto/blockchain), `bayes.svg` (Bayesian/statistics), `dp.svg` (privacy/GDPR), `mosa.svg` (architecture/systems)
- Cards redesigned: left column widened from 56px to 84px, topic pictogram displayed with rounded corners + border + shadow, source badges below
- Fallback to `icon-research.svg` for articles without matching tags
- Registered as Jinja2 `pictogram` filter

## Remaining
- (none — all phases complete)

## Key Decisions
- `section_type_color()` is still used for left border color of section harvesters; `section_pattern_svg()` in `core/brand.py` is dead code (no longer called)
- Quality metrics (SQI meters, bloom charts, source bars, radars) removed from frontend — `_section_viz_svg()` and `section-viz` CSS removed
- All icon `<g>` wrappers use `color="{pal['accent']}"` (NOT `stroke="{accent}" fill="none"`) so both brand icons (`fill="currentColor"`) and abstract icons (`stroke="currentColor"`) correctly inherit the pillar accent color via `currentColor`
- Brand keyword matching uses `re.search(rf'(?<![a-z]){re.escape(kw)}(?![a-z])', text)` with word boundaries to avoid false positives (e.g., "tf" not matching "platform")
- `<details>`/`<summary>` for section collapse — zero-JS baseline, accessible; TOC links open parent via `learning_hub.js`
- `BRAND_ICON_KEYWORDS` checked before `SUBTOPIC_CATEGORIES` — specific tech names (Kafka, Docker, etc.) map directly to brand SVGs without disrupting general subtopic matching
- Layer strip (4px fixed bar at top) provides immediate content-type identity before user notices background tint
- `_pick_subtopic()` first checks brand keywords (word-boundary regex, any single match wins), then falls back to scoring-based subtopic matching
- `inject_section_images()` accepts full `AcaciaContent` object; `_article_as_dict()` helper for `generate_fallback_svg()` compatibility

## Relevant Files
- `core/visuals.py`: `TOPIC_ICONS` dict (14 abstract + 11 brand); `BRAND_ICON_KEYWORDS` dict; `_pick_subtopic()`; `generate_thumbnail_svg()`; `PILLAR_COLORS`
- `core/brand.py`: `section_pattern_svg()` — dead code; `section_type_color()` — still used for left border
- `static/css/custom.css`: layer strip rules, section collapse rules, section read progress, layer body tints
- `static/js/learning_hub.js`: `initSectionCollapse()`, `initSectionProgress()`

## Mem0 Integration
- **Location**: `services/mem0/`
- **Database**: `services/mem0/mem0.db` (SQLite)
- **CLI Tool**: `scripts/mem0_query.py`
- **Deployment Hook**: `scripts/mem0_log_deployment.py`
- **Commit Parser**: `scripts/mem0_extract_insights.py`
- **Admin UI**: `scripts/mem0_admin.py`

### Query Mem0
```bash
# Show recent deployments
python scripts/mem0_query.py --deployments

# Search sessions and insights
python scripts/mem0_query.py "diagrams rebuild"

# Show all insights
python scripts/mem0_query.py --insights
```

### Recent Deployments
| Commit | Status | Pages | Duration |
|--------|--------|-------|----------|
| 006d1e0 | ✅ | 376 | 12.0s |

### Technical Insights
| Type | Title | Tags |
|------|-------|------|
| decision | Mem0 Integration Strategy | mem0, architecture |
| bug_fix | Mermaid Syntax Errors | mermaid, syntax, fix |
| context | Current Task: Diagrams Rebuild | diagrams, mermaid |
| context | Project Stack | stack, architecture |

## Build
