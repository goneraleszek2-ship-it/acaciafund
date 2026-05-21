from collections import Counter

from .data import (
    PILLARS, DOMAIN_PATTERNS, KEYWORD_PATTERNS,
    RULES_META, RULES_SYSTEMS, RULES_CONN,
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


def apply_rules(rules: list[dict], signals: dict, stories: list[dict],
                 pname: str, extra: any = None) -> str:
    for rule in rules:
        if rule["match"](signals if extra is None else extra):
            return rule["generate"](signals if extra is None else extra, stories, pname)
    return ""


def _sqi_badge(sqi: dict) -> str:
    score = sqi.get("sqi", 0)
    if score >= 0.6:
        return f" 🟢{score:.2f}"
    if score >= 0.35:
        return f" 🟡{score:.2f}"
    return f" 🔴{score:.2f}"


def build_analysis(stories: list[dict], pillar_name: str,
                   all_pillar_stories: dict[str, list[dict]] | None = None) -> dict[str, str]:
    if not stories:
        return {
            "trending": "*Brak doniesień z tego okresu.*\n\n*Pipeline AcaciaFund kontynuuje skanowanie.*",
            "metaanalysis": "Brak danych do analizy w tym oknie czasowym.",
            "systems_lens": "Brak sygnałów. Z punktu widzenia teorii systemów, brak informacji to również informacja.",
            "connections": "Brak korelacji w tym oknie czasowym.",
        }

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

    meta = apply_rules(RULES_META, signals, stories, pillar_name)
    if not meta:
        meta = apply_rules([RULES_META[-1]], signals, stories, pillar_name)

    systems = apply_rules(RULES_SYSTEMS, signals, stories, pillar_name)
    if not systems:
        systems = apply_rules([RULES_SYSTEMS[-1]], signals, stories, pillar_name)

    # cross-pillar
    cp_signal = None
    if all_pillar_stories:
        for p in all_pillar_stories:
            if p == pillar_name:
                continue
            p_stories = all_pillar_stories.get(p, [])
            if not p_stories:
                continue
            p_signals = build_pillar_signals(p_stories, p)
            shared = set(signals.get("top_entities", [])) & set(p_signals.get("top_entities", []))
            if shared:
                a_in_p = next((s["title"] for s in all_pillar_stories[pillar_name]
                              if any(e.lower() in s["title"].lower() for e in shared)), "")
                cp_signal = {
                    "pair": (pillar_name, p),
                    "shared_entities": list(shared),
                    "strength": len(shared),
                    "article_a": a_in_p,
                }
                break

    conn = apply_rules(RULES_CONN, signals, stories, pillar_name, cp_signal)
    if not conn:
        conn = apply_rules([RULES_CONN[-1]], signals, stories, pillar_name, cp_signal)

    sqi = signals.get("avg_sqi", 0)
    sqi_label = "wysoka" if sqi >= 0.6 else "średnia" if sqi >= 0.35 else "niska"
    top_sqi_items = signals.get("top_sqi_articles", [])
    signal_quality = (
        f"**SQI (Signal Quality Index)**: {sqi:.2f} — jakość sygnału w tym oknie: **{sqi_label}**. "
        f"Średnia ważona 6 wymiarów: zaangażowanie społeczności, autorytet źródła, "
        f"nowość tematu, aktualność, gęstość encji i znaczenie cross-pillar. "
        + (f"Najwyżej punktowane: „{top_sqi_items[0][0]}” ({top_sqi_items[0][1]['sqi']:.2f})"
           if top_sqi_items else "")
    )

    return {
        "trending": trending,
        "metaanalysis": meta,
        "systems_lens": systems,
        "connections": conn,
        "signal_quality": signal_quality,
        "avg_sqi": signals.get("avg_sqi", 0),
    }
