import hashlib
import random
import re

from .bloom_keywords import (
    ANALYZE_KW,
    APPLY_KW,
    CREATE_KW,
    EVALUATE_KW,
    REMEMBER_KW,
    UNDERSTAND_KW,
)

_VERBS = {
    "remember": "recalling",
    "understand": "explaining",
    "apply": "implementing",
    "analyze": "analyzing",
    "evaluate": "evaluating",
    "create": "creating",
}

_LEVEL_ORDER = ["remember", "understand", "apply", "analyze", "evaluate", "create"]

_REMEMBER_KW = REMEMBER_KW
_UNDERSTAND_KW = UNDERSTAND_KW
_APPLY_KW = APPLY_KW
_ANALYZE_KW = ANALYZE_KW
_EVALUATE_KW = EVALUATE_KW
_CREATE_KW = CREATE_KW

_GOV_ORG_DOMAIN = re.compile(r"\.(gov|mil|edu|org)$", re.I)
_ARXIV_DOMAIN = re.compile(r"arxiv\.org", re.I)


_KEYWORD_LEVELS = [
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


def level_label_en(level: str) -> str:
    labels = {
        "remember": "Remembering",
        "understand": "Understanding",
        "apply": "Applying",
        "analyze": "Analyzing",
        "evaluate": "Evaluating",
        "create": "Creating",
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


def _build_source_question(article: dict, pool: list[dict]) -> dict | None:
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
        "question": f'Which domain does the article "{_format_title(article["title"])}" come from?',
        "options": opts,
        "correct": domain,
    }


def _build_top_article_question(articles: list[dict]) -> dict | None:
    """Choose the article most relevant to the pillar topic."""
    if len(articles) < 2:
        return None
    relevant = [a for a in articles if a.get("url")]
    if len(relevant) < 2:
        return None
    random.shuffle(relevant)
    # Pick one article, ask about its source category
    a = relevant[0]
    domain = _extract_domain(a.get("url", ""))
    if not domain:
        return None
    # Categorize domain
    edu = bool(re.search(r"\.(edu|gov|mil|org)$", domain))
    news = bool(re.search(r"(reuters|bloomberg|ft\.com|wsj|nature|science)\.", domain))
    tech = bool(re.search(r"(techcrunch|theverge|arstechnica|wired|zdnet|github)\.", domain))
    cat = "educational/government" if edu else "news" if news else "technology" if tech else "other"
    other_articles = [x for x in relevant if x != a]
    random.shuffle(other_articles)
    titles = [a["title"][:50]] + [x["title"][:50] for x in other_articles[:3]]
    random.shuffle(titles)
    return {
        "bloom_level": "analyze",
        "type": "mc",
        "question": f"Which of these articles comes from a {cat} source?",
        "options": [t + ("…" if len(t) == 50 else "") for t in titles],
        "correct": a["title"][:50] + ("…" if len(a["title"]) > 50 else ""),
    }


def _build_source_tier_question(article: dict) -> dict | None:
    domain = _extract_domain(article.get("url", ""))
    if not domain:
        return None
    tiers = {
        r"arxiv\.org|\.edu|scholar\.google": "High – academic source",
        r"reuters\.com|bloomberg\.com|ft\.com|wsj\.com|nature\.com|science\.org": "High – reputable media",
        r"techcrunch\.com|theverge\.com|arstechnica\.com|wired\.com|zdnet\.com": "Medium – industry media",
        r"github\.com|stackoverflow\.com|medium\.com|reddit\.com": "Low – community source",
    }
    correct = "Unknown"
    for pat, label in tiers.items():
        if re.search(pat, domain, re.I):
            correct = label
            break
    all_labels = list(tiers.values()) + ["Low – community source"]
    others = [label for label in all_labels if label != correct]
    random.shuffle(others)
    return {
        "bloom_level": "evaluate",
        "type": "mc",
        "question": f"What is the credibility level of the source {domain}?",
        "options": [correct] + others[:3],
        "correct": correct,
    }


def _build_domain_type_question(article: dict) -> dict | None:
    domain = _extract_domain(article.get("url", ""))
    m = re.search(r"\.([a-z]+)$", domain)
    tld = m.group(1) if m else ""
    cats = {
        "com": "Commercial",
        "org": "Non-profit organization",
        "edu": "Educational",
        "gov": "Government",
        "mil": "Military",
        "io": "Technology (startup)",
        "ai": "Technology (AI)",
    }
    correct = cats.get(tld, "Other")
    return {
        "bloom_level": "understand",
        "type": "mc",
        "question": f"What type of domain is {domain}?",
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
            "question": f'Which domain does the article "{fmt_title}" come from?',
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
        "question": f'Why is the article "{_format_title(article["title"])}" relevant to {pillar_name}?',
    }


def _build_application_question(article: dict, pillar_name: str) -> dict:
    return {
        "bloom_level": "apply",
        "type": "open-ended",
        "question": f'How can concepts from the article "{_format_title(article["title"])}" be applied in practice in {pillar_name}?',
    }


def _build_create_question(articles: list[dict], pillar_name: str) -> dict:
    themes = list(set(a.get("title", "").split()[0] for a in articles if a.get("title")))
    theme = random.choice(themes[:5]) if themes else pillar_name
    return {
        "bloom_level": "create",
        "type": "open-ended",
        "question": f'Based on articles from {pillar_name}, propose a new research direction or project inspired by the topic "{theme}".',
    }


def _build_content_question(
    article_title: str, names: list[str], pillar_name: str, article_url: str = ""
) -> dict | None:
    """Ask about the main entity/organization described in an article."""
    title_lower = article_title.lower()

    def _is_good_name(n: str) -> bool:
        tokens = n.split()
        if len(tokens) < 2 or len(tokens) > 4:
            return False
        # Skip if it looks like an article title fragment
        if n.lower() in title_lower and len(n) > 20:
            return False
        if any(
            w.lower()
            in {
                "the",
                "this",
                "that",
                "these",
                "those",
                "what",
                "which",
                "where",
                "when",
                "how",
                "why",
                "there",
                "here",
                "they",
                "them",
                "their",
                "its",
                "our",
                "all",
                "each",
                "some",
                "any",
                "most",
                "many",
                "much",
                "new",
                "now",
                "first",
                "last",
                "next",
                "also",
                "just",
                "more",
                "such",
                "every",
                "after",
                "before",
                "into",
                "over",
                "between",
            }
            for w in tokens
        ):
            return False
        if tokens[0][0].islower():
            return False
        return True

    good_names = [n for n in names if _is_good_name(n)]
    if len(good_names) < 2:
        return None

    from collections import Counter

    name_counts = Counter(good_names)
    primary = name_counts.most_common(1)[0][0]
    others = [n for n in good_names if n != primary]
    random.shuffle(others)
    options = ([primary] + others[:3])[:4]
    random.shuffle(options)

    # Alternate question templates for variety
    template = random.choice(
        [
            'What organization/institution is the main subject of the article "{title}"?',
            'Which of these institutions is described in the article "{title}"?',
        ]
    )

    return {
        "bloom_level": "remember",
        "type": "mc",
        "question": template.format(title=_format_title(article_title)),
        "options": options,
        "correct": primary,
    }


def _build_factoid_question(sentence: str, article_title: str) -> dict | None:
    """Turn a factual sentence into a true/false question."""
    sentence = sentence.strip()
    if len(sentence) < 50 or len(sentence) > 200:
        return None
    words = sentence.split()
    if len(words) < 8:
        return None
    nums = re.findall(r"\b(\d+)\b", sentence)
    if not nums:
        return None
    return {
        "bloom_level": "understand",
        "type": "tf",
        "question": f'Is the following statement true according to the article "{_format_title(article_title)}"?',
        "statement": sentence[:180],
        "correct": True,
    }


def generate_quiz_questions(
    articles: list[dict], pillar_name: str = "", scraped: dict[str, dict] | None = None
) -> list[dict]:
    from .data import PILLARS

    pillar_label = (
        PILLARS.get(pillar_name, {}).get("label", pillar_name) if pillar_name else pillar_name
    )
    questions: list[dict] = []
    pool = articles[:]
    random.shuffle(pool)
    all_articles = pool
    candidates = []

    # ── Content-based questions (from scraped text) ──
    content_used = 0
    if scraped:
        for a in all_articles[:20]:
            key = hashlib.md5(a.get("url", "").encode()).hexdigest()[:12]
            cached = scraped.get(key, {})
            facts = cached.get("facts", {})
            names = facts.get("names", [])
            sentences = facts.get("sentences", [])
            # Entity question
            if names:
                q = _build_content_question(a.get("title", ""), names, pillar_label)
                if q:
                    candidates.append(q)
                    content_used += 1
            # Factoid question using text sentence
            if sentences:
                for s in sentences[:3]:
                    q = _build_factoid_question(s, a.get("title", ""))
                    if q:
                        candidates.append(q)
                        content_used += 1
                        break
            if content_used >= 6:
                break
            if content_used >= 4:
                break

    # ── Metadata-based questions (fallback) ──
    for a in pool[:6]:
        q = _build_source_question(a, all_articles)
        if q:
            candidates.append(q)
    q = _build_top_article_question(all_articles)
    if q:
        candidates.append(q)
    for a in pool[:4]:
        q = _build_source_tier_question(a)
        if q:
            candidates.append(q)
    for a in pool[:3]:
        q = _build_domain_type_question(a)
        if q:
            candidates.append(q)
    for a in pool[:3]:
        candidates.append(_build_pillar_question(a, pillar_label))
    for a in pool[:3]:
        candidates.append(_build_application_question(a, pillar_label))
    candidates.append(_build_create_question(all_articles, pillar_label))

    # Filter to one question per Bloom level per post
    levels_present: list[str] = []
    seen: set[str] = set()
    for a in articles:
        lvl = classify_bloom_level(a)
        if lvl not in seen:
            seen.add(lvl)
            levels_present.append(lvl)
    levels_present.sort(key=level_index)

    for lvl in levels_present:
        lvl_candidates = [c for c in candidates if c.get("bloom_level") == lvl]
        if lvl_candidates:
            chosen = random.choice(lvl_candidates)
        else:
            chosen = {
                "bloom_level": lvl,
                "type": "open-ended",
                "question": f"Discuss key aspects of {pillar_label} related to the {level_label_en(lvl)} level.",
            }
        questions.append(chosen)

    return questions


# ── Rich flashcards ──

_BIGRAM_SKIP_WORDS = {
    "after",
    "ahead",
    "amid",
    "among",
    "before",
    "behind",
    "below",
    "despite",
    "during",
    "facing",
    "following",
    "including",
    "inside",
    "into",
    "minus",
    "near",
    "next",
    "onto",
    "outside",
    "past",
    "pending",
    "plus",
    "since",
    "through",
    "toward",
    "under",
    "until",
    "upon",
    "within",
    "without",
    "makes",
    "takes",
    "gives",
    "puts",
    "sets",
    "gets",
    "lets",
    "goes",
    "came",
    "come",
    "bring",
    "brought",
    "seen",
    "shows",
    "showed",
    "pleads",
    "faces",
    "files",
    "hits",
    "wins",
    "loses",
    "joins",
    "says",
    "said",
    "told",
    "called",
    "named",
    "known",
    "used",
    "turns",
    "moves",
    "makes",
    "backs",
    "plans",
    "hopes",
    "aims",
    "wants",
    "needs",
    "looks",
    "seeks",
    "forms",
    "helped",
    "what",
    "when",
    "where",
    "why",
    "which",
    "who",
    "whom",
    "whose",
    "this",
    "that",
    "these",
    "those",
    "every",
    "each",
    "such",
    "same",
    "much",
    "many",
    "some",
    "any",
    "all",
    "both",
    "few",
    "most",
    "very",
    "just",
    "only",
    "also",
    "still",
    "even",
    "quite",
    "rather",
    "first",
    "last",
    "next",
    "second",
    "third",
    "final",
    "early",
    "late",
    "best",
    "worst",
    "good",
    "bad",
    "big",
    "new",
    "old",
    "high",
    "low",
    "long",
    "short",
    "wide",
    "deep",
    "full",
    "open",
    "real",
    "sure",
}


def _extract_bigrams(title: str) -> list[str]:
    cleaned = re.sub(r"[^a-zA-Z\s]", " ", title)
    tokens = cleaned.split()
    bigrams: list[str] = []
    for i in range(len(tokens) - 1):
        w1, w2 = tokens[i], tokens[i + 1]
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
    from .data import ALL_ENTITIES, ENTITY_DEFS

    entity_defs = ENTITY_DEFS

    seen_terms: set[str] = set()
    flashcards: list[dict] = []
    title_text = " ".join(a.get("title", "") for a in articles)
    title_lower = title_text.lower()

    # 1. Match known entities appearing in titles
    for ent, definition in entity_defs.items():
        if ent.lower() in title_lower and ent not in seen_terms:
            seen_terms.add(ent)
            source = next(
                (a["title"] for a in articles if ent.lower() in a.get("title", "").lower()), ""
            )
            flashcards.append(
                {
                    "term": ent,
                    "definition": definition,
                    "pillar": pillar_name,
                    "source": source,
                    "source_type": "entity",
                }
            )

    # 2. Extract meaningful bigrams with article context
    for a in articles:
        bigrams = _extract_bigrams(a.get("title", ""))
        for bg in bigrams:
            if bg not in seen_terms and len(seen_terms) < 80:
                seen_terms.add(bg)
                flashcards.append(
                    {
                        "term": bg,
                        "definition": next(
                            (
                                f"Topic from article: {a['title']}"
                                for a in articles
                                if bg.lower() in a.get("title", "").lower()
                            ),
                            f"Term from the field of {pillar_name or 'this field'}",
                        ),
                        "pillar": pillar_name,
                        "source": a.get("title", ""),
                        "source_type": "bigram",
                    }
                )

    # 3. Cross-pillar concept cards: find terms mentioned across pillars
    cross_terms = [e for e in ALL_ENTITIES if title_lower.count(e.lower()) >= 2]
    for ct in cross_terms:
        if ct not in seen_terms:
            seen_terms.add(ct)
            defn = entity_defs.get(ct, f"Important concept: {ct}")
            flashcards.append(
                {
                    "term": ct,
                    "definition": defn,
                    "pillar": "cross-domain",
                    "source": "Appears across multiple articles",
                    "source_type": "cross",
                }
            )

    return flashcards[:120]
