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

## What’s new (summary)

- Learning Hub: interactive lessons, quizzes, and an in-browser Bayes demo (content/pl/learn/).
- Local-first learning UX: client-side quizzes and progress saved in localStorage (static/js/learning_hub.js).
- Shortcode for interactive Bayes demos: layouts/shortcodes/bayes.html + static/js/learning.js.
- Homepage UX polish: refined hero, call-to-action, pictograms and software stack diagram.
- FastAPI scaffold for future dynamic features: services/api/

---

## Quick Overview — Purpose & Structure

This project is built as a layered system that follows MOSA (Modular Open Systems Architecture):

1. Content Synthesis (Static-first)
   - Python ingestion and analysis produce markdown page bundles under content/pl/blog/.
   - Deterministic Bloom classification and SQI scoring make content educational and sortable.

2. Learning Layer (Interactive, privacy-first)
   - content/pl/learn/ contains lessons, demos and quizzes.
   - Client-side scripts render quizzes and track progress locally; server persistence is optional.

3. Service Scaffold & DevOps
   - services/api/ contains a minimal FastAPI service and Dockerfile for future features (user persistence, auth).
   - .devcontainer/ and docker-compose.yml provide a reproducible developer environment (Codespaces friendly).

---

## Project layout (essential)

```
./
├── services/api/          # FastAPI scaffold & Dockerfile
├── content/pl/blog/       # Static post bundles (Hugo Page Resources)
├── content/pl/learn/      # Learning Hub: lessons, demos, quizzes
├── layouts/               # Hugo layout overrides, shortcodes, partials
├── static/                # images, js (learning.js, learning_hub.js)
├── scripts/               # helper scripts (migration etc.)
├── .devcontainer/         # Codespaces devcontainer
├── docker-compose.yml     # local dev orchestration
└── .github/workflows/     # CI and scheduled pipeline
```

---

## Getting started (developer)

Prerequisites: Hugo (>=0.161), Python 3.11+, Docker (optional)

Local dev (fast):

```bash
git clone https://github.com/goneraleszek2-ship-it/acaciafund.git
cd acaciafund
hugo serve
```

Run synthesis pipeline (full):

```bash
python ingest.py   # fetch + analyze + generate content
hugo --cleanDestinationDir
```

Run tests (site-level synthetic checks):

```bash
hugo --cleanDestinationDir
python tests/usability.py
```

---

## Learning Hub — design intent

- Teach judgment over prediction: interactive Bayes demo to internalize belief updating.
- Privacy-first default: local-only progress and quizzes; opt-in server persistence later.
- Modular lessons: each lesson is a simple markdown file with optional quiz JSON embedded.

---

## Assessment & next steps

Current status: a working static site with an experimental, privacy-preserving learning layer and a clear path to a dynamic backend.

Recommended immediate work:

1. Implement server-side persistence (FastAPI + SQLite) and link to user identity (DIDs / key management) for sovereignty.
2. Expand the lesson catalogue and add authoring tools (simple admin UI or markdown frontmatter templates).
3. Add DP-enabled telemetry for aggregate learning analytics.

If you want, I can implement step 1 as the next PR (FastAPI endpoints + simple SQLite persistence and API calls from learning_hub.js).

---

## License

MIT — Leszek Gonera · AcaciaFund
