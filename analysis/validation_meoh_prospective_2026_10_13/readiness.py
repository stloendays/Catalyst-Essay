#!/usr/bin/env python3
"""Read-only PROSPECTIVE-readiness gate: prevent a green frozen-regression job
from being mistaken for completion of the 40-paper prospective experiment.

No changes to PREREGISTRATION.md, prediction_frozen.json, extraction prompts,
DOI order, scoring windows or existing saved extraction records.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
import re
import sys

HERE=Path(__file__).resolve().parent
PASSES=("main","figures","si","si_figures")
RAW_DIRS={"main":"raw","figures":"raw_figures","si":"raw_si","si_figures":"raw_si_figures"}
LIMITS={"max_total_tokens":8_000_000,"max_per_pass":3_000_000}
EXPECTED_PAPERS=40
EXPECTED_PASSES=4
ABSTRACT_FIRST_MAX_RANK=319


def require(c,message):
    if not c: raise AssertionError(message)


def readcsv(path):
    with path.open(encoding="utf-8-sig",newline="") as f:
        return list(csv.DictReader(f))


def safe_name(doi):
    return re.sub(r"[^a-zA-Z0-9]+","_",doi.lower()).strip("_")+".json"


def jsonread(path):
    return json.loads(path.read_text(encoding="utf-8"))


def audit():
    screen=readcsv(HERE/"screening.csv")
    inc=[r for r in screen if r["decision"]=="include"]
    ranks=[int(r["rank"]) for r in inc]
    require(len(inc)==EXPECTED_PAPERS,"prospective inclusion cohort not 40: "+str(len(inc)))
    require(ranks==sorted(ranks) and ranks[-1]==ABSTRACT_FIRST_MAX_RANK,
            "first 40 DOI ordering or inclusion cutoff changed")
    require(len({r["doi"].lower() for r in inc})==EXPECTED_PAPERS,
            "duplicated prospectively included DOI")
    require(all(r.get("s4")=="ok" and int(r.get("s4_files") or 0)>=1 for r in inc),
            "full SI retrieval is still incomplete for an included DOI")
    require((HERE/"PREREGISTRATION.md").exists() and (HERE/"prediction_frozen.json").exists(),
            "preregistered protocol or frozen prior predictions not present")
    prediction=jsonread(HERE/"prediction_frozen.json")
    require("S6" in prediction and "S5" in prediction,
            "frozen S6 and S5 predictions missing")
    fetch=jsonread(HERE/"fetch_manifest.json")
    fetchmap={r["doi"].lower():r for r in fetch}
    require(all(r["doi"].lower() in fetchmap and
                fetchmap[r["doi"].lower()]["status"] in ("ok","skip") and
                fetchmap[r["doi"].lower()].get("file") for r in inc),
            "original S2 PDF manifest lacks a selected DOI")
    try:
        si=jsonread(HERE/"si_manifest.json")
    except FileNotFoundError:
        si=[]
    # SI source assertions rely on screening final stage; absent raw SI PDFs on Actions is expected.
    counted={}
    missing={}
    invalid={}
    for stage in PASSES:
        path=HERE/"out"/RAW_DIRS[stage]
        keep=[];wait=[];bad=[]
        for r in inc:
            pdf=path/safe_name(r["doi"])
            if not pdf.exists():
                wait.append(dict(rank=int(r["rank"]),doi=r["doi"]))
                continue
            try:
                doc=jsonread(pdf)
                require(doc.get("doi","").lower()==r["doi"].lower(),
                        "DOI mismatch in saved extraction")
                require(isinstance(doc.get("records"),list),
                        "missing raw structured records")
                keep.append(dict(rank=int(r["rank"]),doi=r["doi"],n_records=len(doc["records"]),
                                 sha256=hashlib.sha256(pdf.read_bytes()).hexdigest()))
            except (ValueError,AssertionError,UnicodeDecodeError) as e:
                bad.append(dict(rank=int(r["rank"]),doi=r["doi"],error=str(e)))
        counted[stage]=len(keep)
        missing[stage]=wait
        invalid[stage]=bad
    usage_path=HERE/"out"/"token_usage.csv"
    bypass=defaultdict(lambda:{"calls":0,"tokens":0})
    if usage_path.exists():
        for r in readcsv(usage_path):
            pass_name=r.get("pass","")
            if pass_name in PASSES:
                bypass[pass_name]["calls"]+=1
                bypass[pass_name]["tokens"]+=int(r.get("total_tokens") or 0)
    budgets={}
    for stage in PASSES:
        budgets[stage]=dict(
            calls=bypass[stage]["calls"],
            consumed=bypass[stage]["tokens"],
            remaining_at_registered_3M=max(0,LIMITS["max_per_pass"]-bypass[stage]["tokens"]))
    total=sum(v["consumed"] for v in budgets.values())
    total_left=max(0,LIMITS["max_total_tokens"]-total)
    # Gate conditions specified in original protocol's commit order, NOT just existence of predictions.
    evidence={
        "normalized_records":"out/records_normalized.csv",
        "pdf_corrections_or_check_log":"corrections.csv",
        "blind_predictions":"blind_predictions.csv",
        "blind_rankings":"blind_rankings.csv",
        "industrial_results":"results.json",
        "scored_groups":"scored_groups.csv",
        "costed_candidates":"new_candidates_costed.csv"
    }
    # Corrections may legitimately be empty after a valid PDF check; require either a PDF
    # accuracy report or a corrections ledger, with a clear status rather than fabricating one.
    evidence["pdf_check_manifest"]="pdf_check_40.csv"
    present={k:(HERE/v).exists() for k,v in evidence.items()}
    pdf_evidence_present=present["pdf_corrections_or_check_log"] or present["pdf_check_manifest"]
    blockers=[]
    for stage in PASSES:
        if missing[stage] or invalid[stage]:
            blockers.append(f"extract_{stage}: {len(missing[stage])} DOI not present; {len(invalid[stage])} invalid records")
    if not present["normalized_records"]:blockers.append("normalized_records: missing")
    if not pdf_evidence_present:blockers.append("PDF printed-value accuracy audit: missing")
    for name in ("blind_predictions","blind_rankings","industrial_results","scored_groups","costed_candidates"):
        if not present[name]:blockers.append(name+": missing")
    # If final artifact exists, structural source-derived completeness must be checked by frozen scorer/commit-order CI.
    complete=not blockers
    s=dict(status="READY_FOR_FINAL_FROZEN_SCORING" if complete else "INCOMPLETE_NOT_YET_SCORED",
           existing_frozen_regression_is_not_external_validation=True,
           pre_registered_inclusions=EXPECTED_PAPERS,
           selected_rank_cutoff=ranks[-1],
           stages={stage:{"present":counted[stage],"missing":len(missing[stage]),
                          "invalid":len(invalid[stage]),"missing_dois":missing[stage],
                          "invalid_dois":invalid[stage]} for stage in PASSES},
           token_usage={"per_pass":budgets,"total_consumed":total,
                        "remaining_at_registered_8M":total_left},
           final_stage_files=present,
           readiness_blockers=blockers,
           hard_rules={"gpt_model":"gpt-5.5","max_total_tokens":LIMITS["max_total_tokens"],
                       "max_per_pass_tokens":LIMITS["max_per_pass"],
                       "predictions_before_costing":True,"new_papers":40,
                       "no_change_to_original_extraction_prompts":True},
           suspended_automatic_scoring=not complete,
           pdf_and_si_bytes_not_committed_to_git=True,
           next_action="Resume same frozen extraction with valid NUS cached PDFs/SI and original gpt-5.5 route; do not substitute model or exclude DOI after outcomes.")
    # Generate exact ranked DOI list for each pending pass; script never calls an LLM.
    return s


def emit(report,folder):
    folder.mkdir(parents=True,exist_ok=True)
    (folder/"readiness.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    lines=["# PR #80 prospective CO2-to-methanol validation — readiness, not scoring","",
       f"Status: **{report['status']}**.","",
       "40 pre-registered included papers with source-confirmed PDF and SI retrieval; GitHub does NOT store the proprietary PDF/SI bytes, and this Actions job has neither NUS login nor a configured gpt-5.5 API route.","",
       "| Frozen pass | Stored DOI JSON | Missing | API tokens already spent |","|---|---:|---:|---:|"]
    for p in PASSES:
        x=report["stages"][p]
        lines.append(f"| {p} | {x['present']}/40 | {x['missing']} | {report['token_usage']['per_pass'][p]['consumed']:,} |")
        if x["missing"]:
            lines.append("")
            lines.append("## Next DOI resume set for "+p)
            for z in x["missing_dois"]:
                lines.append(f"- rank {z['rank']}: {z['doi']}")
            lines.append("")
    lines.extend(["","## Evidence gates"])
    for x in report["readiness_blockers"]:lines.append("- "+x)
    lines+=["","## Resume operation (run only in the original authorized NUS/API environment)",
            "Never commit proprietary PDFs/SI, tokens, proxy cookies, API keys, or publisher credentials.",
            "Extract each missing DOI in original retrieval order using the existing wrapper and same model, preserving its recorded route, schema and token limits.",
            "Once all four passes exist, run the existing pv.py normalize and the pre-blind random 40-value PDF audit. Apply corrections through the original corrections.csv interface.",
            "Then commit raw/normalized extraction and corrections, generate and commit blind_predictions.csv and blind_rankings.csv BEFORE running the model scorer. After freeze, run score.py and commit results.",
            "This report makes NO claim about P1/P2 and does not alter the original prediction_frozen.json."]
    (folder/"READINESS.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    # Machine-readable manifest of the exact original paper order by pass.
    with (folder/"resume_manifest.csv").open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=("pass","rank","doi"))
        w.writeheader()
        for p in PASSES:
            for x in report["stages"][p]["missing_dois"]:
                w.writerow(dict(pass_=p,**x) if False else {"pass":p,"rank":x["rank"],"doi":x["doi"]})


def main():
    a=argparse.ArgumentParser()
    a.add_argument("--out",type=Path,required=True)
    a.add_argument("--strict",action="store_true",
                   help="return 2 while the frozen prospectively scored batch is incomplete")
    args=a.parse_args()
    report=audit()
    emit(report,args.out)
    print(json.dumps({k:v for k,v in report.items() if k in
        ("status","pre_registered_inclusions","stages","token_usage","readiness_blockers")},ensure_ascii=False,indent=2))
    return 2 if args.strict and report["readiness_blockers"] else 0


if __name__=="__main__":
    sys.exit(main())
