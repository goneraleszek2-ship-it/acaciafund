#!/usr/bin/env python3
"""Transaction graph analysis toolkit for AML layering detection.

Detects circular transaction patterns (layering/structuring) using
NetworkX cycle enumeration with configurable weight thresholds.
"""

import networkx as nx


def detect_layering_cycles(
    edge_list: list[tuple[str, str, float]],
    weight_threshold: float = 5000.0,
) -> list[list[str]]:
    """Construct a directed transaction graph and return closed loops
    (cycles of length >= 3) indicative of layering or structuring.

    Parameters
    ----------
    edge_list : list of (source, target, amount) tuples
        Each tuple represents a single transaction from source to target
        with the specified monetary amount.
    weight_threshold : float
        Minimum transaction amount for an edge to be included in the
        analysis. Edges below this threshold are filtered out to reduce
        noise from small-value transactions.

    Returns
    -------
    list[list[str]]
        A list of cycles, where each cycle is a list of node identifiers
        forming a directed closed loop of length >= 3.
    """
    G = nx.DiGraph()
    for source, target, amount in edge_list:
        if amount >= weight_threshold:
            G.add_edge(source, target, weight=amount)

    all_cycles = list(nx.simple_cycles(G))
    return [c for c in all_cycles if len(c) >= 3]


if __name__ == "__main__":
    mock_ledger = [
        ("AccA", "AccB", 10500.0),
        ("AccB", "AccC", 10200.0),
        ("AccC", "AccA", 9900.0),
        ("AccD", "AccE", 3000.0),   # below threshold, filtered out
        ("AccE", "AccF", 2500.0),
    ]
    cycles = detect_layering_cycles(mock_ledger, 5000.0)
    print("Detected Layering Networks:", cycles)
