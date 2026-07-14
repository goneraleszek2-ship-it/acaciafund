#!/usr/bin/env python3
"""
Verification script for agent router.
Shows which model would be selected for each UI/UX fix category.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.agent_router import get_optimal_model_for_task

# Map UI/UX fixes to categories (as per our task definitions)
UI_UX_MAP = {
    "word truncation bug": "css_layout",  # card-research-summary line-clamp CSS
    "0/0 progress bar blowout": "system_architecture",  # general JS/system issue
    "empty container issue": "regex_cleaning",  # signal detection/regex-ish? fallback
}


def main():
    print("Agent Router Verification")
    print("=" * 40)
    for issue, category in UI_UX_MAP.items():
        model = get_optimal_model_for_task(category)
        print(f"Issue: {issue:<30} Category: {category:<20} -> Selected Model: {model}")
    print("\nNote: Selection based on data/agent_matching_matrix.json")
    print("Run `python3 scripts/test_agent_arena.py` to update matrix with live data.")


if __name__ == "__main__":
    main()
