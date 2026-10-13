"""Random sample (seed 20261012) of 40 printed values that enter the batch-2 primary, for the PDF check (PROTOCOL.md 3).

Population: every printed primary entry of runs/batch2/candidates_printed.csv x the values its mapping uses:
rate per g catalyst, T, P, metal wt% (not for a fused-Fe reference, whose content is the fixed 71.51 wt%), and the
printed outlet NH3 when the entry uses it, else the space velocity when the entry has one. Each value carries the raw
string, location and page of the extracted record (agent/nh3_field/out_batch2/raw*/<slug>.json).

    python pdf_check_sample.py  -> batch2_pdf_check_sample.csv
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
OUT2 = HERE.parents[1] / "agent" / "nh3_field" / "out_batch2"
RAW = {"main": "raw", "figures": "raw_figures", "si": "raw_si", "si_figures": "raw_si_figures"}
FIELDS = {"rate": "rate", "T": "temperature", "P": "pressure", "metal_wt_pct": "metal_loading",
          "outlet_NH3": "outlet_nh3", "WHSV": "space_velocity"}
FILL_KEY = {"rate": "rate", "outlet_NH3": "outlet", "WHSV": "WHSV", "metal_wt_pct": "metal_wt_pct"}  # normalize `filled`
N, SEED = 40, 20261012


def slug(doi):
    return re.sub(r"[^a-z0-9]+", "_", doi.lower()).strip("_")


def raw_record(doi, entry, pass_):
    d = json.loads((OUT2 / RAW[pass_] / f"{slug(doi)}.json").read_text(encoding="utf-8"))
    hits = [r for r in d["records"] if r["entry_label"] == entry]
    return hits[0] if hits else None


def main():
    pr = pd.read_csv(HERE / "runs" / "batch2" / "candidates_printed.csv", keep_default_na=False, na_values=[""])
    rec = pd.read_csv(OUT2 / "records_normalized.csv", keep_default_na=False, na_values=[""])
    rec = rec.drop_duplicates(["doi", "entry_label"]).set_index(["doi", "entry_label"])
    pop = []
    for r in pr.itertuples():
        fields = ["rate", "T", "P"] + ([] if r.fused else ["metal_wt_pct"])
        if r.y_source == "printed outlet":
            fields.append("outlet_NH3")
        elif not pd.isna(r.WHSV):
            fields.append("WHSV")
        for f in fields:
            pop.append((r.doi, r.entry, r.catalyst, f))
    rng = np.random.default_rng(SEED)
    idx = sorted(rng.choice(len(pop), size=min(N, len(pop)), replace=False))
    rows = []
    for k, i in enumerate(idx, 1):
        doi, entry, cat, f = pop[i]
        nr = rec.loc[(doi, entry)]
        pass_ = nr["pass"]
        raw = raw_record(doi, entry, pass_) or {}
        src_pass = pass_
        filled = str(nr.get("filled") or "")
        m = re.search(rf"{FILL_KEY[f]}<-(\w+)", filled) if f in FILL_KEY else None
        if m:                     # the value came from another pass: same catalyst there (normalize._same_entry)
            src_pass = m.group(1)
        q = raw.get(FIELDS[f]) or {}
        if f == "metal_wt_pct" and q.get("value") is None:
            comp = [c["loading"] for c in raw.get("components", []) if c.get("role") == "active_metal"
                    and c["loading"].get("value") is not None]
            q = comp[0] if comp else q
        if f == "WHSV" and q.get("value") is None:
            fl, ms = raw.get("total_flow") or {}, raw.get("catalyst_mass") or {}
            q = dict(value=f"{fl.get('value')} {fl.get('unit')} / {ms.get('value')} {ms.get('unit')}",
                     unit="flow / mass", location=f"{fl.get('location')}; {ms.get('location')}", page=fl.get("page"))
        used = {"rate": nr.rate_umol_gcat_h, "T": nr.T_C, "P": nr.P_MPa, "metal_wt_pct": nr.metal_wt_pct,
                "outlet_NH3": nr.outlet_nh3_vol_pct, "WHSV": nr.WHSV_mL_g_h}[f]
        if f == "WHSV" and pd.isna(used):
            used = pr[(pr.doi == doi) & (pr.entry == entry)].WHSV.iloc[0]
        rows.append(dict(id=k, doi=doi, entry=entry, catalyst=cat, field=f, value_used_model_basis=used,
                         extracted_value=q.get("value"), extracted_unit=q.get("unit"), qualifier=q.get("qualifier"),
                         location=q.get("location"), page=q.get("page"), source_pass=src_pass,
                         primary_location=nr.primary_location))
    out = pd.DataFrame(rows)
    out.to_csv(HERE / "batch2_pdf_check_sample.csv", index=False, encoding="utf-8")
    print(f"population {len(pop)} values from {len(pr)} entries; sampled {len(out)}")
    print(out.field.value_counts().to_dict())


if __name__ == "__main__":
    main()
