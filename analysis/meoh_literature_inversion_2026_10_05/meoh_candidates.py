"""Candidate construction from extracted methanol records, plant costs, group metrics, and the Gothe Table 4
self-check.

Shared by run_literature_inversion.py, the catalyst-cost and plant-benchmark variants and the ACSA self-check gate
(agent/selfcheck_gate.py), so all of them run the same code path.
"""
import math
import re
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

RECORDS = REPO / "agent" / "extraction" / "out" / "records_normalized.csv"
TABLE4 = REPO / "analysis" / "meoh_general_model_2026_10_05" / "table4_candidate_results.csv"
GOTHE_DOI = "10.1021/acscatal.5c05984"
VM, MW_MEOH = 22.414, 32.042
RHO_DEFAULT, RHO_RANGE = 1.0, (0.5, 2.0)
REQUIRED = ["X_CO2_pct", "S_MeOH_pct", "P_bar", "H2_CO2", "T_K"]


def pct(v, q):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return None
    return 0.0 if str(q).strip() == "<" else float(v) / 100.0


def closure(r):
    """Closed selectivities (workbook convention) and the sum of the selectivities the paper reports (an S_CH4 imputed
    from the residual is not a reported value and does not enter the sum)."""
    sm = pct(r.S_MeOH_pct, r.S_MeOH_q)
    sco = pct(r.S_CO_pct, r.S_CO_q)
    sch4_rep = pct(r.S_CH4_pct, r.S_CH4_q)
    sch4 = sch4_rep
    if sch4 is None:
        sch4 = max(0.0, 1.0 - sm - sco) if sco is not None else 0.0
    reported_sum = sm + (sco or 0.0) + (sch4_rep or 0.0)
    sm, sco_c, sch4 = G.close_selectivity(sm, None, min(sch4, 1.0 - sm))
    return sm, sco_c, sch4, reported_sum


def vol_ghsv(raw):
    s = str(raw).replace("−", "-").lower()
    if "h-1" not in s and "h−1" not in s:
        return None
    try:
        return float(s.split("h")[0].replace(",", "").strip())
    except ValueError:
        return None


def cofeed(feed) -> bool:
    """True when the stated feed adds water or CO to CO2/H2 (e.g. 'additional H2O = 0.8 mol%', 'R = CO/(CO2+CO) =
    40%', 'CO2:CO:H2 = ...'). The plant model takes a dry CO2/H2 make-up, so these entries are not candidates."""
    s = str(feed)
    for m in re.finditer(r"(?:H2O|water)[^;|]*?=\s*([\d.]+)", s, re.I):
        if float(m.group(1)) > 0:
            return True
    m = re.search(r"CO/\(CO2\s*\+\s*CO\)\s*=\s*([\d.]+)", s)
    if m:
        return float(m.group(1)) > 0
    return bool(re.search(r"(?:^|[\s:/,(])CO(?=\s*[:/,=)])", s))


def read_records(path=RECORDS) -> pd.DataFrame:
    """records_normalized.csv with only empty cells as missing (a catalyst is named 'NA' in Richard et al. 2017)."""
    return pd.read_csv(path, keep_default_na=False, na_values=[""])


def candidate_row(r):
    """One extracted record -> one candidate operating point, or None if it has no conversion or methanol, or if its
    feed adds water or CO."""
    if cofeed(r.feed):
        return None
    X = float(r.X_CO2_pct) / 100.0
    sm, sco, sch4, rep = closure(r)
    if X <= 0 or sm <= 0:
        return None
    inert = 0.0 if pd.isna(r.inert_frac) else float(r.inert_frac)
    y_co2 = (1.0 - inert) / (1.0 + float(r.H2_CO2))
    sty_print = float(r.STY_g_gcat_h) if pd.notna(r.STY_g_gcat_h) and pd.notna(r.STY_q) else None
    sty_mass = (float(r.GHSV_NL_gcat_h) * y_co2 * X * sm / VM * MW_MEOH) if pd.notna(r.GHSV_NL_gcat_h) else None
    gv = vol_ghsv(r.GHSV_raw) if pd.isna(r.GHSV_NL_gcat_h) else None
    sty_vol = (gv / (RHO_DEFAULT * 1000.0) * y_co2 * X * sm / VM * MW_MEOH) if gv else None
    gkey = (f"{float(r.GHSV_NL_gcat_h):.3g} NL/g/h" if pd.notna(r.GHSV_NL_gcat_h)
            else (f"{gv:g} h-1" if gv else str(r.GHSV_raw)))
    plot_read = "~" in (str(r.X_CO2_q), str(r.S_MeOH_q))
    return dict(doi=r.doi, entry=r.entry_label, catalyst=f"{r.catalyst_name} [{r.entry_label}]", T_C=float(r.T_K) - 273.15,
                P_bar=float(r.P_bar), h2_co2=float(r.H2_CO2), ghsv_key=gkey, X=X, SMeOH=sm, SCO=sco,
                SCH4=sch4, reported_S_sum=rep, other_products=rep < 0.95, plot_read=plot_read,
                sty_print=sty_print, sty_mass=sty_mass, sty_vol=sty_vol, gv=gv, y_co2=y_co2,
                source=r.data_source_type, location=r.primary_location)


def gothe_selfcheck(got: pd.DataFrame) -> pd.DataFrame:
    """Run the extracted Gothe et al. 2025 Table 4 candidates through the methanol model and compare with the
    frozen Table 4 costs (inert and recycled CO, 2 % purge)."""
    t4 = pd.read_csv(TABLE4)
    got = got.copy()
    got["row"] = got.entry.str.extract(r"row (\d+)").astype(float)
    check = []
    for r in got.itertuples():
        ref = t4.iloc[int(r.row) - 1]
        for tag, xco in (("inert", "inert"), ("rec", "recycled_central")):
            # every input from the Agent's extraction (STY printed per g Re, converted with the extracted loading)
            c = G.cost(dict(X=r.X, SMeOH=r.SMeOH, SCH4=r.SCH4, SCO=r.SCO), STY_per_g_cat=r.sty_print,
                       P_bar=r.P_bar, h2_co2=r.h2_co2, T_C=r.T_C, x_co=xco, purge=0.02)["cost_eur_t"]
            check.append(dict(id=ref.id, canonical_state=ref.canonical_state if isinstance(ref.canonical_state, str) else "",
                              treatment=tag, frozen=float(ref[f"{tag}_NPC_2pct"]), agent=float(c),
                              abs_diff=abs(float(c) - float(ref[f"{tag}_NPC_2pct"]))))
    return pd.DataFrame(check)


def gothe_candidates(records: pd.DataFrame = None) -> pd.DataFrame:
    d = read_records() if records is None else records
    d = d[d.doi == GOTHE_DOI].dropna(subset=REQUIRED)
    return pd.DataFrame([c for c in (candidate_row(r) for _, r in d.iterrows()) if c is not None])


# ---------------------------------------------------------------- candidate set ----------------------------------
PRINTED_SPREAD_MAX = 3.0   # printed STY / (F_CO2 X S) may vary by plot reading, not by more than this within a group


def group_basis(g):
    """One productivity basis per comparison group. The printed STY when every entry prints it, unless printed STY /
    conversion-derived productivity varies by more than PRINTED_SPREAD_MAX within the group (the paper's printed
    rates then contradict its own conversion and selectivity); the reference productivity is the mass-GHSV STY or,
    where the group states only a volumetric GHSV, the density-assumed volumetric-GHSV STY (the density is one
    factor for the whole group and cancels in the spread). Otherwise STY from the mass GHSV, then from the
    volumetric GHSV."""
    if g.sty_mass.notna().all():
        ref, ref_label = g.sty_mass, "STY from mass GHSV"
    elif g.sty_vol.notna().all():
        ref, ref_label = g.sty_vol, "STY from volumetric GHSV (assumed density)"
    else:
        ref, ref_label = None, None
    if g.sty_print.notna().all():
        if ref is not None:
            ratio = g.sty_print / ref
            if ratio.min() <= 0 or ratio.max() / ratio.min() > PRINTED_SPREAD_MAX:
                return ref_label + " (printed STY inconsistent with X*S*F)", ref
        return "printed STY", g.sty_print
    if ref is not None:
        return ref_label, ref
    if g.sty_print.notna().any():
        return "printed STY (partial)", g.sty_print
    return None, None


def build_candidates(records: pd.DataFrame = None) -> pd.DataFrame:
    """Every extracted record with conversion, methanol selectivity, T, P and H2/CO2 (and a dry CO2/H2 feed) -> one
    candidate operating point; comparison groups (paper, P, H2/CO2, space velocity) and the group STY basis."""
    d = read_records() if records is None else records
    d = d.dropna(subset=REQUIRED).copy()
    cand = pd.DataFrame([c for c in (candidate_row(r) for _, r in d.iterrows()) if c is not None])
    cand["group"] = (cand.doi + " | " + cand.P_bar.map("{:g} bar".format) + " | H2/CO2 "
                     + cand.h2_co2.map("{:.3g}".format) + " | " + cand.ghsv_key)
    parts = []
    for key, g in cand.groupby("group"):
        basis, sty = group_basis(g)
        g = g.copy()
        g["sty_basis"] = basis
        g["STY"] = sty
        parts.append(g)
    cand = pd.concat([p for p in parts if p.STY.notna().any()]).dropna(subset=["STY"])
    return cand[cand.STY > 0].reset_index(drop=True)


# ---------------------------------------------------------------- plant costs ------------------------------------
I_2PCT = int(np.argmin(np.abs(G.PURGES - 0.02)))
RHO_SCALES = {f"rho{rho:g}": RHO_DEFAULT / rho for rho in RHO_RANGE}   # STY per g scales with 1/density
ROW_KEYS = ["X", "SMeOH", "SCH4", "SCO", "STY", "P_bar", "h2_co2", "T_C"]


def _pick(cost, mask):
    if not mask.any():
        return np.nan, np.nan
    j = int(np.argmin(np.where(mask, cost, np.inf)))
    return float(cost[j]), float(G.PURGES[j])


def plant_costs(row: dict, sty_scales: dict = None) -> dict:
    """All plant-cost treatments of one candidate (dict with ROW_KEYS).

    For recycled CO (central rule) and inert CO, on the canonical purge grid:
      cost_<co>_opt                  primary: minimum over the eligible purge levels (equilibrium feasible and
                                     nonreactive fraction within the workbook limit); NaN when none is eligible
      cost_<co>_opt_eqonly           minimum over the equilibrium-feasible levels (no nonreactive limit)
      cost_<co>_opt_limit_ch4n2      diagnostic: equilibrium feasible and CH4 + N2 (not CO) within the limit
      cost_<co>_opt_unconstrained    minimum over every level (the earlier treatment)
      cost_<co>_2pct / _2pct_unconstrained   at 2 % purge: NaN when 2 % is not eligible / always evaluated
    plus the purges chosen, the number of eligible levels, and the nonreactive fraction and CO2-hydrogenation
    approach at the unconstrained optimum. sty_scales: {name: factor} for recycled-CO variants with STY x factor
    (eligibility does not depend on STY)."""
    c = dict(X=row["X"], SMeOH=row["SMeOH"], SCH4=row["SCH4"], SCO=row["SCO"])
    kw = dict(P_bar=row["P_bar"], h2_co2=row["h2_co2"], T_C=row["T_C"])
    out = {}
    for tag, rule in (("recycled", "recycled_central"), ("inert", "inert")):
        s = G.purge_sweep(c, STY_per_g_cat=row["STY"], x_co=rule, **kw)
        cost = np.asarray(s["cost_eur_t"], dtype=float)
        ok = G.eligible_purges(s)
        eq = np.asarray(s["equilibrium_feasible"])
        out[f"cost_{tag}_opt"], out[f"purge_{tag}_opt"] = _pick(cost, ok)
        out[f"cost_{tag}_opt_eqonly"], out[f"purge_{tag}_opt_eqonly"] = _pick(cost, eq)
        # diagnostic: the limit applied to CH4 + N2 only (recycled CO counted as a reactant, not as an inert)
        ch4n2 = np.asarray(s["methane_fraction"]) + np.asarray(s["n2_inlet_fraction"])
        out[f"cost_{tag}_opt_limit_ch4n2"] = _pick(cost, eq & (ch4n2 <= G.NONREACTIVE_MAX))[0]
        out[f"cost_{tag}_opt_unconstrained"], out[f"purge_{tag}_opt_unconstrained"] = _pick(cost, np.isfinite(cost))
        out[f"cost_{tag}_2pct"] = float(cost[I_2PCT]) if ok[I_2PCT] else np.nan
        out[f"cost_{tag}_2pct_unconstrained"] = float(cost[I_2PCT])
        out[f"n_eligible_{tag}"] = int(ok.sum())
        ju = int(np.nanargmin(cost))
        out[f"nonreactive_at_unconstrained_{tag}"] = float(s["nonreactive_fraction"][ju])
        out[f"co2_hyd_approach_at_unconstrained_{tag}"] = float(s["co2_hyd_approach"][ju])
        if tag == "recycled":
            for name, f in (sty_scales or {}).items():
                e = G.cost(c, purge=G.PURGES, x_co=s["x_co"], STY_per_g_cat=row["STY"] * f, **kw)
                out[f"cost_recycled_opt_{name}"] = _pick(np.asarray(e["cost_eur_t"], dtype=float), ok)[0]
    return out


def plant_costs_star(args):
    return plant_costs(*args)


# ---------------------------------------------------------------- group metrics ----------------------------------
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
    """Group metrics over the candidates with a finite cost in cost_col: an infeasible candidate (NaN cost) leaves
    both leaderboards of its group; groups with fewer than two remaining entries are not scored."""
    f = frame[np.isfinite(frame[cost_col].astype(float))]
    out = []
    for key, g in f.groupby("group"):
        if len(g) < 2:
            continue
        m = group_metrics(g, cost_col, up_col)
        m.update(group=key, doi=g.doi.iloc[0], basis=g.sty_basis.iloc[0])
        out.append(m)
    gm = pd.DataFrame(out)
    if gm.empty:
        return gm, {}
    papers = gm.groupby("doi").top1_mismatch.any()
    n_all = frame.groupby("group").size()
    s = dict(variant=label, groups=len(gm), papers=int(gm.doi.nunique()), entries=int(gm.n.sum()),
             candidates_infeasible=int((~np.isfinite(frame[cost_col].astype(float))).sum()),
             groups_lost_to_infeasibility=int(((n_all >= 2) & ~n_all.index.isin(gm.group)).sum()),
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


def bootstrap(gm, n=10_000, seed=20261006):
    """Paper-cluster bootstrap of the fraction of groups with a different winner (resample papers with
    replacement; every group of a drawn paper enters)."""
    per = gm.groupby("doi").top1_mismatch.agg(["sum", "count"])
    s, c = per["sum"].to_numpy(float), per["count"].to_numpy(float)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(per), size=(n, len(per)))
    frac = s[idx].sum(1) / c[idx].sum(1)
    lo, hi = np.percentile(frac, [2.5, 97.5])
    return dict(resamples=n, papers=len(per), fraction=float(s.sum() / c.sum()), ci95=[float(lo), float(hi)],
                ci95_of_groups=[float(lo * len(gm)), float(hi * len(gm))], seed=seed)
