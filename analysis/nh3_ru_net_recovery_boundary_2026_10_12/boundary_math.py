"""Pure helpers for the Ru/C net-recovery decision boundary.

q = physical Ru recovery fraction * net monetary realization per recovered Ru unit.
The credited metal purchase price in the existing frozen 10-year replacement-cost approximation
is p_eff = p_Ru * (1-q) / u.  No new kinetic or process parameter is fitted here.
"""
from __future__ import annotations

import math
from typing import Callable


def effective_credit(recovery: float, net_realization: float) -> float:
    """Fraction of the original Ru metal value that is actually credited."""
    for name, x in (("recovery", recovery), ("net_realization", net_realization)):
        if not math.isfinite(x) or not 0.0 <= x <= 1.0:
            raise ValueError(f"{name} must be finite and within [0,1], got {x!r}")
    return recovery * net_realization


def same_loop_gap(ru_cost: float, fe_same_loop_cost: float) -> float:
    """Positive means Fe cheaper in that very same loop; never mix loop baselines."""
    if not math.isfinite(ru_cost) or not math.isfinite(fe_same_loop_cost):
        raise ValueError("Costs must be finite")
    return ru_cost - fe_same_loop_cost


def threshold_credit(cost_at_credit: Callable[[float], float], fe_reference: float, *,
                     iterations: int = 48, tol: float = 1e-10) -> float | None:
    """Smallest effective credited fraction q in [0,1] achieving cost <= Fe.

    Returns 0 if already competitive without recovery; None if unattainable even at q=1.
    Requires a nonincreasing globally reoptimized Ru cost function of q.  Binary
    search handles discontinuous changes of the optimal process state.
    """
    if not math.isfinite(fe_reference) or iterations < 1 or tol <= 0:
        raise ValueError("Invalid reference, iterations or tolerance")
    c0, c1 = cost_at_credit(0.0), cost_at_credit(1.0)
    if math.isnan(c0) or math.isnan(c1) or c1 > c0 + tol:
        raise ValueError("Ru cost must be nonincreasing with increased net credit")
    if c0 <= fe_reference + tol:
        return 0.0
    if c1 > fe_reference + tol:
        return None
    lo, hi = 0.0, 1.0
    for _ in range(iterations):
        mid = (lo + hi) / 2.0
        if cost_at_credit(mid) <= fe_reference:
            hi = mid
        else:
            lo = mid
    return hi
