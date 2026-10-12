"""Finite-plant cash-flow accounting for active-metal purchase, recovery and refining.

This module does NOT change the frozen kinetic/process equations. The investment
horizon is finite (25 years in NH3-FINAL-1.1), and each catalytic bed is purchased
at commissioning/replacement. Spent metal is collected at each replacement and,
optionally, at final plant closure. Refining fees occur on collection; saleable
metal proceeds arrive after a distinct settlement delay.

Every monetary coefficient is an explicit *scenario* until primary industrial
recycler quotations are obtained.
"""
from __future__ import annotations

import math
from dataclasses import dataclass


def discount_factor(rate: float, time_y: float) -> float:
    if not math.isfinite(rate) or rate < 0 or not math.isfinite(time_y) or time_y < 0:
        raise ValueError("discount rate and elapsed time must be nonnegative, finite")
    return math.exp(-time_y * math.log1p(rate))


def capital_recovery_factor(rate: float, years: float) -> float:
    if not math.isfinite(years) or years <= 0:
        raise ValueError("project years must be positive and finite")
    if not math.isfinite(rate) or rate < 0:
        raise ValueError("discount rate must be nonnegative and finite")
    if rate == 0:
        return 1.0 / years
    return rate / -math.expm1(-years * math.log1p(rate))


def lifecycle_dates(life_y: float, project_y: float, terminal_recovery: bool = True):
    """Return purchases and spent-catalyst collections in a finite project.

    A bed is bought at t=0 and when its life expires strictly before closure.
    The final partially used bed is collected at closure if requested. A
    collection at closure does not trigger a new purchase.
    """
    if not math.isfinite(life_y) or life_y <= 0 or not math.isfinite(project_y) or project_y <= 0:
        raise ValueError("life and project horizon must be positive and finite")
    purchases = []
    step = 0
    while step * life_y < project_y - 1e-10:
        purchases.append(step * life_y)
        step += 1
        if step > 10000:
            raise ValueError("Too many catalyst purchases for this project horizon")
    retirements = purchases[1:].copy()
    if terminal_recovery:
        retirements.append(project_y)
    return purchases, retirements


@dataclass(frozen=True)
class MetalCashflow:
    project_y: float
    catalyst_life_y: float
    discount_rate: float
    gross_recovery: float
    refining_yield: float = 1.0
    sale_price_fraction: float = 1.0
    processing_fee_USD_kg_collected: float = 0.0
    sale_delay_y: float = 0.0
    terminal_recovery: bool = True


def annualized_metal_multiplier(case: MetalCashflow, metal_price_USD_kg: float, legacy_life_y: float = 10.0) -> float:
    """Scale frozen metal term M*P/(legacy_life_y*annual_tonnes).

    Returned value accounts for ALL metal purchases, processing fees and metal
    sale proceeds over the finite plant project. A separate Fe calculation
    using its own 0%-recovery case is necessary for a like-for-like comparison.
    """
    if not math.isfinite(metal_price_USD_kg) or metal_price_USD_kg <= 0:
        raise ValueError("Metal price must be positive and finite")
    if not math.isfinite(legacy_life_y) or legacy_life_y <= 0:
        raise ValueError("Legacy catalyst life must be positive and finite")
    for name in ("gross_recovery", "refining_yield", "sale_price_fraction"):
        value = getattr(case, name)
        if not math.isfinite(value) or not 0 <= value <= 1:
            raise ValueError(f"{name} outside [0,1]")
    for name in ("processing_fee_USD_kg_collected", "sale_delay_y"):
        value = getattr(case, name)
        if not math.isfinite(value) or value < 0:
            raise ValueError(f"{name} must be finite and nonnegative")
    purchases, retirements = lifecycle_dates(case.catalyst_life_y, case.project_y, case.terminal_recovery)
    rate = case.discount_rate
    pv_purchases = sum(discount_factor(rate, t) for t in purchases)
    pv_collection = sum(discount_factor(rate, t) for t in retirements)
    pv_sale = sum(discount_factor(rate, t + case.sale_delay_y) for t in retirements)
    fee_ratio = case.processing_fee_USD_kg_collected / metal_price_USD_kg
    net_pv = (pv_purchases
              + case.gross_recovery * fee_ratio * pv_collection
              - case.gross_recovery * case.refining_yield * case.sale_price_fraction * pv_sale)
    if net_pv < -1e-10:
        raise AssertionError("Metal salvage PV unexpectedly exceeds total metal expenditure")
    multiplier = legacy_life_y * capital_recovery_factor(rate, case.project_y) * max(net_pv, 0.0)
    if not math.isfinite(multiplier):
        raise ArithmeticError("Non-finite lifecycle cash-flow multiplier")
    return multiplier
