#!/usr/bin/env python3
"""Source-data consistency and independence audit of the four MeOH survivors.

Only numerical quantities verified in accessible paper main text are marked as
'external_crosscheck'. Internal CSV checks verify transcription consistency,
NOT independent manual validation of paywalled original supplementary tables.
No frozen data is overwritten.
"""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
RECORDS = ROOT / "agent/extraction/out/records_normalized.csv"
ENGINE = (ROOT / "analysis/meoh_engineering_envelope_2026_10_12"
          / "results/engineering_summary.json")
JOINT = (ROOT / "analysis/field_robustness_2026_10_12"
         / "results/joint_summary.json")
RE = "10.1021/acscatal.5c05984"
INNI = "10.1126/sciadv.abi6012"
IN2O3 = "10.1016/j.jes.2023.05.010"
EVIDENCE = {
    RE: {
        "public_main_text": "https://doi.org/10.1021/acscatal.5c05984",
        "source": "ACS Catalysis Re/TiO2, Table 4, rows 3 and 11",
        "limitations": "Paper reports methanol STY per gram Re; the process model needs per gram catalyst. Qualifiers '<1' indicate detection/reporting limits.",
    },
    INNI: {
        "public_main_text": "https://doi.org/10.1126/sciadv.abi6012",
        "source": "Science Advances, Figure 2A/2B and Results section",
        "limitations": "Figure 2A STY is derived from printed conversion/selectivity and mass-based space velocity, not separately printed; CO/CH4 values originate from SI and need source-level recheck.",
    },
    IN2O3: {
        "public_main_text": "https://doi.org/10.1016/j.jes.2023.05.010",
        "source": "J. Environmental Sciences bare In2O3 morphologies, SI Table S5",
        "limitations": "Original SI Table S5 is not independently visible in the accessible public abstract; CO and CH4 not printed for the comparison. Public article says an Ar/N2 dilution is used for another series; the SI bare-control feed's dilution is not resolved by normalized records.",
    },
}


def read(path):
    with path.open(newline="", encoding="utf-8-sig") as fd:
        return list(csv.DictReader(fd))


def close(value, expected, label, tol=1e-6):
    if value is None or str(value).strip() == "":
        raise AssertionError(f"Missing numeric {label}")
    got = float(value)
    if not math.isclose(got, expected, rel_tol=tol, abs_tol=tol):
        raise AssertionError(f"{label}: actual {got}, expected {expected}")
    return got


def get(rows, doi, location):
    matches = [r for r in rows if r["doi"] == doi and r["entry_label"] == location]
    if len(matches) != 1:
        raise AssertionError(f"Expected one source record for {doi} {location}, found {len(matches)}")
    return matches[0]


def site_check(records, doi, label, expected):
    r = get(records, doi, label)
    for column, target in expected.items():
        close(r[column], target, f"{doi}::{label}::{column}")
    return r


def audit():
    raw = read(RECORDS)
    # Re/TiO2 at 100 bar, 200 C, H2/CO2=4, 10000 ml / (gcat h).
    # The original article reports e.g. 55 vs 18 g MeOH / (g Re h),
    # so per-catalyst STYs are 0.55 and 0.90 g / (gcat h).
    re_1 = site_check(raw, RE, "Table 4 row 3",
                      dict(metal_wt_pct=1., T_K=473.15, P_bar=100.,
                           H2_CO2=4., X_CO2_pct=19., S_MeOH_pct=99.,
                           STY_g_gmetal_h=55., STY_g_gcat_h=.55,
                           GHSV_NL_gcat_h=10.))
    re_5 = site_check(raw, RE, "Table 4 row 11",
                      dict(metal_wt_pct=5., T_K=473.15, P_bar=100.,
                           H2_CO2=4., X_CO2_pct=33., S_MeOH_pct=97.,
                           STY_g_gmetal_h=18., STY_g_gcat_h=.90,
                           GHSV_NL_gcat_h=10.))
    for r in [re_1, re_5]:
        calc = float(r["STY_g_gmetal_h"]) * float(r["metal_wt_pct"]) / 100.
        close(r["STY_g_gcat_h"], calc, "Re STY metal-to-catalyst conversion")
        if r["sty_basis"] != "per_g_metal":
            raise AssertionError("Re source STY unit provenance has drifted")
    if not .90 > .55:
        raise AssertionError("Expected per-catalyst STY winner 5wt Re")
    # InNi3C0.5 at 40 bar, 300 C; Fig. 2A = 12, Fig. 2B = 24 NL/gcat/h.
    entries = {
        "12_sio2": ("Fig. 2A, InNi3C0.5/SiO2, 12000 ml gcat-1 hour-1",
                    dict(T_K=573.15, P_bar=40., H2_CO2=3., GHSV_NL_gcat_h=12.,
                         X_CO2_pct=2.5, S_MeOH_pct=90.)),
        "12_mzro2": ("Fig. 2A, InNi3C0.5/m-ZrO2, 12000 ml gcat-1 hour-1",
                     dict(T_K=573.15, P_bar=40., H2_CO2=3., GHSV_NL_gcat_h=12.,
                          X_CO2_pct=11.2, S_MeOH_pct=85.4)),
        "24_sio2": ("Fig. 2B, InNi3C0.5/SiO2, 24000 ml gcat-1 hour-1",
                    dict(T_K=573.15, P_bar=40., H2_CO2=3., GHSV_NL_gcat_h=24.,
                         X_CO2_pct=2.2, S_MeOH_pct=94.9, STY_g_gcat_h=.18)),
        "24_mzro2": ("Fig. 2B, InNi3C0.5/m-ZrO2, 24000 ml gcat-1 hour-1",
                     dict(T_K=573.15, P_bar=40., H2_CO2=3., GHSV_NL_gcat_h=24.,
                          X_CO2_pct=8.5, S_MeOH_pct=87.9, STY_g_gcat_h=.62)),
    }
    data = {k: site_check(raw, INNI, label, cols) for k, (label, cols) in entries.items()}
    for k in ("12_sio2", "12_mzro2"):
        if data[k]["STY_g_gcat_h"]:
            raise AssertionError("Fig.2A STY was not printed in the source records")
    for k in ("24_sio2", "24_mzro2"):
        if data[k]["sty_basis"] != "per_g_catalyst":
            raise AssertionError("Fig.2B productivity basis drifted")
    # The In2O3-HM/NS pair is SI-sourced and *not* independently verified.
    bare = {
        "si_ns": ("SI Table S5 row In2O3-NS",
                  dict(T_K=573.15, P_bar=30., H2_CO2=4.,
                       X_CO2_pct=9.15, S_MeOH_pct=44.08, STY_g_gcat_h=.17)),
        "si_hm": ("SI Table S5 row In2O3-HM",
                  dict(T_K=573.15, P_bar=30., H2_CO2=4.,
                       X_CO2_pct=5.43, S_MeOH_pct=53.23, STY_g_gcat_h=.12)),
    }
    bare_records = {k: site_check(raw, IN2O3, loc, values)
                    for k, (loc, values) in bare.items()}
    if any(bare_records[k]["S_CO_pct"] or bare_records[k]["S_CH4_pct"] for k in bare_records):
        raise AssertionError("Missing secondary product fields were silently replaced")

    joint = json.loads(JOINT.read_text(encoding="utf-8"))
    engineering = json.loads(ENGINE.read_text(encoding="utf-8"))
    expected = [x["group"] for x in
                joint["cross_inlet_sameT_other_catalyst_gt5"]["groups_and_dois"]]
    if len(expected) != 4 or {g.split(" | ", 1)[0] for g in expected} != set(EVIDENCE):
        raise AssertionError("Unexpected set of source-sensitive candidates")
    physical = {}
    for key, value in engineering["scenarios"].items():
        survived = [x["group"] for x in
                    value["robust_sameT_gt5_all_three_inlets"]["cases"]]
        physical[key] = {
            "groups_scored_6p86": value["inlets"]["inlet_6p86"]["groups_scored"],
            "reversal_cases_all_3_inlet_envelopes": len(survived),
            "original_4_survived": len(set(expected) & set(survived)),
            "original_4_now_unscorable_or_no_longer_material": sorted(set(expected) - set(survived)),
            "unreviewed_new_paper_dois": sorted(
                {g.split(" | ", 1)[0] for g in survived} - set(EVIDENCE)),
        }
    report = {
        "status": "Source-level numerical crosscheck, NOT an independent audit of every SI table or cooled reactor.",
        "paper_dois": list(EVIDENCE),
        "source_evidence": EVIDENCE,
        "re": {
            "per_metal_reported_sty": {"1_wt_pct":55., "5_wt_pct":18.},
            "converted_per_catalyst_sty": {"1_wt_pct":.55, "5_wt_pct":.90},
            "upstream_winner_per_g_catalyst": "5 wt% Re/TiO2",
            "qualifier_caution": "'<1%' product values mean reporting limits, not verified chemical zeros",
            "verification": "Table rows match accessible article main text, and internal extraction unit conversion checks pass",
        },
        "inni": {
            "12_NL_gcat_h": {"SiO2_X_pct": 2.5, "m_ZrO2_X_pct":11.2,
                            "STY_from_X_S_GHSV": True, "STY_not_independently_printed":True},
            "24_NL_gcat_h": {"SiO2_STY_g_gcat_h": .18,
                            "m_ZrO2_STY_g_gcat_h": .62,
                            "STY_printed_in_paper": True},
            "remaining": "Independent page-by-page recheck of SI product CO and CH4 selectivities",
        },
        "in2o3": {
            "curated_si_values_consistent": True,
            "independently_verified_against_original_si": False,
            "missing_CO_CH4": True,
            "feed_uncertainty": "The public main article includes H2:CO2:Ar (or caption N2) = 4:1:1. The extracted bare-catalyst SI Table S5 records only H2:CO2=4, so lab inert dilution for those specific controls requires checking original SI.",
        },
        "engineering_context": physical,
        "outstanding_human_work": [
            "Independent visual/manual verification of Hou et al. SI Table S5 and bare-catalyst feed conditions",
            "Source-page verification of both InNi3C0.5 CO and CH4 product columns and the Fig.2A STY reconstruction",
            "Obtain measured reactor geometry, pellet properties, variable pressure-drop and allowable module size; the existing 1.5-bar fixed assumption is not physical scale-up validation",
            "Review new comparison papers that emerge after equipment caps (see unreviewed_new_paper_dois), without conflating group with DOI independence",
        ],
    }
    return report


def main():
    out = HERE / "results"
    out.mkdir(parents=True, exist_ok=True)
    result = audit()
    (out / "source_verification.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "Re_STY_gcat_1wt": result["re"]["converted_per_catalyst_sty"]["1_wt_pct"],
        "Re_STY_gcat_5wt": result["re"]["converted_per_catalyst_sty"]["5_wt_pct"],
        "papers": len(result["paper_dois"]),
        "in2o3_SI_independent": result["in2o3"]["independently_verified_against_original_si"],
        "new_equipment_survivor_papers_needing_QA": sorted(
            {d for v in result["engineering_context"].values()
             for d in v["unreviewed_new_paper_dois"]}),
    }, indent=2))


if __name__ == "__main__":
    main()
