#!/usr/bin/env python3
"""
Read the broken‑link report, ask the optimal model (via StrategicTaskRouter)
to fix the source file, and write the patch.

The task is categorized as "regex_cleaning" because we are essentially
doing a search‑and‑replace on broken href values.
"""

import json
import os
import sys
from pathlib import Path

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from core.agent_router import StrategicTaskRouter

REPORT_PATH = Path("/root/acaciafund/data/broken_links.json")
CONTENT_ROOT = Path("/root/acaciafund/content")
TEMPLATE_ROOT = Path("/root/acaciafund/templates")


def load_report() -> dict:
    if not REPORT_PATH.exists():
        print("No broken-links report found. Run check_internal_links.py first.")
        sys.exit(1)
    return json.loads(REPORT_PATH.read_text())


def map_to_source(source_file: str) -> Path | None:
    """
    Given a relative path like 'blog/post-1.html' under dist/,
    return the likely source file under content/ or templates/.
    Heuristic:
      - If under 'blog/', 'learn/', 'knowledge/' → look in content/ for a .md with same stem.
      - Otherwise assume a Jinja2 template under templates/ with same name (or .j2).
    """
    source_file = source_file.lstrip("/")
    # Try content/
    if source_file.startswith(("blog/", "learn/", "knowledge/")):
        md_path = CONTENT_ROOT / source_file
        md_path = md_path.with_suffix(".md")
        if md_path.is_file():
            return md_path
    # Fallback: templates/
    tmpl_path = TEMPLATE_ROOT / source_file
    if tmpl_path.is_file():
        return tmpl_path
    # Try adding .j2 if not present
    if not tmpl_path.suffix:
        tmpl_path = tmpl_path.with_suffix(".j2")
        if tmpl_path.is_file():
            return tmpl_path
    return None


def build_prompt(broken_entry: dict) -> str:
    """
    Create a prompt asking the model to fix the broken link in the source file.
    We give the file content and ask it to return the *entire corrected* file.
    """
    src_path = map_to_source(broken_entry["source_file"])
    if not src_path or not src_path.is_file():
        return f"# ERROR: Could not locate source for {broken_entry['source_file']}"
    src_text = src_path.read_text(encoding="utf-8")
    prompt = f"""
You are an expert web‑developer. The following source file contains a broken internal link.
Return the *complete, corrected* file content with the link fixed.

Source file: {src_path}
Broken link (as it appears in the generated HTML): {broken_entry["broken_link"]}
Resolved expected path (what the link should point to): {broken_entry["resolved_path"]}

Instructions:
- Only change the href/src attribute that caused the 404.
- Preserve all other formatting, whitespace, and Jinja2/template syntax.
- If the link appears multiple times, fix all occurrences.
- Return ONLY the raw file content, no explanations or markdown fences.

--- BEGIN FILE ---
{src_text}
--- END FILE ---
""".strip()
    return prompt


def main():
    report = load_report()
    broken = report.get("broken_links", [])
    if not broken:
        print("✅ No broken links to repair.")
        return

    router = StrategicTaskRouter()
    fixed_any = False

    for entry in broken:
        src_path = map_to_source(entry["source_file"])
        if not src_path:
            print(f"⚠️  Skipping {entry['source_file']} – source not found")
            continue

        prompt = build_prompt(entry)
        # Determine optimal model for regex_cleaning task
        route = router.determine_optimal_route("regex_cleaning", payload_size=len(prompt))
        model = route["model"]
        provider = route["provider"]
        reason = route["reason"]
        print(f"\n🔧 Repairing {src_path.name} using {model} ({provider}, {reason}) …")

        # Re‑use the query_model function from test_agent_arena (import locally)
        sys.path.append(os.path.join(os.path.dirname(__file__)))
        from test_agent_arena import query_model  # type: ignore

        try:
            response, latency, tokens = query_model(model, prompt)
            print(f"   → Model responded (latency={latency:.2f}s, tokens={tokens})")
            # Write back the fixed content
            src_path.write_text(response.strip(), encoding="utf-8")
            print(f"   ✅ Written fixed content to {src_path}")
            fixed_any = True
        except Exception as e:
            print(f"   ❌ Error querying model: {e}")

    if fixed_any:
        print("\n🔧 Repair complete. Re‑run the build to regenerate the site.")
    else:
        print("\n⚠️  No files were repaired.")


if __name__ == "__main__":
    main()
