---
title: "Lekcja 2 — Myślenie Bayesowskie"
date: 2026-05-23
type: "lesson"
difficulty: "średni"
tags: ["bayes","prawdopodobieństwo","podejmowanie decyzji"]
tldr: "Myślenie bayesowskie aktualizuje przekonania na podstawie nowych dowodów, wykorzystując prawdopodobieństwa a priori i wiarygodność, aby uzyskać prawdopodobieństwa a posteriori."
takeaways: 
  - "Rozpocznij od przekonań a priori opartych na istniejącej wiedzy"
  - "Aktualizuj przekonania, gdy pojawią się nowe dowody, korzystając z twierdzenia Bayesa"
  - "Skup się na stosunku wiarygodności, a nie tylko na surowych prawdopodobieństwach"
---
![Ilustracja bayesowska](/images/bayes.svg)

## Wprowadzenie

Myślenie bayesowskie to ramowy sposób aktualizowania naszych przekonań w świetle nowych dowodów. Zamiast trzymać się sztywno jednej hipotezy, traktujemy nasze przekonania jako prawdopodobieństwa, które można zmieniać w zależności od tego, co obserwujemy.

### Dlaczego myślenie bayesowskie jest przydatne?

- Pozwala uniknąć błędów wynikających z ignorowania podstawowych stawek (base rate neglect).
- Pomaga rozróżnić między siłą dowodu a jego rzadkością.
- Umożliwia ilościowe łączenie różnych źródeł informacji.
- Jest fundamentem wielu nowoczesnych metod uczenia maszynowego i sztucznej inteligencji.

### Formalizm: Twierdzenie Bayesa

Twierdzenie Bayesa opisuje, jak zmienić prawdopodobieństwo hipotezy H przy osservacji dowodu E:

$$
P(H|E) = \frac{P(E|H) \cdot P(H)}{P(E)}
$$

Gdzie:
- $P(H)$ to prawdopodobieństwo a priori hipotezy (nasze początkowe przekonanie).
- $P(E|H)$ to prawdopodobieństwo wystąpienia dowodu E assuming hipoteza H jest prawdziwa (wiarygodność).
- $P(E)$ to całkowite prawdopodobieństwo dowodu (czynnik normalizujący).
- $P(H|E)$ to prawdopodobieństwo a posteriori (zaktualizowane przekonanie po zobaczeniu dowodu).

Często bardziej praktyczne jest skupienie się na stosunku szans:

$$
\frac{P(H|E)}{P(\neg H|E)} = \frac{P(E|H)}{P(E|\neg H)} \cdot \frac{P(H)}{P(\neg H)}
$$

Stosunek szans po aktualizacji równa się stosunkowi szans przed aktualizacji pomnożonemu przez stosunek wiarygodności (likelihood ratio).

## Przykład: Test na chorobę

Wyobraź sobie, że test na określoną chorobę ma:
- Czułość (prawdopodobieństwo pozytywnego testu przy chorobie) = 99%
- Specyficzność (prawdopodobieństwo negatywnego testu przy braku choroby) = 95%
- Występowanie choroby w populacji (prawdopodobieństwo a priori) = 0.1%

Jaki jest prawdopodobieństwo, że osoba jest chora po otrzymaniu pozytywnego wyniku testu?

Korzystając z twierdzenia Bayesa:
- $P(H) = 0.001$
- $P(E|H) = 0.99$
- $P(E|\neg H) = 1 - 0.95 = 0.05$ (false positive rate)
- $P(E) = P(E|H)P(H) + P(E|\neg H)P(\neg H) = 0.99*0.001 + 0.05*0.999 ≈ 0.05094$
- $P(H|E) = (0.99 * 0.001) / 0.05094 ≈ 0.0194$ → tylko około 1.94%

Mimo że test jest bardzo dokładny, ze względu na rzadkość choroby większość pozytywnych wyników to falszywe alarmy.

Ten przykład pokazuje, dlaczego ważne jest uwzględnienie prawdopodobieństwa a priori.

### Zastosowania w praktyce

1. **Diagnostyka medyczna** – jak powyżej, łączenie wyników testów z wiedzą o występowaniu choroby.
2. **Filtr spamu** – ocena prawdopodobieństwa, że wiadomość jest spamem na podstawie słów w niej zawartych.
3. **Ewaluacja ryzyka kredytowego** – aktualizacja prawdopodobieństwa niewypłacalności na podstawie historii płatności i innych wskaźników.
4. **Nauka i eksperymenty** – aktualizacja przekonań o hipotezie naukowej w świetle nowych danych eksperymentalnych.

### Jak ćwiczyć myślenie bayesowskie?

- Zadawaj sobie pytanie: "Jaki było moje przekonanie a priori przed zobaczeniem tego dowodu?"
- Ocenić, jak mocny jest dowód: czy jest równie prawdopodobny pod różnymi hipotezami?
- Aktualizować przekonania krok po kroku, gdy pojawia się więcej dowodów.
- Używać kalkulatorów bayesowych lub prostych arkuszy do wyliczania prawdopodobieństw a posteriori.
- Rozpoznawać sytuacje, w których nieuwzględnienie podstawowej stawki prowadzi do błędnych wniosków.

### Refleksja

Pomyśl o ostatniej sytuacji, w której zmieniłeś zdanie na podstawie nowych informacji. Czy jawnie uwzględniłeś swoje poprzednie przekonania? Jak silny był dowód? Czy mógłbyś lepiej kwantyfikować swoją aktualizację?

### Quiz

<div class="quiz" data-quiz='{"questions":[{"q":"W przykładzie testu na chorobę, dlaczego pozytywny wynik jeszcze nie oznacza wysokiego prawdopodobieństwa choroby?","options":["Ponieważ test jest niewiarygodny","Ponieważ choroba jest bardzo rzadka (niska podstawowa stawka)","Ponieważ lekarze często popełniają błędy"],"a":1},{"q":"Co to jest stosunek wiarygodności (likelihood ratio)?","options":["Stosunek prawdopodobieństwa a posteriori do a priori","Stosunek prawdopodobieństwa dowodu pod dwiema różnymi hipotezami","Stosunek liczby prawdziwie dodatnich do falszywie dodatnich"],"a":1},{"q":"Która z poniższych praktyk pomaga uniknąć błędu pomijania podstawowej stawki?","options":["Ignorowanie częstości występowania zdarzenia w populacji","Zawsze zaczynanie od 50/50 przekonania","Jawnie uwzględnianie częstości podstawowej przy ocenie dowodów"],"a":2}]}'></div>