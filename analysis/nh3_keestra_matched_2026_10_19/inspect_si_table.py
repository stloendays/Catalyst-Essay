#!/usr/bin/env python3
"""Human-auditable, source-only excerpt index for official Keestra Ru 2025 SI.

This tool intentionally DOES NOT set any fitted factors or unlock G2; the
exact formulation/table row must be confirmed by an author using the source.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re

from source_probe import CANDIDATES, download, extract_pdf

MAX_PRINT_PER_TERM=3
WINDOW_BEFORE=500
WINDOW_AFTER=1700
TERMS = (
  r"\btable\s+A[- .]?\d+\b",
  r"\btable\s+S[- .]?\d+\b",
  r"(?i:Ru[\s/-]*Ba[\s/-]*K[\s/]*/?\s*C)",
  r"(?i:\bmodel\s+D\b)",
  r"(?i:\bb[\s_]?cat\b)",
  r"(?i:\bb[\s_]?N\b)",
  r"(?i:Ru[\s/-]*Ba)",
  r"(?i:4\s*wt\s*%|4\s*%)",
)


def make_review(out:Path):
    url=next(x[1] for x in CANDIDATES if x[0]=="elsevier_mmc1_pdf")
    meta,pdf=download(url,timeout=30)
    if meta["sniffed"]!="pdf":
        raise ValueError("Official SI URL did not return a valid PDF")
    body=extract_pdf(pdf)
    if len(body)<3000:
        raise ValueError("PDF contained unexpectedly little text")
    terms={}
    for term in TERMS:
        hits=list(re.finditer(term,body,flags=re.IGNORECASE))
        spans=[]
        for match in hits[:MAX_PRINT_PER_TERM]:
            s=max(0,match.start()-WINDOW_BEFORE)
            e=min(len(body),match.end()+WINDOW_AFTER)
            snippet=body[s:e]
            spans.append({"index":match.start(),"raw_source_excerpt":snippet,
                          "source_identifier":f"{meta['sha256'][:12]} offset={match.start()}"})
        terms[term]={"n_hits":len(hits),"excerpts":spans}
    # PDF extraction can separate b_cat / b_N by columns or ligatures, so
    # include tiny first-block provenance and headings, never numeric defaults.
    index={
        "source_url":url,"sha256":meta["sha256"],"byte_count":meta["byte_count"],
        "source_text_chars":len(body),
        "evidence_type":"2025 published article supplementary PDF; unreviewed source text",
        "identity_status":"PENDING_HUMAN_CATALYST_ROW_REVIEW",
        "extracted_factors_are_not_approved_for_model":True,
        "keywords":{k:{"n_hits":v["n_hits"]} for k,v in terms.items()}
    }
    out.mkdir(parents=True,exist_ok=True)
    (out/"SI_SOURCE_INDEX.json").write_text(json.dumps(index,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    heads=["SI Keestra Ru 2025 source PDF",f"SHA256 {meta['sha256']}",
           f"Size {meta['byte_count']} bytes; text {len(body)} characters",
           "Pending scientist transcription; NEVER fit factors to 5.8x output.", "",
           "First text section (verify this is the correct supporting article):",
           body[:1600],""]
    for term,x in terms.items():
        heads.extend([f"### {term}: {x['n_hits']} occurrences"])
        for i,span in enumerate(x["excerpts"]):
            heads.extend([f"Candidate {i+1}: text position {span['index']}",
                          span["raw_source_excerpt"], ""])
    # Pull the exact Model D block, not earlier A/B/C rows with different
    # catalyst-specific parameters. The row is not yet approved to enter
    # sources.json until the full source panel/table is audited.
    mo=re.search(r"A-1-4\s+Model\s+D",body,re.IGNORECASE)
    if mo:
        nextmodel=re.search(r"A-1-5\s+Model\s+E",body[mo.end():],re.IGNORECASE)
        end=mo.end()+nextmodel.start() if nextmodel else mo.start()+14000
        model_d_text=body[mo.start():end][:14000]
        (out/"SI_MODEL_D_PARAMETER_SECTION.txt").write_text(model_d_text,encoding="utf-8")
        # The registered commercial formulation is the Model D row, NOT the
        # first Ru-Ba-K/C occurrence in source Model A/B/C.
        row_start=model_d_text.find("Ru-Ba-K/C")
        row=model_d_text[row_start:row_start+320] if row_start>=0 else ""
        source_json=json.loads((Path(__file__).resolve().parent/"sources.json").read_text(encoding="utf-8"))
        validated=(row_start>=0 and "Liu (2013)" in row and
                   "7.625E+01" in row and "8.514E-01" in row and
                   "3.561E-02" in row and "8.091E-03" in row and
                   source_json["referenceTarget100Bar"]["Ru_Ba_K_C_bcat"]==76.25 and
                   source_json["referenceTarget100Bar"]["Ru_Ba_K_C_bN"]==.8514 and
                   source_json["referenceTarget100Bar"]["specific_ru_parameters_source"]["source_sha256"]==meta["sha256"] and
                   meta["sha256"]=="a6137d61860d2c55905a12544d7792437592a02fcbed6b0d05c237d4a1569598")
        if not validated:
            raise AssertionError("Source SI Model D commercial catalyst row/sha does not match pinned factors; do not use!")
        index["exact_Ru_Ba_K_C_factor_table_status"]="PASS_SOURCE_SHA_AND_EXACT_MODEL_D_TABLE8_ROW"
        index["bcat_verified"]=76.25
        index["bN_verified"]=.8514
        index["model_D_block_found"]=True
        index["model_D_source_span"]=[mo.start(),end]
        print("=== VERIFIED SOURCE MODEL D TABLE SECTION ===")
        print(model_d_text[:11000])
    else:
        index["model_D_block_found"]=False
    text="\n".join(heads)
    (out/"SI_SOURCE_REVIEW_EXCERPTS.txt").write_text(text,encoding="utf-8")
    (out/"SI_SOURCE_INDEX.json").write_text(json.dumps(index,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("=== OTHER SOURCE DISCOVERY EXCERPTS ===")
    print(text[:3000])
    return index


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    make_review(args.out)
