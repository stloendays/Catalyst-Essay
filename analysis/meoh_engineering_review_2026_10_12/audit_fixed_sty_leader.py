#!/usr/bin/env python3
"""Hold the ORIGINAL laboratory STY leader fixed under engineering constraints.

Crucial distinction:
  1. *Conditional/economic reversal*: original top-STY entry is physically
     feasible, another feasible catalyst wins by a material cost margin.
  2. *Leader exclusion*: original top-STY entry(s) are infeasible; recomputing
     an STY ranking among survivors answers a different decision question.
  3. *Unrankable*: fewer than two feasible candidate entries remain.

Do not silently reselect the laboratory winner after a constraint filter.
Read existing CI outputs only. No frozen data or optimization is changed.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "analysis/field_robustness_2026_10_12"))
import joint_inventory_purge as J  # noqa: E402

ME = ROOT / "analysis/meoh_engineering_envelope_2026_10_12"
JOINT = ROOT / "analysis/field_robustness_2026_10_12/results/joint_summary.json"
BANSODE = "10.1039/c2cy20604h"
STY_TOL = 1e-12
COST_RTOL = 1e-9
KINDS = ("other catalyst, same temperature", "other catalyst and temperature",
         "other temperature", "same catalyst, same temperature")
CASES = ("original_sty_leader_feasible", "original_sty_leader_infeasible",
         "one_feasible_candidate", "no_feasible_candidates")


def classify_group(original: pd.DataFrame, candidate_costs: pd.Series):
    """Analyze one *original* comparison group using fixed original STY leaders.

    If tied original top-STY entries exist, any feasible tied entry preserves
    the original maximum; compare the lowest cost among these tied entries.
    An original winner being infeasible does not become a zero-regret tie.
    """
    group = original.sort_values("row_id").copy()
    cost = group.row_id.map(candidate_costs)
    is_feasible = np.isfinite(cost.astype(float))
    f = group.loc[is_feasible].copy()
    f["cost"] = cost[is_feasible].to_numpy(dtype=float)
    original_max = float(group.STY.max())
    top = group.loc[group.STY >= original_max - STY_TOL]
    leader_rows = set(top.row_id.astype(int))
    retained = f.loc[f.row_id.isin(leader_rows)]
    baseline = {
        "group": str(group.group.iloc[0]), "doi": str(group.doi.iloc[0]),
        "candidates_original": int(len(group)),
        "candidates_feasible": int(len(f)),
        "original_STY_top_entries": int(len(top)),
        "original_STY_top_entries_feasible": int(len(retained)),
        "original_STY_leader": "|".join(sorted(set(top.catalyst))),
        "original_STY_max": original_max,
        "winner_from_original_set": False,
        "status": "",
        "economic_winner": "",
        "lab_winner_feasible_cost": np.nan,
        "economic_best_cost": np.nan,
        "mismatch": False,
        "regret": np.nan,
        "kind": "",
        "material_gt5": False,
        "sameT_other_catalyst_gt5": False,
        "max_sty_ties_partially_excluded": bool(0 < len(retained) < len(top)),
    }
    if len(f) == 0:
        return dict(baseline, status="no_feasible_candidates")
    if len(f) == 1:
        return dict(baseline, status="one_feasible_candidate",
                    economic_winner=str(f.catalyst.iloc[0]))
    if retained.empty:
        # Important: the original STY champion is gone. Do not relabel the
        # best STY among the remaining entries as the ORIGINAL champion.
        eco = f.sort_values(["cost", "row_id"]).iloc[0]
        return dict(baseline, status="original_sty_leader_infeasible",
                    economic_winner=str(eco.catalyst))
    eco = f.sort_values(["cost", "row_id"]).iloc[0]
    lb = retained.sort_values(["cost", "row_id"]).iloc[0]
    c_best, c_lab = float(eco.cost), float(lb.cost)
    if not np.isfinite(c_best) or c_best <= 0:
        raise AssertionError("An invalid economic optimum escaped the optimization")
    regret = max(0., (c_lab - c_best) / c_best)
    mismatch = (c_lab - c_best) > COST_RTOL * max(abs(c_best), abs(c_lab))
    same_cat = str(eco.catalyst_key) == str(lb.catalyst_key)
    same_temp = abs(float(eco.T_C) - float(lb.T_C)) <= 1e-8
    kind = ("same catalyst, same temperature" if same_cat and same_temp
            else "other temperature" if same_cat
            else "other catalyst, same temperature" if same_temp
            else "other catalyst and temperature")
    material = mismatch and regret > 0.05
    return dict(baseline, status="original_sty_leader_feasible",
                winner_from_original_set=not mismatch,
                economic_winner=str(eco.catalyst),
                original_STY_leader_best_feasible=str(lb.catalyst),
                economic_best_cost=c_best, lab_winner_feasible_cost=c_lab,
                mismatch=bool(mismatch), regret=regret,
                kind=kind if mismatch else "agree",
                material_gt5=bool(material),
                sameT_other_catalyst_gt5=bool(
                    material and kind == "other catalyst, same temperature"))


def bootstrap_paper_cluster(rows, seed=20261012, n=5000):
    """Bootstrap over independent papers for ELIGIBLE original-leader groups only."""
    subset = rows[rows.status == "original_sty_leader_feasible"]
    if subset.empty:
        return {"groups": 0, "papers": 0, "fraction": None, "ci95": None}
    by_paper = subset.groupby("doi").mismatch.agg(["sum", "count"])
    s = by_paper["sum"].to_numpy(float)
    c = by_paper["count"].to_numpy(float)
    gen = np.random.default_rng(seed)
    pick = gen.integers(0, len(by_paper), size=(n, len(by_paper)))
    samples = s[pick].sum(axis=1) / c[pick].sum(axis=1)
    return {"groups": len(subset), "papers": len(by_paper),
            "fraction": float(s.sum() / c.sum()),
            "ci95": [float(v) for v in np.quantile(samples, [0.025, .975])],
            "resamples": n, "seed": seed}


def analyze(baseline, df, previous):
    orig_groups = {g: sub.copy() for g, sub in baseline.groupby("group")}
    if len(orig_groups) != 40 or len(baseline) != 310:
        raise AssertionError("The printed cohort must remain the 310/40 frozen cohort")
    required = {"row_id", "max_m", "inlet", "cap", "cost"}
    if not required.issubset(df):
        raise ValueError("Engineering optima missing required columns")
    unique = ["row_id", "max_m", "inlet", "cap"]
    if df.duplicated(unique).any() or df[unique].isna().any().any():
        raise AssertionError("Duplicated/missing engineering optimization identity keys")

    records, all_results = [], {}
    four = set(x["group"] for x in
        json.loads(JOINT.read_text(encoding="utf-8"))[
            "cross_inlet_sameT_other_catalyst_gt5"]["groups_and_dois"])
    for m in (10, 25):
        for cap in ("uncapped", "anchor_1x", "anchor_2x", "anchor_4x",
                    "inventory_2x", "reactor_inlet_2x", "recycle_power_2x"):
            by_inlet, groupdata = {}, {}
            for inlet in ("open", "inlet_4p92", "inlet_6p86", "inlet_10p25"):
                v = df.loc[(df.max_m == m) & (df.cap == cap) &
                           (df.inlet == inlet)]
                if len(v) != len(baseline) or v.row_id.nunique() != len(baseline):
                    raise AssertionError(f"Missing rows for {m}/{cap}/{inlet}")
                costs = v.set_index("row_id").cost
                details = pd.DataFrame([
                    dict(classify_group(original, costs), max_m=m, cap=cap, inlet=inlet)
                    for original in orig_groups.values()
                ])
                if len(details) != 40 or details.group.nunique() != 40:
                    raise AssertionError("Wrong denominator")
                records.extend(details.to_dict(orient="records"))
                statuses = Counter(details.status)
                if sum(statuses.values()) != 40:
                    raise AssertionError("Statuses must partition the original 40 groups")
                valid = details.loc[details.status == "original_sty_leader_feasible"]
                ineligible = details[details.status == "original_sty_leader_infeasible"]
                by_inlet[inlet] = {
                    "source_groups": 40,
                    "original_leader_comparable": len(valid),
                    "original_leader_excluded": len(ineligible),
                    "single_feasible": statuses.get("one_feasible_candidate", 0),
                    "none_feasible": statuses.get("no_feasible_candidates", 0),
                    "groups_with_at_least_two_feasible": len(valid) + len(ineligible),
                    "fixed_leader_mismatch": int(valid.mismatch.sum()),
                    "fixed_leader_regret_gt5": int(valid.material_gt5.sum()),
                    "fixed_leader_sameT_other_catalyst_regret_gt5": int(
                        valid.sameT_other_catalyst_gt5.sum()),
                    "fixed_leader_mismatch_papers": int(
                        valid.loc[valid.mismatch, "doi"].nunique()),
                    "fixed_leader_gt5_without_bansode": int(
                        (valid.material_gt5 & (valid.doi != BANSODE)).sum()),
                    "paper_cluster_ci": bootstrap_paper_cluster(details),
                    "original_four_eligible": int(valid.group.isin(four).sum()),
                    "original_four_material_sameT": int(
                        valid.loc[valid.group.isin(four), "sameT_other_catalyst_gt5"].sum()),
                }
                groupdata[inlet] = details.set_index("group")
                assert (by_inlet[inlet]["original_leader_comparable"] +
                        by_inlet[inlet]["original_leader_excluded"] +
                        by_inlet[inlet]["single_feasible"] +
                        by_inlet[inlet]["none_feasible"]) == 40
            robust = set(orig_groups)
            for inlet in ("inlet_4p92", "inlet_6p86", "inlet_10p25"):
                eligible = groupdata[inlet]
                robust &= set(eligible.index[eligible.sameT_other_catalyst_gt5])
            anchored = sorted(robust)
            all_results[f"m{m}__{cap}"] = {
                "inlets": by_inlet,
                "fixed_leader_material_sameT_3inlet_intersection": {
                    "groups": len(anchored),
                    "papers": len({str(orig_groups[g].doi.iloc[0]) for g in anchored}),
                    "without_bansode": sum(str(orig_groups[g].doi.iloc[0]) != BANSODE for g in anchored),
                    "cases": [{"group": g, "doi": str(orig_groups[g].doi.iloc[0])}
                              for g in anchored],
                },
                "original_four_retained_under_fixed_leader_rule": len(robust & four),
                "original_four_no_longer_eligible_or_material": sorted(four - robust),
            }
            # The old report is useful for comparison, but its upstream
            # champion is RESELECTED after filtering (source: aggregate()).
            earlier = previous["scenarios"][f"m{m}__{cap}"]["inlets"]
            for inlet in by_inlet:
                expected = earlier[inlet]["groups_scored"]
                current = by_inlet[inlet]["groups_with_at_least_two_feasible"]
                if current != expected:
                    raise AssertionError(
                        f"Feasibility denominator drift: {m}/{cap}/{inlet}: {current} vs {expected}")
                if (cap == "uncapped" and m == 10):
                    if by_inlet[inlet]["original_leader_excluded"]:
                        raise AssertionError("Original lab champion excluded in baseline m10 unbounded equipment")
                    if (by_inlet[inlet]["fixed_leader_mismatch"] != earlier[inlet]["groups_mismatch"] or
                        by_inlet[inlet]["fixed_leader_regret_gt5"] != earlier[inlet]["material_gt5"]):
                        raise AssertionError("Fixed-leader baseline should agree with joint PR #55")
    table = pd.DataFrame.from_records(records)
    return table, {
        "scope": "Hold original STY leader fixed; never redefine the source laboratory champion after engineering feasibility filter.",
        "input_entries": len(baseline), "original_comparison_groups": len(orig_groups),
        "raw_groups_retained_for_each_scenario": True,
        "baseline_matches_pr55_39_group_result": True,
        "category_definitions": {
            "original_sty_leader_feasible": "At least two eligible designs, including an original raw STY top-ranked entry; the original top-STY candidate is compared to the cheapest feasible candidate.",
            "original_sty_leader_infeasible": "At least two feasible designs but NONE of the original STY top-ranked entries remains feasible; a redefined STY leader is a different question.",
            "one_feasible_candidate": "Exactly one feasible design; rank correlation or reversal cannot be tested.",
            "no_feasible_candidates": "Zero feasible candidate designs.",
        },
        "scenarios": all_results,
        "caveats": [
            "Only source-anchored equipment ratios and first-order m surrogate; still no independently calibrated packed-bed pressure-drop.",
            "An original STY champion that is infeasible is not evidence that process/economic rankings agree.",
            "The 3-inlet intersection is conditional on the same group being comparable under all three envelope definitions.",
            "Bootstrap resamples papers from the eligible subset; selection and physics-model uncertainty are not captured.",
            "DOI is not always independent catalyst physics; two space-velocity groups in one article are not two independent papers.",
        ],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=ME / "results/engineering_candidate_optima.csv")
    parser.add_argument("--reference", type=Path, default=ME / "results/engineering_summary.json")
    parser.add_argument("--output", type=Path, default=ROOT / "analysis/meoh_engineering_review_2026_10_12/results")
    args = parser.parse_args()
    before = json.loads(args.reference.read_text(encoding="utf-8"))
    original = J.candidates()
    df = pd.read_csv(args.input)
    table, summary = analyze(original, df, before)
    args.output.mkdir(parents=True, exist_ok=True)
    table.to_csv(args.output / "fixed_original_STY_leader_groups.csv",
                 index=False, float_format="%.12g")
    (args.output / "fixed_original_STY_leader_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: {
        "anchor_6p86": v["inlets"]["inlet_6p86"],
        "cross_three_fixed_original": v["fixed_leader_material_sameT_3inlet_intersection"]["groups"],
        "original_four": v["original_four_retained_under_fixed_leader_rule"]}
                      for k,v in summary["scenarios"].items()}, indent=2))


if __name__ == "__main__":
    main()
