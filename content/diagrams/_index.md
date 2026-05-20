---
title: "Diagramy — architektura AcaciaFund"
date: 2026-05-20
layout: "diagrams"
---

## 🏗️ Architektura systemu

Potok danych: źródła (HN + arXiv) → ingest.py (klasyfikacja NLP) → generacja Radar → Hugo (SSG) → Cloudflare Pages.

<svg viewBox="0 0 720 280" xmlns="http://www.w3.org/2000/svg" style="max-width:100%;height:auto;background:#fafafa;border-radius:8px;font-family:system-ui,sans-serif">
  <defs>
    <marker id="a" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6" fill="#555"/></marker>
    <marker id="ac" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6" fill="#2E86AB"/></marker>
  </defs>
  <rect x="10" y="10" width="700" height="260" rx="8" fill="none" stroke="#ccc" stroke-dasharray="4"/>
  <text x="360" y="34" text-anchor="middle" font-size="14" font-weight="bold" fill="#1a1a2e">AcaciaFund — Architecture &amp; Data Pipeline</text>

  <!-- Top row: sources -->
  <polygon points="20,58 180,58 180,102 20,102" fill="#d4e6f1" stroke="#2E86AB"/>
  <text x="100" y="84" text-anchor="middle" font-size="12" fill="#1a1a2e">HackerNews</text>

  <polygon points="200,58 360,58 360,102 200,102" fill="#d4e6f1" stroke="#2E86AB"/>
  <text x="280" y="84" text-anchor="middle" font-size="12" fill="#1a1a2e">arXiv API</text>

  <polygon points="380,58 540,58 540,102 380,102" fill="#e8d4f0" stroke="#A23B72"/>
  <text x="460" y="84" text-anchor="middle" font-size="12" fill="#1a1a2e">Ingest.py</text>

  <polygon points="540,58 700,58 700,102 540,102" fill="#fde8c8" stroke="#F18F01"/>
  <text x="620" y="84" text-anchor="middle" font-size="12" fill="#1a1a2e">Radar Gen</text>

  <!-- Bottom row: classification → output -->
  <polygon points="20,168 180,168 180,212 20,212" fill="#d5f5e3" stroke="#27ae60"/>
  <text x="100" y="194" text-anchor="middle" font-size="11" fill="#1a1a2e">Klasyfikacja NLP</text>

  <polygon points="200,168 360,168 360,212 200,212" fill="#d5f5e3" stroke="#27ae60"/>
  <text x="280" y="194" text-anchor="middle" font-size="11" fill="#1a1a2e">3× Markdown</text>

  <polygon points="380,168 540,168 540,212 380,212" fill="#f9e79f" stroke="#f39c12"/>
  <text x="460" y="194" text-anchor="middle" font-size="11" fill="#1a1a2e">Hugo SSG</text>

  <polygon points="540,168 700,168 700,212 540,212" fill="#f5b7b1" stroke="#c0392b"/>
  <text x="620" y="194" text-anchor="middle" font-size="11" fill="#1a1a2e">CloudFlare Pages</text>

  <!-- arrows top row -->
  <line x1="150" y1="102" x2="230" y2="102" stroke="#555" stroke-width="1.5" marker-end="url(#a)"/>
  <line x1="330" y1="102" x2="410" y2="102" stroke="#555" stroke-width="1.5" marker-end="url(#a)"/>
  <line x1="510" y1="102" x2="570" y2="102" stroke="#555" stroke-width="1.5" marker-end="url(#a)"/>

  <!-- vertical connectors -->
  <line x1="100" y1="124" x2="100" y2="168" stroke="#888" stroke-width="1.5" stroke-dasharray="4" marker-end="url(#ac)"/>
  <line x1="280" y1="124" x2="280" y2="168" stroke="#888" stroke-width="1.5" stroke-dasharray="4" marker-end="url(#ac)"/>
  <line x1="460" y1="124" x2="460" y2="168" stroke="#888" stroke-width="1.5" stroke-dasharray="4" marker-end="url(#ac)"/>
  <line x1="620" y1="124" x2="620" y2="168" stroke="#888" stroke-width="1.5" stroke-dasharray="4" marker-end="url(#ac)"/>

  <!-- arrows bottom row -->
  <line x1="150" y1="212" x2="230" y2="212" stroke="#555" stroke-width="1.5" marker-end="url(#a)"/>
  <line x1="330" y1="212" x2="410" y2="212" stroke="#555" stroke-width="1.5" marker-end="url(#a)"/>
  <line x1="510" y1="212" x2="570" y2="212" stroke="#555" stroke-width="1.5" marker-end="url(#a)"/>

  <!-- labels -->
  <text x="180" y="120" text-anchor="middle" font-size="9" fill="#888">Algolia API</text>
  <text x="535" y="120" text-anchor="middle" font-size="9" fill="#888">generate_radar.py</text>
</svg>

## 🔄 Przepływ klasyfikacji

Jak pojedyncza historia jest klasyfikowana do jednego z trzech filarów.

<svg viewBox="0 0 520 320" xmlns="http://www.w3.org/2000/svg" style="max-width:100%;height:auto;background:#fafafa;border-radius:8px;font-family:system-ui,sans-serif">
  <defs>
    <marker id="b" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6" fill="#555"/></marker>
  </defs>
  <text x="260" y="24" text-anchor="middle" font-size="14" font-weight="bold" fill="#1a1a2e">Klasyfikacja — przepływ danych</text>

  <!-- start node -->
  <ellipse cx="260" cy="55" rx="100" ry="18" fill="#d5f5e3" stroke="#27ae60"/>
  <text x="260" y="60" text-anchor="middle" font-size="11" fill="#1a1a2e">Story z HN / arXiv</text>

  <line x1="260" y1="73" x2="260" y2="100" stroke="#555" stroke-width="1.5" marker-end="url(#b)"/>

  <!-- diamond: decision -->
  <polygon points="260,100 310,140 260,180 210,140" fill="#fde8c8" stroke="#F18F01"/>
  <text x="260" y="145" text-anchor="middle" font-size="10" fill="#1a1a2e">score &gt; 0?</text>

  <!-- no branch -->
  <line x1="310" y1="140" x2="400" y2="140" stroke="#e74c3c" stroke-width="1.5" marker-end="url(#b)"/>
  <rect x="400" y="126" width="100" height="28" rx="4" fill="#fadbd8" stroke="#e74c3c"/>
  <text x="450" y="144" text-anchor="middle" font-size="10" fill="#1a1a2e">Odrzucone</text>
  <text x="350" y="135" text-anchor="middle" font-size="9" fill="#e74c3c">nie</text>

  <!-- yes branch -->
  <line x1="260" y1="180" x2="260" y2="215" stroke="#27ae60" stroke-width="1.5" marker-end="url(#b)"/>
  <text x="270" y="200" text-anchor="start" font-size="9" fill="#27ae60">tak</text>

  <rect x="180" y="215" width="160" height="28" rx="4" fill="#d5f5e3" stroke="#27ae60"/>
  <text x="260" y="233" text-anchor="middle" font-size="10" fill="#1a1a2e">Przypisz do pilastra</text>

  <line x1="260" y1="243" x2="260" y2="270" stroke="#555" stroke-width="1.5" marker-end="url(#b)"/>

  <!-- three outputs -->
  <rect x="90" y="270" width="100" height="28" rx="4" fill="#d4e6f1" stroke="#2E86AB"/>
  <text x="140" y="288" text-anchor="middle" font-size="10" fill="#1a1a2e">🛡️ AML</text>
  <rect x="210" y="270" width="100" height="28" rx="4" fill="#d4e6f1" stroke="#2E86AB"/>
  <text x="260" y="288" text-anchor="middle" font-size="10" fill="#1a1a2e">📈 Markets</text>
  <rect x="330" y="270" width="100" height="28" rx="4" fill="#d4e6f1" stroke="#2E86AB"/>
  <text x="380" y="288" text-anchor="middle" font-size="10" fill="#1a1a2e">🧬 Science</text>
</svg>

## 🔗 Cross-Pillar Atlas

Wykrywanie połączeń między filarami na podstawie wspólnych słów kluczowych w tym samym dniu.

<svg viewBox="0 0 520 280" xmlns="http://www.w3.org/2000/svg" style="max-width:100%;height:auto;background:#fafafa;border-radius:8px;font-family:system-ui,sans-serif">
  <text x="260" y="24" text-anchor="middle" font-size="14" font-weight="bold" fill="#1a1a2e">Cross-Pillar Atlas — wykrywanie połączeń</text>

  <!-- three pillars as circles -->
  <circle cx="130" cy="130" r="68" fill="#2E86AB20" stroke="#2E86AB" stroke-width="2"/>
  <text x="130" y="125" text-anchor="middle" font-size="12" font-weight="bold" fill="#2E86AB">AML</text>
  <text x="130" y="142" text-anchor="middle" font-size="9" fill="#555">keywords</text>

  <circle cx="260" cy="80" r="68" fill="#F18F0120" stroke="#F18F01" stroke-width="2"/>
  <text x="260" y="75" text-anchor="middle" font-size="12" font-weight="bold" fill="#F18F01">Markets</text>
  <text x="260" y="92" text-anchor="middle" font-size="9" fill="#555">keywords</text>

  <circle cx="390" cy="130" r="68" fill="#A23B7220" stroke="#A23B72" stroke-width="2"/>
  <text x="390" y="125" text-anchor="middle" font-size="12" font-weight="bold" fill="#A23B72">Science</text>
  <text x="390" y="142" text-anchor="middle" font-size="9" fill="#555">keywords</text>

  <!-- intersections -->
  <ellipse cx="200" cy="120" rx="35" ry="20" fill="#F18F0140" stroke="#F18F01" stroke-width="1.5" stroke-dasharray="3"/>
  <text x="200" y="124" text-anchor="middle" font-size="8" fill="#1a1a2e">AML∩Mkt</text>

  <ellipse cx="330" cy="120" rx="35" ry="20" fill="#A23B7240" stroke="#A23B72" stroke-width="1.5" stroke-dasharray="3"/>
  <text x="330" y="124" text-anchor="middle" font-size="8" fill="#1a1a2e">Mkt∩Sci</text>

  <ellipse cx="265" cy="165" rx="35" ry="20" fill="#2E86AB40" stroke="#2E86AB" stroke-width="1.5" stroke-dasharray="3"/>
  <text x="265" y="169" text-anchor="middle" font-size="8" fill="#1a1a2e">AML∩Sci</text>

  <!-- center triple intersection -->
  <ellipse cx="260" cy="127" rx="18" ry="14" fill="#55555540" stroke="#555" stroke-width="1" stroke-dasharray="2"/>
  <text x="260" y="131" text-anchor="middle" font-size="7" fill="#1a1a2e">All</text>

  <!-- legend -->
  <text x="260" y="240" text-anchor="middle" font-size="10" fill="#555">Te same słowa kluczowe pojawiające się tego samego dnia w ≥2 filarach → wpis w Atlas</text>
</svg>

## 📁 Struktura repozytorium

```
acaciafund/
├── .github/workflows/daily-synthesis.yml   # CI/CD cron (08:00 UTC)
├── ingest.py                                # Źródła + klasyfikacja
├── generate_radar.py                        # Dashboard trendów
├── generate_diagrams.py                     # Ten generator
├── hugo.yaml                                # Konfiguracja Hugo
├── wrangler.jsonc                           # Cloudflare Pages
├── content/
│   └── daily/{aml,stock,science}/           # Syntezy dzienne (Markdown)
├── layouts/
│   ├── _default/{single,list}.html          # Szablony Hugo
│   ├── partials/{head,style}.html           # Współdzielone partiale
│   └── radar/, diagrams/                      # Niestandardowe layouty
├── static/
│   ├── manifest.json                        # PWA manifest
│   ├── sw.js                                # Service Worker
│   ├── icons/                               # Ikony PWA
│   └── api/radar.json                       # API endpoint
└── public/                                  # Wynik budowania
```

---

*Diagramy generowane automatycznie przez `generate_diagrams.py`.*
