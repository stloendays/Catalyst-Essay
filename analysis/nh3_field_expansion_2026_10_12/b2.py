"""Thin wrappers that run the frozen agent/nh3_field pipeline on the batch-2 papers (PROTOCOL.md).

Only the paper list and the output directory change; prompts, schema, model settings, normalisation and every
other definition come from the imported, unmodified agent modules.

    python b2.py text                     # pdf_to_text.py on the 25 batch-2 candidates (screening input)
    python b2.py si-text                  # pdf_to_text.py --si (SI of the batch-2 papers in si/)
    python b2.py extract --pass main --api-yes [--doi ...]   # extract_records.py -> out_batch2/raw*/
    python b2.py normalize                # normalize.py -> out_batch2/records_normalized.csv
    nus-fetch python: b2.py si-fetch      # fetch_si.py on the included papers; manifest -> batch2_si_manifest.json
    nus-fetch python: b2.py si-fetch-screen DOI ...   # SI of excluded papers for the screening revisit (PROTOCOL 2);
                                          # manifest -> batch2_screening_si_manifest.json

NH3_API_YES_ONLY=1 restricts extract to the API-YES route (no fallback to the advisor key; the run stops when API-YES
is used up). It narrows llm_route.ROUTES in this process only; llm_route.py itself is unchanged.

The batch-2 list is batch2_candidates.txt (text) or the included rows of batch2_screening.csv (extract, normalize);
B2_SCREEN=with_si takes the column with_si_decision (screening revisited with the SI, 2026-10-13) instead of decision.

Model version: none of these steps loads the ammonia model, so NH3_MODEL (analysis/nh3_model.py) has no effect here and
its outputs (out_batch2/, the SI manifests) serve both NH3-FINAL-1.1 and 1.2. The model enters only at scoring:
score.py writes runs/ for NH3_MODEL=1.1 (default) and nh3_1_2/runs/ for NH3_MODEL=1.2, from the same records.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
AGENT = REPO / "agent" / "nh3_field"
OUT2 = AGENT / "out_batch2"
sys.path.insert(0, str(AGENT))


def candidates() -> dict[str, str]:
    return {l.strip().lower(): "batch2" for l in (HERE / "batch2_candidates.txt").read_text(encoding="utf-8").splitlines()
            if l.strip()}


def included() -> dict[str, str]:
    """B2_SCREEN=with_si selects the screening revisited with the SI (column with_si_decision); default: decision."""
    import os
    col = "with_si_decision" if os.environ.get("B2_SCREEN") == "with_si" else "decision"
    with (HERE / "batch2_screening.csv").open(encoding="utf-8") as f:
        return {r["doi"].lower(): "batch2" for r in csv.DictReader(f) if r[col] == "include"}


def run_text(si: bool):
    import paper_set
    paper_set.load_paper_set = candidates
    import pdf_to_text
    sys.argv = [sys.argv[0]] + (["--si"] if si else [])
    pdf_to_text.main()


def run_si_fetch(argv):
    import fetch_si as F
    F.MANIFEST = HERE / "batch2_si_manifest.json"
    sys.argv = [sys.argv[0]] + [a for d in included() for a in ("--doi", d)] + argv
    F.main()


def run_si_fetch_screen(dois):
    import fetch_si as F
    F.MANIFEST = HERE / "batch2_screening_si_manifest.json"
    sys.argv = [sys.argv[0]] + [a for d in dois for a in ("--doi", d)]
    F.main()


def run_extract(argv):
    import os
    if os.environ.get("NH3_API_YES_ONLY") == "1":
        import llm_route
        llm_route.ROUTES = ("api-yes",)
    import extract_records as E
    E.OUT_DIR = OUT2
    E.RAW_DIR = OUT2 / "raw"
    E.RAW_DIRS = {"main": OUT2 / "raw", "figures": OUT2 / "raw_figures", "si": OUT2 / "raw_si",
                  "si_figures": OUT2 / "raw_si_figures"}
    E.USAGE_CSV = OUT2 / "token_usage.csv"
    E.load_paper_set = included
    sys.argv = [sys.argv[0]] + argv
    E.main()


def run_normalize():
    import paper_set
    paper_set.load_paper_set = included
    import normalize as N
    import pandas as pd
    N.IN_SET = included()
    N.PASS_DIRS = {"main": OUT2 / "raw", "si": OUT2 / "raw_si", "figures": OUT2 / "raw_figures",
                   "si_figures": OUT2 / "raw_si_figures"}
    # normalize.main() with the output path changed
    slug_to_doi = {N.slug(d): d for d in N.IN_SET}
    by_pass = {p_: N.load_pass(p_, slug_to_doi) for p_ in ("main", "si", "figures", "si_figures")}
    df = pd.DataFrame(N.merge_passes(by_pass))
    df.to_csv(OUT2 / "records_normalized.csv", index=False, encoding="utf-8")
    print(f"{len(df)} merged records from {df.doi.nunique()} papers; per-pass {({k: len(v) for k, v in by_pass.items()})}; "
          f"by origin {df['pass'].value_counts().to_dict()}; rows with filled fields {(df['filled'] != '').sum()}")
    bad = df["flags"].astype(bool)
    if bad.any():
        print(df[bad][["doi", "entry_label", "flags", "rate_raw", "SV_raw", "outlet_raw"]].to_string())


if __name__ == "__main__":
    cmd, rest = sys.argv[1], sys.argv[2:]
    if cmd == "text":
        run_text(False)
    elif cmd == "si-text":
        run_text(True)
    elif cmd == "si-fetch":
        run_si_fetch(rest)
    elif cmd == "si-fetch-screen":
        run_si_fetch_screen(rest)
    elif cmd == "extract":
        run_extract(rest)
    elif cmd == "normalize":
        run_normalize()
    else:
        raise SystemExit(f"unknown command {cmd}")
