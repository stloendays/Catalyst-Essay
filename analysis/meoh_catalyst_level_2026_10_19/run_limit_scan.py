"""Catalyst-level comparison at laboratory conversion across inlet limits of 4–30% of CO, methane and N2 (the
pooled candidates' cost_recycled_opt_lim* columns, the same columns as the point-level scan of Extended Data Fig. 10),
with the primary 6.86% and the unlimited loop for reference. Same rules and code as run_catalyst_level.py.

    python run_limit_scan.py   -> summary_limit_scan.json
"""
import json

import pandas as pd

import run_catalyst_level as C

COLS = [("4", "cost_recycled_opt_lim4"), ("5", "cost_recycled_opt_lim5"), ("6", "cost_recycled_opt_lim6"),
        ("6.86", "cost_recycled_opt_inlet"), ("8", "cost_recycled_opt_lim8"), ("10", "cost_recycled_opt_lim10"),
        ("12", "cost_recycled_opt_lim12"), ("15", "cost_recycled_opt_lim15"), ("20", "cost_recycled_opt_lim20"),
        ("25", "cost_recycled_opt_lim25"), ("30", "cost_recycled_opt_lim30"), ("none", "cost_recycled_opt")]


def main():
    c = pd.read_csv(C.POOLED / "pooled_candidates.csv")
    res = {}
    for lim, col in COLS:
        f = C.identities(C.scored(c, col))
        gm = C.compare(C.catalyst_table(f, "cat_primary", col))
        b = C.brief(gm)
        gp, sp = C.aggregate(c, col)
        res[lim] = dict(catalyst_level=dict(changed=b["changed"], groups=b["groups_2plus_catalysts"],
                                            gt5pct=b["gt5pct"], papers_changed=b["papers_changed"]),
                        point_level=dict(changed=int(sp["top1_mismatch_groups"]), groups=int(sp["groups"])))
        print(f"limit {lim:>5}: catalyst {b['changed']}/{b['groups_2plus_catalysts']} (>5% {b['gt5pct']}), "
              f"point {sp['top1_mismatch_groups']}/{sp['groups']}")
    assert res["6.86"]["catalyst_level"]["changed"] == 26 and res["none"]["catalyst_level"]["changed"] == 16
    (C.HERE / "summary_limit_scan.json").write_text(json.dumps(res, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
