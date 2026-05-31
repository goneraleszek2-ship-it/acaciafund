#!/usr/bin/env python3
"""AcaciaFund — generates SVG architecture/UML diagrams and a Hugo content page."""

from pathlib import Path

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "content" / "pl" / "diagrams"
OUTPUT_FILE = OUTPUT_DIR / "_index.md"


def svg_pipeline() -> str:
    """Component diagram: data pipeline architecture (current state)."""
    w, h = 820, 360
    def bx(x, y, w=160, h=44): return f"{x-w//2},{y-h//2} {x+w//2},{y-h//2} {x+w//2},{y+h//2} {x-w//2},{y+h//2}"

    return f'''<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" style="max-width:100%;height:auto;background:#fafafa;border-radius:8px;font-family:system-ui,sans-serif">
  <defs>
    <marker id="a" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6" fill="#555"/></marker>
    <marker id="ac" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6" fill="#2E86AB"/></marker>
  </defs>
  <rect x="10" y="10" width="800" height="340" rx="8" fill="none" stroke="#ccc" stroke-dasharray="4"/>
  <text x="410" y="34" text-anchor="middle" font-size="14" font-weight="bold" fill="#1a1a2e">AcaciaFund — Architecture &amp; Data Pipeline</text>

  <polygon points="{bx(90, 80)}" fill="#d4e6f1" stroke="#2E86AB"/>
  <text x="90" y="84" text-anchor="middle" font-size="11" fill="#1a1a2e">HackerNews</text>

  <polygon points="{bx(260, 80)}" fill="#d4e6f1" stroke="#2E86AB"/>
  <text x="260" y="84" text-anchor="middle" font-size="11" fill="#1a1a2e">arXiv API</text>

  <polygon points="{bx(440, 80)}" fill="#e8d4f0" stroke="#A23B72"/>
  <text x="440" y="84" text-anchor="middle" font-size="11" fill="#1a1a2e">core/fetch.py</text>

  <polygon points="{bx(620, 80)}" fill="#e8d4f0" stroke="#A23B72"/>
  <text x="620" y="84" text-anchor="middle" font-size="11" fill="#1a1a2e">core/analyze.py</text>

  <polygon points="{bx(140, 180)}" fill="#d5f5e3" stroke="#27ae60"/>
  <text x="140" y="184" text-anchor="middle" font-size="11" fill="#1a1a2e">Klasyfikacja NLP</text>

  <polygon points="{bx(320, 180)}" fill="#d5f5e3" stroke="#27ae60"/>
  <text x="320" y="184" text-anchor="middle" font-size="11" fill="#1a1a2e">Bloom Taxonomy</text>

  <polygon points="{bx(510, 180)}" fill="#d5f5e3" stroke="#27ae60"/>
  <text x="510" y="184" text-anchor="middle" font-size="11" fill="#1a1a2e">3× Markdown posty</text>

  <polygon points="{bx(700, 180)}" fill="#f9e79f" stroke="#f39c12"/>
  <text x="700" y="184" text-anchor="middle" font-size="11" fill="#1a1a2e">Hugo SSG</text>

  <polygon points="{bx(290, 280)}" fill="#f5b7b1" stroke="#c0392b"/>
  <text x="290" y="284" text-anchor="middle" font-size="11" fill="#1a1a2e">Git push → main</text>

  <polygon points="{bx(500, 280)}" fill="#f5b7b1" stroke="#c0392b"/>
  <text x="500" y="284" text-anchor="middle" font-size="11" fill="#1a1a2e">Cloudflare Pages</text>

  <line x1="170" y1="102" x2="360" y2="102" stroke="#555" stroke-width="1.5" marker-end="url(#a)"/>
  <text x="260" y="95" text-anchor="middle" font-size="9" fill="#888">Algolia API</text>

  <line x1="340" y1="102" x2="360" y2="102" stroke="#555" stroke-width="1" stroke-dasharray="3"/>
  <line x1="520" y1="102" x2="540" y2="102" stroke="#555" stroke-width="1.5" marker-end="url(#a)"/>

  <line x1="90" y1="124" x2="90" y2="158" stroke="#888" stroke-width="1.5" stroke-dasharray="4" marker-end="url(#ac)"/>
  <line x1="260" y1="124" x2="260" y2="158" stroke="#888" stroke-width="1.5" stroke-dasharray="4" marker-end="url(#ac)"/>
  <line x1="440" y1="124" x2="440" y2="158" stroke="#888" stroke-width="1.5" stroke-dasharray="4" marker-end="url(#ac)"/>
  <line x1="620" y1="124" x2="620" y2="158" stroke="#888" stroke-width="1.5" stroke-dasharray="4" marker-end="url(#ac)"/>

  <line x1="220" y1="202" x2="240" y2="202" stroke="#555" stroke-width="1.5" marker-end="url(#a)"/>
  <line x1="400" y1="202" x2="430" y2="202" stroke="#555" stroke-width="1.5" marker-end="url(#a)"/>
  <line x1="590" y1="202" x2="620" y2="202" stroke="#555" stroke-width="1.5" marker-end="url(#a)"/>

  <line x1="510" y1="224" x2="510" y2="258" stroke="#888" stroke-width="1.5" stroke-dasharray="4" marker-end="url(#ac)"/>
  <line x1="370" y1="258" x2="410" y2="258" stroke="#555" stroke-width="1.5" marker-end="url(#a)"/>
  <line x1="580" y1="258" x2="580" y2="302" stroke="#888" stroke-width="1.5" stroke-dasharray="4" marker-end="url(#ac)"/>

  <text x="105" y="155" text-anchor="middle" font-size="8" fill="#888">JSON</text>
  <text x="275" y="155" text-anchor="middle" font-size="8" fill="#888">JSON</text>
  <text x="700" y="220" text-anchor="middle" font-size="9" fill="#888">public/</text>
  <text x="400" y="278" text-anchor="middle" font-size="9" fill="#888">trigger CI</text>
</svg>'''


def svg_classify_flow() -> str:
    """UML activity diagram: how a story gets classified."""
    return '''<svg viewBox="0 0 520 340" xmlns="http://www.w3.org/2000/svg" style="max-width:100%;height:auto;background:#fafafa;border-radius:8px;font-family:system-ui,sans-serif">
  <defs>
    <marker id="b" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6" fill="#555"/></marker>
  </defs>
  <text x="260" y="24" text-anchor="middle" font-size="14" font-weight="bold" fill="#1a1a2e">Klasyfikacja — przepływ danych</text>

  <ellipse cx="260" cy="55" rx="100" ry="18" fill="#d5f5e3" stroke="#27ae60"/>
  <text x="260" y="60" text-anchor="middle" font-size="11" fill="#1a1a2e">Story z HN / arXiv</text>

  <line x1="260" y1="73" x2="260" y2="100" stroke="#555" stroke-width="1.5" marker-end="url(#b)"/>

  <polygon points="260,100 310,140 260,180 210,140" fill="#fde8c8" stroke="#F18F01"/>
  <text x="260" y="145" text-anchor="middle" font-size="10" fill="#1a1a2e">score &gt; 0?</text>

  <line x1="310" y1="140" x2="400" y2="140" stroke="#e74c3c" stroke-width="1.5" marker-end="url(#b)"/>
  <rect x="400" y="126" width="100" height="28" rx="4" fill="#fadbd8" stroke="#e74c3c"/>
  <text x="450" y="144" text-anchor="middle" font-size="10" fill="#1a1a2e">Odrzucone</text>
  <text x="350" y="135" text-anchor="middle" font-size="9" fill="#e74c3c">nie</text>

  <line x1="260" y1="180" x2="260" y2="215" stroke="#27ae60" stroke-width="1.5" marker-end="url(#b)"/>
  <text x="270" y="200" text-anchor="start" font-size="9" fill="#27ae60">tak</text>

  <rect x="180" y="215" width="160" height="28" rx="4" fill="#d5f5e3" stroke="#27ae60"/>
  <text x="260" y="233" text-anchor="middle" font-size="10" fill="#1a1a2e">Przypisz do filaru</text>

  <line x1="260" y1="243" x2="260" y2="270" stroke="#555" stroke-width="1.5" marker-end="url(#b)"/>

  <rect x="90" y="270" width="100" height="28" rx="4" fill="#d4e6f1" stroke="#2E86AB"/>
  <text x="140" y="288" text-anchor="middle" font-size="10" fill="#1a1a2e">🛡️ AML</text>
  <rect x="210" y="270" width="100" height="28" rx="4" fill="#d4e6f1" stroke="#2E86AB"/>
  <text x="260" y="288" text-anchor="middle" font-size="10" fill="#1a1a2e">📈 Markets</text>
  <rect x="330" y="270" width="100" height="28" rx="4" fill="#d4e6f1" stroke="#2E86AB"/>
  <text x="380" y="288" text-anchor="middle" font-size="10" fill="#1a1a2e">🧬 Science</text>

  <rect x="80" y="310" width="360" height="22" rx="4" fill="#f9e79f" stroke="#f39c12"/>
  <text x="260" y="325" text-anchor="middle" font-size="9" fill="#1a1a2e">content/pl/blog/ — Educenter frontmatter (category, tags, type: post)</text>
</svg>'''


def svg_atlas() -> str:
    """Cross-pillar Atlas: how connections are detected."""
    return '''<svg viewBox="0 0 520 280" xmlns="http://www.w3.org/2000/svg" style="max-width:100%;height:auto;background:#fafafa;border-radius:8px;font-family:system-ui,sans-serif">
  <text x="260" y="24" text-anchor="middle" font-size="14" font-weight="bold" fill="#1a1a2e">Cross-Pillar Atlas — wykrywanie połączeń</text>

  <circle cx="130" cy="130" r="68" fill="#2E86AB20" stroke="#2E86AB" stroke-width="2"/>
  <text x="130" y="125" text-anchor="middle" font-size="12" font-weight="bold" fill="#2E86AB">AML</text>
  <text x="130" y="142" text-anchor="middle" font-size="9" fill="#555">keywords</text>

  <circle cx="260" cy="80" r="68" fill="#F18F0120" stroke="#F18F01" stroke-width="2"/>
  <text x="260" y="75" text-anchor="middle" font-size="12" font-weight="bold" fill="#F18F01">Markets</text>
  <text x="260" y="92" text-anchor="middle" font-size="9" fill="#555">keywords</text>

  <circle cx="390" cy="130" r="68" fill="#A23B7220" stroke="#A23B72" stroke-width="2"/>
  <text x="390" y="125" text-anchor="middle" font-size="12" font-weight="bold" fill="#A23B72">Science</text>
  <text x="390" y="142" text-anchor="middle" font-size="9" fill="#555">keywords</text>

  <ellipse cx="200" cy="120" rx="35" ry="20" fill="#F18F0140" stroke="#F18F01" stroke-width="1.5" stroke-dasharray="3"/>
  <text x="200" y="124" text-anchor="middle" font-size="8" fill="#1a1a2e">AML∩Mkt</text>

  <ellipse cx="330" cy="120" rx="35" ry="20" fill="#A23B7240" stroke="#A23B72" stroke-width="1.5" stroke-dasharray="3"/>
  <text x="330" y="124" text-anchor="middle" font-size="8" fill="#1a1a2e">Mkt∩Sci</text>

  <ellipse cx="265" cy="165" rx="35" ry="20" fill="#2E86AB40" stroke="#2E86AB" stroke-width="1.5" stroke-dasharray="3"/>
  <text x="265" y="169" text-anchor="middle" font-size="8" fill="#1a1a2e">AML∩Sci</text>

  <ellipse cx="260" cy="127" rx="18" ry="14" fill="#55555540" stroke="#555" stroke-width="1" stroke-dasharray="2"/>
  <text x="260" y="131" text-anchor="middle" font-size="7" fill="#1a1a2e">All</text>

  <text x="260" y="240" text-anchor="middle" font-size="10" fill="#555">Te same słowa kluczowe pojawiające się tego samego dnia w ≥2 filarach → wpis w Atlas</text>
</svg>'''


def svg_theme_arch() -> str:
    """Educenter theme architecture: layouts, modules, config."""
    return '''<svg viewBox="0 0 720 280" xmlns="http://www.w3.org/2000/svg" style="max-width:100%;height:auto;background:#fafafa;border-radius:8px;font-family:system-ui,sans-serif">
  <defs>
    <marker id="c" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6" fill="#555"/></marker>
  </defs>
  <text x="360" y="24" text-anchor="middle" font-size="14" font-weight="bold" fill="#1a1a2e">Educenter Theme — struktura nadpisów</text>

  <rect x="30" y="40" width="200" height="32" rx="4" fill="#d4e6f1" stroke="#2E86AB"/>
  <text x="130" y="61" text-anchor="middle" font-size="11" fill="#1a1a2e">themes/educenter/ (submoduł)</text>

  <rect x="260" y="40" width="200" height="32" rx="4" fill="#e8d4f0" stroke="#A23B72"/>
  <text x="360" y="61" text-anchor="middle" font-size="11" fill="#1a1a2e">_vendor/ (hugo mod vendor)</text>

  <rect x="490" y="40" width="200" height="32" rx="4" fill="#d5f5e3" stroke="#27ae60"/>
  <text x="590" y="61" text-anchor="middle" font-size="11" fill="#1a1a2e">layouts/ (nadpisy)</text>

  <line x1="230" y1="56" x2="258" y2="56" stroke="#555" stroke-width="1" marker-end="url(#c)"/>
  <line x1="460" y1="56" x2="488" y2="56" stroke="#555" stroke-width="1" marker-end="url(#c)"/>

  <rect x="30" y="95" width="660" height="28" rx="4" fill="#f9e79f" stroke="#f39c12"/>
  <text x="360" y="113" text-anchor="middle" font-size="11" fill="#1a1a2e">Nadpisane: image.html, head.html, footer.html, post.html, list.html, single.html, page-header.html</text>

  <rect x="30" y="145" width="320" height="28" rx="4" fill="#d5f5e3" stroke="#27ae60"/>
  <text x="190" y="163" text-anchor="middle" font-size="11" fill="#1a1a2e">SVG miniaturki kategorii (static/images/)</text>

  <rect x="370" y="145" width="320" height="28" rx="4" fill="#d5f5e3" stroke="#27ae60"/>
  <text x="530" y="163" text-anchor="middle" font-size="11" fill="#1a1a2e">assets/scss/custom.scss</text>

  <rect x="30" y="195" width="660" height="28" rx="4" fill="#fadbd8" stroke="#e74c3c"/>
  <text x="360" y="213" text-anchor="middle" font-size="11" fill="#1a1a2e">config/_default/ → {hugo, languages, menus.pl, module}.toml</text>

  <rect x="30" y="245" width="660" height="28" rx="4" fill="#fadbd8" stroke="#e74c3c"/>
  <text x="360" y="263" text-anchor="middle" font-size="11" fill="#1a1a2e">i18n/pl.yaml · data/pl/homepage.yml · content/pl/{blog,about,contact,course,research,notice}</text>
</svg>'''


DIR_TREE = """```
acaciafund/
├── .github/workflows/daily-synthesis.yml   # CI/CD cron co 6h + deploy
├── ingest.py                                # Entrypoint: fetch → analyze → generate
├── generate_diagrams.py                     # Ten generator
├── config/_default/
│ ├── hugo.toml # Main configuration
│   ├── languages.toml                       # i18n (pl)
│   ├── menus.pl.toml                        # Menu główne + footer
│   └── module.toml                          # Hugo Modules (hugo-modules/images)
├── content/pl/blog/                         # 232 syntezy dzienne (Markdown)
├── layouts/
│   ├── _default/post.html                   # Nadpisy szablonów kart bloga
│   ├── _default/list.html                   # Nadpis listingu bloga
│   ├── _default/single.html                 # Nadpis detalu posta
│   ├── partials/image.html                  # Nadpis obrazka (fallback kategorii)
│   ├── partials/head.html                   # Custom CSS
│   ├── partials/footer.html                 # Czysta stopka
│   └── partials/page-header.html            # Fix bg_image
├── assets/scss/custom.scss                  # Customowe style (placeholdery, typografia)
├── static/images/
│   ├── aml-thumb.svg                        # Miniaturka AML
│   ├── markets-thumb.svg                    # Miniaturka Markets
│   ├── science-thumb.svg                    # Miniaturka Science
│   ├── logo.svg                             # Logo AcaciaFund
│   └── favicon.svg                          # Favicon
├── data/en/homepage.yml # Homepage configuration
├── i18n/en.yaml # Translations
├── core/
	│ ├── fetch.py # Fetching from HN + arXiv
│ ├── analyze.py # NLP Analysis
│ ├── generate.py # Post generation
│   ├── bloom.py                             # Bloom Taxonomy
│ ├── score.py # Article scoring
│ └── data.py # Path configuration
├── tests/usability.py                       # 63 testy E2E
├── themes/educenter/                        # Submoduł GIT
└── _vendor/                                 # Vendor Hugo Modules
```"""


def build_page() -> str:
    return f'''---
title: "Diagramy — architektura AcaciaFund"
date: 2026-05-22
draft: false
type: "about"
---

## 🏗️ Architektura systemu

Potok danych: źródła (HN + arXiv) → ingest.py (klasyfikacja NLP + Bloom Taxonomy) → Markdown posty → Hugo (Educenter theme) → Cloudflare Pages z domeną niestandardową.

<div>{svg_pipeline()}</div>

## 🔄 Przepływ klasyfikacji

Jak pojedyncza historia jest klasyfikowana do jednego z trzech filarów z frontmatterem Educenter.

<div>{svg_classify_flow()}</div>

## 🔗 Cross-Pillar Atlas

Wykrywanie połączeń między filarami na podstawie wspólnych słów kluczowych w tym samym dniu.

<div>{svg_atlas()}</div>

## 🎨 Struktura nadpisów Educenter

Jak działają nadpisy (layout overrides) względem motywu i modułów Hugo.

<div>{svg_theme_arch()}</div>

## 📁 Struktura repozytorium

{DIR_TREE}

---

*Diagramy generowane automatycznie przez `generate_diagrams.py`.*
'''


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(build_page(), encoding="utf-8")
    print(f"[+] Diagrams: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
