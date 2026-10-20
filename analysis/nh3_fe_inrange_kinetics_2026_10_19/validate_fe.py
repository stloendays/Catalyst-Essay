"""Checks of the Keestra 2025 Model 3 fused-iron law (keestra_fe.py) against the data and laws already in the repository.

1. Equilibrium: source K_f against the Gillespie-Beattie constant of the loop states, 350-450 C.
2. Micropilot points at 100 bar, 430 C, GHSV 30,000 h^-1, H2/N2 3 (Tripodi et al. 2018 AAM p. 7, data of Pernicone
   et al. 2003 / Rossetti 2006, as in analysis/nh3_staged_converter_2026_10_12/validate_kinetics.py): commercial magnetite
   about 8 vol% NH3, wustite about 12.5 vol%. The micropilot pressure lies outside the Dyson-Simon range.
3. Same catalyst, Dyson-Simon's own range: KM1R (1964) Keestra bed volume against the Dyson-Simon bed volume, plug flow,
   on every NH3-FINAL-1.2 state at 155-310 bar (the states the in-range comparison uses for Dyson-Simon).

    set NH3_MODEL=1.2
    python validate_fe.py   -> validation.json
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np

assert os.environ.get("NH3_MODEL") == "1.2", "run with NH3_MODEL=1.2"
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "nh3_staged_converter_2026_10_12"))
import keestra_fe as KF  # noqa: E402
import kinetics as K  # noqa: E402
import kinetics_swap as KS  # noqa: E402
import validate_kinetics as VK  # noqa: E402


def main():
    out = {}
    out["Kf_source_over_GB"] = {f"{t} C": float(KF.Kf_source(t + 273.15) / KF.Kf_GB(t + 273.15)) for t in (350, 375, 400, 425, 450)}

    mp = {}
    for cat in KF.BCAT:
        mp[f"Keestra {cat}"] = VK.pfr_outlet(lambda T, P, a, b, c, cat=cat: KF.rate(T, P, a, b, c, catalyst=cat), 430, 100, 30000,
                                             KF.BED_DENSITY / 1000)
    mp["Dyson-Simon KM1"] = VK.pfr_outlet(lambda T, P, a, b, c: K.rate_fe_dyson_simon(T, P, a, b, c, per="m3"), 430, 100, 30000,
                                          None, per_volume=True)
    out["micropilot_430C_100bar_30000h"] = dict(
        model_pct=mp, measured_pct=dict(magnetite=8.0, wustite=12.5),
        rel_err={"Keestra KM1R_1964 vs magnetite": mp["Keestra KM1R_1964"] / 8.0 - 1,
                 "Dyson-Simon vs magnetite": mp["Dyson-Simon KM1"] / 8.0 - 1,
                 "Keestra KM1R_1999 vs wustite": mp["Keestra KM1R_1999"] / 12.5 - 1,
                 "Keestra AmoMax10 vs wustite": mp["Keestra AmoMax10_2024"] / 12.5 - 1})

    # 4. apparent orders at 90 bar, 400 C, 2 % NH3 (kinetics.apparent_orders) and the Ru/C (8 wt%) / Fe rate ratio along
    #    the converter, as in validate_kinetics.py (Fe there: Dyson-Simon per kg at 2,850 kg m^-3)
    out["apparent_orders_90bar_400C_2pct"] = dict(
        Fe_Keestra_KM1R1964=K.apparent_orders(lambda T, P, a, b, c: KF.rate(T, P, a, b, c), 673.15, 90.0, 0.02),
        Fe_DysonSimon=K.apparent_orders(K.rate_fe_dyson_simon, 673.15, 90.0, 0.02),
        Ru_C_Rossetti=K.apparent_orders(K.rate_ru_rossetti, 673.15, 90.0, 0.02))
    ratios = {}
    for yA in (0.02, 0.06, 0.10, 0.14):
        yN = (1 - yA) / 4
        fe_ = float(KF.rate(673.15, 90.0, yN, 3 * yN, yA))
        ru_ = float(K.rate_ru_rossetti(673.15, 90.0, yN, 3 * yN, yA, ru_wt_frac=0.08))
        ratios[f"400C_yNH3_{yA}"] = dict(Ru_over_Fe_per_kg=ru_ / fe_, Ru_over_Fe_per_m3=ru_ * 490 / (fe_ * KF.BED_DENSITY))
    out["rate_ratio_90bar_Keestra"] = ratios

    h = KS.build(False)
    st = KS.state_arrays(h)
    ds = KS.amount(st, KS.rate_fe_m3, h, "plug")
    kee = KS.amount(st, lambda T, P, a, b, c: KF.rate(T, P, a, b, c, per="m3"), h, "plug")
    ok = np.isfinite(ds) & np.isfinite(kee)
    for lab, m in (("155-310 bar (Dyson-Simon range)", (h.state_P >= 150.97) & (h.state_P <= 313.09)),
                   ("90 bar, -20 C (KAAP-type)", (h.state_P == 90.0) & (h.state_Tsep == -20.0)),
                   ("50-100 bar", (h.state_P >= 50.0) & (h.state_P <= 100.0))):
        r = (kee / ds)[m & ok]
        out[f"bed_volume_Keestra_KM1R1964_over_DysonSimon, {lab}"] = dict(
            n=int(r.size), median=float(np.median(r)), p05=float(np.percentile(r, 5)), p95=float(np.percentile(r, 95)),
            min=float(r.min()), max=float(r.max()))
    (HERE / "validation.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
