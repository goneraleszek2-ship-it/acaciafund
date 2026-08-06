"""Markdown helpers for controlled markdown subsets.

`md_to_html` converts the small markdown dialect used by the glossary
generator (headings, bold/italic, bullet lists, links) into HTML.

`fix_markdown_residue` repairs raw markdown artifacts that leak into
otherwise-HTML body content, skipping `<pre>`/`<code>` regions so glob
patterns and code samples are never touched.
"""

from __future__ import annotations

import re

_HEADING_RE = re.compile(r"^(#{2,3})\s+(.*)$")
_BULLET_RE = re.compile(r"^\s*[-*]\s+(.*)$")
_LINK_RE = re.compile(r"\[([^\]]+)\]\((https?://[^)\s]+)\)")
_BOLD_RE = re.compile(r"\*\*([^*<>\n]{1,300})\*\*")
_ITALIC_RE = re.compile(r"(?<!\*)\*([^*<>\n]{1,300})\*(?!\*)")

_CODE_REGION_RE = re.compile(r"<(?:pre|code)\b[^>]*>.*?</(?:pre|code)>", re.S)


def _escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _inline(text: str) -> str:
    """Apply inline markdown (bold, italic, links) to a text fragment."""
    text = _escape(text)
    text = _LINK_RE.sub(r'<a href="\2">\1</a>', text)
    text = _BOLD_RE.sub(r"<strong>\1</strong>", text)
    text = _ITALIC_RE.sub(r"<em>\1</em>", text)
    return text


def md_to_html(md: str) -> str:
    """Convert the controlled markdown dialect to HTML.

    Supports `##`/`###` headings, `-` bullet lists, blank-line separated
    paragraphs, and inline bold/italic/links. Other markdown constructs are
    treated as plain text.
    """
    if not md:
        return ""
    lines = md.splitlines()
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        head = _HEADING_RE.match(line)
        if head:
            level = len(head.group(1))
            out.append(f"<h{level}>{_inline(head.group(2).strip())}</h{level}>")
            i += 1
            continue
        if _BULLET_RE.match(line):
            items = []
            while i < len(lines) and _BULLET_RE.match(lines[i]):
                items.append(f"<li>{_inline(_BULLET_RE.match(lines[i]).group(1).strip())}</li>")
                i += 1
            out.append(f"<ul>{''.join(items)}</ul>")
            continue
        if not line:
            i += 1
            continue
        para = [_inline(line)]
        i += 1
        while i < len(lines) and lines[i].strip() and not _HEADING_RE.match(lines[i]) and not _BULLET_RE.match(lines[i]):
            para.append(_inline(lines[i].strip()))
            i += 1
        out.append(f"<p>{' '.join(p for p in para if p)}</p>")
    return "\n".join(out)


def _replace_outside_code(html: str, pattern: re.Pattern, replacement) -> str:
    """Apply `re.sub` only to regions outside <pre>/<code> blocks."""
    masked: list[str] = []
    regions: list[str] = []
    offset = 0
    for m in _CODE_REGION_RE.finditer(html):
        masked.append(html[offset : m.start()])
        regions.append(m.group(0))
        masked.append(f"\x00code{len(regions) - 1}\x00")
        offset = m.end()
    masked.append(html[offset:])
    result = pattern.sub(replacement, "".join(masked))
    for idx, region in enumerate(regions):
        result = result.replace(f"\x00code{idx}\x00", region)
    return result


def fix_markdown_residue(html: str) -> str:
    """Convert markdown artifacts embedded in HTML text nodes.

    Handles `## Heading` paragraphs (h2), `### Heading` (h3), `**bold**`,
    and `*italic*` — while leaving `<pre>`/`<code>` content untouched.
    """
    if not html:
        return ""
    result = html
    result = _replace_outside_code(
        result,
        re.compile(r"<p>#\s+([^<]{1,120})</p>"),
        lambda m: f"<h1>{_inline(m.group(1))}</h1>",
    )
    result = _replace_outside_code(
        result,
        re.compile(r"<p>###\s+([^<]{1,120})</p>"),
        lambda m: f"<h3>{_inline(m.group(1))}</h3>",
    )
    result = _replace_outside_code(
        result,
        re.compile(r"<p>##\s+([^<]{1,120})</p>"),
        lambda m: f"<h2>{_inline(m.group(1))}</h2>",
    )
    result = _replace_outside_code(result, _BOLD_RE, r"<strong>\1</strong>")
    result = _replace_outside_code(result, _ITALIC_RE, r"<em>\1</em>")
    return result
