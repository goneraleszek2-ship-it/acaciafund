import math
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path

from .data import (
    PILLARS, ALL_ENTITIES, SOURCE_TIERS, DOMAIN_PATTERNS, KEYWORD_PATTERNS,
    extract_domain, log, CONTENT_DIR,
)


def source_authority(url: str) -> float:
    domain = extract_domain(url)
    for pattern, score in SOURCE_TIERS:
        if pattern.search(domain):
            return score
    return 0.2


def engagement_score(story: dict, now: datetime) -> float:
    points = story.get("points", 0) or 0
    if points <= 0:
        return 0.0
    created_at = story.get("created_at", "")
    try:
        created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        hours = max(0.1, (now - created).total_seconds() / 3600)
    except (ValueError, TypeError):
        hours = 48.0
    velocity = points / hours
    raw = points * (1 + math.log1p(velocity))
    return min(1.0, math.log1p(raw) / 8.0)


def _tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-z]\w{3,}", text.lower()))


_ARTICLE_URL_RE = re.compile(r"^\d+\.\s+\[(.+?)\]\(https?://")


def _extract_article_titles(fpath: Path) -> list[str]:
    content = fpath.read_text(encoding="utf-8")
    titles = []
    for line in content.splitlines():
        m = _ARTICLE_URL_RE.match(line.strip())
        if m:
            titles.append(m.group(1))
    return titles


def build_history(window_days: int = 7) -> dict[str, set[str]]:
    history: dict[str, set[str]] = {}
    now = datetime.now(timezone.utc)
    for i in range(1, window_days + 1):
        date = now - timedelta(days=i)
        date_str = date.strftime("%Y-%m-%d")
        all_titles: list[str] = []
        for pname, config in PILLARS.items():
            fpath = config["folder"] / f"{date_str}.md"
            if fpath.exists():
                all_titles.extend(_extract_article_titles(fpath))
        if all_titles:
            tokens: set[str] = set()
            for t in all_titles:
                tokens.update(_tokenize(t))
            history[date_str] = tokens
    return history


def novelty_score(title: str, history: dict[str, set[str]]) -> float:
    tokens = _tokenize(title)
    if not tokens:
        return 0.5
    max_sim = 0.0
    for hist_tokens in history.values():
        inters = tokens & hist_tokens
        union = tokens | hist_tokens
        sim = len(inters) / len(union) if union else 0
        if sim > max_sim:
            max_sim = sim
    return 1.0 - max_sim


def cross_pillar_count(title: str, url: str) -> int:
    title_lower = title.lower()
    domain = extract_domain(url)
    count = 0
    for pname in PILLARS:
        score = 0
        for pat, s in DOMAIN_PATTERNS[pname]:
            if pat.search(domain):
                score += s
        for pat in KEYWORD_PATTERNS[pname]:
            if pat.search(title_lower):
                score += 3
        if score > 0:
            count += 1
    return count


def entity_density(title: str) -> float:
    if not title:
        return 0.0
    title_lower = title.lower()
    matches = sum(1 for ent in ALL_ENTITIES if ent.lower() in title_lower)
    return min(1.0, matches / 3.0)


def compute_signal_score(
    story: dict,
    history: dict[str, set[str]] | None = None,
    now: datetime | None = None,
) -> dict:
    if now is None:
        now = datetime.now(timezone.utc)
    if history is None:
        history = build_history()

    title = story.get("title", "")
    url = story.get("url", "")

    eng = engagement_score(story, now)
    auth = source_authority(url)
    novel = novelty_score(title, history)

    age_hours = 48.0
    try:
        created = datetime.fromisoformat(
            story.get("created_at", "").replace("Z", "+00:00")
        )
        age_hours = (now - created).total_seconds() / 3600
    except (ValueError, TypeError):
        pass
    timeliness = max(0.0, 1.0 - (age_hours / 72.0))

    cp = cross_pillar_count(title, url)
    ent = entity_density(title)

    composite = (
        0.30 * eng
        + 0.20 * auth
        + 0.20 * novel
        + 0.10 * min(1.0, cp / 3.0)
        + 0.10 * timeliness
        + 0.10 * ent
    )

    return {
        "sqi": round(composite, 3),
        "engagement": round(eng, 3),
        "authority": round(auth, 3),
        "novelty": round(novel, 3),
        "timeliness": round(timeliness, 3),
        "cross_pillar": cp,
        "entity_density": round(ent, 3),
    }
