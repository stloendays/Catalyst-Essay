"""Paper STY leader vs plant-cost leader with catalyst replacement charged per tonne of inventory at each candidate's
own composition-based price.

Copy of the logic of analysis/meoh_literature_inversion_2026_10_05/run_literature_inversion.py (candidate
construction, group STY basis, group_metrics, aggregate), with the plant cost taken from the frozen
meoh_general_model.economics(..., cat_price_eur_kg=, cat_life_y=) on the canonical purge grid (recycled CO, central
RWGS rule, entry-optimal purge). The frozen model and the original script are not edited.

Order of work:
  1. rebuild the 991 candidates and check them against the frozen literature_candidates.csv;
  2. catalyst term off: must reproduce 33/83 and 1019/8458 (the frozen headline);
  3. variants (VARIANTS); primary = composition price (catalyst_prices.py), 3-year life;
  4. paper-cluster bootstrap (10,000 resamples of papers) of the primary and of the term-off headline;
  5. Gothe et al. 2025 Table 4 self-check with the term off, and the Re/TiO2 prices and canonical states with it on.

Parallel: multiprocessing over candidates, CATCOST_WORKERS (default 4).
Outputs: catalyst_prices.csv, element_prices.csv, candidate_costs.csv, group_metrics.csv, group_changes.csv,
selfcheck_gothe.csv, summary.json.
"""
from __future__ import annotations

import json
import os
import sys
import time
from itertools import combinations
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
INV = REPO / "analysis" / "meoh_literature_inversion_2026_10_05"
sys.path.insert(0, str(REPO / "data" / "meoh"))
sys.path.insert(0, str(INV))
sys.path.insert(0, str(HERE))
import meoh_general_model as G  # noqa: E402
from meoh_candidates import GOTHE_DOI, REQUIRED, candidate_row, gothe_selfcheck, read_records  # noqa: E402

import catalyst_prices as CP  # noqa: E402

WORKERS = int(os.environ.get("CATCOST_WORKERS", "4"))
N_BOOT = 10_000
RECOVERY = 0.95

# name -> (price column or uniform EUR/kg, life in years, precious-metal recovery fraction)
VARIANTS = {
    "off": (None, None, 0.0),
    "composition_3y": ("price_eur_kg", 3.0, 0.0),                 # primary (anchor life, Campos 2022)
    "composition_1y": ("price_eur_kg", 1.0, 0.0),                 # Perez-Fortes 2016 yearly replacement
    "composition_4y": ("price_eur_kg", 4.0, 0.0),                 # Nieminen 2019, Sollai 2023
    "composition_6y": ("price_eur_kg", 6.0, 0.0),                 # Dieterich 2020 upper industrial life
    "composition_3y_recovery95": ("price_eur_kg", 3.0, RECOVERY),  # precious metals recovered at end of life
    "composition_pf_base_3y": ("price_pf_base_eur_kg", 3.0, 0.0),  # base cost from Perez-Fortes 95.24 EUR/kg
    "composition_pf_base_1y": ("price_pf_base_eur_kg", 1.0, 0.0),
    "uniform_cza_18.1_3y": (CP.CZA_ANCHOR_EUR_KG, 3.0, 0.0),      # benchmark variant (32/83)
    "uniform_pf_95.24_3y": (CP.PEREZ_FORTES_EUR_KG, 3.0, 0.0),
}
PRIMARY = "composition_3y"


# ---------------------------------------------------------------- candidates (copied logic) -------------------
def build_candidates():
    d = read_records()
    d = d.dropna(subset=REQUIRED).copy()
    rows = [c for c in (candidate_row(r) for _, r in d.iterrows()) if c is not None]
    cand = pd.DataFrame(rows)
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


PRINTED_SPREAD_MAX = 3.0


def group_basis(g):
    if g.sty_print.notna().all():
        ratio = g.sty_print / g.sty_mass
        if g.sty_mass.notna().all() and (ratio.min() <= 0 or ratio.max() / ratio.min() > PRINTED_SPREAD_MAX):
            return "STY from mass GHSV (printed STY inconsistent with X*S*F)", g.sty_mass
        return "printed STY", g.sty_print
    if g.sty_mass.notna().all():
        return "STY from mass GHSV", g.sty_mass
    if g.sty_vol.notna().all():
        return "STY from volumetric GHSV (assumed density)", g.sty_vol
    if g.sty_print.notna().any():
        return "printed STY (partial)", g.sty_print
    return None, None


# ---------------------------------------------------------------- plant cost -----------------------------------
def _one(args):
    """Primary plant cost (recycled CO, central rule, entry-optimal purge) for every variant of one candidate. The
    CO-recycle window depends only on the loop, so it is solved once and passed as numbers."""
    row, charges = args
    c = (row["X"], row["SMeOH"], row["SCH4"], row["SCO"])
    kw = dict(STY_per_g_cat=row["STY"], P_bar=row["P_bar"], h2_co2=row["h2_co2"], T_C=row["T_C"])
    x = G.resolve_x_co("recycled_central", *c, row["h2_co2"], G.PURGES, row["T_C"], row["P_bar"])
    out = {}
    for name, (price, life) in charges.items():
        extra = {} if price is None else dict(cat_price_eur_kg=price, cat_life_y=life)
        e = G.economics(*c, purge=G.PURGES, x_co=x, **kw, **extra)
        j = int(np.nanargmin(e["cost_eur_t"]))
        out[name] = (float(e["cost_eur_t"][j]), float(G.PURGES[j]), float(e["cat_repl_eur_t"]),
                     float(e["catalyst_t"]))
    return out


def charges_for(prices: pd.DataFrame):
    out = []
    for p in prices.itertuples():
        ch = {}
        for name, (col, life, rec) in VARIANTS.items():
            if col is None:
                ch[name] = (None, None)
                continue
            price = getattr(p, col) if isinstance(col, str) else float(col)
            price -= rec * p.precious_value_eur_kg
            ch[name] = (price, life)
        out.append(ch)
    return out


# ---------------------------------------------------------------- group metrics (copied verbatim) --------------
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
             pairwise_inversion_fraction=float(gm.inversions.sum() / gm.pairs.sum()))
    return gm, s


def bootstrap(gm, n=N_BOOT, seed=20261006):
    """Paper-cluster bootstrap of the fraction of groups with a different winner (resample papers with
    replacement; every group of a drawn paper enters)."""
    per = gm.groupby("doi").top1_mismatch.agg(["sum", "count"])
    s, c = per["sum"].to_numpy(float), per["count"].to_numpy(float)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(per), size=(n, len(per)))
    frac = s[idx].sum(1) / c[idx].sum(1)
    lo, hi = np.percentile(frac, [2.5, 97.5])
    return dict(resamples=n, papers=len(per), fraction=float(s.sum() / c.sum()), ci95=[float(lo), float(hi)],
                ci95_of_83=[float(lo * len(gm)), float(hi * len(gm))], seed=seed)


# ---------------------------------------------------------------- self-check ------------------------------------
def gothe_with_catalyst(got: pd.DataFrame, prices: pd.DataFrame, life=3.0):
    """Table 4 path (2 % purge, inert and recycled CO, printed STY per g cat) with the catalyst term on."""
    t4 = pd.read_csv(CP.REPO / "analysis" / "meoh_general_model_2026_10_05" / "table4_candidate_results.csv")
    pr = prices.set_index("entry")
    rows = []
    for r in got.itertuples():
        ref = t4.iloc[int(r.row) - 1]
        price = float(pr.at[r.entry, "price_eur_kg"])
        for tag, xco in (("inert", "inert"), ("rec", "recycled_central")):
            kw = dict(STY_per_g_cat=r.sty_print, P_bar=r.P_bar, h2_co2=r.h2_co2, T_C=r.T_C, x_co=xco, purge=0.02)
            c = dict(X=r.X, SMeOH=r.SMeOH, SCH4=r.SCH4, SCO=r.SCO)
            off = float(G.cost(c, **kw)["cost_eur_t"])
            on = G.cost(c, cat_price_eur_kg=price, cat_life_y=life, **kw)
            rows.append(dict(id=ref.id, entry=r.entry, catalyst=r.catalyst,
                             canonical_state=ref.canonical_state if isinstance(ref.canonical_state, str) else "",
                             treatment=tag, price_eur_kg=price, catalyst_t=float(on["catalyst_t"]),
                             frozen=float(ref[f"{tag}_NPC_2pct"]), off=off, on=float(on["cost_eur_t"]),
                             cat_repl_eur_t=float(on["cat_repl_eur_t"])))
    return pd.DataFrame(rows)


def main():
    t0 = time.time()
    print(CP.check_frozen_prices())
    cand = build_candidates()
    frozen = pd.read_csv(INV / "literature_candidates.csv")
    key = ["group", "entry"]
    a = cand.set_index(key).sort_index()
    b = frozen.set_index(key).sort_index()
    assert len(a) == len(b) == 991 and (a.index == b.index).all(), "candidate set differs from the frozen CSV"
    assert np.allclose(a.loc[b.index, "STY"], b.STY, rtol=1e-5), "STY basis differs from the frozen CSV"

    prices = CP.build(cand)
    CP.element_table().to_csv(HERE / "element_prices.csv", index=False, float_format="%.6g")
    prices.to_csv(HERE / "catalyst_prices.csv", index=False, float_format="%.6g")

    rows = cand[["X", "SMeOH", "SCH4", "SCO", "STY", "P_bar", "h2_co2", "T_C"]].to_dict("records")
    with Pool(WORKERS) as pool:
        res = pool.map(_one, list(zip(rows, charges_for(prices))), chunksize=4)
    for name in VARIANTS:
        cand[f"cost_{name}"] = [r[name][0] for r in res]
        cand[f"purge_{name}"] = [r[name][1] for r in res]
        cand[f"catrepl_{name}"] = [r[name][2] for r in res]
    cand["catalyst_t"] = [r["off"][3] for r in res]
    cand["price_eur_kg"] = prices.price_eur_kg.to_numpy()
    cand["price_flag"] = prices.flag.to_numpy()

    gms, summ = {}, {}
    for name in VARIANTS:
        gms[name], summ[name] = aggregate(cand, f"cost_{name}", label=name)
    froz = json.loads((INV / "summary.json").read_text(encoding="utf-8"))["primary"]
    rel = np.abs(cand.set_index(key).sort_index().cost_off / b.cost_recycled_opt - 1)
    check = dict(max_rel_diff_off_vs_frozen_costs=float(rel.max()),
                 off_top1=f"{summ['off']['top1_mismatch_groups']}/{summ['off']['groups']}",
                 frozen_top1=f"{froz['top1_mismatch_groups']}/{froz['groups']}",
                 off_inversions=summ["off"]["pairwise_inversions"], frozen_inversions=froz["pairwise_inversions"])
    assert check["off_top1"] == check["frozen_top1"] == "33/83", check
    assert check["off_inversions"] == check["frozen_inversions"] == "1019/8458", check

    base = gms["off"].set_index("group")
    for name, gm in gms.items():
        g = gm.set_index("group")
        summ[name]["groups_flipped_vs_off"] = int((g.top1_mismatch != base.loc[g.index, "top1_mismatch"]).sum())
        summ[name]["groups_economic_winner_changed"] = int((g.economic_winner != base.loc[g.index, "economic_winner"]).sum())

    # which groups change verdict under the primary, and why
    p = gms[PRIMARY].set_index("group")
    price_of = dict(zip(cand.catalyst, cand.price_eur_kg))
    flag_of = dict(zip(cand.catalyst, cand.price_flag))
    cat_t = dict(zip(cand.catalyst, cand.catalyst_t))
    changes = []
    for k in p.index:
        if p.at[k, "top1_mismatch"] == base.at[k, "top1_mismatch"] and p.at[k, "economic_winner"] == base.at[k, "economic_winner"]:
            continue
        up, w0, w1 = p.at[k, "upstream_winner"], base.at[k, "economic_winner"], p.at[k, "economic_winner"]
        changes.append(dict(group=k, doi=p.at[k, "doi"], mismatch_off=bool(base.at[k, "top1_mismatch"]),
                            mismatch_primary=bool(p.at[k, "top1_mismatch"]), sty_winner=up,
                            plant_winner_off=w0, plant_winner_primary=w1,
                            price_sty_winner=price_of[up], price_plant_winner_off=price_of[w0],
                            price_plant_winner_primary=price_of[w1],
                            catalyst_t_sty_winner=cat_t[up], catalyst_t_plant_winner_off=cat_t[w0],
                            catalyst_t_plant_winner_primary=cat_t[w1],
                            flags=";".join(sorted({flag_of[up], flag_of[w0], flag_of[w1]} - {""})),
                            regret_off=base.at[k, "regret"], regret_primary=p.at[k, "regret"]))
    changes = pd.DataFrame(changes)

    # self-check
    got = cand[cand.doi == GOTHE_DOI].copy()
    chk = gothe_selfcheck(got)
    got["row"] = got.entry.str.extract(r"row (\d+)").astype(float)
    on = gothe_with_catalyst(got, prices[prices.doi == GOTHE_DOI])
    canon = on[(on.canonical_state != "") & (on.treatment == "inert")]

    out_cols = (["group", "doi", "entry", "catalyst", "T_C", "P_bar", "h2_co2", "X", "SMeOH", "SCO", "SCH4",
                 "sty_basis", "STY", "catalyst_t", "price_eur_kg", "price_flag"]
                + [f"cost_{v}" for v in VARIANTS] + [f"purge_{v}" for v in VARIANTS] + [f"catrepl_{v}" for v in VARIANTS])
    cand.sort_values(["group", "STY"], ascending=[True, False])[out_cols].to_csv(
        HERE / "candidate_costs.csv", index=False, float_format="%.6g")
    gp = gms[PRIMARY].merge(gms["off"][["group", "top1_mismatch", "economic_winner", "regret"]], on="group",
                            suffixes=("", "_off"))
    gp.to_csv(HERE / "group_metrics.csv", index=False, float_format="%.6g")
    changes.to_csv(HERE / "group_changes.csv", index=False, float_format="%.6g")
    on.merge(chk[["id", "treatment", "abs_diff"]], on=["id", "treatment"]).to_csv(
        HERE / "selfcheck_gothe.csv", index=False, float_format="%.10g")

    fl = prices.flag.replace("", "parsed")
    summary = dict(
        check=check,
        price_model=dict(usd_per_eur_2025=CP.USD_PER_EUR_2025, base_eur_kg=CP.BASE_EUR_KG,
                         base_pf_eur_kg=CP.BASE_PF_EUR_KG, cza_commercial=CP.CZA_COMMERCIAL,
                         cza_price_eur_kg=CP.price_table(CP.CZA_COMMERCIAL)["price_eur_kg"]),
        parse_coverage=dict(candidates=int(len(prices)), flags=fl.value_counts().to_dict(),
                            unparsed_catalysts=int(prices[prices.flag == "unparsed"].drop_duplicates(
                                ["doi", "catalyst_name"]).shape[0]),
                            distinct_catalysts=int(prices.drop_duplicates(["doi", "catalyst_name"]).shape[0])),
        price_quantiles_eur_kg={q: float(prices.price_eur_kg.quantile(q)) for q in (0.0, 0.1, 0.25, 0.5, 0.75, 0.9, 1.0)},
        variants=summ,
        bootstrap={PRIMARY: bootstrap(gms[PRIMARY]), "off": bootstrap(gms["off"])},
        groups_changed_primary=dict(total=int(len(changes)),
                                    mismatch_to_match=int((changes.mismatch_off & ~changes.mismatch_primary).sum()) if len(changes) else 0,
                                    match_to_mismatch=int((~changes.mismatch_off & changes.mismatch_primary).sum()) if len(changes) else 0),
        selfcheck=dict(entries=int(len(got)), off_max_abs_diff_eur_t=float(chk.abs_diff.max()),
                       re_price_eur_kg={r.catalyst: round(r.price_eur_kg, 2) for r in on[on.treatment == "inert"].drop_duplicates("catalyst").itertuples()},
                       canonical_states={r.canonical_state: dict(off=round(r.off, 2), on=round(r.on, 2),
                                                                 catalyst_t=round(r.catalyst_t, 2),
                                                                 cat_repl_eur_t=round(r.cat_repl_eur_t, 2))
                                         for r in canon.itertuples()}),
        runtime_s=round(time.time() - t0, 1), workers=WORKERS,
    )
    assert summary["selfcheck"]["off_max_abs_diff_eur_t"] < 1e-9, summary["selfcheck"]
    (HERE / "summary.json").write_text(json.dumps(summary, indent=1, default=float) + "\n", encoding="utf-8")
    print(json.dumps({k: (v["top1_mismatch_groups"], v["groups"], v["papers_with_mismatch"], v["pairwise_inversions"],
                          round(v["regret_median_mismatched"], 4), round(v["regret_max"], 3), v["groups_flipped_vs_off"])
                      for k, v in summ.items()}, indent=1))
    print(json.dumps({k: summary[k] for k in ("check", "parse_coverage", "bootstrap", "groups_changed_primary", "selfcheck")},
                     indent=1, default=float))


if __name__ == "__main__":
    main()
