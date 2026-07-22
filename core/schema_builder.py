"""Schema builder — transforms ontology prerequisite relations into learning-path DAGs.

Provides:
  build_prerequisite_graph(manager) → nx.DiGraph
  compute_learning_paths(graph, start_concept_id, depth) → List[LearningPath]
  categorize_by_bloom(concept_id, graph) → str
  compute_feynman_learning_paths(manager) → List[FeynmanLearningPath]
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

import networkx as nx

from core.ontology import Concept, OntologyManager

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


# ---------------------------------------------------------------------------
# Feynman Learning Paths
# ---------------------------------------------------------------------------

FEYNMAN_STAGE_TYPES = ["eli5", "analogy", "concrete", "gap_map", "build", "teach_back"]


@dataclass
class FeynmanStage:
    """A single stage in a Feynman learning path."""

    stage_type: str
    label: str
    description: str
    concept_ids: List[str]
    prompt: str = ""
    difficulty_range: Tuple[int, int] = (1, 2)


@dataclass
class FeynmanLearningPath:
    """A structured learning journey using Feynman technique stages."""

    pillar: str
    stages: List[FeynmanStage] = field(default_factory=list)
    total_concepts: int = 0
    difficulty_tiers: List[int] = field(default_factory=list)


@dataclass
class CrossPillarFeynmanTriple:
    """A triple of analog concepts across pillars."""
    source_id: str
    source_pillar: str
    target_id: str
    target_pillar: str
    relation_type: str = "analogous"


@dataclass
class CrossPillarFeynmanPath:
    """A cross-pillar Feynman synthesis grouping analog concepts together."""
    pillar: str  # hosting pillar
    triples: List[CrossPillarFeynmanTriple] = field(default_factory=list)
    total_triples: int = 0
    connected_pillars: List[str] = field(default_factory=list)


def _order_by_prerequisites(
    concept_ids: List[str],
    manager: OntologyManager,
) -> List[str]:
    """Topological sort by prerequisite ('requires') relations.

    Concepts with no prerequisites come first within their group.
    Falls back to original order if no DAG can be built.
    """
    if len(concept_ids) <= 1:
        return concept_ids

    graph = nx.DiGraph()
    for cid in concept_ids:
        graph.add_node(cid)
    for cid in concept_ids:
        prereqs = [
            r.target_id for r in manager.outgoing_relations(cid)
            if r.relation_type == "requires" and r.target_id in concept_ids
        ]
        for p in prereqs:
            graph.add_edge(p, cid)

    try:
        order = list(nx.topological_sort(graph))
        if order:
            return order
    except nx.NetworkXUnfeasible:
        pass

    return concept_ids


STAGE_DEFS: Dict[str, Dict] = {
    "eli5": {
        "label": "Explain Like I'm 5",
        "description": "Start with a one-paragraph, no-jargon explanation for absolute beginners.",
        "prompt": "Explain this concept to someone with no background knowledge.",
        "difficulty_range": (1, 2),
    },
    "analogy": {
        "label": "Analogy Mapping",
        "description": "Map the concept to a real-world analogy that makes it intuitive.",
        "prompt": "Create an analogy from everyday life that captures the essence of this concept.",
        "difficulty_range": (1, 2),
    },
    "concrete": {
        "label": "Concrete Example",
        "description": "Work through a specific, numbered example with real data or code.",
        "prompt": "Walk through a concrete example step by step.",
        "difficulty_range": (2, 3),
    },
    "gap_map": {
        "label": "Gap Map",
        "description": (
            "Identify what you don't know yet — questions that expose"
            " understanding gaps."
        ),
        "prompt": (
            "Answer these gap-detection questions. If you can't, review the"
            " prerequisite concepts first."
        ),
        "difficulty_range": (1, 5),
    },
    "build": {
        "label": "Build Exercise",
        "description": (
            "Create something — code, a diagram, or a calculation — to prove"
            " understanding."
        ),
        "prompt": "Complete the hands-on exercise to verify deep understanding.",
        "difficulty_range": (2, 5),
    },
    "teach_back": {
        "label": "Teach Back",
        "description": (
            "Explain the concept in your own words as if teaching a peer."
        ),
        "prompt": (
            "Teach this concept back. Cover: what it is, how it works,"
            " why it matters."
        ),
        "difficulty_range": (3, 5),
    },
}


def compute_feynman_learning_paths(
    manager: OntologyManager,
) -> List[FeynmanLearningPath]:
    """Build Feynman-scaffolded learning paths for each pillar.

    Groups concepts by pillar, orders by Feynman difficulty within each pillar,
    then assigns concepts to sequential Feynman stages:

      1. ELI5       — difficulty 1-2 concepts with eli5_explanation
      2. Analogy    — difficulty 1-2 concepts with analogy
      3. Concrete   — difficulty 2-3 concepts with concrete_example
      4. Gap Map    — all concepts with gap_questions (checkpoints)
      5. Build      — concepts with build_exercise (hands-on)
      6. Teach Back — all concepts (final checkpoints)

    Within each stage, concepts are topologically sorted by prerequisites.
    """
    pillars: Dict[str, List[Concept]] = {}
    for c in manager._concepts.values():
        pillars.setdefault(c.pillar, []).append(c)

    paths: List[FeynmanLearningPath] = []

    for pillar_key, concepts in pillars.items():
        if not concepts:
            continue

        # Sort concepts by feynman_difficulty
        sorted_concepts = sorted(concepts, key=lambda c: (
            getattr(c, "feynman_difficulty", 1) or 1,
            c.label,
        ))

        stages: List[FeynmanStage] = []
        seen_ids: set = set()
        all_ids = [c.id for c in sorted_concepts]

        for stage_type in FEYNMAN_STAGE_TYPES:
            stage_def = STAGE_DEFS[stage_type]
            dr = stage_def["difficulty_range"]

            candidate_ids = []
            for c in sorted_concepts:
                fd = getattr(c, "feynman_difficulty", 1) or 1
                if not (dr[0] <= fd <= dr[1]):
                    continue
                _eli5 = c.eli5_explanation is not None
                _analogy = c.analogy is not None
                _concrete = c.concrete_example is not None
                _gaps = c.gap_questions is not None and len(c.gap_questions) > 0
                _build = c.build_exercise is not None
                _teach = c.teach_back_prompt is not None
                if stage_type == "eli5" and not _eli5:
                    continue
                if stage_type == "analogy" and not _analogy:
                    continue
                if stage_type == "concrete" and not _concrete:
                    continue
                if stage_type == "gap_map" and not _gaps:
                    continue
                if stage_type == "build" and not _build:
                    continue
                if stage_type == "teach_back" and not _teach:
                    continue
                candidate_ids.append(c.id)

            if stage_type in ("gap_map", "build", "teach_back"):
                # Make sure gap_map, build, teach_back include ALL concepts from earlier stages too
                for prev_cid in all_ids:
                    if prev_cid not in candidate_ids and prev_cid not in seen_ids:
                        candidate_ids.append(prev_cid)

            ordered = _order_by_prerequisites(candidate_ids, manager)
            for cid in ordered:
                if cid not in seen_ids:
                    seen_ids.add(cid)

            if ordered:
                stages.append(FeynmanStage(
                    stage_type=stage_type,
                    label=stage_def["label"],
                    description=stage_def["description"],
                    concept_ids=ordered,
                    prompt=stage_def["prompt"],
                    difficulty_range=dr,
                ))

        difficulty_tiers = sorted(set(
            getattr(c, "feynman_difficulty", 1) or 1
            for c in concepts
        ))

        paths.append(FeynmanLearningPath(
            pillar=pillar_key,
            stages=stages,
            total_concepts=len(seen_ids),
            difficulty_tiers=difficulty_tiers,
        ))

    return paths


def compute_cross_pillar_feynman_paths(
    manager: OntologyManager,
) -> List[CrossPillarFeynmanPath]:
    """Build cross-pillar Feynman synthesis paths using cross_pillar_analogs.

    For each pillar, finds concepts that have analogs in OTHER pillars and
    groups them into triples. This creates "synthesis" paths that connect
    concepts across domains — the core of the Feynman technique.

    Returns one CrossPillarFeynmanPath per pillar (hosted from that pillar's perspective).
    """
    concepts = list(manager._concepts.values())
    analog_map: Dict[str, List[str]] = {}

    for c in concepts:
        analogs = getattr(c, "cross_pillar_analogs", None) or []
        if analogs:
            analog_map[c.id] = [a for a in analogs if a != c.id]

    pillar_concepts: Dict[str, List[Concept]] = {}
    for c in concepts:
        pillar_concepts.setdefault(c.pillar, []).append(c)

    paths: List[CrossPillarFeynmanPath] = []

    for pillar_key, p_concepts in pillar_concepts.items():
        triples: List[CrossPillarFeynmanTriple] = []
        seen_local: set = set()

        for c in p_concepts:
            source_analogs = analog_map.get(c.id, [])
            for analog_id in source_analogs:
                analog_c = manager.get_concept(analog_id)
                if not analog_c or analog_c.pillar == pillar_key:
                    continue
                pair_key = tuple(sorted([c.id, analog_id]))
                if pair_key in seen_local:
                    continue
                seen_local.add(pair_key)
                triples.append(CrossPillarFeynmanTriple(
                    source_id=c.id,
                    source_pillar=pillar_key,
                    target_id=analog_id,
                    target_pillar=analog_c.pillar,
                ))

        connected = sorted(set(t.target_pillar for t in triples))
        triples.sort(key=lambda t: (t.target_pillar, t.target_id))

        paths.append(CrossPillarFeynmanPath(
            pillar=pillar_key,
            triples=triples,
            total_triples=len(triples),
            connected_pillars=connected,
        ))

    return paths
