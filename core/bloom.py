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
