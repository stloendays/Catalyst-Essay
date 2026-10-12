#!/usr/bin/env python3
"""Read-only DOI-level source erratum proposal for ALL Hou 2024 extracted entries.

Original publisher article Section 1.4 specifies Au/In2O3 and bare In2O3
activity test gas H2:CO2:Ar=4:1:1. Its SI Table S5 abbreviates H2:CO2=4.
Neither the existing extracted CSV nor the frozen 310 printed cohort is edited.

This creates an auditable, REVIEW-REQUIRED sidecar ledger. Plot-read entries
with absent gas details are marked 'verify figure caption before applying'.
It does NOT promote plotted values to printed evidence.

Publisher source original PDFs and SI live ONLY in the private companion repo;
DOI, page, source-file SHA and brief facts are sufficient here.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
DOI="10.1016/j.jes.2023.05.010"
SOURCE=ROOT/"agent/extraction/out/records_normalized.csv"
COHORT=ROOT/"analysis/meoh_literature_inversion_2026_10_05/literature_candidates.csv"
FEED="H2:CO2:Ar = 4:1:1"
INERT="0.16666666666666666"
SOURCE_SHA={
    "paper_pdf":"a42b9e52bc33b8de323be4c2010b4c9d7faaeb1934fef96c7c6cd7f213ff51b7",
    "si_pdf":"e429573f05bdd233f96963d397f6cd1ca802edf23e49adf42923b73b8aceb446",
    "si_docx":"effbce2d5cad7d88183bd3e6851cc3c809eb6977f19148b55d6b70d4034ea8fe",
}
CATEGORIES=("incorrect_N2_species","reactants_ratio_only","source_feed_absent")

def read(p):
    with p.open(newline="",encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

def old_feed_class(record):
    f=record.get("feed","").strip()
    if not f:
        return "source_feed_absent"
    if re.search(r"\bN\s*2\b|nitrogen",f,re.I):
        return "incorrect_N2_species"
    if re.search(r"H\s*2.*CO\s*2",f,re.I) and not re.search(r"\bAr\b",f,re.I):
        return "reactants_ratio_only"
    raise AssertionError(f"Unexpected unclassified old feed {f!r}; protocol must be reviewed")

def run(out):
    raw=read(SOURCE)
    subset=[r for r in raw if r["doi"]==DOI]
    cohort={r["entry"] for r in read(COHORT) if r["doi"]==DOI}
    if len(subset)!=30 or len(cohort)!=6:
        raise AssertionError("Unexpected Hou source records or printed cohort identity")
    if len({r["entry_label"] for r in subset})!=30:
        raise AssertionError("Duplicate Hou normalized source entry names")
    counters=Counter()
    matched=[]
    for r in subset:
        old=r.get("inert_frac","").strip()
        cat=old_feed_class(r)
        counters[cat]+=1
        if old=="":
            counters["old_inert_fraction_unreported"]+=1
        elif float(old)==0.:
            counters["old_inert_fraction_zero"]+=1
        elif abs(float(old)-1/6)<1e-10:
            counters["old_inert_fraction_already_1over6"]+=1
        else:
            raise AssertionError(f"Unexpected Hou inert fraction {old!r}")
        primary=r["entry_label"] in cohort
        if primary:
            counters["original_printed_cohort_entries"]+=1
        if cat=="source_feed_absent":
            review="REQUIRES_MANUAL_SOURCE_FIGURE_CAPTION_REVIEW_BEFORE_DATA_CHANGE"
        else:
            review="MAIN_ARTICLE_PROTOCOL_SUPPORTS_PROPOSAL_REVIEW_BEFORE_DATA_CHANGE"
        proposed=dict(
            doi=DOI,
            entry_label=r["entry_label"],
            catalyst=r.get("catalyst_name",""),
            temperature_K=r.get("T_K",""),
            primary_310_printed_cohort=primary,
            old_feed_text=r.get("feed",""),
            old_inert_fraction=old,
            old_feed_problem=cat,
            proposed_feed_text=FEED,
            proposed_inert_fraction=INERT,
            proposed_lab_y_CO2=INERT,
            proposal_status="UNAPPLIED_SIDE_CAR",
            review_gate=review,
            source_method="main article Section 1.4; SI Table S5 only prints reactant H2:CO2=4",
            change_to_reported_STY="NO",
            change_to_printed_X_or_selectivity="NO",
            potential_plot_read_record=r["entry_label"].startswith("SI Figure"),
            source_pdf_sha256=SOURCE_SHA["paper_pdf"],
        )
        matched.append(proposed)
    expected_counts={
        "incorrect_N2_species":13,
        "reactants_ratio_only":5,
        "source_feed_absent":12,
        "old_inert_fraction_unreported":12,
        "old_inert_fraction_zero":3,
        "old_inert_fraction_already_1over6":15,
        "original_printed_cohort_entries":6,
    }
    for field,expected in expected_counts.items():
        if counters[field]!=expected:
            raise AssertionError(f"{field} changed from expected {expected} to {counters[field]}")
    scored=[x for x in matched if x["primary_310_printed_cohort"]]
    scored_old_zero=[x for x in scored if x["old_inert_fraction"]=="0.0"]
    if len(scored_old_zero)!=3 or not all(x["entry_label"].startswith("SI Table S5 row In2O3-") for x in scored_old_zero):
        raise AssertionError("The primary printed cohort should have EXACTLY 3 missing-Ar bare source rows")
    out.mkdir(parents=True,exist_ok=True)
    columns=list(matched[0])
    with (out/"hou_30_entry_proposed_source_erratum.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=columns)
        w.writeheader()
        w.writerows(matched)
    summary={
        "status":"PROPOSAL ONLY. No frozen records or prior model output changed.",
        "doi":DOI,
        "original_record_count":len(subset),
        "original_printed_cohort_entries":len(scored),
        "original_printed_cohort_bare_yco2_misassignments":len(scored_old_zero),
        "source_evidence":"SHA verified in private Catalyst-Essay-sources freeze-field-2026-10-12: original paper Section 1.4 H2:CO2:Ar=4:1:1 for Au and bare In2O3; SI Table S5 abbreviates H2:CO2=4.",
        "private_original_sha256":SOURCE_SHA,
        "curated_record_issue_counts":dict(counters),
        "proposal_new_complete_lab_feed":FEED,
        "proposal_new_lab_inert_fraction":1/6,
        "source_scope":"All 30 Hou activity extraction entries including 24 non-primary plot/extraction rows; the main 310 printed cohort includes only 6 Hou entries and only 3 need yCO2 correction.",
        "future_work":[
          "Do not apply proposals automatically until approved, especially 12 SI Figure records without original feed metadata",
          "Replace N2 label by Ar where verified, even if yCO2 fraction already correct: source chemical identity matters for laboratory Peng-Robinson EOS",
          "Do not change experimentally printed conversion, methanol selectivity or STY",
          "Re-score all-entries (not only 310 printed cohort) only after checking each relevant SI plot record and the selected modeling cohort",
          "Keep laboratory Ar separate from the industrial process recycle/inlet bounds",
        ],
    }
    (out/"hou_source_erratum_proposal_summary.json").write_text(
        json.dumps(summary,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps(summary,indent=2,ensure_ascii=False))
    return summary

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output",type=Path,default=ROOT/"analysis/meoh_hou_source_provenance_2026_10_12/results")
    args=p.parse_args()
    run(args.output)

if __name__=="__main__":
    main()
