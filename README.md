<div align="center">
  <img src="https://img.shields.io/badge/status-active-22c55e?style=flat-square" alt="Status">
  <img src="https://img.shields.io/badge/python-3.14+-3776AB?logo=python&logoColor=fff&style=flat-square" alt="Python">
  <img src="https://img.shields.io/badge/hugo-0.161+-FF4088?logo=hugo&logoColor=fff&style=flat-square" alt="Hugo">
  <img src="https://img.shields.io/badge/cloudflare-pages-F38020?logo=cloudflare&logoColor=fff&style=flat-square" alt="Cloudflare">
  <img src="https://img.shields.io/badge/license-MIT-6366f1?style=flat-square" alt="License">
  <br>
  <img src="https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Facaciafund.pages.dev%2Fapi%2Farticles.json&query=%24.count&style=flat-square&label=syntezy&color=c9a84c" alt="Syntezy">
  <img src="https://img.shields.io/badge/Bloom-Taxonomy-c9a84c?style=flat-square" alt="Bloom">
  <img src="https://img.shields.io/badge/edu-widgets-2c3e6b?style=flat-square" alt="Edu Widgets">
</div>

<h1 align="center">
  🌳 AcaciaFund
</h1>

<p align="center">
  <strong>Automatyczny pipeline informacyjny</strong><br>
  <sup>Hacker News + ArXiv → synteza → analiza Bloom → edukacja</sup>
</p>

<p align="center">
  <a href="#-architecture">Architecture</a> ·
  <a href="#-pipeline">Pipeline</a> ·
  <a href="#-bloom-taxonomy">Bloom</a> ·
  <a href="#-learning-platform">Learning</a> ·
  <a href="#-quick-start">Quick Start</a>
</p>

---

## 📡 Architecture

```
┌──────────┐   ┌──────────┐   ┌───────────┐   ┌──────────┐   ┌────────────┐
│  Hacker   │   │  ArXiv   │   │  Python   │   │   Hugo   │   │ Cloudflare │
│   News    │──▶│  OAI-PMH │──▶│ Pipeline  │──▶│   SSG    │──▶│   Pages    │
│  (REST)   │   │  (API)   │   │  stdlib   │   │ 0.161+   │   │   (CDN)    │
└──────────┘   └──────────┘   └───────────┘   └──────────┘   └────────────┘
                                   │
                                   ▼
                            ┌──────────────┐
                            │  Static API  │
                            │  JSON files  │
                            └──────────────┘
```

Zero external Python dependencies. Zero runtime backend. Fully deterministic (or LLM-enhanced on demand).

### Pillars

| 📁 | Pillar | Topics | Articles |
|----|--------|--------|----------|
| 🛡️ | **AML** | Financial crime, compliance, regtech, sanctions | ~480 |
| 📈 | **Markets** | Semiconductors, valuation, supply chains | ~470 |
| 🧬 | **Science** | Cybernetics, complexity, systems theory | ~470 |

---

## 🔄 Pipeline

Every 6 hours (cron `0 */6 * * *`):

```
ingest.py         → fetch HN + ArXiv, parse, classify Bloom
generate_diagrams → mind maps (Graphviz)
generate_notebook → Jupyter-style notebooks
generate_metadata → /api/articles.json + /api/bloom.json
generate_quiz     → /api/quiz.json (591 questions)
generate_flashcards → /api/flashcards.json
┬ generate_llm    → LLM-enhanced quiz/flashcards (optional)
hugo build        → static site → deploy to Cloudflare
```

**Stack**: Python 3.14+ stdlib (`urllib`, `tomllib`, `re`) · Hugo · Cloudflare Pages · GitHub Actions

---

## 🧠 Bloom Taxonomy

Each article is classified into one of 6 cognitive levels using deterministic heuristics:

```
🟢 Remember   📝   recall, announce, launch, release
🟢 Understand 🧠   explain, guide, overview, basics, primer
🟡 Apply      🔧   implement, deploy, build, train, fine-tune
🟡 Analyze    🔍   analysis, benchmark, evaluate, compare
🟠 Evaluate   ⚖️   assess, audit, comply, regulatory, guideline  
🔴 Create     🚀   propose, design, develop, novel, framework
```

Classification uses keyword regex, source domain reputation, and HN points threshold. Deterministic and reproducible — no LLM required by default.

**Signal Quality Index (SQI)** scores each article on 6 dimensions: engagement, authority, novelty, timeliness, cross-pillar relevance, entity density.

---

## 🎓 Learning Platform

Built into the static site — all client-side JavaScript + localStorage:

### Widgets

| Widget | What | Tracks |
|--------|------|--------|
| 🧭 **Bloom Navigator** | Vertical pyramid sidebar per post | Active level highlighting |
| ✅ **Quiz Widget** | Self-assessment per Bloom level | Scores stored in `ac-quiz-*` |
| 📚 **Flashcard Deck** | Spaced repetition (7d/3d/1d) | Mastery in `ac-flashcards-*` |
| 📊 **Progress Dashboard** | `/learn/` — metrics, streak, bars | Aggregates all localStorage |
| 🧭 **Learning Paths** | 3 curated paths (AML/Markets/Science) | Step completion tracking |
| 🏆 **Achievements** | 14 unlockable badges | First quiz → 30-day streak |

### APIs

| Endpoint | Content |
|----------|---------|
| `/api/articles.json` | 231 posts, 1417 articles with Bloom metadata |
| `/api/bloom.json` | Aggregated stats per pillar |
| `/api/quiz.json` | 591 Bloom-level quiz questions |
| `/api/flashcards.json` | 11 entity-term flashcards |

---

## 🚀 Quick Start

```bash
# Clone
git clone https://github.com/goneraleszek2-ship-it/acaciafund.git
cd acaciafund

# Generate content
python ingest.py
python generate_quiz.py
python generate_flashcards.py
python generate_metadata.py

# Optional LLM enhancement
LLM_API_KEY=sk-... python3 generate_llm.py

# Build & serve
hugo serve
```

### Environment

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_API_KEY` | — | OpenAI-compatible API key (optional) |
| `LLM_MODEL` | `gpt-4o-mini` | Model for LLM generation |
| `LLM_MAX_POSTS` | `50` | Max posts to process with LLM |
| `LLM_API_URL` | OpenAI endpoint | Custom API endpoint |

---

## 📂 Project Structure

```
├── core/                  # Python library (fetch, analyze, bloom, score, data)
├── etc/
│   └── pillars.toml       # Pillars, domains, entities, source tiers, learning paths
├── content/
│   └── daily/{aml,stock,science}/  # Generated markdown posts
├── layouts/               # Hugo templates (index, list, single, partials)
├── static/api/            # Generated JSON APIs
├── generate_*.py          # CLI generators
├── ingest.py              # Main pipeline entry point
└── .github/workflows/     # CI — daily-synthesis.yml
```

---

## 📜 License

MIT — Leszek Gonera · AcaciaFund

<p align="center">
  <sub>Built with ⚡ no pip, no backend, no excuses</sub>
</p>
