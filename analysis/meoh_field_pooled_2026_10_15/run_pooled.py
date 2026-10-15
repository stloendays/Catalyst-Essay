"""Methanol field result on the combined comparison set: the 40 groups of the first extraction (frozen,
analysis/meoh_literature_inversion_2026_10_05/literature_candidates.csv) and the 41 groups of the second extraction
(papers published 2025-11-05 to 2026-10-13; analysis/validation_meoh_prospective_2026_10_13/new_candidates_costed.csv,
printed values, PDF-checked records). Both sets were extracted and costed by the same frozen pipeline.

Every statistic is computed by the frozen code on the concatenated candidate table:
  analysis/meoh_s6_robustness_2026_10_13/run_frozen_columns.treatment  (aggregate, bootstrap, mismatch kinds,
  leader differences, without the dominant study, other laboratory leaderboards, product closure, inert CO)
plus the single-pass-yield leaderboard (X * S_MeOH, as Fig. 2b), the near-infeasibility rule of PR #69 and the
largest-regret group. Analyses whose inputs exist only for the first extraction (re-measurement Monte Carlo, inlet
limits other than 6.86 %, the CO-excluded definition, catalyst-inventory and composition-priced variants) are not
recomputed here.

    python run_pooled.py  -> summary.json, pooled_candidates.csv, groups_S6.csv, groups_S5.csv
"""
import json
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
ROB = REPO / "analysis" / "meoh_s6_robustness_2026_10_13"
NEW = REPO / "analysis" / "validation_meoh_prospective_2026_10_13" / "new_candidates_costed.csv"
sys.path.insert(0, str(ROB))
import run_frozen_columns as F  # noqa: E402  (puts data/meoh, the inversion and boundary folders on sys.path)
from meoh_candidates import aggregate  # noqa: E402

FIRST_ANCHORS = {"S6": (28, 40, 22), "S5": (15, 40, 7)}      # frozen: disagreements, groups, > 5 %


def load_pooled() -> pd.DataFrame:
    first = F.load().assign(batch="first")
    new = pd.read_csv(NEW)
    new["XS"] = new.X * new.SMeOH
    new["other_products"] = new.other_products.astype(str).str.lower().isin(["true", "1"])
    new = new[[c for c in first.columns if c in new.columns]].assign(batch="second")
    assert not set(first.doi) & set(new.doi), "a paper appears in both extractions"
    assert not set(first.group) & set(new.group), "a group id appears in both extractions"
    return pd.concat([first, new], ignore_index=True)


def near_infeasible(c, gm):
    out = {"ordinary": [0, 0], "near-infeasible": [0, 0]}
    for r in gm[gm.top1_mismatch].itertuples():
        g = c[c.group == r.group]
        lab = g[g.catalyst == r.upstream_winner].sort_values("cost_recycled_opt_inlet").iloc[0]
        near = (r.regret > F.NEAR_REGRET) or (lab.cost_recycled_opt_inlet / lab.cost_recycled_opt > F.NEAR_COST_RATIO)
        k = "near-infeasible" if near else "ordinary"
        out[k][0] += 1
        out[k][1] += int(r.regret > 0.05)
    return {k: dict(groups=v[0], gt5pct=v[1]) for k, v in out.items()}


def main():
    c = load_pooled()
    res = {"sets": {b: dict(groups_with_2plus=None, papers=int(g.doi.nunique()), operating_points=int(len(g)))
                    for b, g in c.groupby("batch")},
           "operating_points": int(len(c)), "papers_with_operating_points": int(c.doi.nunique())}
    for name in ("S6", "S5"):
        gm, out = F.treatment(c, name)
        col = F.TREAT[name][0]
        gy, sy = aggregate(c, col, up_col="XS")
        out["leaderboard_XS"] = F.brief(gy, sy)
        # anchors: the first extraction alone reproduces the frozen result through the same code
        g1, s1 = aggregate(c[c.batch == "first"], col)
        d1 = (s1["top1_mismatch_groups"], s1["groups"], int((g1[g1.top1_mismatch].regret > 0.05).sum()))
        assert d1 == FIRST_ANCHORS[name], (name, d1)
        g2, s2 = aggregate(c[c.batch == "second"], col)
        out["by_set"] = {"first": dict(groups=s1["groups"], papers=s1["papers"], disagreements=s1["top1_mismatch_groups"]),
                         "second": dict(groups=s2["groups"], papers=s2["papers"], disagreements=s2["top1_mismatch_groups"])}
        if name == "S6":
            out["near_infeasibility"] = near_infeasible(c, gm)
        top = gm.sort_values("regret", ascending=False).iloc[0]
        out["largest_regret"] = dict(group=top.group, doi=top.doi, regret=float(top.regret))
        bans = gm[gm.doi == F.BANSODE]
        out["bansode"] = dict(groups=int(len(bans)), max_regret=float(bans.regret.max()),
                              is_largest=bool(top.doi == F.BANSODE))
        res[name] = out
        gm.to_csv(HERE / f"groups_{name}.csv", index=False, float_format="%.6g")
        p = out["primary"]
        print(f"{name}: {p['disagreements']}/{p['groups']} groups ({p['papers']} papers), >5% {p['gt5pct']}, "
              f"papers with disagreement {p['papers_with_disagreement']}, pairwise {p['pairwise_inversions']}, "
              f"CI {p['bootstrap_frozen_inversion'].get('ci95', p['bootstrap_frozen_inversion'])}")
    c.to_csv(HERE / "pooled_candidates.csv", index=False, float_format="%.10g")
    (HERE / "summary.json").write_text(json.dumps(res, indent=1, default=str), encoding="utf-8")


if __name__ == "__main__":
    main()
