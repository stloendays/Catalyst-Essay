"""Paper leaderboards versus plant-cost leaderboards for thermal ammonia-synthesis catalysts, 30 primary papers.

The ammonia analogue of analysis/meoh_literature_inversion_2026_10_05/run_literature_inversion.py.

Input: the extraction agent's normalized records (agent/nh3_field/out/records_normalized.csv), used as extracted.

Mapping (unchanged from analysis/nh3_supported_2026_10_06/run_supported_chain.py, whose functions are imported):
each measured catalyst of one model metal with a known metal content and a rate per g catalyst at its laboratory T, P
and NH3 fraction is inverted into an effective descriptor E_eff on its metal's side of the volcano (residual factor
alpha_res above the volcano top) and goes through the frozen 14,136-state library with its own metal content (bed
density 1,000 kg m-3; fused Fe 71.51 wt% and 2,500 kg m-3). Laboratory NH3 fraction: printed outlet, else rate / WHSV,
else the median of the set; entered at the same approach to equilibrium (Gillespie-Beattie). Primary set: 300-500 C,
steady thermal operation, outlet below 90 % of equilibrium, H2/N2 = 3 (the mapping's feed).

An entry without a space velocity takes the single one its paper reports at the same T, P and H2/N2, before the
laboratory NH3 fraction is computed. Comparison groups: one paper, one T, P, H2/N2 and space velocity (the comparison
the paper makes); pressures within 0.102 MPa and 6 % count as one setting (gauge and absolute values of the same run,
e.g. 2.0 and 2.1 MPa). One entry per catalyst (name, preparation and metal content) and group: printed main text > SI >
plot reading, then the longest time on stream.

Paper leaderboard: the NH3 synthesis rate on the basis the paper prints for the group (per g catalyst, or per g metal
when every rate of the group is printed per g metal); variants rank every group per g catalyst or per g metal.
Plant leaderboard: plant cost (USD/t NH3), no metal recovery; variant with 90 % Ru recovery.

Self-check: every row of the Humphreys 2021 chain (agent/nh3_supported/out/records.csv) is run through this script's
mapping function with the inputs of that chain; the costs must equal analysis/nh3_supported_2026_10_06/
supported_candidates.csv.

Outputs (this folder): candidates.csv, group_metrics.csv, selfcheck_supported.csv, summary.json.

    CatalystForge/.venv/python run_field_chain.py [--workers N]
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import re
import sys
from concurrent.futures import ProcessPoolExecutor
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
SUPPORTED = REPO / "analysis" / "nh3_supported_2026_10_06"
RECORDS = REPO / "agent" / "nh3_field" / "out" / "records_normalized.csv"
PAPER_SET = REPO / "agent" / "nh3_field" / "paper_set.txt"
H_RECORDS = REPO / "agent" / "nh3_supported" / "out" / "records.csv"

_argv, sys.argv = sys.argv, sys.argv[:1]          # run_supported_chain reads an optional harness path from argv
sys.path.insert(0, str(SUPPORTED))
import run_supported_chain as SC  # noqa: E402
sys.argv = _argv
hc = SC.hc

T_PRIMARY = SC.T_PRIMARY
FUSED = re.compile(r"fused|w[uü]stite|magnetite|industrial|commercial (?:fe|iron)|\bKM[- ]?\d|\bA301\b|\bZA-?5\b", re.I)
# A name that states a composition (a percentage, a support after "/", an added component) is a new catalyst made from
# or with the industrial one, e.g. "80% magnetite based industrial Fe catalyst-20% Ce0.8Sm0.2O2-d": it keeps its own
# metal content and the supported-bed density instead of the fused-iron formulation.
COMPOSITE = re.compile(r"\d\s*(?:wt\.?\s*)?%|/|\+")
NONSTEADY_MODES ={"chemical_looping", "plasma", "electric_field", "microwave", "photo"}
N_BOOT = 10_000

# ------------------------------------------------------------------ the mapping (one catalyst) ----------------------
_H = _RESP = None


def _init():
    global _H, _RESP
    if _H is None:
        _H, _RESP = SC.load_harness()


def map_catalyst(job: dict) -> dict:
    """One measured catalyst -> plant costs. Same arithmetic, in the same order, as run_supported_chain.main()."""
    _init()
    h, response = _H, _RESP
    metal, R, fused = job["metal"], job["R_umol_gcat_h"], job["fused"]
    w = 0.7151 if fused else job["w_pct"] / 100.0
    T_C, P_MPa = job["T_C"], job["P_MPa"]
    T_K, P_bar = T_C + 273.15, P_MPa * 10.0
    y_out = job["y_out"] if job["y_out"] is not None else job["y_default"]
    y_eq = SC.y_eq_exp(h, T_K, P_bar)
    y_lab = min(0.5 * y_out, 0.5 * y_eq) * SC.y_eq_model(h, T_K, P_bar) / y_eq
    cond = SC.lab_condition(h, T_K, P_bar, y_lab)
    log_target = math.log10(R * 1e-6 / 3600.0 / w)
    alpha = 10.0 ** log_target / (h.F_CAL * 10.0 ** cond.logtof(hc.EN0_CANON[metal]) / hc.MW[metal] / 1000.0)
    E_eff, la_res = SC.effective_descriptor(h, cond, metal, log_target)
    bed = 2500.0 if fused else SC.BED_SUPPORTED
    a_res = 10.0 ** la_res
    out = dict(key=job["key"], E_eff_eV=E_eff, log10_alpha_res=la_res, alpha=alpha, y_out=y_out, y_eq_exp=y_eq,
               cost_USD_t=None, T_opt_C=None, P_opt_bar=None, V_m3=None, cost_alpha_transfer=None,
               cost_bed500=None, cost_bed2500=None, cost_recovery90=None)
    best = SC.plant_cost(h, response, metal, a_res, w, bed, E=E_eff)
    if best is not None:
        out.update(cost_USD_t=best["total_cost"], T_opt_C=best["T_C"], P_opt_bar=best["P_bar"], V_m3=best["V_m3"])
    if job.get("sens", True):
        s = SC.plant_cost(h, response, metal, alpha, w, bed)
        out["cost_alpha_transfer"] = None if s is None else s["total_cost"]
        if not fused:
            for bd, k in zip(SC.BED_SENS, ("cost_bed500", "cost_bed2500")):
                s = SC.plant_cost(h, response, metal, a_res, w, bd, E=E_eff)
                out[k] = None if s is None else s["total_cost"]
        if metal in SC.PRECIOUS:
            s = SC.plant_cost(h, response, metal, a_res, w, bed, recovery=0.9, E=E_eff)
            out["cost_recovery90"] = None if s is None else s["total_cost"]
    return out


def run_jobs(jobs, workers):
    if workers <= 1:
        return [map_catalyst(j) for j in jobs]
    with ProcessPoolExecutor(max_workers=workers, initializer=_init) as ex:
        return list(ex.map(map_catalyst, jobs, chunksize=4))


# ------------------------------------------------------------------ self-check on the Humphreys chain ---------------
def supported_jobs():
    """The rows of run_supported_chain.main() that reach the plant model, with exactly its inputs."""
    rows, seen = [], {}
    for r in csv.DictReader(H_RECORDS.open(encoding="utf-8")):
        key = (r["T_C"], r["P_MPa"], r["rate_umol_g_h"], r["ref"])
        if r["rate_umol_g_h"] and key in seen:
            continue
        seen[key] = r
        rows.append(r)
    fnum = SC.fnum
    y_known = []
    for r in rows:
        R, whsv, out = fnum(r["rate_umol_g_h"]), fnum(r["whsv_mL_g_h"]), fnum(r["outlet_nh3_vol_pct"])
        r["_y_out"] = out / 100.0 if out is not None else (SC.y_out_from_rate(R, whsv) if R and whsv else None)
        if r["_y_out"] is not None:
            y_known.append(r["_y_out"])
    y_default = float(np.median(y_known))
    jobs = []
    for r in rows:
        metals = [m for m in r["active_metals"].split(";") if m]
        R, w, T_C, P_MPa = fnum(r["rate_umol_g_h"]), fnum(r["metal_wt_pct"]), fnum(r["T_C"]), fnum(r["P_MPa"])
        fused = r.get("fused_fe", "") == "True"
        if (len(metals) != 1 or metals[0] not in hc.EN0_CANON or R is None or R <= 0 or r["rate_unit_ok"] != "True"
                or (w is None and not fused) or T_C is None or P_MPa is None):
            continue
        jobs.append(dict(key=r["id"], metal=metals[0], R_umol_gcat_h=R, fused=fused, w_pct=w, T_C=T_C, P_MPa=P_MPa,
                         y_out=r["_y_out"], y_default=y_default))
    return jobs


def selfcheck(workers):
    ref = {r["id"]: r for r in csv.DictReader((SUPPORTED / "supported_candidates.csv").open(encoding="utf-8"))}
    res = run_jobs(supported_jobs(), workers)
    cols = ("cost_USD_t", "cost_alpha_transfer", "cost_bed500", "cost_bed2500", "cost_recovery90", "E_eff_eV", "alpha")
    rows, worst = [], 0.0
    for o in res:
        want = ref[o["key"]]
        for c in cols:
            a, b = o[c], want[c]
            if b in ("", None) and a is None:
                continue
            d = abs(float(a) - float(b)) if (a is not None and b not in ("", None)) else float("inf")
            rel = d / max(abs(float(b)), 1e-12) if b not in ("", None) else float("inf")
            worst = max(worst, rel)
            rows.append(dict(id=o["key"], catalyst=want["catalyst"], ref=want["ref"], field=c, supported=b, field_chain=a,
                             rel_diff=rel))
    return pd.DataFrame(rows), worst, len(res)


# ------------------------------------------------------------------ candidates from the extraction ------------------
def _f(x):
    return None if x is None or (isinstance(x, float) and math.isnan(x)) else float(x)


def _has(x):
    return not (x is None or (isinstance(x, float) and math.isnan(x)) or not str(x).strip())


def _name_key(s):
    return re.sub(r"[\s.\-_(),/:;%–—\[\]]+", "", str(s).lower())


def _rank(r):
    srcs = str(r.get("rate_src") or "")
    return 1 if ("plot" in srcs or r.get("rate_q") == "~") else (2 if srcs.startswith("SI") else 3)


def _tos(raw):
    m = re.match(r"\s*([\d.]+)", str(raw or ""))
    try:
        return float(m.group(1)) if m else -1.0
    except ValueError:
        return -1.0


def _sig(x, n=3):
    return f"{float(x):.{n}g}"


def build_candidates(d: pd.DataFrame):
    """Records -> candidate rows (status, inputs) without costs."""
    out = []
    y_known = []
    for r in d.to_dict("records"):
        metals = [m for m in str(r.get("active_metals") or "").split(";") if m and m != "nan"]
        R = _f(r.get("rate_umol_gcat_h"))
        w = _f(r.get("metal_wt_pct"))
        whsv = _f(r.get("WHSV_mL_g_h"))
        outlet = _f(r.get("outlet_nh3_vol_pct"))
        y = outlet / 100.0 if outlet is not None else (SC.y_out_from_rate(R, whsv) if R and whsv else None)
        name = str(r["catalyst_name"])
        # the commercial fused or wustite iron catalyst used as a reference, not a composite that contains it
        fused = (metals == ["Fe"] and bool(FUSED.search(name + " " + str(r.get("composition") or "")))
                 and not COMPOSITE.search(name) and not _has(r.get("support")))
        prep = r.get("preparation")
        prep = "" if prep is None or (isinstance(prep, float) and math.isnan(prep)) else str(prep)
        rec = dict(doi=r["doi"], entry=r["entry_label"], catalyst=name, preparation=prep, metal=";".join(metals),
                   metal_wt_pct=w, support=str(r.get("support")) if _has(r.get("support")) else "",
                   fused=fused, T_C=_f(r.get("T_C")), P_MPa=_f(r.get("P_MPa")), H2_N2=_f(r.get("H2_N2")), WHSV=whsv,
                   SV_raw=r.get("SV_raw"), outlet_pct=outlet, rate_umol_gcat_h=R,
                   rate_umol_gmetal_h=_f(r.get("rate_umol_gmetal_h")),
                   rate_printed_per_metal=bool(r.get("rate_cat_from_metal") in (True, "True")),
                   rate_src=r.get("rate_src"), rate_q=r.get("rate_q"), TOS=r.get("TOS_raw"),
                   operation_mode=r.get("operation_mode"), location=r.get("primary_location"),
                   y_out=y, y_source="printed outlet" if outlet is not None else ("rate / WHSV" if y is not None else ""),
                   status="")
        reasons = []
        if len(metals) != 1 or metals[0] not in hc.EN0_CANON:
            reasons.append("not a single model metal")
        if R is None or R <= 0:
            reasons.append("no rate per g catalyst")
        if w is None and not fused:
            reasons.append("metal content not given")
        if rec["T_C"] is None or rec["P_MPa"] is None:
            reasons.append("no T or P")
        if reasons:
            rec["status"] = "outside: " + "; ".join(reasons)
        rec["WHSV_filled"] = False
        out.append(rec)
    # An entry without a space velocity inherits the single one its paper reports at the same T, P and H2/N2 (the
    # condition stated once for a figure or table); its laboratory NH3 fraction then follows from rate / WHSV like its
    # neighbours', instead of the set median.
    df = pd.DataFrame(out)
    df["T_key"] = df.T_C.round(0)
    df["P_key"] = pressure_keys(df)
    df["H_key"] = df.H2_N2.map(lambda x: "3" if x is None or (isinstance(x, float) and math.isnan(x)) else _sig(x))
    for _, g in df.groupby(["doi", "T_key", "P_key", "H_key"]):
        svs = g.WHSV.dropna().unique()
        if len(svs) != 1:
            continue
        for i in g.index[g.WHSV.isna()]:
            rec = out[i]
            rec["WHSV"], rec["WHSV_filled"] = float(svs[0]), True
            if rec["y_out"] is None and rec["rate_umol_gcat_h"]:
                rec["y_out"] = SC.y_out_from_rate(rec["rate_umol_gcat_h"], rec["WHSV"])
                rec["y_source"] = "rate / WHSV (WHSV of the paper's comparison)"
    y_known = [r["y_out"] for r in out if not r["status"] and r["y_out"] is not None]
    y_default = float(np.median(y_known)) if y_known else 0.0043
    for rec in out:
        if rec["status"]:
            continue
        flags = []
        if str(rec["operation_mode"]) in NONSTEADY_MODES:
            flags.append("non-steady or non-thermal")
        if not (T_PRIMARY[0] <= rec["T_C"] <= T_PRIMARY[1]):
            flags.append("T outside 300-500 C")
        if rec["H2_N2"] is not None and abs(rec["H2_N2"] - SC.H2_N2) > 0.05:
            flags.append("H2/N2 not 3")
        rec["_flags"] = flags
    return out, y_default


def pressure_keys(c: pd.DataFrame) -> pd.Series:
    """One pressure per comparison: values within 0.102 MPa and 6 % are the same setting printed as gauge in one place
    and absolute in another (2.0 and 2.1 MPa, 5.0 and 5.1 MPa); 0.1 and 0.2 MPa stay apart."""
    key = pd.Series("", index=c.index, dtype=object)
    for _, g in c.dropna(subset=["P_MPa"]).groupby(["doi", c.T_C.round(0)]):
        ref = None
        for i, p in g.P_MPa.sort_values().items():
            if ref is None or not (p - ref <= 0.102 and (p - ref) / ref <= 0.06):
                ref = p
            key.at[i] = _sig(ref)
    return key


def assign_groups(c: pd.DataFrame) -> pd.DataFrame:
    c = c.copy()
    c["T_key"] = c.T_C.round(0)
    c["P_key"] = pressure_keys(c)
    c["H_key"] = c.H2_N2.map(lambda x: "3" if x is None or (isinstance(x, float) and math.isnan(x)) else _sig(x))
    c["SV_key"] = c.WHSV.map(lambda x: None if x is None or (isinstance(x, float) and math.isnan(x)) else _sig(x))
    c["SV_filled"] = False
    for (doi, T, P, H), g in c.groupby(["doi", "T_key", "P_key", "H_key"]):
        svs = g.SV_key.dropna().unique()
        if len(svs) == 1:
            miss = g.index[g.SV_key.isna()]
            c.loc[miss, "SV_key"] = svs[0]
            c.loc[miss, "SV_filled"] = True
    c["SV_key"] = c.SV_key.fillna("SV not given")
    c["group"] = (c.doi + " | " + c.T_key.map("{:g} C".format) + " | " + c.P_key + " MPa | H2/N2 " + c.H_key
                  + " | " + c.SV_key.map(lambda s: s if s == "SV not given" else s + " mL/g/h"))
    # one entry per catalyst and group
    # a catalyst is its name, preparation and metal content (Kitano 2012 Table 1 names four Ru loadings alike)
    c["_nk"] = (c.catalyst + "|" + c.preparation + "|" + c.metal_wt_pct.map(lambda w: "" if pd.isna(w) else f"{w:g}")
                ).map(_name_key)
    c["_rank"] = c.apply(lambda r: _rank(r), axis=1)
    c["_tos"] = c.TOS.map(_tos)
    c = c.sort_values(["group", "_nk", "_rank", "_tos"], ascending=[True, True, False, False])
    dup_name = c.duplicated(["group", "_nk"])
    # one entry per measurement and group: the same metal, metal content and rate (3 significant figures) in one group
    # is one measurement printed twice (text and SI figure, or a catalyst named two ways), whatever the name
    c["_mk"] = (c.metal + "|" + c.fused.map(str) + "|"
                + c.metal_wt_pct.map(lambda w: "" if pd.isna(w) else f"{w:g}") + "|"
                + c.rate_umol_gcat_h.map(lambda x: _sig(x, 3)))
    kept = c[~dup_name].sort_values(["group", "_mk", "_rank", "_tos"], ascending=[True, True, False, False])
    dup_meas = kept.index[kept.duplicated(["group", "_mk"])]
    c["duplicate_in_group"] = np.where(dup_name, "same catalyst", "")
    c.loc[dup_meas, "duplicate_in_group"] = "same measurement"
    return c


def group_metrics(g, cost_col, up_col):
    g = g.sort_values(up_col, ascending=False)
    up_best = g[up_col].max()
    up_winners = set(g.index[g[up_col] >= up_best * (1 - 1e-12)])
    econ_idx = g[cost_col].idxmin()
    c_best = g[cost_col].min()
    c_up = g.loc[list(up_winners), cost_col].min()
    n = len(g)
    pairs = list(combinations(g.index, 2))
    inv = sum(1 for a, b in pairs if (g.at[a, up_col] - g.at[b, up_col]) * (g.at[b, cost_col] - g.at[a, cost_col]) < 0)
    rho = float(spearmanr(g[up_col], -g[cost_col]).statistic) if n >= 3 and g[up_col].nunique() > 1 else None
    pw = g.loc[sorted(up_winners)[0]]
    ew = g.loc[econ_idx]
    if econ_idx in up_winners:
        kind = ""
    elif bool(pw.fused) != bool(ew.fused):
        kind = "fused-Fe reference vs supported catalyst"
    elif pw.metal != ew.metal:
        kind = "different metal"
    elif not bool(pw.fused) and abs(float(pw.metal_wt_pct) - float(ew.metal_wt_pct)) > 1e-9:
        kind = "same metal, different metal content"
    else:
        kind = "same metal and metal content"
    # the same support: the same host cations, anions (O, N, H) and stoichiometry ignored, so BaTiO2.5H0.5 and
    # BaTiO2.35H0.65, or BaCeO3-xNy and BaCeO3-xNyHz, are one support
    # (x, y, z after a symbol are stoichiometry variables, as in NyHz)
    fam = lambda x: (frozenset(re.findall(r"[A-Z][a-z]?", re.sub(r"(?<=[A-Z])[xyz]", "", str(x)))) - {"O", "N", "H"}  # noqa: E731
                     if _has(x) else frozenset())
    same_support = bool(fam(pw.support)) and fam(pw.support) == fam(ew.support)
    return dict(n=n, top1_mismatch=econ_idx not in up_winners, mismatch_kind=kind, regret=(c_up - c_best) / c_best,
                paper_winner_metal=pw.metal, plant_winner_metal=ew.metal, paper_winner_support=pw.support,
                plant_winner_support=ew.support, same_support_family=same_support,
                paper_winner=g.loc[sorted(up_winners)[0], "catalyst"], plant_winner=g.at[econ_idx, "catalyst"],
                paper_winner_cost=c_up, plant_winner_cost=c_best,
                plant_rank_of_paper_winner=int((g[cost_col] < c_up - 1e-9).sum()) + 1,
                pairs=len(pairs), inversions=inv, spearman=rho)


def aggregate(frame, cost_col="cost_USD_t", up_col="paper_rate", label="", boot=False, seed=20261006):
    rows = []
    for key, g in frame.dropna(subset=[cost_col, up_col]).groupby("group"):
        if len(g) < 2:
            continue
        m = group_metrics(g, cost_col, up_col)
        m.update(group=key, doi=g.doi.iloc[0], paper_basis=g.paper_basis.iloc[0], metals=";".join(sorted(set(g.metal))))
        rows.append(m)
    gm = pd.DataFrame(rows)
    if gm.empty:
        return gm, dict(variant=label, groups=0)
    mm = gm[gm.top1_mismatch]
    sp = gm.spearman.dropna()
    s = dict(variant=label, groups=len(gm), papers=int(gm.doi.nunique()), entries=int(gm.n.sum()),
             top1_mismatch_groups=int(gm.top1_mismatch.sum()), top1_mismatch_fraction=float(gm.top1_mismatch.mean()),
             top1_mismatch_groups_regret_ge_1pct=int((gm.top1_mismatch & (gm.regret >= 0.01)).sum()),
             papers_with_mismatch=int(gm.groupby("doi").top1_mismatch.any().sum()),
             paper_weighted_mismatch_fraction=float(gm.groupby("doi").top1_mismatch.mean().mean()),
             regret_median_mismatched=float(mm.regret.median()) if len(mm) else 0.0,
             regret_max=float(gm.regret.max()), regret_median_all=float(gm.regret.median()),
             pairwise_inversions=f"{int(gm.inversions.sum())}/{int(gm.pairs.sum())}",
             pairwise_inversion_fraction=float(gm.inversions.sum() / gm.pairs.sum()),
             spearman_median_groups_n_ge_3=float(sp.median()) if len(sp) else None, groups_n_ge_3=int(len(sp)),
             mismatch_kinds={k: dict(groups=int(len(x)), papers=int(x.doi.nunique()),
                                     regret_median=float(x.regret.median()), regret_max=float(x.regret.max()))
                             for k, x in mm.groupby("mismatch_kind")})
    dm = mm[mm.mismatch_kind == "different metal"]
    if len(dm):
        s["different_metal_split"] = {
            lab: dict(groups=int(len(x)), papers=int(x.doi.nunique()),
                      regret_median=float(x.regret.median()) if len(x) else None,
                      regret_max=float(x.regret.max()) if len(x) else None)
            for lab, x in (("Fe plant winner, same support family", dm[(dm.plant_winner_metal == "Fe") & dm.same_support_family]),
                           ("Fe plant winner, other support", dm[(dm.plant_winner_metal == "Fe") & ~dm.same_support_family]),
                           ("plant winner not Fe", dm[dm.plant_winner_metal != "Fe"]))}
    s["paper_basis_groups"] = {k: int(v) for k, v in gm.paper_basis.value_counts().items()}
    if boot:
        rng = np.random.default_rng(seed)
        per = gm.groupby("doi").top1_mismatch.agg(["sum", "count"])
        k, n = per["sum"].to_numpy(), per["count"].to_numpy()
        idx = rng.integers(0, len(per), size=(N_BOOT, len(per)))
        frac = k[idx].sum(1) / n[idx].sum(1)
        pw = gm.groupby("doi").top1_mismatch.mean().to_numpy()[idx].mean(1)
        s["bootstrap_papers"] = dict(resamples=N_BOOT, seed=seed, mismatch_fraction_ci95=[float(np.percentile(frac, 2.5)),
                                                                                         float(np.percentile(frac, 97.5))],
                                     paper_weighted_ci95=[float(np.percentile(pw, 2.5)), float(np.percentile(pw, 97.5))])
    return gm, s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=1)   # each worker holds the 130 MB response surface; RAM is shared
    ap.add_argument("--skip-selfcheck", action="store_true")
    args = ap.parse_args()
    sys.path.insert(0, str(REPO / "agent"))
    from selfcheck_gate import require
    require()          # ACSA scores new candidates only after reproducing all three hand-built cases

    summary = {}
    if not args.skip_selfcheck:
        chk, worst, n = selfcheck(args.workers)
        chk.to_csv(HERE / "selfcheck_supported.csv", index=False, float_format="%.12g")
        summary["selfcheck_supported_chain"] = dict(catalysts=n, values_compared=len(chk), max_rel_diff=worst,
                                                    pass_=bool(worst < 1e-9))
        print("self-check against supported_candidates.csv:", summary["selfcheck_supported_chain"], flush=True)
        if worst >= 1e-9:
            raise SystemExit("self-check failed: the field chain does not reproduce the Humphreys chain")

    d = pd.read_csv(RECORDS, keep_default_na=False, na_values=[""])
    cands, y_default = build_candidates(d)
    jobs = [dict(key=i, metal=c["metal"], R_umol_gcat_h=c["rate_umol_gcat_h"], fused=c["fused"], w_pct=c["metal_wt_pct"],
                 T_C=c["T_C"], P_MPa=c["P_MPa"], y_out=c["y_out"], y_default=y_default)
            for i, c in enumerate(cands) if not c["status"]]
    print(f"{len(cands)} records, {len(jobs)} mapped, y_default {y_default:.5f}; running on {args.workers} workers", flush=True)
    res = {o["key"]: o for o in run_jobs(jobs, args.workers)}
    for i, c in enumerate(cands):
        if c["status"]:
            continue
        o = res[i]
        c.update({k: v for k, v in o.items() if k != "key"})
        flags = list(c.pop("_flags"))
        if c["y_out"] >= 0.9 * c["y_eq_exp"] and c["y_source"]:
            flags.append("outlet near equilibrium")
        if not c["y_source"]:
            flags.append("outlet NH3 assumed (median)")
        primary = not flags or flags == ["outlet NH3 assumed (median)"]
        c["status"] = ("primary" if primary else "flagged") + ("" if not flags else ": " + "; ".join(flags))
        if c["cost_USD_t"] is None:
            c["status"] += "; infeasible within bed limit"
    for c in cands:
        c.pop("_flags", None)
    cand = pd.DataFrame(cands)
    fe_cost = float(json.loads((SC.RUN / "results.json").read_text(encoding="utf-8"))["deterministic"]["metals"]["Fe"]
                    ["feasible"]["total_cost"])

    prim = cand[cand.status.str.startswith("primary") & cand.cost_USD_t.notna()].copy()
    grouped = assign_groups(prim)
    dedup = grouped.duplicate_in_group.value_counts().to_dict()
    prim = grouped[grouped.duplicate_in_group == ""].copy()
    # the paper's own basis per group: per g metal when every rate of the group is printed per g metal
    basis = prim.groupby("group").rate_printed_per_metal.transform("all")
    prim["paper_basis"] = np.where(basis, "per g metal", "per g catalyst")
    prim["paper_rate"] = np.where(basis, prim.rate_umol_gmetal_h, prim.rate_umol_gcat_h)
    prim["rate_per_gmetal"] = prim.rate_umol_gcat_h / (np.where(prim.fused, 71.51, prim.metal_wt_pct) / 100.0)
    prim["plot_read"] = prim.apply(_rank, axis=1) == 1

    gm, primary = aggregate(prim, label="primary: paper's own rate basis, plant cost without metal recovery", boot=True)
    variants = {}
    variants["per_g_catalyst_leaderboard"] = aggregate(prim, up_col="rate_umol_gcat_h", label="rate per g catalyst",
                                                       boot=True)[1]
    variants["per_g_metal_leaderboard"] = aggregate(prim, up_col="rate_per_gmetal", label="rate per g metal", boot=True)[1]
    variants["Ru_recovery_90pct"] = aggregate(prim.assign(cost_rec=prim.cost_recovery90.fillna(prim.cost_USD_t)),
                                              cost_col="cost_rec", label="90 % Ru recovery", boot=True)[1]
    variants["printed_values_only"] = aggregate(prim[~prim.plot_read], label="no plot readings", boot=True)[1]
    variants["bed_density_500"] = aggregate(prim.assign(c5=prim.cost_bed500.where(~prim.fused, prim.cost_USD_t)),
                                            cost_col="c5", label="bed density 500 kg/m3")[1]
    variants["bed_density_2500"] = aggregate(prim.assign(c25=prim.cost_bed2500.where(~prim.fused, prim.cost_USD_t)),
                                             cost_col="c25", label="bed density 2,500 kg/m3")[1]
    variants["without_fused_Fe_references"] = aggregate(prim[~prim.fused], label="commercial fused-Fe reference catalysts removed",
                                                        boot=True)[1]
    variants["P_ge_5MPa"] = aggregate(prim[prim.P_MPa >= 5.0], label="measured at >= 5 MPa", boot=True)[1]
    variants["outlet_known_only"] = aggregate(prim[~prim.status.str.contains("assumed")], label="outlet NH3 known")[1]
    variants["alpha_transfer"] = aggregate(prim, cost_col="cost_alpha_transfer",
                                           label="constant multiplier on the metal's own TOF")[1]
    pooled = prim.copy()
    pooled["group"] = (pooled.doi + " | " + pooled.P_key + " MPa | H2/N2 " + pooled.H_key + " | " + pooled.SV_key)
    pooled = pooled.sort_values(["group", "_nk", "T_C"]).copy()
    variants["T_pooled_groups"] = aggregate(pooled, up_col="rate_umol_gcat_h",
                                            label="groups pooled over T (methanol grouping), per g catalyst")[1]
    BIG = gm.groupby("doi").size().idxmax() if not gm.empty else None
    variants["without_paper_with_most_groups"] = aggregate(prim[prim.doi != BIG], label=f"without {BIG}")[1]

    # outputs
    keep = ["doi", "entry", "catalyst", "preparation", "metal", "metal_wt_pct", "fused", "T_C", "P_MPa", "H2_N2", "WHSV", "SV_raw",
            "outlet_pct", "rate_umol_gcat_h", "rate_umol_gmetal_h", "rate_printed_per_metal", "rate_src", "rate_q",
            "TOS", "operation_mode", "y_out", "y_source", "y_eq_exp", "E_eff_eV", "log10_alpha_res", "alpha",
            "cost_USD_t", "cost_recovery90", "cost_bed500", "cost_bed2500", "cost_alpha_transfer", "T_opt_C",
            "P_opt_bar", "V_m3", "status", "location"]
    keep.insert(keep.index("SV_raw"), "WHSV_filled")
    keep.insert(keep.index("metal_wt_pct") + 1, "support")
    allc = cand[keep].merge(grouped[["doi", "entry", "group", "duplicate_in_group"]], on=["doi", "entry"], how="left")
    allc = allc.merge(prim[["doi", "entry", "paper_basis", "paper_rate", "SV_filled"]], on=["doi", "entry"], how="left")
    allc.to_csv(HERE / "candidates.csv", index=False, float_format="%.6g")
    gm.to_csv(HERE / "group_metrics.csv", index=False, float_format="%.6g")
    st = cand.status.fillna("")
    reasons = {}
    for s_ in st[st.str.startswith("outside")]:
        for x in s_[len("outside: "):].split("; "):
            reasons[x] = reasons.get(x, 0) + 1
    paper_set = [l.split("#")[0].split()[0] for l in PAPER_SET.read_text(encoding="utf-8").splitlines()
                 if l.split("#")[0].strip()]
    summary.update(
        papers_in_set=len(paper_set), records_in=int(len(d)), papers_with_records=int(d.doi.nunique()),
        mapped=int(len(jobs)), primary_with_cost=int((cand.status.str.startswith("primary") & cand.cost_USD_t.notna()).sum()),
        flagged=int(st.str.startswith("flagged").sum()), outside=int(st.str.startswith("outside").sum()),
        outside_reasons=reasons, y_default_median=y_default, Fe_benchmark_USD_t=fe_cost,
        primary_entries_after_dedup=int(len(prim)), papers_with_primary=int(prim.doi.nunique()),
        removed_as_duplicate={"same catalyst (name, preparation, metal content)": int(dedup.get("same catalyst", 0)),
                              "same measurement (metal, metal content, rate to 3 s.f.)": int(dedup.get("same measurement", 0)),
                              "groups_with_same_measurement": int(grouped[grouped.duplicate_in_group == "same measurement"]
                                                                  .group.nunique())},
        fused_reference_entries_primary=int(prim.fused.sum()),
        primary_below_Fe=int((prim.cost_USD_t < fe_cost).sum()),
        primary=primary, variants=variants)
    (HERE / "summary.json").write_text(json.dumps(summary, indent=1, default=float) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=1, default=float))


if __name__ == "__main__":
    main()
