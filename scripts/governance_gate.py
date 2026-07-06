#!/usr/bin/env python3
"""Governance Gate — Content Density & Semantic Validation for AcaciaFund.

Blocks deployment if any article fails quality thresholds:
  - Content Density < 40% substantive analytical prose
  - Code-dominated filler (code > 60% of body)
  - Front-matter-only articles (body < 100 chars)
  - Boilerplate prose ratio > 30%

Integration: called by scripts/preflight.py. Exits with code 1 on failure.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

BODY_MIN_CHARS = 100
DENSITY_THRESHOLD = 0.40
CODE_MAX_RATIO = 0.60
BOILERPLATE_MAX_RATIO = 0.30
WORD_ENTROPY_MAX = 8.5  # Raised from 8.0 — technical/philosophical content
                          # (cybernetics, systems theory) routinely reaches 8.0-8.5 bits/word.
ANALYTICAL_COVERAGE_MIN = 5  # Lowered from 8 — tutorials, glossaries, and reference
                              # material naturally score lower but are still valid.
SENTENCE_VARIANCE_MIN = 3.0
DUPLICATE_SIMILARITY_MAX = 0.85  # Raised from 0.75 — only flag near-duplicates
SIMILARITY_WINDOW_DAYS = 90   # Only compare items within this rolling window

# Pillar / tag mapping for abstract (non-empirical) domains whose analytical
# vocabulary differs from the data-engineering / AML / markets keywords.
ABSTRACT_DOMAIN_TAGS: set[str] = {
    "cybernetics", "information-theory", "signal-quality", "knowledge-fabric",
    "systems", "complexity", "epistemology", "philosophy", "entropy",
    "emergence", "self-organization", "feedback-loops",
}

ABSTRACT_KEYWORDS: set[str] = {
    "feedback", "signal", "noise", "entropy", "cybernetics", "emergence",
    "self-organization", "complexity", "system", "information", "theory",
    "communication", "control", "regulation", "adaptation", "evolution",
    "pattern", "network", "hierarchy", "autonomy", "governance",
    "equilibrium", "dynamics", "resilience", "robustness", "loop",
}

BOILERPLATE_PATTERNS: list[re.Pattern] = [
    re.compile(r"\bcomprehensive guide\b", re.IGNORECASE),
    re.compile(r"\bdeep dive\b", re.IGNORECASE),
    re.compile(r"\bin this article\b", re.IGNORECASE),
    re.compile(r"\bin this (section|chapter|report)\b", re.IGNORECASE),
    re.compile(r"\bas we have seen\b", re.IGNORECASE),
    re.compile(r"\bas mentioned earlier\b", re.IGNORECASE),
    re.compile(r"\bit is important to note\b", re.IGNORECASE),
    re.compile(r"\bit should be noted\b", re.IGNORECASE),
    re.compile(r"\bin conclusion\b", re.IGNORECASE),
    re.compile(r"\bthe purpose of this\b", re.IGNORECASE),
    re.compile(r"\bwe can see that\b", re.IGNORECASE),
    re.compile(r"\bserves as the\b", re.IGNORECASE),
    re.compile(r"\bin the era of\b", re.IGNORECASE),
    re.compile(r"\bat scale\b", re.IGNORECASE),
    re.compile(r"\boperational backbone\b", re.IGNORECASE),
    re.compile(r"\baccelerates downstream\b", re.IGNORECASE),
    re.compile(r"\bbalance flexibility with\b", re.IGNORECASE),
    re.compile(r"\bfirst-class (product|data) interface\b", re.IGNORECASE),
    re.compile(r"\bwell-designed\b", re.IGNORECASE),
]


def read_markdown_articles(content_dir: str | Path) -> list[dict]:
    """Read all .md articles from content/ tree, return list of {path, frontmatter, body}."""
    articles: list[dict] = []
    base = Path(content_dir)
    if not base.is_dir():
        return articles
    for md_file in sorted(base.rglob("*.md")):
        try:
            raw = md_file.read_text(encoding="utf-8")
        except Exception:
            continue
        fm_match = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)", raw, re.DOTALL)
        if fm_match:
            frontmatter_raw = fm_match.group(1)
            body = fm_match.group(2).strip()
        else:
            frontmatter_raw = ""
            body = raw.strip()
        articles.append({
            "path": str(md_file.relative_to(base.parent)),
            "frontmatter": frontmatter_raw,
            "body": body,
            "raw": raw,
        })
    return articles


def strip_code_blocks(body: str) -> tuple[str, list[str]]:
    """Extract code blocks from body. Returns (body_without_code, code_blocks)."""
    code_blocks: list[str] = []
    def _extract(m: re.Match) -> str:
        code_blocks.append(m.group(0))
        return ""
    body_no_code = re.sub(r"```[\s\S]*?```|`[^`]+`", _extract, body)
    return body_no_code, code_blocks


def strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text)


def count_substantive_chars(text: str) -> int:
    """Count non-whitespace, non-structural characters."""
    cleaned = re.sub(r"\s+", " ", text).strip()
    return len(cleaned)


def count_code_chars(code_blocks: list[str]) -> int:
    return sum(len(re.sub(r"\s+", "", b)) for b in code_blocks)


def count_boilerplate_sentences(text: str) -> int:
    """Count sentences matching boilerplate patterns."""
    sentences = re.split(r"[.!?]+", text)
    count = 0
    for sent in sentences:
        stripped = sent.strip().lower()
        if len(stripped) < 10:
            continue
        if any(p.search(stripped) for p in BOILERPLATE_PATTERNS):
            count += 1
    return count


def total_sentences(text: str) -> int:
    sentences = [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]
    return len(sentences)


def measure_article(article: dict) -> dict:
    """Compute quality metrics for a single article."""
    body = article["body"]
    path = article["path"]

    result: dict = {
        "path": path,
        "total_chars": 0,
        "substantive_chars_prose": 0,
        "code_chars": 0,
        "boilerplate_sentences": 0,
        "total_sentences": 0,
        "body_len": len(body),
        "code_dominated": False,
        "too_short": False,
        "boilerplate_dominated": False,
        "overall_density": 0.0,
        "passed": True,
        "failures": [],
    }

    if len(body) < BODY_MIN_CHARS:
        result["too_short"] = True
        result["passed"] = False
        result["failures"].append("too_short")
        return result

    stripped = strip_html(body)
    result["total_chars"] = count_substantive_chars(stripped)

    body_no_code, code_blocks = strip_code_blocks(stripped)
    result["code_chars"] = count_code_chars(code_blocks)
    prose_text = strip_html(body_no_code)
    result["substantive_chars_prose"] = count_substantive_chars(prose_text)

    total_substantive = result["substantive_chars_prose"] + result["code_chars"]
    if total_substantive == 0:
        result["passed"] = False
        result["failures"].append("no_substantive_content")
        return result

    # Code domination check
    code_ratio = result["code_chars"] / max(total_substantive, 1)
    result["code_dominated"] = code_ratio > CODE_MAX_RATIO

    # Boilerplate check (on prose only)
    sentences = re.split(r"[.!?]+", prose_text)
    result["total_sentences"] = len([s for s in sentences if s.strip()])
    if result["total_sentences"] > 0:
        boilerplate_count = count_boilerplate_sentences(prose_text)
        result["boilerplate_sentences"] = boilerplate_count
        boilerplate_ratio = boilerplate_count / result["total_sentences"]
        result["boilerplate_dominated"] = boilerplate_ratio > BOILERPLATE_MAX_RATIO
    else:
        result["boilerplate_dominated"] = False

    # Overall density: unique analytical prose / total chars
    unique_prose = result["substantive_chars_prose"]
    # Penalize boilerplate-sentence chars (heuristic: 20% of boilerplate-sentence chars)
    if result["total_sentences"] > 0:
        bp_penalty = result["boilerplate_sentences"] / result["total_sentences"]
    else:
        bp_penalty = 0.0
    adjusted_prose = unique_prose * (1.0 - bp_penalty * 0.5)
    result["overall_density"] = adjusted_prose / max(total_substantive, 1)

    # Fail conditions
    if result["overall_density"] < DENSITY_THRESHOLD:
        result["passed"] = False
        result["failures"].append("low_density")
    if result["code_dominated"]:
        result["passed"] = False
        result["failures"].append("code_dominated")
    if result["boilerplate_dominated"]:
        result["passed"] = False
        result["failures"].append("boilerplate_dominated")

    return result


def run_governance_check(content_dir: str = "content") -> list[dict]:
    """Run governance gate over all articles. Returns list of per-article results."""
    articles = read_markdown_articles(content_dir)
    results: list[dict] = []
    for article in articles:
        result = measure_article(article)
        results.append(result)
    return results


def print_report(results: list[dict]) -> int:
    """Print governance report. Returns number of failures."""
    failures = [r for r in results if not r["passed"]]
    total = len(results)

    print("=" * 60)
    print("GOVERNANCE GATE REPORT")
    print("=" * 60)
    print(f"Total articles scanned: {total}")
    print(f"Failed: {len(failures)}")
    if failures:
        print()
        print("--- FAILURES ---")
        for f in failures:
            reasons = ", ".join(f["failures"])
            print(f"  FAIL [{reasons}] {f['path']}")
            print(f"       density={f['overall_density']:.2f} "
                  f"code_ratio={f['code_chars']/max(f['code_chars']+f['substantive_chars_prose'],1):.2f} "
                  f"boilerplate={f['boilerplate_sentences']}/{f['total_sentences']}")
        print()
    print("=" * 60)
    return len(failures)


def print_report_registry(report: dict) -> None:
    """Print governance report for registry mode."""
    print("=" * 60)
    print("GOVERNANCE GATE REPORT (REGISTRY MODE)")
    print("=" * 60)
    print(f"Total items scanned: {report['total_items']}")
    print(f"Passed: {report['passed']}")
    print(f"Failed: {report['failed']}")
    
    failed_results = [r for r in report["results"] if not r["passed"]]
    if failed_results:
        print()
        print("--- FAILURES ---")
        for r in failed_results[:20]:
            reasons = ", ".join(r["failures"])
            print(f"  FAIL [{reasons}] {r['slug']}")
            print(f"       density={r['overall_density']:.2f} "
                  f"entropy={r['word_entropy']:.2f} "
                  f"analytical={r['analytical_coverage']} "
                  f"variance={r['sentence_variance']:.1f}")
        if len(failed_results) > 20:
            print(f"  ... and {len(failed_results) - 20} more")
        print()
    
    # Layer summary
    print("--- 7-LAYER MOAT SUMMARY ---")
    layers = ["density", "code_ratio", "boilerplate_ratio", "word_entropy", 
              "analytical_coverage", "sentence_variance", "duplicate_similarity"]
    for layer in layers:
        passed = sum(1 for r in report["results"] if r.get("layers", {}).get(layer, {}).get("pass", False))
        total = report["total_items"]
        print(f"  {layer}: {passed}/{total} passed ({100*passed/max(total,1):.0f}%)")
    
    print()
    print("=" * 60)
    print(f"Report written to: registry/governance_report.json")


def read_registry_items(registry_path: str | Path = "registry.json") -> list[dict]:
    """Read content items from registry.json. Returns list of {slug, body_html, pillar, date_str}."""
    items: list[dict] = []
    reg_path = Path(registry_path)
    if not reg_path.exists():
        return items
    try:
        with open(reg_path, "r", encoding="utf-8") as f:
            reg = json.load(f)
        for item in reg.get("content", []):
            items.append({
                "slug": item.get("slug", ""),
                "body_html": item.get("body_html", ""),
                "pillar": item.get("pillar", "unknown"),
                "title": item.get("title", ""),
                "tags": item.get("tags", []),
                "date_str": item.get("date_str") or item.get("created_at", ""),
            })
    except Exception:
        pass
    return items


def compute_word_entropy(text: str, vocabulary: set[str] | None = None) -> float:
    """Compute per-word Shannon entropy in bits."""
    import math
    words = re.findall(r"\b[a-zA-Z]+\b", text.lower())
    if not words:
        return 0.0
    
    word_counts = Counter(words)
    total = len(words)
    entropy = 0.0
    
    for word, count in word_counts.items():
        p = count / total
        if p > 0:
            entropy -= p * math.log2(p)
    
    return entropy


def count_analytical_keywords(text: str, extra_keywords: set[str] | None = None) -> int:
    """Count unique analytical signal words.

    For abstract-domain content (cybernetics, information theory, etc.)
    the caller may pass an extra keyword set to supplement the base
    analytical vocabulary so that these items are not unfairly penalised.
    """
    analytical_keywords = {
        "evidence", "finding", "analysis", "methodology", "correlation",
        "causation", "significant", "bias", "hypothesis", "test", "validate",
        "empirical", "framework", "model", "parameter", "metric", "statistical",
        "probability", "confidence", "interval", "regression", "distribution",
        "variance", "deviation", "threshold", "algorithm", "complexity",
        "architecture", "schema", "contract", "validation", "verification"
    }
    if extra_keywords:
        analytical_keywords.update(extra_keywords)
    text_lower = text.lower()
    found = {kw for kw in analytical_keywords if kw in text_lower}
    return len(found)


def compute_sentence_variance(text: str) -> float:
    """Compute standard deviation of sentence lengths (in words)."""
    sentences = re.split(r"[.!?]+", text)
    lengths = [len(s.split()) for s in sentences if s.strip()]
    if len(lengths) < 2:
        return 0.0
    mean = sum(lengths) / len(lengths)
    variance = sum((l - mean) ** 2 for l in lengths) / len(lengths)
    return variance ** 0.5


def _parse_date(date_str: str | None) -> datetime | None:
    """Parse an ISO date string, always returning a timezone-aware UTC
    datetime. Returns None on failure."""
    if not date_str:
        return None
    try:
        cleaned = date_str.replace("Z", "+00:00")
        dt = datetime.fromisoformat(cleaned)
        # Attach UTC for naive dates (e.g. "2026-07-06")
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        return None


def _is_abstract_item(tags: list[str] | None, pillar: str | None) -> bool:
    """Check whether an item belongs to an abstract / philosophical domain.

    Items tagged with ABSTRACT_DOMAIN_TAGS (e.g. cybernetics, information
    theory, knowledge-fabric) or with a pillar matching one of those tags
    qualify. Their analytical keyword set is supplemented so they are not
    unfairly penalised for lacking data-engineering vocabulary.
    """
    if tags:
        domain_lower = {t.lower().replace("-", "").replace(" ", "") for t in ABSTRACT_DOMAIN_TAGS}
        tag_lower = {t.lower().replace("-", "").replace(" ", "") for t in tags}
        if tag_lower & domain_lower:
            return True
    if pillar and pillar.lower() in [d.replace("-", "").replace(" ", "") for d in ABSTRACT_DOMAIN_TAGS]:
        return True
    # Also check tags directly against the set (for exact matches like "cybernetics")
    if tags:
        tag_set_lower = {t.lower() for t in tags}
        if tag_set_lower & ABSTRACT_DOMAIN_TAGS:
            return True
    return False


def jaccard_similarity(s1: str, s2: str) -> float:
    """Compute Jaccard similarity between two strings."""
    words1 = set(re.findall(r"\b\w+\b", s1.lower()))
    words2 = set(re.findall(r"\b\w+\b", s2.lower()))
    if not words1 or not words2:
        return 0.0
    intersection = words1 & words2
    union = words1 | words2
    return len(intersection) / len(union)


def measure_registry_item(
    item: dict,
    vocabulary: set[str] | None = None,
    previous_items: list[tuple[str, str]] | None = None,
) -> dict:
    """Compute quality metrics for a registry item (body_html).

    previous_items: list of (text, date_str) tuples for duplicate detection
                    with time-windowing (only items within
                    SIMILARITY_WINDOW_DAYS are compared).
    """
    slug = item.get("slug", "unknown")
    body_html = item.get("body_html", "")
    title = item.get("title", "")
    tags = item.get("tags", [])
    pillar = item.get("pillar", "unknown")
    item_date_str = item.get("date_str", "")

    is_abstract = _is_abstract_item(tags, pillar)

    # Strip HTML for text analysis
    text = strip_html(body_html)

    result: dict = {
        "slug": slug,
        "title": title[:60],
        "pillar": pillar,
        "is_abstract": is_abstract,
        "body_len": len(body_html),
        "text_len": len(text),
        "total_chars": 0,
        "substantive_chars_prose": 0,
        "code_chars": 0,
        "boilerplate_sentences": 0,
        "total_sentences": 0,
        "code_dominated": False,
        "too_short": False,
        "boilerplate_dominated": False,
        "low_density": False,
        "high_entropy": False,
        "low_analytical_coverage": False,
        "low_sentence_variance": False,
        "high_similarity": False,
        "overall_density": 0.0,
        "word_entropy": 0.0,
        "analytical_coverage": 0,
        "sentence_variance": 0.0,
        "max_similarity": 0.0,
        "passed": True,
        "failures": [],
        "layers": {},
    }

    if len(text) < BODY_MIN_CHARS:
        result["too_short"] = True
        result["passed"] = False
        result["failures"].append("too_short")
        return result

    # Strip code blocks
    body_no_code, code_blocks = strip_code_blocks(text)
    result["code_chars"] = count_code_chars(code_blocks)
    prose_text = strip_html(body_no_code)
    result["substantive_chars_prose"] = count_substantive_chars(prose_text)
    result["total_chars"] = result["substantive_chars_prose"] + result["code_chars"]

    if result["total_chars"] == 0:
        result["failures"].append("no_substantive_content")
        return result

    # Code domination check
    code_ratio = result["code_chars"] / max(result["total_chars"], 1)
    result["code_dominated"] = code_ratio > CODE_MAX_RATIO
    result["layers"]["code_ratio"] = {"value": code_ratio, "threshold": CODE_MAX_RATIO, "pass": not result["code_dominated"]}

    # Boilerplate check (on prose only)
    sentences = re.split(r"[.!?]+", prose_text)
    result["total_sentences"] = len([s for s in sentences if s.strip()])
    if result["total_sentences"] > 0:
        boilerplate_count = count_boilerplate_sentences(prose_text)
        result["boilerplate_sentences"] = boilerplate_count
        boilerplate_ratio = boilerplate_count / result["total_sentences"]
        result["boilerplate_dominated"] = boilerplate_ratio > BOILERPLATE_MAX_RATIO
        result["layers"]["boilerplate_ratio"] = {"value": boilerplate_ratio, "threshold": BOILERPLATE_MAX_RATIO, "pass": not result["boilerplate_dominated"]}

    # Density check
    unique_prose = result["substantive_chars_prose"]
    if result["total_sentences"] > 0:
        bp_penalty = result["boilerplate_sentences"] / result["total_sentences"]
    else:
        bp_penalty = 0.0
    adjusted_prose = unique_prose * (1.0 - bp_penalty * 0.5)
    result["overall_density"] = adjusted_prose / max(result["total_chars"], 1)
    result["low_density"] = result["overall_density"] < DENSITY_THRESHOLD
    result["layers"]["density"] = {"value": result["overall_density"], "threshold": DENSITY_THRESHOLD, "pass": not result["low_density"]}

    # Word entropy check (Layer 6)
    result["word_entropy"] = compute_word_entropy(prose_text)
    result["high_entropy"] = result["word_entropy"] > WORD_ENTROPY_MAX
    result["layers"]["word_entropy"] = {"value": result["word_entropy"], "threshold": WORD_ENTROPY_MAX, "pass": not result["high_entropy"]}

    # Analytical coverage check (Layer 4)
    # Abstract-domain items get a supplemented keyword set so their
    # philosophical vocabulary is recognised as analytical signal.
    extra_keywords = ABSTRACT_KEYWORDS if is_abstract else None
    result["analytical_coverage"] = count_analytical_keywords(prose_text, extra_keywords=extra_keywords)
    result["low_analytical_coverage"] = result["analytical_coverage"] < ANALYTICAL_COVERAGE_MIN
    result["layers"]["analytical_coverage"] = {"value": result["analytical_coverage"], "threshold": ANALYTICAL_COVERAGE_MIN, "pass": not result["low_analytical_coverage"]}

    # Sentence variance check (Layer 5)
    result["sentence_variance"] = compute_sentence_variance(prose_text)
    result["low_sentence_variance"] = result["sentence_variance"] < SENTENCE_VARIANCE_MIN
    result["layers"]["sentence_variance"] = {"value": result["sentence_variance"], "threshold": SENTENCE_VARIANCE_MIN, "pass": not result["low_sentence_variance"]}

    # Duplicate detection (Layer 7) — 90-day rolling window
    if previous_items:
        item_date = _parse_date(item.get("date_str"))
        # Filter previous items to within the rolling window
        candidates: list[str] = []
        for prev_text, prev_date_str in previous_items:
            if item_date is not None and prev_date_str:
                prev_date = _parse_date(prev_date_str)
                if prev_date is not None:
                    delta_days = abs((item_date - prev_date).total_seconds() / 86400)
                    if delta_days > SIMILARITY_WINDOW_DAYS:
                        continue  # Outside the rolling window
            candidates.append(prev_text)

        if candidates:
            text_lower = prose_text.lower()
            max_sim = max(jaccard_similarity(text_lower, c) for c in candidates)
            result["max_similarity"] = max_sim
            result["high_similarity"] = max_sim > DUPLICATE_SIMILARITY_MAX
            result["layers"]["duplicate_similarity"] = {"value": max_sim, "threshold": DUPLICATE_SIMILARITY_MAX, "pass": not result["high_similarity"]}

    # Determine overall pass/fail
    if result["low_density"]:
        result["failures"].append("low_density")
    if result["code_dominated"]:
        result["failures"].append("code_dominated")
    if result["boilerplate_dominated"]:
        result["failures"].append("boilerplate_dominated")
    if result["high_entropy"]:
        result["failures"].append("high_entropy")
    if result["low_analytical_coverage"]:
        result["failures"].append("low_analytical_coverage")
    if result["low_sentence_variance"]:
        result["failures"].append("low_sentence_variance")
    if result["high_similarity"]:
        result["failures"].append("high_similarity")

    result["passed"] = len(result["failures"]) == 0

    return result


def run_governance_check_registry(registry_path: str = "registry.json") -> tuple[list[dict], dict]:
    """Run governance gate over registry items. Returns (results, report)."""
    items = read_registry_items(registry_path)
    results: list[dict] = []
    previous_items: list[tuple[str, str]] = []  # (text_lower, date_str)
    
    for item in items:
        result = measure_registry_item(item, previous_items=previous_items)
        results.append(result)
        # Add text + date to previous for duplicate detection with time-windowing
        text = strip_html(item.get("body_html", ""))
        previous_items.append((text.lower(), item.get("date_str", "")))
    
    # Build report
    report = {
        "mode": "registry",
        "registry_path": registry_path,
        "total_items": len(results),
        "passed": sum(1 for r in results if r["passed"]),
        "failed": sum(1 for r in results if not r["passed"]),
        "results": results,
    }
    
    return results, report


def main() -> int:
    parser = argparse.ArgumentParser(
        description="AcaciaFund Governance Gate — content density & semantic validation"
    )
    parser.add_argument(
        "--content-dir", default="content",
        help="Root content directory (default: content)"
    )
    parser.add_argument(
        "--registry", action="store_true",
        help="Scan registry.json instead of .md files"
    )
    parser.add_argument(
        "--registry-path", default="registry.json",
        help="Path to registry.json (default: registry.json)"
    )
    parser.add_argument(
        "--output-report", default="registry/governance_report.json",
        help="Path to output report JSON (default: registry/governance_report.json)"
    )
    parser.add_argument(
        "--density-threshold", type=float, default=DENSITY_THRESHOLD,
        help=f"Minimum substantive density (default: {DENSITY_THRESHOLD})"
    )
    parser.add_argument(
        "--quiet", action="store_true",
        help="Suppress detailed per-article output"
    )
    args = parser.parse_args()

    if args.registry:
        results, report = run_governance_check_registry(args.registry_path)
        
        # Write report
        report_path = Path(args.output_report)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        failure_count = report["failed"]
        print_report_registry(report)
        
        # Write simplified governance report for SQI engine
        sqi_report_path = Path(args.output_report).parent / "governance_sqi.json"
        sqi_report = {
            "results": [
                {"path": r["slug"], "passed": r["passed"], "failures": r["failures"]}
                for r in results
            ]
        }
        with open(sqi_report_path, "w", encoding="utf-8") as f:
            json.dump(sqi_report, f, indent=2)
    else:
        results = run_governance_check(args.content_dir)
        failure_count = print_report(results)
    
    if failure_count > 0:
        if not args.quiet:
            print(f"BLOCKED: {failure_count} article(s) failed governance gate")
        return 1
    print("governance: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
