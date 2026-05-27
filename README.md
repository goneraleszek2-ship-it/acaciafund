<div align="center">
  <img src="https://img.shields.io/badge/status-active-22c55e?style=flat-square" alt="Status">
  <img src="https://img.shields.io/badge/python-3.11+-3776AB?logo=python&logoColor=fff&style=flat-square" alt="Python">
  <img src="https://img.shields.io/badge/hugo-0.161+-FF4088?logo=hugo&logoColor=fff&style=flat-square" alt="Hugo">
  <img src="https://img.shields.io/badge/cloudflare-pages-F38020?logo=cloudflare&logoColor=fff&style=flat-square" alt="Cloudflare">
</div>

# AcaciaFund

Automated research synthesis and an experimental learning ecosystem.

HackerNews + arXiv → deterministic classification (Bloom taxonomy) → static site (Hugo) → interactive learning layer.

---

## What's New (Summary)

- **Learning Hub**: Interactive lessons, quizzes, and an in-browser Bayes demo (content/pl/learn/)
- **Local-first Learning UX**: Client-side quizzes with progress saved in localStorage (static/js/learning_hub.js)
- **Interactive Bayes Demo Shortcode**: layouts/shortcodes/bayes.html + static/js/learning.js
- **Homepage UX Enhancement**: Refined hero section, call-to-action, pictograms and software stack diagram
- **FastAPI Scaffold**: services/api/ for future dynamic features
- **UX 2026 Improvements**: Dark mode toggle, skip‑to‑content link, AI transparency note, category badges + reading time, hover/button micro‑interactions, fade‑in scroll animations, client‑side search (JSON API + overlay) – all deployed via Cloudflare Pages.

## Further Steps

1. **Performance & Accessibility**: Run Lighthouse, optimize images (WebP), improve contrast, add reading‑progress bar.
2. **Navigation Enhancements**: Sticky header that hides on scroll down, breadcrumbs on category/tag pages.
3. **Content Enrichment**: Generate lightweight SVG graphics based on post tags/metadata (e.g., decorative badges, sparklines) to increase visual richness without extra weight.
4. **Search Refinement**: Implement fuzzy matching, boost recent content, and add keyboard navigation.
5. **Analytics Framework**: Deploy differential privacy‑enabled telemetry for aggregated learning insights (per strategic assessment).
6. **Server‑Side Persistence**: Implement FastAPI + SQLite backend for learning progress (as recommended in the strategic assessment).

---

## Overview — Purpose & Structure

AcaciaFund follows a Modular Open Systems Architecture (MOSA) with three core layers:

### 1. Content Synthesis (Static-first)
- Python ingestion engine processes HackerNews and arXiv content
- Deterministic Bloom taxonomy classification and SQI scoring create educational, sortable content
- Generated as markdown page bundles under content/pl/blog/

### 2. Learning Layer (Interactive, Privacy-first)
- Located in content/pl/learn/: lessons, demonstrations, and quizzes
- Client-side rendering with localStorage progress tracking (optional server persistence)
- Privacy-focused design: data remains local by default

### 3. Service Infrastructure & DevOps
- services/api/: Minimal FastAPI service with Dockerfile for future features
- .devcontainer/ and docker-compose.yml: Reproducible development environment (Codespaces compatible)
- .github/workflows/: CI/CD pipeline for automated synthesis and deployment

---

## Project Structure

```
./
├── services/api/          # FastAPI backend & Docker configuration
├── content/pl/blog/       # Hugo page bundles (research syntheses)
├── content/pl/learn/      # Learning Hub: lessons, demos, assessments
├── layouts/               # Custom Hugo layouts, shortcodes, partials
├── static/                # Assets: images, JavaScript (learning.js, learning_hub.js)
├── scripts/               # Utility scripts (migration, maintenance)
├── .devcontainer/         # Development container configuration
├── docker-compose.yml     # Local development orchestration
└── .github/workflows/     # GitHub Actions: CI/CD and scheduled pipelines
```

---

## Developer Guide

### Prerequisites
- Hugo (version 0.161 or newer)
- Python 3.11+
- Docker (optional, for API service)

### Local Development (Quick Start)

```bash
git clone https://github.com/goneraleszek2-ship-it/acaciafund.git
cd acaciafund
hugo serve
```

### Full Synthesis Pipeline

```bash
python ingest.py   # Execute: fetch → analyze → generate content
hugo --cleanDestinationDir
```

### Testing

```bash
hugo --cleanDestinationDir
python tests/usability.py
```

---

## Learning Hub — Design Principles

- **Judgment Over Prediction**: Interactive Bayes demo develops belief updating intuition
- **Privacy-First Approach**: Default local-only storage; server persistence available as opt-in
- **Modular Lessons**: Each lesson is a standalone markdown file with optional embedded quiz JSON

---

## Strategic Assessment & Recommended Priorities

**Current State**: Production-ready static site featuring an experimental, privacy-preserving learning layer with a defined path toward dynamic backend capabilities.

**Immediate Focus Areas**:

1. **Server-Side Persistence**: Implement FastAPI + SQLite backend with user identity management (DIDs/key management) for data sovereignty
2. **Learning Content Expansion**: Broaden lesson catalog and create authoring tools (admin interface or markdown templates)
3. **Analytics Framework**: Deploy differential privacy-enabled telemetry for aggregated learning insights

**Next PR Recommendation**: I can deliver the server-side persistence layer (FastAPI endpoints with SQLite storage and corresponding learning_hub.js API integration) as the immediate next step.

---

## Licensing

MIT License — Leszek Gonera · AcaciaFund
# Language routing update
