"""Build a certified inner approximation to the Ru direct-activity/lifecycle target region.

No DFT and no frozen response-cache rebuild are performed. The calculation reuses
only process states that already appear in the fully reoptimized Ru metal-price
sweep (figures/composite/fig2/fig2_ru_price_sweep.csv).

For a fixed process state, a direct Ru activity multiplier alpha rescales required
bed volume exactly as V(alpha) = V(alpha=1) / alpha. Catalyst lifetime L and metal
recovery r enter the Ru replacement-cost term exactly through an effective metal
price

    P_eff = P_Ru * (1-r) * (10 y / L).

Fresh/recycle compression, refrigeration and compressor CAPEX are state properties.
Reactor-volume and vessel-pressure terms are recomputed from the frozen FINAL-1.1
cost correlations at the rescaled V. Minimizing over the 53 states present in the
price sweep therefore gives an upper bound on the true fully reoptimized Ru cost.
Consequently, every point declared cost-feasible here is certified cost-feasible
in the full 14,136-state model for the specified direct, state-independent activity
multiplier. This is a backward-target calculation, not proof that the same multiplier
is reachable on the strict descriptor-scaling manifold: the scaling-derived activity
gain is process-state dependent. Points declared infeasible may simply require a
state not in this subset.

The subset reproduces both exact one-dimensional parity anchors:
  alpha=1       -> P_eff* ~= 163.763 USD/kg
  alpha=201.223 -> P_eff* ~= canonical Ru price 53,852.5 USD/kg

Outputs:
  activity_lifecycle_certified_boundary.csv
  activity_lifecycle_target_keypoints.csv
  activity_lifecycle_certified_keypoint.json
"""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
PRICE_SWEEP = ROOT / "figures/composite/fig2/fig2_ru_price_sweep.csv"
RUN = ROOT / "provenance/nh3_final_1_1/source_harness/outputs/nh3_final_20260905T134204Z"
CFG = yaml.safe_load((RUN / "manifest_resolved.yaml").read_text(encoding="utf-8"))
RES = json.loads((RUN / "results.json").read_text(encoding="utf-8"))

FE_COST = float(RES["deterministic"]["metals"]["Fe"]["feasible"]["total_cost"])
P_RU = 53852.5
ALPHA_STAR = float(RES["backward_reachability"]["Ru_activity_break_even_multiplier"])
G673 = float(RES["backward_reachability"]["Ru_scaling_max_gain_673K"])
GALL = float(RES["backward_reachability"]["Ru_scaling_max_gain_all_states"])

econ = CFG["economics"]
pc = econ["pressure_capex"]
vessel_cfg = pc["vessel"]
CRF = econ["discount_rate"] * (1 + econ["discount_rate"]) ** econ["plant_life_y"] / (
    (1 + econ["discount_rate"]) ** econ["plant_life_y"] - 1
)
ANNUAL_T = CFG["plant"]["production_tpd"] * 365 * CFG["plant"]["capacity_factor"]
PCIR = pc["cost_index_current"] / pc["cost_index_base"]


def read_rows(path: Path):
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def q(value: float, ndigits: int = 9) -> float:
    """Quantize derived outputs so the audit is byte-stable across platforms."""
    y = round(float(value), ndigits)
    return 0.0 if abs(y) < 10 ** (-ndigits) else y


raw = read_rows(PRICE_SWEEP)
states = {}
for row in raw:
    key = (float(row["T_C"]), float(row["P_bar"]), float(row["Tsep_C"]))
    states.setdefault(key, row)
states = list(states.values())

k_values = [
    float(r["metal_cost"]) / (float(r["V_m3"]) * float(r["price_USD_kg"]))
    for r in states
]
K_METAL = sum(k_values) / len(k_values)
assert max(abs(k - K_METAL) for k in k_values) < 1e-15


def reactor_cost(V: float) -> float:
    raw_usd = econ["reactor_fixed_USD"] + econ["reactor_variable_USD"] * (
        V / econ["reactor_reference_m3"]
    ) ** econ["reactor_exponent"]
    return raw_usd * CRF / ANNUAL_T


def vessel_pressure_premium(V: float, P_bar: float) -> float:
    Vc = max(V, float(vessel_cfg["A_min_m3"]))
    L_over_D = float(vessel_cfg["L_over_D"])
    D = (4 * Vc / (math.pi * L_over_D)) ** (1 / 3)
    S_E = float(vessel_cfg["allowable_stress_x_weld_eff_bar"])
    CA = float(vessel_cfg["corrosion_allowance_m"])
    tmin = float(vessel_cfg["min_thickness_m"])
    t = P_bar * D / (2 * (S_E - 0.6 * P_bar)) + CA
    Fp = max(t / tmin, 1.0)
    K0, K1, K2 = map(float, vessel_cfg["K"])
    lv = math.log10(Vc)
    Cp0 = 10 ** (K0 + K1 * lv + K2 * lv * lv)
    delta_cbm = Cp0 * float(vessel_cfg["B2"]) * float(vessel_cfg["Fm"]) * (Fp - 1) * PCIR
    return delta_cbm * CRF / ANNUAL_T


def state_cost(row, alpha: float, effective_price: float):
    V = float(row["V_m3"]) / alpha
    total = (
        float(row["fresh_comp"])
        + float(row["recycle_comp"])
        + float(row["refrigeration"])
        + float(row["compressor_capex"])
        + reactor_cost(V)
        + vessel_pressure_premium(V, float(row["P_bar"]))
        + K_METAL * V * effective_price
    )
    return total, V


def subset_optimum(alpha: float, effective_price: float):
    best = None
    for row in states:
        cost, V = state_cost(row, alpha, effective_price)
        if best is None or cost < best["cost"]:
            best = {
                "cost": cost,
                "V_m3": V,
                "T_C": float(row["T_C"]),
                "P_bar": float(row["P_bar"]),
                "Tsep_C": float(row["Tsep_C"]),
            }
    return best


def parity_price(alpha: float):
    lo, hi = 0.0, 60000.0
    if subset_optimum(alpha, lo)["cost"] > FE_COST:
        return None
    while subset_optimum(alpha, hi)["cost"] <= FE_COST:
        hi *= 2
        if hi > 1e8:
            raise RuntimeError("failed to bracket parity price")
    for _ in range(100):
        mid = 0.5 * (lo + hi)
        if subset_optimum(alpha, mid)["cost"] <= FE_COST:
            lo = mid
        else:
            hi = mid
    opt = subset_optimum(alpha, lo)
    return lo, opt


def parity_alpha(effective_price: float):
    """Smallest direct activity multiplier that reaches Fe parity in the state subset."""
    lo, hi = 0.05, 10.0
    if subset_optimum(lo, effective_price)["cost"] <= FE_COST:
        return lo, subset_optimum(lo, effective_price)
    while subset_optimum(hi, effective_price)["cost"] > FE_COST:
        hi *= 2
        if hi > 1e6:
            raise RuntimeError("failed to bracket parity activity")
    for _ in range(100):
        mid = 0.5 * (lo + hi)
        if subset_optimum(mid, effective_price)["cost"] <= FE_COST:
            hi = mid
        else:
            lo = mid
    return hi, subset_optimum(hi, effective_price)


# Axis-anchor validation.
p1, _ = parity_price(1.0)
assert abs(p1 - 163.76330261666772) < 1e-3
pa, _ = parity_price(ALPHA_STAR)
assert abs(pa - P_RU) < 1e-2

alpha_grid = [
    1.0,
    G673,
    1.25,
    1.5,
    1.75,
    2.0,
    2.25,
    GALL,
    3.0,
    5.0,
    10.0,
    50.0,
    100.0,
    ALPHA_STAR,
]

rows = []
for alpha in alpha_grid:
    pcrit, opt = parity_price(alpha)
    rec10 = 1 - pcrit / P_RU
    rec15 = 1 - pcrit / P_RU * 1.5
    rec20 = 1 - pcrit / P_RU * 2.0
    rows.append(
        {
            "alpha": q(alpha, 12),
            "certified_parity_effective_Ru_price_USD_kg": q(pcrit, 6),
            "boundary_T_C": int(round(opt["T_C"])),
            "boundary_P_bar": int(round(opt["P_bar"])),
            "boundary_Tsep_C": int(round(opt["Tsep_C"])),
            "boundary_V_m3": q(opt["V_m3"], 9),
            "required_recovery_at_10y": q(rec10, 9),
            "required_recovery_at_15y": q(rec15, 9),
            "required_recovery_at_20y": q(rec20, 9),
        }
    )

with (HERE / "activity_lifecycle_certified_boundary.csv").open("w", encoding="utf-8", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)


# Representative backward targets. These are requirements in direct-alpha space;
# strict scaling-manifold reachability is a separate calculation.
target_rows = []
for life_i, recovery_i in ((10.0, 0.99), (15.0, 0.99), (20.0, 0.99), (20.0, 0.98)):
    peff_i = P_RU * (1 - recovery_i) * (10.0 / life_i)
    alpha_i, opt_i = parity_alpha(peff_i)
    target_rows.append(
        {
            "catalyst_life_y": int(round(life_i)),
            "Ru_recovery_fraction": q(recovery_i, 6),
            "effective_Ru_price_USD_kg": q(peff_i, 6),
            "certified_upper_bound_required_direct_activity_multiplier": q(alpha_i, 9),
            "boundary_T_C": int(round(opt_i["T_C"])),
            "boundary_P_bar": int(round(opt_i["P_bar"])),
            "boundary_Tsep_C": int(round(opt_i["Tsep_C"])),
            "boundary_V_m3": q(opt_i["V_m3"], 9),
        }
    )

with (HERE / "activity_lifecycle_target_keypoints.csv").open("w", encoding="utf-8", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(target_rows[0]))
    w.writeheader()
    w.writerows(target_rows)

# Conditional cost-feasibility point using the numerical all-state scaling gain maximum only as a comparison value.
life_y = 20.0
recovery = 0.98
peff = P_RU * (1 - recovery) * (10.0 / life_y)
key = subset_optimum(GALL, peff)
pcrit_gall, boundary_gall = parity_price(GALL)
record = {
    "schema": "nh3-backward-direct-activity-lifecycle-target-v2",
    "method": "minimize reconstructed FINAL-1.1 cost over the 53 distinct process states already present in the fully reoptimized Ru price sweep; this gives a conservative upper bound on the direct activity multiplier required for parity at each lifecycle condition",
    "no_new_DFT": True,
    "frozen_sources_modified": False,
    "Fe_cost_USD_t": q(FE_COST, 9),
    "canonical_Ru_price_USD_kg": q(P_RU, 6),
    "reference_direct_activity_multiplier_equal_to_all_state_scaling_gain_maximum": q(GALL, 12),
    "conditional_parity_effective_price_at_reference_multiplier_USD_kg": q(pcrit_gall, 6),
    "conditional_required_recovery_at_reference_multiplier_and_20y": q(1 - pcrit_gall / P_RU * 2.0, 9),
    "reachability_caution": "The 2.524565 value is the maximum scaling-derived gain at any process state, not a uniform multiplier proven reachable at the cost-optimal state. The explicit point below certifies cost feasibility only under the direct-multiplier parameterization; strict scaling-consistent joint reachability requires a separate E_N x lifecycle sweep.",
    "explicit_point": {
        "activity_multiplier": q(GALL, 12),
        "catalyst_life_y": int(round(life_y)),
        "metal_recovery_fraction": q(recovery, 6),
        "effective_Ru_price_USD_kg": q(peff, 6),
        "best_subset_cost_USD_t": q(key["cost"], 9),
        "margin_vs_Fe_USD_t": q(key["cost"] - FE_COST, 9),
        "state": {
            "T_C": int(round(key["T_C"])),
            "P_bar": int(round(key["P_bar"])),
            "Tsep_C": int(round(key["Tsep_C"])),
            "V_m3": q(key["V_m3"], 9),
        },
        "certified_cost_feasible_given_direct_activity_multiplier": key["cost"] <= FE_COST,
        "strict_scaling_reachability_established": False,
    },
    "boundary_state_at_reference_multiplier": {
        "cost": q(boundary_gall["cost"], 9),
        "V_m3": q(boundary_gall["V_m3"], 9),
        "T_C": int(round(boundary_gall["T_C"])),
        "P_bar": int(round(boundary_gall["P_bar"])),
        "Tsep_C": int(round(boundary_gall["Tsep_C"])),
    },
}
assert record["explicit_point"]["certified_cost_feasible_given_direct_activity_multiplier"]
(HERE / "activity_lifecycle_certified_keypoint.json").write_text(
    json.dumps(record, indent=2), encoding="utf-8"
)

print(json.dumps(record, indent=2))
