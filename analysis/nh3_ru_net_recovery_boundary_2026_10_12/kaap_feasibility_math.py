"""Read-only feasibility/decision rules for a SAME-MASK mono-metal comparison.

These methods do NOT model a serial Fe+Ru multibed KAAP converter. Activity
factor alpha is a declared counterfactual to scale active Fe TOF at otherwise
unchanged frozen process states; its range is not an empirically calibrated
confidence interval.
"""
from __future__ import annotations
import math


def require_finite_positive(value, name):
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be positive and finite")
    return float(value)


def minimum_feasible_activity_multiplier(min_bed_volume_at_alpha1, bed_capacity):
    """For V(alpha)=V(1)/alpha and cap, alpha >= min(V(1))/cap."""
    v = require_finite_positive(min_bed_volume_at_alpha1, "min_bed_volume")
    cap = require_finite_positive(bed_capacity, "bed_capacity")
    return v / cap


def classify_feasibility(optimal_volume, bed_capacity):
    """A volume-cap pass is a model-filter, never a plant feasibility certificate."""
    return "within_frozen_volume_cap" if (math.isfinite(optimal_volume) and
            0 <= optimal_volume <= require_finite_positive(bed_capacity, "bed_capacity")) else "no_volume_feasible_state"


def find_fe_activity_cost_parity(cost_at_alpha, ru_reference, lowest_feasible_alpha,
                                 low=0.2, high=4.0, steps=48, tol=1e-10):
    """Fe activity alpha where Fe cost falls to Ru cost, if bracketed.

    Only examines states that satisfy the frozen bed cap. For alpha less
    than the capacity feasibility threshold there is no Fe comparator. If
    the first feasible Fe state is already cheaper than Ru, the boundary
    is a *feasibility onset*, not a cost-parity root.

    The function may be discontinuous at the first feasible state and when
    another frozen process state becomes optimal. We only label cost parity
    when the returned Fe cost is numerically close to Ru cost.
    """
    for v, name in ((ru_reference, "Ru reference"), (lowest_feasible_alpha, "Fe feasibility alpha"),
                    (low, "low"), (high, "high")):
        require_finite_positive(v, name)
    if not (low < high) or steps < 1 or not math.isfinite(tol) or tol <= 0:
        raise ValueError("Invalid bracket, search steps or tolerance")
    if lowest_feasible_alpha > high:
        return {"status": "Fe_volume_infeasible_over_range", "alpha": None}
    start = max(low, lowest_feasible_alpha * (1.0 + 1e-9))
    if start > high:
        return {"status": "Fe_volume_infeasible_over_range", "alpha": None}
    ca = cost_at_alpha(start)
    cb = cost_at_alpha(high)
    if not (math.isfinite(ca) and math.isfinite(cb)):
        raise ValueError("Cost callable must be finite at feasible bracket endpoints")
    if cb > ca + tol:
        raise ValueError("Fe cost should decrease with increasing effective activity")
    if ca <= ru_reference:
        return {"status": "Fe_wins_at_first_feasible_alpha", "alpha": None,
                "first_feasible_alpha": start}
    if cb > ru_reference:
        return {"status": "Ru_wins_through_upper_activity_bound", "alpha": None,
                "first_feasible_alpha": start}
    left, right = start, high
    for _ in range(steps):
        mid = (left + right) / 2.0
        c = cost_at_alpha(mid)
        if not math.isfinite(c):
            raise ValueError("Fe cost must be finite within feasible search bracket")
        if c > ru_reference:
            left = mid
        else:
            right = mid
    value = (left + right) / 2.0
    residual = cost_at_alpha(value) - ru_reference
    if abs(residual) > max(tol, 1e-7):
        return {"status": "discrete_state_switch_or_numerical_jump", "alpha": value,
                "gap_residual_USD_t": residual, "first_feasible_alpha": start}
    return {"status": "cost_parity", "alpha": value,
            "gap_residual_USD_t": residual, "first_feasible_alpha": start}
