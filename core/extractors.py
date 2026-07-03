"""Deterministic extractors for structured data from article content.

No LLM dependency — pure regex and rule-based extraction for:
- Timeline events (dates + descriptions)
- Process flows (sequential steps with arrows/numbering)
- Numeric comparisons (X vs Y, percentages)
"""

import re
from typing import Any

# ── Date patterns ──────────────────────────────────────────────

_MONTHS = r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
_MONTHS += r"Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"

_DATE_PATTERNS = [
    re.compile(rf"({_MONTHS})\s+(\d{{4}})", re.IGNORECASE),
    re.compile(rf"({_MONTHS})\s+(\d{{1,2}}),?\s+(\d{{4}})", re.IGNORECASE),
    re.compile(
        r"(?<![\w.])(?:in|by|since|until|from|of|after|before|around|between|during|c\.)\s+(\d{4})\b",
        re.IGNORECASE,
    ),
    re.compile(r"\b(19[8-9]\d|20[0-2]\d|2030)\b"),
    re.compile(r"Q([1-4])\s*'?(\d{2})\b"),
    re.compile(r"(\d{4})–(\d{4})"),
]

_PASSAGE_BOUNDARY = re.compile(r"(?:<br\s*/?>|</p>|</li>|</blockquote>|\.\s+(?=[A-Z]))")


def extract_timeline(body_text: str, title: str = "") -> list[dict[str, Any]]:
    """Extract date-event pairs from article body.

    Returns chronologically sorted list of {date, event} dicts.
    """
    text = re.sub(r"<[^>]+>", " ", body_text)
    text = re.sub(r"\s+", " ", text).strip()

    passages = _split_passages(text)
    candidates: list[dict] = []

    for passage in passages:
        matched = False
        date_info = None

        for pat_idx, pat in enumerate(_DATE_PATTERNS):
            m = pat.search(passage)
            if m:
                g = m.groups()
                if pat_idx == 0:
                    date_info = f"{g[0]} {g[1]}"
                elif pat_idx == 1:
                    month = g[0][:3]
                    date_info = f"{month} {g[2]}"
                elif pat_idx in (2, 3):
                    year = g[0]
                    try:
                        y = int(year)
                        if y < 1970 or y > 2030:
                            continue
                    except ValueError:
                        continue
                    date_info = year
                elif pat_idx == 4:
                    date_info = f"Q{g[0]} '{g[1]}"
                elif pat_idx == 5:
                    date_info = g[0]
                matched = True
                break

        if matched and date_info:
            event = passage[:300].strip()
            event = re.sub(r"^[^a-zA-Z0-9]*", "", event)
            event = re.sub(r"\s+", " ", event).strip()
            event = event.rstrip(".,;:")[:150]
            if len(event) > 20:
                candidates.append({"date": date_info, "event": event})

    candidates.sort(key=_date_sort_key)
    return candidates[:12]


def _split_passages(text: str) -> list[str]:
    """Split text into candidate passages for event extraction."""
    text = re.sub(r"\s+", " ", text).strip()
    # Split on boundary patterns without consuming the leading char of next sentence
    parts = _PASSAGE_BOUNDARY.split(text)
    result = []
    for p in parts:
        p = p.strip().lstrip(". ")
        if len(p) >= 15:
            result.append(p)
    return result


_ABBR_MONTH = {
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}


def _date_sort_key(d: dict) -> tuple:
    """Sort key: year first, then month (0 for bare years), then day (0)."""
    ds = d.get("date", "")
    if ds.startswith("Q"):
        try:
            q = int(ds[1])
            y_part = ds.split("'")[-1].strip()
            y = int("20" + y_part) if len(y_part) == 2 else int(y_part)
            return (y, q * 3, 0)
        except (ValueError, IndexError):
            return (9999, 0, 0)
    m = re.match(r"([A-Za-z]{3,})\s+(\d{4})", ds)
    if m:
        mn = _ABBR_MONTH.get(m.group(1).lower()[:3], 1)
        return (int(m.group(2)), mn, 0)
    m2 = re.match(r"([A-Za-z]{3,})\s+(\d{1,2}),?\s+(\d{4})", ds)
    if m2:
        mn = _ABBR_MONTH.get(m2.group(1).lower()[:3], 1)
        return (int(m2.group(3)), mn, int(m2.group(2)))
    try:
        return (int(ds), 99, 0)  # bare years sort after month+year
    except (ValueError, TypeError):
        return (9999, 0, 0)


# ── Flow/Process extraction ────────────────────────────────────

_STEP_PATTERNS = [
    re.compile(r"(?:^|\s)(\d+)\.\s+(.*)"),
    re.compile(r"(?:^|\s)(\d+)\)\s+(.*)"),
    re.compile(r"Step\s+(\d+)[:\-–\s]+(.*)", re.IGNORECASE),
    re.compile(
        r"(\w[\w\s]+?)\s*[\u2192\u27a1\u27a4\u25b8>]\s+(\w[\w\s]+?)(?=[,.;]|(?:\s+[\u2192\u27a1\u27a4\u25b8>])|$)"
    ),
    re.compile(r"(?:^|\s)(?:First|Firstly),?\s+(.+)", re.IGNORECASE),
    re.compile(r"(?:^|\s)(?:Then|Next|Second(?:ly)?|Afterwards),?\s+(.+)", re.IGNORECASE),
    re.compile(r"(?:^|\s)(?:Finally|Third(?:ly)?|Last(?:ly)?),?\s+(.+)", re.IGNORECASE),
]

_FLOW_KW = re.compile(
    r"\b(?:process|workflow|pipeline|flow|step|stage|phase|"
    r"sequence|transfer|transition|route|forward|propagat|"
    r"verif|review|report|monitor|screen|flagged?|escalat|rout(?:e|ing))"
    r"\b",
    re.IGNORECASE,
)


def extract_flow(body_text: str) -> list[dict[str, Any]]:
    """Extract sequential process steps from article body.

    Returns list of {step, description} dicts in order.
    Assumes the article contains at least one flow keyword.
    """
    text = re.sub(r"<[^>]+>", " ", body_text)
    text = re.sub(r"\s+", " ", text).strip()

    # Heuristic: skip if no flow keywords
    if not _FLOW_KW.search(text):
        return []

    lines = [line.strip() for line in text.split(".") if line.strip()]
    candidates: list[dict] = []
    seen = set()

    for line in lines:
        for pat_idx, pat in enumerate(_STEP_PATTERNS):
            m = pat.search(line)
            if not m:
                continue
            g = m.groups()
            if pat_idx == 3:
                # Arrow pattern
                src = g[0].strip().rstrip(".,")
                dst = g[1].strip().rstrip(".,")
                for pair in [(src, dst)]:
                    description = f"{pair[0]} → {pair[1]}"
                    if description not in seen and len(description) > 10:
                        candidates.append(
                            {"step": len(candidates) + 1, "description": description[:120]}
                        )
                        seen.add(description)
            elif pat_idx in (4, 5, 6):
                # First/then/finally patterns
                for part in g:
                    if part:
                        desc = part.strip().rstrip(".,")
                        if desc not in seen and len(desc) > 10:
                            candidates.append(
                                {"step": len(candidates) + 1, "description": desc[:120]}
                            )
                            seen.add(desc)
            else:
                # Numbered step (indices 0, 1, 2)
                step_num = int(g[0])
                desc = g[1].strip().rstrip(".,")
                if desc not in seen and len(desc) > 10:
                    candidates.append({"step": step_num, "description": desc[:120]})
                    seen.add(desc)

    candidates.sort(key=lambda x: x["step"])
    deduped: list[dict] = []
    seen_descs = set()
    for c in candidates:
        if c["description"] not in seen_descs:
            seen_descs.add(c["description"])
            c["step"] = len(deduped) + 1
            deduped.append(c)

    return deduped[:10]


# ── Comparison extraction ──────────────────────────────────────

_COMPARE_PATTERNS = [
    re.compile(
        r"(\w[\w\s&()+'-]+?)\s+(?:vs\.?|versus|compared to|"
        r"compared with|over|outperform(?:s|ed)?)\s+"
        r"(\w[\w\s&()+'-]+?)(?=[,;:\u2014\u2013)\]\[-]|(?:\s+and\s+)|\s*$)",
        re.IGNORECASE,
    ),
    re.compile(
        r"(\w[\w\s]+?)\s+(?:grew|rose|increased|climbed|surged|"
        r"jumped|declined|fell|dropped|plunged)\s+(?:by\s+)?"
        r"(\d+(?:\.\d+)?)\s*%",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:by\s+)?(\d+(?:\.\d+)?)\s*%\s*(?:to\s+|,?\s*(?:up|down)\s+"
        r"from\s+)(\d+(?:\.\d+)?)\s*%\s*(?:for\s+)?(\w[\w\s&'-]{1,60})",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:reached|hit|achieved)\s+(\d+(?:\.\d+)?)\s*%\s*"
        r"(?:\w+\s+){0,3}(?:for|in|of)\s+(\w[\w\s&'-]{1,60})",
        re.IGNORECASE,
    ),
]


def extract_comparisons(body_text: str) -> list[dict[str, Any]]:
    """Extract numeric comparisons and entity pairs from article body.

    Returns list of {entity_a, entity_b, metric, value_a, value_b} dicts.
    """
    text = re.sub(r"<[^>]+>", " ", body_text)
    text = re.sub(r"\s+", " ", text).strip()

    results: list[dict] = []
    seen = set()

    for pat in _COMPARE_PATTERNS:
        for m in pat.finditer(text):
            g = m.groups()
            if pat == _COMPARE_PATTERNS[0]:
                # Entity A vs Entity B
                a = g[0].strip()[:60]
                b = g[1].strip()[:60]
                key = f"compare|{a}|{b}"
                if key not in seen:
                    seen.add(key)
                    results.append(
                        {
                            "entity_a": a,
                            "entity_b": b,
                            "metric": "comparison",
                            "value_a": "",
                            "value_b": "",
                        }
                    )
            elif pat == _COMPARE_PATTERNS[1]:
                entity = g[2].strip() if len(g) > 2 else "value"
                val = g[1]
                key = f"percent|{entity}|{val}"
                if key not in seen:
                    seen.add(key)
                    results.append(
                        {
                            "entity_a": entity[:60],
                            "entity_b": "",
                            "metric": "change",
                            "value_a": f"{val}%",
                            "value_b": "",
                        }
                    )
            elif pat == _COMPARE_PATTERNS[2]:
                entity = g[2].strip()[:60] if g[2] else ""
                key = f"range|{entity}|{g[0]}|{g[1]}"
                if key not in seen:
                    seen.add(key)
                    results.append(
                        {
                            "entity_a": entity,
                            "entity_b": "",
                            "metric": "percentage_range",
                            "value_a": f"{g[0]}%",
                            "value_b": f"{g[1]}%",
                        }
                    )
            elif pat == _COMPARE_PATTERNS[3]:
                entity = g[1].strip()[:60] if g[1] else ""
                key = f"reached|{entity}|{g[0]}"
                if key not in seen:
                    seen.add(key)
                    results.append(
                        {
                            "entity_a": entity,
                            "entity_b": "",
                            "metric": "milestone",
                            "value_a": f"{g[0]}%",
                            "value_b": "",
                        }
                    )

    return results[:8]


# ── Analysis HTML extractors ───────────────────────────────────

_ANALYSIS_ENTITIES_RE = re.compile(
    r"\*\*Key entities:\*\*\s*(.*?)(?:\*\*Key numbers|\*\*SQI|\*\*From articles|$)", re.DOTALL
)
_ANALYSIS_NUMBERS_RE = re.compile(
    r"\*\*Key numbers:\*\*\s*(.*?)(?:\*\*SQI|\*\*From articles|\*\*Key entities|$)", re.DOTALL
)
_ANALYSIS_SQI_RE = re.compile(r"\*\*SQI:\*\*\s*([\d.]+)")
_ANALYSIS_FROM_RE = re.compile(r"\*\*From articles:\*\*\s*(.*?)$", re.DOTALL)
_TRENDING_DATE_RE = re.compile(r"Top Story\s*\([^,]+,\s*(\d{4}-\d{2}-\d{2})\)")
_TRENDING_TITLE_RE = re.compile(r"\d+\.\s*\[([^\]]+)\]")


def extract_entities_from_analysis(analysis_html: str) -> list[str]:
    """Parse 'Key entities' from analysis_html.

    Returns list of entity names (backtick-delimited in source).
    """
    if not analysis_html:
        return []
    m = _ANALYSIS_ENTITIES_RE.search(analysis_html)
    if not m:
        return []
    segment = m.group(1)
    entities = re.findall(r"`([^`]+)`", segment)
    # Filter noise words
    stop = {"a", "an", "the", "of", "in", "to", "for", "and", "or", "at", "by", "on", "as", "with"}
    return [e for e in entities if e.lower() not in stop and len(e) >= 2][:8]


def extract_numbers_from_analysis(analysis_html: str) -> list[dict]:
    """Parse 'Key numbers' from analysis_html.

    Returns list of {value, label} dicts. Labels are inferred from
    surrounding context when possible.
    """
    if not analysis_html:
        return []
    m = _ANALYSIS_NUMBERS_RE.search(analysis_html)
    if not m:
        return []
    segment = m.group(1).strip()
    parts = re.split(r"\s*[·•]\s*", segment)
    results = []
    for p in parts:
        p = p.strip().rstrip("., ")
        if not p:
            continue
        # Try to extract a clean number
        num_m = re.match(r"([\d,.]+[kKmMbB]?)", p)
        if num_m:
            results.append({"value": num_m.group(1), "label": ""})
        else:
            results.append({"value": p, "label": ""})
    return results[:6]


def extract_sqi_from_analysis(analysis_html: str) -> float | None:
    """Parse SQI value from analysis_html."""
    if not analysis_html:
        return None
    m = _ANALYSIS_SQI_RE.search(analysis_html)
    if m:
        try:
            return float(m.group(1))
        except ValueError:
            return None
    return None


_ESCAPE_TD = re.compile(r"\\(.)")


def extract_timeline_from_trending(trending_html: str) -> list[dict]:
    """Extract dated events from trending_html.

    Returns list of {date, event} dicts.
    """
    if not trending_html:
        return []
    results: list[dict] = []

    # Date from header
    m = _TRENDING_DATE_RE.search(trending_html)
    date_str = m.group(1) if m else ""

    # Extract story titles
    for m in _TRENDING_TITLE_RE.finditer(trending_html):
        title = m.group(1)
        title = _ESCAPE_TD.sub(r"\1", title)
        if date_str and len(title) > 10:
            results.append({"date": date_str, "event": title[:120]})

    return results[:5]
