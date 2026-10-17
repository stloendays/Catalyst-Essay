#!/usr/bin/env python3
"""Independent, unfrozen methanol catalyst-loading x purge counterfactual.

Jointly minimize modelled plant cost over m (catalyst per unit feed, relative to
the printed laboratory point) and purge. The existing frozen S5 outputs and
their calculation remain untouched.

Important limitations:
- X(m) is a one-point-calibrated first-order approach-to-equilibrium surrogate,
  NOT reactor kinetics or an experimentally observed catalyst optimum.
- Each entry retains its measured T, P, selectivity and inlet H2/CO2.
- CO-conversion and plant cost use the frozen model; CO2 outlet equilibrium,
  optional inlet composition and optional catalyst inventory caps are enforced.
- No universal process feasibility is inferred from a published loop's inlet.
- Points above laboratory feed equilibrium cannot be extrapolated in m.
- The equilibrium solver uses multi-start roots, like conversion_sensitivity.py.

Usage:
    python analysis/field_robustness_2026_10_12/joint_inventory_purge.py \
        shard --index 0 --count 4 --out /tmp/shards/shard_0.csv
    python analysis/field_robustness_2026_10_12/joint_inventory_purge.py \
        aggregate --input-dir /tmp/shards --output /tmp/joint_report
"""
from __future__ import annotations

import argparse
import functools
import json
import math
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
ME = ROOT / "analysis/meoh_literature_inversion_2026_10_05"
sys.path.insert(0, str(ROOT / "data/meoh"))
sys.path.insert(0, str(ME))

import meoh_general_model as G  # noqa: E402
from meoh_candidates import aggregate, bootstrap  # noqa: E402
from mismatch_kinds import classify  # noqa: E402
from run_conversion_sensitivity import x_eq_feed  # noqa: E402

# These are illustrative envelope cases from published plant inlet streams,
# not universally valid physical upper limits on non-H2/CO2 components.
LIMITS = {"open": None, "inlet_4p92": 0.0492,
          "inlet_6p86": float(G.NONREACTIVE_MAX), "inlet_10p25": 0.10249}
INLET_NAMES = tuple(x for x in LIMITS if x != "open")
BANSODE = "10.1039/c2cy20604h"
M_GRID = (0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 3.0, 5.0, 10.0)
GRID = np.unique(np.r_[np.geomspace(1e-6, float(G.PURGES[0]), 61)[:-1], G.PURGES])
FIELDS = ("cost_eur_t", "nonreactive_fraction", "catalyst_t",
          "recycle_kmol_h", "carbon_efficiency", "fresh_h2_co2",
          "co2_hyd_approach")
TOL = float(G.EQ_TOL)


def candidates():
    f = pd.read_csv(ME / "literature_candidates.csv")
    sizes = f.groupby("group").size()
    f = f[f.group.isin(sizes[sizes >= 2].index)].copy()
    # Deterministic row identity independent of job shard or environment.
    f = f.sort_values(["group", "catalyst", "T_C", "X", "STY"]).reset_index(drop=True)
    f.insert(0, "row_id", np.arange(len(f), dtype=int))
    return f


@functools.lru_cache(maxsize=None)
def feed_eq(h2_co2, y_co2, temperature, pressure):
    xe, nroots = x_eq_feed(h2_co2, y_co2, temperature, pressure)
    if not np.isfinite(xe) or xe <= 0 or xe >= 1:
        raise ValueError(f"Bad equilibrium result: {xe} at {(h2_co2, y_co2, temperature, pressure)}")
    return float(xe), int(nroots)


def states(x0, xeq):
    """(m, X, flag) with guaranteed exact experimental anchor when m=1."""
    if x0 >= xeq * (1 - 1e-10):
        # Do not extrapolate an experimentally reported above-feed-equilibrium point.
        return [(1.0, float(x0), "above_feed_eq_only_measured")]
    frac = x0 / xeq
    answer = []
    for m in M_GRID:
        x = xeq * (1.0 - (1.0 - frac) ** m)
        if m == 1.0:
            x = x0
        if 0 < x < 1:
            answer.append((m, float(x), "surrogate"))
    return answer


def evaluate_array(c, purge):
    """Vectorized path, scalar fallback where a single invalid purge invalidates the array."""
    try:
        x = G.cost(c, purge=purge, x_co="recycled_central",
                   P_bar=c["P_bar"], h2_co2=c["h2_co2"],
                   T_C=c["T_C"], STY_per_g_cat=c["STY"])
        return {key: np.broadcast_to(np.asarray(x[key], dtype=float), purge.shape).copy()
                for key in FIELDS}
    except (ValueError, FloatingPointError, OverflowError):
        data = {k: np.full(purge.shape, np.nan) for k in FIELDS}
        for j, p in enumerate(purge):
            try:
                x = G.cost(c, purge=float(p), x_co="recycled_central",
                           P_bar=c["P_bar"], h2_co2=c["h2_co2"],
                           T_C=c["T_C"], STY_per_g_cat=c["STY"])
                for key in FIELDS:
                    data[key][j] = float(np.asarray(x[key]))
            except (ValueError, FloatingPointError, OverflowError):
                continue
        return data


def evaluate(row, max_inventory_multiple=None):
    x0 = float(row.X)
    sty0 = float(row.STY)
    xeq, roots = feed_eq(float(row.h2_co2), float(row.y_co2),
                         float(row.T_C), float(row.P_bar))
    result = {
        "row_id": int(row.row_id), "group": row.group, "doi": row.doi,
        "catalyst": row.catalyst, "x_eq_feed": xeq, "x_eq_roots": roots,
        "above_feed_eq": bool(x0 >= xeq * (1 - 1e-10)),
        "states_tested": 0, "feasible_states": 0,
    }
    best = {key: None for key in LIMITS}
    # Cost-based reactor sizing is already part of G.cost (catalyst_t -> modules).
    # The optional cap is intentionally separate and explicit, not a fitted constant.
    max_t = (float(G.M.SOURCE_CAT_T) * max_inventory_multiple
             if max_inventory_multiple is not None else float("inf"))
    for m, x, mode in states(x0, xeq):
        sty = sty0 * x / (x0 * m)
        c = dict(X=x, SMeOH=float(row.SMeOH), SCH4=float(row.SCH4),
                 SCO=float(row.SCO), STY=sty, P_bar=float(row.P_bar),
                 h2_co2=float(row.h2_co2), T_C=float(row.T_C))
        with np.errstate(all="ignore"), warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            e = evaluate_array(c, GRID)
        result["states_tested"] += 1
        cost = e["cost_eur_t"]
        ok = (np.isfinite(cost) & (cost > 0) &
              np.isfinite(e["co2_hyd_approach"]) &
              (e["co2_hyd_approach"] <= 1.0 + TOL) &
              (np.isfinite(e["catalyst_t"])) &
              (e["catalyst_t"] > 0) &
              (e["catalyst_t"] <= max_t))
        if not ok.any():
            continue
        result["feasible_states"] += 1
        for tag, limit in LIMITS.items():
            legal = ok if limit is None else (
                ok & np.isfinite(e["nonreactive_fraction"]) &
                (e["nonreactive_fraction"] <= limit))
            if not legal.any():
                continue
            j = int(np.argmin(np.where(legal, cost, np.inf)))
            optimum = float(cost[j])
            if best[tag] is not None and optimum >= best[tag]["cost"] - 1e-9:
                continue
            fresh = ((1.0 + float(e["fresh_h2_co2"][j])) /
                     float(e["carbon_efficiency"][j]) * G.M.PROD_KMOL_H)
            best[tag] = {
                "cost": optimum, "m": m, "purge": float(GRID[j]),
                "X": x, "STY": sty,
                "inventory_t": float(e["catalyst_t"][j]),
                "nonreactive": float(e["nonreactive_fraction"][j]),
                "recycle_ratio": float(e["recycle_kmol_h"][j] / fresh)
                if np.isfinite(fresh) and fresh > 0 else np.nan,
                "mode": mode,
            }
    for tag, value in best.items():
        for field in ("cost", "m", "purge", "X", "STY", "inventory_t",
                      "nonreactive", "recycle_ratio", "mode"):
            result[f"{tag}_{field}"] = (value[field] if value is not None else
                                       ("" if field == "mode" else np.nan))
        result[f"{tag}_feasible"] = value is not None
    return result


def shard(args):
    f = candidates()
    if args.max_entries is not None:
        f = f.iloc[:args.max_entries].copy()
    chosen = f[f.row_id % args.count == args.index]
    rows = []
    for i, row in enumerate(chosen.itertuples(index=False), 1):
        rows.append(evaluate(row, args.max_inventory_multiple))
        if i % 10 == 0 or i == len(chosen):
            print(f"shard={args.index} completed={i}/{len(chosen)}",
                  flush=True)
    if not rows:
        raise ValueError("Empty shard: choose count <= number of candidates")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(args.out, index=False, float_format="%.12g")
    print(f"WROTE {args.out} entries={len(rows)}")


def metrics(frame, cost_col, label):
    g, summary = aggregate(frame, cost_col, label=label)
    if g.empty:
        return g, summary
    g, kinds = classify(frame, g, cost_col)
    m = g[g.top1_mismatch]
    summary["kinds"] = kinds
    summary["gt5pct"] = int((m.regret > 0.05).sum())
    summary["gt5pct_papers"] = int(m[m.regret > 0.05].doi.nunique())
    summary["without_bansode"] = {
        "groups": int((g.doi != BANSODE).sum()),
        "mismatch": int((m.doi != BANSODE).sum()),
        "regret_gt5": int(((m.doi != BANSODE) & (m.regret > 0.05)).sum()),
        "papers_with_regret_gt5": int(m[(m.doi != BANSODE) & (m.regret > 0.05)].doi.nunique()),
    }
    summary["paper_cluster_bootstrap"] = bootstrap(g)
    return g, summary


def aggregate_runs(args):
    paths = sorted(args.input_dir.glob("shard_*.csv"))
    if not paths:
        raise FileNotFoundError(f"No shard_*.csv in {args.input_dir}")
    data = pd.concat([pd.read_csv(path) for path in paths], ignore_index=True)
    base = candidates()
    expected = set(base.row_id)
    found = data.row_id.astype(int)
    if len(found) != len(expected) or found.duplicated().any() or set(found) != expected:
        raise AssertionError("Shards did not cover all 310 frozen printed entries exactly once")
    if (data.states_tested <= 0).any():
        raise AssertionError("Some candidates were not evaluated")
    merged = base.merge(data.drop(columns=["group", "doi", "catalyst"]),
                        on="row_id", how="left", validate="one_to_one")
    if not merged.group.equals(base.group) or merged.row_id.isna().any():
        raise AssertionError("Candidate identity changed during merge")
    args.output.mkdir(parents=True, exist_ok=True)
    results = {}
    gm_sets = {}
    for tag in LIMITS:
        col = tag + "_cost"
        gm, summary = metrics(merged, col, tag)
        results[tag] = summary
        gm_sets[tag] = gm
        gm.to_csv(args.output / f"joint_group_metrics_{tag}.csv", index=False)
        # Feasible conditions must be respected at every selected optimum.
        chosen = merged[np.isfinite(merged[col])]
        if tag != "open" and (chosen[tag + "_nonreactive"] > LIMITS[tag] + 1e-9).any():
            raise AssertionError("A chosen purge exceeds its inlet limit")
        if (chosen[tag + "_m"] < min(M_GRID) - 1e-12).any():
            raise AssertionError("Invalid loading multiplier")
    # Cross-envelope robust cases: share a paper and group, cross-catalyst
    # and temperature classification must agree in all three separate limits.
    common = None
    for tag in INLET_NAMES:
        gm = gm_sets[tag]
        keep = gm[(gm.top1_mismatch) & (gm.regret > 0.05)].copy()
        keep = keep[keep.kind == "other catalyst, same temperature"]
        ids = set(keep.group)
        common = ids if common is None else common & ids
    common = common or set()
    key = merged[["group", "doi"]].drop_duplicates().set_index("group")["doi"]
    # NOTE: this intersection is within the JOINTLY-optimized scenarios.
    robust = sorted(common)
    result = {
        "status": "Unfrozen first-order-surrogate joint m-p analysis; do not overwrite S5.",
        "limits": LIMITS, "loading_grid": M_GRID,
        "purge_grid": {"points": len(GRID), "min": float(GRID.min()),
                       "max": float(GRID.max())},
        "candidate_entries": len(merged),
        "entries_above_lab_feed_eq": int(merged.above_feed_eq.sum()),
        "entries_with_no_feasible_state_open": int((~merged.open_feasible.astype(bool)).sum()),
        "joint_scenarios": results,
        "cross_inlet_sameT_other_catalyst_gt5": {
            "groups": len(robust),
            "without_bansode": sum(key[g] != BANSODE for g in robust),
            "independent_papers": len(set(key[g] for g in robust)),
            "groups_and_dois": [{"group": g, "doi": key[g]} for g in robust],
        },
        "caveats": [
            "First-order X(m) is a surrogate, not validated kinetics.",
            "Laboratory feed equilibrium may disagree with a measured point; no loading extrapolation is attempted there.",
            "No general upper bound on reactor bed tonnes unless --max-inventory-multiple was set.",
            "Each catalyst retains the measured selectivities, temperature, pressure and feed ratio.",
            "Published inlet compositions are scenario references, not universal engineering design limits.",
            "The frozen S5 treatment caps conversion without rescaling STY; this joint model checks equilibrium and rescales productivity, so its output must not be interpreted as an S5 rerun.",
        ],
    }
    (args.output / "joint_summary.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False, default=float) + "\n",
        encoding="utf-8")
    merged.to_csv(args.output / "joint_candidates.csv",
                  index=False, float_format="%.12g")
    print(json.dumps({
        "entries": len(merged),
        "joint_counts": {k: {"mismatch": v.get("top1_mismatch_groups"),
                             "gt5": v.get("gt5pct"),
                             "other_catalyst": v.get("kinds", {}).get("other_catalyst", {}).get("groups")}
                         for k, v in results.items()},
        "joint_cross_inlet_sameT_gt5": len(robust)}, indent=2))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="command", required=True)
    s = sub.add_parser("shard")
    s.add_argument("--index", type=int, required=True)
    s.add_argument("--count", type=int, default=4)
    s.add_argument("--out", type=Path, required=True)
    s.add_argument("--max-entries", type=int, help="smoke test only; cannot be aggregated")
    s.add_argument("--max-inventory-multiple", type=float, help="optional upper bound in units of anchor inventory")
    a = sub.add_parser("aggregate")
    a.add_argument("--input-dir", type=Path, required=True)
    a.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    if args.command == "shard":
        if args.index < 0 or args.index >= args.count:
            ap.error("0 <= shard index < shard count required")
        if args.max_inventory_multiple is not None and args.max_inventory_multiple <= 0:
            ap.error("--max-inventory-multiple must be >0")
        shard(args)
    else:
        aggregate_runs(args)


if __name__ == "__main__":
    main()
