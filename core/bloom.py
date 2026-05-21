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
    ],
    "understand": [
        "Wyjaśnij własnymi słowami, czym jest {topic} i dlaczego jest istotne.",
        "Jak {topic} wpływa na szerszy kontekst w swojej dziedzinie?",
    ],
    "apply": [
        "Jak można zastosować {topic} w praktyce w obszarze {pillar}?",
        "Opisz scenariusz, w którym {topic} rozwiązałby rzeczywisty problem.",
    ],
    "analyze": [
        "Jakie są kluczowe różnice między {topic} a alternatywnymi podejściami?",
        "Przeanalizuj, jakie czynniki stoją za {topic} i jakie mają implikacje.",
    ],
    "evaluate": [
        "Oceń wiarygodność i znaczenie {topic}. Jakie są mocne i słabe strony?",
        "Czy {topic} to dobry kierunek? Uzasadnij swoją opinię.",
    ],
    "create": [
        "Jakie nowe rozwiązanie mógłbyś zaproponować, opierając się na {topic}?",
        "Zaprojektuj eksperyment myślowy, który łączy {topic} z innym obszarem wiedzy.",
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


def generate_flashcards(articles: list[dict], pillar_name: str = "") -> list[dict]:
    """Generuje fiszki (term → definition) z encji i tytułów artykułów."""
    from .data import KNOWN_ENTITIES

    entity_defs: dict[str, str] = {
        "FinCEN": "Financial Crimes Enforcement Network — agencja USA ds. przestępczości finansowej",
        "FATF": "Financial Action Task Force — międzynarodowa organizacja ds. przeciwdziałania praniu pieniędzy",
        "SEC": "Securities and Exchange Commission — amerykański regulator rynku papierów wartościowych",
        "FCA": "Financial Conduct Authority — brytyjski regulator finansowy",
        "ECB": "European Central Bank — Europejski Bank Centralny",
        "GDPR": "General Data Protection Regulation — unijne rozporządzenie o ochronie danych osobowych",
        "KYC": "Know Your Customer — procedura weryfikacji tożsamości klienta",
        "AML": "Anti-Money Laundering — przeciwdziałanie praniu pieniędzy",
        "CBDC": "Central Bank Digital Currency — cyfrowa waluta banku centralnego",
        "PSD2": "Payment Services Directive 2 — unijna dyrektywa o usługach płatniczych",
        "SAR": "Suspicious Activity Report — zgłoszenie podejrzanej aktywności",
        "CTF": "Counter-Terrorism Financing — przeciwdziałanie finansowaniu terroryzmu",
        "SQI": "Signal Quality Index — miara jakości sygnału w 6 wymiarach (AcaciaFund)",
        "NLP": "Natural Language Processing — przetwarzanie języka naturalnego",
        "API": "Application Programming Interface — interfejs programistyczny aplikacji",
        "LLM": "Large Language Model — duży model językowy",
        "HN": "Hacker News — platforma społecznościowa dla branży technologicznej",
        "arXiv": "Open-access repozytorium preprintów naukowych",
        "KYC": "Know Your Customer — proces weryfikacji tożsamości klienta",
    }

    seen_terms: set[str] = set()
    flashcards: list[dict] = []

    title_text = " ".join(a.get("title", "") for a in articles).lower()
    for ent, definition in entity_defs.items():
        if ent.lower() in title_text and ent not in seen_terms:
            seen_terms.add(ent)
            flashcards.append({
                "term": ent,
                "definition": definition,
                "pillar": pillar_name,
            })

    return flashcards[:10]
