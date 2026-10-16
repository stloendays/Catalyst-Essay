"""Item 4: the unreported CO / CH4 split set to either bound, under S5 (frozen) and S6 (inlet-limited).

Imports analysis/meoh_literature_inversion_2026_10_05/run_selectivity_split.py unchanged (its split() rule, candidate
file, aggregate and classify) and swaps only the plant cost of one candidate:

  S5  the frozen lab_cost: minimum over every level of the conversion-capped sweep (reproduces 15 / 14 / 18 of 40)
  S6  the same sweep, minimum over the eligible levels (meoh_general_model.optimal_purge(constrained=True), reactor-inlet
      CH4 + CO + N2 <= 6.86 %); NaN when no level is eligible, and the entry leaves its group (frozen rule)

The convention variant must reproduce the frozen cost column of each treatment (cost_recycled_opt /
cost_recycled_opt_inlet). Writes selectivity_split.json and selectivity_split_groups.csv (this folder).

MEOH_FIELD_SET=combined (analysis/meoh_field_pooled_2026_10_15/field_set.py) runs the same analysis on the 81 groups of
both extractions and writes to analysis/meoh_field_pooled_2026_10_15/robustness/selectivity_split/; the first-set
groups must reproduce the first-set counts (S5 15 / 14 / 18, S6 28 / 26 / 29 of 40).
"""
import json
import os
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
INV = REPO / "analysis" / "meoh_literature_inversion_2026_10_05"
sys.path.insert(0, str(INV))
import run_selectivity_split as SS  # noqa: E402

G = SS.G
WORKERS = int(os.environ.get("INV_WORKERS", "4"))
FROZEN_COL = {"S5": "cost_recycled_opt", "S6": "cost_recycled_opt_inlet"}
sys.path.insert(0, str(REPO / "analysis" / "meoh_field_pooled_2026_10_15"))
import field_set as FS  # noqa: E402  (MEOH_FIELD_SET=first, the default, or combined)

OUT = FS.out_dir("selectivity_split", HERE)
FIRST_SET_S6 = {"convention": 28, "low": 26, "high": 29}


def lab_cost_both(key):
    X, sm, sch4, sco, sty, P, h2, T = key
    kw = dict(STY_per_g_cat=sty, P_bar=P, h2_co2=h2, T_C=T, x_co="recycled_central")
    c = dict(X=X, SMeOH=sm, SCH4=sch4, SCO=sco)
    try:
        s = G.purge_sweep(c, **kw)
    except ValueError:
        return key, (float("nan"), float("nan"))
    s5 = float(np.nanmin(np.asarray(s["cost_eur_t"], dtype=float)))          # = frozen SS.lab_cost
    s6 = G.optimal_purge(c, constrained=True, sweep=s, **kw)["cost_eur_t"]
    return key, (s5, float(s6))


def main():
    c = FS.candidates()
    variants = {}
    for v in ("convention", "low", "high"):
        f = c.copy()
        f[["SCH4", "SCO"]] = [SS.split(r, v) for r in f.itertuples(index=False)]
        variants[v] = f
    keys = sorted({tuple(float(x) for x in r) for f in variants.values() for r in f[SS.ROW_KEYS].itertuples(index=False)})
    with Pool(WORKERS) as pool:
        table = dict(pool.map(lab_cost_both, keys, chunksize=4))
    out, groups = {}, []
    for ti, treat in enumerate(("S5", "S6")):
        summary = {}
        for v, f in variants.items():
            f = f.copy()
            f["cost"] = [table[tuple(float(x) for x in r)][ti] for r in f[SS.ROW_KEYS].itertuples(index=False)]
            if v == "convention":
                ref = f[FROZEN_COL[treat]]
                same_nan = bool((np.isnan(f.cost) == np.isnan(ref)).all())
                dev = float(np.nanmax(np.abs(f.cost / ref - 1)))
                assert same_nan and dev < 1e-9, f"{treat} convention differs from {FROZEN_COL[treat]}: {dev}"
            gm, s = SS.aggregate(f, "cost", label=f"{treat} unreported CO / CH4 split: {v}")
            gm, kinds = SS.classify(f, gm, "cost")
            m = gm[gm.top1_mismatch]
            n = c.groupby("group").size()
            ing = f[f.group.isin(n[n >= 2].index)]
            summary[v] = dict(groups=s["groups"], disagreements=s["top1_mismatch_groups"],
                              papers_with_disagreement=s["papers_with_mismatch"],
                              gt5pct=int((m.regret > 0.05).sum()), median_regret_disagreements=s["regret_median_mismatched"],
                              infeasible_entries=int((~np.isfinite(ing.cost)).sum()),
                              other_catalyst=kinds["other_catalyst"], other_temperature=kinds["other_temperature"])
            groups.append(gm.assign(treatment=treat, variant=v))
        out[treat] = summary
    frozen = json.loads((INV / "selectivity_split_summary.json").read_text(encoding="utf-8"))["variants"]
    chk = out
    if FS.COMBINED:                     # the same checks on the first-set groups
        g = pd.concat(groups)
        g = g[g.group.isin(set(FS.first_part(c).group))]
        chk = {t: {v: dict(disagreements=int(d.top1_mismatch.sum()), groups=int(len(d)),
                           gt5pct=int((d.top1_mismatch & (d.regret > 0.05)).sum()))
                   for v, d in gt.groupby("variant")} for t, gt in g.groupby("treatment")}
        for v in ("low", "high"):
            assert chk["S6"][v]["disagreements"] == FIRST_SET_S6[v], (v, chk["S6"][v])
        out["first_set"] = chk
    for v in ("convention", "low", "high"):
        assert chk["S5"][v]["disagreements"] == frozen[v]["top1_mismatch_groups"], (v, chk["S5"][v], frozen[v])
        assert chk["S5"][v]["gt5pct"] == frozen[v]["gt5pct"], v
    assert chk["S6"]["convention"]["disagreements"] == 28
    (OUT / "selectivity_split.json").write_text(json.dumps(out, indent=1, default=float) + "\n", encoding="utf-8")
    pd.concat(groups).to_csv(OUT / "selectivity_split_groups.csv", index=False, float_format="%.6g")
    for t, s in ((t, out[t]) for t in ("S5", "S6")):
        print(t, {v: (x["disagreements"], x["groups"], x["gt5pct"], x["infeasible_entries"]) for v, x in s.items()})


if __name__ == "__main__":
    main()
