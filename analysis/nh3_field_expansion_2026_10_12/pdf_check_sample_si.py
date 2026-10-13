"""Random sample (seed 20261013) of 20 printed values that enter the batch-2 primary *with Supporting Information* and
come from the SI (source pass `si` or `si_figures`, after normalize.py's pass merge and field filling), for the second
AI-assisted PDF check. Population and value lookup exactly as in pdf_check_sample.py; only the run folder
(runs/batch2_si, uncorrected, as pdf_check_sample.py uses runs/batch2), the SI-origin filter, N and the seed differ.

    python pdf_check_sample_si.py  -> batch2_si_pdf_check_sample.csv
"""
from __future__ import annotations

import re

import numpy as np
import pandas as pd

import pdf_check_sample as S

N, SEED = 20, 20261013


def main():
    pr = pd.read_csv(S.HERE / "runs" / "batch2_si" / "candidates_printed.csv", keep_default_na=False,
                     na_values=[""])
    rec = pd.read_csv(S.OUT2 / "records_normalized.csv", keep_default_na=False, na_values=[""])
    rec = rec.drop_duplicates(["doi", "entry_label"]).set_index(["doi", "entry_label"])
    pop = []
    for r in pr.itertuples():
        fields = ["rate", "T", "P"] + ([] if r.fused else ["metal_wt_pct"])
        if r.y_source == "printed outlet":
            fields.append("outlet_NH3")
        elif not pd.isna(r.WHSV):
            fields.append("WHSV")
        nr = rec.loc[(r.doi, r.entry)]
        filled = str(nr.get("filled") or "")
        for f in fields:
            m = re.search(rf"{S.FILL_KEY[f]}<-(\w+)", filled) if f in S.FILL_KEY else None
            src = m.group(1) if m else nr["pass"]
            if src in ("si", "si_figures"):
                pop.append((r.doi, r.entry, r.catalyst, f))
    rng = np.random.default_rng(SEED)
    idx = sorted(rng.choice(len(pop), size=min(N, len(pop)), replace=False))
    rows = []
    for k, i in enumerate(idx, 1):
        doi, entry, cat, f = pop[i]
        nr = rec.loc[(doi, entry)]
        pass_ = nr["pass"]
        raw = S.raw_record(doi, entry, pass_) or {}
        src_pass = pass_
        m = re.search(rf"{S.FILL_KEY[f]}<-(\w+)", str(nr.get("filled") or "")) if f in S.FILL_KEY else None
        if m:
            src_pass = m.group(1)
        q = raw.get(S.FIELDS[f]) or {}
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
    out.to_csv(S.HERE / "batch2_si_pdf_check_sample.csv", index=False, encoding="utf-8")
    print(f"population {len(pop)} SI-derived values from {len(pr)} printed entries; sampled {len(out)}")
    print(out.field.value_counts().to_dict(), out.source_pass.value_counts().to_dict())


if __name__ == "__main__":
    main()
