# Content Admin

Content admin pages provide inventory management and build pipeline visibility.

## Articles Page (`admin/articles.html`)

Full content inventory table with:
- **Slug** — Internal slug with link to live page
- **Title** — Content title
- **Type** — Research / Learn / Knowledge
- **Pillar** — Compliance / Markets / Data
- **SQI** — Badge-colored quality score
- **Status** — published / draft / review
- **Date** — Publication date
- **Actions** — (future: edit, delete, re-index)

Searchable and sortable by column.

## Gallery Page (`admin/gallery.html`)

Visual thumbnail grid of content items:
- Card with thumbnail (if available)
- Title overlay
- Pillar badge
- Content type badge
- Click to navigate to live page

## Manifest Page (`admin/manifest.html`)

Build manifest details:
- **Build version** — URL_STRUCTURE_VERSION
- **Generated at** — Build timestamp
- **Pages total** — Total HTML pages
- **Registry items** — Total items in registry
- **Skipped items** — Items skipped by incremental cache
- **Build time** — Wall-clock build time in seconds
- **SQI average** — Mean SQI across all items
- **SQI below threshold** — Items failing quality gate

Source: `dist/build-meta.json`

## Pipeline Page (`admin/pipeline.html`)

Build pipeline execution status:
- **Phase** — Current/previous phase
- **Duration** — Time per phase
- **Items processed** — Count per phase
- **Errors** — Error count per phase

Source: Build process logging (real-time during build).

> **See also:** [Admin Dashboard](admin-dashboard.md), [Build Pipeline Overview](../02-build-pipeline/build-overview.md)
