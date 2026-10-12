"""Bounds on the unreported CO / CH4 split in the printed-value methanol result (thermodynamically consistent treatment).

The printed-value cohort requires printed CO2 conversion and methanol selectivity. Where a paper does not report the
CH4 selectivity, the candidate builder (workbook convention, meoh_candidates.closure) fills it:

  CO printed, CH4 not printed      CH4 = 1 - S_MeOH - S_CO   (the unreported remainder is counted as methane)
  neither printed                  CH4 = 0                   (the whole non-methanol carbon is counted as CO)

and CO is the closure 1 - S_MeOH - S_CH4. The two rules put the unreported carbon on opposite sides (methane leaves
only with the purge and is costly; CO is recycled and cheap). Flagged by the independent provenance audit
analysis/review_selectivity_2026_10_09/selectivity_source_audit.py. This script brackets the assumption: for every
entry whose CH4 selectivity is not printed,

  low     CH4 = 0, CO = 1 - S_MeOH                          (all unreported carbon as CO)
  high    CH4 = 1 - S_MeOH - S_CO(printed, else 0), CO = S_CO(printed, else 0)   (all unreported carbon as CH4)

Entries with a printed CH4 selectivity are unchanged. The convention coincides with "high" for CO-only entries and with
"low" for entries that report neither. Each variant reruns the plant model of the thermodynamically consistent
treatment (step S5) at laboratory conversion and with conversion raised with catalyst inventory
(meoh_conversion_sensitivity.evaluate, base "thermo"); the convention is rerun too and must equal
conversion_sensitivity_points.csv. Paper leaderboards (STY) do not depend on the split.

Outputs: selectivity_split_summary.csv, selectivity_split_groups.csv, selectivity_split_points.csv.
"""
import math
import sys
from io import StringIO
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import meoh_conversion_sensitivity as S  # noqa: E402
import meoh_decomposition as D  # noqa: E402
from reversal_kinds import KINDS, kind  # noqa: E402

COSTS = {"lab": "laboratory conversion", "cost_f0.95": "conversion raised with catalyst inventory (<= 0.95 X_eq)"}


def annotate(r):
    co = D.MC.pct(r.S_CO_pct, r.S_CO_q)
    return dict(ch4_printed=not pd.isna(r.S_CH4_pct), co_printed=co is not None, co_print=co)


def safe_evaluate(job):
    """meoh_conversion_sensitivity.evaluate, with a split the plant cannot run (H2 inlet ratio insufficient for the
    methane it implies) returned as infeasible (NaN costs) instead of stopping the run."""
    try:
        return S.evaluate(job)
    except ValueError:
        return job[0], job[2], {col: float("nan") for col in COSTS}


def split(c, variant):
    """(SCH4, SCO) of one candidate under a variant."""
    if variant == "convention" or c.ch4_printed:
        return c.SCH4, c.SCO
    co = c.co_print if c.co_printed else 0.0
    if variant == "low":
        return 0.0, 1.0 - c.SMeOH
    ch4 = max(0.0, 1.0 - c.SMeOH - co)
    return ch4, max(0.0, round(1.0 - c.SMeOH - ch4, 12))


def main():
    rec = pd.read_csv(StringIO(D.git_show("agent/extraction/out/records_normalized.csv")), keep_default_na=False,
                      na_values=[""])
    cand = D.build(rec, D.basis_lock, True, True, annotate=annotate)
    jobs, rows = {}, []
    for v in ("convention", "low", "high"):
        for c in cand.itertuples(index=False):
            sch4, sco = split(c, v)
            key = (float(c.X), float(c.SMeOH), float(sch4), float(sco), float(c.STY), float(c.P_bar),
                   float(c.h2_co2), float(c.T_C))
            jobs[key] = (key, float(c.y_co2), "thermo")
            rows.append(dict(variant=v, group=c.group, doi=c.doi, catalyst=c.catalyst, T_C=c.T_C, STY=c.STY,
                             SMeOH=c.SMeOH, SCH4=sch4, SCO=sco, ch4_printed=c.ch4_printed, co_printed=c.co_printed,
                             key=key))
    with Pool(4, initializer=D._init) as pool:
        res = {k: o for k, _, o in pool.map(safe_evaluate, list(jobs.values()), chunksize=4)}
    pts = pd.DataFrame(rows)
    for col in COSTS:
        pts[col] = [res[k][col] for k in pts.key]
    pts = pts.drop(columns="key")

    # the convention must reproduce the committed conversion-sensitivity points (thermo, printed)
    ref = pd.read_csv(HERE / "conversion_sensitivity_points.csv")
    ref = ref[(ref.base == "thermo") & (ref["mode"] == "printed")]
    conv = pts[pts.variant == "convention"].reset_index(drop=True)
    assert len(conv) == len(ref), (len(conv), len(ref))
    for col in COSTS:
        a, b = conv[col].to_numpy(float), ref[col].to_numpy(float)
        assert np.allclose(a, b, rtol=1e-5), (col, float(np.max(np.abs(a / b - 1))))   # reference written to 6 digits

    summary, groups = [], []
    for v, p in pts.groupby("variant", sort=False):
        n = p.groupby("group").size()
        p = p[p.group.isin(n[n >= 2].index)]
        for col, label in COSTS.items():
            out = []
            q = p[np.isfinite(p[col].astype(float))]
            n2 = q.groupby("group").size()
            q = q[q.group.isin(n2[n2 >= 2].index)]
            for g, x in q.groupby("group"):
                up = x.index[x.STY >= x.STY.max() - 1e-12]
                econ = x[col].idxmin()
                c_best, c_up = x[col].min(), x.loc[up, col].min()
                mism = econ not in set(up)
                lead = x.loc[sorted(up)[0], "catalyst"]
                out.append(dict(variant=v, conversion=label, group=g, doi=x.doi.iloc[0], mismatch=mism,
                                regret=(c_up - c_best) / c_best, sty_leader=lead, cost_leader=x.at[econ, "catalyst"],
                                kind=kind(x, lead, x.at[econ, "catalyst"]) if mism else ""))
            gm = pd.DataFrame(out)
            m = gm[gm.mismatch]
            row = dict(variant=v, conversion=label, infeasible=int((~np.isfinite(p[col].astype(float))).sum()),
                       groups=len(gm), leader_differs=len(m),
                       leader_differs_gt5pct=int((m.regret > 0.05).sum()), papers_with_mismatch=int(m.doi.nunique()))
            for k, tag in zip(KINDS, ("cat_sameT", "cat_and_T", "T", "same_record")):
                x = m[m.kind == k]
                row[tag], row[tag + "_gt5pct"] = len(x), int((x.regret > 0.05).sum())
            row["max_regret"] = float(gm.regret.max())
            summary.append(row)
            groups.append(gm)
    s = pd.DataFrame(summary)
    s.to_csv(HERE / "selectivity_split_summary.csv", index=False, float_format="%.4g")
    pd.concat(groups).to_csv(HERE / "selectivity_split_groups.csv", index=False, float_format="%.6g")
    pts.to_csv(HERE / "selectivity_split_points.csv", index=False, float_format="%.6g")
    changed = {v: int((pts[pts.variant == v][["SCH4", "SCO"]].to_numpy()
                       != conv[["SCH4", "SCO"]].to_numpy()).any(axis=1).sum()) for v in ("low", "high")}
    print("entries:", len(conv), "CH4 not printed:", int((~conv.ch4_printed).sum()),
          "| changed vs convention:", changed)
    pd.set_option("display.width", 250)
    print(s.to_string(index=False))


if __name__ == "__main__":
    main()
