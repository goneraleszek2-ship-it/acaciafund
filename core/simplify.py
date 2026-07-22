from __future__ import annotations

import re
from typing import Any


def generate_tldr(body_html: str, max_sentences: int = 3) -> str:
    """Extract a plain-English TL;DR from HTML content."""
    text = re.sub(r'<[^>]+>', '', body_html)
    text = re.sub(r'\$.*?\$', '', text)
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    meaningful = [s for s in sentences if len(s.split()) > 3]
    if not meaningful:
        return text[:200].strip()
    return ' '.join(meaningful[:max_sentences]).strip()


def generate_section_summaries(body_html: str) -> list[dict[str, str]]:
    """Extract section headings and generate plain-English summaries."""
    sections = []
    pattern = re.compile(r'<h([23])[^>]*>(.*?)</h\1>', re.IGNORECASE)
    for match in pattern.finditer(body_html):
        heading = re.sub(r'<[^>]+>', '', match.group(2)).strip()
        if heading:
            sections.append({
                "heading": heading,
                "level": int(match.group(1)),
            })
    return sections


def strip_latex(text: str) -> str:
    """Replace LaTeX expressions with plain-English descriptions."""
    text = re.sub(r'\$\$.*?\$\$', '[mathematical expression]', text, flags=re.DOTALL)
    text = re.sub(r'\$(.*?)\$', lambda m: _describe_math(m.group(1)), text)
    return text


def _describe_math(expr: str) -> str:
    """Convert a LaTeX math expression to a plain description."""
    expr = expr.strip()
    if not expr:
        return "[expression]"
    if 'sim' in expr or 'approx' in expr:
        return "[approximately equal to]"
    if 'sum' in expr or 'Sigma' in expr:
        return "[sum of values]"
    if 'int' in expr:
        return "[integral over a range]"
    if 'partial' in expr or 'nabla' in expr:
        return "[rate of change]"
    if 'rightarrow' in expr or 'mapsto' in expr:
        return "[maps to]"
    if 'in' in expr or 'subset' in expr:
        return "[element of]"
    if 'times' in expr or 'cdot' in expr:
        return "[product]"
    if 'frac' in expr or 'over' in expr:
        return "[ratio]"
    if 'sqrt' in expr:
        return "[square root]"
    if 'alpha' in expr or 'beta' in expr or 'gamma' in expr:
        return "[parameter]"
    if 'geq' in expr or 'leq' in expr:
        return "[greater/less than or equal to]"
    return "[formula]"


def simplify_content(
    body_html: str,
    description: str = "",
) -> dict[str, Any]:
    """Generate simplified content for popular-science presentation.

    Returns a dict with:
    - tldr: short plain-English summary
    - sections: list of {heading, level} from the content
    - plain_body: body with LaTeX stripped
    """
    return {
        "tldr": generate_tldr(body_html),
        "sections": generate_section_summaries(body_html),
        "plain_body": strip_latex(body_html),
        "description_simple": description or generate_tldr(body_html, max_sentences=2),
    }
