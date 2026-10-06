"""Accuracy of the ammonia extraction agent against the adjudicated Humphreys 2021 records (independent curated
reference), and the random PDF-check sample of the other extracted entries.

    python evaluate.py                 -> eval/humphreys_match.csv, eval/humphreys_fields.csv, eval/summary.json
    python evaluate.py --sample 40     -> eval/pdf_check_sample.csv (random entries not covered by Humphreys, seed
                                          20261006) for checking by hand; the verdict columns are filled in by hand
                                          and read back on the next run

Matching (Humphreys row -> extracted entry): same DOI (Humphreys reference number -> DOI in humphreys_refs.csv),
|dT| <= 1.5 K, |dP| <= max(1 %, 0.102 MPa) (a gauge pressure converted to absolute) and, among those, the extracted entry whose catalyst name shares the most tokens with the
Humphreys name, ties broken by the closest rate (|ln ratio|). A Humphreys row with no extracted entry at its T and P
is a miss. Where the PDF shows that this rule picked the wrong entry (the review's generic names such as
'1% Fe/BaTiO3-xHx'), eval/humphreys_adjudication.csv names the extracted entry the review row refers to
(match_catalyst; 'NONE' when the paper has no such catalyst). Fields scored: metal content (wt%), T, P, WHSV, outlet NH3, rate per g catalyst. Strict: equal within
1 % (the review rounds); loose: within 10 %.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import re
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
EVAL = HERE / "eval"
H_RECORDS = REPO / "agent" / "nh3_supported" / "out" / "records.csv"
SEED = 20261006


def tokens(s):
    return {t for t in re.split(r"[^0-9a-z]+", str(s).lower().replace("–", "-").replace("−", "-")) if t}


def f(x):
    try:
        v = float(x)
        return None if math.isnan(v) else v
    except (TypeError, ValueError):
        return None


def close(a, b, rel):
    if a is None or b is None:
        return None
    return abs(a - b) <= rel * max(abs(a), abs(b), 1e-12)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=0)
    args = ap.parse_args()
    EVAL.mkdir(exist_ok=True)
    refs = {r["ref"]: r["doi"].lower() for r in csv.DictReader(
        (l for l in (HERE / "humphreys_refs.csv").open(encoding="utf-8") if not l.startswith("#"))) if r["doi"]}
    from paper_set import load_paper_set
    in_set = load_paper_set()
    ext = pd.read_csv(HERE / "out" / "records_normalized.csv", keep_default_na=False, na_values=[""])
    hum = [r for r in csv.DictReader(H_RECORDS.open(encoding="utf-8")) if refs.get(r["ref"]) in in_set]
    adj_path = EVAL / "humphreys_adjudication.csv"
    adj = pd.read_csv(adj_path, keep_default_na=False) if adj_path.exists() else pd.DataFrame(
        columns=["h_id", "match_catalyst", "field", "pdf_value", "extraction_correct", "humphreys_correct", "note"])
    overrides = {r.h_id: r.match_catalyst for r in adj.itertuples() if r.match_catalyst}
    rows, used = [], set()
    for h in hum:
        doi = refs[h["ref"]]
        T, P = f(h["T_C"]), f(h["P_MPa"])
        e = ext[(ext.doi == doi)]
        e = e[(e.T_C - T).abs() <= 1.5] if T is not None else e.iloc[0:0]
        e = e[(e.P_MPa - P).abs() <= max(0.01 * P, 0.102)] if P is not None else e.iloc[0:0]   # gauge vs absolute
        ov = overrides.get(h["id"])
        if ov is not None:
            e = e[e.catalyst_name == ov] if ov != "NONE" else e.iloc[0:0]
        rec = dict(h_id=h["id"], ref=h["ref"], doi=doi, h_catalyst=h["catalyst"], h_metal_wt=f(h["metal_wt_pct"]),
                   h_T=T, h_P=P, h_whsv=f(h["whsv_mL_g_h"]), h_outlet=f(h["outlet_nh3_vol_pct"]),
                   h_rate=f(h["rate_umol_g_h"]), matched=False)
        if len(e):
            ht = tokens(h["catalyst"])
            hr = rec["h_rate"]

            def score(r):
                ov = len(ht & tokens(r.catalyst_name)) / max(len(ht), 1)
                rr = f(r.rate_umol_gcat_h)
                lr = abs(math.log(rr / hr)) if (rr and hr) else 9.0
                return (-ov, lr)
            best = min(e.itertuples(), key=score)
            rec.update(matched=True, e_index=int(best.Index), e_catalyst=best.catalyst_name, e_entry=best.entry_label,
                       e_metal_wt=f(best.metal_wt_pct), e_T=f(best.T_C), e_P=f(best.P_MPa), e_whsv=f(best.WHSV_mL_g_h),
                       e_outlet=f(best.outlet_nh3_vol_pct), e_rate=f(best.rate_umol_gcat_h), e_rate_raw=best.rate_raw,
                       e_rate_src=best.rate_src, e_location=best.primary_location)
            used.add(int(best.Index))
        rows.append(rec)
    m = pd.DataFrame(rows)
    fields = []
    for name, rel_s in (("metal_wt", 0.01), ("T", 0.0), ("P", 0.01), ("whsv", 0.01), ("outlet", 0.01), ("rate", 0.01)):
        hcol, ecol = f"h_{name}", f"e_{name}"
        if ecol not in m:
            continue
        sub = m[m.matched & m[hcol].notna()]
        both = sub[sub[ecol].notna()]
        strict = sum(bool(close(a, b, max(rel_s, 1e-9)) or (name == "T" and abs(a - b) <= 1.5))
                     for a, b in zip(both[hcol], both[ecol]))
        loose = sum(bool(close(a, b, 0.10)) for a, b in zip(both[hcol], both[ecol]))
        fields.append(dict(field=name, humphreys_values=len(sub), extracted=len(both), strict=strict, loose=loose,
                           strict_frac=strict / len(both) if len(both) else None,
                           loose_frac=loose / len(both) if len(both) else None))
    # adjudicated: every strict disagreement was checked in the PDF (humphreys_adjudication.csv, one row per field);
    # the extraction is correct when it equals the PDF, whatever the review prints
    adjf = adj[adj.field != ""]
    for fr in fields:
        a = adjf[adjf.field == fr["field"]]
        wrong_ext = int((a.extraction_correct == "no").sum())
        fr["adjudicated_disagreements"] = int(len(a))
        fr["extraction_errors"] = wrong_ext
        fr["humphreys_errors"] = int((a.humphreys_correct == "no").sum())
        fr["adjudicated_correct_frac"] = (fr["extracted"] - wrong_ext) / fr["extracted"] if fr["extracted"] else None
    m.to_csv(EVAL / "humphreys_match.csv", index=False, float_format="%.6g")
    fd = pd.DataFrame(fields)
    fd.to_csv(EVAL / "humphreys_fields.csv", index=False, float_format="%.4g")
    summary = dict(humphreys_rows_in_set=len(m), papers=int(m.doi.nunique()) if len(m) else 0,
                   matched=int(m.matched.sum()) if len(m) else 0, fields=fields)

    sample_path = EVAL / "pdf_check_sample.csv"
    if args.sample:
        pool = ext[~ext.index.isin(used) & ext.rate_umol_gcat_h.notna()]
        smp = pool.sample(n=min(args.sample, len(pool)), random_state=SEED)
        cols = ["doi", "entry_label", "catalyst_name", "metal_wt_pct", "metal_loading_raw", "T_C", "P_MPa", "WHSV_mL_g_h",
                "SV_raw", "outlet_nh3_vol_pct", "rate_raw", "rate_basis", "rate_umol_gcat_h", "rate_src",
                "primary_location", "primary_page"]
        out = smp[cols].copy()
        out["verdict"] = ""
        out["comment"] = ""
        if sample_path.exists():
            raise SystemExit(f"{sample_path} exists (hand verdicts); delete it deliberately to draw a new sample")
        out.to_csv(sample_path, index_label="record_index", float_format="%.6g")
    if sample_path.exists():
        s = pd.read_csv(sample_path, keep_default_na=False)
        done = s[s.verdict != ""]
        ok = (done.verdict == "correct").sum()
        n = len(done)
        if n:
            from scipy.stats import beta
            lo = beta.ppf(0.025, ok, n - ok + 1) if ok else 0.0
            hi = beta.ppf(0.975, ok + 1, n - ok) if ok < n else 1.0
            summary["pdf_check_sample"] = dict(checked=int(n), correct=int(ok), fraction=ok / n,
                                               ci95_clopper_pearson=[float(lo), float(hi)],
                                               verdicts=done.verdict.value_counts().to_dict())
    (EVAL / "summary.json").write_text(json.dumps(summary, indent=1, default=float) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=1, default=float))


if __name__ == "__main__":
    main()
