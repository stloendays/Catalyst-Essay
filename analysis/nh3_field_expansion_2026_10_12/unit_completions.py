"""Sensitivity input (not the primary): the values normalize.py left unparsed (`flags` rate_unit / SV_unit) in
out_batch2/records_normalized.csv, converted by hand-checked factors -> batch2_unit_completions.csv, applied by
score.py --corrections in the run `batch2_units`.

  'X mmol-NH3/g-cat/h'                 -> rate_umol_gcat_h = 1000 X
  'X gNH3 gC+Co-1 h-1' (Tarka 2015)    -> rate_umol_gcat_h = X / 17.031 g mol-1 x 1e6 (per g of C + Co, Ba excluded)
  '72 L h-1 per gram of catalyst'      -> WHSV_mL_g_h = 72,000
Left out, correctly unparsed: 'normalized rate/temperature' (dimensionless) and '% NH3-yield' (not an outlet).
"""
import re
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
REC = HERE.parents[1] / "agent" / "nh3_field" / "out_batch2" / "records_normalized.csv"


def num(s):
    return float(re.match(r"\s*([\d.]+)", str(s)).group(1))


d = pd.read_csv(REC, keep_default_na=False, na_values=[""])
rows = []
for r in d[d["flags"].fillna("") != ""].itertuples():
    for fl in str(r.flags).split(";"):
        if fl == "rate_unit":
            raw = str(r.rate_raw)
            if re.search(r"mmol-NH3/g-cat/h", raw):
                v, note = num(raw) * 1000.0, "mmol -> umol"
            elif re.search(r"gNH3 gC\+Co", raw):
                v, note = num(raw) / 17.031 * 1e6, "g NH3 / 17.031 g mol-1 -> umol; per g (C + Co)"
            elif "normalized" in raw:     # a normalised (dimensionless) rate is not a rate; stays out
                continue
            else:
                raise SystemExit(f"unhandled rate unit {raw}")
            rows.append(dict(doi=r.doi, entry_label=r.entry_label, field="rate_umol_gcat_h", extracted=raw,
                             corrected=f"{v:.6g}", note=note))
        elif fl == "SV_unit":
            raw = str(r.SV_raw)
            if not re.search(r"L h.1 per gram of catalyst", raw):
                raise SystemExit(f"unhandled SV unit {raw}")
            rows.append(dict(doi=r.doi, entry_label=r.entry_label, field="WHSV_mL_g_h", extracted=raw,
                             corrected=f"{num(raw) * 1000:.6g}", note="L -> mL"))
out = pd.DataFrame(rows)
out.to_csv(HERE / "batch2_unit_completions.csv", index=False, encoding="utf-8")
print(len(out), out.groupby(["doi", "field"]).size().to_dict())
