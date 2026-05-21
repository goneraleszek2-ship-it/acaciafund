from collections import Counter

from .data import (
    PILLARS, DOMAIN_PATTERNS, KEYWORD_PATTERNS,
    extract_domain, categorize_domain, extract_entities, extract_themes, log,
)
from .score import compute_signal_score, build_history


def classify_story(story: dict) -> list[tuple[str, int]]:
    """Klasyfikacja z prekompilowanymi regexami — 10× szybciej."""
    from .data import DOMAIN_PATTERNS, KEYWORD_PATTERNS
    title = story.get("title", "").lower()
    url = story.get("url", "")
    domain = extract_domain(url)
    scores = []

    for pillar_name in PILLARS:
        score = 0
        for pat, s in DOMAIN_PATTERNS[pillar_name]:
            if pat.search(domain):
                score += s
        for pat in KEYWORD_PATTERNS[pillar_name]:
            if pat.search(title):
                score += 3
        if score > 0:
            scores.append((pillar_name, score))
    return scores


_SQI_HISTORY_CACHE: dict | None = None


def _get_history() -> dict:
    global _SQI_HISTORY_CACHE
    if _SQI_HISTORY_CACHE is None:
        _SQI_HISTORY_CACHE = build_history()
    return _SQI_HISTORY_CACHE


def build_pillar_signals(stories: list[dict], pillar_name: str) -> dict:
    if not stories:
        return {}
    scores = [s["points"] for s in stories]
    avg = sum(scores) / len(scores)
    max_s = max(scores)
    domains = [categorize_domain(extract_domain(s.get("url", ""))) for s in stories]
    domain_counts = Counter(domains)
    all_entities = []
    for s in stories:
        all_entities.extend(extract_entities(s["title"]))
    entity_counts = Counter(all_entities)

    history = _get_history()
    sqi_scores = [compute_signal_score(s, history) for s in stories]
    avg_sqi = sum(s["sqi"] for s in sqi_scores) / len(sqi_scores) if sqi_scores else 0
    top_sqi = sorted(
        [(s, q) for s, q in zip(stories, sqi_scores)],
        key=lambda x: x[1]["sqi"], reverse=True
    )[:3]

    return {
        "count": len(stories),
        "avg_score": avg,
        "max_score": max_s,
        "total_score": sum(scores),
        "has_outlier": max_s > 3 * avg if avg > 0 else False,
        "outlier_ratio": max_s / (avg or 1),
        "score_skew": "outlier" if max_s > 3 * avg and avg > 0 else "balanced",
        "domain_diversity": len(domain_counts),
        "top_domain": domain_counts.most_common(1)[0][0] if domain_counts else "nieznane",
        "top_domain_share": domain_counts.most_common(1)[0][1] / len(stories) if stories else 0,
        "top_entities": [e for e, _ in entity_counts.most_common(5)],
        "entity_coherence": "high" if entity_counts and len(entity_counts) < max(2, len(stories) * 0.4) else "low",
        "avg_sqi": round(avg_sqi, 3),
        "top_sqi_articles": [(s["title"], q) for s, q in top_sqi],
    }


def _sqi_badge(sqi: dict) -> str:
    score = sqi.get("sqi", 0)
    if score >= 0.6:
        return f" 🟢{score:.2f}"
    if score >= 0.35:
        return f" 🟡{score:.2f}"
    return f" 🔴{score:.2f}"


def _cap(text: str, n: int = 100) -> str:
    if len(text) <= n:
        return text
    return text[:n].rsplit(" ", 1)[0] + "…"


def generate_popular_summary(stories: list[dict], signals: dict,
                              pillar_name: str, config: dict) -> str:
    top = stories[0]
    label = config["label"]
    desc = config["description"]

    opening = (
        f"Dzisiaj w obszarze {desc} uwagę przykuwa przede wszystkim "
        f"„**{top['title']}**”, który zebrał {top['points']}⭐ na Hacker News"
    )

    if signals.get("has_outlier") and signals.get("outlier_ratio", 0) > 3:
        opening += (
            f" — wynik blisko {signals['outlier_ratio']:.0f}× wyższy od średniej "
            f"pozostałych artykułów w tym filarze. To nie przypadek: taki sygnał "
            f"oznacza, że społeczność technologiczną poruszył temat o dużym potencjale "
            f"kaskadowym."
        )
    else:
        opening += "."

    midsection = ""
    if signals.get("domain_diversity", 0) >= 3:
        midsection += (
            f" Co ciekawe, źródła są tu wyjątkowo zróżnicowane "
            f"({signals['domain_diversity']} różnych kategorii) — "
            f"temat rezonuje w wielu kręgach jednocześnie."
        )
    elif signals.get("domain_diversity", 0) == 1:
        midsection += (
            f" Dyskusja koncentruje się głównie wokół źródła z kategorii "
            f"**{signals['top_domain']}**."
        )

    entities = signals.get("top_entities", [])
    if entities:
        midsection += (
            f" Wśród kluczowych podmiotów pojawiają się "
            f"{', '.join(f'**{e}**' for e in entities[:3])}."
        )

    other = ""
    if len(stories) > 1:
        others = [s for s in stories[1:4] if s.get("points", 0) > 0]
        if others:
            other = (
                f" W tle przewijają się też: „{_cap(others[0]['title'], 70)}”"
                + (f" i „{_cap(others[1]['title'], 70)}”" if len(others) > 1 else "")
                + "."
            )

    closer = ""
    total = signals.get("total_score", 0)
    count = signals.get("count", 0)
    closer = (
        f" Łącznie w dzisiejszej syntezie {label} znalazło się {count} artykułów "
        f"o łącznej wartości {total}⭐. To tyle na dziś — więcej jutro."
    )

    return opening + midsection + other + closer


def build_analysis(stories: list[dict], pillar_name: str,
                   all_pillar_stories: dict[str, list[dict]] | None = None) -> dict:
    if not stories:
        return {
            "trending": "*Brak doniesień z tego okresu.*\n\n*Pipeline AcaciaFund kontynuuje skanowanie.*",
            "metaanalysis": "Brak danych do analizy w tym oknie czasowym.",
        }

    config = PILLARS[pillar_name]

    history = _get_history()
    story_sqis = {s.get("url", ""): compute_signal_score(s, history) for s in stories[:7]}
    trending = "\n".join(
        f"{i+1}. [{s['title']}]({s['url']})"
        + (f" ([dyskusja]({s['hn_url']}))" if s.get("hn_url") and s["hn_url"] != s["url"] else "")
        + f" (⭐{s['points']})"
        + _sqi_badge(story_sqis.get(s.get("url", ""), {}))
        for i, s in enumerate(stories[:7])
    )

    signals = build_pillar_signals(stories, pillar_name)
    meta = generate_popular_summary(stories, signals, pillar_name, config)

    return {
        "trending": trending,
        "metaanalysis": meta,
    }
