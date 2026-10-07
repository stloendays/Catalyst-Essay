"""Headline group-level comparison (paper STY leader vs plant-cost leader) rerun with plant terms set to reference values.

Input: the candidate set of the literature inversion
(analysis/meoh_literature_inversion_2026_10_05/literature_candidates.csv: operating points, groups, STY basis).
For each variant the primary plant cost (recycled CO, central rule, cost-optimal purge among the eligible levels of
the 0.5-40 % grid: within CO2-hydrogenation equilibrium and the workbook nonreactive limit) is recomputed with
`plant_variant.economics`, and the group metrics are re-aggregated with the main result's own functions
(meoh_candidates.aggregate). Eligibility depends on the loop only, not on prices or the knobs varied here. The baseline
variant must reproduce the main result.

Parallel: multiprocessing over candidates (BENCH_WORKERS, default 4).
"""
from __future__ import annotations

import json
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(REPO / "analysis" / "meoh_literature_inversion_2026_10_05"))
import plant_variant as V  # noqa: E402
from meoh_candidates import ROW_KEYS, aggregate  # noqa: E402

G = V.G
WORKERS = int(__import__("os").environ.get("BENCH_WORKERS", "4"))
CANDS = REPO / "analysis" / "meoh_literature_inversion_2026_10_05" / "literature_candidates.csv"


def _one(args):
    """All variants for one candidate. The CO-recycle window (x_CO per purge level) depends only on the loop
    thermodynamics, not on prices, so it is solved once and passed to every variant as numbers."""
    row, variants = args
    c = (row["X"], row["SMeOH"], row["SCH4"], row["SCO"])
    base = dict(STY_per_g_cat=row["STY"], P_bar=row["P_bar"], h2_co2=row["h2_co2"], T_C=row["T_C"])
    out = {}
    try:
        b = G.purge_sweep(dict(X=c[0], SMeOH=c[1], SCH4=c[2], SCO=c[3]), x_co="recycled_central", **base)
    except ValueError:
        return {name: (np.nan, np.nan) for name in variants}
    ok = G.eligible_purges(b)
    c = (b["X_eff"],) + c[1:]          # per-pass conversion capped at CO2-hydrogenation equilibrium
    for name, kw in variants.items():
        if not ok.any():
            out[name] = (np.nan, np.nan)
            continue
        sweep = V.economics(*c, purge=G.PURGES, x_co=b["x_co"], **base, **kw)["cost_eur_t"]
        j = int(np.argmin(np.where(ok, sweep, np.inf)))
        out[name] = (float(sweep[j]), float(G.PURGES[j]))
    return out


def costs(cand, variants, workers=WORKERS):
    rows = cand[ROW_KEYS].to_dict("records")
    with Pool(workers) as pool:
        return pool.map(_one, [(r, variants) for r in rows], chunksize=4)


def run(variants: dict, workers=WORKERS):
    cand = pd.read_csv(CANDS)
    res = costs(cand, variants, workers)
    results, group_tables = {}, {}
    for name, kw in variants.items():
        cand[f"cost_{name}"] = [r[name][0] for r in res]
        cand[f"purge_{name}"] = [r[name][1] for r in res]
        gm, s = aggregate(cand, f"cost_{name}", label=name)
        s["knobs"] = {k: (list(v) if isinstance(v, tuple) else v) for k, v in kw.items()}
        results[name] = s
        group_tables[name] = gm
    return cand, results, group_tables


# Plant terms set to reference values (see README section 4). Each knob is one reference value.
VARIANTS = {
    "baseline": {},
    # catalyst inventory charged as replacement cost: anchor's own CZA price and 3-y life (Campos 2022, Table 2, 2.7)
    "catalyst_repl_18.1EURkg_3y": dict(cat_term=(18.1, 3.0)),
    # same price, industrial lifetime 4-6 y (Dieterich 2020, p8) -> 5 y
    "catalyst_repl_18.1EURkg_5y": dict(cat_term=(18.1, 5.0)),
    # recycle loop pressure drop of industrial loops: Lurgi SRC loop 3.5-4 bar (Dieterich 2020 Table 8) -> 3.75 bar
    "loop_dp_3.75bar": dict(loop_dp=3.75),
    # H2 at half the anchor price (1548.7 EUR/t): H2 share of cost falls to the low end of the reference range
    "h2_price_half": dict(h2_price=3097.4 / 2),
    # Perez-Fortes 2016 price set as tabulated by Dieterich 2020 Table 12 / Mbatha 2021 Table 15 (secondary)
    "perez_fortes_prices": dict(h2_price=3090.0, co2_price=0.0, elec_price=95.1),
    # industrial loops circulate more gas than the model loop at the same per-pass conversion (Lurgi CO2 pilot:
    # recycle ratio 4.5 at 35-45 % per pass vs 1.7 in the model, Table A row M5) -> recycle flow x 2.68
    "recycle_flow_x2.68": dict(recycle_mult=2.68),
    # primary-source values added 2026-10-06 (second pass)
    # Perez-Fortes 2016: 44.5 t replaced yearly at 95.24 EUR/kg (AE p727; JRC EUR 27629 p37)
    "catalyst_repl_95.24EURkg_1y": dict(cat_term=(95.24, 1.0)),
    # Nieminen 2019 / Sollai 2023: 95.24 EUR/kg, 4 y
    "catalyst_repl_95.24EURkg_4y": dict(cat_term=(95.24, 4.0)),
    # 95.24 EUR/kg with the upper industrial lifetime 6 y (Dieterich 2020: 4-6 y)
    "catalyst_repl_95.24EURkg_6y": dict(cat_term=(95.24, 6.0)),
    # Perez-Fortes 2016 stream table: loop pressure drop 78.5 -> 74.3 bar
    "loop_dp_4.2bar": dict(loop_dp=4.2),
    # anchor equipment split as tabulated in the Campos SI (Table S17) instead of the engine's figure-pixel split
    "ec_split_campos_SI": dict(ec_ref=V.EC_SI_TABLE_S17),
    # recycle weight calibrated so the model reproduces Nyari 2022's kinetic-model cost spread (VD - Slotboom 84 EUR/t;
    # model 83.4 with loop dP 4.2 bar and recycle-driven costs x10)
    "recycle_weight_nyari": dict(loop_dp=4.2, recycle_mult=10.0),
    "combined_primary_cat1y_dp4.2_recycle10": dict(cat_term=(95.24, 1.0), loop_dp=4.2, recycle_mult=10.0),
    "combined_primary_cat4y_dp4.2_recycle10": dict(cat_term=(95.24, 4.0), loop_dp=4.2, recycle_mult=10.0),
    "combined_cat3y_dp3.75": dict(cat_term=(18.1, 3.0), loop_dp=3.75),
    "combined_cat3y_dp3.75_recycle2.68": dict(cat_term=(18.1, 3.0), loop_dp=3.75, recycle_mult=2.68),
    "combined_cat3y_dp3.75_h2half": dict(cat_term=(18.1, 3.0), loop_dp=3.75, h2_price=3097.4 / 2),
}


if __name__ == "__main__":
    import time
    t0 = time.time()
    cand, res, gms = run(VARIANTS)
    frozen = pd.read_csv(CANDS)
    rel = np.abs(cand.cost_baseline / frozen.cost_recycled_opt - 1)
    froz_summary = json.loads((CANDS.parent / "summary.json").read_text(encoding="utf-8"))["primary"]
    check = dict(max_rel_diff_vs_frozen_costs=float(np.nanmax(rel)),
                 infeasible_same_as_main=bool((np.isnan(cand.cost_baseline) == np.isnan(frozen.cost_recycled_opt)).all()),
                 baseline_top1=f"{res['baseline']['top1_mismatch_groups']}/{res['baseline']['groups']}",
                 frozen_top1=f"{froz_summary['top1_mismatch_groups']}/{froz_summary['groups']}",
                 baseline_inversions=res["baseline"]["pairwise_inversions"],
                 frozen_inversions=froz_summary["pairwise_inversions"])
    assert check["baseline_top1"] == check["frozen_top1"] and check["infeasible_same_as_main"], check
    assert check["baseline_inversions"] == check["frozen_inversions"], check
    base = gms["baseline"].set_index("group")
    flips = []
    for name, gm in gms.items():
        g = gm.set_index("group")
        changed = g.index[g.top1_mismatch != base.loc[g.index, "top1_mismatch"]]
        winner_changed = g.index[g.economic_winner != base.loc[g.index, "economic_winner"]]
        res[name]["groups_flipped_vs_baseline"] = int(len(changed))
        res[name]["groups_economic_winner_changed"] = int(len(winner_changed))
        for k in winner_changed:
            flips.append(dict(variant=name, group=k, baseline_winner=base.at[k, "economic_winner"],
                              variant_winner=g.at[k, "economic_winner"],
                              baseline_mismatch=bool(base.at[k, "top1_mismatch"]), variant_mismatch=bool(g.at[k, "top1_mismatch"])))
    keep = (["group", "doi", "catalyst", "STY", "X", "SMeOH", "SCO", "SCH4", "T_C", "P_bar", "h2_co2"]
            + [f"cost_{v}" for v in VARIANTS] + [f"purge_{v}" for v in VARIANTS])
    cand[keep].to_csv(HERE / "sensitivity_candidates.csv", index=False, float_format="%.6g")
    pd.DataFrame(flips).to_csv(HERE / "sensitivity_winner_changes.csv", index=False)
    out = dict(check=check, variants=res, runtime_s=round(time.time() - t0, 1), workers=WORKERS)
    (HERE / "sensitivity_summary.json").write_text(json.dumps(out, indent=1, default=float) + chr(10), encoding="utf-8")
    print(json.dumps({k: (v["top1_mismatch_groups"], v["groups"], v["papers_with_mismatch"], v["pairwise_inversions"],
                          round(v["regret_median_mismatched"], 4), v["groups_flipped_vs_baseline"])
                      for k, v in res.items()}, indent=1))
    print(check)
