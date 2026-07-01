#!/usr/bin/env python3
"""
Execute UI/UX bug fixes using the live agent router.
For each bug, asks the optimal model to produce the fixed file content,
then writes it to disk and runs the build.
"""

import os
import sys
import time
from pathlib import Path

# Ensure we can import from core
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from core.agent_router import get_optimal_model_for_task

# Reuse the query_model function from test_agent_arena (or redefine)
# We'll import it to avoid duplication
sys.path.append(os.path.join(os.path.dirname(__file__)))
from test_agent_arena import query_model  # type ignore

DATA_DIR = Path("/root/acaciafund/data")
STATIC_CSS = Path("/root/acaciafund/static/css/custom.css")
TEMPLATES_DIR = Path("/root/acaciafund/templates")
BLOG_POST_J2 = TEMPLATES_DIR / "blog_post.j2"
LEARN_INDEX_J2 = TEMPLATES_DIR / "learn_index.j2"

TASKS = [
    {
        "name": "Fix text truncation and inject CSS -webkit-line-clamp",
        "category": "css_layout",
        "prompt": (
            "Return the full contents of the CSS file at static/css/custom.css "
            "with the following rule added or ensured: "
            ".card-research-summary { display: -webkit-box; -webkit-line-clamp: 3; "
            "-webkit-box-orient: vertical; overflow: hidden; font-size: 0.875rem; "
            "line-height: 1.55; color: var(--color-text-secondary); } "
            "Do not include any extra explanation, only the raw CSS file content."
        ),
        "target_file": STATIC_CSS,
    },
    {
        "name": "Fix Blank Asset Containers under Knowledge Check",
        "category": "regex_cleaning",
        "prompt": (
            "Return the full contents of the Jinja2 template file at templates/blog_post.j2 "
            "with the signals section guarded so it only renders when content.signals exists "
            "and has a count > 0. Specifically, change the line that currently reads "
            "'{%- if content.signals %}' to '{%- if content.signals and content.signals.get(\"count\", 0) > 0 %}'. "
            "Do not include any extra explanation, only the raw template file content."
        ),
        "target_file": BLOG_POST_J2,
    },
    {
        "name": "Fix Learning Hub Dashboard 0/0 progress bar blowout",
        "category": "system_architecture",
        "prompt": (
            "Return the full contents of the Jinja2 template file at templates/learn_index.j2 "
            "with the following two changes: "
            "1) Add the class 'learn-card' to both <a> elements that have class 'ghost-card block' "
            "   (around lines 198 and 244). "
            "2) In the JavaScript section, change the pillar progress detection from using "
            "   card.querySelector('[class*=\"inline-flex\"]').textContent.indexOf(pathKey) > -1 "
            "   to card.getAttribute('data-pillar') === pathKey. "
            "Do not include any extra explanation, only the raw template file content."
        ),
        "target_file": LEARN_INDEX_J2,
    },
]


def main():
    print("Starting automated UI/UX bug fixing via live agent router...\n")
    for task in TASKS:
        print(f"=== {task['name']} ===")
        category = task["category"]
        model_name = get_optimal_model_for_task(category)
        print(f"Selected model for category '{category}': {model_name}")

        prompt = task["prompt"]
        print(f"Querying model {model_name}...")
        try:
            response, latency, tokens = query_model(model_name, prompt)
            print(f"Received response (latency: {latency:.2f}s, tokens: {tokens})")
            # Write the response to the target file
            target = task["target_file"]
            # Backup original
            backup = target.with_suffix(target.suffix + ".bak")
            if target.exists():
                backup.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")
                print(f"Backed up original to {backup}")
            # Write new content
            target.write_text(response.strip(), encoding="utf-8")
            print(f"Written fixed content to {target}")
        except Exception as e:
            print(f"Error processing task: {e}")
            continue
        print()

    # Run the build
    print("Running full build...")
    start = time.time()
    # We'll run build.py and capture output
    import subprocess

    result = subprocess.run(
        [sys.executable, "build.py"],
        cwd="/root/acaciafund",
        capture_output=True,
        text=True,
    )
    elapsed = time.time() - start
    if result.returncode == 0:
        print(f"Build succeeded in {elapsed:.2f}s.")
        print(f"Output: {result.stdout[-500:] if len(result.stdout) > 500 else result.stdout}")
    else:
        print(f"Build failed after {elapsed:.2f}s.")
        print(f"Stdout: {result.stdout}")
        print(f"Stderr: {result.stderr}")

    print("\nDone.")


if __name__ == "__main__":
    main()
