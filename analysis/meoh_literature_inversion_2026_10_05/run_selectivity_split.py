"""Bounds on the unreported CO / CH4 split in the frozen methanol field result (printed values, step S5).

The printed-value cohort requires a printed CO2 conversion and methanol selectivity. Where a paper does not report the
CH4 selectivity, the candidate builder (workbook convention, meoh_candidates.closure) fills it:

  CO printed, CH4 not printed      CH4 = 1 - S_MeOH - S_CO   (the unreported remainder is counted as methane)
  neither printed                  CH4 = 0                   (the whole non-methanol carbon is counted as CO)

and CO is the closure 1 - S_MeOH - S_CH4. The two rules put the unreported carbon on opposite sides (methane leaves
only with the purge and is costly; CO is recycled). Flagged by the independent provenance audit
analysis/review_selectivity_2026_10_09/selectivity_source_audit.py. For every entry whose CH4 selectivity is not
printed:

  low     CH4 = 0, CO = 1 - S_MeOH                  (all unreported carbon as CO; equals the convention where
                                                     neither is printed)
  high    CH4 = 1 - S_MeOH - S_CO(printed, else 0)  (all unreported carbon as CH4; equals the convention where CO is
                                                     printed)

Entries with a printed CH4 selectivity are unchanged. Each variant reruns the frozen plant model at laboratory
conversion; the convention must reproduce cost_recycled_opt. Paper leaderboards (STY) do not depend on the split.

Outputs (this folder): selectivity_split_summary.json, selectivity_split_groups.csv.
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
sys.path.insert(0, str(REPO / "data" / "meoh"))
sys.path.insert(0, str(HERE))
import meoh_general_model as G  # noqa: E402
from meoh_candidates import ROW_KEYS, aggregate  # noqa: E402
from mismatch_kinds import classify  # noqa: E402

WORKERS = int(os.environ.get("INV_WORKERS", "4"))


def split(r, variant):
    """(SCH4, SCO) of one candidate under a variant."""
    if variant == "convention" or r.ch4_printed:
        return r.SCH4, r.SCO
    if variant == "low":
        return 0.0, 1.0 - r.SMeOH
    if r.co_printed:                       # the convention already puts the remainder in CH4
        return r.SCH4, r.SCO
    return 1.0 - r.SMeOH, 0.0


def lab_cost(key):
    X, sm, sch4, sco, sty, P, h2, T = key
    try:
        s = G.purge_sweep(dict(X=X, SMeOH=sm, SCH4=sch4, SCO=sco), STY_per_g_cat=sty, P_bar=P, h2_co2=h2, T_C=T,
                          x_co="recycled_central")
        return key, float(np.nanmin(np.asarray(s["cost_eur_t"], dtype=float)))
    except ValueError:        # the H2 inlet ratio cannot supply the methane the split implies: infeasible
        return key, float("nan")


def main():
    c = pd.read_csv(HERE / "literature_candidates.csv")
    variants = {}
    for v in ("convention", "low", "high"):
        f = c.copy()
        f[["SCH4", "SCO"]] = [split(r, v) for r in f.itertuples(index=False)]
        variants[v] = f
    keys = sorted({tuple(float(x) for x in r) for f in variants.values() for r in f[ROW_KEYS].itertuples(index=False)})
    with Pool(WORKERS) as pool:
        table = dict(pool.map(lab_cost, keys, chunksize=4))
    summary, groups = {}, []
    for v, f in variants.items():
        f["cost"] = [table[tuple(float(x) for x in r)] for r in f[ROW_KEYS].itertuples(index=False)]
        if v == "convention":
            dev = float(np.nanmax(np.abs(f.cost / f.cost_recycled_opt - 1)))
            assert dev < 1e-9, f"convention differs from cost_recycled_opt: {dev}"
        gm, s = aggregate(f, "cost", label=f"unreported CO / CH4 split: {v}")
        gm, kinds = classify(f, gm, "cost")
        m = gm[gm.top1_mismatch]
        n = c.groupby("group").size()
        ing = f[f.group.isin(n[n >= 2].index)]
        s.update(entries_changed=int(((ing.SCH4 != c.loc[ing.index, "SCH4"]) | (ing.SCO != c.loc[ing.index, "SCO"])).sum()),
                 infeasible=int((~np.isfinite(ing.cost)).sum()),
                 gt5pct=int((m.regret > 0.05).sum()), gt10pct=int((m.regret > 0.10).sum()), kinds=kinds)
        summary[v] = s
        groups.append(gm.assign(variant=v))
    n = c.groupby("group").size()
    ing = c[c.group.isin(n[n >= 2].index)]
    meta = dict(entries_in_scored_groups=int(len(ing)), ch4_not_printed=int((~ing.ch4_printed).sum()),
                co_printed_ch4_not=int((ing.co_printed & ~ing.ch4_printed).sum()),
                neither_printed=int((~ing.co_printed & ~ing.ch4_printed).sum()))
    (HERE / "selectivity_split_summary.json").write_text(json.dumps(dict(meta=meta, variants=summary), indent=1,
                                                                    default=float) + "\n", encoding="utf-8")
    pd.concat(groups).to_csv(HERE / "selectivity_split_groups.csv", index=False, float_format="%.6g")
    print(json.dumps(meta))
    for v, s in summary.items():
        print(v, f"{s['top1_mismatch_groups']}/{s['groups']}", ">5%", s["gt5pct"], "changed", s["entries_changed"],
              "infeasible", s["infeasible"], "other catalyst", s["kinds"]["other_catalyst"]["groups"],
              "other T", s["kinds"]["other_temperature"]["groups"])


if __name__ == "__main__":
    main()
