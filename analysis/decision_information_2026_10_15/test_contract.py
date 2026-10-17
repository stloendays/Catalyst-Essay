"""Contract checks for model-conditional minimax/regret and cap path outputs."""
from __future__ import annotations
import argparse
import csv
import json
import math
from pathlib import Path
import unittest
from run import minimax, regret, has_reentry, CAPS, SETS, AUGMENTED


class MethodProofs(unittest.TestCase):
    def test_regret_under_infeasibility(self):
        self.assertEqual(regret(math.inf,100),math.inf)
        self.assertEqual(regret(100,100),0)
        self.assertAlmostEqual(regret(120,100),.2)
        with self.assertRaises(AssertionError):
            regret(90,100)

    def test_minimax_not_same_as_scenario_optimum(self):
        costs={
           0:{"s1":100,"s2":112},
           1:{"s1":105,"s2":95},
           2:{"s1":150,"s2":120}}
        i,r,rr=minimax([0,1,2],costs,("s1","s2"))
        self.assertEqual(i,1)
        self.assertAlmostEqual(r,.05)
        self.assertGreater(rr[0],r)

    def test_nonfinite_robust_candidate(self):
        costs={0:{"a":10,"b":math.inf},1:{"a":12,"b":11}}
        i,r,rr=minimax([0,1],costs,("a","b"))
        self.assertEqual(i,1)
        self.assertTrue(math.isinf(rr[0]))

    def test_rank_path_versus_reentrant(self):
        self.assertTrue(has_reentry(["A","B","A"]))
        self.assertTrue(has_reentry(["A","B","C","B","D"]))
        self.assertFalse(has_reentry(["A","A","B","C","C"]))
        self.assertFalse(has_reentry(["A","B","C","D","E"]))

    def test_information_bound_set_theory(self):
        cost={0:{"cap5":100,"cap10":90,"alt":120},
              1:{"cap5":115,"cap10":96,"alt":82}}
        full=minimax([0,1],cost,("cap5","cap10","alt"))[1]
        partial=minimax([0,1],cost,("cap5","cap10"))[1]
        self.assertGreaterEqual(full+1e-12,partial)


def csvread(p):
    with p.open(newline="",encoding="utf-8-sig") as f:return list(csv.DictReader(f))


def check(pred,msg):
    if not pred:raise AssertionError(msg)


def validate(out,study):
    summary=json.loads((out/"summary.json").read_text())
    if study=="decision":
        records=csvread(out/"01_robust_group_decisions.csv")
        check(len(records)==40 and len({r["group"] for r in records})==40,"group ledger count")
        check(summary["frozen_anchors"]=={
           "groups":40,"entries":310,"papers":28,
           "S5_STY_inversion":15,"S6_STY_inversion":28,"true_inert_STY_inversion":18},
           "source anchors changed")
        check(summary["scenario_sets"]["augmented_six"]==list(AUGMENTED),
              "unauthorized scenario set change")
        check(summary["robust_primary"]["certified_5pct_groups"]==
              sum(r["robust_5pct"]=="1" for r in records),"coverage table contradiction")
        check(summary["robust_primary"]["certified_5pct_groups"]>=0,"invalid groups")
        for r in records:
            robust=r["worst_regret_full"]
            cap=r["worst_regret_cap_only"]
            form=r["worst_regret_form_6p86"]
            if robust!="INF":
                check(cap!="INF" and form!="INF","subset impossible when superset feasible")
                check(float(robust)+1e-9>=float(cap) and float(robust)+1e-9>=float(form),
                      "conditioning on extra knowledge increases optimum worst risk")
            if r["robust_5pct"]=="1":
                check(float(robust)<=.05000000001,"invalid safe recommendation")
        check((out/"REPORT.md").exists(),"missing scientific interpretation")
    else:
        g=csvread(out/"01_cap_path_groups.csv")
        tr=csvread(out/"02_cap_switch_events.csv")
        check(len(g)==40 and len(tr)==160,"group/path loss")
        check(summary["groups"]==40 and summary["verified_candidate_count"]==310,
              "cap ladder changed cohort")
        check(summary["scenario_order"]==list(CAPS),"changed cap ladder")
        check(summary["costs_are_monotone_per_candidate"] is True,
              "nested feasibility did not pass")
        for e in tr:
            if e["point_switch"]=="0":
                check(e["significant_1pct"]=="0" and e["significant_5pct"]=="0",
                      "claimed material change without a changed winner")
            if e["significant_5pct"]=="1":
                check(float(e["old_point_regret_at_new_cap"])>.05,
                      "economically immaterial >5% classification")
        check((out/"REPORT.md").exists(),"missing interpretation")
    print("PASS: model-conditional output schema and frozen-40 denominators",study)


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--study",choices=("decision","paths"),required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    validate(args.out,args.study)


if __name__=="__main__":
    main()
