#!/usr/bin/env python3
"""Market regime detector — order-flow imbalance tracking.

Calculates directional pressure index from bid/ask volume arrays
collected at microsecond-level snapshots. Used to classify market
regimes (buying pressure, selling pressure, equilibrium).
"""

import numpy as np


def calculate_order_flow_imbalance(
    bid_volumes: np.ndarray,
    ask_volumes: np.ndarray,
) -> np.ndarray:
    """Compute the normalised directional pressure index.

    The imbalance score ranges in [-1, 1]:
      positive → buying pressure (bid volume exceeds ask volume)
      negative → selling pressure (ask volume exceeds bid volume)
      zero     → equilibrium (bid = ask or both zero)

    Parameters
    ----------
    bid_volumes : np.ndarray
        Array of bid-side volumes per microsecond snapshot.
    ask_volumes : np.ndarray
        Array of ask-side volumes per microsecond snapshot (same shape).

    Returns
    -------
    np.ndarray
        Per-snapshot imbalance scores. Shape matches input arrays.
    """
    delta_v = bid_volumes - ask_volumes
    total_v = bid_volumes + ask_volumes
    return np.divide(
        delta_v,
        total_v,
        out=np.zeros_like(delta_v, dtype=float),
        where=total_v != 0,
    )


def classify_regime(
    imbalance_scores: np.ndarray,
    buy_threshold: float = 0.30,
    sell_threshold: float = -0.30,
) -> list[str]:
    """Classify each snapshot's regime from its imbalance score.

    Parameters
    ----------
    imbalance_scores : np.ndarray
        Output from calculate_order_flow_imbalance.
    buy_threshold : float
        Scores above this value are classified as "buying_pressure".
    sell_threshold : float
        Scores below this value are classified as "selling_pressure".

    Returns
    -------
    list[str]
        Per-snapshot regime label.
    """
    labels = []
    for score in imbalance_scores:
        if score >= buy_threshold:
            labels.append("buying_pressure")
        elif score <= sell_threshold:
            labels.append("selling_pressure")
        else:
            labels.append("equilibrium")
    return labels


if __name__ == "__main__":
    # Simulated microsecond snapshots with variable liquidity
    bids = np.array([1200, 1500, 800, 400, 2200, 900])
    asks = np.array([1100, 900, 1400, 1600, 800, 1000])

    imbalance = calculate_order_flow_imbalance(bids, asks)
    regimes = classify_regime(imbalance)

    print("Microsecond Imbalance Signatures:", imbalance)
    print("Regime Classification:           ", regimes)
