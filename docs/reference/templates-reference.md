# Templates Reference

Jinja2 templates used to render all site pages.

## Template Hierarchy

```
layout.j2
├── index.j2                    # Homepage
├── research.j2                 # Research articles
├── learn.j2                    # Learn modules
├── knowledge.j2                # Knowledge base
├── blog_post.j2                # Cross-pillar content pages
├── pillar_index.j2             # Pillar landing pages
├── search.j2                   # Search page
├── graph.j2                    # Knowledge graph
├── tag_index.j2                # Tag archive pages
├── category_index.j2           # Category index pages
├── concept_detail.j2           # Ontology concept detail
├── review.j2                   # Content review page
├── review_queue.j2             # Review queue
├── knowledge_index.j2          # Knowledge index
├── learn_index.j2              # Learn index
├── aml_signals.j2              # Compliance signals dashboard
├── 404.j2                      # 404 page
└── admin/
    ├── base.html               # Admin layout (extends layout.j2)
    ├── login.html              # Admin login
    ├── dashboard.html          # Admin dashboard
    ├── quality.html            # SQI quality view
    ├── coverage.html           # Content coverage
    ├── articles.html           # Content inventory
    ├── gallery.html            # Thumbnail gallery
    ├── manifest.html           # Build manifest
    ├── pipeline.html           # Build pipeline
    ├── sources.html            # Source freshness
    ├── telemetry.html          # Plausible analytics
    └── ontology.html           # Ontology CRUD
```

## Key Templates

### `layout.j2`
Base layout with:
- Header + site navigation
- Footer
- Dark mode support
- Plausible analytics script inclusion
- Meta tags for SEO
- Content blocks: `{% block content %}`, `{% block head %}`, `{% block scripts %}`

### `research.j2`
- Extends `layout.j2`
- Blocks: `content`, `head`, `scripts`
- Context: `item`, `related_articles`, `section_images`, `cross_pillar`, `topic_icons`
- Features: SQI badge, reading time, difficulty, topic icons

### `learn.j2`
- Extends `layout.j2`
- Blocks: `content`, `head`, `scripts`
- Context: `item`, `flashcards`, `bloom_questions`, `prerequisites`
- Features: Bloom question accordion, flashcard toggles, code examples

### `knowledge.j2`
- Extends `layout.j2`
- Blocks: `content`, `head`, `scripts`
- Context: `item`, `concept_badges`, `further_reading`, `cross_pillar`
- Features: Concept badge pills, Further Reading links

### `pillar_index.j2`
- Extends `layout.j2`
- Context: `pillar`, `pillar_url`, `pillar_name`, `pillar_emoji`, `items`, `key_terms`
- Features: Content grouped by type, ontology concept cloud

### `graph.j2`
- Extends `layout.j2`
- Context: `cytograph_json`
- Features: Cytoscape.js with toolbar (pillar filter, relation filter, layout selector, search), node detail panel

### `admin/base.html`
- Extends `layout.j2`
- Blocks: `admin_content`
- Features: Sidebar navigation, active page highlighting, login state

### Template Macros

Located in `templates/macros/` and `templates/partials/`:
- Reusable card components
- Pillar badges
- SQI badge rendering
- Difficulty indicators
- Pagination

## Template Context

Global context passed to all templates:

| Variable | Source | Description |
|----------|--------|-------------|
| `site_name` | `config.py` | `"AcaciaFund"` |
| `site_url` | `config.py` | Production URL |
| `site_description` | `config.py` | Meta description |
| `pillar_names` | `config.py` | Pillar display names |
| `pillar_emojis` | `config.py` | Pillar emoji icons |
| `pillar_url_map` | `config.py` | Internal → URL mapping |
| `build_timestamp` | Build time | ISO timestamp |
| `plausible_domain` | `config.py` | Analytics domain (empty if disabled) |
