"""Catalyst-level comparison of the 81 methanol groups under the rules of RULES.md (fixed before this script).

Each catalyst is placed at its best measured operating point (highest space-time yield for the laboratory leaderboard,
lowest modeled plant cost for the plant leaderboard); catalysts are then compared with catalysts. Groups with one
catalyst do not enter the ranking-change count. Primary identity: the author's sample (catalyst_key, with the one
sample that the extraction recorded under two names merged). Strict identity: material_key_strict.csv (samples that
differ only in synthesis are one catalyst).

    python run_catalyst_level.py   -> summary.json, groups_catalyst_level.csv, catalysts_temperature.csv
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
POOLED = REPO / "analysis" / "meoh_field_pooled_2026_10_15"
CONV = POOLED / "robustness" / "conversion_s6" / "s6_conversion_points.csv"
sys.path.insert(0, str(REPO / "analysis" / "meoh_literature_inversion_2026_10_05"))
from meoh_candidates import aggregate, catalyst_key  # noqa: E402

COST = "cost_recycled_opt_inlet"
T_TOL_C = 0.05
SEED = 20261006
# One sample recorded under two names: Frei et al. 2019, Fig. 6 extended test of the 0.75 wt% Pd-In2O3 CP catalyst
# ("CP") is the same sample as "Pd-In2O3 CP" (material_key_strict.csv, evidence column).
ALIAS = {("10.1038/s41467-019-11349-9 | 50 bar | H2/CO2 4 | 48 NL/g/h", "cp"): "pd-in2o3cp"}
CONV_COLS = ("cost_f0.95", "cost_f0.9", "cost_f0.99", "cost_two_sided")


def scored(frame, cost):
    """The candidates that enter the frozen scoring: finite cost, groups with at least two entries."""
    f = frame[np.isfinite(frame[cost].astype(float))]
    n = f.groupby("group").size()
    return f[f.group.isin(n[n >= 2].index)].copy()


def identities(f):
    f["cat_primary"] = [ALIAS.get((g, k), k) for g, k in zip(f.group, f.catalyst.map(catalyst_key))]
    strict = pd.read_csv(HERE / "material_key_strict.csv")
    m = dict(zip(zip(strict.group, strict.catalyst_key), strict.material_key_strict))
    f["cat_strict"] = [m.get((g, k), k) for g, k in zip(f.group, f.catalyst.map(catalyst_key))]
    return f


def catalyst_table(f, ident, cost):
    """Per (group, catalyst): best STY and its temperature, best cost and its temperature."""
    rows = []
    for (g, cat), x in f.groupby(["group", ident]):
        sty_max = x.STY.max()
        at_sty = x[x.STY >= sty_max - 1e-12]
        rows.append(dict(group=g, doi=x.doi.iloc[0], catalyst=cat, points=len(x),
                         temperatures=n_distinct(x.T_C.tolist()),
                         sty_best=sty_max, cost_at_sty_best=at_sty[cost].min(), T_sty_best=at_sty.T_C.iloc[0],
                         cost_best=x[cost].min(), T_cost_best=x.loc[x[cost].idxmin(), "T_C"]))
    return pd.DataFrame(rows)


def n_distinct(temps):
    out = []
    for t in sorted(temps):
        if not out or t - out[-1] > T_TOL_C:
            out.append(t)
    return len(out)


def compare(ct):
    """Catalyst-level leaders per group with at least two catalysts."""
    out = []
    for g, x in ct.groupby("group"):
        if len(x) < 2:
            continue
        lab = x[x.sty_best >= x.sty_best.max() - 1e-12]
        plant = x.loc[x.cost_best.idxmin()]
        lab_cost = lab.cost_best.min()
        out.append(dict(group=g, doi=x.doi.iloc[0], catalysts=len(x), lab_leader=" | ".join(lab.catalyst),
                        plant_leader=plant.catalyst, changed=plant.catalyst not in set(lab.catalyst),
                        gap=lab_cost / plant.cost_best - 1.0))
    return pd.DataFrame(out)


def bootstrap(gm, n=10_000, seed=SEED):
    per = gm.groupby("doi").changed.agg(["sum", "count"])
    s, c = per["sum"].to_numpy(float), per["count"].to_numpy(float)
    idx = np.random.default_rng(seed).integers(0, len(per), size=(n, len(per)))
    lo, hi = np.percentile(s[idx].sum(1) / c[idx].sum(1), [2.5, 97.5])
    return [float(lo), float(hi)]


def brief(gm):
    ch = gm[gm.changed]
    return dict(groups_2plus_catalysts=len(gm), papers=int(gm.doi.nunique()), changed=len(ch),
                fraction=len(ch) / len(gm), ci95=bootstrap(gm), papers_changed=int(ch.doi.nunique()),
                gt1pct=int((ch.gap > 0.01).sum()), gt5pct=int((ch.gap > 0.05).sum()),
                gt10pct=int((ch.gap > 0.10).sum()), gt5pct_papers=int(ch[ch.gap > 0.05].doi.nunique()),
                median_gap_changed=float(ch.gap.median()) if len(ch) else 0.0)


def temperature_result(ct):
    t = ct[ct.temperatures >= 2].copy()
    t["T_differs"] = (t.T_sty_best - t.T_cost_best).abs() > T_TOL_C
    t["gap"] = t.cost_at_sty_best / t.cost_best - 1.0
    d = t[t.T_differs]
    return t, dict(catalysts_with_2plus_T=len(t), groups=int(t.group.nunique()), papers=int(t.doi.nunique()),
                   plant_T_differs=len(d), groups_with_difference=int(d.group.nunique()),
                   papers_with_difference=int(d.doi.nunique()), gt5pct=int((d.gap > 0.05).sum()),
                   gt10pct=int((d.gap > 0.10).sum()), median_gap=float(d.gap.median()) if len(d) else 0.0,
                   plant_hotter=int((d.T_cost_best > d.T_sty_best).sum()),
                   plant_colder=int((d.T_cost_best < d.T_sty_best).sum()))


def main():
    c = pd.read_csv(POOLED / "pooled_candidates.csv")
    f = identities(scored(c, COST))
    gm_point, s_point = aggregate(c, COST)
    assert (s_point["groups"], s_point["top1_mismatch_groups"], int((gm_point[gm_point.top1_mismatch].regret > 0.05).sum())) \
        == (81, 50, 42), "point-level anchor"
    res = dict(point_level_total=dict(groups=81, changed=50, gt5pct=42, papers=s_point["papers"]))
    for ident in ("cat_primary", "cat_strict"):
        ct = catalyst_table(f, ident, COST)
        gm = compare(ct)
        res[ident] = dict(comparison=brief(gm))
        t, res[ident]["operating_point"] = temperature_result(ct)
        # how the 50 point-level disagreements split under this identity
        pm = gm_point[gm_point.top1_mismatch].group
        res[ident]["point_level_50_split"] = dict(
            catalyst_level_change=int(gm[gm.changed].group.isin(pm).sum()),
            catalyst_level_change_not_in_point_level=int((~gm[gm.changed].group.isin(pm)).sum()),
            single_catalyst_groups=int((~pm.isin(gm.group)).sum()),
            same_catalyst_leads_both=int((pm.isin(gm.group) & ~pm.isin(gm[gm.changed].group)).sum()))
        if ident == "cat_primary":
            gm.to_csv(HERE / "groups_catalyst_level.csv", index=False, float_format="%.6g")
            t.to_csv(HERE / "catalysts_temperature.csv", index=False, float_format="%.6g")
        else:
            gm.to_csv(HERE / "groups_catalyst_level_strict.csv", index=False, float_format="%.6g")

    # conversion raised toward equilibrium with catalyst amount (laboratory leaderboard unchanged)
    p = pd.read_csv(CONV)
    p = p[p["mode"] == "printed"].assign(sty_basis="")
    assert len(p) == len(c), "conversion table and pooled candidates differ in size"
    key = ["group", "catalyst", "T_C", "STY"]
    chk = p.merge(c[key + [COST]], on=key, suffixes=("", "_pooled"), validate="one_to_one")
    assert np.allclose(chk[COST], chk[COST + "_pooled"], rtol=1e-8, equal_nan=True), "conversion table lab cost"
    res["conversion_raised"] = {}
    for col in CONV_COLS:
        g_pt, s_pt = aggregate(p, col)
        row = dict(point_level=dict(groups=s_pt["groups"], changed=s_pt["top1_mismatch_groups"],
                                    gt5pct=int((g_pt[g_pt.top1_mismatch].regret > 0.05).sum())))
        for ident in ("cat_primary", "cat_strict"):
            fp = identities(scored(p, col))
            ct = catalyst_table(fp, ident, col)
            row[ident] = brief(compare(ct))
            row[ident]["operating_point"] = temperature_result(ct)[1]
        res["conversion_raised"][col] = row
    (HERE / "summary.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    b = res["cat_primary"]["comparison"]
    print(f"primary: {b['changed']}/{b['groups_2plus_catalysts']} changed, >5% {b['gt5pct']}, CI {b['ci95']}")


if __name__ == "__main__":
    main()
