#!/usr/bin/env python3
"""Validate ontology as a deterministic acyclic graph (DAG) mirroring
Salamucha's formal proofs of causality.

Checks:
  1. Prerequisite ('requires') edges form a DACyc (no circular dependencies)
  2. Epistemic metadata coverage on all nodes
  3. Prerequisite necessity: B cannot be derived without A in A→B
  4. Redundant edges: B reachable from A without the direct edge
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

import networkx as nx

PROJECT_ROOT = Path(__file__).parent.parent
ONTOLOGY_PATH = PROJECT_ROOT / "data" / "ontology.json"
REPORT_PATH = PROJECT_ROOT / "dist" / "validation_report.json"


def load_ontology(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    ontology = load_ontology(ONTOLOGY_PATH)
    concepts = ontology.get("concepts", [])
    relations = ontology.get("relations", [])

    G = nx.DiGraph()
    for c in concepts:
        G.add_node(c["id"], epistemic_status=c.get("epistemic_status", ""))
    for r in relations:
        G.add_edge(r["source_id"], r["target_id"], type=r.get("relation_type", ""))

    # 1. Check acyclicity of prerequisite subgraph
    req_graph = nx.subgraph_view(G, filter_edge=lambda u, v: G[u][v]["type"] == "requires")
    is_acyclic = nx.is_directed_acyclic_graph(req_graph)

    # 2. Epistemic metadata coverage
    unqualified = [n for n, d in G.nodes(data=True) if not d.get("epistemic_status")]
    total_nodes = G.number_of_nodes()

    # 3. Prerequisite necessity check
    # For each A→B (requires), verify B cannot be derived without A
    redundant_edges = []
    for u, v, d in G.edges(data=True):
        if d["type"] == "requires":
            # Temporarily remove u and check if v is still reachable from any predecessor
            # that doesn't go through u
            G_temp = G.copy()
            G_temp.remove_node(u)
            # Check if v is reachable from any node that previously reached v via u
            # Simple check: is v reachable from any node without going through u?
            # We'll check if there's an alternative path to v
            try:
                # Check all predecessors of v in original graph
                alt_paths = 0
                for predecessor in list(G.predecessors(v)):
                    if predecessor == u:
                        continue
                    try:
                        nx.shortest_path(G_temp, source=predecessor, target=v)
                        alt_paths += 1
                    except nx.NetworkXNoPath:
                        pass
                if alt_paths > 0:
                    redundant_edges.append({
                        "edge": (u, v),
                        "alt_paths_found": alt_paths,
                        "reason": "v reachable from alternative predecessors without u"
                    })
            except Exception as e:
                redundant_edges.append({
                    "edge": (u, v),
                    "error": str(e)
                })

    # 4. Summary
    report = {
        "total_concepts": total_nodes,
        "is_acyclic": is_acyclic,
        "unqualified_concepts": unqualified,
        "unqualified_count": len(unqualified),
        "redundant_requires_edges": len(redundant_edges),
        "details": {
            "redundant_edges": redundant_edges[:20],  # first 20 for brevity
            "unqualified_sample": unqualified[:10]
        }
    }

    save_json(REPORT_PATH, report)
    print(f"Validation report written to {REPORT_PATH}")
    print(f"  Total concepts: {total_nodes}")
    print(f"  Prerequisite DAG acyclic: {is_acyclic}")
    print(f"  Unqualified concepts (no epistemic_status): {len(unqualified)}")
    print(f"  Redundant requires edges: {len(redundant_edges)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())