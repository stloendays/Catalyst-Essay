"""Synthetic mathematical checks and independent result gates for source-only NH3 studies."""
from __future__ import annotations
import argparse
import csv
import json
import math
from pathlib import Path
import unittest

import vle_cv


class TheoryChecks(unittest.TestCase):
    def test_effective_pressure_one_parameter(self):
        k0=3.1e-5
        rows=[{"X":x,"z":k0*x} for x in (2100.,3600.,5500.,7700.)]
        a,k=vle_cv.fit(rows,1)
        self.assertEqual(a,0.)
        self.assertAlmostEqual(k,k0,places=12)

    def test_effective_pressure_intercept(self):
        a0=0.11;k0=4.3e-5
        rows=[{"X":x,"z":a0+k0*x} for x in (2100.,3600.,5500.,7700.)]
        a,k=vle_cv.fit(rows,2)
        self.assertAlmostEqual(a,a0,places=12)
        self.assertAlmostEqual(k,k0,places=12)

    def test_pressure_nonnegative(self):
        a,k=vle_cv.fit([{"X":x,"z":-0.0002*x} for x in (2100.,3600.,5500.,7700.)],1)
        self.assertEqual(a,0.)
        self.assertEqual(k,0.)

    def test_prevent_train_test_overlap(self):
        data=[{"key":f"{t}_{p}","T_C":t,"P_MPa":p} for t in vle_cv.T_GRID for p in vle_cv.P_GRID]
        for t in vle_cv.T_GRID:
            train,test=vle_cv._fold(data,"leave_temperature_out",t)
            self.assertEqual((len(train),len(test)),(24,4))
        for p in vle_cv.P_GRID:
            train,test=vle_cv._fold(data,"leave_pressure_out",p)
            self.assertEqual((len(train),len(test)),(21,7))


def csvread(path):
    with path.open(encoding="utf-8",newline="") as f:return list(csv.DictReader(f))


def require(ok,reason):
    if not ok:raise AssertionError(reason)


def check_vle(folder):
    s=json.loads((folder/"summary.json").read_text(encoding="utf-8"))
    grid=csvread(folder/"01_source28.csv")
    folds=csvread(folder/"02_locked_holdout_folds.csv")
    preds=csvread(folder/"03_blocked_source_predictions.csv")
    require(len(grid)==28 and len(folds)==33 and len(preds)==168,
            "source stratification lost or invented rows")
    require(len({(x["T_C"],x["P_MPa"]) for x in grid})==28,"source grid unique points")
    require(s["n_pinned_source_points"]==28 and (s["n_temperature_folds"],s["n_pressure_folds"])==(7,4),
            "source claim did not match artifacts")
    require(s["preregistered_64case_NH3_score_untouched"]=="32/64","unregistered changed score")
    for blocked in vle_cv.BLOCKS:
        for model in vle_cv.MODELS:
            selected=[r for r in preds if r["block"]==blocked and r["method"]==model]
            require(len(selected)==28 and len({r["source_ref_id"] for r in selected})==28,
                    "withheld source cell missing or duplicated")
            count=sum(r["within_registered_plus_minus_20pct"]=="1" for r in selected)
            require(s["outcomes"][blocked][model]["within_20pct"]==count,"source holdout tally drift")
            require(all(0<float(z["predicted_molpct"])<100 for z in selected),
                    "predicted composition nonphysical")
    require((folder/"REPORT.md").exists(),"missing source caveats")
    print("PASS: 168 blocked predictions across 28 pinned BASF values; original industrial judgments untouched")


def check_energy(folder):
    s=json.loads((folder/"summary.json").read_text(encoding="utf-8"))
    e=csvread(folder/"01_preregistered_compressor_scopes.csv")
    k=csvread(folder/"02_Fe_Ru_kinetic_bridge_domains.csv")
    require(len(e)==3 and len({z["metric_id"] for z in e})==3,
            "three compressor source scopes missing")
    require(len(k)==24 and len({(z["pair"],z["model_basis"]) for z in k})==24,
            "24 existing kinetic bridge model pairs changed")
    require(s["original_NH3_scores"]=={"pass":32,"total":64,
           "compressor":{"passed":0,"total":3},"separator":{"passed":0,"total":1}},
           "preregistered physical benchmark changed")
    require(s["compressor"]["all_three_could_pass_single_scalar"] is False,
            "expected scoped correction result changed")
    require(s["rates"]["common_fit_pressure_interval_bar"] is None,
            "measured Fe and promoted Ru/C pressure fit ranges overlap unexpectedly")
    for r in e:
        rel=(float(r["published_MW"])-float(r["original_model_MW"]))/float(r["published_MW"])
        require(abs(rel-float(r["relative_model_shortfall"]))<1e-10,"registered power ratio inconsistent")
    require((folder/"REPORT.md").exists(),"missing source caveats")
    print("PASS: three original failed compression cases and disjoint measured kinetic source-pressure windows preserved")


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--study",choices=("vle","energy"),required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    if a.study=="vle":check_vle(a.out)
    else:check_energy(a.out)


if __name__=="__main__":
    main()
