"""Standalone contract for complete 2 model definitions x 5 cap levels."""
from __future__ import annotations
import argparse
import csv
import json
from pathlib import Path
import math
import unittest

from factorial import CAP_PERCENT,DEFS,SCENARIOS,INV_ANCHORS


def require(cond,msg):
    if not cond:raise AssertionError(msg)


def readcsv(p):
    with p.open(encoding="utf-8",newline="") as f:return list(csv.DictReader(f))


class FullCrossProofs(unittest.TestCase):
    def test_cartesian_set_complete(self):
        self.assertEqual(len(SCENARIOS),10)
        self.assertEqual(len(set(SCENARIOS)),10)
        self.assertEqual(len(CAP_PERCENT),5)
        self.assertEqual(set(DEFS),{"frozen","true_inert"})

    def test_information_order(self):
        # In complete factorial each partition-specific policy can always mimic
        # the global robust candidate, so it cannot have higher worst-case regret.
        from run import minimax
        C={
            0:{"f5":120,"f10":100,"t5":95,"t10":90},
            1:{"f5":103,"f10":101,"t5":112,"t10":105},
            2:{"f5":102,"f10":85,"t5":110,"t10":99}}
        ids=sorted(C)
        alls=list(C[0])
        full=minimax(ids,C,alls)[1]
        after_form=max(minimax(ids,C,["f5","f10"])[1],
                       minimax(ids,C,["t5","t10"])[1])
        after_cap=max(minimax(ids,C,["f5","t5"])[1],
                      minimax(ids,C,["f10","t10"])[1])
        self.assertGreaterEqual(full+1e-12,after_form)
        self.assertGreaterEqual(full+1e-12,after_cap)


def validate(folder):
    out=json.loads((folder/"summary.json").read_text(encoding="utf-8"))
    rows=readcsv(folder/"01_factorial10_minimax_groups.csv")
    paths=readcsv(folder/"02_form_specific_cap_paths.csv")
    require((out["n_groups"],out["n_scored_entries"],out["n_papers"],out["scenario_count"])
            ==(40,310,28,10),"factorial source cohort changed")
    require(out["source_inversion_anchors"]==
      {d:dict(zip(CAP_PERCENT,INV_ANCHORS[d])) for d in DEFS},"published inversion anchors changed")
    require(out["source_crosscheck"]["n_original_frozen_costs_checked"]==1550,
            "source original vs alternate cost vector incomplete")
    require(len(rows)==40 and len({r["group"] for r in rows})==40,
            "factorial group choices incomplete")
    require(len(paths)==80 and len({(p["group"],p["definition"]) for p in paths})==80,
            "factorial path identity duplication/loss")
    require(out["previous_six_scenario"]["certified5"]==24,"previous 6-scenario comparator drift")
    require(out["fully_crossed_ten"]["certified5"]<=24,
            "expanded ambiguity set cannot IMPROVE minimax 5%-guarantee")
    for r in rows:
        rf=float(r["robust10_worst_regret"])
        r6=float(r["robust6_risk"])
        f=float(r["form_information_gain"])
        c=float(r["cap_information_gain"])
        require(math.isfinite(rf) and math.isfinite(r6) and rf>=r6-1e-8,
                "fully crossed risk optimistic compared to subset")
        require(f>=-1e-10 and c>=-1e-10,"perfect-information benefit negative")
        require(f<=rf+1e-10 and c<=rf+1e-10,"information benefit exceeds baseline risk")
        require(float(r["full_form_known_residual_regret"])<=rf+1e-8,
                "known model type increased worst-case loss")
        require(float(r["full_cap_known_residual_regret"])<=rf+1e-8,
                "known inlet cap increased worst-case loss")
    require(sum(r["robust10_certified5"]=="1" for r in rows)==out["fully_crossed_ten"]["certified5"],
            "reported 10-case guarantee contradicts group record")
    require(out["perfect_information_counters"]["form_more_benefit"]+
       out["perfect_information_counters"]["cap_more_benefit"]+
       out["perfect_information_counters"]["equal_benefit"]==40,
       "model-information classification not partition")
    require((folder/"REPORT.md").exists(),"missing caveat/report")
    print("PASS: complete 10-scenario crossing, anchors, information bounds, and previous 6-scenario comparator")


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    validate(args.out)


if __name__=="__main__":
    main()
