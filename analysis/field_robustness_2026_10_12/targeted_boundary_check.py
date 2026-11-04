#!/usr/bin/env python3
"""Targeted follow-up on the four joint m-p survivors of the initial CI run.

Tests the finite-loading upper bound and the missing CO/CH4 selectivity split.
This is a TARGETED robustness test; it does not rescore the other 36 groups.
Never overwrites the frozen field outputs or the complete joint scan.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

import joint_inventory_purge as J

HERE = Path(__file__).resolve().parent
PRIOR = HERE / "results"
REPORT = PRIOR / "joint_summary.json"
BASE = PRIOR / "joint_candidates.csv"
OUT = HERE / "targeted_results"
M5 = (0.25, 0.5, 0.75, 1, 1.25, 1.5, 2, 3, 5)
M10 = J.M_GRID
M25 = (*M10, 15, 20, 25)
SCENARIOS = [
    ("loading_max_5", M5, "printed_closure"),
    ("loading_max_10", M10, "printed_closure"),
    ("loading_max_25", M25, "printed_closure"),
    ("all_missing_as_CO", M10, "missing_as_CO"),
    ("all_missing_as_CH4", M10, "missing_as_CH4"),
]


def rerun(reference, choices, choice_name):
    # MeOH selectivity remains measured. If neither CO nor CH4 was printed,
    # the residual can be assigned to CO or CH4 as an explicit model bound.
    f = reference.copy()
    altered = 0
    for idx, r in f.iterrows():
        both_missing = not bool(r.co_printed) and not bool(r.ch4_printed)
        if both_missing and choice_name != "printed_closure":
            remainder = max(0.0, 1.0 - float(r.SMeOH))
            if choice_name == "missing_as_CO":
                f.loc[idx, "SCO"], f.loc[idx, "SCH4"] = remainder, 0.0
            else:
                f.loc[idx, "SCO"], f.loc[idx, "SCH4"] = 0.0, remainder
            altered += 1
    old_grid = J.M_GRID
    J.M_GRID = tuple(choices)
    try:
        jobs = [J.evaluate(row) for row in f.itertuples(index=False)]
    finally:
        J.M_GRID = old_grid
    run = pd.DataFrame(jobs)
    f = f.merge(run.drop(columns=["group", "doi", "catalyst"]),
                on="row_id", how="left", validate="one_to_one")
    return f, altered


def run():
    if not REPORT.is_file() or not BASE.is_file():
        raise FileNotFoundError("Run the full joint m-p workflow and commit its results first")
    prior = json.loads(REPORT.read_text(encoding="utf-8"))
    groups = [x["group"] for x in
              prior["cross_inlet_sameT_other_catalyst_gt5"]["groups_and_dois"]]
    if len(groups) != 4:
        raise AssertionError("The current targeted protocol needs the four recorded survivor groups")
    original = J.candidates()
    original = original[original.group.isin(groups)].copy()
    if original.group.nunique() != 4:
        raise AssertionError("Target comparison groups changed")
    frozen_run = pd.read_csv(BASE).set_index("row_id")
    outputs = []
    verdicts = []
    scenarios = {}
    for label, grid, split in SCENARIOS:
        print(f"Running {label}: {len(original)} entries; m={grid[-1]}; {split}", flush=True)
        f, altered = rerun(original, grid, split)
        # Verify the targeted m<=10 reference reproduces the FULL scan before
        # drawing conclusions from boundary and selectivity counterfactuals.
        if label == "loading_max_10":
            for tag in J.LIMITS:
                col = tag + "_cost"
                comp = f.set_index("row_id")[col]
                recorded = frozen_run.loc[comp.index, col]
                if not np.allclose(comp, recorded, rtol=2e-8, atol=2e-5, equal_nan=True):
                    raise AssertionError("Targeted m<=10 differs from full CI for " + col)
        one = {"changed_missing_selectivities": altered, "grid_max": max(grid)}
        gm_by_tag = {}
        for tag in J.INLET_NAMES:
            gm, s = J.metrics(f, tag + "_cost", label)
            gm_by_tag[tag] = gm.set_index("group")
            one[tag] = {
                "groups": s.get("groups", 0),
                "material_gt5": s.get("gt5pct", 0),
                "other_catalyst_gt5": s.get("kinds", {}).get("other_catalyst", {}).get("gt5pct", 0),
                "paper_count_gt5": s.get("gt5pct_papers", 0),
            }
            for g in groups:
                if g not in gm_by_tag[tag].index:
                    verdicts.append({
                        "scenario": label, "inlet": tag, "group": g, "doi": g.split(" | ", 1)[0],
                        "kind": "not scored", "regret": np.nan, "material_sameT": False,
                        "econ_winner": "", "up_winner": "",
                    })
                    continue
                r = gm_by_tag[tag].loc[g]
                verdicts.append({
                    "scenario": label, "inlet": tag, "group": g, "doi": r["doi"],
                    "kind": r["kind"], "regret": float(r["regret"]),
                    "material_sameT": (
                        bool(r["top1_mismatch"]) and float(r["regret"]) > 0.05
                        and r["kind"] == "other catalyst, same temperature"),
                    "econ_winner": r["economic_winner"], "up_winner": r["upstream_winner"],
                })
        stable = [
            g for g in groups if all(
                g in gm_by_tag[tag].index and
                bool(gm_by_tag[tag].loc[g, "top1_mismatch"]) and
                float(gm_by_tag[tag].loc[g, "regret"]) > 0.05 and
                gm_by_tag[tag].loc[g, "kind"] == "other catalyst, same temperature"
                for tag in J.INLET_NAMES
            )
        ]
        one["stable_three_inlet_sameT_gt5"] = len(stable)
        one["stable_three_inlet_papers"] = len({g.split(" | ", 1)[0] for g in stable})
        one["stable_groups"] = stable
        one["chosen_at_loading_grid_ceiling_inlet_6p86"] = int(
            (f.inlet_6p86_m == max(grid)).sum())
        scenarios[label] = one
        f["scenario"] = label
        outputs.append(f)
    OUT.mkdir(parents=True, exist_ok=True)
    pd.concat(outputs, ignore_index=True).to_csv(
        OUT / "targeted_candidates.csv", index=False, float_format="%.12g")
    pd.DataFrame(verdicts).to_csv(
        OUT / "targeted_group_verdicts.csv", index=False, float_format="%.12g")
    report = {
        "scope": "Only the 4 robust jointly-optimized groups and their original candidate entries.",
        "groups": len(groups), "entries": len(original),
        "hypotheses": {
            "loading_extension": "Joint ranking might change if m=10 is a binding grid boundary.",
            "missing_selectivities": "A group with neither CO nor CH4 printed may be sensitive to carbon-residual allocation."
        },
        "scenarios": scenarios,
        "limitations": [
            "Only originally identified survivors retested; no new global numerator or denominator.",
            "Loading response is a single-point calibrated surrogate, not independent kinetics.",
            "All missing carbon assigned to CO vs CH4 provides model bounds, not measured product distributions.",
            "No pressure-drop or bed-volume engineering bound here.",
        ],
    }
    (OUT / "targeted_summary.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({k: {"stable": v["stable_three_inlet_sameT_gt5"],
                          "papers": v["stable_three_inlet_papers"],
                          "at_m_ceiling": v["chosen_at_loading_grid_ceiling_inlet_6p86"]}
                      for k, v in scenarios.items()}, indent=2))


if __name__ == "__main__":
    run()
