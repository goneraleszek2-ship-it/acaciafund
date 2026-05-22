---
title: "Badania"
draft: false
bg_image: ""
description: "Metodologia syntezy badań — potok danych, klasyfikacja NLP i Bloom Taxonomy"
image: ""
type: "research"
---

## Metodologia

AcaciaFund stosuje zautomatyzowany potok NLP do codziennej syntezy badań z HackerNews i arXiv.

### Potok danych

1. **Ingest** — scraping API HackerNews i arXiv (submissions z ostatnich 24h)
2. **Klasyfikacja** — model NLP przypisuje każdy artykuł do jednego z 3 filarów (AML, Markets, Science) z wagą istotności
3. **Bloom Taxonomy** — do każdego posta generowane są pytania na 6 poziomach taksonomii Blooma (zapamiętywanie, rozumienie, stosowanie, analiza, ewaluacja, tworzenie)
4. **Generowanie** — synteza w formacie Markdown z podsumowaniem, pytaniami i fiszkami

### Filtry

| Filar | Zakres | Źródła |
|-------|--------|--------|
| 🛡️ AML | przeciwdziałanie praniu pieniędzy, compliance, regtech, sankcje, financial crime | HN, arXiv |
| 📈 Markets | rynki kapitałowe, makroekonomia, asset management, fintech | HN |
| 🔬 Science | AI, biotech, energia, fizyka, nauki przyrodnicze | HN, arXiv |

### Linki

- [Blog — syntezy AML](/pl/blog/categories/aml/)
- [Blog — syntezy Markets](/pl/blog/categories/markets/)
- [Blog — syntezy Science](/pl/blog/categories/science/)
- [Diagramy architektury](/pl/diagrams/)
