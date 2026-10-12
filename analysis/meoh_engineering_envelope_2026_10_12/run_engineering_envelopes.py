#!/usr/bin/env python3
"""Unfrozen, reference-normalized engineering-cap sensitivity for joint MeOH m,p.

This simultaneously reoptimizes catalyst loading and purge under illustrative
caps on (1) catalyst inventory, (2) reactor inlet molar throughput, and
(3) recycle compressor power. Each cap is in *multiples of the published
one-step-loop reference*, not a validated equipment design limit.

The original joint optimizer assumes a fixed 1.5-bar recycle-loop pressure
drop at every catalyst and scale. Power constraints inherit that approximation;
a physical Ergun pressure-drop calculation is NOT possible without bed geometry
and catalyst properties. Frozen S5 and the prior unfrozen 310-entry results
are never modified.
"""
from __future__ import annotations

import argparse
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "analysis/field_robustness_2026_10_12"))
import joint_inventory_purge as J  # noqa: E402

G = J.G
M = G.M
# All values already used by the published-process-anchored cost model.
ANCHORS = {
    "catalyst_inventory_t": float(M.SOURCE_CAT_T),            # 6 x 478.13 t
    "reactor_inlet_kmol_h": float(M.REF_REACTOR_IN_KMOL_H),
    "recycle_compressor_MW": float(M.REF_POWERS[2]),
    "recycle_kmol_h": float(M.SOURCE_RECYCLE_KMOL_H),
    "reactor_pressure_bar": float(M.REF_PRESSURE_BAR),
    "assumed_loop_pressure_drop_bar": float(M.LOOP_DP_BAR),
}
if not all(ANCHORS[k] > 0 for k in ("catalyst_inventory_t",
       "reactor_inlet_kmol_h", "recycle_compressor_MW")):
    raise AssertionError("The reference design normalization must be positive")

# Caps are *sensitivity choices*, NOT industrial maximums.
CAPS = {
    "uncapped": (None, None, None),
    "anchor_1x": (1., 1., 1.),
    "anchor_2x": (2., 2., 2.),
    "anchor_4x": (4., 4., 4.),
    "inventory_2x": (2., None, None),
    "reactor_inlet_2x": (None, 2., None),
    "recycle_power_2x": (None, None, 2.),
}
LOADING_MAX = (10., 25.)
LOADING_GRID = (*J.M_GRID, 15., 20., 25.)
INLETS = J.LIMITS  # source-dependent loop inlet compositions and an open baseline

METRICS = ("cost_eur_t", "nonreactive_fraction", "catalyst_t",
           "co2_hyd_approach", "P_rec_MW", "recycle_kmol_h")


def extract(obj, n):
    data = {k: np.broadcast_to(np.asarray(obj[k], dtype=float), (n,)).copy()
            for k in METRICS}
    loop = obj["loop"]
    data["reactor_inlet_kmol_h"] = np.broadcast_to(
        np.asarray(loop["reactor_in"], dtype=float) *
        M.PROD_KMOL_H * M.RECYCLE_FLOW_CORRECTION, (n,)).copy()
    return data


def evaluate_grid(c):
    grid = J.GRID
    try:
        return extract(G.cost(c, purge=grid, x_co="recycled_central",
                              STY_per_g_cat=c["STY"]), len(grid))
    except (ValueError, FloatingPointError, OverflowError):
        data = {k: np.full(len(grid), np.nan, dtype=float)
                for k in (*METRICS, "reactor_inlet_kmol_h")}
        for i, purge in enumerate(grid):
            try:
                obj = G.cost(c, purge=float(purge), x_co="recycled_central",
                             STY_per_g_cat=c["STY"])
                record = extract(obj, 1)
                for k, value in record.items():
                    data[k][i] = float(value[0])
            except (ValueError, FloatingPointError, OverflowError):
                continue
        return data


def feasible_mask(e, inlet_limit, caps):
    """A cap must hold AT THE OPTIMUM; reoptimize within all valid m,p states."""
    cost = e["cost_eur_t"]
    ok = (np.isfinite(cost) & (cost > 0) &
          np.isfinite(e["co2_hyd_approach"]) &
          (e["co2_hyd_approach"] <= 1. + J.TOL) &
          np.isfinite(e["catalyst_t"]) & (e["catalyst_t"] > 0) &
          np.isfinite(e["reactor_inlet_kmol_h"]) &
          (e["reactor_inlet_kmol_h"] > 0) &
          np.isfinite(e["P_rec_MW"]) & (e["P_rec_MW"] >= 0))
    if inlet_limit is not None:
        ok &= (np.isfinite(e["nonreactive_fraction"]) &
               (e["nonreactive_fraction"] <= inlet_limit + 1e-12))
    inventory_multiple, inlet_multiple, power_multiple = caps
    if inventory_multiple is not None:
        ok &= e["catalyst_t"] <= inventory_multiple * ANCHORS["catalyst_inventory_t"] + 1e-9
    if inlet_multiple is not None:
        ok &= e["reactor_inlet_kmol_h"] <= inlet_multiple * ANCHORS["reactor_inlet_kmol_h"] + 1e-9
    if power_multiple is not None:
        ok &= e["P_rec_MW"] <= power_multiple * ANCHORS["recycle_compressor_MW"] + 1e-9
    return ok


def empty(row, max_m, inlet, case, xeq, roots):
    return {
        "row_id": int(row.row_id), "group": row.group, "doi": row.doi,
        "catalyst": row.catalyst, "max_m": int(max_m),
        "inlet": inlet, "cap": case, "cost": np.nan, "m": np.nan,
        "purge": np.nan, "inventory_ratio": np.nan, "inlet_flow_ratio": np.nan,
        "recycle_power_ratio": np.nan, "recycle_flow_ratio": np.nan,
        "nonreactive": np.nan, "x_eq_feed": xeq, "x_eq_roots": roots,
        "above_feed_eq": bool(float(row.X) >= xeq * (1 - 1e-10)),
        "selection_at_m_max": False,
    }


def optimize(row):
    """Evaluate physics only once for all inlet/cap/m_max combinations."""
    x0 = float(row.X)
    sty0 = float(row.STY)
    xeq, roots = J.feed_eq(float(row.h2_co2), float(row.y_co2),
                           float(row.T_C), float(row.P_bar))
    scenarios = [(max_m, inlet, case)
                 for max_m in LOADING_MAX
                 for inlet in INLETS
                 for case in CAPS]
    best = {s: empty(row, *s, xeq, roots) for s in scenarios}
    # J.states stops at m=10; extend with the same calibrated surrogate to m=25.
    if x0 >= xeq * (1. - 1e-10):
        states = [(1., x0, "above_feed_eq_only_measured")]
    else:
        ratio = x0 / xeq
        states = [(float(m), float(x0 if m == 1 else
                   xeq * (1. - (1. - ratio) ** m)), "surrogate")
                  for m in LOADING_GRID]
    for m, x, mode in states:
        if not (0 < x < 1):
            continue
        sty = sty0 * x / (x0 * m)
        c = {"X": x, "SMeOH": float(row.SMeOH), "SCH4": float(row.SCH4),
             "SCO": float(row.SCO), "STY": sty, "P_bar": float(row.P_bar),
             "h2_co2": float(row.h2_co2), "T_C": float(row.T_C)}
        with np.errstate(all="ignore"), warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            e = evaluate_grid(c)
        # Efficient: feasibility and argmin are shared over the four inlet
        # conditions and seven equipment envelopes; m=25 includes m=10.
        for inlet, inlet_max in INLETS.items():
            for cap, thresholds in CAPS.items():
                ok = feasible_mask(e, inlet_max, thresholds)
                if not ok.any():
                    continue
                ix = int(np.argmin(np.where(ok, e["cost_eur_t"], np.inf)))
                v = float(e["cost_eur_t"][ix])
                for max_m in LOADING_MAX:
                    if m > max_m:
                        continue
                    key = (max_m, inlet, cap)
                    if np.isfinite(best[key]["cost"]) and v >= best[key]["cost"] - 1e-9:
                        continue
                    b = best[key]
                    b.update(
                        cost=v, m=m, purge=float(J.GRID[ix]),
                        inventory_ratio=float(e["catalyst_t"][ix] / ANCHORS["catalyst_inventory_t"]),
                        inlet_flow_ratio=float(e["reactor_inlet_kmol_h"][ix] / ANCHORS["reactor_inlet_kmol_h"]),
                        recycle_power_ratio=float(e["P_rec_MW"][ix] / ANCHORS["recycle_compressor_MW"]),
                        recycle_flow_ratio=float(e["recycle_kmol_h"][ix] / ANCHORS["recycle_kmol_h"]),
                        nonreactive=float(e["nonreactive_fraction"][ix]),
                        selection_at_m_max=(abs(m - max_m) < 1e-12),
                    )
    return list(best.values())


def make_shard(args):
    base = J.candidates()
    if args.smoke is not None:
        base = base.head(args.smoke)
    chosen = base[base.row_id % args.count == args.index]
    if chosen.empty:
        raise ValueError("Empty shard")
    rows = []
    for i, row in enumerate(chosen.itertuples(index=False), 1):
        rows.extend(optimize(row))
        if i % 10 == 0 or i == len(chosen):
            print(f"shard={args.index} processed {i}/{len(chosen)}", flush=True)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(args.out, index=False, float_format="%.12g")
    print(f"WROTE {args.out}: candidates={len(chosen)} scenario_rows={len(rows)}")


def validate_output(baseline, data, smoke=False):
    identity = ["row_id", "max_m", "inlet", "cap"]
    if data[identity].isna().any().any() or data.duplicated(identity).any():
        raise AssertionError("Missing or repeated candidate/scenario record")
    observed = set(map(int, data.row_id.unique()))
    expected = set(map(int, baseline.row_id))
    if observed != expected:
        raise AssertionError("Shards do not cover the complete expected candidate ID set")
    expected_rows = len(expected) * len(LOADING_MAX) * len(INLETS) * len(CAPS)
    if len(data) != expected_rows:
        raise AssertionError(f"Scenario rows {len(data)} != {expected_rows}")
    if (data.groupby("row_id").size() != len(LOADING_MAX)*len(INLETS)*len(CAPS)).any():
        raise AssertionError("Some candidate scenarios are missing")
    for _, r in data.loc[np.isfinite(data.cost)].iterrows():
        cap = CAPS[r.cap]
        limit = INLETS[r.inlet]
        if r.m > r.max_m + 1e-9:
            raise AssertionError("Chosen loading multiplier above allowed cap")
        if limit is not None and r.nonreactive > limit + 1e-9:
            raise AssertionError("Chosen inlet exceeds source-specific fraction envelope")
        for measured, choice in zip(("inventory_ratio", "inlet_flow_ratio", "recycle_power_ratio"), cap):
            if choice is not None and r[measured] > choice + 1e-8:
                raise AssertionError(f"{r.cap} violates {measured}")
    if not smoke:
        prior = pd.read_csv(ROOT / "analysis/field_robustness_2026_10_12/results/joint_candidates.csv")
        old = prior.set_index("row_id")
        new = data[(data.max_m == 10) & (data.cap == "uncapped")]
        for inlet in INLETS:
            k = new[new.inlet == inlet].set_index("row_id")["cost"].sort_index()
            prev = old.loc[k.index, inlet + "_cost"]
            if not np.allclose(k, prev, rtol=1e-8, atol=2e-5, equal_nan=True):
                bad = k.index[~np.isclose(k, prev, rtol=1e-8, atol=2e-5, equal_nan=True)]
                raise AssertionError(f"Reference baseline does not reproduce the prior 310-point scan: {inlet}; rows {list(bad[:10])}")
    return True


def aggregate_runs(args):
    files = sorted(args.input_dir.glob("shard_*.csv"))
    if not files:
        raise FileNotFoundError(f"No shard_*.csv in {args.input_dir}")
    data = pd.concat([pd.read_csv(path) for path in files], ignore_index=True)
    base = J.candidates()
    validate_output(base, data)
    args.output.mkdir(parents=True, exist_ok=True)
    results = {}
    gm_parts = []
    all_m_groups = {}
    for max_m in LOADING_MAX:
        for cap in CAPS:
            grouped = {}
            entry = {}
            for inlet in INLETS:
                sel = data[(data.max_m == max_m) & (data.cap == cap) &
                           (data.inlet == inlet)]
                costs = sel.set_index("row_id")["cost"]
                f = base.copy()
                f["engineering_cost"] = f.row_id.map(costs)
                g, s = J.metrics(f, "engineering_cost",
                                 label=f"max_m_{int(max_m)}:{cap}:{inlet}")
                if not g.empty:
                    g = g.assign(max_m=int(max_m), cap=cap, inlet=inlet)
                    gm_parts.append(g)
                grouped[inlet] = g.set_index("group") if not g.empty else pd.DataFrame()
                # A loss of feasibility is NOT counted as a matching leader.
                entry[inlet] = {
                    "groups_scored": len(g),
                    "groups_lost_vs_original_40": 40-len(g),
                    "candidates_feasible": int(np.isfinite(sel.cost).sum()),
                    "candidates_lost_vs_original_310": int((~np.isfinite(sel.cost)).sum()),
                    "groups_mismatch": s.get("top1_mismatch_groups", 0),
                    "material_gt5": s.get("gt5pct", 0),
                    "same_temperature_other_catalyst_gt5": (
                        s.get("kinds", {}).get("cat_sameT", {}).get("gt5pct", 0)),
                    "other_catalyst_any_temperature_gt5": (
                        s.get("kinds", {}).get("other_catalyst", {}).get("gt5pct", 0)),
                    "without_bansode": s.get("without_bansode", {}),
                    "paper_cluster_bootstrap": s.get("paper_cluster_bootstrap", {}),
                    "selected_at_m_ceiling": int(
                        sel.loc[np.isfinite(sel.cost), "selection_at_m_max"].astype(str)
                        .str.lower().eq("true").sum()),
                }
            robust = None
            source = {}
            for inlet in J.INLET_NAMES:
                g = grouped[inlet]
                if g.empty:
                    choices = set()
                else:
                    choices = set(g.loc[
                        (g["top1_mismatch"]) & (g["regret"] > 0.05) &
                        (g["kind"] == "other catalyst, same temperature")].index)
                    source.update({x: d for x, d in g["doi"].items()})
                robust = choices if robust is None else robust & choices
            robust = sorted(robust or set())
            results[f"m{int(max_m)}__{cap}"] = {
                "conditions": dict(max_m=max_m, inventory_inlet_power_anchor_multiple=CAPS[cap]),
                "inlets": entry,
                "robust_sameT_gt5_all_three_inlets": {
                    "groups": len(robust),
                    "papers": len({source[g] for g in robust}),
                    "without_bansode": sum(source[g] != J.BANSODE for g in robust),
                    "cases": [{"group": g, "doi": source[g]} for g in robust],
                },
            }
            all_m_groups[(max_m, cap)] = robust
    pd.concat(gm_parts, ignore_index=True).to_csv(
        args.output / "engineering_group_metrics.csv",
        index=False, float_format="%.12g") if gm_parts else None
    data.to_csv(args.output / "engineering_candidate_optima.csv",
                index=False, float_format="%.12g")
    # Previously 4 robust m=10 cases; explicitly report their status for every envelope.
    previous = json.loads((ROOT / "analysis/field_robustness_2026_10_12/results/joint_summary.json").read_text())
    target_groups = [d["group"] for d in previous["cross_inlet_sameT_other_catalyst_gt5"]["groups_and_dois"]]
    survivor = {
        key: {"original_four_retained": sum(g in set(cases) for g in target_groups),
              "original_four_lost": [g for g in target_groups if g not in set(cases)]}
        for (max_m, cap), cases in all_m_groups.items()
        for key in [f"m{int(max_m)}__{cap}"]
    }
    result = {
        "status": "Exploratory reference-normalized equipment-cap screen; not a validated plant design.",
        "basis": ANCHORS, "caps": CAPS,
        "loading_maxima": LOADING_MAX, "loading_grid": LOADING_GRID,
        "inlet_constraints": INLETS,
        "candidate_entries": len(base), "comparison_groups": int(base.group.nunique()),
        "checks": {
            "baseline_m10_no_caps_matches_prior_joint_scan": True,
            "all_selected_optima_satisfy_equipment_and_inlet_caps": True,
        },
        "scenarios": results,
        "prior_four_survivor_status": survivor,
        "engineering_limitations": [
            "Equipment caps are illustrative ratios to a single published 70-bar one-step process, not validated limits.",
            "Reactor inlet normalized on molar flow, not actual gas velocity or residence-time distribution.",
            "Recycle compressor power is calculated at FIXED 1.5-bar loop pressure drop regardless of reactor loading; this is not pressure-drop verification.",
            "Pressure drop requires catalyst pellet properties, bed geometry and hot-gas thermophysical properties.",
            "The first-order conversion-vs-catalyst-loading surrogate and fixed selectivity are unvalidated outside measured points.",
            "Five printed CZA points in a cooled-reactor paper exceed the isothermal lab-feed equilibrium and are unscorable under this simplified feed model.",
            "Compare numerator together with cases/papers still feasible: a vanishing inversion count due to infeasibility is not proof of rank agreement.",
        ],
    }
    (args.output / "engineering_summary.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False, default=float) + "\n",
        encoding="utf-8")
    print(json.dumps({
        k: {"sameT_robust": v["robust_sameT_gt5_all_three_inlets"]["groups"],
            "papers": v["robust_sameT_gt5_all_three_inlets"]["papers"],
            "anchor_inlet_groups": v["inlets"]["inlet_6p86"]["groups_scored"],
            "anchor_inlet_gt5": v["inlets"]["inlet_6p86"]["material_gt5"]}
        for k, v in results.items()}, indent=2))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)
    shard = sub.add_parser("shard")
    shard.add_argument("--index", required=True, type=int)
    shard.add_argument("--count", required=True, type=int)
    shard.add_argument("--out", required=True, type=Path)
    shard.add_argument("--smoke", type=int, default=None)
    ag = sub.add_parser("aggregate")
    ag.add_argument("--input-dir", type=Path, required=True)
    ag.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    if args.cmd == "shard":
        if args.count <= 0 or not 0 <= args.index < args.count:
            p.error("Shard index must be in [0, count)")
        if args.smoke is not None and args.smoke <= 0:
            p.error("Smoke must have positive number of entries")
        make_shard(args)
    else:
        aggregate_runs(args)


if __name__ == "__main__":
    main()
