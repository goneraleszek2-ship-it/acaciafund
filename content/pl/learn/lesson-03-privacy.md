---
title: "Lekcja 3 — Prywatność i Agregacja"
date: 2026-05-22
type: "lesson"
difficulty: "średni"
tags: ["prywatność","dp"]
tldr: "Prywatność różniczkowa dodaje szum do ochrony danych indywidualnych, umożliwiając jednocześnie przydatną analizę agregatową. ε (epsilon) to budżet prywatności - im niższy, tym większa prywatność."
takeaways: 
  - "Prywatność różniczkowa gwarantuje, że usunięcie lub zmiana jednego rekordu nie wpływa istotnie na wyniki"
  - "Budżet prywatności ε kontroluje kompromis między prywatnością a dokładnością"
  - "Acacia wykorzystuje prywatność różniczkową do ochrony współtwórców, zapewniając jednocześnie przydatne agregaty"
---
![Ilustracja prywatności](/images/privacy.svg)

## Wprowadzenie

W erze big data ochrona prywatności jednostek staje się coraz ważniejsza, jednocześnie chcemy korzystać z wartościowych analiz statystycznych. Prywatność różniczkowa (differential privacy, DP) to matematyczna ramka, która pozwala na obie rzeczy: ochronę danych indywidualnych oraz uzyskanie użytecznych wyników agregatowych.

### Dlaczego tradycyjne podejścia zawodzą?

Proste usuwanie danych identyfikacyjnych (anonymizacja) często okazuje się niewystarczające. Przykładowo, znając kod pocztowy, datę urodzenia i płeć, można zidentyfikować znaczną część populacji. Co więcej, nawet jeśli dane są agregowane, czasem można wnioskować o jednostkach poprzez ataki typu "różnicowanie" lub "rekonstrukcja".

### Jak działa prywatność różniczkowa?

Główną ideą jest dodanie starannie dobranego szumu do wyników zapytań statystycznych (np. liczby, średniej). Szum jest tak dobrany, że:
- Prawdopodobieństwo uzyskania danego wyniku praktycznie nie zmienia się, gdyby w bazie danych znajdował się lub nie znajdował się jakikolwiek pojedynczy osobnik.
- Jednocześnie, jeśli zapytanie dotyczy dużej grupy, dodany szum jest stosunkowo mały w porównaniu z prawdziwą wartością, więc wynik pozostaje przydatny.

Formalnie, mechanizm 𝓜 zapewnia ε-prywatność różniczkową, jeżeli dla wszystkich par baz danych D i D' różniących się maksymalnie jednym rekordem oraz dla wszystkich możliwych wyjść S:
$$
Pr[\mathcal{M}(D) \in S] \leq e^\varepsilon \cdot Pr[\mathcal{M}(D') \in S]
$$
Im mniejsze ε, tym silniejsza gwarancja prywatności (mniejszy wpływ zmiany jednego rekordu).

### Wybór szumu

Do najczęściej stosowanych mechanizmów należą:
- **Mechanizm Laplace'a** – dodaje szum rozłożony Laplace'a o skali proporcjonalnej do czułości zapytania (np. dla licznika czułość wynosi 1).
- **Mechanizm Gaussa** – dodaje szum rozłożony normalnego, używany gdy wymagana jest (ε,δ)-prywatność różniczkowa (pozwala na nieco większą elastyczność przy zachowaniu użyteczności).
- **Mechanizm wykładniczy** – używany do wyboru z kategorii (np. wybór najczęstszej odpowiedzi).

### Przykład: Liczenie osób z określoną cechą

Załóżmy, że chcemy policzyć, ile osób w bazie danych palą papierosy, jednocześnie chroniąc prywatność każdego respondenta.
- Rzeczywista liczba: 150 osób.
- Czułość zapytania (zmiana jednego rekordu może zmienić licznik o maksymalnie 1): Δ = 1.
- Dodajemy szum Laplace'a o skali Δ/ε. Przy ε = 1, skala = 1.
- Wynik może wyglądać np. jako 149.3 lub 152.7 – nie dowiadujemy się dokładnej liczby, ale błąd jest zazwyczaj niewielki względem rozmiaru grupy.

### Zastosowania w Acacia

W projekcie Acacia wykorzystujemy prywatność różniczkową do:
1. **Agregowania opinii** – gdy wielu użytkowników ocenia ten sam artykuł lub pomysł, dodajemy szum do średniej oceny, aby uniemożliwić odczytanie indywidualnych głosów.
2. **Publishing statystyk tematycznych** – liczba wystąpień określonych tagów (np. "AML", "bayes") jest publikowana z dodatkiem szumu, dzięki czemu nie można wywnioskować, czy konkretny użytkownik dodał lub usunął określony tag.
3. **Analiza trendów czasowych** – śledzimy, jak zmienia się zainteresowanie danym tematem tygodniowo, chroniąc jednocześnie prywatność osób odpowiedzialnych za poszczególne wpisy.

### Kompromis prywatność–użyteczność

Kluczowym parametrem jest ε (epsilon):
- **Małe ε** (np. 0.1) → bardzo silna prywatność, ale wyniki mogą być bardzo zakłócone szumem, niewydatne dla małych grup.
- **Duże ε** (np. 5.0) → słabsza gwarancja prywatności, ale wyniki bliższe prawdziwym wartościom.
W praktyce wybiera się ε w zależności od kontekstu: dla bardzo wrażliwych danych stosuje się mniejsze ε, dla publicznych statystyk można pozwolić na większe.

### Refleksja

Zastanów się, jakie rodzaje danych chciałbyś udostępniać w formie agregatowej, a jakie uważasz za zbyt wrażliwe, nawet po dodaniu szumu. Czy istnieją sytuacje, w których wolisz całkowicie zrezygnować z udostępniania danych, nawet jeśli oznacza to utratę pewnych wglądów?

### Quiz

<div class="quiz" data-quiz='{"questions":[{"q":"Co zapewnia prywatność różniczkowa?","options":["Pełną anonimizację danych","Że zmiana jednego rekordu nie wpływa istotnie na wynik zapytania"," że dane są szyfrowane kluczem publicznym"],"a":1},{"q":"Jak vaikuttaa ε (epsilon) na prywatność różniczkową?","options":["Im większe ε, tym silniejsza prywatność","Im mniejsze ε, tym silniejsza prywatność","ε nie ma wpływu na poziom prywatności"],"a":1},{"q":"Który mechanizm jest często używany do publikowania średnich wartości z zachowaniem prywatności różniczkowej?","options":["Mechanizm wykładniczy","Mechanizm Laplace'a lub Gaussa","Mechanizm permutacji"],"a":1}]}'></div>