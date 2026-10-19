#!/usr/bin/env python3
"""Read-only public source retrieval probe for the exact Keestra 2025 Ru SI.

IMPORTANT: A URL guess is NOT scientific evidence. Only a verified source PDF,
with exact original model-D, formulation-specific parameter table, can unlock
any kinetics/economics gate. We save HTTP/byte type and bounded excerpts, not
an invented b_cat or a fitted value.
"""
from __future__ import annotations
import argparse
import hashlib
import html
import io
import json
import re
import subprocess
import tempfile
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

PII = "S1385894725093830"
MAX_BYTES = 24 * 1024 * 1024
CANDIDATES = (
    ("elsevier_mmc1_pdf",f"https://ars.els-cdn.com/content/image/1-s2.0-{PII}-mmc1.pdf","pdf","hypothesis"),
    ("elsevier_mmc1_docx",f"https://ars.els-cdn.com/content/image/1-s2.0-{PII}-mmc1.docx","docx","hypothesis"),
    ("elsevier_mmc2_pdf",f"https://ars.els-cdn.com/content/image/1-s2.0-{PII}-mmc2.pdf","pdf","hypothesis"),
    ("ut_keestra_thesis_2026",
      "https://research.utwente.nl/files/516740119/Keestra_Dissertation_2026.pdf","pdf","university catalog direct URL"),
    ("ut_ru_article_main_2025",
      f"https://research.utwente.nl/files/512051776/1-s2.0-{PII}-main.pdf","pdf","university catalog; MAIN ARTICLE not SI"),
)
TRIGGERS = ("bcat","b_cat","b cat","b_N","bN","Ru-Ba-K","Ru Ba K","A-1","model D","Keestra")
ALLOWED_HOSTS = ("ars.els-cdn.com","research.utwente.nl")
PAGE_TEXT_LIMIT = 900
MAX_HITS = 5


def sniff(data:bytes) -> str:
    if data.lstrip().startswith(b"%PDF-"):return "pdf"
    if data[:2]==b"PK":return "zip"
    if b"<html" in data[:1500].lower() or b"<!doctype" in data[:1500].lower():return "html"
    if data.startswith(b"<?xml"):return "xml"
    return "other"


def download(url:str, timeout=20) -> tuple[dict,bytes]:
    from urllib.parse import urlsplit
    if urlsplit(url).scheme!="https" or urlsplit(url).hostname not in ALLOWED_HOSTS:
        raise ValueError("remote host not allowed for public-source audit")
    req=urllib.request.Request(url,headers={
      "User-Agent":"Mozilla/5.0 (compatible; AcademicSourceAudit/1.0; +https://github.com/stloendays/Catalyst-Essay)",
      "Accept":"application/pdf, application/vnd.openxmlformats-officedocument.wordprocessingml.document, */*;q=0.6",
      "Referer":"https://www.sciencedirect.com/"})
    with urllib.request.urlopen(req,timeout=timeout) as response:
        # Read with a hard cap to avoid unexpectedly large resource downloads.
        data=response.read(MAX_BYTES+1)
        if len(data)>MAX_BYTES:
            raise ValueError("source larger than 24MB hard limit")
        final_url=response.geturl()
        if urlsplit(final_url).hostname not in ALLOWED_HOSTS:
            raise ValueError("redirect to non-allowlisted source host")
        return dict(http_status=response.status,
                    content_type=response.headers.get("content-type",""),
                    final_url=final_url,byte_count=len(data),
                    sha256=hashlib.sha256(data).hexdigest(),sniffed=sniff(data)),data


def extract_pdf(data:bytes)->str:
    with tempfile.TemporaryDirectory() as tmp:
        path=Path(tmp)/"source.pdf"
        path.write_bytes(data)
        result=subprocess.run(["pdftotext","-layout",str(path),"-"],capture_output=True,
                              text=True,timeout=35,check=True)
        return result.stdout


def extract_docx(data:bytes)->str:
    paragraphs=[]
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        for name in z.namelist():
            if name.startswith("word/") and name.endswith(".xml") and name in ("word/document.xml",):
                root=ET.fromstring(z.read(name))
                ns={"w":"http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
                for para in root.findall(".//w:p",ns):
                    texts=[e.text for e in para.findall(".//w:t",ns) if e.text]
                    if texts:paragraphs.append("".join(texts))
    return "\n".join(paragraphs)


def excerpts(text:str):
    hits=[]
    lowered=text.lower()
    for needle in ("Ru-Ba-K/C","Ru-Ba-K","b_cat","bcat","b_N","bN","Supplementary Information","Table A-1"):
        start=0
        while len(hits)<MAX_HITS and (at:=lowered.find(needle.lower(),start))>=0:
            s=max(0,at-150);e=min(len(text),at+PAGE_TEXT_LIMIT-150)
            body=" ".join(text[s:e].split())
            hits.append({"term":needle,"approx_char_offset":at,"nearby_source_text":body[:PAGE_TEXT_LIMIT]})
            start=at+len(needle)
        if len(hits)>=MAX_HITS:break
    return hits


def audit(paths=CANDIDATES):
    found=[]
    for label,url,expected,provenance in paths:
        entry=dict(label=label,url=url,expected_type=expected,url_provenance=provenance,
                   is_original_2025_ru_supplementary="UNVERIFIED", exact_Ru_Ba_K_C_factors="NOT_EXTRACTED")
        try:
            meta,data=download(url)
            entry.update(meta)
            actual=sniff(data)
            if expected=="pdf" and actual=="pdf":
                body=extract_pdf(data)
                entry["text_char_count"]=len(body)
                entry["excerpts"]=excerpts(body)
                entry["contains_Ru_Ba_K_case"]=bool(re.search(r"Ru\s*[-–]?\s*Ba\s*[-–]?\s*K",body,re.I))
            elif expected=="docx" and actual=="zip":
                body=extract_docx(data)
                entry["text_char_count"]=len(body)
                entry["excerpts"]=excerpts(body)
                entry["contains_Ru_Ba_K_case"]=bool(re.search(r"Ru\s*[-–]?\s*Ba\s*[-–]?\s*K",body,re.I))
            else:
                entry["error"]="Downloaded response is not the expected PDF/DOCX source file"
            # NEVER auto-promote snippets to exact fitted parameters; SI must be reviewed.
        except (urllib.error.URLError,TimeoutError,ValueError,subprocess.CalledProcessError,
                subprocess.TimeoutExpired,zipfile.BadZipFile,ET.ParseError,OSError) as exc:
            entry["error"]=str(exc)[:500]
        found.append(entry)
    return dict(protocol="GET SOURCE ONLY, NO RATE OR BED VALIDATION",
                all_attempts=found,
                source_pdf_count=sum(x.get("sniffed")=="pdf" and "error" not in x for x in found),
                source_docx_count=sum(x.get("sniffed")=="zip" and "error" not in x for x in found),
                original_ru_ba_k_c_SI_exact_parameter_gate="ACCESS_ONLY_NOT_THE_FACTOR_VALIDATOR__SEE_SI_SOURCE_INDEX",
                do_not_fit_to_published_5p8_ratio=True)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    result=audit()
    (args.out/"source_probe.json").write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    report=[
      "# Public primary-source retrieval audit — Keestra Ru CEJ 2025",
      "",
      "This automatically checks explicitly labelled potential official source URLs. Guessed filenames are hypotheses, not citations. Source-access detection alone does not verify catalyst-specific factors. A separate SHA- and SI Table 8 row-check now validates the factors. Full G2 industrial reactor reproduction remains blocked until corrected-SRK and adiabatic PFR physics are verified.",
      "",
      "| Candidate URL | Expected content | Retrieved content | Bytes | Outcome |",
      "|---|---|---|---:|---|"
    ]
    for x in result["all_attempts"]:
        report.append(f"| {x['label']} | {x['expected_type']} | {x.get('sniffed','not retrieved')} | {x.get('byte_count',0)} | {x.get('error','FILE RETRIEVED; identity/parameters unverified')[:110]} |")
    report.extend([
      "",
      "Successful archive-level HTTP/PDF access only confirms bytes are available; it does not verify a catalyst-specific table, model D correction coefficients, EOS or external reactor reproduction. The recorded bounded excerpts in source_probe.json help locate pages but do not establish correct numbers without full PDF inspection.",
      "",
      "**No effect on main paper, frozen benchmark, PR #111 or G2/G3 blocked status.**",
      ""
    ])
    (args.out/"SOURCE_PROBE.md").write_text("\n".join(report),encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k!="all_attempts"},indent=2))
    for x in result["all_attempts"]:
        print(x["label"],x.get("http_status","ERR"),x.get("sniffed","missing"),
              x.get("byte_count",0),x.get("error","OK"))
if __name__=="__main__":
    main()
