#!/usr/bin/env python3
"""AcaciaFund Onboarding — sets user preferences for philosophical framework.

This script creates a preferences file at ~/.acaciafund/preferences.json
with the user's chosen way_of_knowing and philosophy version.
Subsequent runs are no-ops (preferences already set).

Usage:
    python3 scripts/onboard_tutorial.py    # Interactive — sets preferences
    python3 -c "import json; json.load(open('~/.acaciafund/preferences.json'))"  # Verify
"""

import json
import os
import sys
from pathlib import Path

# Ensure config is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import PILLAR_VALIDATION_WEIGHTS
import sys

PREFERENCES_DIR = Path.home() / ".acaciafund"
PREFERENCES_FILE = PREFERENCES_DIR / "preferences.json"


def ensure_dir():
    PREFERENCES_DIR.mkdir(parents=True, exist_ok=True)


def preferences_exist():
    return PREFERENCES_FILE.is_file()


def load_default_preferences():
    """Load default preferences based on philosophy version v1.0-pluralistic-2026-08."""
    return {
        "philosophy_version": "v1.0-pluralistic-2026-08",
        "way_of_knowing": "empirical",  # default; user can change
        "pillar_weights": {
            "aml": {"empirical_fidelity": 0.3, "coherence": 0.2, "philosophical_consistency": 0.2, "schema_validity": 0.2, "test_suite_validity": 0.1},
            "stock": {"empirical_fidelity": 0.3, "coherence": 0.2, "philosophical_consistency": 0.2, "schema_validity": 0.2, "test_suite_validity": 0.1},
            "data-engineering": {"empirical_fidelity": 0.25, "coherence": 0.25, "philosophical_consistency": 0.2, "schema_validity": 0.2, "test_suite_validity": 0.1},
        },
    }


def interactive_setup():
    """Interactive preference selection."""
    print("=" * 58)
    print("  AcaciaFund Onboarding — Philosophical Framework Setup")
    print("=" * 58)
    print()

    # Way of knowing
    print("  Step 1: Select your primary way of knowing.")
    print("  This affects how content is filtered and displayed.")
    print()
    print("  1. empirical   - Knowledge from verified external sources")
    print("  2. contemplative - Knowledge as contemplative practice")
    print("  3. authority   - Knowledge from established authorities/tradition")
    print("  4. experiential - Knowledge from direct experience/practice")
    print()

    way_map = {"1": "empirical", "2": "contemplative", "3": "authority", "4": "experiential"}
    while True:
        choice = input("  Your choice (1-4): ").strip()
        if choice in way_map:
            way_of_knowing = way_map[choice]
            break
        print("  Please enter 1, 2, 3, or 4.")

    print(f"  Selected way of knowing: {way_of_knowing}")
    print()

    # Philosophy version
    print("  Step 2: Philosophy version (for change-tracking).")
    print(f"  Current: v1.0-pluralistic-2026-08")
    print("  This version is tracked in every content item's metadata.")
    print("  Change it when you deliberately modify validation tracks or philosophical framing.")
    version = input("  Accept current version? (y/n, default y): ").strip().lower()
    if version != "y" and version != "":
        # In a real system, would let user select from version history
        version = "v1.0-pluralistic-2026-08"  # fallback
    else:
        version = "v1.0-pluralistic-2026-08"

    print(f"  Philosophy version: {version}")
    print()

    # Create preferences
    prefs = load_default_preferences()
    prefs["way_of_knowing"] = way_of_knowing
    prefs["philosophy_version"] = version

    # Add pillar weights based on selected way of knowing
    # (This is a simplified example - real implementation would adjust weights)
    print("  Step 3: Pillar validation weights.")
    print("  These determine how the 5 validation tracks influence accept/reject/review")
    print("  decisions per pillar. Defaults are shown below.")
    print()
    from config import PILLAR_VALIDATION_WEIGHTS
    for pillar, weights in PILLAR_VALIDATION_WEIGHTS.items():
        print(f"  {pillar}: empirical={weights['empirical_fidelity']}, "
              f"coherence={weights['coherence']}, philosophical={weights['philosophical_consistency']}, "
              f"schema={weights['schema_validity']}, tests={weights['test_suite_validity']}")
    print()
    print("  Weight adjustments are optional - defaults are used if not specified.")

    # Write preferences
    ensure_dir()
    with open(PREFERENCES_FILE, "w") as f:
        json.dump(prefs, f, indent=2)

    print("=" * 58)
    print("  Preferences saved to: ~-/acaciafund/preferences.json")
    print("  " + str(PREFERENCES_FILE))
    print("=" * 58)
    print()
    print("  Onboarding complete. You may now use AcaciaFund with your")
    print("  selected philosophical framework actively in effect.")
    print("  To adjust preferences later, re-run this script or edit")
    print("  ~/acaciafund/preferences.json directly.")


def main():
    ensure_dir()

    if preferences_exist():
        print("=" * 58)
        print("  AcaciaFund Onboarding — Preferences Already Set")
        print("=" * 58)
        print()
        print(f"  Preferences already exist at: {PREFERENCES_FILE}")
        print("  Loading existing preferences...")
        print()

        # Load and display
        try:
            with open(PREFERENCES_FILE) as f:
                prefs = json.load(f)
            print(f"  way_of_knowing: {prefs.get('way_of_knowing')}")
            print(f"  philosophy_version: {prefs.get('philosophy_version')}")
            print(f"  pillar_weights: {prefs.get('pillar_weights', 'using defaults')}")
        except Exception as e:
            print(f"  Error loading preferences: {e}")
            print("  Re-setting preferences...")
            interactive_setup()
        print()
        print("  Onboarding already complete. Skip re-onboarding with:")
        print("  $ rm ~/acaciafund/preferences.json  # then re-run this script")
        print()
        return

    interactive_setup()


if __name__ == "__main__":
    main()