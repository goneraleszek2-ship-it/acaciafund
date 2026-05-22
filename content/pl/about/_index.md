---
title: "O AcaciaFund"
date: 2026-01-01
draft: false
bg_image: ""
description: "Platforma codziennej syntezy badań — AML, rynki kapitałowe i nauka"
image: ""
type: "about"
---

AcaciaFund to platforma codziennej syntezy badań, która agreguje i klasyfikuje treści z HackerNews i arXiv w trzy filary: AML, rynki kapitałowe (Markets) i naukę (Science).

### Jak działa?

1. **Ingest** — codziennie o 07:00 CET system pobiera najnowsze submissiony z HackerNews i arXiv
2. **Klasyfikacja NLP** — model analizuje tytuł, treść i tagi, przypisując każdy artykuł do filara z wagą istotności
3. **Bloom Taxonomy** — do każdej syntezy generowane są pytania na 6 poziomach taksonomii Blooma, od zapamiętywania po tworzenie
4. **Publikacja** — gotowe posty są budowane przez Hugo i deployowane na Cloudflare Pages

### Dlaczego trzy filary?

| Filar | Cel |
|-------|-----|
| 🛡️ AML | Śledzenie zmian regulacyjnych, orzecznictwa i technologii w obszarze przeciwdziałania praniu pieniędzy |
| 📈 Markets | Makroekonomia, rynki kapitałowe, asset management i fintech |
| 🔬 Science | Przełomy w AI, biotechnologii, energetyce i naukach przyrodniczych |

### Technologia

- **Źródła**: Algolia HN API, arXiv OAI-PMH
- **NLP**: TF-IDF + regresja logistyczna (klasyfikacja), szablonowy generator Bloom
- **Frontend**: Hugo z theme Educenter, Bootstrap 4, SCSS
- **Hosting**: Cloudflare Pages (edge caching, auto-deploy z GitHub Actions cron co 6h)
- **Testy**: 63 scenariusze usability testów w Pythonie

### Open Source

Kod źródłowy dostępny na [GitHub](https://github.com/anomalyco/acaciafund). Zapraszamy do zgłaszania issues i pull requestów.
