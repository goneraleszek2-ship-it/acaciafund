"""Schema builder — transforms ontology prerequisite relations into learning-path DAGs.

Provides:
  build_prerequisite_graph(manager) → nx.DiGraph
  compute_learning_paths(graph, start_concept_id, depth) → List[LearningPath]
  categorize_by_bloom(concept_id, graph) → str
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List

import networkx as nx

from core.ontology import OntologyManager

logger = logging.getLogger(__name__)


@dataclass
class LearningPath:
    concepts: List[Dict] = field(default_factory=list)
    total_depth: int = 0
    pillar_span: int = 0
    start: str = ""
    end: str = ""

    def __post_init__(self):
        self.total_depth = max(0, len(self.concepts) - 1)
        pillars = {c.get("pillar", "") for c in self.concepts}
        self.pillar_span = len(pillars)


def build_prerequisite_graph(manager: OntologyManager) -> nx.DiGraph:
    """Build a directed graph from 'requires' relations only.

    Skips edges that would introduce a cycle (logs a warning).
    Each node carries 'id', 'label', 'pillar' attributes.
    """
    graph = nx.DiGraph()

    for relation in manager._relations:
        if relation.relation_type != "requires":
            continue

        src = manager.get_concept(relation.source_id)
        tgt = manager.get_concept(relation.target_id)
        if not src or not tgt:
            continue

        if src.id not in graph:
            graph.add_node(src.id, id=src.id, label=src.label, pillar=src.pillar)
        if tgt.id not in graph:
            graph.add_node(tgt.id, id=tgt.id, label=tgt.label, pillar=tgt.pillar)

        if graph.has_edge(src.id, tgt.id):
            continue

        graph.add_edge(src.id, tgt.id)
        if not nx.is_directed_acyclic_graph(graph):
            graph.remove_edge(src.id, tgt.id)
            logger.warning("Cycle detected: skipping edge %s -> %s", src.id, tgt.id)

    return graph


def compute_learning_paths(
    graph: nx.DiGraph,
    start_concept_id: str,
    depth: int = 3,
) -> List[LearningPath]:
    """BFS from start concept to find all learning paths up to `depth` hops.

    Returns paths sorted by total_depth descending (longest path first).
    Returns empty list if start_concept_id has no outgoing 'requires' edges.
    """
    if start_concept_id not in graph:
        return []

    paths: List[LearningPath] = []

    def _bfs(current: str, path_ids: List[str], remaining: int):
        if remaining < 0:
            return
        if remaining == 0 or not list(graph.successors(current)):
            if len(path_ids) > 1:
                concepts = [
                    {
                        "id": nid,
                        "label": graph.nodes[nid].get("label", nid),
                        "pillar": graph.nodes[nid].get("pillar", ""),
                    }
                    for nid in path_ids
                ]
                paths.append(
                    LearningPath(
                        concepts=concepts,
                        start=path_ids[0],
                        end=path_ids[-1],
                    )
                )
            return
        for successor in graph.successors(current):
            if successor in path_ids:
                continue
            _bfs(successor, path_ids + [successor], remaining - 1)

    _bfs(start_concept_id, [start_concept_id], depth)
    paths.sort(key=lambda p: p.total_depth, reverse=True)
    return paths


def categorize_by_bloom(concept_id: str, graph: nx.DiGraph) -> str:
    """Map a concept's position in the prerequisite DAG to a Bloom taxonomy level.

    Rules:
      - Depth 0 (no incoming 'requires') → "remember"
      - Depth 1-2 → "apply"
      - Depth 3+ → "evaluate"

    Depth is the longest distance from any root (node with no predecessors
    in the 'requires' graph) to this concept.
    """
    if concept_id not in graph:
        return "remember"

    roots = [n for n in graph.nodes() if not list(graph.predecessors(n))]
    depth = 0
    for root in roots:
        if nx.has_path(graph, root, concept_id):
            try:
                d = len(nx.shortest_path(graph, root, concept_id)) - 1
                if d > depth:
                    depth = d
            except nx.NetworkXNoPath:
                continue

    if depth >= 3:
        return "evaluate"
    if depth >= 1:
        return "apply"
    return "remember"
