---
title: "📊 Acacia Radar — Trendy i Połączenia"
date: 2026-05-20
layout: "radar"
---

*Ostatnia aktualizacja: 2026-05-20 20:16 UTC*

## 📈 Aktywność w czasie

Suma punktów (⭐) ze wszystkich znalezisk HackerNews w podziale na filary.

<canvas id="trendChart" width="800" height="350"></canvas>

## 🔗 Połączenia między filarami (Atlas)

Dni, w których ten sam temat pojawił się w dwóch lub trzech filarach jednocześnie.

<table style="width:100%;border-collapse:collapse">
<tr><th style='text-align:left;padding:8px;border-bottom:2px solid #1a1a2e'>Data</th><th style='text-align:left;padding:8px;border-bottom:2px solid #1a1a2e'>Połączenie</th><th style='text-align:left;padding:8px;border-bottom:2px solid #1a1a2e'>Wspólne tematy</th></tr>
<tr><td style='padding:8px;border-bottom:1px solid #ddd'>2026-05-17</td><td style='padding:8px;border-bottom:1px solid #ddd'>🛡️ + 📈</td><td style='padding:8px;border-bottom:1px solid #ddd'>trending, connections, skor, metaanalysis</td></tr>
<tr><td style='padding:8px;border-bottom:1px solid #ddd'>2026-05-17</td><td style='padding:8px;border-bottom:1px solid #ddd'>🛡️ + 🧬</td><td style='padding:8px;border-bottom:1px solid #ddd'>trending, connections, skor, metaanalysis</td></tr>
<tr><td style='padding:8px;border-bottom:1px solid #ddd'>2026-05-17</td><td style='padding:8px;border-bottom:1px solid #ddd'>📈 + 🧬</td><td style='padding:8px;border-bottom:1px solid #ddd'>trending, connections, skor, metaanalysis</td></tr>
<tr><td style='padding:8px;border-bottom:1px solid #ddd'>2026-05-20</td><td style='padding:8px;border-bottom:1px solid #ddd'>🛡️ + 📈</td><td style='padding:8px;border-bottom:1px solid #ddd'>domain, metaanaliza, raport, trending</td></tr>
<tr><td style='padding:8px;border-bottom:1px solid #ddd'>2026-05-20</td><td style='padding:8px;border-bottom:1px solid #ddd'>🛡️ + 🧬</td><td style='padding:8px;border-bottom:1px solid #ddd'>domain, metaanaliza, raport, trending</td></tr>
<tr><td style='padding:8px;border-bottom:1px solid #ddd'>2026-05-20</td><td style='padding:8px;border-bottom:1px solid #ddd'>📈 + 🧬</td><td style='padding:8px;border-bottom:1px solid #ddd'>domain, metaanaliza, raport, trending</td></tr>
</table>

## 🏷️ Dominujące tematy (ostatnie 30 dni)

### 🛡️ AML
<p><span class="tag" style="margin:2px;display:inline-block">skor</span> <span class="tag" style="margin:2px;display:inline-block">visa</span> <span class="tag" style="margin:2px;display:inline-block">mastercard</span> <span class="tag" style="margin:2px;display:inline-block">goodbye</span> <span class="tag" style="margin:2px;display:inline-block">trending</span> <span class="tag" style="margin:2px;display:inline-block">fintech</span> <span class="tag" style="margin:2px;display:inline-block">systems</span> <span class="tag" style="margin:2px;display:inline-block">antifragility</span> <span class="tag" style="margin:2px;display:inline-block">cybernetics</span> <span class="tag" style="margin:2px;display:inline-block">connections</span> <span class="tag" style="margin:2px;display:inline-block">europeans</span> <span class="tag" style="margin:2px;display:inline-block">cybersecurity</span></p>

### 📈 Markets
<p><span class="tag" style="margin:2px;display:inline-block">skor</span> <span class="tag" style="margin:2px;display:inline-block">college</span> <span class="tag" style="margin:2px;display:inline-block">preparing</span> <span class="tag" style="margin:2px;display:inline-block">students</span> <span class="tag" style="margin:2px;display:inline-block">drown</span> <span class="tag" style="margin:2px;display:inline-block">trending</span> <span class="tag" style="margin:2px;display:inline-block">nvidia</span> <span class="tag" style="margin:2px;display:inline-block">apple</span> <span class="tag" style="margin:2px;display:inline-block">systems</span> <span class="tag" style="margin:2px;display:inline-block">antifragility</span> <span class="tag" style="margin:2px;display:inline-block">cybernetics</span> <span class="tag" style="margin:2px;display:inline-block">connections</span></p>

### 🧬 Science
<p><span class="tag" style="margin:2px;display:inline-block">skor</span> <span class="tag" style="margin:2px;display:inline-block">cybernetics</span> <span class="tag" style="margin:2px;display:inline-block">alignment</span> <span class="tag" style="margin:2px;display:inline-block">pretraining</span> <span class="tag" style="margin:2px;display:inline-block">discourse</span> <span class="tag" style="margin:2px;display:inline-block">trending</span> <span class="tag" style="margin:2px;display:inline-block">systems</span> <span class="tag" style="margin:2px;display:inline-block">antifragility</span> <span class="tag" style="margin:2px;display:inline-block">connections</span> <span class="tag" style="margin:2px;display:inline-block">synergia</span> <span class="tag" style="margin:2px;display:inline-block">audio</span> <span class="tag" style="margin:2px;display:inline-block">znaleziska</span></p>

<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
<script>
const ctx = document.getElementById('trendChart').getContext('2d');
const data = {"labels": ["2026-05-17", "2026-05-20"], "datasets": [{"label": "\ud83d\udee1\ufe0f AML", "data": [0, 982], "borderColor": "#2E86AB", "backgroundColor": "#2E86AB20", "fill": true, "tension": 0.3}, {"label": "\ud83d\udcc8 Markets", "data": [0, 722], "borderColor": "#F18F01", "backgroundColor": "#F18F0120", "fill": true, "tension": 0.3}, {"label": "\ud83e\uddec Science", "data": [0, 156], "borderColor": "#A23B72", "backgroundColor": "#A23B7220", "fill": true, "tension": 0.3}]};
new Chart(ctx, {
  type: 'line',
  data: data,
  options: {
    responsive: true,
    plugins: { legend: { position: 'top' } },
    scales: {
      x: { ticks: { maxTicksLimit: 10 } },
      y: { beginAtZero: true, title: { display: true, text: '⭐ suma punków' } }
    }
  }
});
</script>

---
*Radar generowany automatycznie przez `generate_radar.py`.*
