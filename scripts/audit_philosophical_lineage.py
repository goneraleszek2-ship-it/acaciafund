"""Cluster ontology concepts by shared philosophical lineage.

Usage:
    python3 scripts/audit_philosophical_lineage.py
    python3 scripts/audit_philosophical_lineage.py --format json
    python3 scripts/audit_philosophical_lineage.py --min-cluster 3
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def main():
    parser = argparse.ArgumentParser(description="Cluster concepts by philosophical lineage")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    parser.add_argument("--min-cluster", type=int, default=2, help="Minimum concepts per lineage tag to include")
    args = parser.parse_args()

    path = PROJECT_ROOT / "data" / "philosophy_metadata.json"
    if not path.exists():
        print(f"ERROR: {path} not found")
        sys.exit(1)
    metadata = json.loads(path.read_text())

    # lineage_tag -> [(concept_id, pillar)]
    clusters: dict[str, list[dict]] = defaultdict(list)
    for cid, data in metadata.items():
        for tag in data.get("philosophical_lineage", []):
            clusters[tag].append({"id": cid, "pillar": data.get("epistemic_status", "")})

    filtered = {tag: members for tag, members in sorted(clusters.items()) if len(members) >= args.min_cluster}
    by_size = sorted(filtered.items(), key=lambda x: -len(x[1]))

    # Cross-pillar clusters
    cross_pillar = [(tag, members) for tag, members in by_size if len({m["pillar"] for m in members}) > 1]

    report = {
        "summary": {
            "total_lineage_tags": len(clusters),
            "clusters_above_threshold": len(filtered),
            "cross_pillar_clusters": len(cross_pillar),
        },
        "clusters": [
            {"tag": tag, "count": len(members), "concepts": members}
            for tag, members in by_size
        ],
        "cross_pillar_clusters": [
            {"tag": tag, "count": len(members), "pillars": sorted({m["pillar"] for m in members})}
            for tag, members in cross_pillar
        ],
    }

    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        s = report["summary"]
        print(f"{'='*60}")
        print(f"  PHILOSOPHICAL LINEAGE CLUSTERS")
        print(f"{'='*60}")
        print(f"  Total lineage tags:         {s['total_lineage_tags']}")
        print(f"  Clusters (≥{args.min_cluster} concepts):  {s['clusters_above_threshold']}")
        print(f"  Cross-pillar clusters:      {s['cross_pillar_clusters']}")
        print()

        for entry in by_size[:20]:
            tag = entry[0]
            members = entry[1]
            pillars = sorted({m["pillar"] for m in members})
            is_cross = "★" if len(pillars) > 1 else " "
            print(f"  {is_cross} {tag:30s}  {len(members):2d} concepts  pillars={pillars}")
        print()
        if cross_pillar:
            print(f"  {'─'*40}")
            print(f"  CROSS-PILLAR CLUSTERS (synthesis candidates)")
            print(f"  {'─'*40}")
            for tag, members in cross_pillar:
                pillars = sorted({m["pillar"] for m in members})
                print(f"    {tag:30s}  {len(members):2d} concepts  across {pillars}")


if __name__ == "__main__":
    main()
