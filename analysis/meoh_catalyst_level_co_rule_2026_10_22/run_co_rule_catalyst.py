"""Methanol catalyst-level count under the recycled-CO rules (PREREGISTRATION.md).

Laboratory conversion: entry costs of analysis/meoh_field_pooled_2026_10_15/robustness/co_conversion_bound/entry_costs.csv.
More catalyst loaded (f = 0.95), 6.86 % limit: run_s6_conversion.evaluate with the x_CO rule set in every worker.
Catalyst identity, leaders and bootstrap: analysis/meoh_catalyst_level_2026_10_19/run_catalyst_level.py, unchanged.

    set MEOH_FIELD_SET=combined
    set INV_WORKERS=2
    D:\\Research\\CatalystForge\\.venv\\Scripts\\python.exe -X utf8 run_co_rule_catalyst.py [--lab-only]
"""
from __future__ import annotations

import json
import os
import re
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

os.environ.setdefault("MEOH_FIELD_SET", "combined")
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
AN = REPO / "analysis"
for p in (AN / "meoh_catalyst_level_2026_10_19", AN / "verify_2026_10_12_s6_conversion"):
    sys.path.insert(0, str(p))
import run_catalyst_level as CL  # noqa: E402
import run_s6_conversion as S6  # noqa: E402

RC = S6.RC
POOLED = AN / "meoh_field_pooled_2026_10_15"
ENTRY = POOLED / "robustness" / "co_conversion_bound" / "entry_costs.csv"
RULES = {"central": "recycled_central", "equal_X": "recycled_equal_X", "high": "recycled_high"}
LIMITS = ["none", "5", "6.86", "8", "10", "15"]
CU = re.compile(r"Cu(?![a-z])")
WORKERS = int(os.environ.get("INV_WORKERS", "2"))


def count(frame, cost):
    f = CL.identities(CL.scored(frame, cost))
    out = {}
    for ident in ("cat_primary", "cat_strict"):
        gm = CL.compare(CL.catalyst_table(f, ident, cost))
        out[ident] = CL.brief(gm)
        if ident == "cat_primary":
            out["_gm"] = gm
    return out


def _init(rule):
    RC.KW_RULE = dict(x_co=rule)


def _eval(job):
    return S6.evaluate(job)          # already returns (key, result dict)


def raised(points, rule_of_row):
    """cost_f0.95 per row under the given x_CO rule (one rule per row)."""
    out = pd.Series(np.nan, index=points.index)
    for rule in sorted(set(rule_of_row)):
        idx = [i for i, r in zip(points.index, rule_of_row) if r == rule]
        jobs = {}
        for i in idx:
            r = points.loc[i]
            key = tuple(float(r[k]) for k in S6.ROW_KEYS)
            jobs[key] = (key, float(r.y_co2))
        with Pool(WORKERS, initializer=_init, initargs=(rule,)) as pool:
            table = dict(pool.map(_eval, list(jobs.values()), chunksize=4))
        for i in idx:
            r = points.loc[i]
            out[i] = table[tuple(float(r[k]) for k in S6.ROW_KEYS)][f"cost_f{S6.F_PRIMARY:g}"]
        print(f"  raised conversion, {rule}: {len(jobs)} operating points", flush=True)
    return out


def main(lab_only=False):
    c = pd.read_csv(POOLED / "pooled_candidates.csv")
    e = pd.read_csv(ENTRY)
    key = ["group", "catalyst", "T_C", "STY"]
    cols = [f"cost_{r}_{l}" for r in RULES for l in LIMITS]
    m = c.merge(e[key + cols], on=key, how="left", validate="one_to_one")
    assert len(m) == len(c)
    m["cu_based"] = m.catalyst.astype(str).str.contains(CU)
    for l in LIMITS:
        m[f"cost_family_{l}"] = np.where(m.cu_based, m[f"cost_high_{l}"], m[f"cost_central_{l}"])

    res = dict(gates={}, laboratory_conversion={}, raised_conversion={},
               cu_based_entries=int(m.cu_based.sum()), entries=int(len(m)))
    dev = np.nanmax(np.abs(m["cost_central_6.86"] / m.cost_recycled_opt_inlet - 1))
    g1 = count(m, "cost_central_6.86")["cat_primary"]
    res["gates"]["1_central_lab"] = dict(max_rel_dev=float(dev), changed=g1["changed"], groups=g1["groups_2plus_catalysts"],
                                         gt5pct=g1["gt5pct"], ok=dev < 1e-9 and (g1["changed"], g1["groups_2plus_catalysts"], g1["gt5pct"]) == (26, 63, 19))
    print(res["gates"]["1_central_lab"], flush=True)
    assert res["gates"]["1_central_lab"]["ok"]

    for r in [*RULES, "family"]:
        for l in LIMITS:
            k = count(m, f"cost_{r}_{l}")
            k.pop("_gm")
            res["laboratory_conversion"][f"{r}|{l}"] = k
            b = k["cat_primary"]
            print(f"lab  {r:8s} {l:5s} {b['changed']}/{b['groups_2plus_catalysts']} >5% {b['gt5pct']}", flush=True)
    if not lab_only:
        conv = pd.read_csv(POOLED / "robustness" / "conversion_s6" / "s6_conversion_points.csv")
        conv = conv[conv["mode"] == "printed"].reset_index(drop=True)
        cc = conv.merge(m[key + ["cu_based"]], on=key, how="left", validate="one_to_one")
        g2 = count(cc.assign(sty_basis=""), f"cost_f{S6.F_PRIMARY:g}")["cat_primary"]
        res["gates"]["2_central_raised_frozen"] = dict(changed=g2["changed"], groups=g2["groups_2plus_catalysts"], gt5pct=g2["gt5pct"],
                                                       ok=(g2["changed"], g2["groups_2plus_catalysts"], g2["gt5pct"]) == (21, 63, 10))
        print(res["gates"]["2_central_raised_frozen"], flush=True)
        assert res["gates"]["2_central_raised_frozen"]["ok"]
        for r in ["central", "high", "equal_X", "family"]:
            col = f"cost_raised_{r}"
            if r == "central":                       # the frozen column, verified by gate 2
                cc[col] = cc[f"cost_f{S6.F_PRIMARY:g}"]
            else:
                rules = [RULES["high"] if (r == "family" and cu) else RULES["central"] if r == "family" else RULES[r]
                         for cu in cc.cu_based]
                cache = HERE / f"raised_{r}.csv"
                if cache.exists():
                    cc[col] = pd.read_csv(cache)[col].to_numpy()
                else:
                    cc[col] = raised(cc, rules)
                    cc[[col]].to_csv(cache, index=False, float_format="%.10g")
            k = count(cc.assign(sty_basis=""), col)
            gm = k.pop("_gm")
            gm.to_csv(HERE / f"groups_raised_{r}.csv", index=False, float_format="%.6g")
            res["raised_conversion"][r] = k
            b = k["cat_primary"]
            print(f"raised {r:8s} {b['changed']}/{b['groups_2plus_catalysts']} >5% {b['gt5pct']}", flush=True)
        if "central" in res["raised_conversion"]:
            b = res["raised_conversion"]["central"]["cat_primary"]
            res["gates"]["2b_central_raised_frozen_column"] = dict(ok=(b["changed"], b["gt5pct"]) == (21, 10))
        cc.to_csv(HERE / "raised_points.csv", index=False, float_format="%.10g")
    (HERE / "summary.json").write_text(json.dumps(res, indent=1, default=float) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main(lab_only="--lab-only" in sys.argv)
