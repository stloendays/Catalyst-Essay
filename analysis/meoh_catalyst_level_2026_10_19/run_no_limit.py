"""Catalyst-level comparison in the loop without the inlet limit (S5), under the rules of RULES.md and the same code
as run_catalyst_level.py: each catalyst at its best measured point (laboratory conversion) or with conversion raised
towards equilibrium by loading more catalyst (0.90, 0.95 and 0.99 of equilibrium), plant cost from the unlimited loop.

    python run_no_limit.py   -> summary_no_limit.json, groups_catalyst_level_no_limit.csv
"""
import json

import numpy as np
import pandas as pd

import run_catalyst_level as C

S5 = "cost_recycled_opt"
CONV_S5 = C.POOLED / "robustness" / "conversion_s5" / "conversion_sensitivity_points.csv"


def run(frame, cost):
    out = {}
    for ident in ("cat_primary", "cat_strict"):
        f = C.identities(C.scored(frame, cost))
        gm = C.compare(C.catalyst_table(f, ident, cost))
        out[ident] = C.brief(gm)
        if ident == "cat_primary":
            out["_groups"] = gm
    return out


def main():
    c = pd.read_csv(C.POOLED / "pooled_candidates.csv")
    gm_pt, s_pt = C.aggregate(c, S5)
    assert (s_pt["groups"], s_pt["top1_mismatch_groups"]) == (81, 25), "point-level S5 anchor"
    res = {"point_level": dict(groups=81, changed=25, gt5pct=int((gm_pt[gm_pt.top1_mismatch].regret > 0.05).sum()))}

    lab = run(c, S5)
    lab.pop("_groups").to_csv(C.HERE / "groups_catalyst_level_no_limit.csv", index=False, float_format="%.6g")
    res["laboratory_conversion"] = lab

    p = pd.read_csv(CONV_S5)
    p = p[p["mode"] == "printed"].assign(sty_basis="")
    assert len(p) == len(c), "conversion table and pooled candidates differ in size"
    chk = p.merge(c[["group", "catalyst", "T_C", "STY", S5]], on=["group", "catalyst", "T_C", "STY"],
                  suffixes=("", "_pooled"), validate="one_to_one")
    assert np.allclose(chk["cost_recycled_opt"], chk[S5 + "_pooled"], rtol=1e-8, equal_nan=True), "lab cost"
    res["conversion_raised"] = {}
    for col in ("cost_f0.9", "cost_f0.95", "cost_f0.99"):
        r = run(p, col)
        r.pop("_groups")
        res["conversion_raised"][col] = r
    (C.HERE / "summary_no_limit.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    for k, v in (("lab X", lab), ("X raised 0.95", res["conversion_raised"]["cost_f0.95"])):
        b = v["cat_primary"]
        print(f"{k}: {b['changed']}/{b['groups_2plus_catalysts']} ({100 * b['fraction']:.1f}%, CI "
              f"{100 * b['ci95'][0]:.1f}-{100 * b['ci95'][1]:.1f}), >5% {b['gt5pct']}, papers {b['papers_changed']}; "
              f"strict {v['cat_strict']['changed']}/{v['cat_strict']['groups_2plus_catalysts']}")


if __name__ == "__main__":
    main()
