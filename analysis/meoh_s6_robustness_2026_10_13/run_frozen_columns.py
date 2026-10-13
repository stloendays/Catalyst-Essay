"""Items 2, 3, 5, 7, 8 and 9 under S5 (frozen) and S6 (inlet-limited), from the frozen candidate columns.

Everything is scored with the frozen code: meoh_candidates.aggregate / bootstrap (group metrics, pairwise
inversions, paper-cluster bootstrap), mismatch_kinds.classify / leader_differences (kinds with denominators, how the
plant-cost leader differs) and the near-infeasibility rule of analysis/meoh_constraint_boundary_2026_10_12
(run_boundary.NEAR_REGRET, NEAR_COST_RATIO). Only the plant-cost column changes:

  S5  cost_recycled_opt        / purge_recycled_opt          (frozen primary, no inlet limit)
  S6  cost_recycled_opt_inlet  / purge_recycled_opt_inlet    (reactor-inlet CH4 + CO + N2 <= 6.86 %)

Item 7 also scores cost_inert_opt / cost_inert_opt_inlet (frozen columns) and the CO-excluded definition
(CH4 + N2 <= 6.86 %, column cost_true_inert_6.86 of analysis/meoh_inlet_definition_2026_10_12/entry_costs.csv).

Writes frozen_columns.json and s6_groups.csv; asserts the S5 and S6 anchors.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
INV = REPO / "analysis" / "meoh_literature_inversion_2026_10_05"
CB = REPO / "analysis" / "meoh_constraint_boundary_2026_10_12"
IDEF = REPO / "analysis" / "meoh_inlet_definition_2026_10_12"
sys.path.insert(0, str(REPO / "data" / "meoh"))
sys.path.insert(0, str(INV))
from meoh_candidates import aggregate, bootstrap  # noqa: E402
from mismatch_kinds import classify, leader_differences  # noqa: E402

sys.path.insert(0, str(CB))
from run_boundary import NEAR_COST_RATIO, NEAR_REGRET  # noqa: E402

BANSODE = "10.1039/c2cy20604h"
TREAT = {"S5": ("cost_recycled_opt", "purge_recycled_opt"), "S6": ("cost_recycled_opt_inlet", "purge_recycled_opt_inlet")}


def load():
    c = pd.read_csv(INV / "literature_candidates.csv")
    c["XS"] = c.X * c.SMeOH
    c["other_products"] = c.other_products.astype(str).str.lower().isin(["true", "1"])
    return c


def brief(gm, s):
    m = gm[gm.top1_mismatch]
    return dict(groups=s["groups"], papers=s["papers"], entries=s["entries"],
                disagreements=s["top1_mismatch_groups"], fraction=s["top1_mismatch_fraction"],
                papers_with_disagreement=s["papers_with_mismatch"],
                gt5pct=int((m.regret > 0.05).sum()), gt5pct_papers=int(m[m.regret > 0.05].doi.nunique()),
                gt1pct=int((m.regret > 0.01).sum()), gt10pct=int((m.regret > 0.10).sum()),
                median_regret_disagreements=s["regret_median_mismatched"], median_regret_all=s["regret_median_all"],
                pairwise_inversions=s["pairwise_inversions"], candidates_infeasible=s["candidates_infeasible"])


def kinds_table(c, gm, col, purge):
    gm, k = classify(c, gm, col)
    m = gm[gm.top1_mismatch]
    for tag, sel in (("cat_sameT", m.kind == "other catalyst, same temperature"),
                     ("cat_and_T", m.kind == "other catalyst and temperature"),
                     ("T", m.kind == "other temperature")):
        k[tag]["gt5pct_papers"] = int(m[sel & (m.regret > 0.05)].doi.nunique())
    ld = leader_differences(c, gm, col, purge)
    n = ld["disagreements"]
    mech = {key: dict(count=ld[key], fraction=ld[key] / n) for key in
            ("plant_leader_more_selective", "plant_leader_less_CO", "plant_leader_higher_conversion",
             "plant_leader_cooler")}
    return gm, k, dict(disagreements=n, **mech, median=ld["median"])


def treatment(c, name):
    col, purge = TREAT[name]
    gm, s = aggregate(c, col)
    out = dict(primary=brief(gm, s))
    out["primary"]["bootstrap_frozen_inversion"] = bootstrap(gm)
    gm, out["kinds"], out["mechanism"] = kinds_table(c, gm, col, purge)
    nb_gm, nb = aggregate(c[c.doi != BANSODE], col)
    out["without_bansode"] = brief(nb_gm, nb)
    for up in ("SMeOH", "X"):                                       # item 3
        g2, s2 = aggregate(c, col, up_col=up)
        out[f"leaderboard_{up}"] = brief(g2, s2)
    g5, s5 = aggregate(c[~c.other_products], col)                     # item 5
    out["closure_ge95"] = brief(g5, s5)
    inert = "cost_inert_opt" if name == "S5" else "cost_inert_opt_inlet"   # item 7
    gi, si = aggregate(c, inert)
    out["inert_co"] = brief(gi, si)
    return gm, out


def co_excluded(c):
    e = pd.read_csv(IDEF / "entry_costs.csv")
    f = c.merge(e[["group", "entry", "cost_true_inert_6.86", "cost_true_inert_none"]], on=["group", "entry"],
                how="left", validate="one_to_one")
    assert np.allclose(f.cost_true_inert_none, f.cost_recycled_opt, rtol=1e-6), "CO-excluded 'none' is not S5"
    gm, s = aggregate(f, "cost_true_inert_6.86")
    gm, k = classify(f, gm, "cost_true_inert_6.86")
    return dict(brief(gm, s), kinds=dict(other_catalyst=k["other_catalyst"], other_temperature=k["other_temperature"]))


def near_infeasibility(c, gm6):
    """PR #69 rule: a disagreement is near-infeasible when regret > NEAR_REGRET or the STY leader's S6 cost is more
    than NEAR_COST_RATIO x its S5 cost."""
    rows = []
    for r in gm6.itertuples():
        g = c[c.group == r.group]
        lab = g[g.catalyst == r.upstream_winner].sort_values("cost_recycled_opt_inlet").iloc[0]
        ratio = lab.cost_recycled_opt_inlet / lab.cost_recycled_opt
        near = (r.regret > NEAR_REGRET) or (ratio > NEAR_COST_RATIO)
        rows.append(dict(group=r.group, doi=r.doi, mismatch=bool(r.top1_mismatch), regret=r.regret, kind=r.kind,
                         sty_leader=r.upstream_winner, plant_leader=r.economic_winner, sty_leader_cost_vs_S5=ratio,
                         cls=("near-infeasible" if near else "ordinary") if r.top1_mismatch else ""))
    t = pd.DataFrame(rows)
    ref = pd.read_csv(CB / "boundary_groups.csv")
    ref = ref[ref.scenario == "S6"].set_index("group")["class"].fillna("")
    agree = int((t.set_index("group").cls == ref.reindex(t.group).to_numpy()).sum())
    m = t[t.mismatch]
    out = {k: dict(groups=int((m.cls == k).sum()), gt5pct=int(((m.cls == k) & (m.regret > 0.05)).sum()))
           for k in ("ordinary", "near-infeasible")}
    out["agrees_with_pr69_boundary_groups"] = f"{agree}/{len(t)}"
    return t, out


def main():
    c = load()
    res = {}
    for name in ("S5", "S6"):
        gm, res[name] = treatment(c, name)
        if name == "S6":
            gm6 = gm
    res["S6"]["co_excluded_ch4_n2"] = co_excluded(c)
    groups, res["S6"]["near_infeasibility"] = near_infeasibility(c, gm6)
    groups.to_csv(HERE / "s6_groups.csv", index=False, float_format="%.6g")

    s5, s6 = res["S5"], res["S6"]
    anchors = {
        "S5 disagreements 15/40": (s5["primary"]["disagreements"], s5["primary"]["groups"]) == (15, 40),
        "S5 >5 % 7": s5["primary"]["gt5pct"] == 7,
        "S5 pairwise 304/1997": s5["primary"]["pairwise_inversions"] == "304/1997",
        "S5 selectivity leaderboard 31/40": s5["leaderboard_SMeOH"]["disagreements"] == 31,
        "S5 conversion leaderboard 12/40": s5["leaderboard_X"]["disagreements"] == 12,
        "S5 closure subset 11/28": (s5["closure_ge95"]["disagreements"], s5["closure_ge95"]["groups"]) == (11, 28),
        "S5 inert CO 21/40": s5["inert_co"]["disagreements"] == 21,
        "S5 mechanism 4/3/9/3 of 15": [s5["mechanism"][k]["count"] for k in (
            "plant_leader_more_selective", "plant_leader_less_CO", "plant_leader_higher_conversion",
            "plant_leader_cooler")] == [4, 3, 9, 3],
        "S5 without Bansode 8/32 (1 >5 %)": (s5["without_bansode"]["disagreements"],
                                             s5["without_bansode"]["groups"], s5["without_bansode"]["gt5pct"]) == (8, 32, 1),
        "S6 disagreements 28/40": (s6["primary"]["disagreements"], s6["primary"]["groups"]) == (28, 40),
        "S6 >5 % 22": s6["primary"]["gt5pct"] == 22,
        "S6 papers 21, 18 with >5 %": (s6["primary"]["papers_with_disagreement"], s6["primary"]["gt5pct_papers"]) == (21, 18),
        "S6 other catalyst 16/32 (11)": (s6["kinds"]["other_catalyst"]["groups"], s6["kinds"]["other_catalyst"]["of"],
                                         s6["kinds"]["other_catalyst"]["gt5pct"]) == (16, 32, 11),
        "S6 same-T other catalyst 12 (8, 8 papers)": (s6["kinds"]["cat_sameT"]["groups"], s6["kinds"]["cat_sameT"]["gt5pct"],
                                                      s6["kinds"]["cat_sameT"]["gt5pct_papers"]) == (12, 8, 8),
        "S6 other temperature 12/22 (11)": (s6["kinds"]["other_temperature"]["groups"],
                                            s6["kinds"]["other_temperature"]["of"],
                                            s6["kinds"]["other_temperature"]["gt5pct"]) == (12, 22, 11),
        "S6 without Bansode 21/32 (17)": (s6["without_bansode"]["disagreements"], s6["without_bansode"]["groups"],
                                          s6["without_bansode"]["gt5pct"]) == (21, 32, 17),
        "S6 inert CO 28/40 (frozen inert_opt_inlet_limit)": s6["inert_co"]["disagreements"] == 28,
        "S6 CO-excluded 18/40 (8)": (s6["co_excluded_ch4_n2"]["disagreements"], s6["co_excluded_ch4_n2"]["gt5pct"]) == (18, 8),
        "S6 near-infeasibility 17 ordinary (12) / 11 (10)": (
            s6["near_infeasibility"]["ordinary"]["groups"], s6["near_infeasibility"]["ordinary"]["gt5pct"],
            s6["near_infeasibility"]["near-infeasible"]["groups"],
            s6["near_infeasibility"]["near-infeasible"]["gt5pct"]) == (17, 12, 11, 10),
        "S6 near-infeasibility classes match PR #69": s6["near_infeasibility"]["agrees_with_pr69_boundary_groups"] == "40/40",
    }
    res["anchors"] = anchors
    (HERE / "frozen_columns.json").write_text(json.dumps(res, indent=1, default=float) + "\n", encoding="utf-8")
    for k, ok in anchors.items():
        print("PASS" if ok else "FAIL", k)
    bad = [k for k, ok in anchors.items() if not ok]
    if bad:
        sys.exit("anchor mismatch: " + "; ".join(bad))


if __name__ == "__main__":
    main()
