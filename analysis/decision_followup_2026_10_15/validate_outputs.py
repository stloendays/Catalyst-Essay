#!/usr/bin/env python3
"""External artifact contract for exploratory source-only research."""
from __future__ import annotations
import argparse
import csv
from hashlib import sha256
import json
import math
from pathlib import Path


def check(c,reason):
    if not c:raise AssertionError(reason)


def rows(path):
    with path.open(encoding="utf-8",newline="") as f:return list(csv.DictReader(f))


def validate_meoh(root):
    s=json.loads((root/"summary.json").read_text(encoding="utf-8"))
    check((s["groups"],s["scored_entries"],s["papers"])==(40,310,28),"cohort drift")
    check(s["frozen_anchors"]=={"S5_inversions":15,"S6_inversions":28,
        "STY_first_choice_correct":12,"selectivity_tie_set_correct":23},"frozen anchor drift")
    check(s["surrogate_training"]["test_time_S6_feasibility_used"] is False,"test-time oracle")
    fold=rows(root/"01_fold_coefficients.csv")
    predicted=rows(root/"02_blind_paper_predictions.csv")
    decisions=rows(root/"03_group_predictions_and_regret.csv")
    cases=rows(root/"04_posthoc_candidate_errors.csv")
    check((len(fold),len(predicted),len(decisions),len(cases))==(28,310,40,310),"artifacts truncated")
    check(len({(r["group"],r["entry"]) for r in predicted})==310,"duplicate test-time prediction")
    check(len({r["group"] for r in decisions})==40,"duplicate comparison groups")
    docs=sorted({r["doi"] for r in predicted})
    check(len(docs)==28,"paper identity dropped")
    fdict={r["heldout_doi"]:r for r in fold}
    check(set(fdict)==set(docs),"missing LOPO fold")
    for doc in docs:
        expected=sha256("\n".join(x for x in docs if x!=doc).encode()).hexdigest()
        f=fdict[doc]
        check(f["train_doi_sha256"]==expected and int(f["train_papers"])==27,
              "heldout source included in training")
        check(int(f["heldout_entries"])==sum(z["doi"]==doc for z in predicted),"missing heldout entries")
        for b in (json.loads(f["one_feature_beta"]),json.loads(f["three_feature_beta"])):
            check(all(math.isfinite(x) and x>=0 for x in b),"invalid physical penalty coefficient")
    for r in predicted:
        check(r["heldout_fold"]==r["doi"],"paper prediction leakage")
        for key in ("Jhat6_one_feature","Jhat6_three_feature"):
            check(float(r[key])+1e-8 >= float(r["J5"]),"predicted negative cap penalty")
        if float(r["q_S5"]) <= 0.0686:
            check(math.isclose(float(r["Jhat6_three_feature"]),float(r["J5"]),rel_tol=1e-12),
                  "S5 feasible optimum should have zero predicted penalty")
        check(not any("S6" in k for k in r.keys()),"test predictor leak through saved feature table")
    for method in ("STY","S","S5","one_feature","three_feature"):
        correct=sum(x[method+"_correct"]=="1" for x in decisions)
        check(s["performance"][method]["correct"]==correct,"score/table mismatch")
        check(0<=correct<=40,"invalid score")
    print("PASS: 28 genuinely left-out DOI feature-prediction partitions; 310-row source and all baselines locked")


def validate_nh3(root):
    s=json.loads((root/"summary.json").read_text(encoding="utf-8"))
    check(s["original_verdict"]["passes"]==32 and s["original_verdict"]["metrics"]==64,"registered NH3 result changed")
    expected={"A":(28,18),"B":(20,5),"C":(12,9),"E":(3,0),"V":(1,0)}
    for k,(n,c) in expected.items():
        z=s["original_verdict"]["table_breakdown"][k]
        check((z["n"],z["pass"])==(n,c),f"NH3 category {k} drift")
    check(s["source_mixture_vle"]["n"]==28,"BASF points lost")
    files=[
        ("01_five_inlet_joint_closure.csv",5),
        ("02_three_source_flow_consistency.csv",3),
        ("03_four_bed_single_multiplier_audit.csv",4),
        ("04_three_compression_duties.csv",3)]
    for name,n in files:
        check(len(rows(root/name))==n,"partial physical evidence: "+name)
    check(s["source_plant_inlets"]["separator_only_within_20pct"]==1,"separator conditional status changed")
    check(s["two_bed_source_profile"]["unavoidable_worst_multiplicative_discrepancy_factor"]>1,
          "unphysical single-bed reconciliation")
    check(s["no_fit"] is True and s["canonical_NH3_model_modified"] is False,"hidden refit")
    print("PASS: all five source inlets, three independent source-flow bounds, four bed cases, three compressor audits")


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--study",choices=["meoh","nh3"],required=True)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    validate_meoh(args.out) if args.study=="meoh" else validate_nh3(args.out)


if __name__=="__main__":
    main()
