"""Random sample (seed 20261013) of 40 printed values that enter the new batch's primary, for the PDF check
(PREREGISTRATION.md section 7). Drawn from the uncorrected records, before any plant-model run.

Population: every printed-cohort candidate (meoh_candidates.build_candidates, printed_only=True) in a comparison group
with at least two entries, x the values its candidate row uses: X_CO2, S_MeOH, S_CO and S_CH4 when the paper reports
them, the STY when it is printed, T, P, H2/CO2 and the space velocity. Each value carries the raw string, location
and page of the extracted record of the pass it came from (out/raw*/<slug>.json).

    python pdf_check_sample.py  -> pdf_check_sample.csv
"""
from __future__ import annotations

import json
import re

import numpy as np
import pandas as pd

from pv_common import HERE, load_new_records
from meoh_candidates import build_candidates

RAW = {"main": "raw", "figures": "raw_figures", "si": "raw_si", "si_figures": "raw_si_figures"}
RAW_FIELD = {"X_CO2": "co2_conversion", "S_MeOH": "selectivity_ch3oh", "S_CO": "selectivity_co",
             "S_CH4": "selectivity_ch4", "STY": "methanol_sty", "T": "temperature", "P": "pressure",
             "H2_CO2": "h2_co2_ratio", "GHSV": "ghsv"}
REC_COL = {"X_CO2": "X_CO2_pct", "S_MeOH": "S_MeOH_pct", "S_CO": "S_CO_pct", "S_CH4": "S_CH4_pct",
           "STY": "STY_g_gcat_h", "T": "T_K", "P": "P_bar", "H2_CO2": "H2_CO2", "GHSV": "GHSV_NL_gcat_h"}
N, SEED = 40, 20261013


def slug(doi):
    return re.sub(r"[^a-z0-9]+", "_", doi.lower()).strip("_")


def raw_record(doi, entry, pass_):
    p = HERE / "out" / RAW[pass_] / f"{slug(doi)}.json"
    if not p.exists():
        return None
    hits = [r for r in json.loads(p.read_text(encoding="utf-8"))["records"] if r["entry_label"] == entry]
    return hits[0] if hits else None


def main():
    rec = load_new_records(corrected=False)
    cand = build_candidates(rec, printed_only=True)
    n = cand.groupby("group").size()
    cand = cand[cand.group.isin(n[n >= 2].index)]
    recx = rec.drop_duplicates(["doi", "entry_label"]).set_index(["doi", "entry_label"])
    pop = []
    for r in cand.itertuples():
        fields = ["X_CO2", "S_MeOH"] + (["S_CO"] if r.co_printed else []) + (["S_CH4"] if r.ch4_printed else []) \
            + (["STY"] if r.sty_printed else []) + ["T", "P", "H2_CO2", "GHSV"]
        for f in fields:
            pop.append((r.doi, r.entry, r.catalyst, f))
    rng = np.random.default_rng(SEED)
    idx = sorted(rng.choice(len(pop), size=min(N, len(pop)), replace=False))
    rows = []
    for k, i in enumerate(idx, 1):
        doi, entry, cat, f = pop[i]
        nr = recx.loc[(doi, entry)]
        src_pass = nr["pass"]
        m = re.search(rf"(?:^|;){f}<-(\w+)", str(nr.get("filled") or ""))
        if m:
            src_pass = m.group(1)
        raw = raw_record(doi, entry, src_pass) or raw_record(doi, entry, nr["pass"]) or {}
        q = raw.get(RAW_FIELD[f]) or {}
        used = nr[REC_COL[f]]
        if f == "GHSV" and pd.isna(used):
            used = nr["GHSV_raw"]
        rows.append(dict(id=k, doi=doi, entry=entry, catalyst=cat, field=f, value_in_records=used,
                         record_column=REC_COL[f], extracted_value=q.get("value"), extracted_unit=q.get("unit"),
                         qualifier=q.get("qualifier"), location=q.get("location"), page=q.get("page"),
                         source_pass=src_pass, primary_location=nr["primary_location"]))
    out = pd.DataFrame(rows)
    out.to_csv(HERE / "pdf_check_sample.csv", index=False)
    print(f"population {len(pop)} values from {cand.doi.nunique()} papers; sample {len(out)}:",
          out.field.value_counts().to_dict())


if __name__ == "__main__":
    main()
