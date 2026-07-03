"""Shared Bloom Taxonomy keyword regex patterns.

Centralized single source of truth used by both bloom.py and analyze.py.
"""

import re

REMEMBER_KW = re.compile(
    r"\b(announce(?:s|d)?|launch(?:es|ed)?|release(?:s|d)?|"
    r"introduc(?:es|ed)|unveil(?:s|ed|ing)?|publish(?:es|ed)?)\b",
    re.I,
)
UNDERSTAND_KW = re.compile(
    r"\b(explain(?:s|ed|ing)?|guide|introduction|"
    r"primer|overview|basics?|fundamentals?|"
    r"what is|how to|understand(?:ing)?|tutorial"
    r"|lesson|walkthrough|demonstrat(?:e|es|ed|ing)|illustrat(?:e|es|ed|ing))\b",
    re.I,
)
APPLY_KW = re.compile(
    r"\b(implement(?:s|ed|ing|ation)?|deploy(?:s|ed|ing|ment)?|"
    r"framework|tool(?:s|ing)?|system(?:s)?|"
    r"pipeline|workflow|building|build\b|"
    r"practical|hands\.on"
    r"|applica(?:tion|tions)|us(?:e|es|ed|ing)|using|utiliz(?:e|es|ed|ing))\b",
    re.I,
)
ANALYZE_KW = re.compile(
    r"\b(analys(is|e|es|ing)|comparison|benchmark(?:s|ing)?|"
    r"survey|review(?:s|ed|ing)?|evaluat(?:e|es|ing|ion)|"
    r"measur(?:e|es|ing|ement)|assessment|"
    r"stud(?:y|ies)|investigat(?:e|es|ing|ion)|"
    r"pattern(?:s)?|trend(?:s)?"
    r"|correlation|relationship|impact|effect(?:s)?|cause|factor(?:s)?|implication(?:s)?)\b",
    re.I,
)
EVALUATE_KW = re.compile(
    r"\b(regulat(?:e|es|ing|ion|ory|ions?)|"
    r"compliance|compliant|risk(?:s|y)?|"
    r"secur(?:e|ity|ing)|privacy|"
    r"should|must|need to|ethical|ethic(?:s)?|"
    r"law(?:s)?|legal|policy|standard(?:s)?|"
    r"audit(?:s|ing|ed)?|oversight|governance"
    r"|warn(?:s|ed|ing)?|danger|threat(?:s)?|crisis|crash|"
    r"ban(?:s|ned|ning)?|prohibi(?:t|ted|tion)|fine(?:s|d)?|penalt(?:y|ies))\b",
    re.I,
)
CREATE_KW = re.compile(
    r"\b(novel|breakthrough|discover(?:y|ies|ed)?|"
    r"invent(?:s|ed|ion)?|first[-\s]ever|"
    r"pioneer(?:s|ed|ing)?|revolutionary|"
    r"paradigm[.\s]shift|new[.\s]approach|"
    r"generat(?:e|es|ing|ed|ive)|synthes(?:is|ize|izes|ized)"
    r"|propos(?:e|es|ed|ing)|present(?:s|ed|ing))\b",
    re.I,
)

LEVEL_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("create", CREATE_KW),
    ("evaluate", EVALUATE_KW),
    ("analyze", ANALYZE_KW),
    ("apply", APPLY_KW),
    ("understand", UNDERSTAND_KW),
    ("remember", REMEMBER_KW),
]

GOV_ORG_DOMAIN = re.compile(r"\.(gov|mil|edu|org)$", re.I)
ARXIV_DOMAIN = re.compile(r"arxiv\.org", re.I)
