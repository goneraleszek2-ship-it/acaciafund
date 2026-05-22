---
title: "System"
draft: false
bg_image: ""
description: "Komponenty systemu AcaciaFund — modele, API i narzędzia"
image: ""
type: "teacher"
---

## Komponenty systemu

### NLP Engine
Klasyfikacja artykułów do 3 filarów z użyciem modelu TF-IDF + regresji logistycznej. Wagi istotności obliczane na podstawie punktacji HN, recency i dopasowania do profilu filara.

### Generator Bloom
Automatyczne generowanie pytań na 6 poziomów taksonomii Blooma dla każdej syntezy. Poziomy:
- 🟢 Zapamiętywanie — fakty, daty, definicje
- 🔵 Rozumienie — wyjaśnienie koncepcji
- 🟡 Stosowanie — zastosowanie w praktyce
- 🟠 Analiza — porównanie, kontrast
- 🔴 Ewaluacja — ocena, krytyka
- 🟣 Tworzenie — synteza nowych pomysłów

### Pipeline CI/CD
GitHub Actions cron co 6h → Hugo build → Cloudflare Pages deploy. Testy: 63 scenariuszy usability.

### API i źródła
- Algolia HN API (darmowy tier)
- arXiv API (OAI-PMH)
- Cloudflare Pages (hosting z edge caching)
