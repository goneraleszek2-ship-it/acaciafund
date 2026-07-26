"""Generate alphabetical index (A-Z browser) inspired by MathWorld's letter index.

Scans all content items from registry.json and generates:
  /letters/index.html       → Letter grid with counts
  /letters/A/index.html     → All entries starting with 'A'
  /letters/B/index.html     → All entries starting with 'B'
  ...
"""

import logging
from collections import defaultdict
from pathlib import Path
from typing import Any, Callable

logger = logging.getLogger(__name__)


def _make_content(title="", description=""):
    """Create a simple content object for template rendering."""
    return type("obj", (object,), {
        "title": title,
        "description": description,
        "slug": "",
        "body_html": "",
        "tags": [],
        "pillar": "",
        "date_str": "",
        "language": "en",
        "category": "index",
        "created_at": None,
        "updated_at": None,
    })()


def _first_letter(title: str) -> str:
    """Extract the first letter for alphabetization, handling special chars."""
    clean = title.strip().lstrip("_")
    if not clean:
        return "?"
    # Handle "X-Ray" → X, "3D" → 3, etc.
    first = clean[0].upper()
    if first.isalpha():
        return first
    if first.isdigit():
        return "0-9"
    return "?"


def generate_alpha_index(
    output_dir: Path,
    all_content: list[Any],
    render_template: Callable,
    ctx_base: dict[str, Any],
    pillar_config: dict[str, Any] | None = None,
) -> int:
    """Generate A-Z alphabetical index pages. Returns count of generated pages."""

    pillar_config = pillar_config or {}
    letters_dir = output_dir / "letters"
    letters_dir.mkdir(parents=True, exist_ok=True)

    # Group content by first letter
    by_letter: dict[str, list[Any]] = defaultdict(list)
    for item in all_content:
        title = getattr(item, "title", "") or ""
        letter = _first_letter(title)
        by_letter[letter].append(item)

    # Sort entries within each letter
    for letter in by_letter:
        by_letter[letter].sort(key=lambda x: (getattr(x, "title", "") or "").lower())

    # Sort letters: digits first, then A-Z, then other
    def _letter_sort_key(lt: str) -> str:
        if lt == "0-9":
            return "0"
        if len(lt) == 1 and lt.isalpha():
            return lt
        return "~" + lt

    sorted_letters = sorted(by_letter.keys(), key=_letter_sort_key)

    # Track pages generated for stats
    letter_page_count = 0

    # Generate per-letter pages
    for letter in sorted_letters:
        items = by_letter[letter]
        letter_dir = letters_dir / ("digit" if letter == "0-9" else letter.lower())
        letter_dir.mkdir(parents=True, exist_ok=True)

        # Build entry list for template
        entries = []
        for item in items:
            pillar = getattr(item, "pillar", "")
            pc = pillar_config.get(pillar, {}) if pillar_config else {}
            entries.append({
                "slug": getattr(item, "slug", ""),
                "title": getattr(item, "title", ""),
                "description": getattr(item, "description", ""),
                "pillar": pillar,
                "pillar_label": pc.get("label", pillar.capitalize() if pillar else ""),
                "pillar_url": pc.get("url", pillar),
                "content_type": getattr(item, "content_type", ""),
                "date_str": getattr(item, "date_str", ""),
            })

        html = render_template(
            "alpha_index.j2",
            content=_make_content(f"Entries starting with '{letter}'",
                                  description=f"All knowledge entries beginning with the letter {letter}."),
            current_letter=letter,
            entries=entries,
            all_letters=sorted_letters,
            letter_counts={lt: len(by_letter[lt]) for lt in sorted_letters},
            page_title=f"Browse: {letter}",
            page_path=f"letters/{'digit' if letter == '0-9' else letter.lower()}/",
            **ctx_base,
        )
        (letter_dir / "index.html").write_text(html, encoding="utf-8")
        letter_page_count += 1

    # Generate master index page (letter grid)
    master_entries = []
    for letter in sorted_letters:
        items = by_letter[letter]
        sample = []
        for item in items[:5]:
            sample.append({
                "slug": getattr(item, "slug", ""),
                "title": getattr(item, "title", ""),
                "pillar": getattr(item, "pillar", ""),
            })
        master_entries.append({
            "letter": letter,
            "count": len(items),
            "sample": sample,
        })

    html = render_template(
        "alpha_index.j2",
            content=_make_content("Alphabetical Index",
                                  description="Browse the complete knowledge repository alphabetically."),
        current_letter=None,
        entries=[],
        all_letters=sorted_letters,
        letter_counts={lt: len(by_letter[lt]) for lt in sorted_letters},
        master_entries=master_entries,
        page_title="Alphabetical Index",
        page_path="letters/",
        **ctx_base,
    )
    (letters_dir / "index.html").write_text(html, encoding="utf-8")
    letter_page_count += 1

    print(f"  alpha-index: {letter_page_count} pages")
    return letter_page_count
