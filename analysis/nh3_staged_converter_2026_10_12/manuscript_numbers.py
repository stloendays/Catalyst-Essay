"""Numbers the manuscript quotes from this folder, recomputed from the outputs of the selected model.

    python manuscript_numbers.py                  -> manuscript_numbers.json          (NH3-FINAL-1.1 outputs)
    NH3_MODEL=1.2 python manuscript_numbers.py    -> nh3_1_2/manuscript_numbers.json  (NH3-FINAL-1.2 outputs)

Reads kinetics_swap.json and design_library.csv of the selected model folder and validation_summary.json (rate laws,
model-independent). Financing windows are the rate intervals over which each arrangement is the lower envelope of the
design library (boundary.py), on a 1e-5 grid of the metal financing rate with the edges refined by bisection.
"""
from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import boundary as B  # noqa: E402
import converter as C  # noqa: E402

OUT = C.OUT
P_RU = 53852.5
STAGED = {"FFR", "FRR"}
CLASS = {"FFF": "all-Fe", "RRR": "all-Ru/C", "FFR": "Fe-first", "FRR": "Fe-first"}


def r2(v, n=4):
    return None if v is None or (isinstance(v, float) and not math.isfinite(v)) else round(float(v), n)


# --- kinetics swap ------------------------------------------------------------------------------------------------

def swap_numbers():
    d = json.loads((OUT / "kinetics_swap.json").read_text(encoding="utf-8"))
    var = d["variants"]
    primary = var[0]["states"]
    head = next(v for v in var if v["states"] == primary and v["sizing"] == "plug" and v["scale"] == "source")
    fe, rb, rb12 = head["Fe"], head["Ru_benchmark"], head["Ru_benchmark_best_100_200_bar"]
    sup = head["Ru_C_supported"]
    out = dict(
        states=primary, n_states=head["n_states"], n_variants=len(var),
        descriptor_anchor=d["frozen_anchor_check"],
        Fe_optimum=dict(cost=fe["cost"], T_C=fe["T_C"], P_bar=fe["P_bar"], Tsep_C=fe["Tsep_C"], V_m3=fe["V_m3"]),
        Ru_benchmark_optimum=dict(cost=rb["cost"], T_C=rb["T_C"], P_bar=rb["P_bar"], Tsep_C=rb["Tsep_C"]),
        Ru_benchmark_best_100_200_bar=dict(cost=rb12["cost"], P_bar=rb12["P_bar"], above_optimum=r2(rb12["cost"] - rb["cost"])),
        Ru_parity_multiple=head["Ru_activity_multiple_for_parity"],
        Ru_parity_multiple_range=[min(v["Ru_activity_multiple_for_parity"] for v in var),
                                  max(v["Ru_activity_multiple_for_parity"] for v in var)],
        Ru_benchmark_optimum_P_range=[min(v["Ru_benchmark"]["P_bar"] for v in var), max(v["Ru_benchmark"]["P_bar"] for v in var)],
        Fe_optimum_cost_range=[min(v["Fe"]["cost"] for v in var), max(v["Fe"]["cost"] for v in var)],
        variants=[dict(states=v["states"], sizing=v["sizing"], scale=v["scale"], Fe=v["Fe"]["cost"], Fe_P=v["Fe"]["P_bar"],
                       Ru_benchmark=v["Ru_benchmark"]["cost"], Ru_benchmark_P=v["Ru_benchmark"]["P_bar"],
                       alpha=v["Ru_activity_multiple_for_parity"]) for v in var])
    b95, b90 = sup["benchmark 0% r 0.9555"], sup["benchmark 0% r 0.9"]
    out["supported_RuC_optimum"] = dict(
        r9555=dict(cost=b95["Ru_C_global"]["cost"], T_C=b95["Ru_C_global"]["T_C"], P_bar=b95["Ru_C_global"]["P_bar"],
                   Tsep_C=b95["Ru_C_global"]["Tsep_C"], minus_Fe=r2(b95["Ru_minus_Fe_global"])),
        r90=dict(cost=b90["Ru_C_global"]["cost"], P_bar=b90["Ru_C_global"]["P_bar"], minus_Fe=r2(b90["Ru_minus_Fe_global"])))
    gaps = {}
    for key, lab in (("cashflow 0% r 0.9555", "0%"), ("cashflow 12% r 0.9555", "12%"), ("cashflow 0% r 0.9", "0% r90"),
                     ("cashflow 12% r 0.9", "12% r90"), ("benchmark 0% r 0.9555", "benchmark"), ("benchmark 0% r 0.9", "benchmark r90")):
        s = sup[key]
        gaps[lab] = dict(global_RuC=s["Ru_C_global"]["cost"], global_Fe=s["Fe_global"]["cost"], global_gap=r2(s["Ru_minus_Fe_global"]),
                         RuC_P=s["Ru_C_global"]["P_bar"], KAAP_RuC=s["Ru_C_KAAP"]["cost"], KAAP_Fe=s["Fe_KAAP"]["cost"],
                         KAAP_gap=r2(s["Ru_minus_Fe_KAAP"]))
    out["RuC_minus_Fe"] = gaps
    across = {}
    for key, lab in (("cashflow 0% r 0.9555", "0%"), ("cashflow 12% r 0.9555", "12%")):
        g = [v["Ru_C_supported"][key]["Ru_minus_Fe_global"] for v in var]
        k = [v["Ru_C_supported"][key]["Ru_minus_Fe_KAAP"] for v in var]
        across[lab] = dict(global_range=[r2(min(g)), r2(max(g))], global_negative=sum(x < 0 for x in g),
                           KAAP_range=[r2(min(k)), r2(max(k))], KAAP_negative=sum(x < 0 for x in k), n=len(var))
    out["RuC_minus_Fe_across_variants"] = across
    return out


# --- staged converter ---------------------------------------------------------------------------------------------

def _cls(dec):
    return CLASS[dec["best"]]


def windows(L, loop, p_ru, recovery, accounting="dcf"):
    grid = np.round(np.linspace(0.0, 0.12, 12001), 7)
    dec = [B.decide(L, loop, p_ru, recovery, i, accounting) for i in grid]
    segs, start = [], 0
    for k in range(1, len(grid) + 1):
        if k == len(grid) or _cls(dec[k]) != _cls(dec[start]):
            segs.append([start, k - 1])
            start = k
    out = []
    for n, (a, b) in enumerate(segs):
        cls = _cls(dec[a])
        lo, hi = float(grid[a]), float(grid[b])
        if n > 0:                                     # refine the lower edge between grid[a-1] and grid[a]
            lo = _bisect(L, loop, p_ru, recovery, accounting, float(grid[a - 1]), float(grid[a]), _cls(dec[a - 1]))
        if n < len(segs) - 1:
            hi = _bisect(L, loop, p_ru, recovery, accounting, float(grid[b]), float(grid[b + 1]), cls)
        inside = dec[a:b + 1]
        pats = sorted({d["best"] for d in inside})
        out.append(dict(best=cls, patterns=pats, from_rate=lo if n > 0 else 0.0, to_rate=hi if n < len(segs) - 1 else 0.12,
                        Ru_share_start=r2(inside[0]["best_Ru_volume_fraction"]), Ru_share_end=r2(inside[-1]["best_Ru_volume_fraction"])))
    return out


def _bisect(L, loop, p_ru, recovery, accounting, a, b, cls_a):
    for _ in range(40):
        m = 0.5 * (a + b)
        if _cls(B.decide(L, loop, p_ru, recovery, m, accounting)) == cls_a:
            a = m
        else:
            b = m
    return 0.5 * (a + b)


def staged_numbers():
    L = B.load_library(OUT / "design_library.csv")
    kaap, c150, c200 = (90.0, -20.0), (150.0, -5.0), (200.0, -5.0)
    res = dict(
        KAAP_r9555=windows(L, kaap, P_RU, 0.9555), KAAP_r90=windows(L, kaap, P_RU, 0.90),
        KAAP_r9555_price_minus30=windows(L, kaap, 0.7 * P_RU, 0.9555), KAAP_r9555_price_plus30=windows(L, kaap, 1.3 * P_RU, 0.9555),
        loop150_r9555=windows(L, c150, P_RU, 0.9555), loop200_r9555=windows(L, c200, P_RU, 0.9555))
    sav = {}
    for i in (0.0135, 0.021, 0.04, 0.051):
        d = B.decide(L, kaap, P_RU, 0.9555, i)
        sav[f"{100 * i:.2f}%"] = dict(best=d["best"], staged_pattern=d["staged_pattern"], staged_minus_allFe=r2(d["staged_minus_Fe"]),
                                     staged_Ru_share=r2(d["staged_Ru_volume_fraction"]))
    res["KAAP_r9555_savings"] = sav
    bm = B.decide(L, kaap, P_RU, 0.9555, 0.0, accounting="frozen")
    res["KAAP_benchmark_accounting_r9555"] = dict(best=bm["best"], all_Ru=r2(bm["all_Ru"]), staged=r2(bm["staged"]),
                                                  all_Fe=r2(bm["all_Fe"]), all_Ru_minus_staged=r2(bm["all_Ru"] - bm["staged"]))
    ruc_first = []
    for name, keys in (("arrangements.csv", ("loop", "economics", "mode")), ("sensitivities.csv", ("case", "economics"))):
        with (OUT / name).open(encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        cases = {}
        for r in rows:
            cases.setdefault(tuple(r[k] for k in keys), []).append(r)
        for k, g in cases.items():
            b = min(g, key=lambda r: float(r["cost"]))
            if b["pattern"].startswith("R") and "F" in b["pattern"]:
                ruc_first.append(dict(file=name, case=k, best=b["pattern"]))
    res["RuC_first_optimal_cases"] = ruc_first
    return res


def rate_numbers():
    v = json.loads((HERE / "validation_summary.json").read_text(encoding="utf-8"))
    rr = v["rate_ratio_90bar"]
    return dict(rate_ratio_per_kg_400C=dict(yNH3_2pct=rr["400C_yNH3_0.02"]["Ru_over_Fe_per_kg"],
                                            yNH3_14pct=rr["400C_yNH3_0.14"]["Ru_over_Fe_per_kg"]),
                rate_ratio_per_m3_400C=dict(yNH3_2pct=rr["400C_yNH3_0.02"]["Ru_over_Fe_per_m3"],
                                            yNH3_14pct=rr["400C_yNH3_0.14"]["Ru_over_Fe_per_m3"]),
                apparent_orders_90bar=v["apparent_orders_90bar"])


def main():
    out = dict(model=C.NM.LABEL, kinetics_swap=swap_numbers(), staged=staged_numbers(), rate_laws=rate_numbers())
    (OUT / "manuscript_numbers.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
