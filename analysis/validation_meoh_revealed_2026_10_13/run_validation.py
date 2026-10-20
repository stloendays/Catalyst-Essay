"""Revealed-preference validation H1-H3 exactly as pre-registered in PREREGISTRATION.md.

Runs the reproduction anchors first (test_anchors.py) and stops if any fails. Then, for each cohort (printed = primary,
extended = secondary) and scenario (S6 = primary, S5, S6-TI = CH4+N2 limit), computes:

  H1        within-group leaders in groups with a Cu/ZnO/Al2O3-type reference: D = share(cost leader is CuZnAl) -
            share(STY leader is CuZnAl); paired paper-cluster bootstrap; pass if D > 0 and lower 95 % bound > 0
  H1-broad  the same with any Cu-based reference against a non-Cu family
  H2        G_cost = ln(min non-Cu cost / min Cu-based cost), G_STY = ln(max Cu-based STY / max non-Cu STY);
            pass if lower 95 % bound of G_cost > 0 and point G_STY < 0
  H2-CZA    the same with Cu/ZnO/Al2O3-type as the focal family
  H2-regret within-group regret: family medians of cost regret and STY shortfall
  H3        dAUC = AUC_cost - AUC_STY for scaled vs lab-only entries; pass if lower 95 % bound > 0
  H3-catalyst, H3-alt  secondaries

Bootstrap: papers resampled with replacement, 10,000 draws, seed 20261013 (one resample matrix per cohort, shared by
every scenario and test of that cohort). Outputs: results.json, results_tables.md, h1_groups.csv, h2_families.csv,
h3_auc.csv.
"""
import json
import time

import numpy as np
import pandas as pd

import test_anchors
from rp_common import BOOT_N, BOOT_SEED, HERE, PRIMARY, SCENARIOS, cu_based, load, scored

SC_LABEL = {"S6": "S6 (CH4+CO+N2 <= 6.86 %, primary)", "S5": "S5 (no inlet limit)",
            "S6TI": "S6-TI (CH4+N2 <= 6.86 %)"}
H2_FAMILIES = ("Cu-based", "In2O3", "Pd", "ZnZrOx", "MZrOx_other", "Re")


def ci(x):
    """Percentile 95 % interval; -inf entries (undefined resamples, counted as failures) sort lowest."""
    x = np.sort(np.asarray(x, float))
    with np.errstate(invalid="ignore"):
        lo, hi = np.percentile(x, 2.5, method="lower"), np.percentile(x, 97.5, method="higher")
    return [float(lo), float(hi)]


def resample_counts(papers, n=BOOT_N, seed=BOOT_SEED):
    """(n, P) matrix: how often each paper is drawn in each resample."""
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(papers), size=(n, len(papers)))
    w = np.zeros((n, len(papers)))
    np.add.at(w, (np.repeat(np.arange(n), len(papers)), idx.ravel()), 1.0)
    return w


# ------------------------------------------------------------------------------------------------ H1 ---------------
def h1(d, gm, groups, focal):
    """focal(family) -> bool. Rows per scored subset group; D and its paper-cluster bootstrap."""
    rows = []
    for _, g in gm[gm.group.isin(groups)].iterrows():
        sub = d[d.group == g.group]
        fam = dict(zip(sub.catalyst, sub.family))
        rows.append(dict(group=g.group, doi=g.doi, n=int(g.n), sty_leader=g.upstream_winner,
                         sty_leader_family=fam[g.upstream_winner], cost_leader=g.economic_winner,
                         cost_leader_family=fam[g.economic_winner],
                         c=int(focal(fam[g.economic_winner])), s=int(focal(fam[g.upstream_winner])),
                         regret=float(g.regret)))
    t = pd.DataFrame(rows)
    out = dict(groups_in_subset=len(groups), groups_scored=len(t))
    if t.empty:
        return t, dict(out, D=None, pass_=False)
    # paired paper-cluster bootstrap over the subset's own papers (pre-registration: "with 2 papers, this requires
    # D > 0 in each paper"); same seed, one draw matrix per subset size
    per = t.groupby("doi").agg(c=("c", "sum"), s=("s", "sum"), k=("c", "size"))
    wc = resample_counts(list(per.index))
    with np.errstate(invalid="ignore", divide="ignore"):
        Db = (wc @ per.c.to_numpy(float) - wc @ per.s.to_numpy(float)) / (wc @ per.k.to_numpy(float))
    Db = np.where(np.isfinite(Db), Db, -np.inf)            # resample without a subset paper: failure
    D = float(t.c.mean() - t.s.mean())
    lo, hi = ci(Db)
    out.update(papers=int(t.doi.nunique()), cost_leader_focal=int(t.c.sum()), sty_leader_focal=int(t.s.sum()),
               share_cost=float(t.c.mean()), share_sty=float(t.s.mean()), D=D, ci95=[lo, hi],
               pass_=bool(D > 0 and lo > 0))
    return t, out


# ------------------------------------------------------------------------------------------------ H2 ---------------
def paper_extreme(e, mask, col, fn, pidx, P):
    """Per paper: min (fn='min') or max of col over the masked entries; +inf / -inf where the paper has none."""
    fill = np.inf if fn == "min" else -np.inf
    v = np.full(P, fill)
    for doi, x in e.loc[mask].groupby("doi")[col]:
        v[pidx[doi]] = x.min() if fn == "min" else x.max()
    return v


def h2(e, col, W, pidx, focal_mask):
    P = W.shape[1]
    fc = paper_extreme(e, focal_mask, col, "min", pidx, P)
    oc = paper_extreme(e, ~focal_mask, col, "min", pidx, P)
    fs = paper_extreme(e, focal_mask, "STY", "max", pidx, P)
    os_ = paper_extreme(e, ~focal_mask, "STY", "max", pidx, P)
    pres = W > 0

    def bmin(v):
        return np.where(pres, v[None, :], np.inf).min(1)

    def bmax(v):
        return np.where(pres, v[None, :], -np.inf).max(1)

    g_cost_pt = float(np.log(oc.min() / fc.min()))
    g_sty_pt = float(np.log(fs.max() / os_.max()))
    a, b = bmin(fc), bmin(oc)
    gc = np.where(np.isfinite(a) & np.isfinite(b), np.log(np.where(np.isfinite(b), b, 1) / np.where(np.isfinite(a), a, 1)), -np.inf)
    a, b = bmax(fs), bmax(os_)
    ok = np.isfinite(a) & np.isfinite(b)
    gs = np.log(np.where(ok, a, 1) / np.where(ok, b, 1))[ok]
    lo, hi = ci(gc)
    return dict(G_cost=g_cost_pt, G_cost_ci95=[lo, hi], G_STY=g_sty_pt, G_STY_ci95=ci(gs),
                share_resamples_focal_first_by_cost=float((gc > 0).mean()),
                share_resamples_focal_first_by_sty=float((gs > 0).sum() / len(gc)),
                focal_entries=int(focal_mask.sum()), other_entries=int((~focal_mask).sum()),
                pass_=bool(lo > 0 and g_sty_pt < 0))


def family_table(e, col):
    f = e.assign(fam=np.where(e.cu_based, "Cu-based", e.family))
    rows = []
    for fam, x in f.groupby("fam"):
        rows.append(dict(family=fam, entries=len(x), papers=x.doi.nunique(), min_cost=x[col].min(),
                         median_cost=x[col].median(), max_sty=x.STY.max(), median_sty=x.STY.median(),
                         cheapest=x.loc[x[col].idxmin(), "catalyst"], top_sty=x.loc[x.STY.idxmax(), "catalyst"]))
    t = pd.DataFrame(rows)
    t["rank_by_min_cost"] = t.min_cost.rank(method="min").astype(int)
    t["rank_by_max_sty"] = t.max_sty.rank(ascending=False, method="min").astype(int)
    return t.sort_values("rank_by_min_cost")


def h2_regret(e_all, col, W, pidx):
    """Within-group regret (blanks kept in the group extremes, excluded from the family medians)."""
    x = e_all.copy()
    x["cost_regret"] = x[col] / x.groupby("group")[col].transform("min") - 1.0
    x["sty_shortfall"] = x.groupby("group").STY.transform("max") / x.STY - 1.0
    x = x[x.family != "blank"]
    x["fam"] = np.where(x.cu_based, "Cu-based", x.family)
    med = x.groupby("fam")[["cost_regret", "sty_shortfall"]].median()
    first_cost, first_sty = med.cost_regret.idxmin(), med.sty_shortfall.idxmin()
    # bootstrap: weighted median per family = median of the entries repeated by their paper's draw count
    fams = list(med.index)
    pc = {f: [] for f in fams}
    w_ent = W[:, [pidx[p] for p in x.doi]]                       # (N, n)
    cnt = {"cost": np.zeros(len(fams)), "sty": np.zeros(len(fams))}
    vals = {k: x[c].to_numpy(float) for k, c in (("cost", "cost_regret"), ("sty", "sty_shortfall"))}
    fam_idx = [np.where(x.fam.to_numpy() == f)[0] for f in fams]
    for r in range(W.shape[0]):
        for k in ("cost", "sty"):
            m = np.full(len(fams), np.inf)
            for j, ix in enumerate(fam_idx):
                w = w_ent[r, ix]
                if w.sum() > 0:
                    m[j] = weighted_median(vals[k][ix], w)
            if np.isfinite(m).any():
                cnt[k][int(np.argmin(m))] += 1
    share = {k: dict(zip(fams, (cnt[k] / W.shape[0]).tolist())) for k in cnt}
    return dict(median=med.reset_index().to_dict("records"), first_by_cost_regret=first_cost,
                first_by_sty_shortfall=first_sty, bootstrap_share_first_by_cost=share["cost"],
                bootstrap_share_first_by_sty=share["sty"],
                pass_=bool(first_cost == "Cu-based" and first_sty != "Cu-based"))


def weighted_median(v, w):
    o = np.argsort(v, kind="mergesort")
    v, w = v[o], w[o]
    c = np.cumsum(w)
    half = c[-1] / 2.0
    i = int(np.searchsorted(c, half))
    if np.isclose(c[i], half) and i + 1 < len(v):            # even total weight: midpoint, as np.median
        return 0.5 * (v[i] + v[i + 1])
    return v[i]


# ------------------------------------------------------------------------------------------------ H3 ---------------
def wauc(v, y, W):
    """Weighted AUC = P(v_pos < v_neg) + 0.5 P(tie) for every row of W (entry weights); y: 1 = positive class."""
    u, k = np.unique(v, return_inverse=True)
    oh = np.zeros((len(v), len(u)))
    oh[np.arange(len(v)), k] = 1.0
    S = (W * (y == 1)) @ oh
    L = (W * (y == 0)) @ oh
    tl = L.sum(1, keepdims=True)
    greater = tl - np.cumsum(L, 1)
    num = (S * (greater + 0.5 * L)).sum(1)
    den = S.sum(1) * tl[:, 0]
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(den > 0, num / den, np.nan)


def h3(pts, col, cls, W, pidx):
    """pts: one row per entry (or per catalyst); cls column with 'scaled' / 'lab_only'."""
    y = (pts[cls] == "scaled").to_numpy(int)
    w_ent = W[:, [pidx[p] for p in pts.doi]]
    one = np.ones((1, len(pts)))
    a_cost = wauc(pts[col].to_numpy(float), y, np.vstack([one, w_ent]))
    a_sty = wauc(-pts.STY.to_numpy(float), y, np.vstack([one, w_ent]))
    d = a_cost - a_sty
    db = np.where(np.isfinite(d[1:]), d[1:], -np.inf)
    lo, hi = ci(db)
    return dict(n_scaled=int(y.sum()), n_lab_only=int((1 - y).sum()),
                papers_scaled=int(pts.loc[y == 1, "doi"].nunique()),
                papers_lab_only=int(pts.loc[y == 0, "doi"].nunique()),
                AUC_cost=float(a_cost[0]), AUC_cost_ci95=ci(np.nan_to_num(a_cost[1:], nan=0.0)),
                AUC_STY=float(a_sty[0]), AUC_STY_ci95=ci(np.nan_to_num(a_sty[1:], nan=0.0)),
                dAUC=float(d[0]), dAUC_ci95=[lo, hi], pass_=bool(lo > 0))


def catalyst_points(e, col, cls):
    x = e.copy()
    x["ckey"] = x.catalyst.str.split(" [", regex=False).str[0].str.replace(r"\s+", "", regex=True).str.lower()
    return x.groupby(["doi", "ckey"]).agg(**{col: (col, "min"), "STY": ("STY", "max"), cls: (cls, "first")}).reset_index()


# ------------------------------------------------------------------------------------------------ main -------------
def main():
    t0 = time.time()
    for f in (test_anchors.test_field_anchors, test_anchors.test_cohort_sizes,
              test_anchors.test_true_inert_matches_committed, test_anchors.test_subsets_unchanged):
        f()
    print("anchors reproduced")
    res, h1_rows, fam_rows, h3_rows = {}, [], [], []
    for cohort in ("printed", "extended"):
        d = load(cohort)
        sub = pd.read_csv(HERE / f"subsets_{cohort}.csv")
        h1g = set(sub.loc[sub.h1_group, "group"])
        h1bg = set(sub.loc[sub.h1_broad_group, "group"])
        papers = sorted(d.loc[d.group.isin(sub.group), "doi"].unique())
        pidx = {p: i for i, p in enumerate(papers)}
        W = resample_counts(papers)
        for sc, col in SCENARIOS.items():
            gm, s, e_all = scored(d, col)
            e = e_all[e_all.family != "blank"]
            r = dict(scenario=SC_LABEL[sc], field=dict(groups=s["groups"], different_leader=s["top1_mismatch_groups"],
                                                      entries=s["entries"], papers=s["papers"]))
            t1, r["H1"] = h1(d, gm, h1g, lambda f: f == "CuZnAl")
            t1b, r["H1_broad"] = h1(d, gm, h1bg, cu_based)
            for t, lab in ((t1, "H1"), (t1b, "H1_broad")):
                if not t.empty:
                    h1_rows.append(t.assign(cohort=cohort, scenario=sc, test=lab))
            r["H2"] = h2(e, col, W, pidx, e.cu_based.to_numpy())
            r["H2_CZA"] = h2(e, col, W, pidx, (e.family == "CuZnAl").to_numpy())
            r["H2_regret"] = h2_regret(e_all, col, W, pidx)
            fam_rows.append(family_table(e, col).assign(cohort=cohort, scenario=sc))
            r["H3"] = h3(e, col, "scale", W, pidx)
            r["H3_catalyst"] = h3(catalyst_points(e, col, "scale"), col, "scale", W, pidx)
            r["H3_alt"] = h3(e, col, "scale_alt", W, pidx)
            for k in ("H3", "H3_catalyst", "H3_alt"):
                h3_rows.append(dict(cohort=cohort, scenario=sc, test=k, **{a: b for a, b in r[k].items()
                                                                            if not isinstance(b, list)},
                                    dAUC_lo=r[k]["dAUC_ci95"][0], dAUC_hi=r[k]["dAUC_ci95"][1]))
            res[f"{cohort}/{sc}"] = r
            print(cohort, sc, "H1", r["H1"].get("D"), r["H1"]["pass_"], "| H2", round(r["H2"]["G_cost"], 3),
                  [round(v, 3) for v in r["H2"]["G_cost_ci95"]], round(r["H2"]["G_STY"], 3), r["H2"]["pass_"],
                  "| H3", round(r["H3"]["dAUC"], 3), [round(v, 3) for v in r["H3"]["dAUC_ci95"]], r["H3"]["pass_"])
    out = dict(preregistration="PREREGISTRATION.md", primary=f"{PRIMARY[0]}/{PRIMARY[1]}", bootstrap=dict(
        resamples=BOOT_N, seed=BOOT_SEED, unit="paper"), results=res, runtime_s=round(time.time() - t0, 1))
    (HERE / "results.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    pd.concat(h1_rows).to_csv(HERE / "h1_groups.csv", index=False)
    pd.concat(fam_rows).to_csv(HERE / "h2_families.csv", index=False, float_format="%.6g")
    pd.DataFrame(h3_rows).to_csv(HERE / "h3_auc.csv", index=False, float_format="%.6g")
    write_tables(res)


def f3(x):
    return "–" if x is None else f"{x:.3f}"


def write_tables(res):
    L = ["# Results tables (generated by run_validation.py)", ""]
    L += ["| Cohort / scenario | H1: cost-leader CZA / STY-leader CZA (groups) | D [95 % CI] | H1 pass | "
          "H1-broad D [CI] | H2: G_cost [CI] | G_STY [CI] | H2 pass | H2-CZA G_cost [CI] / G_STY | H2-CZA pass | "
          "H3: AUC_cost / AUC_STY | dAUC [CI] | H3 pass |", "|" + "---|" * 13]
    for k, r in res.items():
        a, b, c, cz, h = r["H1"], r["H1_broad"], r["H2"], r["H2_CZA"], r["H3"]
        L.append(f"| {k} | {a.get('cost_leader_focal')} / {a.get('sty_leader_focal')} of {a['groups_scored']} | "
                 f"{f3(a.get('D'))} [{f3(a['ci95'][0])}, {f3(a['ci95'][1])}] | {'pass' if a['pass_'] else 'FAIL'} | "
                 f"{f3(b.get('D'))} [{f3(b['ci95'][0])}, {f3(b['ci95'][1])}] | "
                 f"{f3(c['G_cost'])} [{f3(c['G_cost_ci95'][0])}, {f3(c['G_cost_ci95'][1])}] | "
                 f"{f3(c['G_STY'])} [{f3(c['G_STY_ci95'][0])}, {f3(c['G_STY_ci95'][1])}] | "
                 f"{'pass' if c['pass_'] else 'FAIL'} | {f3(cz['G_cost'])} [{f3(cz['G_cost_ci95'][0])}, "
                 f"{f3(cz['G_cost_ci95'][1])}] / {f3(cz['G_STY'])} | {'pass' if cz['pass_'] else 'FAIL'} | "
                 f"{f3(h['AUC_cost'])} / {f3(h['AUC_STY'])} | {f3(h['dAUC'])} [{f3(h['dAUC_ci95'][0])}, "
                 f"{f3(h['dAUC_ci95'][1])}] | {'pass' if h['pass_'] else 'FAIL'} |")
    L += ["", "| Cohort / scenario | H2-regret first by cost regret / by STY shortfall | H2-regret pass | "
          "H3-catalyst dAUC [CI] | pass | H3-alt dAUC [CI] | pass |", "|" + "---|" * 7]
    for k, r in res.items():
        g, hc, ha = r["H2_regret"], r["H3_catalyst"], r["H3_alt"]
        L.append(f"| {k} | {g['first_by_cost_regret']} / {g['first_by_sty_shortfall']} | "
                 f"{'pass' if g['pass_'] else 'FAIL'} | {f3(hc['dAUC'])} [{f3(hc['dAUC_ci95'][0])}, "
                 f"{f3(hc['dAUC_ci95'][1])}] | {'pass' if hc['pass_'] else 'FAIL'} | {f3(ha['dAUC'])} "
                 f"[{f3(ha['dAUC_ci95'][0])}, {f3(ha['dAUC_ci95'][1])}] | {'pass' if ha['pass_'] else 'FAIL'} |")
    (HERE / "results_tables.md").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
