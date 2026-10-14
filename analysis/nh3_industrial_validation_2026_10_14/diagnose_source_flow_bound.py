#!/usr/bin/env python3
"""Source-only NH3 make-up/recycle bounds for three industrial converter inlets.

This checks the equivalence of plant observations to ONE ideal saturated
separator feeding an NH3-free makeup stream. It is conditional on a simplified
flowsheet; violations do not invalidate actual plants or prove an EOS is wrong.

Independent of DFT, Fe/Ru rate laws, converter volume or cost optimisation.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from audit_industrial import SRC, PINS, enforce_pin, rows
from diagnose_separator_vle import grid_from_printed_sources, source_interpolation

MW_NH3_KG_MOL = 0.017031
NORMAL_M3_MOL = 0.022414
CASES = {
    "TOP140": {"inlet_id":"A01","flow_id":"A03","capacity_ref":"R1060"},
    "TOP220": {"inlet_id":"A04","flow_id":"A06","capacity_ref":"R1052"},
    "UHDE188":{"inlet_id":"A07","flow_id":"A09","capacity_ref":"R0001"},
}


def minimum_stoichiometric_makeup_Nm3_h(tpd: float) -> float:
    """2 mol reactive syngas consumed per mol NH3 produced; no purge/inert losses."""
    if tpd <= 0:
        raise ValueError("Positive production required")
    nh3_mol_h = tpd * 1000.0 / MW_NH3_KG_MOL / 24.0
    return 2.0 * nh3_mol_h * NORMAL_M3_MOL


def single_separator_inlet_limit_pct(separator_y_pct: float, inlet_Nm3_h: float,
                                      makeup_min_Nm3_h: float) -> float:
    """Optimistic upper bound if sole NH3 source is one recycle separator vapor.

    y_in= ysep*(1-Fmakeup/Ftotal) <= ysep*(1-Fmakeup_min/Ftotal).
    """
    if not 0 <= separator_y_pct < 100:
        raise ValueError("Separator fraction outside domain")
    if inlet_Nm3_h <= 0 or makeup_min_Nm3_h < 0:
        raise ValueError("Invalid streams")
    if makeup_min_Nm3_h >= inlet_Nm3_h:
        raise ValueError("Published inlet cannot hold minimum reactive feed at that production")
    return separator_y_pct * (1.0 - makeup_min_Nm3_h/inlet_Nm3_h)


def records():
    for p in ("benchmark_metrics.csv","benchmark_cases.csv","reference_values.csv"):
        enforce_pin(SRC/p, PINS[p])
    metrics = {r["metric_id"]:r for r in rows(SRC/"benchmark_metrics.csv")}
    cases = {r["case_id"]:r for r in rows(SRC/"benchmark_cases.csv")}
    refs = {r["row_id"]:r for r in rows(SRC/"reference_values.csv")}
    grid=grid_from_printed_sources()
    report=[]
    for cid,spec in CASES.items():
        a,b=metrics[spec["inlet_id"]],metrics[spec["flow_id"]]
        case=cases[cid];cap=refs[spec["capacity_ref"]]
        assert a["case_id"]==b["case_id"]==cid
        assert a["quantity"]=="inlet_NH3_molpct" and b["quantity"]=="inlet_Nm3_h"
        assert cap["quantity"]=="capacity_tpd" and cap["kind"]=="source_fact"
        assert abs(float(cap["value"])-float(case["capacity_tpd"]))<1e-9
        assert a["counted"]==b["counted"]=="yes"
        for metric in (a,b):
            for k in metric["ref_rows"].split():
                if k not in refs: raise AssertionError(f"Unsourced {cid}: {k}")
                if refs[k]["kind"] not in ("source_fact","derived"):
                    raise AssertionError(f"{cid} inlet uses non-primary source row {k}")
        y_plant=float(a["industrial_value"])
        inlet=float(b["industrial_value"])
        capacity=float(cap["value"])
        ysep=source_interpolation(grid,float(case["Tsep_C"]),float(case["P_bar"]))
        makeup=minimum_stoichiometric_makeup_Nm3_h(capacity)
        y_max=single_separator_inlet_limit_pct(ysep,inlet,makeup)
        dilution=1-makeup/inlet
        report.append(dict(
            case_id=cid,
            inlet_concentration_metric_id=a["metric_id"],
            inlet_flow_metric_id=b["metric_id"],
            capacity_source_row=spec["capacity_ref"],
            source_rows=";".join([a["ref_rows"],b["ref_rows"],spec["capacity_ref"]]),
            source_inlet_NH3_molpct=y_plant,
            source_inlet_Nm3_h=inlet,
            source_design_tpd=capacity,
            Tsep_C=float(case["Tsep_C"]),
            P_bar=float(case["P_bar"]),
            BASF_saturated_vapor_pct=ysep,
            minimum_stoichiometric_makeup_Nm3_h=makeup,
            optimistic_max_recycle_share=dilution,
            optimistic_max_inlet_NH3_pct=y_max,
            observed_over_optimistic_bound=y_plant/y_max,
            separator_y_required_at_minimum_makeup_pct=y_plant/dilution,
            source_inlet_greater_than_BASF_vapor=y_plant>ysep,
            source_inlet_greater_than_optimistic_bound=y_plant>y_max,
            status="CONDITIONAL_SOURCE_ONLY_MASS_BALANCE_DIAGNOSTIC_NOT_VALIDATED_VLE",
            interpretation="Single saturated 1:3 N2/H2 separator, NH3-free makeup, printed flows at design production; source topology and gas mixture may differ",
        ))
    return report


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--out-dir",type=Path,required=True)
    args=parser.parse_args()
    args.out_dir.mkdir(parents=True,exist_ok=True)
    data=records()
    with (args.out_dir/"source_mass_balance_bounds_3.csv").open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(data[0]))
        w.writeheader();w.writerows(data)
    s={
        "n":len(data),"n_above_upper_bound_under_assumptions":sum(x["source_inlet_greater_than_optimistic_bound"] for x in data),
        "status":"CONDITIONAL_SOURCE_ONLY_FLOWSHEET_INCONSISTENCY_NOT_A_VALIDATED_PLANT_ERROR",
        "source_accounting":"stoichiometric minimum reactive makeup 2 mol N2+H2 per mol NH3; nominal source production treated as matching inlet flow",
        "physical_scope":"single BASF-equivalent liquid NH3 separator vapor; stoichiometric NH3-free makeup and no other NH3-containing inlet streams",
        "nonapplicability":"real separator mixture thermodynamics, inerts, purges, operating load, and multiple separators/recirculation layouts may invalidate the simplified comparator",
        "baseline_registered_score_untouched":"32/64",
        "rows":data
    }
    (args.out_dir/"summary.json").write_text(json.dumps(s,indent=2)+"\n",encoding="utf-8")
    lines=["# NH3 source-only fresh-feed dilution consistency bound", "",
           "**Conditional design-basis cross-check, independent of catalyst kinetics and optimisation.**",
           "Equation: y_in <= y_sep [1 - F_makeup,minimum / F_in], with F_makeup,minimum = 2 n_NH3 produced.",
           "", "| Published plant | Published inlet % | BASF vapor % | Optimistic inlet limit % | Actual / upper bound |",
           "|---|---:|---:|---:|---:|"]
    for x in data:
        lines.append(f"| {x['case_id']} | {x['source_inlet_NH3_molpct']:.2f} | "
                     f"{x['BASF_saturated_vapor_pct']:.3f} | "
                     f"{x['optimistic_max_inlet_NH3_pct']:.3f} | "
                     f"{x['observed_over_optimistic_bound']:.2f} |")
    lines+=["",
        "The three observed inlet percentages exceed this optimistic upper bound *under the stated surrogate flowsheet*. "
        "The printed values are internally sourced from the same identified plant design cases, but the "
        "source gas-phase mixture and separator topology are not equivalent to the single ideal reference.",
        "This does not demonstrate a real mass-conservation violation: BASF table data are for 1:3 N2/H2 "
        "saturation over liquid ammonia, whereas the actual processes can have inerts, "
        "purge, different pressure boundaries, more than one separator, and different operating load.",
        "The 1000/1500 tpd numbers are design-basis production rates, treated here as coincident with the "
        "reported inlet flows. Unit convention: 1 mol gas at 0 C and 1 atm occupies 0.022414 Nm3.",
        "No costs, rankings, scientific model equations, or preregistered scores are changed.", ""]
    (args.out_dir/"REPORT.md").write_text("\n".join(lines),encoding="utf-8")
    print(f"PASS: {len(data)} source-only mass-balance checks; "
          f"{s['n_above_upper_bound_under_assumptions']} violate surrogate upper bound (conditional)")


if __name__=="__main__":
    main()
