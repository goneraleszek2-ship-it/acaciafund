import re

_VERBS = {
    "remember": "recalling",
    "understand": "explaining",
    "apply": "implementing",
    "analyze": "analyzing",
    "evaluate": "evaluating",
    "create": "creating",
}

_LEVEL_ORDER = ["remember", "understand", "apply", "analyze", "evaluate", "create"]

_REMEMBER_KW = re.compile(
    r"\b(announce(?:s|d)?|launch(?:es|ed)?|release(?:s|d)?|"
    r"introduc(?:es|ed)|unveil(?:s|ed|ing)?|publish(?:es|ed)?)\b", re.I
)
_UNDERSTAND_KW = re.compile(
    r"\b(explain(?:s|ed|ing)?|guide|introduction|"
    r"primer|overview|basics?|fundamentals?|"
    r"what is|how to|understand(?:ing)?|tutorial)\b", re.I
)
_APPLY_KW = re.compile(
    r"\b(implement(?:s|ed|ing|ation)?|deploy(?:s|ed|ing|ment)?|"
    r"framework|tool(?:s|ing)?|system(?:s)?|"
    r"pipeline|workflow|building|build\b|"
    r"practical|hands.on)\b", re.I
)
_ANALYZE_KW = re.compile(
    r"\b(analys(is|e|es|ing)|comparison|benchmark(?:s|ing)?|"
    r"survey|review(?:s|ed|ing)?|evaluat(?:e|es|ing|ion)|"
    r"measur(?:e|es|ing|ement)|assessment|"
    r"stud(?:y|ies)|investigat(?:e|es|ing|ion)|"
    r"pattern(?:s)?|trend(?:s)?)\b", re.I
)
_EVALUATE_KW = re.compile(
    r"\b(regulat(?:e|es|ing|ion|ory|ions?)|"
    r"compliance|compliant|risk(?:s|y)?|"
    r"secur(?:e|ity|ing)|privacy|"
    r"should|must|need to|ethical|ethic(?:s)?|"
    r"law(?:s)?|legal|policy|standard(?:s)?|"
    r"audit(?:s|ing|ed)?|oversight|governance)\b", re.I
)
_CREATE_KW = re.compile(
    r"\b(novel|breakthrough|discover(?:y|ies|ed)?|"
    r"invent(?:s|ed|ion)?|first.ever|"
    r"pioneer(?:s|ed|ing)?|revolutionary|"
    r"paradigm.shift|new approach|"
    r"generat(?:e|es|ing|ed|ive)|synthes(?:is|ize|izes|ized))\b", re.I
)

_GOV_ORG_DOMAIN = re.compile(r"\.(gov|mil|edu|org)$", re.I)
_ARXIV_DOMAIN = re.compile(r"arxiv\.org", re.I)


_KEYWORD_LEVELS = [
    ("create", _CREATE_KW),
    ("evaluate", _EVALUATE_KW),
    ("analyze", _ANALYZE_KW),
    ("apply", _APPLY_KW),
    ("understand", _UNDERSTAND_KW),
    ("remember", _REMEMBER_KW),
]


def classify_bloom_level(article: dict) -> str:
    """Zwraca poziom Blooma dla artykułu na podstawie tytułu, źródła i punktów."""
    title = article.get("title", "")
    url = article.get("url", "")
    points = article.get("points", 0) or 0
    is_arxiv = bool(_ARXIV_DOMAIN.search(url))
    is_gov_org = bool(_GOV_ORG_DOMAIN.search(url))

    if is_arxiv and _CREATE_KW.search(title):
        return "create"
    if is_gov_org and _EVALUATE_KW.search(title):
        return "evaluate"
    if is_arxiv and _APPLY_KW.search(title):
        return "apply"

    for level, pattern in _KEYWORD_LEVELS:
        if pattern.search(title):
            return level

    title_lower = title.lower()
    if points > 0:
        if points >= 200:
            return "evaluate"
        if points >= 50:
            return "understand"
        if points > 0:
            return "remember"

    return "understand"


def bloom_verb(level: str) -> str:
    return _VERBS.get(level, "reviewing")


def level_index(level: str) -> int:
    try:
        return _LEVEL_ORDER.index(level)
    except ValueError:
        return -1


def level_label_pl(level: str) -> str:
    labels = {
        "remember": "Zapamiętywanie",
        "understand": "Rozumienie",
        "apply": "Stosowanie",
        "analyze": "Analiza",
        "evaluate": "Ewaluacja",
        "create": "Tworzenie",
    }
    return labels.get(level, level.capitalize())


def _extract_key_terms(articles: list[dict]) -> list[str]:
    """Wyciąga kluczowe terminy z tytułów artykułów."""
    words: list[str] = []
    for a in articles:
        cleaned = re.sub(r"[^a-z\s]", " ", a.get("title", "").lower())
        words.extend(
            w for w in cleaned.split()
            if len(w) > 4 and w not in {"this", "that", "with", "from", "what", "how", "why", "about", "their", "these", "those", "which", "there", "would", "could", "should", "after", "still", "into", "than", "then", "also", "just", "more", "very", "been", "over", "such", "only"}
        )
    seen: set[str] = set()
    unique: list[str] = []
    for w in words:
        if w not in seen:
            seen.add(w)
            unique.append(w)
    return unique[:8]


_QUESTION_TEMPLATES: dict[str, list[str]] = {
    "remember": [
        "Jakie kluczowe fakty dotyczące {topic} zostały przedstawione w artykule?",
        "Wymień najważniejsze dane liczbowe związane z {topic}.",
        "Kto opisał {topic} i jakie były główne tezy?",
        "Zidentyfikuj daty i wydarzenia kluczowe dla {topic}.",
    ],
    "understand": [
        "Wyjaśnij własnymi słowami, czym jest {topic} i dlaczego jest istotne.",
        "Jak {topic} wpływa na szerszy kontekst w swojej dziedzinie?",
        "Opisz główną ideę stojącą za {topic} — jak byś ją wytłumaczył laikowi?",
        "Dlaczego {topic} budzi zainteresowanie w obszarze {pillar}?",
    ],
    "apply": [
        "Jak można zastosować {topic} w praktyce w obszarze {pillar}?",
        "Opisz scenariusz, w którym {topic} rozwiązałby rzeczywisty problem.",
        "Jakie narzędzia lub metody są potrzebne, aby wdrożyć {topic}?",
        "Zaproponuj praktyczne wykorzystanie {topic} w swoim projekcie.",
    ],
    "analyze": [
        "Jakie są kluczowe różnice między {topic} a alternatywnymi podejściami?",
        "Przeanalizuj, jakie czynniki stoją za {topic} i jakie mają implikacje.",
        "Jakie wzorce lub trendy można zidentyfikować w kontekście {topic}?",
        "Rozbij {topic} na części składowe i opisz relacje między nimi.",
    ],
    "evaluate": [
        "Oceń wiarygodność i znaczenie {topic}. Jakie są mocne i słabe strony?",
        "Czy {topic} to dobry kierunek? Uzasadnij swoją opinię.",
        "Jakie argumenty przemawiają za i przeciw {topic}?",
        "Porównaj {topic} z alternatywami — które rozwiązanie jest lepsze i dlaczego?",
    ],
    "create": [
        "Jakie nowe rozwiązanie mógłbyś zaproponować, opierając się na {topic}?",
        "Zaprojektuj eksperyment myślowy, który łączy {topic} z innym obszarem wiedzy.",
        "Sformułuj hipotezę badawczą dotyczącą {topic}.",
        "Jak wyglądałby twój autorski framework lub model inspirowany {topic}?",
    ],
}


def generate_quiz_questions(articles: list[dict], pillar_name: str = "") -> list[dict]:
    """Generuje pytania Bloom na podstawie artykułów. 1 pytanie na poziom."""
    from .data import KNOWN_ENTITIES

    levels_present: list[str] = []
    seen: set[str] = set()
    for a in articles:
        lvl = classify_bloom_level(a)
        if lvl not in seen:
            seen.add(lvl)
            levels_present.append(lvl)
    levels_present.sort(key=level_index)

    key_terms = _extract_key_terms(articles)
    questions: list[dict] = []
    for lvl in levels_present:
        templates = _QUESTION_TEMPLATES.get(lvl, ["Opowiedz o {topic}."])
        template = templates[levels_present.index(lvl) % len(templates)]

        if key_terms:
            topic = key_terms[levels_present.index(lvl) % len(key_terms)]
        else:
            topic = articles[0].get("title", "temacie")[:50] if articles else "temacie"

        question = template.format(topic=topic, pillar=pillar_name or "tej dziedzinie")
        questions.append({
            "bloom_level": lvl,
            "question": question,
            "type": "open-ended",
        })
    return questions


_BIGRAM_SKIP_WORDS = {
    "after", "ahead", "amid", "among", "before", "behind", "below", "despite",
    "during", "facing", "following", "including", "inside", "into", "minus",
    "near", "next", "onto", "outside", "past", "pending", "plus", "since",
    "through", "toward", "under", "until", "upon", "within", "without",
    "makes", "takes", "gives", "puts", "sets", "gets", "lets", "goes",
    "came", "come", "bring", "brought", "seen", "shows", "showed",
    "pleads", "faces", "files", "hits", "wins", "loses", "joins",
    "says", "said", "told", "called", "named", "known", "used",
    "turns", "moves", "makes", "backs", "plans", "hopes", "aims",
    "wants", "needs", "looks", "seeks", "forms", "helped",
    "what", "when", "where", "why", "which", "who", "whom", "whose",
    "this", "that", "these", "those", "every", "each", "such", "same",
    "much", "many", "some", "any", "all", "both", "few", "most",
    "very", "just", "only", "also", "still", "even", "quite", "rather",
    "first", "last", "next", "second", "third", "final", "early", "late",
    "best", "worst", "good", "bad", "big", "new", "old", "high", "low",
    "long", "short", "wide", "deep", "full", "open", "real", "sure",
}


def _extract_bigrams(title: str) -> list[str]:
    """Wyciąga istotne 2-wyrazowe frazy z tytułu."""
    cleaned = re.sub(r"[^a-zA-Z\s]", " ", title)
    tokens = cleaned.split()
    bigrams: list[str] = []
    for i in range(len(tokens) - 1):
        w1, w2 = tokens[i], tokens[i+1]
        phrase = f"{w1} {w2}"
        if len(phrase) < 14:
            continue
        if not (w1[0].isupper() and w2[0].isupper()):
            continue
        if len(w1) < 4 or len(w2) < 4:
            continue
        w1l, w2l = w1.lower(), w2.lower()
        if w1l in _BIGRAM_SKIP_WORDS or w2l in _BIGRAM_SKIP_WORDS:
            continue
        # Skip email-like patterns (word@word)
        if "@" in phrase or "." in phrase:
            continue
        bigrams.append(phrase)
    return bigrams


def generate_flashcards(articles: list[dict], pillar_name: str = "") -> list[dict]:
    """Generuje fiszki (term → definition) z encji, tytułów i bigramów."""
    from .data import KNOWN_ENTITIES, ALL_ENTITIES

    # Comprehensive definitions (hardcoded + loaded from config entities)
    entity_defs: dict[str, str] = {
        # ── AML ──
        "FinCEN": "Financial Crimes Enforcement Network — agencja USA ds. przestępczości finansowej",
        "FATF": "Financial Action Task Force — międzynarodowa organizacja ds. przeciwdziałania praniu pieniędzy",
        "SEC": "Securities and Exchange Commission — amerykański regulator rynku papierów wartościowych",
        "FCA": "Financial Conduct Authority — brytyjski regulator finansowy",
        "ECB": "European Central Bank — Europejski Bank Centralny",
        "Fed": "Federal Reserve System — bank centralny Stanów Zjednoczonych",
        "OCC": "Office of the Comptroller of the Currency — amerykański nadzór bankowy",
        "EBA": "European Banking Authority — Europejski Urząd Nadzoru Bankowego",
        "Binance": "Największa giełda kryptowalut na świecie",
        "Coinbase": "Amerykańska giełda kryptowalut notowana na Nasdaq",
        "Circle": "Emiter stablecoina USDC",
        "PayPal": "Globalna platforma płatności cyfrowych",
        "Stripe": "Platforma obsługi płatności internetowych",
        "JPMorgan": "Największy bank w USA pod względem aktywów",
        "HSBC": "Międzynarodowy bank z siedzibą w Londynie",
        "Visa": "Globalna sieć kart płatniczych",
        "Mastercard": "Globalna sieć kart płatniczych",
        "SWIFT": "Society for Worldwide Interbank Financial Telecommunication — system komunikacji międzybankowej",
        "FedNow": "System natychmiastowych płatności amerykańskiego Fed",
        "KYC": "Know Your Customer — procedura weryfikacji tożsamości klienta",
        "AML": "Anti-Money Laundering — przeciwdziałanie praniu pieniędzy",
        "CBDC": "Central Bank Digital Currency — cyfrowa waluta banku centralnego",
        "PSD2": "Payment Services Directive 2 — unijna dyrektywa o usługach płatniczych",
        "SAR": "Suspicious Activity Report — zgłoszenie podejrzanej aktywności",
        "CTF": "Counter-Terrorism Financing — przeciwdziałanie finansowaniu terroryzmu",
        # ── Markets ──
        "NVIDIA": "Producent procesorów graficznych (GPU) i lider w AI computing",
        "AMD": "Advanced Micro Devices — producent CPU i GPU, konkurent Intel/NVIDIA",
        "TSMC": "Taiwan Semiconductor Manufacturing Company — największy producent układów scalonych",
        "Intel": "Największy producent procesorów x86 na świecie",
        "ASML": "Holenderski producent maszyn litograficznych dla przemysłu półprzewodnikowego",
        "ARM": "Architektura procesorów o niskim poborze energii, własność SoftBank",
        "Qualcomm": "Producent układów Snapdragon dla urządzeń mobilnych",
        "Broadcom": "Producent układów scalonych i infrastruktury sieciowej",
        "Micron": "Amerykański producent pamięci DRAM i NAND",
        "Samsung": "Konglomerat technologiczny, największy producent pamięci",
        "SoftBank": "Japoński konglomerat inwestycyjny, właściciel ARM i Vision Fund",
        "S&P 500": "Indeks giełdowy 500 największych spółek USA",
        "Nasdaq": "Amerykańska giełda technologiczna",
        "GPU": "Graphics Processing Unit — procesor graficzny",
        "CPU": "Central Processing Unit — procesor główny",
        "ASIC": "Application-Specific Integrated Circuit — układ scalony dedykowanego zastosowania",
        "RISC-V": "Otwarta architektura procesorów",
        # ── Science ──
        "DeepMind": "Laboratorium AI należące do Alphabet/Google",
        "Anthropic": "Firma AI tworząca model Claude",
        "MIT": "Massachusetts Institute of Technology",
        "Stanford": "Stanford University — lider w badaniach AI",
        "Harvard": "Harvard University — najstarsza uczelnia USA",
        "Oxford": "University of Oxford — wiodący brytyjski uniwersytet badawczy",
        "Cambridge": "University of Cambridge — brytyjski uniwersytet badawczy",
        "Caltech": "California Institute of Technology",
        "DARPA": "Defense Advanced Research Projects Agency — agencja badawcza USA",
        "NIH": "National Institutes of Health — amerykański instytut zdrowia",
        "CERN": "Europejska Organizacja Badań Jądrowych",
        "NASA": "National Aeronautics and Space Administration — amerykańska agencja kosmiczna",
        "WHO": "World Health Organization — Światowa Organizacja Zdrowia",
        # ── Cross-domain ──
        "GDPR": "General Data Protection Regulation — unijne rozporządzenie o ochronie danych osobowych",
        "SQI": "Signal Quality Index — miara jakości sygnału w 6 wymiarach (AcaciaFund)",
        "NLP": "Natural Language Processing — przetwarzanie języka naturalnego",
        "API": "Application Programming Interface — interfejs programistyczny aplikacji",
        "LLM": "Large Language Model — duży model językowy",
        "HN": "Hacker News — platforma społecznościowa dla branży technologicznej",
        "arXiv": "Open-access repozytorium preprintów naukowych",
        "PoC": "Proof of Concept — dowód koncepcji",
        "GDP": "Gross Domestic Product — produkt krajowy brutto",
        "IPO": "Initial Public Offering — pierwsza oferta publiczna akcji",
        "SPAC": "Special Purpose Acquisition Company — spółka celowa przejęć",
    }

    seen_terms: set[str] = set()
    flashcards: list[dict] = []
    title_text = " ".join(a.get("title", "") for a in articles)
    title_lower = title_text.lower()

    # 1. Match known entities appearing in titles
    for ent, definition in entity_defs.items():
        if ent.lower() in title_lower and ent not in seen_terms:
            seen_terms.add(ent)
            flashcards.append({
                "term": ent,
                "definition": definition,
                "pillar": pillar_name,
            })

    # 2. Extract meaningful bigrams (proper noun phrases) from titles
    for a in articles:
        bigrams = _extract_bigrams(a.get("title", ""))
        for bg in bigrams:
            if bg not in seen_terms and len(seen_terms) < 50:
                seen_terms.add(bg)
                definition = f"Termin z dziedziny {pillar_name or 'tej dziedziny'}: {bg}"
                flashcards.append({
                    "term": bg,
                    "definition": definition,
                    "pillar": pillar_name,
                })

    return flashcards[:100]
