"""Thin wrappers that run the frozen agent/extraction pipeline (CO2-to-methanol) on the prospective batch
(PREREGISTRATION.md section 5), as analysis/nh3_field_expansion_2026_10_12/b2.py does for ammonia (PR #78).

Only the paper list and the input/output directories change (all inside this folder); prompts, schema, model
settings, routes, normalisation and every other definition come from the imported, unmodified agent modules.

    nus-fetch python:  pv.py fetch -f dois.txt       # fetch_papers.run_fetch -> pdf/, fetch_manifest.json
    pv.py text                                       # pdf_to_text.py on every retrieved candidate (screening input)
    nus-fetch python:  pv.py si-fetch                # fetch_si.py on the papers that pass S3 -> si/, si_manifest.json
    pv.py si-text                                    # pdf_to_text.py --si -> text_si/
    pv.py extract --pass main --api-yes [--doi ...]  # extract_records.py -> out/raw*/ , out/token_usage.csv
    pv.py normalize                                  # normalize.py -> out/records_normalized.csv

Paper lists: `fetch_manifest.json` rows with status ok (text); `screening.csv` rows with s3 == "pass" (si-fetch);
rows with decision == "include" (si-text, extract, normalize).
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
AGENT = REPO / "agent" / "extraction"
OUT = HERE / "out"
sys.path.insert(0, str(AGENT))


def _screening(col: str, value: str) -> dict[str, str]:
    p = HERE / "screening.csv"
    if not p.exists():
        return {}
    with p.open(encoding="utf-8") as f:
        return {r["doi"].lower(): "prospective" for r in csv.DictReader(f) if r.get(col) == value}


def included() -> dict[str, str]:
    return _screening("decision", "include")


def retrieved() -> dict[str, str]:
    import json
    man = HERE / "fetch_manifest.json"
    rows = json.loads(man.read_text(encoding="utf-8")) if man.exists() else []
    return {r["doi"].lower(): "prospective" for r in rows if r["status"] in ("ok", "skip") and r.get("file")}


def _redirect(mod):
    """Point a frozen module's folder globals at this folder (its code reads them at call time)."""
    mod.HERE = HERE
    for name, sub in (("PDF_DIR", "pdf"), ("TEXT_DIR", "text"), ("TEXT_SI_DIR", "text_si"), ("SI_DIR", "si")):
        if hasattr(mod, name):
            setattr(mod, name, HERE / sub)


def run_fetch(argv):
    import argparse
    import fetch_papers as F
    ap = argparse.ArgumentParser()
    ap.add_argument("-f", "--file", required=True)
    a = ap.parse_args(argv)
    summary = F.run_fetch(Path(a.file).resolve(), HERE / "pdf")
    rows = F.update_manifest(summary, HERE / "fetch_manifest.json")
    for r in rows:
        print(f'{r["status"]:7s} {r["doi"]:40s} pages={r["pages"]} doi_in_pdf={r["doi_in_pdf"]} {r["file"]}')


def run_text(si: bool):
    import paper_set
    paper_set.load_paper_set = retrieved
    import pdf_to_text as P
    _redirect(P)
    sys.argv = [sys.argv[0]] + (["--si"] if si else [])
    P.main()


def run_si_fetch(argv):
    import fetch_si as F
    _redirect(F)
    F.MANIFEST = HERE / "si_manifest.json"
    passed = _screening("s3", "pass")
    sys.argv = [sys.argv[0]] + [a for d in passed for a in ("--doi", d)] + argv
    F.main()


def run_extract(argv):
    import paper_set
    paper_set.load_paper_set = included
    import extract_records as E
    _redirect(E)
    E.OUT_DIR = OUT
    E.RAW_DIR = OUT / "raw"
    E.RAW_DIRS = {"main": OUT / "raw", "figures": OUT / "raw_figures", "si": OUT / "raw_si",
                  "si_figures": OUT / "raw_si_figures"}
    E.USAGE_CSV = OUT / "token_usage.csv"
    E.load_paper_set = included
    OUT.mkdir(exist_ok=True)
    sys.argv = [sys.argv[0]] + argv
    E.main()


def run_normalize():
    import paper_set
    paper_set.load_paper_set = included
    import normalize as N
    N.IN_SET = included()
    N.HERE = HERE
    N.RAW_DIR = OUT / "raw"
    N.PASS_DIRS = {"main": OUT / "raw", "si": OUT / "raw_si", "figures": OUT / "raw_figures",
                   "si_figures": OUT / "raw_si_figures"}
    sys.argv = [sys.argv[0]]
    N.main()


if __name__ == "__main__":
    cmd, rest = sys.argv[1], sys.argv[2:]
    {"fetch": lambda: run_fetch(rest), "text": lambda: run_text(False), "si-text": lambda: run_text(True),
     "si-fetch": lambda: run_si_fetch(rest), "extract": lambda: run_extract(rest),
     "normalize": run_normalize}[cmd]()
