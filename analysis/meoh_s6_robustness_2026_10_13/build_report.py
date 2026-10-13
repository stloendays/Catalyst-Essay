"""Collect items 1-9 (S5 frozen-reproduced and S6) into results.json and results_tables.md, and check the anchors.

Inputs (this folder): stats_s5/ and stats_s6/ (run_stats_wrapper.py), frozen_columns.json and s6_groups.csv
(run_frozen_columns.py), selectivity_split.json, catalyst_cost.json. Exits non-zero when any S5 frozen anchor or S6
anchor differs.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
FROZEN_STATS = REPO / "analysis" / "meoh_main_result_stats_2026_10_06"


def jload(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def pct(x, d=0):
    return f"{100 * x:.{d}f} %"


def noise_block(folder):
    s = jload(folder / "summary.json")
    pg = pd.read_csv(folder / "group_noise_probabilities.csv")
    pg["observed_mismatch"] = pg.observed_mismatch.astype(str).str.lower().isin(["true", "1"])
    out = dict(point=s["point_estimate"], bootstrap=s["cluster_bootstrap"], curve=s["regret_threshold_curve"],
               validation=s["validation"], surface_f0_max_rel_diff=s["surface_f0_max_rel_diff_vs_frozen"], noise={})
    for k in ("k1", "k2", "k4"):
        r = s["noise"][f"meas_{k}"]
        robust = pg[pg.observed_mismatch & (pg[f"p_mismatch_meas_{k}"] >= 0.9)]
        out["noise"][k] = dict(
            kept_ge90=int(len(robust)), of=int(pg.observed_mismatch.sum()),
            kept_regrets=sorted(float(x) for x in robust.observed_regret),
            kept_median_regret=float(robust.observed_regret.median()) if len(robust) else None,
            kept_regret_gt5pct=int((robust.observed_regret > 0.05).sum()),
            kept_papers=int(robust.doi.nunique()), kept_groups=robust.group.tolist(),
            mismatch_mean=r["mismatch_groups_mean"], mismatch_q=r["mismatch_groups_q025_q975"],
            noise_floor_mean=r["sty_leader_differs_from_reported_mean"],
            noise_floor_q=r["sty_leader_differs_from_reported_q025_q975"],
            exact_runs_outside_grid=r["exact_runs_outside_grid"])
    return out


def main():
    fc = jload(HERE / "frozen_columns.json")
    ss = jload(HERE / "selectivity_split.json")
    cc = jload(HERE / "catalyst_cost.json")
    n5, n6 = noise_block(HERE / "stats_s5"), noise_block(HERE / "stats_s6")
    groups = pd.read_csv(HERE / "s6_groups.csv")
    cls = dict(zip(groups.group, groups.cls.fillna("")))
    robust6 = n6["noise"]["k1"]["kept_groups"]
    robust_ordinary = [g for g in robust6 if cls.get(g) == "ordinary"]
    res = dict(noise_S5=n5, noise_S6=n6, frozen_columns=fc, selectivity_split=ss, catalyst_cost=cc,
               noise_robust_S6_k1_ordinary=dict(ordinary=len(robust_ordinary), of=len(robust6),
                                               near_infeasible=sum(cls.get(g) == "near-infeasible" for g in robust6),
                                               ordinary_groups=robust_ordinary))
    reg6 = dict(zip(*[pd.read_csv(HERE / "stats_s6" / "group_noise_probabilities.csv")[c]
                      for c in ("group", "observed_regret")]))
    res["noise_robust_S6_by_class"] = {}
    for k in ("k1", "k2", "k4"):
        kept = n6["noise"][k]["kept_groups"]
        res["noise_robust_S6_by_class"][k] = {
            c: dict(groups=len(g), gt5pct=sum(reg6[x] > 0.05 for x in g),
                    median_regret=float(np.median([reg6[x] for x in g])) if g else None)
            for c in ("ordinary", "near-infeasible") for g in [[x for x in kept if cls.get(x) == c]]}

    # ------------------------------------------------------------ anchors -----------------------------------------
    frozen_stats = jload(FROZEN_STATS / "summary.json")
    s5, s6 = fc["S5"], fc["S6"]
    A = {
        "S5 stats summary reproduces the frozen summary.json (point, bootstrap, curve, noise)": all(
            jload(HERE / "stats_s5" / "summary.json")[k] == frozen_stats[k]
            for k in ("point_estimate", "cluster_bootstrap", "regret_threshold_curve", "noise")),
        "S5 noise: 11 of 15 kept in >= 90 %": (n5["noise"]["k1"]["kept_ge90"], n5["noise"]["k1"]["of"]) == (11, 15),
        "S5 15/40": (n5["point"]["groups"], s5["primary"]["groups"]) == (15, 40),
        "S5 pairwise 304/1997": s5["primary"]["pairwise_inversions"] == "304/1997",
        "S5 selectivity 31/40, conversion 12/40": (s5["leaderboard_SMeOH"]["disagreements"],
                                                  s5["leaderboard_X"]["disagreements"]) == (31, 12),
        "S5 split bounds 14-18/40": (ss["S5"]["low"]["disagreements"], ss["S5"]["high"]["disagreements"]) == (14, 18),
        "S5 closure 11/28": (s5["closure_ge95"]["disagreements"], s5["closure_ge95"]["groups"]) == (11, 28),
        "S5 catalyst-priced 16/40": cc["S5"]["variants"]["composition_3y"]["disagreements"] == 16,
        "S6 28/40, 22 > 5 %": (n6["point"]["groups"], s6["primary"]["groups"], s6["primary"]["gt5pct"]) == (28, 40, 22),
        "S6 stats f0 equals frozen cost_recycled_opt_inlet (rel. < 1e-6)": n6["surface_f0_max_rel_diff"] < 1e-6,
        "S6 split convention 28/40": ss["S6"]["convention"]["disagreements"] == 28,
        "S6 catalyst term off 28/40": cc["S6"]["variants"]["off"]["disagreements"] == 28,
        "frozen-column anchors (run_frozen_columns.py)": all(fc["anchors"].values()),
    }
    res["anchors"] = A
    (HERE / "results.json").write_text(json.dumps(res, indent=1, default=float) + "\n", encoding="utf-8")
    (HERE / "results_tables.md").write_text(tables(res), encoding="utf-8")
    for k, ok in A.items():
        print("PASS" if ok else "FAIL", k)
    bad = [k for k, ok in A.items() if not ok]
    if bad:
        sys.exit("anchor mismatch: " + "; ".join(bad))


def rng(q):
    return f"{q[0]:g}–{q[1]:g}"


def tables(r):
    n5, n6, fc, ss, cc = r["noise_S5"], r["noise_S6"], r["frozen_columns"], r["selectivity_split"], r["catalyst_cost"]
    s5, s6 = fc["S5"], fc["S6"]

    def dis(b, gt=True):
        t = f"{b['disagreements']}/{b['groups']}"
        return t + (f" ({b['gt5pct']} > 5 %)" if gt else "")

    def boot(n):
        b = n["bootstrap"]
        return (f"{pct(b['fraction_ci95'][0], 1)}–{pct(b['fraction_ci95'][1], 1)} "
                f"(paper-weighted {pct(n['point']['paper_weighted_fraction'], 1)}, "
                f"{pct(b['paper_weighted_ci95'][0], 1)}–{pct(b['paper_weighted_ci95'][1], 1)})")

    def curve(n):
        return " · ".join(f"{c['threshold'] * 100:g} %: {c['groups']} ({c['papers']} p.)" for c in n["curve"])

    def kept(n, k):
        x = n["noise"][k]
        med = "–" if x["kept_median_regret"] is None else pct(x["kept_median_regret"], 1)
        return (f"{x['kept_ge90']} of {x['of']} (median regret {med}, {x['kept_regret_gt5pct']} > 5 %, "
                f"{x['kept_papers']} papers); mean {x['mismatch_mean']:.1f} [{rng(x['mismatch_q'])}]")

    def floor(n):
        return " · ".join(f"×{k[1]}: {n['noise'][k]['noise_floor_mean']:.1f} [{rng(n['noise'][k]['noise_floor_q'])}]"
                          for k in ("k1", "k2", "k4"))

    def med(b):
        return pct(b["median_regret_disagreements"], 1)

    cat5, cat6 = cc["S5"]["variants"]["composition_3y"], cc["S6"]["variants"]["composition_3y"]
    rows = [
        ("1 Point estimate", f"{dis(s5['primary'])}, {s5['primary']['papers_with_disagreement']} papers",
         f"{dis(s6['primary'])}, {s6['primary']['papers_with_disagreement']} papers ({s6['primary']['gt5pct_papers']} with > 5 %)"),
        ("1A Paper-cluster bootstrap 95 % CI (10,000, seed 20261006)", boot(n5), boot(n6)),
        ("1B Regret-threshold curve (groups, papers)", curve(n5), curve(n6)),
        ("1C Disagreements kept in ≥ 90 % of re-measurements, ×1", kept(n5, "k1"), kept(n6, "k1")),
        ("1C … ×2", kept(n5, "k2"), kept(n6, "k2")),
        ("1C … ×4", kept(n5, "k4"), kept(n6, "k4")),
        ("1C Noise floor (re-measured STY leader ≠ reported), mean [95 %]", floor(n5), floor(n6)),
        ("1C Surface vs exact: group verdicts differing / compared",
         f"{n5['validation']['verdict_disagreements_total']}/{n5['validation']['verdicts_compared']}",
         f"{n6['validation']['verdict_disagreements_total']}/{n6['validation']['verdicts_compared']}"),
        ("2 Pairwise orderings inverted", s5["primary"]["pairwise_inversions"], s6["primary"]["pairwise_inversions"]),
        ("3 Ranking by methanol selectivity: disagreements, median regret",
         f"{dis(s5['leaderboard_SMeOH'])}, {med(s5['leaderboard_SMeOH'])}",
         f"{dis(s6['leaderboard_SMeOH'])}, {med(s6['leaderboard_SMeOH'])}"),
        ("3 Ranking by conversion: disagreements, median regret",
         f"{dis(s5['leaderboard_X'])}, {med(s5['leaderboard_X'])}",
         f"{dis(s6['leaderboard_X'])}, {med(s6['leaderboard_X'])}"),
        ("3 (reference) Ranking by STY: median regret", med(s5["primary"]), med(s6["primary"])),
        ("4 Unreported CO/CH4 split: all CO – all CH4",
         f"{ss['S5']['low']['disagreements']}–{ss['S5']['high']['disagreements']}/40 "
         f"({ss['S5']['low']['gt5pct']}–{ss['S5']['high']['gt5pct']} > 5 %)",
         f"{ss['S6']['low']['disagreements']}–{ss['S6']['high']['disagreements']}/40 "
         f"({ss['S6']['low']['gt5pct']}–{ss['S6']['high']['gt5pct']} > 5 %; infeasible entries "
         f"{ss['S6']['low']['infeasible_entries']} / {ss['S6']['high']['infeasible_entries']})"),
        ("5 Products close to MeOH + CO + CH4 (≥ 95 %)", dis(s5["closure_ge95"]), dis(s6["closure_ge95"])),
        ("6 Catalyst priced from composition (3-year life)",
         f"{dis(cat5)}, median regret {med(cat5)}", f"{dis(cat6)}, median regret {med(cat6)}"),
        ("7 Recycled CO treated as inert (same limit for S6)", dis(s5["inert_co"]), dis(s6["inert_co"])),
        ("7 Limit counts CH4 + N2 only (CO excluded), 6.86 %", "= S5 (no limit)",
         dis(s6["co_excluded_ch4_n2"])),
    ]
    out = ["## Items 1–7: S5 (frozen, reproduced) and S6\n",
           "| Item | S5 (frozen, reproduced) | S6 (inlet-limited, primary) |", "|---|---|---|"]
    out += [f"| {a} | {b} | {c} |" for a, b, c in rows]

    def kinds(x):
        k, m = x["kinds"], x["mechanism"]
        f = lambda key: f"{m[key]['count']} ({pct(m[key]['fraction'])})"   # noqa: E731
        return [
            ("Disagreements (> 5 %), papers", f"{k['leader_differs']} ({k['leader_differs_gt5pct']}), "
                                              f"{x['primary']['papers_with_disagreement']}"),
            ("Other catalyst / multi-catalyst groups (> 5 %)",
             f"{k['other_catalyst']['groups']}/{k['other_catalyst']['of']} ({k['other_catalyst']['gt5pct']})"),
            ("… same temperature (> 5 %, papers of > 5 %)",
             f"{k['cat_sameT']['groups']} ({k['cat_sameT']['gt5pct']}, {k['cat_sameT']['gt5pct_papers']})"),
            ("… other temperature too (> 5 %)", f"{k['cat_and_T']['groups']} ({k['cat_and_T']['gt5pct']})"),
            ("Same catalyst, other temperature / temperature-series groups (> 5 %)",
             f"{k['other_temperature']['groups']}/{k['other_temperature']['of']} ({k['other_temperature']['gt5pct']})"),
            ("Plant leader more selective (share of disagreements)", f("plant_leader_more_selective")),
            ("Plant leader makes less CO", f("plant_leader_less_CO")),
            ("Plant leader has higher single-pass conversion", f("plant_leader_higher_conversion")),
            ("Plant leader runs cooler", f("plant_leader_cooler")),
            ("Median regret of disagreements", pct(x["primary"]["median_regret_disagreements"], 1)),
            ("Without Bansode 2013: disagreements (> 5 %)",
             f"{x['without_bansode']['disagreements']}/{x['without_bansode']['groups']} ({x['without_bansode']['gt5pct']})"),
        ]
    k5, k6 = kinds(s5), kinds(s6)
    ni = s6["near_infeasibility"]
    rb = r["noise_robust_S6_k1_ordinary"]
    out += ["", "## Item 8–9: kinds, mechanism, near-infeasibility\n",
            "| | S5 (frozen, reproduced) | S6 |", "|---|---|---|"]
    out += [f"| {a} | {b} | {d} |" for (a, b), (_, d) in zip(k5, k6)]
    out += [f"| Near-infeasible disagreements (PR #69 rule; > 5 %) | 0 | {ni['near-infeasible']['groups']} "
            f"({ni['near-infeasible']['gt5pct']}) |",
            f"| Ordinary disagreements (> 5 %) | 15 (7) | {ni['ordinary']['groups']} ({ni['ordinary']['gt5pct']}) |",
            f"| Noise-robust disagreements (×1, ≥ 90 %) that are ordinary | {n5['noise']['k1']['kept_ge90']} of "
            f"{n5['noise']['k1']['kept_ge90']} | {rb['ordinary']} of {rb['of']} |"]
    for k in ("k1", "k2", "k4"):
        b = r["noise_robust_S6_by_class"][k]
        o, q = b["ordinary"], b["near-infeasible"]
        m = lambda x: "–" if x["median_regret"] is None else pct(x["median_regret"], 1)   # noqa: E731
        out.append(f"| Noise-robust (×{k[1]}, ≥ 90 %): ordinary / near-infeasible (median regret) | "
                   f"{n5['noise'][k]['kept_ge90']} / 0 | {o['groups']} ({m(o)}) / {q['groups']} ({m(q)}) |")
    out.append("")
    return "\n".join(out)


if __name__ == "__main__":
    main()
