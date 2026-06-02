<div align="center">
  <img src="https://img.shields.io/badge/status-active-22c55e?style=flat-square" alt="Status">
  <img src="https://img.shields.io/badge/python-3.11+-3776AB?logo=python&logoColor=fff&style=flat-square" alt="Python">
  <img src="https://img.shields.io/badge/cloudflare-pages-F38020?logo=cloudflare&logoColor=fff&style=flat-square" alt="Cloudflare">
</div>

# AcaciaFund

Automated research synthesis and an experimental learning ecosystem.

HackerNews + arXiv → deterministic classification (Bloom taxonomy) → static site (Python-native) → interactive learning layer.

---

## What's New (Summary)

- **Python-native Headless Static Generator**: Replaced Astro/Node.js with a data-driven Python architecture (orchestrator + generator + Jinja2 template)
- **Learning Hub**: Interactive lessons, quizzes, and an in-browser Bayes demo (content/learn/)
- **Local-first Learning UX**: Client-side quizzes with progress saved in localStorage (static/js/learning_hub.js)
- **Interactive Bayes Demo Shortcode**: static/js/learning.js
- **Homepage UX Enhancement**: Refined hero section, call-to-action, pictograms and software stack diagram
- **Accessibility Improvements**: Proper heading structure (H1→H2→H3), skip-to-content link, ARIA labels, lang attribute
- **Zero Client-Side JavaScript for Content**: Only CSS/Tailwind CDN used for styling; no JS required to read content
- **Deployed via Cloudflare Pages**: Fully static site with automatic deployments

---

## Architecture Overview

AcaciaFund now follows a **Data-as-the-App** pattern with three core layers:

### 1. Data Engine (Python)
- `ingest.py`: Fetches and processes HackerNews and arXiv content
- `orchestrator.py`: Converts Markdown content to structured `registry.json` (single source of truth)
- Uses Pydantic for data validation before rendering

### 2. Rendering Shell (Immutable)
- `generator.py`: Reads `registry.json` and renders content using Jinja2 template
- `templates/layout.j2`: Single HTML template using Tailwind CSS CDN
- Produces static HTML in `dist/` directory

### 3. Deployment
- `deploy.sh`: Orchestrates full pipeline (ingest → orchestrator → generator → deploy)
- Deploys to Cloudflare Pages via Wrangler

---

## Project Structure

```
.
├── content/                  # Source Markdown files (blog, lessons, etc.)
├── dist/                     # Generated static site (output)
├── registry.json             # Generated data file (single source of truth)
├── schemas.py                # Pydantic models defining content schema
├── orchestrator.py           # Parses Markdown and writes registry.json
├── generator.py              # Renders registry.json to static HTML
├── templates/                # Jinja2 templates (layout.j2)
├── static/                   # Static assets (CSS, JS, images)
├── deploy.sh                 # Deployment script: orchestrates pipeline
├── .env                      # Environment variables (Wrangler API token)
└── README.md                 # This file
```

---

## Developer Guide

### Prerequisites
- Python 3.11+
- Wrangler (for Cloudflare Pages deployment)
- Git

### Local Development (Quick Start)

```bash
git clone https://github.com/yourusername/acaciafund.git
cd acaciafund
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt  # or install via apt: python3-markdown python3-pydantic python3-jinja2
```

### Full Synthesis Pipeline

```bash
# Fetch and process new content (optional)
python ingest.py

# Convert Markdown to structured data
python orchestrator.py

# Generate static HTML
python generator.py

# Preview locally (optional)
python -m http.server 8000 --dir dist

# Deploy to Cloudflare Pages
./deploy.sh
```

### Requirements

Create a `requirements.txt` with:
```
markdown2
pydantic
jinja2
```

Or install via system packages:
```bash
apt-get install python3-markdown2 python3-pydantic python3-jinja2
```

---

## Learning Hub — Design Principles

- **Judgment Over Prediction**: Interactive Bayes demo develops belief updating intuition
- **Privacy-First Approach**: Default local-only storage; server persistence available as opt-in
- **Modular Lessons**: Each lesson is a standalone markdown file with optional embedded quiz JSON
- **Accessibility**: All content accessible without JavaScript; proper heading structure and ARIA labels

---

## Strategic Assessment & Recommended Priorities

**Current State**: Production-ready static site featuring an experimental, privacy-preserving learning layer with a defined path toward dynamic backend capabilities.

**Immediate Focus Areas**:

1. **Performance Optimization**: 
   - Implement image optimization (WebP, lazy loading)
   - Add CSS purging for Tailwind
   - Enable Cloudflare caching and Polish

2. **Analytics Framework**: 
   - Deploy differential privacy-enabled telemetry for aggregated learning insights
   - Add basic pageview analytics (Plausible or Umami)

3. **Content Enrichment**: 
   - Generate lightweight SVG graphics based on post tags/metadata
   - Add interactive elements to lessons (only where beneficial)

4. **i18n Foundation**: 
   - Prepare structure for multilingual content (though English-only per current requirements)

5. **CI/CD Pipeline**: 
   - Set up GitHub Actions for automated testing and deployment on PRs

---

## Accessibility Compliance

The site adheres to WCAG 2.1 AA standards:
- Proper heading hierarchy (H1 → H2 → H3)
- Skip-to-content link
- ARIA labels on interactive elements
- Language attribute set on HTML element
- Sufficient color contrast (via Tailwind CSS)
- All images have alt text
- No reliance on JavaScript for content consumption

---

## Licensing

MIT License — Leszek Gonera · AcaciaFund
