"""Build script: Compile deontic states (O, P, F) into integer bitmasks.

Classification and bit-assignment live in ``core.deontic``; this script only
adds run metadata and writes the artifact. Masks are arbitrary-precision
integers (the registry has more than 64 deontically-classified concepts, so a
64-bit mask cannot be injective).
"""
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ONT_PATH = ROOT / "data" / "ontology.json"
KV_PATH = ROOT / "dist" / "deontic_bitmasks.json"


def main():
    from core.deontic import build_deontic_masks

    with open(ONT_PATH) as f:
        data = json.load(f)

    result = build_deontic_masks(data["concepts"])
    result["metadata"] = {
        "generated": datetime.now().isoformat(),
        "source": "acaciafund_deontic_bitmasks",
        "ontology_concepts": len(data["concepts"]),
        "classified_concepts": len(result["index_map"]),
        "pillar_distribution": {
            "aml": sum(1 for c in data["concepts"] if c["pillar"] == "aml"),
            "stock": sum(1 for c in data["concepts"] if c["pillar"] == "stock"),
            "data-engineering": sum(1 for c in data["concepts"] if c["pillar"] == "data-engineering"),
        },
    }

    KV_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(KV_PATH, "w") as f:
        json.dump(result, f, indent=2)

    print("Deontic bitmasks generated:")
    print(f"  Obligation mask: {result['obligation_mask']} ({result['obligation_count']} bits set)")
    print(f"  Permission mask: {result['permission_mask']} ({result['permission_count']} bits set)")
    print(f"  Prohibition mask: {result['prohibition_mask']} ({result['prohibition_count']} bits set)")
    print(f"  Classified concepts: {result['metadata']['classified_concepts']}")
    print(f"  Output: {KV_PATH}")


if __name__ == "__main__":
    main()
