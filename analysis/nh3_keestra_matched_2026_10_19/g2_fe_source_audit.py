#!/usr/bin/env python3
"""Official 2025 Keestra Fe SI retrieval/section audit for G2 reproducibility.

Only retrieves publisher-hosted PRIMARY SI and writes an author-reviewable
source text index, not an invented SRK parameterization or calibrated PFR.
Use only in separately scoped exploration and never change frozen data.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from pathlib import Path
from source_probe import download, extract_pdf

PII="S1385894725054294"
CANDIDATES=[
  ("mmc1",f"https://ars.els-cdn.com/content/image/1-s2.0-{PII}-mmc1.pdf"),
  ("mmc2",f"https://ars.els-cdn.com/content/image/1-s2.0-{PII}-mmc2.pdf"),
  ("mmc3",f"https://ars.els-cdn.com/content/image/1-s2.0-{PII}-mmc3.pdf"),
]
HEADINGS=[
 ("polarity/Python","A-5-1"),
 ("EOS+thermo","A-5"),
 ("pure/binary","A-6"),
 ("adiabatic-PFR","A-7"),
 ("bibliography", "References"),
]
SOURCE_LABEL="Fe Keestra 2025 DOI 10.1016/j.cej.2025.164593"


def text_window(text,needle,limit=10500):
    items=[m for m in re.finditer(re.escape(needle),text,flags=re.I)]
    useful=[]
    for m in items[:8]:
        s=max(0,m.start()-400)
        e=min(len(text),m.start()+limit)
        useful.append((m.start(),text[s:e]))
    return useful


def run(out:Path):
    out.mkdir(parents=True,exist_ok=True)
    response={"source_DOI":"10.1016/j.cej.2025.164593","source_title":"A century of data: Thermodynamics and kinetics for ammonia synthesis on various commercial iron-based catalysts",
        "probe_status":"SOURCE_PDF_NOT_YET_VERIFIED", "author_reported_sections":["A-5","A-5-1","A-6","A-7"],
        "no_kinetic_factor_refit":True,"no_physics_gate_pass_inferred":True,
        "attempts":[]}
    excerpts=[]
    for label,url in CANDIDATES:
        rec={"candidate":label,"url":url}
        try:
            meta,raw=download(url,timeout=28)
            rec.update(meta)
            if meta["sniffed"]!="pdf": raise ValueError("no official valid PDF")
            text=extract_pdf(raw)
            rec.update({"text_char_count":len(text),
                "initial_document_title":" ".join(text[:400].split())[:180]})
            title_verification=bool(re.search(
                r"A century of data|commercial iron-based catalysts",text[:3000],re.I))
            rec["correct_Fe_SI_title_verified"]=title_verification
            if not title_verification:
                raise ValueError("PDF accessible, but Fe 2025 SI article title not verified")
            (out/"OFFICIAL_2025_FE_SI_TEXT.txt").write_text(text,encoding="utf-8")
            response.update({"probe_status":"OFFICIAL_PDF_TEXT_VERIFIED",
                "source_url":url,"sha256":meta["sha256"],
                "length_chars":len(text),"official_SI_article_title_verified":True,
                "sections":{}})
            for section,needle in HEADINGS:
                windows=text_window(text,needle)
                response["sections"][section]={"needle":needle,"matches":len(windows),
                                               "positions":[p for p,_ in windows]}
                excerpts.append(f"\n{'='*25}\n{section} {needle} matches {len(windows)}\n{'='*25}\n")
                for i,(offset,win) in enumerate(windows[:2]):
                    snippets=win[:13500]
                    excerpts.append(f"[{i} at {offset}]\n"+snippets+"\n")
            # Write SHORT section-only source text review as a separate artifact.
            (out/"SI_SECTION_EXCERPTS.txt").write_text("\n".join(excerpts),encoding="utf-8")
            rec["status"]="SOURCE_VERIFIED_FOR_AUTHOR_REVIEW"
            response["attempts"].append(rec)
            break
        except Exception as exc:
            rec["status"]="UNAVAILABLE_OR_SOURCE_UNVERIFIED"
            rec["error"]=str(exc)[:600]
            response["attempts"].append(rec)
    lines=["# Keestra Fe 2025 — original SI retrieval audit","",SOURCE_LABEL,
        "Status: "+response["probe_status"],
        "EOS, Python alpha code, pure compound parameters, binary interaction and adiabatic reactor requirements are NOT automatically verified by this availability probe.",""]
    for t in response["attempts"]:
        lines.append(f"- {t['candidate']}: {t['status']}, {t.get('sniffed','missing')}, {t.get('error','')} ; URL {t['url']}")
    if response.get("source_url"):
        lines.extend([f"- Verified URL: {response['source_url']}",
             f"- SHA256: {response['sha256']}",
             "- Text portions recorded in SI_SECTION_EXCERPTS.txt and full extracted text in private workflow artifact (not committed to main)."])
    (out/"SOURCE_AUDIT.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    (out/"source_audit.json").write_text(json.dumps(response,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in response.items() if k!="attempts"},indent=2))
    for attempt in response["attempts"]:
        print(attempt["candidate"],attempt["status"],
              attempt.get("sniffed","NA"),attempt.get("byte_count",0),attempt.get("error",""))
    if excerpts:
        print("=== SOURCE-ONLY EXCERPTS BEGIN, UNVERIFIED FOR G2 ===")
        print("\n".join(excerpts)[:34500])
    return response


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    run(args.out)
