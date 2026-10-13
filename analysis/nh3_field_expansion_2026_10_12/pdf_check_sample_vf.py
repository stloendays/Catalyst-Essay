"""PDF-check sample for the papers that the screening revisit with the SI newly included (batch2_screening.csv:
decision exclude, with_si_decision include), 10 values per paper, seed 20261013. Population and value lookup exactly as
in pdf_check_sample.py (uncorrected run runs/batch2_vf_screen): the printed primary values of the paper first; when a
paper has fewer than 10, the remainder is drawn at random from the values of its other primary entries of the
all-entries run (candidates.csv; plot readings included) so that 10 values per paper are checked.

    python pdf_check_sample_vf.py  -> batch2_vf_pdf_check_sample.csv
"""
from __future__ import annotations

import re

import numpy as np
import pandas as pd

import pdf_check_sample as S

N, SEED = 10, 20261013
RUN = S.HERE / "runs" / "batch2_vf_screen"


def values(df):
    pop = []
    for r in df.itertuples():
        fields = ["rate", "T", "P"] + ([] if r.fused else ["metal_wt_pct"])
        if r.y_source == "printed outlet":
            fields.append("outlet_NH3")
        elif not pd.isna(r.WHSV):
            fields.append("WHSV")
        pop += [(r.doi, r.entry, r.catalyst, f) for f in fields]
    return pop


def row(k, item, rec, cands, tier):
    doi, entry, cat, f = item
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
        used = cands[(cands.doi == doi) & (cands.entry == entry)].WHSV.iloc[0]
    return dict(id=k, doi=doi, entry=entry, catalyst=cat, field=f, tier=tier, value_used_model_basis=used,
                extracted_value=q.get("value"), extracted_unit=q.get("unit"), qualifier=q.get("qualifier"),
                location=q.get("location"), page=q.get("page"), source_pass=src_pass,
                primary_location=nr.primary_location)


def main():
    scr = pd.read_csv(S.HERE / "batch2_screening.csv")
    new = scr[(scr.decision == "exclude") & (scr.with_si_decision == "include")].doi.tolist()
    pr = pd.read_csv(RUN / "candidates_printed.csv", keep_default_na=False, na_values=[""])
    ca = pd.read_csv(RUN / "candidates.csv", keep_default_na=False, na_values=[""])
    ca = ca[ca.status.str.startswith("primary") & ca.cost_USD_t.notna()]
    rec = pd.read_csv(S.OUT2 / "records_normalized.csv", keep_default_na=False, na_values=[""])
    rec = rec.drop_duplicates(["doi", "entry_label"]).set_index(["doi", "entry_label"])
    rng = np.random.default_rng(SEED)
    rows = []
    for doi in new:
        a = values(pr[pr.doi == doi])
        pick = [(a[i], "printed primary") for i in sorted(rng.choice(len(a), size=min(N, len(a)), replace=False))]
        if len(pick) < N:
            b = [v for v in values(ca[ca.doi == doi]) if v not in a]
            pick += [(b[i], "all-entries primary") for i in sorted(rng.choice(len(b), size=min(N - len(pick), len(b)),
                                                                              replace=False))]
        cands = pd.concat([pr, ca], ignore_index=True)
        for item, tier in pick:
            rows.append(row(len(rows) + 1, item, rec, cands, tier))
        print(f"{doi}: printed primary values {len(a)}; sampled {len(pick)}")
    out = pd.DataFrame(rows)
    out.to_csv(S.HERE / "batch2_vf_pdf_check_sample.csv", index=False, encoding="utf-8")
    print(out.groupby(["doi", "tier"]).size().to_dict(), out.field.value_counts().to_dict())


if __name__ == "__main__":
    main()
