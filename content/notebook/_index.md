---
title: "📓 AcaciaFund Research Notebook"
date: 2026-05-20
layout: "notebook"
---

<div class="notebook">
<div class="cell">
  <div class="cell-header">
    <span class="exec">[1]</span>
    <span class="tag md">Markdown</span>
  </div>
  <div class="cell-content"># 📓 AcaciaFund Research Notebook

*Analiza danych z HackerNews i arXiv — kod źródłowy wizualizacji i przetwarzania.*

Ostatnia aktualizacja: `2026-05-20 20:59 UTC`  •  Posty: `6`  •  Punkty: `1903⭐`  •  Linki: `44`</div>
</div>
<div class="cell">
  <div class="cell-header">
    <span class="exec">[2]</span>
    <span class="tag code">Code</span>
  </div>
  <pre><code>import json, re, math
from collections import Counter
from datetime import datetime
from pathlib import Path

# SVG chart helpers
def donut(data): ...   # see source
def topic_bars(data): ...</code></pre>
</div>
<div class="cell">
  <div class="cell-header">
    <span class="exec">[3]</span>
    <span class="tag code">Code</span>
  </div>
  <pre><code>BASE_DIR = Path.cwd()
data = parse_content_files()  # ← reads content/daily/*/*.md

# Sample: latest entries
latest = [
  {"date": "2026-05-20", "score": 1028, "links": 8},
  {"date": "2026-05-20", "score": 723, "links": 13},
  {"date": "2026-05-20", "score": 152, "links": 8}
]
print(f'Total posts: {len(data)}')</code></pre>
</div>
<div class="cell">
  <div class="cell-header">
    <span class="exec">[4]</span>
    <span class="tag output">Output</span>
  </div>
  <div class="cell-content"><table style='font-size:.82rem'><tr><th>Pillar</th><th>Posts</th><th>Total ⭐</th><th>Links</th><th>Avg ⭐</th></tr><tr><td>🛡️ AML</td><td>2</td><td>1028</td><td>13</td><td>102.8</td></tr><tr><td>📈 Markets</td><td>2</td><td>723</td><td>18</td><td>51.6</td></tr><tr><td>🧬 Science</td><td>2</td><td>152</td><td>13</td><td>15.2</td></tr></table></div>
</div>
<div class="cell">
  <div class="cell-header">
    <span class="exec">[5]</span>
    <span class="tag code">Code</span>
  </div>
  <pre><code># Keyword-based classification (NLP heuristics)
# Each story is scored against pillar keyword sets

PILLAR_KEYWORDS = {
    'aml': ['aml', 'compliance', 'regtech', 'financial crime', 'kyc', 'money laundering'],
    'stock': ['semiconductor', 'supply chain', 'market', 'valuation', 'chip'],
    'science': ['mitochondria', 'cybernetics', 'complex systems', 'emergence'],
}}

def classify(story):
    text = (story['title'] + ' ' + story.get('url','')).lower()
    scores = {}
    for pillar, kws in PILLAR_KEYWORDS.items():
        score = sum(3 for kw in kws if kw in text)
        if score: scores[pillar] = score
    return scores</code></pre>
</div>
<div class="cell">
  <div class="cell-header">
    <span class="exec">[6]</span>
    <span class="tag code">Code</span>
  </div>
  <pre><code># Score distribution across pillars
totals = {p: sum(d['score_total'] for d in data[p]) for p in data}
print(totals)
donut_chart(totals)  # → SVG rendered below</code></pre>
</div>
<div class="cell">
  <div class="cell-header">
    <span class="exec">[7]</span>
    <span class="tag output">Output</span>
  </div>
  <div class="cell-content"><div class="chart-wrap" style="text-align:center"><h4>Rozkład punktów ⭐</h4><svg viewBox="0 0 240 180" xmlns="http://www.w3.org/2000/svg" style="max-width:100%;height:auto;font-family:Inter,system-ui,sans-serif"><path d="M120,90 L120.0,20.0 A70,70 0 1,1 102.5,157.8 Z" fill="#3B6999" opacity=".85"/>
<text x="214" y="102" text-anchor="middle" font-size="10" font-weight="600" fill="#3B6999">1028⭐</text>
<path d="M120,90 L102.5,157.8 A70,70 0 0,1 86.3,28.6 Z" fill="#C47F58" opacity=".85"/>
<text x="26" y="102" text-anchor="middle" font-size="10" font-weight="600" fill="#C47F58">723⭐</text>
<path d="M120,90 L86.3,28.6 A70,70 0 0,1 120.0,20.0 Z" fill="#9C6B8E" opacity=".85"/>
<text x="97" y="-2" text-anchor="middle" font-size="10" font-weight="600" fill="#9C6B8E">152⭐</text>
<circle cx="120" cy="90" r="35.0" fill="#fff"/>
<text x="120" y="94" text-anchor="middle" font-size="13" font-weight="700" fill="#0d1b2a">1903</text></svg></div></div>
</div>
<div class="cell">
  <div class="cell-header">
    <span class="exec">[8]</span>
    <span class="tag code">Code</span>
  </div>
  <pre><code># Keyword frequency analysis
themes = {p: Counter() for p in data}
for pillar, posts in data.items():
    for post in posts:
        themes[pillar].update(w.lower() for w in post['themes'])

topic_bars(themes)  # → SVG rendered below</code></pre>
</div>
<div class="cell">
  <div class="cell-header">
    <span class="exec">[9]</span>
    <span class="tag output">Output</span>
  </div>
  <div class="cell-content"><div class="chart-wrap"><h4>Top keywords per pillar</h4><svg viewBox="0 0 500 474" xmlns="http://www.w3.org/2000/svg" style="max-width:100%;height:auto;font-family:Inter,system-ui,sans-serif"><text x="4" y="12" font-size="11" font-weight="600" fill="#3B6999">🛡️ AML</text>
<text x="8" y="31" font-size="9" fill="#374151">skor</text>
<rect x="100" y="20" width="380" height="14" rx="2" fill="#3B6999" opacity=".7"/>
<text x="104" y="31" font-size="8" font-weight="500" fill="#fff">5</text>
<text x="8" y="49" font-size="9" fill="#374151">visa</text>
<rect x="100" y="38" width="380" height="14" rx="2" fill="#3B6999" opacity=".7"/>
<text x="104" y="49" font-size="8" font-weight="500" fill="#fff">5</text>
<text x="8" y="67" font-size="9" fill="#374151">mastercard</text>
<rect x="100" y="56" width="380" height="14" rx="2" fill="#3B6999" opacity=".7"/>
<text x="104" y="67" font-size="8" font-weight="500" fill="#fff">5</text>
<text x="8" y="85" font-size="9" fill="#374151">goodbye</text>
<rect x="100" y="74" width="228" height="14" rx="2" fill="#3B6999" opacity=".7"/>
<text x="104" y="85" font-size="8" font-weight="500" fill="#fff">3</text>
<text x="8" y="103" font-size="9" fill="#374151">europeans</text>
<rect x="100" y="92" width="228" height="14" rx="2" fill="#3B6999" opacity=".7"/>
<text x="104" y="103" font-size="8" font-weight="500" fill="#fff">3</text>
<text x="8" y="121" font-size="9" fill="#374151">trending</text>
<rect x="100" y="110" width="152" height="14" rx="2" fill="#3B6999" opacity=".7"/>
<text x="104" y="121" font-size="8" font-weight="500" fill="#fff">2</text>
<text x="4" y="170" font-size="11" font-weight="600" fill="#C47F58">📈 Markets</text>
<text x="8" y="189" font-size="9" fill="#374151">skor</text>
<rect x="100" y="178" width="380" height="14" rx="2" fill="#C47F58" opacity=".7"/>
<text x="104" y="189" font-size="8" font-weight="500" fill="#fff">5</text>
<text x="8" y="207" font-size="9" fill="#374151">college</text>
<rect x="100" y="196" width="304" height="14" rx="2" fill="#C47F58" opacity=".7"/>
<text x="104" y="207" font-size="8" font-weight="500" fill="#fff">4</text>
<text x="8" y="225" font-size="9" fill="#374151">preparing</text>
<rect x="100" y="214" width="228" height="14" rx="2" fill="#C47F58" opacity=".7"/>
<text x="104" y="225" font-size="8" font-weight="500" fill="#fff">3</text>
<text x="8" y="243" font-size="9" fill="#374151">students</text>
<rect x="100" y="232" width="228" height="14" rx="2" fill="#C47F58" opacity=".7"/>
<text x="104" y="243" font-size="8" font-weight="500" fill="#fff">3</text>
<text x="8" y="261" font-size="9" fill="#374151">drown</text>
<rect x="100" y="250" width="228" height="14" rx="2" fill="#C47F58" opacity=".7"/>
<text x="104" y="261" font-size="8" font-weight="500" fill="#fff">3</text>
<text x="8" y="279" font-size="9" fill="#374151">trending</text>
<rect x="100" y="268" width="152" height="14" rx="2" fill="#C47F58" opacity=".7"/>
<text x="104" y="279" font-size="8" font-weight="500" fill="#fff">2</text>
<text x="4" y="328" font-size="11" font-weight="600" fill="#9C6B8E">🧬 Science</text>
<text x="8" y="347" font-size="9" fill="#374151">skor</text>
<rect x="100" y="336" width="380" height="14" rx="2" fill="#9C6B8E" opacity=".7"/>
<text x="104" y="347" font-size="8" font-weight="500" fill="#fff">5</text>
<text x="8" y="365" font-size="9" fill="#374151">alignment</text>
<rect x="100" y="354" width="304" height="14" rx="2" fill="#9C6B8E" opacity=".7"/>
<text x="104" y="365" font-size="8" font-weight="500" fill="#fff">4</text>
<text x="8" y="383" font-size="9" fill="#374151">cybernetics</text>
<rect x="100" y="372" width="228" height="14" rx="2" fill="#9C6B8E" opacity=".7"/>
<text x="104" y="383" font-size="8" font-weight="500" fill="#fff">3</text>
<text x="8" y="401" font-size="9" fill="#374151">pretraining</text>
<rect x="100" y="390" width="228" height="14" rx="2" fill="#9C6B8E" opacity=".7"/>
<text x="104" y="401" font-size="8" font-weight="500" fill="#fff">3</text>
<text x="8" y="419" font-size="9" fill="#374151">discourse</text>
<rect x="100" y="408" width="228" height="14" rx="2" fill="#9C6B8E" opacity=".7"/>
<text x="104" y="419" font-size="8" font-weight="500" fill="#fff">3</text>
<text x="8" y="437" font-size="9" fill="#374151">trending</text>
<rect x="100" y="426" width="152" height="14" rx="2" fill="#9C6B8E" opacity=".7"/>
<text x="104" y="437" font-size="8" font-weight="500" fill="#fff">2</text></svg></div></div>
</div>
<div class="cell">
  <div class="cell-header">
    <span class="exec">[10]</span>
    <span class="tag md">Markdown</span>
  </div>
  <div class="cell-content">## Insights

Z analizy danych wyłaniają się następujące wzorce:

1. **Dominacja AML** — 1028⭐ to najwyższa suma, co odzwierciedla intensywność dyskursu regulacyjnego.
2. **Keywords cross-pillar** — tematy takie jak *cybernetics*, *systems*, *trending* pojawiają się we wszystkich trzech filarach, sugerując emergencję wspólnego języka systemowego.
3. **Rozkład aktywności** — większość punktów pochodzi z HackerNews; arXiv stanowi uzupełnienie o głębsze prace badawcze.</div>
</div>
<div class="cell">
  <div class="cell-header">
    <span class="exec">[11]</span>
    <span class="tag code">Code</span>
  </div>
  <pre><code># Export to JSON API
api_data = {
    'generated': datetime.now().isoformat(),
    'pillars': {p: [{'date': d['date'], 'score_total': d['score_total']}
                     for d in data[p]] for p in data}
}
Path('static/api/radar.json').write_text(json.dumps(api_data, indent=2))
print('API exported')</code></pre>
</div>
</div>

---

<p style="color:#999;font-size:.78rem">Notebook generowany automatycznie przez <code>generate_notebook.py</code>.
Zaprojektowany jako statyczny odpowiednik JupyterLab — kod Python i wygenerowane wizualizacje SVG w jednym widoku.</p>
