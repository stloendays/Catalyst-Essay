"""Paper leaderboards versus plant-cost leaderboards for literature CO2-to-methanol catalysts.

Input: the literature-extraction Agent's normalized records (agent/extraction/out/records_normalized.csv), used as
extracted, with no manual correction. Every record with CO2 conversion, methanol selectivity, temperature, pressure
and H2/CO2 is a candidate operating point.

Comparison groups. Within one paper, entries tested at the same pressure, H2/CO2 ratio and space velocity form one
group: the comparison the paper itself makes (catalysts, and temperatures of one catalyst, as in the frozen
four-state case). Groups with at least two entries are scored.

Paper leaderboard. Methanol space-time yield per g catalyst, the productivity figure papers use to rank catalysts.
One productivity basis per group: the printed STY when every entry prints it, otherwise STY derived from the mass
space velocity, otherwise from the volumetric space velocity with a bulk density of 1.0 g/mL (0.5 and 2.0 g/mL
tested). Derived STY = GHSV x y_CO2 x X x S_MeOH / 22.414 x 32.042.

Plant leaderboard. Net production cost (EUR/t MeOH) from the generalized recycle-economics model
(data/meoh/meoh_general_model.py) at each entry's own pressure, H2/CO2 and temperature, with catalyst mass from the
group's productivity basis. Primary: recycled CO (central RWGS rule), entry-optimal purge. Variants: inert CO,
2 % purge. Selectivity closure follows the workbook: S_MeOH and S_CH4 as reported ("<1" -> 0), CO-like residual
1 - S_MeOH - S_CH4; when S_CH4 is not reported, S_CH4 = 1 - S_MeOH - S_CO if S_CO is reported, else 0.

Self-check (Agent consistency with the hand-built case): the extracted Gothe et al. 2025 Table 4 entries are run
through the same code path; their costs must equal the frozen Table 4 results, including the four canonical states.

Outputs (this folder): literature_candidates.csv, group_metrics.csv, summary.json.
"""
import csv
import json
import sys
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "data" / "meoh"))
import meoh_general_model as G  # noqa: E402

from meoh_candidates import (GOTHE_DOI, RECORDS, REQUIRED, RHO_DEFAULT, RHO_RANGE, candidate_row,  # noqa: E402
                             gothe_selfcheck, read_records)

sys.path.insert(0, str(REPO / "agent"))
from selfcheck_gate import require  # noqa: E402

require()          # ACSA scores new candidates only after reproducing all three hand-built cases


# ---------------------------------------------------------------- candidates ----------------------------------
d = read_records()
d = d.dropna(subset=REQUIRED).copy()
rows = [c for c in (candidate_row(r) for _, r in d.iterrows()) if c is not None]
cand = pd.DataFrame(rows)
cand["group"] = (cand.doi + " | " + cand.P_bar.map("{:g} bar".format) + " | H2/CO2 "
                 + cand.h2_co2.map("{:.3g}".format) + " | " + cand.ghsv_key)


PRINTED_SPREAD_MAX = 3.0   # printed STY / (F_CO2 X S) may vary by plot reading, not by more than this within a group


def group_basis(g):
    if g.sty_print.notna().all():
        ratio = g.sty_print / g.sty_mass
        if g.sty_mass.notna().all() and (ratio.min() <= 0 or ratio.max() / ratio.min() > PRINTED_SPREAD_MAX):
            # the paper's printed rates contradict its own conversion and selectivity (mixed per-g-metal and
            # per-g-catalyst rates in Sharma 2021; a zero rate at non-zero conversion in Rui 2017)
            return "STY from mass GHSV (printed STY inconsistent with X*S*F)", g.sty_mass
        return "printed STY", g.sty_print
    if g.sty_mass.notna().all():
        return "STY from mass GHSV", g.sty_mass
    if g.sty_vol.notna().all():
        return "STY from volumetric GHSV (assumed density)", g.sty_vol
    if g.sty_print.notna().any():
        return "printed STY (partial)", g.sty_print
    return None, None


parts = []
for key, g in cand.groupby("group"):
    basis, sty = group_basis(g)
    g = g.copy()
    g["sty_basis"] = basis
    g["STY"] = sty
    parts.append(g)
cand = pd.concat([p for p in parts if p.STY.notna().any()]).dropna(subset=["STY"])
cand = cand[cand.STY > 0].reset_index(drop=True)


def plant(row, x_co="recycled_central", purge="opt", sty_scale=1.0):
    kw = dict(STY_per_g_cat=row.STY * sty_scale, P_bar=row.P_bar, h2_co2=row.h2_co2, T_C=row.T_C, x_co=x_co)
    c = dict(X=row.X, SMeOH=row.SMeOH, SCH4=row.SCH4, SCO=row.SCO)
    if purge == "opt":
        sweep = G.purge_sweep(c, **kw)["cost_eur_t"]
        j = int(np.nanargmin(sweep))
        return float(sweep[j]), float(G.PURGES[j])
    return float(G.cost(c, purge=purge, **kw)["cost_eur_t"]), purge


VARIANTS = {
    "recycled_opt": dict(x_co="recycled_central", purge="opt"),
    "recycled_2pct": dict(x_co="recycled_central", purge=0.02),
    "inert_opt": dict(x_co="inert", purge="opt"),
    "inert_2pct": dict(x_co="inert", purge=0.02),
}
for name, kw in VARIANTS.items():
    res = [plant(r, **kw) for r in cand.itertuples()]
    cand[f"cost_{name}"] = [c for c, _ in res]
    if kw["purge"] == "opt":
        cand[f"purge_{name}"] = [p for _, p in res]
vol = cand.sty_basis.str.startswith("STY from volumetric")
for rho in RHO_RANGE:
    scale = RHO_DEFAULT / rho          # STY per g scales with 1/density
    cand[f"cost_recycled_opt_rho{rho:g}"] = [plant(r, sty_scale=scale if v else 1.0)[0]
                                             for r, v in zip(cand.itertuples(), vol)]

# ---------------------------------------------------------------- self-check ----------------------------------
got = cand[cand.doi == GOTHE_DOI].copy()
check = gothe_selfcheck(got)
selfcheck_max = float(check.abs_diff.max())
canon = check[(check.canonical_state != "") & (check.treatment == "inert")]

# ---------------------------------------------------------------- group metrics -------------------------------
def group_metrics(g, cost_col, up_col="STY"):
    g = g.sort_values(up_col, ascending=False)
    up_best = g[up_col].max()
    up_winners = set(g.index[g[up_col] >= up_best - 1e-12])
    econ_idx = g[cost_col].idxmin()
    c_best = g[cost_col].min()
    c_up = g.loc[list(up_winners), cost_col].min()
    n = len(g)
    pairs = list(combinations(g.index, 2))
    inv = sum(1 for a, b in pairs
              if (g.at[a, up_col] - g.at[b, up_col]) * (g.at[b, cost_col] - g.at[a, cost_col]) < 0)
    rho = (float(spearmanr(g[up_col], -g[cost_col]).statistic) if n >= 3 and g[up_col].nunique() > 1 else None)
    up3 = set(g.nlargest(min(3, n), up_col).index)
    ec3 = set(g.nsmallest(min(3, n), cost_col).index)
    return dict(n=n, top1_mismatch=econ_idx not in up_winners,
                regret=(c_up - c_best) / c_best,
                upstream_winner=g.loc[sorted(up_winners)[0], "catalyst"], economic_winner=g.at[econ_idx, "catalyst"],
                upstream_winner_cost=c_up, economic_winner_cost=c_best,
                economic_rank_of_upstream_winner=int((g[cost_col] < c_up - 1e-9).sum()) + 1,
                pairs=len(pairs), inversions=inv, spearman=rho,
                top3_overlap=len(up3 & ec3) if n >= 4 else None)


def aggregate(frame, cost_col, up_col="STY", label=""):
    out = []
    for key, g in frame.groupby("group"):
        if len(g) < 2:
            continue
        m = group_metrics(g, cost_col, up_col)
        m.update(group=key, doi=g.doi.iloc[0], basis=g.sty_basis.iloc[0])
        out.append(m)
    gm = pd.DataFrame(out)
    if gm.empty:
        return gm, {}
    papers = gm.groupby("doi").top1_mismatch.any()
    s = dict(variant=label, groups=len(gm), papers=int(gm.doi.nunique()), entries=int(gm.n.sum()),
             top1_mismatch_groups=int(gm.top1_mismatch.sum()),
             top1_mismatch_fraction=float(gm.top1_mismatch.mean()),
             papers_with_mismatch=int(papers.sum()),
             paper_weighted_mismatch_fraction=float(gm.groupby("doi").top1_mismatch.mean().mean()),
             regret_median_all=float(gm.regret.median()),
             regret_median_mismatched=float(gm.loc[gm.top1_mismatch, "regret"].median()) if gm.top1_mismatch.any() else 0.0,
             regret_max=float(gm.regret.max()),
             regret_mean_all=float(gm.regret.mean()),
             pairwise_inversions=f"{int(gm.inversions.sum())}/{int(gm.pairs.sum())}",
             pairwise_inversion_fraction=float(gm.inversions.sum() / gm.pairs.sum()),
             groups_n_ge_4=int((gm.n >= 4).sum()),
             top3_overlap_mean_n_ge_4=float(gm.loc[gm.n >= 4, "top3_overlap"].mean()) if (gm.n >= 4).any() else None)
    return gm, s


primary_gm, primary = aggregate(cand, "cost_recycled_opt", label="primary: recycled CO, optimal purge, STY leaderboard")
variants = {}
for name in VARIANTS:
    if name != "recycled_opt":
        variants[name] = aggregate(cand, f"cost_{name}", label=name)[1]
for rho in RHO_RANGE:
    variants[f"density_{rho:g}"] = aggregate(cand, f"cost_recycled_opt_rho{rho:g}", label=f"density {rho:g} g/mL")[1]
cand["XS"] = cand.X * cand.SMeOH
variants["leaderboard_X_times_S"] = aggregate(cand, "cost_recycled_opt", up_col="XS", label="X*S leaderboard")[1]
variants["leaderboard_X"] = aggregate(cand, "cost_recycled_opt", up_col="X", label="X leaderboard")[1]
variants["leaderboard_S_MeOH"] = aggregate(cand, "cost_recycled_opt", up_col="SMeOH", label="S_MeOH leaderboard")[1]
variants["printed_values_only"] = aggregate(cand[~cand.plot_read], "cost_recycled_opt", label="no plot readings")[1]
BIGGEST = primary_gm.groupby("doi").size().idxmax()          # paper contributing the most scored groups
variants["without_paper_with_most_groups"] = aggregate(cand[cand.doi != BIGGEST], "cost_recycled_opt",
                                                       label=f"without {BIGGEST}")[1]
variants["methanol_products_only"] = aggregate(cand[~cand.other_products], "cost_recycled_opt",
                                               label="reported S_MeOH+S_CO+S_CH4 >= 95 %")[1]

# ---------------------------------------------------------------- outputs -------------------------------------
keep = ["group", "doi", "entry", "catalyst", "T_C", "P_bar", "h2_co2", "ghsv_key", "X", "SMeOH", "SCO", "SCH4",
        "reported_S_sum", "other_products", "plot_read", "sty_basis", "STY", "cost_recycled_opt",
        "purge_recycled_opt", "cost_recycled_2pct", "cost_inert_opt", "purge_inert_opt", "cost_inert_2pct",
        "cost_recycled_opt_rho0.5", "cost_recycled_opt_rho2", "source", "location"]
cand.sort_values(["group", "STY"], ascending=[True, False])[keep].to_csv(HERE / "literature_candidates.csv",
                                                                       index=False, float_format="%.6g")
primary_gm.to_csv(HERE / "group_metrics.csv", index=False, float_format="%.6g")
check.to_csv(HERE / "selfcheck_gothe_table4.csv", index=False, float_format="%.10g")
summary = dict(
    records_in=int(len(read_records())), candidates=int(len(cand)), papers_with_candidates=int(cand.doi.nunique()),
    primary=primary, variants=variants,
    selfcheck=dict(entries=int(len(got)), max_abs_diff_eur_t=selfcheck_max,
                   canonical_states={r.canonical_state: round(r.agent, 2) for r in canon.itertuples()}),
)
(HERE / "summary.json").write_text(json.dumps(summary, indent=1, default=float) + "\n", encoding="utf-8")
print(json.dumps(summary, indent=1, default=float))
