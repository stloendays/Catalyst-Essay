#!/usr/bin/env python3
"""Independently published Table8 PR kij transfer, same frozen BASF/Uhde holdouts.

No parameters are inferred from either 28 BASF source rows or two Uhde
separator observations. A manuscript-use PASS requires the same predeclared
physics gate; automatic numerical tests PASS separately.
"""
from __future__ import annotations
import argparse
import csv
import json
import math
from pathlib import Path

from run_screen import ACCEPTANCE, report_saturation, dry_ratio
from diagnose_separator_vle import grid_from_printed_sources
from species_reconstruct import load_streams
from thermo_published_bip import (
    PUBLISHED_BIP, PROVENANCE_URL, SOURCE_SCOPE, MISSING_PAIR_POLICY,
    external_nh3_vapor_over_pure_liquid
)


def evaluate()->dict:
    table=grid_from_printed_sources()
    baseline,baseline_summary,baseline_plants=report_saturation()
    b_lookup={(v["T_C"],v["P_MPa"]):v for v in baseline}
    rows=[]
    for (T_C,P_MPa),truth in sorted(table.items()):
        v=external_nh3_vapor_over_pure_liquid(
            T_C+273.15,P_MPa*1e6,{"N2":1.0,"H2":3.0})
        actual=truth["source_y_pct"]
        error=(v["y_NH3_molpct"]/actual-1.0)*100
        prev=b_lookup[T_C,P_MPa]
        rows.append({
            "source_row_id":truth["row_id"],"T_C":T_C,"P_MPa":P_MPa,
            "BASF_NH3_pct":actual,
            "PR_no_fit_kij_zero_pct":prev["PR78_no_kij_pure_liquid_NH3_molpct"],
            "PR_published_reactor_kij_pct":v["y_NH3_molpct"],
            "published_kij_abs_rel_error_pct":abs(error),
            "baseline_zero_kij_abs_rel_error_pct":prev["PR78_abs_relative_error_pct"],
            "within_predeclared_20pct":abs(error)<=20,
            "provenance":"2022 Aspen-HYSYS Table8 published kN2-NH3 0.222, kH2-N2 -0.036",
            "missing_CH4_Ar_pairs":MISSING_PAIR_POLICY,
        })
    st=load_streams()
    gas=[]
    for k,upstream in ((5,4),(6,1)):
        source=st[k]
        v=external_nh3_vapor_over_pure_liquid(
            source["T_C"]+273.15,source["P_MPa"]*1e6,dry_ratio(st[upstream]))
        obs=source["y"]["NH3"]*100
        relative=(v["y_NH3_molpct"]/obs-1.0)*100
        prev=next(x for x in baseline_plants if x["observed_gas_stream"]==k)
        gas.append({
            "source_stream":k,"dry_gas_from_stream":upstream,
            "source_NH3_pct":obs,
            "published_kij_PR_pct":v["y_NH3_molpct"],
            "zero_kij_PR_pct":prev["PR78_NH3_molpct"],
            "published_kij_signed_relative_error_pct":relative,
            "within_predeclared_20pct":abs(relative)<=20,
            "fugacity_ln_residual":v["fugacity_log_residual"],
            "independence":"published kij external; source-conditioned dry mixture excludes target yNH3",
            "cold_separator_extrapolation":SOURCE_SCOPE,
        })
    base_mae=baseline_summary["BASF_mean_abs_relative_pct"]
    cand_mae=sum(x["published_kij_abs_rel_error_pct"] for x in rows)/len(rows)
    candidate_n=sum(x["within_predeclared_20pct"] for x in rows)
    cand_gas_n=sum(x["within_predeclared_20pct"] for x in gas)
    return {
        "publication":PROVENANCE_URL,
        "interactions":{
            "N2-NH3":0.222,"N2-H2":-0.036,"H2-NH3":0.0,
            "CH4/Ar_pairs":"unsourced zero, may not apply to industrial mixture"
        },
        "source_regime_warning":SOURCE_SCOPE,
        "BASF_rows":rows,"plant_rows":gas,
        "comparison":{
            "total_BASF":28,
            "within20_BASF_zero_kij":baseline_summary["n_BASF_under_20pct"],
            "within20_BASF_published_kij":candidate_n,
            "mae_pct_BASF_zero_kij":base_mae,
            "mae_pct_BASF_published_kij":cand_mae,
            "within20_plant_published_kij":cand_gas_n,
            "mae_reduced":cand_mae<base_mae,
            "gate_pass":(
                candidate_n>=ACCEPTANCE["BASF_TABLE_REQUIRE_WITHIN_BAND"] and
                cand_gas_n>=ACCEPTANCE["PLANT_STAGE_REQUIRE_WITHIN_BAND"]
            ),
        },
        "predeclared_science_gate":ACCEPTANCE,
        "scientific_status":"PENDING",
        "no_industrial_recalibration":True,
        "baseline_NH3_FINAL_1_2":"32/64 unchanged"
    }


def run(outdir:Path)->dict:
    d=evaluate()
    d["scientific_status"]=(
        "PASS_EXTERNAL_TABLE_SCREEN__STILL_NEEDS_KIJ_APPLICABILITY"
        if d["comparison"]["gate_pass"]
        else "FAIL__PUBLISHED_REACTOR_BIP_DOES_NOT_VALIDATE_COLD_5COMPONENT_VLE"
    )
    outdir.mkdir(parents=True,exist_ok=True)
    for fn,key in (("BASF_28_published_kij.csv","BASF_rows"),
                   ("Uhde_2_published_kij.csv","plant_rows")):
        with (outdir/fn).open("w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f,fieldnames=list(d[key][0]))
            w.writeheader();w.writerows(d[key])
    (outdir/"summary.json").write_text(json.dumps(d,indent=2)+"\n",encoding="utf-8")
    c=d["comparison"]
    lines=[
        "# Independent 2022 published PR binary-interaction transfer: NH3 cold separator",
        "",
        f"**Scientific status: {d['scientific_status']}**",
        "",
        f"Source Table8: {PROVENANCE_URL}, originally Aspen-HYSYS for Haber synthesis equilibrium.",
        f"Use k_N2-NH3=+0.222, k_N2-H2=-0.036, k_H2-NH3=0; CH4/Ar pairs unsourced and fixed to zero.",
        "",
        "## External BASF 28 source points held out from all interaction parameter selection",
        f"- Zero-kij PR: **{c['within20_BASF_zero_kij']}/28**, MAE **{c['mae_pct_BASF_zero_kij']:.1f}%**.",
        f"- Published 2022 reactor-kij PR: **{c['within20_BASF_published_kij']}/28**, MAE **{c['mae_pct_BASF_published_kij']:.1f}%**.",
        "",
        "## Uhde cold gas NH3, no matching fit",
        "| Stage | Reference gas NH3 % | Zero-kij PR % | Published reactor-kij PR % | Relative error |",
        "|---|---:|---:|---:|---:|"]
    for r in d["plant_rows"]:
        lines.append(f"| {r['source_stream']} | {r['source_NH3_pct']:.3f} | "
                     f"{r['zero_kij_PR_pct']:.3f} | {r['published_kij_PR_pct']:.3f} | "
                     f"{r['published_kij_signed_relative_error_pct']:+.1f}% |")
    lines +=[
        "",
        "## Engineering meaning",
        "This explicitly sourced parameter set was published for Haber *reaction* equilibrium, "
        "not validated at -30 to +30 C against ammonia-rich compressed-liquid phases. "
        "Source Figure57 includes CH4/Ar for which published Table8 gives no pairs. "
        "Retrospective cold-separator transfer cannot claim an accurate industrial VLE. "
        "The unchanged ±20% gate remains an external scientific screen, not the frozen 64-case score.",
        "No industrial target values were used to choose or adjust kij. "
        "No frozen economics, ranking, cost or manuscript data were altered.",
        ""
    ]
    report="\n".join(lines)
    (outdir/"REPORT.md").write_text(report,encoding="utf-8")
    print(report)
    return d


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--out-dir",type=Path,required=True)
    arg=ap.parse_args()
    run(arg.out_dir)
