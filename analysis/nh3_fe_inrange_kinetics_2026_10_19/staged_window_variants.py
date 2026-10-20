"""Fe-first window of the KAAP-type loop at 90 % recovery and at a Ru price 30 % lower or higher, read from the design
libraries with the same extraction as staged_inrange.window (boundary.decide). Dyson-Simon: committed library
(reproduces the SI: 0.13-6.14, 1.42-9.98, 0.50-4.92 %/y); Keestra KM1R-1964: staged_KM1R_1964_design_library.csv.

    set NH3_MODEL=1.2
    python staged_window_variants.py   -> staged_window_variants.json
"""
import json

import numpy as np

import staged_inrange as S
import boundary as B

out = {}
for name, path in (("Keestra KM1R-1964 (both in range)", S.HERE / "staged_KM1R_1964_design_library.csv"),
                   ("Dyson-Simon (committed library)", S.STAGED / "nh3_1_2" / "design_library.csv")):
    L = B.load_library(path)
    rows = {}
    for lab, p, r in (("base", S.PRICE, 0.9555), ("recovery 90%", S.PRICE, 0.90), ("Ru price -30%", S.PRICE * 0.7, 0.9555),
                      ("Ru price +30%", S.PRICE * 1.3, 0.9555)):
        dec = [B.decide(L, S.KAAP, p, r, i) for i in S.FINE]
        rows[lab] = dict(all_RuC_optimal_below=B._crossing(S.FINE, np.array([d["all_Ru"] - min(d["staged"], d["all_Fe"]) for d in dec])),
                         staged_beats_all_Fe_below=B._crossing(S.FINE, np.array([d["staged_minus_Fe"] for d in dec])))
    out[name] = rows
(S.HERE / "staged_window_variants.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
print(json.dumps(out, indent=1))
