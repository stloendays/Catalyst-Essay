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
    text="\n".join(heads)
    (out/"SI_SOURCE_REVIEW_EXCERPTS.txt").write_text(text,encoding="utf-8")
    print(text[:27000])
    return index


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    make_review(args.out)
