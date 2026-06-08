"""Enhanced classification with TF-IDF-like scoring, cross-pillar disambiguation,
and article-level content analysis integration."""

import math
import re
from collections import Counter
from datetime import datetime, timezone, timedelta

from .data import (
    PILLARS, DOMAIN_PATTERNS, KEYWORD_PATTERNS,
    extract_domain, categorize_domain, extract_entities, extract_themes, log,
    ALL_ENTITIES, KNOWN_ENTITIES,
)
from .score import compute_signal_score, build_history


def _tf_score(text: str, keyword: str) -> float:
    """Term frequency–like score: count occurrences, log-normalized."""
    count = text.lower().count(keyword.lower())
    if count == 0:
        return 0.0
    return 1.0 + math.log(count)


def _pillar_text_signature(pillar_name: str) -> tuple[set[str], set[str], set[str]]:
    """Build a richer text signature for each pillar using keywords + entities + domains."""
    cfg = PILLARS[pillar_name]
    kws = set(kw.lower() for kw in cfg["keywords"])
    ents = set(e.lower() for e in KNOWN_ENTITIES.get(pillar_name, set()))
    domains = set()
    for d in cfg["domain_scores"]:
        domains.add(d.lower())
    return kws, ents, domains


def classify_story(story: dict) -> list[tuple[str, float]]:
    """Enhanced classification with TF-IDF-like scoring and cross-pillar disambiguation.

    Returns list of (pillar_name, confidence) sorted descending.
    """
    title = story.get("title", "")
    url = story.get("url", "")
    domain = extract_domain(url)
    title_lower = title.lower()

    scores: list[tuple[str, float]] = []

    for pillar_name in PILLARS:
        kws, ents, domains = _pillar_text_signature(pillar_name)
        cfg = PILLARS[pillar_name]
        score = 0.0
        matched_keywords = 0

        # Domain scoring (weighted)
        for pat, s in DOMAIN_PATTERNS[pillar_name]:
            if pat.search(domain):
                score += s * 0.15
                matched_keywords += 1

        # Keyword TF scoring
        for kw in kws:
            tf = _tf_score(title, kw)
            if tf > 0:
                score += tf * 2.0
                matched_keywords += 1

        # Entity scoring
        for ent in ents:
            if ent in title_lower:
                score += 5.0
                matched_keywords += 1

        # Domain taxonomy category boost
        cat = categorize_domain(domain)
        pillar_domain_cats = {
            "aml": {"regulacje", "finanse"},
            "stock": {"finanse", "technologia"},
            "data-engineering": {"technologia", "nauka"},
        }
        if cat in pillar_domain_cats.get(pillar_name, set()):
            score += 2.0

        # ArXiv category boost per pillar
        if "arxiv.org" in domain:
            arxiv_pillar_map = {
                "aml": {"q-fin", "cs"},
                "stock": {"q-fin", "cs"},
                "data-engineering": {"cs", "stat"},
            }
            for ap in arxiv_pillar_map.get(pillar_name, set()):
                if ap in title_lower:
                    score += 3.0

        if matched_keywords > 0:
            scores.append((pillar_name, score))

    # Cross-pillar disambiguation: if multiple pillars match, boost the most specific
    if len(scores) >= 2:
        scores.sort(key=lambda x: x[1], reverse=True)
        best, second = scores[0], scores[1]
        if best[1] > second[1] * 1.5:
            # Clear winner — keep as is
            pass
        elif best[1] >= second[1] * 1.1:
            # Slight edge — boost winner slightly
            scores[0] = (best[0], best[1] * 1.2)
        else:
            # Too close — check entity tiebreaker
            title_lower = story.get("title", "").lower()
            for ent in ALL_ENTITIES:
                if ent.lower() in title_lower:
                    for pname in PILLARS:
                        if ent.lower() in (e.lower() for e in KNOWN_ENTITIES.get(pname, set())):
                            scores = [(pname, scores[0][1] * 1.5) if s[0] == pname else (s[0], s[1] * 0.8) for s in scores]
                            break
                    break

    scores.sort(key=lambda x: x[1], reverse=True)
    return scores


def classify_bloom_level_enhanced(story: dict, scraped_text: str | None = None) -> str:
    """Enhanced Bloom classification using title + optional scraped text."""
    from .bloom_keywords import CREATE_KW, EVALUATE_KW, ANALYZE_KW, APPLY_KW, UNDERSTAND_KW, REMEMBER_KW

    title = story.get("title", "")
    url = story.get("url", "")
    points = story.get("points", 0) or 0
    text = (title + " " + (scraped_text or "")).lower()

    # High-signal patterns
    create_signals = CREATE_KW
    evaluate_signals = EVALUATE_KW
    analyze_signals = ANALYZE_KW
    apply_signals = APPLY_KW
    understand_signals = UNDERSTAND_KW
    remember_signals = REMEMBER_KW

    signals = [
        ("create", create_signals),
        ("evaluate", evaluate_signals),
        ("analyze", analyze_signals),
        ("apply", apply_signals),
        ("understand", understand_signals),
        ("remember", remember_signals),
    ]

    # Score each level
    level_scores: dict[str, float] = {}
    for level, pattern in signals:
        matches = pattern.findall(text)
        level_scores[level] = len(matches) + (1 if pattern.search(title) else 0)

    # Boosts
    if points >= 200:
        level_scores["evaluate"] = level_scores.get("evaluate", 0) + 2
    elif points >= 50:
        level_scores["understand"] = level_scores.get("understand", 0) + 1

    if not any(level_scores.values()):
        return "understand"

    return max(level_scores, key=level_scores.get)


_SQI_HISTORY_CACHE: dict | None = None
_TREND_CACHE: dict | None = None


def _get_history() -> dict:
    global _SQI_HISTORY_CACHE
    if _SQI_HISTORY_CACHE is None:
        _SQI_HISTORY_CACHE = build_history()
    return _SQI_HISTORY_CACHE


def _get_trends() -> dict:
    """Build trend data: entity mention frequency over last 7 days."""
    global _TREND_CACHE
    if _TREND_CACHE is not None:
        return _TREND_CACHE
    history = _get_history()
    trends: dict[str, dict] = {}
    for date_str, tokens in history.items():
        for token in tokens:
            if token not in trends:
                trends[token] = {"count": 0, "dates": []}
            trends[token]["count"] += 1
            trends[token]["dates"].append(date_str)
    _TREND_CACHE = trends
    return trends


def detect_trending_topics(stories: list[dict]) -> list[dict]:
    """Detect which topics in today's stories are trending compared to 7d history."""
    trends = _get_trends()
    title_words = Counter()
    for s in stories:
        words = re.findall(r"[a-z]\w{3,}", s.get("title", "").lower())
        title_words.update(words)

    trending = []
    total_days = max(1, len(set(
        d for t in trends.values() for d in t.get("dates", [])
    )))
    for word, count in title_words.most_common(20):
        hist = trends.get(word, {"count": 0})
        avg_daily = hist["count"] / total_days if total_days > 0 else 0
        if avg_daily > 0:
            ratio = count / (avg_daily + 0.1)
            if ratio > 2.0:
                trending.append({
                    "word": word,
                    "today": count,
                    "avg_daily": round(avg_daily, 2),
                    "ratio": round(ratio, 1),
                })

    return sorted(trending, key=lambda x: x["ratio"], reverse=True)[:5]


def compute_cross_pillar_scores(story: dict, all_pillar_stories: dict[str, list[dict]]) -> dict:
    """Compute how relevant a story is across pillars."""
    title_lower = story.get("title", "").lower()
    result = {}
    for pillar, stories in all_pillar_stories.items():
        if story in stories:
            continue  # same pillar
        for s in stories:
            other_title = s.get("title", "").lower()
            overlap = len(set(title_lower.split()) & set(other_title.split()))
            if overlap >= 3:
                result[pillar] = result.get(pillar, 0) + overlap
    return result


def build_pillar_signals(stories: list[dict], pillar_name: str,
                         scraped: dict[str, dict] | None = None) -> dict:
    """Enhanced signal building with content analysis."""
    if not stories:
        return {}

    scores = [s["points"] for s in stories]
    avg = sum(scores) / len(scores) if scores else 0
    max_s = max(scores) if scores else 0

    domains = [categorize_domain(extract_domain(s.get("url", ""))) for s in stories]
    domain_counts = Counter(domains)

    all_entities: list[str] = []
    all_sentences: list[str] = []
    numbers_found: list[tuple[str, str]] = []
    for s in stories:
        all_entities.extend(extract_entities(s["title"]))
        # Scraped content analysis
        if scraped:
            from .scraper import _url_key
            key = _url_key(s.get("url", ""))
            cached = scraped.get(key, {})
            facts = cached.get("facts", {})
            all_entities.extend(facts.get("names", []))
            for sent in facts.get("sentences", []):
                all_sentences.append(sent)
                nums = re.findall(r'\$?(\d[\d,]*\.?\d*)\s*(million|billion|trillion|mln|bln|%)?', sent, re.I)
                for num, unit in nums[:2]:
                    numbers_found.append((num + unit, sent[:100]))

    entity_counts = Counter(all_entities)

    history = _get_history()
    sqi_scores = [compute_signal_score(s, history) for s in stories]
    avg_sqi = sum(q["sqi"] for q in sqi_scores) / len(sqi_scores) if sqi_scores else 0

    top_sqi = sorted(
        [(s, q) for s, q in zip(stories, sqi_scores)],
        key=lambda x: x[1]["sqi"], reverse=True
    )[:3]

    trending = detect_trending_topics(stories)

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
        "top_entities": [e for e, _ in entity_counts.most_common(8)],
        "entity_coherence": "high" if entity_counts and len(entity_counts) < max(2, len(stories) * 0.4) else "low",
        "avg_sqi": round(avg_sqi, 3),
        "top_sqi_articles": [(s["title"], q) for s, q in top_sqi],
        "trending_topics": trending,
        "key_numbers": numbers_found[:5],
        "sentences_count": len(all_sentences),
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
    return text[:n].rsplit(" ", 1)[0] + "..."


def generate_popular_summary(stories: list[dict], signals: dict,
                              pillar_name: str, config: dict) -> str:
    """Enhanced meta-analysis with trend data and key statistics."""
    if not stories:
        return "No data to analyze in this time window."

    top = stories[0]
    label = config["label"]
    desc = config["description"]

    opening = (
            f"Today in {desc}, the top story is "
            f"\"**{top['title']}**\", which gathered {top['points']} points on Hacker News"
    )

    if signals.get("has_outlier") and signals.get("outlier_ratio", 0) > 3:
        opening += (
                f" -- nearly {signals['outlier_ratio']:.0f}x higher than the average "
                f"of other articles. This is a strong signal that the topic resonates broadly."
        )
    else:
        opening += "."

    midsection = ""
    if signals.get("domain_diversity", 0) >= 3:
        midsection += (
                f" Sources are diverse ({signals['domain_diversity']} categories) -- "
                f"the topic cuts across different circles."
        )
    elif signals.get("domain_diversity", 0) == 1:
        midsection += (
                f" Discussion centers mainly on a source from the "
                f"**{signals['top_domain']}** category."
        )

    # Trending topics
    trending = signals.get("trending_topics", [])
    if trending:
        midsection += (
                f" In today's articles, trending topics include: "
                + ", ".join(f"**{t['word']}** ({t['ratio']}x above average)" for t in trending[:3])
            + "."
        )

    # Key numbers
    key_nums = signals.get("key_numbers", [])
    if key_nums:
        midsection += (
                f" Key numbers include: "
            + "; ".join(f"{n[0]}" for n in key_nums[:3])
            + "."
        )

    entities = signals.get("top_entities", [])
    if entities:
        midsection += (
                f" Key entities: "
            + ", ".join(f"**{e}**" for e in entities[:4])
            + "."
        )

    other = ""
    if len(stories) > 1:
        others = [s for s in stories[1:4] if s.get("points", 0) > 0]
        if others:
            other = (
                f" In the background: \"{_cap(others[0]['title'], 70)}\""
                + (f", \"{_cap(others[1]['title'], 70)}\"" if len(others) > 1 else "")
                + "."
            )

    closer = ""
    total = signals.get("total_score", 0)
    count = signals.get("count", 0)
    avg_sqi = signals.get("avg_sqi", 0)
    closer = (
            f" Total: {count} articles with {total} points. "
            f"Average SQI (Signal Quality Index): {avg_sqi:.3f}. "
            f"That's all for today -- more tomorrow."
    )

    return opening + midsection + other + closer


def build_analysis(stories: list[dict], pillar_name: str,
                   all_pillar_stories: dict[str, list[dict]] | None = None,
                   scraped: dict[str, dict] | None = None) -> dict:
    """Build complete analysis with enhanced signals."""
    if not stories:
        return {
        "trending": "*No reports for this period.*\n\n*AcaciaFund pipeline continues scanning.*",
        "metaanalysis": "No data to analyze in this time window.",
            "signals": {},
        }

    config = PILLARS[pillar_name]
    history = _get_history()
    story_sqis = {s.get("url", ""): compute_signal_score(s, history) for s in stories[:7]}

    trending = "\n".join(
        f"{i+1}. [{s['title']}]({s['url']})"
            + (f" ([discussion]({s['hn_url']}))" if s.get("hn_url") and s["hn_url"] != s["url"] else "")
            + f" ({s['points']} pts)"
        + _sqi_badge(story_sqis.get(s.get("url", ""), {}))
        for i, s in enumerate(stories[:7])
    )

    signals = build_pillar_signals(stories, pillar_name, scraped)
    meta = generate_popular_summary(stories, signals, pillar_name, config)

    return {
        "trending": trending,
        "metaanalysis": meta,
        "signals": signals,
    }
