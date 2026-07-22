"""General utility functions extracted from build.py.

Text/HTML processing, content grouping, heading extraction, sanitization,
and other general-purpose helpers used by the AcaciaFund build pipeline.
"""

from __future__ import annotations

import os
import re
import unicodedata
from collections import defaultdict
from datetime import datetime, timezone

from config import PROJECT_ROOT

CJK_RE = re.compile(r"[\u4e00-\u9fff\u3400-\u4dbf\uff00-\uffef]")
EMOJI_RE = re.compile(
    r"[\U0001F300-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF\u2600-\u27BF\u2B50\U0001F1E0-\U0001F1FF]"
)

MERMAID_PLACEHOLDER = "@@MERMAID_"
_mermaid_counter = 0

HEADING_RE = re.compile(r"<h([23])([^>]*)>(.*?)</h\1>", re.IGNORECASE | re.DOTALL)

DOMAIN_BREAKDOWN_RE = re.compile(
    r"<li>[^<]*?([A-Za-z]+)\s*:\s*(\d+)%\s*of sources\s*</li>",
    re.IGNORECASE,
)


def load_admin_credentials():
    """Load admin credentials from .env file. Exits if not set."""
    env_path = PROJECT_ROOT / ".env"
    username = os.environ.get("ADMIN_USERNAME")
    password = os.environ.get("ADMIN_PASSWORD")

    if not username or not password:
        if env_path.exists():
            try:
                content = env_path.read_text(encoding="utf-8")
                for line in content.split("\n"):
                    line = line.strip()
                    if line.startswith("#") or not line:
                        continue
                    if "=" in line:
                        key, value = line.split("=", 1)
                        key = key.strip()
                        value = value.strip()
                        if key == "ADMIN_USERNAME":
                            username = value
                        elif key == "ADMIN_PASSWORD":
                            password = value
            except (OSError, ValueError):
                pass

    if not username or not password:
        print("WARNING: ADMIN_USERNAME/ADMIN_PASSWORD not set. Using dev defaults (admin/admin).")
        print("WARNING: Set these via environment variables or a .env file for production.")
        username = "admin"
        password = "admin"

    return username, password


def get_topic_icons(tags: list[str]) -> list[str]:
    """Map article tags to resolved SVG path data, returning up to 3 matches."""
    if not tags:
        return []
    lower_tags = {t.lower() for t in tags}
    matched = []
    seen = set()

    from core.visuals import SUBTOPIC_CATEGORIES, TOPIC_ICONS

    for tag in lower_tags:
        if tag in TOPIC_ICONS and tag not in seen:
            from core.visuals import resolve_topic_icon

            path = resolve_topic_icon(tag)
            if path:
                matched.append(path)
                seen.add(tag)
                if len(matched) >= 3:
                    break
    if len(matched) < 3:
        for subs in SUBTOPIC_CATEGORIES.values():
            for key, keywords in subs.items():
                if key in seen:
                    continue
                if lower_tags & keywords:
                    from core.visuals import resolve_topic_icon

                    path = resolve_topic_icon(key)
                    if path:
                        matched.append(path)
                        seen.add(key)
                        if len(matched) >= 3:
                            break
            if len(matched) >= 3:
                break
    if len(matched) < 3:
        for tag in lower_tags:
            for tkey in TOPIC_ICONS:
                if tkey in seen:
                    continue
                if tkey in tag or tag in tkey:
                    from core.visuals import resolve_topic_icon

                    path = resolve_topic_icon(tkey)
                    if path:
                        matched.append(path)
                        seen.add(tkey)
                        if len(matched) >= 3:
                            break
            if len(matched) >= 3:
                break
    return matched


def add_lazy_loading(html: str) -> str:
    return re.sub(r"<img(?![^>]*loading=)", '<img loading="lazy" decoding="async"', html)


def _get_created(post):
    dt = getattr(post, "created_at", None)
    if dt is None:
        return None
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return None
    if hasattr(dt, "tzinfo") and dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def group_by_pillar(content_list: list) -> dict[str, list]:
    groups: dict[str, list] = defaultdict(list)
    for c in content_list:
        p = c.pillar
        if not p:
            continue
        groups[p].append(c)
    for g in groups.values():
        g.sort(key=lambda x: _get_created(x) or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
    return dict(groups)


def extract_headings(html: str) -> tuple[str, list[dict]]:
    toc = []
    id_counts: dict[str, int] = {}

    def _repl(m):
        tag = m.group(1)
        inner = m.group(3)
        text = re.sub(r"<[^>]+>", "", inner).strip()
        base_id = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "section"
        if base_id in id_counts:
            id_counts[base_id] += 1
            id_str = f"{base_id}-{id_counts[base_id]}"
        else:
            id_counts[base_id] = 0
            id_str = base_id
        toc.append({"id": id_str, "text": text, "tag": f"h{tag}"})
        return f'<h{tag} id="{id_str}">{inner}</h{tag}>'

    html = HEADING_RE.sub(_repl, html)
    return html, toc


def find_related(posts: list, current, max_items: int = 3) -> list:
    """Score relatedness by pillar match (40%), tag overlap (40%), curated relations (20%).

    Curated relations (from current.curated_relations) always appear first
    when they match a post slug in the candidate pool.
    """
    current_tags = set(t.lower() for t in current.tags)
    current_pillar = current.pillar or ""

    scored: list[tuple[float, object]] = []
    seen_slugs: set[str] = set()

    for r in current.curated_relations or []:
        rslug = r.get("slug", "")
        if not rslug:
            continue
        for p in posts:
            if p.slug == rslug and p.slug != current.slug:
                scored.append((2.0, p))
                seen_slugs.add(p.slug)
                break

    for p in posts:
        if p.slug == current.slug or p.slug in seen_slugs:
            continue
        pillar_match = 1.0 if p.pillar and p.pillar == current_pillar else 0.0
        tag_overlap = len(current_tags & set(t.lower() for t in p.tags))
        tag_score = min(tag_overlap / max(len(current_tags), 1), 1.0)
        score = pillar_match * 0.4 + tag_score * 0.4
        if score > 0:
            scored.append((score, p))
    scored.sort(key=lambda x: -x[0])
    return [p for _, p in scored[:max_items]]


def find_cross_pillar(
    current,
    all_content: list,
    ontology=None,
    max_items: int = 4,
    _concept_cache: dict | None = None,
) -> list[dict]:
    """Find related content from *other* pillars sharing ontology concepts.

    Returns a list of dicts with slug, title, description, pillar, and shared_concepts.
    Uses _concept_cache (slug->set of concept_ids) to avoid re-extracting.
    """
    if not ontology or ontology.concept_count() == 0:
        return []

    if _concept_cache is None:
        _concept_cache = {}

    from core.ontology import extract_concepts_from_text

    concept_labels = {c.id: c.label for c in ontology._concepts.values()}

    def _get_concept_ids(item):
        if item.slug in _concept_cache:
            return _concept_cache[item.slug]
        tags_text = " ".join(item.tags or [])
        body_text = re.sub(r"<[^>]+>", " ", item.body_html or "")
        combined = f"{item.title or ''} {tags_text} {body_text[:400]}"
        matches = extract_concepts_from_text(combined, ontology)
        ids = {c.id for c, s in matches if s >= 0.3}
        _concept_cache[item.slug] = ids
        return ids

    current_pillar = current.pillar or "aml"
    current_ids = _get_concept_ids(current)
    if not current_ids:
        return []

    candidates = [c for c in all_content if c.pillar != current_pillar and c.slug != current.slug]

    scored = []
    for cand in candidates:
        cand_ids = _get_concept_ids(cand)
        shared = current_ids & cand_ids
        if shared:
            scored.append((len(shared), cand, shared))

    scored.sort(key=lambda x: -x[0])
    results = []
    for _, cand, shared_ids in scored[:max_items]:
        results.append({
            "slug": cand.slug,
            "title": cand.title,
            "description": getattr(cand, "description", ""),
            "pillar": cand.pillar or "aml",
            "shared_concepts": [concept_labels.get(cid, cid) for cid in list(shared_ids)[:5]],
        })
    return results


def sanitize_text(html: str, strip_emoji: bool = True) -> str:
    global _mermaid_counter
    html = unicodedata.normalize("NFKC", html)
    html = CJK_RE.sub("", html)
    if strip_emoji:
        html = EMOJI_RE.sub("", html)
    mermaid_map = {}

    def _save_mermaid(m):
        global _mermaid_counter
        key = f"{MERMAID_PLACEHOLDER}{_mermaid_counter}_"
        _mermaid_counter += 1
        mermaid_map[key] = m.group(0)
        return key

    html = re.sub(
        r'(<div class="mermaid"[^>]*>)(.*?)(</div>)', _save_mermaid, html, flags=re.DOTALL
    )
    html = re.sub(r"  +", " ", html)
    html = re.sub(r">\s+<", "><", html)
    for key, original in mermaid_map.items():
        html = html.replace(key, original)
    return html


def sanitize_domain_breakdown(html: str) -> str:
    """Normalize domain breakdown percentages so they sum to exactly 100."""
    matches = list(DOMAIN_BREAKDOWN_RE.finditer(html))
    if not matches:
        return html
    total_pct = sum(int(m.group(2)) for m in matches)
    if total_pct <= 100:
        return html
    rescaled = []
    for m in matches:
        domain = m.group(1)
        orig = int(m.group(2))
        capped = max(1, round(orig * 100 / total_pct))
        rescaled.append((domain, capped))
    diff = sum(r[1] for r in rescaled) - 100
    if diff != 0:
        idx = max(range(len(rescaled)), key=lambda i: rescaled[i][1])
        d, v = rescaled[idx]
        rescaled[idx] = (d, max(1, v - diff))
    for m, (domain, capped) in zip(matches, rescaled):
        html = html.replace(m.group(0), f"<li>{domain}: {capped}% of sources</li>", 1)
    return html


def strip_html_tag(tag: str) -> str:
    m = re.search(r">([^<]+)<", tag)
    return m.group(1).strip() if m else ""


def reading_time_minutes(html_or_text: str) -> int:
    text = re.sub(r"<[^>]+>", "", html_or_text)
    words = len(text.strip().split())
    code_blocks = len(re.findall(r"<pre><code>.*?</code></pre>", html_or_text, re.DOTALL))
    code_penalty_sec = code_blocks * 30
    minutes = (words / 150) + (code_penalty_sec / 60)
    return max(2, round(minutes)) if words > 100 else max(1, round(minutes))


def _dt_utc(val):
    if val is None:
        return None
    if isinstance(val, str):
        try:
            val = datetime.fromisoformat(val.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return None
    if hasattr(val, "tzinfo") and val.tzinfo is None:
        val = val.replace(tzinfo=timezone.utc)
    return val
