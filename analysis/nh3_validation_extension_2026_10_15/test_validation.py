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


def check_transfer(folder):
    s=json.loads((folder/"summary.json").read_text(encoding="utf-8"))
    rows_=csvread(folder/"01_five_industrial_inlet_transfer.csv")
    require(len(rows_)==20,"five published industrial test points x four models missing")
    require(len({(r["metric_id"],r["method"]) for r in rows_})==20,"duplicate industrial comparator")
    require({r["metric_id"] for r in rows_}=={"A01","A04","A07","A14","A16"},
            "source original fixed plant cases changed")
    require(s["industrial_targets_used_for_fitting"] is False and
            s["original_64_case_registered_score_unchanged"]=="32/64",
            "unregistered industrial fitting or score change")
    require(s["fixed_policies"]["M0_frozen"]["within_20pct"]==0,
            "canonical VLE baseline falsely altered")
    require(s["fixed_policies"]["BASF_bilinear"]["within_20pct"]==1,
            "original source-only 1/5 transfer replaced")
    for m in ("M0_frozen","BASF_bilinear","M1_source_fit","M2_source_fit"):
        subset=[r for r in rows_ if r["method"]==m]
        require(len(subset)==5,"missing candidate plant inlet model")
        success=sum(r["within_original_20pct"]=="1" for r in subset)
        require(success==s["fixed_policies"][m]["within_20pct"],
                "conditional cross-source pass count table mismatch")
        require(all(r["original_64_case_verdict"]=="FAIL" for r in subset),
                "unregistered original plant scores changed")
    require((folder/"REPORT.md").exists(),"source transfer report missing")
    print("PASS: no-fit-to-plant transfer over all five original, still-failing industrial benchmark cases")


def check_uhde(folder):
    s=json.loads((folder/"summary.json").read_text(encoding="utf-8"))
    rs=csvread(folder/"01_uhde_two_gas_separators.csv")
    require(len(rs)==8 and len({(x["stream_id"],x["method"]) for x in rs})==8,
            "source 2 separators times 4 original/independent source models incomplete")
    require(s["count_independent_plants"]==1 and s["count_gas_streams"]==2,
            "artificially multiplied independent industrial sample size")
    require(s["source_source_git_blob"]=="7d511a788895d1f3ab825f9db9a3f0929db44460",
            "source Figure 57 pin changed")
    require(s["original_registered_industrial_NH3_score"]=="32/64 unchanged",
            "illegal promotion of VLE transfer into industrial metric")
    for m in ("M0_ideal","BASF_interpolated","M1_source_fit","M2_source_fit"):
        x=[r for r in rs if r["method"]==m]
        require(len(x)==2 and {r["stream_id"] for r in x}=={"5","6"},
                "source vapor rows changed")
        require(s["outcomes"][m]["within_20pct"]==sum(z["within_20pct"]=="1" for z in x),
                "vapor source comparison count drift")
        require(all(0<float(z["predicted_vapor_NH3_molpct"])<100 for z in x),
                "nonphysical source gas vapor fraction")
    require((folder/"REPORT.md").exists(),"no source caveats")
    print("PASS: two Git-blob-pinned UHDE gas-phase source streams remain ONE plant, and original 32/64 unchanged")


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--study",choices=("vle","energy","transfer","uhde"),required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    if a.study=="vle":check_vle(a.out)
    elif a.study=="energy":check_energy(a.out)
    elif a.study=="transfer":check_transfer(a.out)
    else:check_uhde(a.out)


if __name__=="__main__":
    main()
