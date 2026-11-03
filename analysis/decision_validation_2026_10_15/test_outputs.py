"""Independent artifact integrity gates; reruns do not rewrite paper or frozen numbers."""
import argparse, csv, json, math
from pathlib import Path

def csvread(path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))
def check(ok, message):
    if not ok: raise AssertionError(message)
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--study",choices=("2","3","4"),required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args();d=args.out
    summary=json.loads((d/"summary.json").read_text())
    if args.study=="2":
        rows=csvread(d/"02_group_robustness.csv")
        check(len(rows)==40,"wrong group count")
        check(len({x["group"] for x in rows})==40,"duplicated group")
        s=summary["study2"]
        check(s["anchors"]=={"S5":15,"S6":28,"true_inert_S6":18},"anchor drift")
        for kind in ("canonical_all","published_limit_envelope","model_form_at_6p86","published_plus_model_form"):
            x=s[kind]["classification"]
            check(sum(x.values())==40,"incomplete trichotomy")
            check(len(s[kind]["inverted_all_bootstrap_ci95"])==2,"bootstrap missing")
    elif args.study=="3":
        r=csvread(d/"03_group_predictions.csv")
        f=csvread(d/"03_folds.csv")
        check(len(r)==40 and len(f)==28,"CV cohort incomplete")
        for x in r:
            check(x["doi"] in {v["doi"] for v in f},"missing training fold")
            check(x["cv_correct"] in ("0","1"),"invalid held-out score")
        m=summary["study3"]["rules"]
        check(math.isclose(m["STY"]["accuracy"],.3),"baseline accuracy drift")
        check(math.isclose(m["S"]["accuracy"],.575),"baseline selectivity drift")
    else:
        r=csvread(d/"04_industrial_metric_ledger.csv")
        b=csvread(d/"04_kinetic_model_bridge.csv")
        check(len(r)==64 and len({x["metric_id"] for x in r})==64,"64-case ledger integrity")
        check(bool(b),"empty model bridge")
        s=summary["study4"]
        check(s["passes"]==32 and s["pressure_range_overlap"] is False,"NH3 fixed anchors")
        check(s["energy_comparison"]["same_sign"] is False,"unexpected KAAP sign agreement")
    print("PASS: artifact contract for study",args.study)

if __name__=="__main__":
    main()
