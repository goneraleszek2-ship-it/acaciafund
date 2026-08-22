"""Bitmask Exporter: Export deontic bitmasks to JSON for Edge KV storage."""

import json
from pathlib import Path
from datetime import datetime

ROOT = Path("/root/acaciafund")
BITMASK_PATH = ROOT / "dist" / "deontic_bitmasks.json"
EXPORT_PATH = ROOT / "static" / "bitmask-data.json"


def export_bitmasks(bitmask_path: Path = None, export_path: Path = None) -> dict:
    """Export deontic bitmasks to static JSON for Edge KV lookup."""
    if bitmask_path is None:
        bitmask_path = Path("/root/acaciafund/dist/deontic_bitmasks.json")
    if export_path is None:
        export_path = Path("/root/acaciafund/static/bitmask-data.json")

    with open(bitmask_path) as f:
        data = json.load(f)

    # Flatten bitmasks into lookup-friendly format
    flattened = {
        "obligation_mask_hex": hex(data["obligation_mask"]),
        "permission_mask_hex": hex(data["permission_mask"]),
        "prohibition_mask_hex": hex(data["prohibition_mask"]),
        "obligation_bit_count": data["obligation_count"],
        "permission_bit_count": data["permission_count"],
        "prohibition_bit_count": data["prohibition_count"],
        "generated": datetime.now().isoformat(),
        "source": "acaciafund_deontic_bitmasks",
    }

    with open(export_path, "w") as f:
        json.dump(flattened, f, indent=2)

    print(f"Bitmask data exported to: {export_path}")
    return flattened


def get_deontic_state(pillar: str, concept_id: str, bitmask_data: dict) -> str:
    """Look up deontic state for a specific pillar/concept combo via bitmask checks.

    O(1) lookup using precomputed bitmasks.
    """
    obligation_mask = bitmask_data["obligation_mask"]
    permission_mask = bitmask_data["permission_mask"]
    prohibition_mask = bitmask_data["prohibition_mask"]

    offset = sum(ord(c) for c in concept_id[:3]) % 60
    bit = 1 << offset

    is_obligation = bool(obligation_mask & bit)
    is_permission = bool(permission_mask & bit)
    is_prohibition = bool(prohibition_mask & bit)

    if is_prohibition:
        return "F"  # Prohibition
    elif is_obligation:
        return "O"  # Obligation
    elif is_permission:
        return "P"  # Permission
    else:
        return "N"  # Neutral


def main():
    import sys
    bitmask_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/root/acaciafund/dist/deontic_bitmasks.json")
    export_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("/root/acaciafund/static/bitmask-data.json")

    result = export_bitmasks(bitmask_path, export_path)
    print(f"Exported bitmask data: {result['obligation_bit_count']} obligation bits, "
          f"{result['permission_bit_count']} permission bits, "
          f"{result['prohibition_bit_count']} prohibition bits")


if __name__ == "__main__":
    main()
