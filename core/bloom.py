import random
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


def _extract_domain(url: str) -> str:
    m = re.search(r"https?://([^/]+)", url)
    return m.group(1).lower().replace("www.", "") if m else ""


def _format_title(t: str, maxlen: int = 60) -> str:
    return t[:maxlen] + "…" if len(t) > maxlen else t


def _distractors(correct: str, pool: list[str], n: int = 3) -> list[str]:
    pool = [x for x in pool if x != correct]
    random.shuffle(pool)
    return pool[:n]


# ── Article-aware quiz generation ──


def _build_source_question(article: dict, pool: list[str]) -> dict | None:
    domain = _extract_domain(article.get("url", ""))
    if not domain or not pool:
        return None
    pool_domains = list({_extract_domain(a.get("url", "")) for a in pool if a.get("url")})
    if len(pool_domains) < 4:
        return None
    opts = [domain] + _distractors(domain, pool_domains, 3)
    random.shuffle(opts)
    return {
        "bloom_level": "remember",
        "type": "mc",
        "question": f"Z jakiej domeny pochodzi artykuł \"{_format_title(article['title'])}\"?",
        "options": opts,
        "correct": domain,
    }


def _build_points_question(article: dict, pool: list[str]) -> dict | None:
    pts = article.get("points", 0)
    if pts == 0:
        return None
    ranges = [
        (0, 10, "0–10"),
        (11, 50, "11–50"),
        (51, 100, "51–100"),
        (101, 300, "101–300"),
        (301, 999, "301–999"),
        (1000, 99999, "1000+"),
    ]
    correct_range = next((r[2] for r in ranges if r[0] <= pts <= r[1]), "1000+")
    opts = [r[2] for r in ranges]
    others = [r for r in opts if r != correct_range]
    random.shuffle(others)
    return {
        "bloom_level": "remember",
        "type": "mc",
        "question": f"Ile punktów na Hacker News zdobył artykuł \"{_format_title(article['title'])}\"?",
        "options": [correct_range] + others[:3],
        "correct": correct_range,
    }


def _build_top_article_question(articles: list[dict]) -> dict | None:
    scored = [a for a in articles if a.get("points", 0) > 0]
    if len(scored) < 4:
        return None
    scored.sort(key=lambda a: a["points"], reverse=True)
    best = scored[0]
    opts = [a["title"][:40] for a in scored[:4]]
    random.shuffle(opts)
    return {
        "bloom_level": "analyze",
        "type": "mc",
        "question": "Który z tych artykułów zdobył najwięcej punktów na HN?",
        "options": [t + ("…" if len(t) == 40 else "") for t in opts],
        "correct": best["title"][:40] + ("…" if len(best["title"]) > 40 else ""),
    }


def _build_source_tier_question(article: dict) -> dict | None:
    domain = _extract_domain(article.get("url", ""))
    if not domain:
        return None
    tiers = {
        r"arxiv\.org|\.edu|scholar\.google": "Wysoki – źródło naukowe",
        r"reuters\.com|bloomberg\.com|ft\.com|wsj\.com|nature\.com|science\.org":
            "Wysoki – renomowane medium",
        r"techcrunch\.com|theverge\.com|arstechnica\.com|wired\.com|zdnet\.com":
            "Średni – branżowe medium",
        r"github\.com|stackoverflow\.com|medium\.com|reddit\.com":
            "Niski – społecznościowe",
    }
    correct = "Nieznany"
    for pat, label in tiers.items():
        if re.search(pat, domain, re.I):
            correct = label
            break
    opts = [correct.replace(" –", " – ").strip()]
    all_labels = list(tiers.values()) + ["Niski – społecznościowe"]
    others = [l for l in all_labels if l != correct]
    random.shuffle(others)
    return {
        "bloom_level": "evaluate",
        "type": "mc",
        "question": f"Jaki jest poziom wiarygodności źródła {domain}?",
        "options": [correct] + others[:3],
        "correct": correct,
    }


def _build_domain_type_question(article: dict) -> dict | None:
    domain = _extract_domain(article.get("url", ""))
    m = re.search(r"\.([a-z]+)$", domain)
    tld = m.group(1) if m else ""
    cats = {
        "com": "Komercyjna",
        "org": "Organizacja non-profit",
        "edu": "Edukacyjna",
        "gov": "Rządowa",
        "mil": "Wojskowa",
        "io": "Technologiczna (startup)",
        "ai": "Technologiczna (AI)",
    }
    correct = cats.get(tld, "Inna")
    return {
        "bloom_level": "understand",
        "type": "mc",
        "question": f"Jakiego typu jest domena {domain}?",
        "options": list(cats.values()),
        "correct": correct,
    }


def _build_which_source_question(articles: list[dict]) -> dict | None:
    details = []
    for a in articles:
        domain = _extract_domain(a.get("url", ""))
        if domain:
            details.append((domain, _format_title(a["title"], 40)))
    if len(set(d[0] for d in details)) < 2:
        return None
    random.shuffle(details)
    questions = [
        {
            "bloom_level": "remember",
            "type": "mc",
            "question": f"Z której domeny pochodzi artykuł \"{fmt_title}\"?",
            "options": [d[0] for d in details[:4]],
            "correct": domain,
        }
        for domain, fmt_title in details[:2]
    ]
    return questions[0] if questions else None


def _build_pillar_question(article: dict, pillar_name: str) -> dict:
    return {
        "bloom_level": "understand",
        "type": "open-ended",
        "question": f"Dlaczego artykuł \"{_format_title(article['title'])}\" jest istotny w obszarze {pillar_name}?",
    }


def _build_application_question(article: dict, pillar_name: str) -> dict:
    return {
        "bloom_level": "apply",
        "type": "open-ended",
        "question": f"Jak koncepcje z artykułu \"{_format_title(article['title'])}\" można zastosować w praktyce w {pillar_name}?",
    }


def _build_evaluate_question(article: dict) -> dict | None:
    pts = article.get("points", 0)
    if pts == 0:
        return None
    return {
        "bloom_level": "evaluate",
        "type": "open-ended",
        "question": f"Czy artykuł \"{_format_title(article['title'])}\" ({pts} pkt na HN) zasługuje na uwagę? Uzasadnij.",
    }


def _build_create_question(articles: list[dict], pillar_name: str) -> dict:
    themes = list(set(
        a.get("title", "").split()[0] for a in articles if a.get("title")
    ))
    theme = random.choice(themes[:5]) if themes else pillar_name
    return {
        "bloom_level": "create",
        "type": "open-ended",
        "question": f"Na podstawie artykułów z {pillar_name}, zaproponuj nowy kierunek badań lub projekt inspirowany tematem \"{theme}\".",
    }


def generate_quiz_questions(articles: list[dict], pillar_name: str = "") -> list[dict]:
    from .data import PILLARS

    pillar_label = PILLARS.get(pillar_name, {}).get("label", pillar_name) if pillar_name else pillar_name
    questions: list[dict] = []
    seen_topics: set[str] = set()
    pool = articles[:]

    # Select diverse articles for questions
    random.shuffle(pool)
    high_score = [a for a in pool if a.get("points", 0) >= 50]
    all_articles = pool

    # Build question pool with variety
    candidates = []

    # Source identification (remember, MC)
    for a in pool[:8]:
        q = _build_source_question(a, all_articles)
        if q:
            candidates.append(q)

    # Points estimation (remember, MC)
    for a in high_score[:6]:
        q = _build_points_question(a, all_articles)
        if q:
            candidates.append(q)

    # Top article (analyze, MC)
    q = _build_top_article_question(all_articles)
    if q:
        candidates.append(q)

    # Source tier (evaluate, MC)
    for a in pool[:6]:
        q = _build_source_tier_question(a)
        if q:
            candidates.append(q)

    # Domain type (understand, MC)
    for a in pool[:4]:
        q = _build_domain_type_question(a)
        if q:
            candidates.append(q)

    # Pillar relevance (understand, open)
    for a in pool[:4]:
        candidates.append(_build_pillar_question(a, pillar_label))

    # Application (apply, open)
    for a in pool[:4]:
        candidates.append(_build_application_question(a, pillar_label))

    # Evaluate (evaluate, open)
    for a in high_score[:4]:
        q = _build_evaluate_question(a)
        if q:
            candidates.append(q)

    # Create (create, open)
    candidates.append(_build_create_question(all_articles, pillar_label))

    # Filter to one question per Bloom level per post (existing logic)
    levels_present: list[str] = []
    seen: set[str] = set()
    for a in articles:
        lvl = classify_bloom_level(a)
        if lvl not in seen:
            seen.add(lvl)
            levels_present.append(lvl)
    levels_present.sort(key=level_index)

    # Pick best question per level: prefer MC, then article-specific
    for lvl in levels_present:
        lvl_candidates = [c for c in candidates if c.get("bloom_level") == lvl]
        if lvl_candidates:
            chosen = random.choice(lvl_candidates)
        else:
            chosen = {
                "bloom_level": lvl,
                "type": "open-ended",
                "question": f"Opowiedz o kluczowych aspektach w obszarze {pillar_label} związanych z poziomem {level_label_pl(lvl)}.",
            }
        questions.append(chosen)

    return questions


# ── Rich flashcards ──

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
        if "@" in phrase or "." in phrase:
            continue
        bigrams.append(phrase)
    return bigrams


def generate_flashcards(articles: list[dict], pillar_name: str = "") -> list[dict]:
    from .data import KNOWN_ENTITIES, ALL_ENTITIES

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
            source = next((a["title"] for a in articles if ent.lower() in a.get("title", "").lower()), "")
            flashcards.append({
                "term": ent,
                "definition": definition,
                "pillar": pillar_name,
                "source": source,
                "source_type": "entity",
            })

    # 2. Extract meaningful bigrams with article context
    for a in articles:
        bigrams = _extract_bigrams(a.get("title", ""))
        for bg in bigrams:
            if bg not in seen_terms and len(seen_terms) < 80:
                seen_terms.add(bg)
                flashcards.append({
                    "term": bg,
                    "definition": next(
                        (f"Temat z artykułu: {a['title']}" for a in articles if bg.lower() in a.get("title", "").lower()),
                        f"Termin z dziedziny {pillar_name or 'tej dziedziny'}"
                    ),
                    "pillar": pillar_name,
                    "source": a.get("title", ""),
                    "source_type": "bigram",
                })

    # 3. Cross-pillar concept cards: find terms mentioned across pillars
    from .data import PILLARS, ALL_ENTITIES
    cross_terms = [e for e in ALL_ENTITIES if title_lower.count(e.lower()) >= 2]
    for ct in cross_terms:
        if ct not in seen_terms:
            seen_terms.add(ct)
            defn = entity_defs.get(ct, f"Ważne pojęcie: {ct}")
            flashcards.append({
                "term": ct,
                "definition": defn,
                "pillar": "cross-domain",
                "source": f"Pojawia się w wielu artykułach",
                "source_type": "cross",
            })

    return flashcards[:120]
