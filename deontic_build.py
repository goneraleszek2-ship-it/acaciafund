"""Build script: Compile deontic states (O, P, F) into 64-bit integer bitmasks."""
import json
from pathlib import Path
from datetime import datetime

ROOT = Path("/root/acaciafund")
ONT_PATH = ROOT / "data" / "ontology.json"
KV_PATH = ROOT / "dist" / "deontic_bitmasks.json"


def classify_deontic(concept):
    pillar = concept.get("pillar", "")
    epistemic = concept.get("epistemic_status", "").lower()
    if epistemic in ["regulatory", "constitutive"] and pillar in ["aml", "compliance"]:
        return "O"
    elif epistemic in ["instrumental", "pragmatic"] and pillar in ["stock", "market"]:
        return "P"
    elif epistemic == "ontological":
        return "F"
    else:
        return None


def main():
    with open(ONT_PATH) as f:
        data = json.load(f)

    obligation_mask = 0
    permission_mask = 0
    prohibition_mask = 0

    for concept in data["concepts"]:
        cid = concept["id"]
        dclass = classify_deontic(concept)
        if dclass is None:
            continue
        offset = sum(ord(c) for c in cid[:3]) % 60
        bit = 1 << offset
        if dclass == "O":
            obligation_mask |= bit
        elif dclass == "P":
            permission_mask |= bit
        elif dclass == "F":
            prohibition_mask |= bit

    obligation_mask = obligation_mask & ((1 << 64) - 1)
    permission_mask = permission_mask & ((1 << 64) - 1)
    prohibition_mask = prohibition_mask & ((1 << 64) - 1)

    result = {
        "obligation_mask": obligation_mask,
        "permission_mask": permission_mask,
        "prohibition_mask": prohibition_mask,
        "obligation_count": bin(obligation_mask).count("1"),
        "permission_count": bin(permission_mask).count("1"),
        "prohibition_count": bin(prohibition_mask).count("1"),
        "metadata": {
            "generated": datetime.now().isoformat(),
            "source": "acaciafund_deontic_bitmasks",
            "ontology_concepts": len(data["concepts"]),
            "pillar_distribution": {
                "aml": sum(1 for c in data["concepts"] if c["pillar"] == "aml"),
                "stock": sum(1 for c in data["concepts"] if c["pillar"] == "stock"),
                "data-engineering": sum(1 for c in data["concepts"] if c["pillar"] == "data-engineering"),
            }
        }
    }

    with open(KV_PATH, "w") as f:
        json.dump(result, f, indent=2)

    print("Deontic bitmasks generated:")
    print(f"  Obligation mask: {result['obligation_mask']} ({result['obligation_count']} bits set)")
    print(f"  Permission mask: {result['permission_mask']} ({result['permission_count']} bits set)")
    print(f"  Prohibition mask: {result['prohibition_mask']} ({result['prohibition_count']} bits set)")
    print(f"  Output: {KV_PATH}")


if __name__ == "__main__":
    main()