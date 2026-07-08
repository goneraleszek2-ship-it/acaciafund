#!/usr/bin/env python3
"""Temporal smurfing and layering detector using time-decayed link intensity.

Computes exponential attenuation scores over inter-transaction deltas and
flags burst clusters where amounts fall below regulatory threshold but
temporal proximity suggests structured layering.
"""

import numpy as np


def calculate_temporal_attenuation(
    transaction_deltas: np.ndarray, alpha: float
) -> np.ndarray:
    """Compute time-decayed link intensity scores for rapid sequence transactions.

    Implements the exponential decay function:
        I(Δt) = exp(-alpha × Δt)

    where Δt is the inter-transaction interval in seconds and alpha is the
    decay rate parameter. Scores near 1.0 indicate near-instantaneous
    succession (Δt → 0); scores near 0.0 indicate widely separated events.

    Parameters
    ----------
    transaction_deltas : np.ndarray
        Array of time differences Δt_i = t_i - t_{i-1} in seconds.
    alpha : float
        Decay rate parameter (s⁻¹). Higher values penalise longer gaps
        more aggressively. For AML detection, typical alpha = 0.005 s⁻¹
        corresponds to a half-life of approximately 138 seconds.

    Returns
    -------
    np.ndarray
        Attenuation scores in [0, 1] for each delta.
    """
    return np.exp(-alpha * transaction_deltas)


def analyze_smurfing_velocity(
    timestamps: list[float],
    amounts: list[float],
    window: float,
    alpha: float = 0.005,
    attenuation_threshold: float = 0.85,
    amount_threshold: float = 10000.0,
) -> dict:
    """Isolate burst transaction clusters that violate temporal structural bounds.

    A smurfing operation distributes a large aggregate value across multiple
    sub-threshold transactions executed in rapid succession. This function
    identifies transaction pairs whose inter-arrival time produces an
    attenuation score above threshold AND whose amounts stay below the
    regulatory reporting threshold — the signature of structured layering.

    Parameters
    ----------
    timestamps : list[float]
        Transaction timestamps as Unix epoch seconds.
    amounts : list[float]
        Transaction amounts in settlement currency units.
    window : float
        Analysis window in seconds (unused in core logic, retained for
        interface compatibility with batch processing pipelines).
    alpha : float
        Decay rate for temporal attenuation (default 0.005).
    attenuation_threshold : float
        Minimum attenuation score to flag a delta as anomalous (default 0.85).
    amount_threshold : float
        Maximum single-transaction amount for smurfing detection (default 10000).

    Returns
    -------
    dict
        Contains 'calculated_deltas' (list of inter-transaction intervals),
        'attenuation_matrix' (list of attenuation scores), and
        'flagged_indices' (indices of anomalous burst edges).
    """
    ts = np.array(timestamps, dtype=np.float64)
    am = np.array(amounts, dtype=np.float64)
    deltas = np.diff(ts)

    decay_scores = calculate_temporal_attenuation(deltas, alpha=alpha)

    # Flag edges where:
    #   1. Attenuation score is high (transactions are nearly instantaneous)
    #   2. Amount is below the regulatory threshold (structured to evade reporting)
    anomalous_bursts = np.where(
        (decay_scores > attenuation_threshold) & (am[:-1] < amount_threshold)
    )[0]

    return {
        "calculated_deltas": deltas.tolist(),
        "attenuation_matrix": decay_scores.tolist(),
        "flagged_indices": anomalous_bursts.tolist(),
    }


if __name__ == "__main__":
    # Simulate a high-frequency peeling sequence:
    #   timestamps in seconds (Unix epoch), amounts below 10,000 EUR
    mock_ts = [1710000000.0, 1710000015.0, 1710000032.0, 1710000120.0]
    mock_am = [9500.0, 9600.0, 9400.0, 12000.0]
    result = analyze_smurfing_velocity(mock_ts, mock_am, 60.0)
    print("Temporal Security Insights:", result)
