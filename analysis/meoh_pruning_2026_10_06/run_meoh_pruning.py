"""Compute saved by ACSA in the methanol literature screen: a closed-form cost lower bound decides which candidates
need the full plant optimization.

Full evaluation (what run_literature_inversion.py does per candidate): the recycle-loop cost on the 396-level purge
grid, with the recycled-CO conversion resolved at every purge level by bisection against the RWGS and CO-hydrogenation
equilibria (central rule), then the minimum over the eligible purge levels (within CO2-hydrogenation equilibrium and
the workbook nonreactive limit).

Lower bound (no equilibrium solve). At each purge level p of the same grid, for 1 mol net methanol and any
recycled-CO per-pass conversion x in [0, 1] (so it covers the inert and every recycled-CO rule):
  reactor-inlet CO2   co2_in in [1 / (X (S_MeOH + (1-p) S_CO)), 1 / (X S_MeOH)]   (x = 1 and x = 0)
  methane made        ch4 = X S_CH4 co2_in >= X S_CH4 co2_in_lb
  fresh CO2           = co2_in (p + X (1-p)), and >= 1 + ch4          (carbon balance)
  H2 consumed         in [3 + 4 ch4, 3 + X (4 S_CH4 + S_CO) co2_in]   (3 per methanol by either route)
  unreacted H2        h2_out = H2/CO2 co2_in - consumed, minimized over the co2_in interval
  fresh H2            = consumed + p h2_out
  loop inerts         CH4 in the loop ch4 / p, N2 fresh_H2 (1 - purity) / (purity p)
  gas out             >= (1 - X) co2_in_lb + h2_out_lb + ch4 / p + N2;   recycle (1-p), purge gas p of it
  reactor inlet       >= (1 + H2/CO2) co2_in_lb + (1-p)/p ch4 + N2;    crude liquid >= 2 + 2 ch4
Every equipment-cost term rises with its flow or power, every cost coefficient is positive, and the catalyst inventory
(from the space-time yield) enters exactly, so the plant model evaluated on these flows is a lower bound on the cost
at that purge level under both CO treatments; the bound is the minimum over the whole grid, so it is also below
the minimum over the eligible levels.

Agent rule per comparison group (the scored groups of the main result, group_metrics.csv): fully evaluate the paper's
leader (needed for the regret) and then candidates in increasing bound order, stopping when the next bound exceeds the
best full cost found. Candidates that are infeasible under a treatment are in no leaderboard of that treatment (as in
the main result); the groups and their STY leaders are those of each treatment's feasible candidates.
The full costs come from literature_candidates.csv of the main result (the frozen full evaluation of every candidate),
so the pruned leader can be checked against the exhaustive one. Timing of one full and one bound evaluation is
measured on this machine.

Outputs: candidate_bounds.csv, group_pruning.csv, summary.json.
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "data" / "meoh"))
sys.path.insert(0, str(REPO / "agent"))
import meoh_general_model as G  # noqa: E402
from selfcheck_gate import require  # noqa: E402

M = G.M
MAIN = REPO / "analysis" / "meoh_literature_inversion_2026_10_05"
TREATMENTS = {"recycled_opt": "cost_recycled_opt", "inert_opt": "cost_inert_opt"}
CSV_REL = 5e-6           # literature_candidates.csv stores costs to 6 significant digits


def bound_flows(X, SMeOH, SCH4, SCO, h2_co2, p):
    """Lower-bound loop flows per mol net methanol at purge levels p (array), valid for any x_co in [0, 1]."""
    co2_lb = 1.0 / (X * (SMeOH + (1.0 - p) * SCO))
    co2_ub = 1.0 / (X * SMeOH)
    ch4 = X * SCH4 * co2_lb
    fresh_co2 = np.maximum(1.0 + ch4, co2_lb * (p + X * (1.0 - p)))
    cons_lb = 3.0 + 4.0 * ch4
    k = h2_co2 - X * (4.0 * SCH4 + SCO)                       # h2_out = k co2_in - 3 at the consumption maximum
    h2_out = np.maximum(0.0, np.minimum(k * co2_lb, k * co2_ub) - 3.0)
    fresh_h2 = cons_lb + p * h2_out
    n2 = fresh_h2 * (1.0 - M.H2_PURITY) / M.H2_PURITY / p
    gas_out = (1.0 - X) * co2_lb + h2_out + ch4 / p + n2
    return dict(fresh_co2=fresh_co2, fresh_h2=fresh_h2, recycle=(1.0 - p) * gas_out, purge_gas=p * gas_out,
                reactor_in=(1.0 + h2_co2) * co2_lb + (1.0 - p) / p * ch4 + n2, crude_liquid_mol=2.0 + 2.0 * ch4)


def lower_bound(X, SMeOH, SCH4, SCO, STY_per_g_cat, P_bar, h2_co2):
    """The general model's economics evaluated on the lower-bound flows (same equations and coefficients)."""
    lp = bound_flows(X, SMeOH, SCH4, SCO, h2_co2, G.PURGES)
    p_co2, p_h2, p_rec = G.powers(lp, P_bar)
    feed_eur_t, _, _ = M._feed_cost(lp)
    feed_M = feed_eur_t * M.PROD_TPY / 1e6
    elec_M = (p_co2 + p_h2 + p_rec) * M.HOURS_Y * M.ELEC_EUR_MWH / 1e6
    catalyst_t = G.catalyst_tonnes(STY_per_g_cat=STY_per_g_cat)
    gas_r = lp["reactor_in"] * M.PROD_KMOL_H * M.RECYCLE_FLOW_CORRECTION / M.REF_REACTOR_IN_KMOL_H
    liq_r = lp["crude_liquid_mol"] * M.PROD_KMOL_H / M.REF_CRUDE_LIQ_KMOL_H
    pur_r = lp["purge_gas"] * M.PROD_KMOL_H * M.RECYCLE_FLOW_CORRECTION / M.REF_PURGE_KMOL_H
    E, Gx, C = M.EC_REF, M.EXP_GENERAL, M.EXP_COMP
    EC = (E["Reactor modules"] * (catalyst_t / M.SOURCE_CAT_T) ** Gx
          + E["Carbon dioxide compressor"] * (p_co2 / M.REF_POWERS[0]) ** C
          + E["Hydrogen compressor"] * (p_h2 / M.REF_POWERS[1]) ** C
          + E["Recycle/reflux compressor"] * (p_rec / M.REF_POWERS[2]) ** C
          + (E["Reactor preheaters"] + E["Heat exchangers"] + E["Flash drums"]) * gas_r ** Gx
          + (E["Distillation column"] + E["Pump"]) * liq_r ** Gx
          + (E["Furnace & blower"] + E["Turbine & generator"]) * pur_r ** Gx)
    FCI = M.LF * EC
    ACC = FCI * M.CRF + FCI / 9.0 * M.IR
    NPC = (ACC + M.COMMON_DIRECT_MEUR_Y + feed_M + elec_M + 2.2125 * M.SOURCE_OL_MEUR_Y + 0.081 * FCI) / 0.90
    return float(np.min(NPC) * 1e6 / M.PROD_TPY)


def prune_group(g, cost_col):
    """Branch and bound in bound order; returns the evaluated index set and the chosen leader. Feasibility is known
    only after a full evaluation: the paper's leader is the highest-STY candidate that evaluates feasible (higher-STY
    infeasible ones are evaluated on the way), and an infeasible candidate reached in bound order is evaluated too."""
    full = g[cost_col].fillna(np.inf)
    evaluated = set()
    best = np.inf
    for i in g.sort_values("STY", ascending=False).index:
        evaluated.add(i)
        best = full[i]
        if np.isfinite(best):
            break
    for i in g.sort_values("bound").index:
        if g.loc[i, "bound"] > best * (1 + CSV_REL):
            break
        evaluated.add(i)
        best = min(best, full[i])
    leader = min(evaluated, key=lambda i: full[i])
    return evaluated, leader


def main():
    require()            # ACSA scores new candidates only after reproducing all three hand-built cases
    c = pd.read_csv(MAIN / "literature_candidates.csv")
    c["bound"] = [lower_bound(r.X, r.SMeOH, r.SCH4, r.SCO, r.STY, r.P_bar, r.h2_co2) for r in c.itertuples()]
    for t, col in TREATMENTS.items():
        f = np.isfinite(c[col])
        slack = c.loc[f, col] * (1 + CSV_REL) - c.loc[f, "bound"]
        assert (slack >= 0).all(), c.loc[f][slack < 0][["group", "entry", col, "bound"]]
    gsize = {t: c[np.isfinite(c[col])].groupby("group").size() for t, col in TREATMENTS.items()}
    scored_all = set().union(*(set(s[s >= 2].index) for s in gsize.values()))
    rows, totals = [], {t: dict(groups=0, full=0, evaluated=0, leader_missed=0) for t in TREATMENTS}
    for key, g_all in c[c.group.isin(scored_all)].groupby("group"):
        row = dict(group=key, candidates=len(g_all))
        for t, col in TREATMENTS.items():
            g = g_all
            if np.isfinite(g[col]).sum() < 2:
                continue
            ev, leader = prune_group(g, col)
            exact = g[col].idxmin()
            ok = np.isclose(g.loc[leader, col], g.loc[exact, col], rtol=0, atol=1e-9)
            row.update({f"candidates_{t}": len(g), f"evaluated_{t}": len(ev), f"leader_found_{t}": bool(ok)})
            totals[t]["groups"] += 1
            totals[t]["full"] += len(g)
            totals[t]["evaluated"] += len(ev)
            totals[t]["leader_missed"] += int(not ok)
        rows.append(row)
    gp = pd.DataFrame(rows)

    # timing: one full evaluation (central recycled-CO rule, 396 purge levels, eligible optimum) vs one bound,
    # median of 5 candidates
    c = c[c.group.isin(scored_all)].reset_index(drop=True)
    sample = c.sample(5, random_state=20261006)
    t_full, t_bound = [], []
    for r in sample.itertuples():
        cd = dict(X=r.X, SMeOH=r.SMeOH, SCH4=r.SCH4, SCO=r.SCO)
        t0 = time.perf_counter()
        G.optimal_purge(cd, STY_per_g_cat=r.STY, P_bar=r.P_bar, h2_co2=r.h2_co2, T_C=r.T_C, x_co="recycled_central")
        t_full.append(time.perf_counter() - t0)
        t0 = time.perf_counter()
        for _ in range(100):
            lower_bound(r.X, r.SMeOH, r.SCH4, r.SCO, r.STY, r.P_bar, r.h2_co2)
        t_bound.append((time.perf_counter() - t0) / 100)
    summary = dict(
        groups=int(len(gp)), candidates=int(len(c)),
        bound_valid_all=True,
        median_bound_gap_eur_t={t: float((c[col] - c.bound).median()) for t, col in TREATMENTS.items()},
        bound_exact_candidates={t: int((abs(c[col] - c.bound) <= c[col] * CSV_REL).sum()) for t, col in TREATMENTS.items()},
        infeasible_candidates={t: int((~np.isfinite(c[col])).sum()) for t, col in TREATMENTS.items()},
        pruning={t: dict(v, excluded=v["full"] - v["evaluated"],
                         excluded_fraction=round(1 - v["evaluated"] / v["full"], 4)) for t, v in totals.items()},
        timing_s=dict(full_median=float(np.median(t_full)), bound_median=float(np.median(t_bound))),
    )
    tf, tb = summary["timing_s"]["full_median"], summary["timing_s"]["bound_median"]
    v = totals["recycled_opt"]
    summary["compute_fraction_recycled_opt"] = round((v["evaluated"] * tf + v["full"] * tb) / (v["full"] * tf), 4)
    c[["group", "doi", "entry", "STY", "bound", "cost_recycled_opt", "cost_inert_opt"]].to_csv(
        HERE / "candidate_bounds.csv", index=False, float_format="%.6g")
    gp.to_csv(HERE / "group_pruning.csv", index=False)
    (HERE / "summary.json").write_text(json.dumps(summary, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
