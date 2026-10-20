"""NH3-FINAL-1.2 measured-kinetics comparisons with BOTH catalysts inside the pressure range of their rate law, the Fe law
being the Keestra et al. (2025) Model 3 law (keestra_fe.py), fitted on a pooled set of commercial-iron data at 1-324 bar.

Why: the Dyson-Simon law of the manuscript was fitted at 149-309 atm (151-313 bar) and the Rossetti Ru/C law at 50-100 bar,
so no pressure lies in both ranges and the KAAP-type loop (90 bar) and the 9 MPa staged converter extrapolate the Fe law
(analysis/nh3_fitted_range_2026_10_19). Keestra Model 3 with the activity factor of the same Topsoe KM1R catalyst whose
1964 data Dyson & Simon fitted (b_cat 0.350) covers 1-324 bar, so the two laws share 50-100 bar.

Everything else is the code path of analysis/nh3_fitted_range_2026_10_19/fitted_range.py (imported, unchanged): the
14,510 NH3-FINAL-1.2 states, plug-flow sizing, costs, u = 11, 8 wt% Ru/C at 490 kg m^-3, 95.55 % recovery, 25-year cash
flow. Only kinetics_swap.rate_fe_m3 is replaced. Fe variants: KM1R 1964 with the source K_f (headline), the same with the
Gillespie-Beattie K_f, and KM1R 1999 (b_cat 0.905). Dyson-Simon in its own range is carried along for reference.

    set NH3_MODEL=1.2
    D:\\Research\\CatalystForge\\.venv\\Scripts\\python.exe -X utf8 fe_inrange.py    # -> results.json, results.csv
"""
from __future__ import annotations

import csv
import json
import os
import sys
from pathlib import Path

import numpy as np

assert os.environ.get("NH3_MODEL") == "1.2", "run with NH3_MODEL=1.2"
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(REPO / "analysis" / "nh3_fitted_range_2026_10_19"))
import fitted_range as FR  # noqa: E402
import keestra_fe as KF  # noqa: E402

KS, h_c = FR.KS, FR.hc
DS_RATE = KS.rate_fe_m3
TOL = 1e-6
KEESTRA_RANGE = dict(P=(1.0, 324.0), T=(251.0, 550.0),
                     source="Keestra et al. 2025, pooled commercial-iron kinetic data (PR #114 sources.json transcription)")
FE_VARIANTS = {
    "Keestra KM1R-1964, source Kf": dict(catalyst="KM1R_1964", eq="source"),
    "Keestra KM1R-1964, GB Kf": dict(catalyst="KM1R_1964", eq="GB"),
    "Keestra KM1R-1999, source Kf": dict(catalyst="KM1R_1999", eq="source"),
}
HEADLINE = "Keestra KM1R-1964, source Kf"


def run_variant(h, st, m, fe_rate, mfe):
    KS.rate_fe_m3 = fe_rate
    try:
        M = FR.Variant(h, st, "plug", "source", None)
        _, V0, _, _ = h.cost_arrays("Fe", h.frozen_state_logtof(h_c.EN0_CANON["Fe"]))
        j0 = next(i for i in range(h.NSTATE) if (h.state_T[i], h.state_P[i], h.state_Tsep[i]) == KS.CAL_STATE)
        variants = [FR.Variant(h, st, s, c, float(V0[j0])) for s in ("plug", "inlet") for c in ("source", "FCAL")]
    finally:
        KS.rate_fe_m3 = DS_RATE
    mru = m["Ru_P"]
    kaap = m["KAAP"]
    both = mfe & mru                                         # 50-100 bar: inside both ranges
    d = dict(n_Fe_states=int(mfe.sum()), n_common_states=int(both.sum()),
             n_KAAP_states_in_Fe_range=int((kaap & mfe).sum()), n_KAAP_states_in_Ru_range=int((kaap & mru).sum()))
    d["a"] = FR.pair(M, M.fe_bench(), M.rub(), mfe, mru)
    d["a_common_50_100"] = FR.pair(M, M.fe_bench(), M.rub(), both, both)
    d["parity"] = FR.parity_multiple(M, mfe, mru)
    d["parity_variants"] = {v.name: FR.parity_multiple(v, mfe, mru) for v in variants}
    d["bench_price_parity"] = FR.bench_price_parity(M, mfe, mru)
    for i in (0.0, 0.12):
        k = int(100 * i)
        d[f"b_{k}"] = FR.pair(M, M.fe_cf(i), M.ruc_cf(i), mfe, mru)
        d[f"b_{k}_common_50_100"] = FR.pair(M, M.fe_cf(i), M.ruc_cf(i), both, both)
        d[f"c_{k}_KAAP"] = FR.pair(M, M.fe_cf(i), M.ruc_cf(i), mfe & kaap, mru & kaap)
        d[f"e_ruc_price_{k}"] = FR.ruc_price_parity(M, i, mfe, mru)
        if (mfe & kaap).any():
            d[f"e_ruc_price_{k}_KAAP"] = FR.ruc_price_parity(M, i, mfe & kaap, mru & kaap)
    d["b_breakeven"] = FR.breakeven_fin(M, mfe, mru)
    FR.R = 0.90                                              # 90 % recovery (fitted_range.R is read at call time)
    try:
        d["b_breakeven_r90"] = FR.breakeven_fin(M, mfe, mru)
        if (mfe & kaap).any():
            d["c_breakeven_KAAP_r90"] = FR.breakeven_fin(M, mfe & kaap, mru & kaap)
    finally:
        FR.R = FR.FS.R_HEAD
    if both.any():
        d["b_breakeven_common_50_100"] = FR.breakeven_fin(M, both, both)
    if (mfe & kaap).any():
        d["c_breakeven_KAAP"] = FR.breakeven_fin(M, mfe & kaap, mru & kaap)
    # Fe cost by pressure (cash flow 0 %/y), to show where the Fe optimum sits
    t0, _ = M.fe_cf(0.0)
    d["_Fe_profile_cf0"] = {float(P): float(np.min(np.where((h.state_P == P) & mfe, t0, np.inf)))
                            for P in np.unique(h.state_P) if P <= 330}
    return d


def main():
    h = KS.build(False)
    st = KS.state_arrays(h)
    m = FR.masks(h)
    P, T = h.state_P, h.state_T
    m_keestra = (P >= KEESTRA_RANGE["P"][0] - TOL) & (P <= KEESTRA_RANGE["P"][1] + TOL)
    assert np.all((T >= KEESTRA_RANGE["T"][0]) & (T <= KEESTRA_RANGE["T"][1]))

    # gate: the Dyson-Simon in-range numbers of fitted_range.py reproduce exactly
    ref = json.loads((REPO / "analysis/nh3_fitted_range_2026_10_19/results.json").read_text(encoding="utf-8"))["in_range_P"]
    ds = run_variant(h, st, m, DS_RATE, m["Fe_P"])
    for key in ("a", "b_0", "b_12"):
        FR.close(ds[key]["gap"], ref[key]["gap"], 1e-5, key)
    FR.close(ds["b_breakeven"]["rate"], ref["b_breakeven"]["rate"], 1e-6, "breakeven")
    print("Dyson-Simon in-range numbers reproduced", flush=True)

    out = dict(model=dict(version=KS.NM.VERSION, run=KS.NM.RUNS[KS.NM.VERSION], n_states=int(h.NSTATE)),
               ranges=dict(Fe_Keestra=KEESTRA_RANGE, Fe_DysonSimon=FR.FIT["Fe"], Ru_C_Rossetti=FR.FIT["Ru"]),
               Fe_DysonSimon_in_range=ds, Fe_Keestra={})
    for name, kw in FE_VARIANTS.items():
        fe_rate = (lambda kw: (lambda T, P_, yN, yH, yA: KF.rate(T, P_, yN, yH, yA, per="m3", **kw)))(kw)
        out["Fe_Keestra"][name] = run_variant(h, st, m, fe_rate, m_keestra)
        d = out["Fe_Keestra"][name]
        print(f"[{name}] Fe {d['a']['Fe']['cost']:.2f} ({d['a']['Fe']['P_bar']:.0f} bar) | bulk Ru {d['a']['Ru']['cost']:.2f} | "
              f"KAAP Ru/C-Fe 0/12 %/y {d['c_0_KAAP']['gap']:+.2f}/{d['c_12_KAAP']['gap']:+.2f}, be {d['c_breakeven_KAAP']['rate']} | "
              f"global Ru/C-Fe {d['b_0']['gap']:+.2f}/{d['b_12']['gap']:+.2f}, be {d['b_breakeven']['rate']}", flush=True)
    (HERE / "results.json").write_text(json.dumps(KS._clean(out), indent=1) + "\n", encoding="utf-8")
    write_csv(out)


def write_csv(out):
    rows = []
    sets = [("Dyson-Simon, own range (151-313 bar)", out["Fe_DysonSimon_in_range"])] + list(out["Fe_Keestra"].items())
    for fe, d in sets:
        def row(comp, x, quantity="", value=None):
            f, r = (x or {}).get("Fe"), (x or {}).get("Ru")
            rows.append(dict(Fe_law=fe, comparison=comp, quantity=quantity, value=value,
                             Fe_cost=f and f["cost"], Fe_T_C=f and f["T_C"], Fe_P_bar=f and f["P_bar"], Fe_Tsep_C=f and f["Tsep_C"],
                             Ru_cost=r and r["cost"], Ru_T_C=r and r["T_C"], Ru_P_bar=r and r["P_bar"], Ru_Tsep_C=r and r["Tsep_C"],
                             gap_Ru_minus_Fe=(x or {}).get("gap")))
        row("a Fe vs bulk-price Ru, each in range", d["a"])
        row("a Fe vs bulk-price Ru, both at 50-100 bar", d["a_common_50_100"])
        row("d Ru activity multiple for parity", None, "multiple", d["parity"])
        row("e bulk Ru break-even price", d["bench_price_parity"], "Ru_USD_kg", d["bench_price_parity"]["price_USD_kg"])
        for k in (0, 12):
            row(f"b Fe vs Ru/C, each in range; {k} %/y", d[f"b_{k}"])
            row(f"b Fe vs Ru/C, both at 50-100 bar; {k} %/y", d[f"b_{k}_common_50_100"])
            row(f"c KAAP-type 90 bar/-20 C, both catalysts; {k} %/y", d[f"c_{k}_KAAP"])
            p = d.get(f"e_ruc_price_{k}_KAAP")
            if p is not None:
                row(f"e KAAP-type Ru/C break-even Ru price; {k} %/y", p, "Ru_USD_kg", p["price_USD_kg"])
        for key, lab in (("b_breakeven", "each in range"), ("b_breakeven_common_50_100", "both at 50-100 bar"),
                         ("c_breakeven_KAAP", "KAAP-type")):
            be = d.get(key)
            if be is not None:
                row(f"break-even Ru financing rate, {lab}", be, "rate_per_y", be["rate"])
    with (HERE / "results.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        for r in rows:
            w.writerow({k: (f"{v:.6f}" if isinstance(v, float) else ("" if v is None else v)) for k, v in r.items()})


if __name__ == "__main__":
    main()
