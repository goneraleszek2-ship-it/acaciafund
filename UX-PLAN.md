# UX Evolution Plan 2026 — AcaciaFund

## 2026 UX Trends — Key Takeaways

Research (Lyssna, Envato, NNG, Forrester) identyfikuje główne kierunki:

| Trend | Waga dla nas |
|-------|-------------|
| **Strategic Minimalism** — każdy element ma cel, brak dekoracji | 🔴 krytyczne |
| **Micro-interactions & Motion** — subtelne animacje, feedback | 🟡 wysokie |
| **Accessibility First** — WCAG, kontrast, klawiatura, czytniki | 🔴 krytyczne |
| **AI Transparency** — oznaczanie treści generowanych przez AI | 🟡 wysokie |
| **Performance UX** — szybkość ładowania, Core Web Vitals | 🔴 krytyczne |
| **Typography-led Design** — typografia jako główny nośnik hierarchii | 🟡 wysokie |
| **Generative UI / Adaptive** — interfejs dopasowujący się do kontekstu | 🟢 średnie |
| **Privacy-first** — minimalna ilość danych, przejrzystość | 🟢 średnie |
| **Paper-like UI** — płaskie, lekkie interfejsy z dobrą czytelnością | 🟡 wysokie |

---

## Faza 1: Fundament (P0 — teraz)

### 1.1 Accessibility
- [ ] Link „Przejdź do treści" (skip-to-content) — pierwszy element po `<body>`
- [ ] `lang="pl-pl"` już jest, OK
- [ ] Kontrast kolorów — sprawdzić `card-title #0d1b2a` na białym tle (ratio ~15:1, OK)
- [ ] Focus indicators dla klawiatury (Bootstrap domyślnie dodaje `:focus` — upewnić się)
- [ ] `alt` texty dla miniaturek kategorii — już są dynamiczne z tytułem posta, OK
- [ ] `aria-label` dla linków „Czytaj dalej" (powinien zawierać tytuł posta)
- [ ] Obsługa `prefers-reduced-motion` w CSS dla animacji

### 1.2 Typography
- [ ] System font stack zamiast domyślnego Bootstrap font-family
  ```scss
  $font-family-base: 'Inter', system-ui, -apple-system, sans-serif;
  ```
- [ ] Płynna skala typografii (clamp()) dla tytułów
  ```scss
  h1 { font-size: clamp(1.75rem, 4vw, 2.5rem); }
  ```
- [ ] `line-height: 1.6` dla treści, `1.3` dla tytułów
- [ ] Maksymalna szerokość kolumny treści: `max-width: 70ch`

### 1.3 Performance
- [ ] Lazy loading dla wszystkich obrazów — już `loading="lazy"`, OK
- [ ] Inline critical CSS zamiast zewnętrznych blokujących renderowanie
- [ ] Usunąć nieużywane pluginy CSS/JS (slick, venobox, filterizr, gmap)
- [ ] Preconnect do zewnętrznych domen (Google Fonts jeśli używane)

### 1.4 AI Transparency
- [ ] Dodać znacznik w stopce: „Treści generowane przez system NLP AcaciaFund"
- [ ] Dodać badge „AI-generated" lub „Synteza automatyczna" na kartach bloga

---

## Faza 2: Tożsamość (P1 — tydzień 1)

### 2.1 Color System
- [ ] Zdefiniować własną paletę kolorów zamiast domyślnej Educenter
  - Primary: deep navy `#0f172a` → `#1e3a5f`
  - Accent: amber/gold `#d97706`  
  - Surface: white + `#f8fafc`
  - Text: `#0f172a` na jasnym, `#f1f5f9` na ciemnym
- [ ] Dark mode support (`prefers-color-scheme: dark`)
- [ ] CSS custom properties (`--color-primary`, `--color-text`, etc.)

### 2.2 Logotyp
- [ ] Obecny SVG logo jest OK, ale można dodać wariant z ikoną (drzewo akacja)
- [ ] Favicon: obecny SVG z literą „A" — OK na start, można dodać warianty

### 2.3 Typography System
- [ ] Wybrać font: Inter (bezpieczny, dobrze czyta się na ekranie)
- [ ] Zdefiniować skalę: 12/14/16/18/20/24/32/40/48
- [ ] Monospace dla kodu: JetBrains Mono lub systemowy

---

## Faza 3: Interakcje (P1 — tydzień 2)

### 3.1 Micro-interactions
- [ ] Subtelny hover na kartach bloga (scale + shadow) — Educenter już ma `hover-shadow`
- [ ] Smooth page transitions (fade-in przy scrollu — Intersection Observer lub CSS `@keyframes`)
- [ ] Link hover underline animation (slide-in)
- [ ] Button press feedback (subtle scale)
- [ ] Progress bar czytania posta (scroll progress)

### 3.2 Navigation
- [ ] Sticky header z ukrywaniem przy scrollu w dół (Educenter już ma `fixed-top`)
- [ ] Breadcrumbs na stronach kategorii i tagów
- [ ] Search (client-side, z indeksem JSON dla postów)
- [ ] Filter by category na blogu (tagi jako checkboxy)

### 3.3 Blog Cards
- [ ] Category badge na karcie (kolorowy, np. niebieski dla AML, zielony dla Markets, fioletowy dla Science)
- [ ] Reading time estimate („3 min czytania")
- [ ] Data w formacie względnym („2 dni temu") — opcjonalnie, bo data bezwzględna też OK
- [ ] Hover state: delikatne podniesienie karty

---

## Faza 4: Treść (P2 — tydzień 3)

### 4.1 Single Post
- [ ] Table of Contents (automatyczny z nagłówków)
- [ ] Social share buttons (Twitter/X, LinkedIn, email)
- [ ] „Następny / poprzedni artykuł" nawigacja
- [ ] Powiązane artykuły (na podstawie tagów/kategorii)
- [ ] Reading progress bar

### 4.2 Author Section
- [ ] Profil autora na dole posta (obecnie tylko link `/author/acaciafund`)
- [ ] Strona autora z listą jego postów (Educenter ma layout `author/single.html`)

### 4.3 Diagrams Page
- [ ] Lepsze responsive SVG (na mobile diagramy są małe)
- [ ] Interaktywne diagramy (tooltipy, klikalne elementy)

---

## Faza 5: Zaawansowane (P2 — tydzień 4)

### 5.1 Dark Mode
- [ ] CSS custom properties dla light/dark
- [ ] Przełącznik w navbarze
- [ ] Persist preference w localStorage

### 5.2 Search
- [ ] Indeks JSON generowany przez Pythona (`static/api/posts.json`)
- [ ] Client-side search z Fuse.js lub natywnym `Intl.Collator`
- [ ] Wyniki wyszukiwania jako overlay

### 5.3 Performance Optimization
- [ ] Audyt Lighthouse, Core Web Vitals
- [ ] Image optimization (WebP dla zdjęć, SVG dla grafik)
- [ ] CSS code splitting
- [ ] Service worker dla offline (jeśli potrzebny)

### 5.4 404 / Offline
- [ ] Custom 404 page z sugestiami
- [ ] Offline page (service worker cache)

---

## Quick Wins (do zrobienia od razu)

1. **Skip-to-content link** — prosty HTML, duży wpływ na a11y
2. **AI transparency note** — jedna linia w footer
3. **Category badges na kartach** — kolorowy `span` nad tytułem
4. **System font stack** — zmiana w `custom.scss`
5. **Usunąć nieużywane pluginy** — slick, venobox, filterizr, gmap
6. **Reading time** — prosty skrót w frontmatter lub template
7. **Focus indicators** — upewnić się że Bootstrap nie je wyłącza

---

## Mierniki sukcesu

| Metryka | Obecnie | Target |
|---------|---------|--------|
| Lighthouse Performance | ? | >90 |
| Lighthouse Accessibility | ? | >95 |
| Core Web Vitals (LCP) | ? | <2.5s |
| Page load time | ? | <1.5s |
| Testy E2E | 63/63 | 80+ |

---

*Plan oparty na trendach UX 2026: Lyssna Design Trends Survey 2026, Envato UX/UI Trends 2026, NNG, Forrester.*
