<div align="center">
  <img src="https://img.shields.io/badge/status-active-22c55e?style=flat-square" alt="Status">
  <img src="https://img.shields.io/badge/python-3.14+-3776AB?logo=python&logoColor=fff&style=flat-square" alt="Python">
  <img src="https://img.shields.io/badge/hugo-0.161+-FF4088?logo=hugo&logoColor=fff&style=flat-square" alt="Hugo">
  <img src="https://img.shields.io/badge/cloudflare-pages-F38020?logo=cloudflare&logoColor=fff&style=flat-square" alt="Cloudflare">
  <img src="https://img.shields.io/badge/tests-63%2F63-22c55e?style=flat-square" alt="Tests">
  <br>
  <img src="https://img.shields.io/badge/Bloom-Taxonomy-c9a84c?style=flat-square" alt="Bloom">
  <img src="https://img.shields.io/badge/theme-Educenter-2c3e6b?style=flat-square" alt="Theme">
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

Zobacz [Diagramy — architektura](https://acaciafund.org/diagrams/) dla wizualizacji. Generowane automatycznie przez `python generate_diagrams.py`.

```
HackerNews + arXiv → core/{fetch,analyze,generate}.py → content/pl/blog/ (Markdown)
                                                       → Hugo (Educenter theme)  
                                                       → Cloudflare Pages (CDN)
```

Zero external Python dependencies. Zero runtime backend.

### Pillars

| 📁 | Pillar | Topics | Posts |
|----|--------|--------|-------|
| 🛡️ | **AML** | Financial crime, compliance, regtech, sanctions | ~77 |
| 📈 | **Markets** | Semiconductors, valuation, supply chains | ~77 |
| 🧬 | **Science** | Cybernetics, complexity, systems theory | ~78 |

---

## 🔄 Pipeline

Every 6 hours (cron `0 */6 * * *`):

```
ingest.py          → fetch HN + ArXiv, classify, generate Markdown
core/bloom.py      → Bloom Taxonomy classification
generate_diagrams  → SVG diagrams dla /diagrams/
hugo build         → Educenter SSG → Cloudflare Pages deploy
```

**Stack**: Python 3.14+ stdlib (`urllib`, `tomllib`, `re`) · Hugo 0.161+ (Educenter theme) · Cloudflare Pages · GitHub Actions

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

## 🌐 Live Site

Strona dostępna pod [acaciafund.org](https://acaciafund.org/).

Educenter theme z Bootstrap 4, blog grid, kategorie, tagi, paginacja, i18n (pl), responsywny navbar.

---

## 🚀 Quick Start

```bash
git clone --recurse-submodules https://github.com/goneraleszek2-ship-it/acaciafund.git
cd acaciafund

python ingest.py        # fetch + analyze + generate
hugo serve              # local dev server
```

### Build for production

```bash
hugo --cleanDestinationDir
python tests/usability.py
```

---

## 👷 CI / Deploy

Workflow: `.github/workflows/daily-synthesis.yml`

```
cron: 0 */6 * * *  →  ingest → hugo build → commit → deploy (Cloudflare Pages)
```

| Trigger | Action |
|---------|--------|
| `schedule: 0 */6 * * *` | Full pipeline + deploy |
| `workflow_dispatch` | Manual run |
| `git push` | Trigger manual run |

**Secrets**:
- `CLOUDFLARE_API_TOKEN` + `CLOUDFLARE_ACCOUNT_ID` — for Pages deploy

---

## 🧪 Tests

```bash
python tests/usability.py
```

63 testy integracyjne sprawdzające strukturę strony, działanie tematów, kategorii, tagów, paginacji, stopki.

---

## 📂 Project Structure

```
├── core/                  # Python library (fetch, analyze, bloom, score, generate, data)
├── config/_default/       # Hugo config (hugo, languages, menus.pl, module)
├── content/pl/blog/       # 232 generated Markdown posts with Educenter frontmatter
├── layouts/               # Layout overrides (post, list, single, partials)
├── static/images/         # SVG thumbnails per category, logo, favicon
├── assets/scss/           # Custom SCSS overrides
├── data/pl/               # Homepage YAML data
├── i18n/                  # Polish translations
├── ingest.py              # Main pipeline entry point
├── generate_diagrams.py   # SVG diagram generator
├── tests/
│   └── usability.py       # 63 integration tests
├── themes/educenter/      # Git submodule
├── _vendor/               # Vendored Hugo modules
└── .github/workflows/     # CI — daily-synthesis.yml
```

---

## 📜 License

MIT — Leszek Gonera · AcaciaFund

<p align="center">
  <sub>Built with ⚡ no pip, no backend, no excuses</sub>
</p>
