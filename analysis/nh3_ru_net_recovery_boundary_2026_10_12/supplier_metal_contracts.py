"""Commercial ownership overlays for Ru catalyst-metal inventory.

The following model is a transparent counterfactual, NOT an industrial quote.
It discounts all operator cash flows at the frozen NH3 plant hurdle rate
(12% over 25 years). It models metal provided by a counterparty: the operator
pays rental/service fees, makes up metal losses, and may post refundable
collateral. The operator never purchases/sells the supplier-owned principal.
Customer-owned pool balances MUST use the existing owned-metal DCF instead.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from lifecycle_cashflow import (annualized_metal_multiplier, capital_recovery_factor,
                                discount_factor, lifecycle_dates, MetalCashflow)


@dataclass(frozen=True)
class SupplierMetalTerms:
    """Value fractions are relative to the purchase price of 1 kg of Ru metal.

    annual_fee_fraction: contract rent / P each year, payable year-end.
    cycle_fee_fraction: contract handling fee / P at each new catalyst loading.
    deposit_fraction: refundable collateral paid at t=0; returned at closure.
    deposit_refund_fraction: independent of metal-loss settlement (avoid double count).
    gross_recovery × refining_yield: metal returned in fine-metal equivalents.
    loss_settlement_price_fraction: fraction of metal price owed on shortfall.
    processing_fee_USD_kg_collected: applied to gross collected Ru metal mass.
    charge_delay_years: payment delay on metal shortfall, not a resale credit.
    """
    project_y: float
    catalyst_life_y: float
    project_discount_rate: float
    gross_recovery: float
    refining_yield: float = 1.0
    annual_fee_fraction: float = 0.0
    cycle_fee_fraction: float = 0.0
    deposit_fraction: float = 0.0
    deposit_refund_fraction: float = 1.0
    loss_settlement_price_fraction: float = 1.0
    processing_fee_USD_kg_collected: float = 0.0
    charge_delay_years: float = 0.0
    terminal_return: bool = True


def supplier_metal_multiplier(case: SupplierMetalTerms, metal_price_USD_kg: float,
                              legacy_life_y: float = 10.0) -> float:
    """Convert supplier-metal cash flows to the frozen metal-cost normalizer.

    The frozen vector ru_metal is M × P /(legacy_life × annual_output),
    so multiply it by legacy_life × CRF × PV_per_initial_metal_dollar.
    All operator costs discounted with one project rate, rather than changing
    discount rates between catalyst choices.
    """
    if not math.isfinite(metal_price_USD_kg) or metal_price_USD_kg <= 0:
        raise ValueError("metal price must be positive")
    if not math.isfinite(legacy_life_y) or legacy_life_y <= 0:
        raise ValueError("legacy life must be positive")
    for name in ("gross_recovery", "refining_yield", "deposit_fraction",
                 "deposit_refund_fraction", "loss_settlement_price_fraction"):
        x = getattr(case, name)
        if not math.isfinite(x) or not 0 <= x <= 1:
            raise ValueError(f"{name} must lie in [0,1]")
    for name in ("annual_fee_fraction", "cycle_fee_fraction",
                 "processing_fee_USD_kg_collected", "charge_delay_years"):
        x = getattr(case, name)
        if not math.isfinite(x) or x < 0:
            raise ValueError(f"{name} must be finite and nonnegative")

    buys, retirements = lifecycle_dates(case.catalyst_life_y, case.project_y,
                                         terminal_recovery=True)
    rate = case.project_discount_rate
    df = lambda t: discount_factor(rate, t)
    n_years = int(round(case.project_y))
    # Year-end invoice with a prorated final invoice if project life noninteger.
    full_years = int(math.floor(case.project_y + 1e-12))
    pv_annual_fees = sum(df(float(k)) for k in range(1, full_years + 1))
    if case.project_y > full_years + 1e-12:
        pv_annual_fees += (case.project_y - full_years) * df(case.project_y)
    pv_cycle_fees = sum(df(t) for t in buys)
    pv_contract = (case.annual_fee_fraction * pv_annual_fees
                   + case.cycle_fee_fraction * pv_cycle_fees)
    # The metal collateral is NOT an asset purchase; full refund yields only
    # an opportunity-cost charge and should not settle shortage twice.
    pv_deposit = (case.deposit_fraction
                  - case.deposit_fraction * case.deposit_refund_fraction
                  * df(case.project_y))
    fine_metal_return = case.gross_recovery * case.refining_yield
    fee_share = case.processing_fee_USD_kg_collected / metal_price_USD_kg
    pv_return_fees = 0.0
    for time in retirements:
        terminal = abs(time - case.project_y) <= 1e-10
        gross_r = case.gross_recovery if (not terminal or case.terminal_return) else 0.0
        fine_r = gross_r * case.refining_yield
        loss_r = 1.0 - fine_r
        pv_return_fees += gross_r * fee_share * df(time)
        pv_return_fees += (loss_r * case.loss_settlement_price_fraction
                           * df(time + case.charge_delay_years))
    pv = pv_contract + pv_deposit + pv_return_fees
    if not math.isfinite(pv) or pv < -1e-12:
        raise ArithmeticError("Nonfinite or negative contract metal present value")
    return legacy_life_y * capital_recovery_factor(rate, case.project_y) * max(0.0, pv)


def owned_metal_multiplier(*, project_y: float, catalyst_life_y: float,
                           discount_rate: float, metal_price_USD_kg: float,
                           gross_recovery: float, refining_yield: float = 1.0,
                           payout_fraction: float = 1.0,
                           processing_fee_USD_kg_collected: float = 0.0,
                           sale_delay_y: float = 0.0,
                           legacy_life_y: float = 10.0) -> float:
    """Owned/buyback metal principal: use original DCF, never supplier model."""
    return annualized_metal_multiplier(
        MetalCashflow(
            project_y=project_y, catalyst_life_y=catalyst_life_y,
            discount_rate=discount_rate, gross_recovery=gross_recovery,
            refining_yield=refining_yield, sale_price_fraction=payout_fraction,
            processing_fee_USD_kg_collected=processing_fee_USD_kg_collected,
            sale_delay_y=sale_delay_y),
        metal_price_USD_kg, legacy_life_y)
