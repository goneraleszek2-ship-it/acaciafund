#!/usr/bin/env python3
"""Hawkes self-exciting process intensity estimator for LOB dynamics.

Computes the conditional intensity function λ(t) using the standard
univariate Hawkes formulation with exponential kernel. Supports
simulation and real-time estimation of market regime branching ratios.
"""

import numpy as np


def compute_hawkes_intensity(
    t: float,
    event_history: np.ndarray,
    mu: float = 0.1,
    alpha: float = 0.4,
    beta: float = 0.6,
) -> float:
    """Evaluate the conditional stochastic intensity at time t.

    The univariate Hawkes intensity is:
        λ(t) = μ + Σ_{t_i < t} α × exp(-β × (t - t_i))

    where:
      μ     — baseline exogenous intensity (events per unit time)
      α     — excitation amplitude (instantaneous intensity jump per event)
      β     — exponential decay rate (s⁻¹), reciprocal is excitation timescale
      t_i   — historical event times

    Parameters
    ----------
    t : float
        Evaluation time point.
    event_history : np.ndarray
        Sorted array of historical event timestamps (must satisfy t_i < t
        for all t_i in the array).
    mu : float, optional
        Baseline intensity (default 0.1).
    alpha : float, optional
        Excitation amplitude (default 0.4).
    beta : float, optional
        Exponential decay rate (default 0.6).

    Returns
    -------
    float
        Conditional intensity λ(t) at the evaluation point.
    """
    past_events = event_history[event_history < t]
    if len(past_events) == 0:
        return mu
    excitation = np.sum(np.exp(-beta * (t - past_events)))
    return mu + alpha * excitation


def compute_branching_ratio(alpha: float, beta: float) -> float:
    """Compute the branching ratio η = α / β.

    The branching ratio controls the stability regime:
      η < 1 → sub-critical (mean-reverting, finite clusters)
      η = 1 → critical (unit-root non-stationary)
      η > 1 → super-critical (explosive cascade)

    Parameters
    ----------
    alpha : float
        Excitation amplitude.
    beta : float
        Decay rate.

    Returns
    -------
    float
        Branching ratio.
    """
    if beta <= 0:
        return float("inf")
    return alpha / beta


def classify_regime(eta: float) -> str:
    """Classify market regime from estimated branching ratio.

    Regime mapping:
      η ≤ 0.4     → quiescent
      0.4 < η ≤ 0.7 → active
      0.7 < η ≤ 0.95 → fragile
      0.95 < η < 1.0 → pre-critical
      η ≥ 1.0     → cascade (flash crash)
    """
    if eta <= 0.4:
        return "quiescent"
    elif eta <= 0.7:
        return "active"
    elif eta <= 0.95:
        return "fragile"
    elif eta < 1.0:
        return "pre-critical"
    return "cascade"


def run_intensity_simulation(events: list[float], eval_steps: int) -> list[float]:
    """Calculate order-flow clustering intensity traces over a timeline.

    Parameters
    ----------
    events : list[float]
        Historical event arrival timestamps.
    eval_steps : int
        Number of evenly spaced evaluation points along the timeline.

    Returns
    -------
    list[float]
        Intensity values λ(t) at each evaluation point.
    """
    history = np.array(events, dtype=np.float64)
    timeline = np.linspace(history[0], history[-1] + 10.0, eval_steps)

    mu, alpha, beta = 0.1, 0.4, 0.6
    return [
        compute_hawkes_intensity(tick, history, mu, alpha, beta)
        for tick in timeline
    ]


if __name__ == "__main__":
    # Mock HFT limit order book arrival timestamps (seconds)
    order_arrivals = [1.12, 1.15, 1.18, 2.45, 2.48, 5.10]
    intensities = run_intensity_simulation(order_arrivals, eval_steps=5)
    eta = compute_branching_ratio(0.4, 0.6)
    regime = classify_regime(eta)

    print("Computed Microstructure Intensity Vector:",
          [round(x, 4) for x in intensities])
    print(f"Branching Ratio η: {eta:.3f} — Regime: {regime}")
