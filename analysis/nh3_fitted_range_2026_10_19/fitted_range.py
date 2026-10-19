"""NH3-FINAL-1.2 measured-kinetics comparisons with each catalyst restricted to the pressure range its rate law was fitted on.

Each catalyst searches for its optimum only among the process states inside its own fitted pressure range, then the two
optima are compared:

  Fe   (Dyson & Simon 1968, Temkin-Pyzhev, Topsoe KM1 data of Nielsen): 149-309 atm = 150.97-313.09 bar, 330-495 C
  Ru/C (Rossetti et al. 2006, promoted Ru/C):                             50-100 bar,                     370-460 C
  (parameters.yaml of analysis/nh3_staged_converter_2026_10_12, `validity` entries; Fe from Hansen 1995 p. 168,
   Ru/C from Rossetti 2006 Table 1 p. 4151)

The code path is the one that produced the manuscript numbers, imported unchanged:
  analysis/nh3_staged_converter_2026_10_12/kinetics_swap.py   (states, plug-flow amounts, costs, evaluate())
  analysis/nh3_frontier_provenance_2026_10_13/frontier_swap.py (generalised costs, break-even financing, price parity)
The script first reproduces the unrestricted numbers (Fe 14.93; Ru 33.07 / 38.26; Ru/C -3.46 / +1.45, KAAP -1.41 /
+1.73; break-even 7.23 / 5.37 %/y; parity 13.95x, 13.95-25.07x over variants; Ru price parity 3,781 USD/kg) and stops
unless they match, then applies the restriction. Only the masks over the existing 14,510 states change.

    set NH3_MODEL=1.2
    python fitted_range.py      -> results.json, results.csv (this folder)
"""
from __future__ import annotations

import csv
import json
import math
import os
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import brentq

assert os.environ.get("NH3_MODEL") == "1.2", "run with NH3_MODEL=1.2"
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "analysis" / "nh3_staged_converter_2026_10_12"))
sys.path.insert(0, str(REPO / "analysis" / "nh3_frontier_provenance_2026_10_13"))
import kinetics_swap as KS  # noqa: E402
import frontier_swap as FS  # noqa: E402

hc = KS.hc
P_RU = KS.P_RU
ATM = 1.01325
FIT = {
    "Fe": dict(P=(149.0 * ATM, 309.0 * ATM), T=(330.0, 495.0), P_src="149-309 atm", T_src="330-495 C",
               source="Nielsen KM1 data fitted by Dyson & Simon 1968 (Hansen 1995, p. 168); parameters.yaml Fe_DysonSimon.validity"),
    "Ru": dict(P=(50.0, 100.0), T=(370.0, 460.0), P_src="50-100 bar", T_src="370-460 C",
               source="Rossetti et al. 2006, Table 1 p. 4151; parameters.yaml Ru_C_Rossetti.validity"),
}
R = FS.R_HEAD                   # 95.55 % recovery
TOL = 1e-6


def masks(h):
    P, T = h.state_P, h.state_T
    m = {}
    for cat, f in FIT.items():
        m[cat + "_P"] = (P >= f["P"][0] - TOL) & (P <= f["P"][1] + TOL)
        m[cat + "_PT"] = m[cat + "_P"] & (T >= f["T"][0] - TOL) & (T <= f["T"][1] + TOL)
    m["all"] = np.ones(h.NSTATE, bool)
    m["KAAP"] = (P == 90.0) & (h.state_Tsep == -20.0)
    m["100_200"] = (P >= 100.0) & (P <= 200.0)
    m["sep_m20"] = h.state_Tsep == -20.0
    return m


def opt(h, tot, V, mask):
    t = np.where(mask, tot, np.inf)
    j = int(np.argmin(t))
    if not np.isfinite(t[j]):
        return None
    return dict(cost=float(t[j]), T_C=float(h.state_T[j]), P_bar=float(h.state_P[j]), Tsep_C=float(h.state_Tsep[j]),
                V_m3=float(V[j]))


class Variant(FS.Model):
    """frontier_swap.Model with the sizing x scale variant of kinetics_swap.evaluate() (rates multiplied by phi)."""

    def __init__(self, h, st, sizing, scale, fcal_target):
        super().__init__(h, st, sizing)
        j = next(i for i in range(h.NSTATE) if (h.state_T[i], h.state_P[i], h.state_Tsep[i]) == KS.CAL_STATE)
        self.phi = self.fe_V[j] / fcal_target if scale == "FCAL" else 1.0
        self.fe_V, self.ru_M = self.fe_V / self.phi, self.ru_M / self.phi
        self.name = f"{sizing}/{scale}"

    # --- costs (arrays over states) ---
    def fe_bench(self):
        (t, _), V = self.fe("benchmark", 0.0)
        return t, V

    def fe_cf(self, i):
        (t, _), V = self.fe("cashflow", i)
        return t, V

    def rub(self, alpha=1.0, p_ru=P_RU):
        (t, _), V = self.ru_bench(alpha=alpha, p_ru=p_ru)
        return t, V

    def ruc_cf(self, i, p_ru=P_RU):
        (t, _), V = self.ruc("cashflow", i, r=R, p_ru=p_ru)
        return t, V


def pair(M, fe, ru, mfe, mru):
    f, r = opt(M.h, *fe, mfe), opt(M.h, *ru, mru)
    gap = (r["cost"] - f["cost"]) if (f and r) else None
    return dict(Fe=f, Ru=r, gap=gap)


def parity_multiple(M, mfe, mru):
    target = opt(M.h, *M.fe_bench(), mfe)["cost"]

    def g(la):
        v = float(np.min(np.where(mru, M.rub(alpha=10.0 ** la)[0], np.inf)))
        return (v if math.isfinite(v) else 1e9) - target
    return 10 ** brentq(g, -6.0, 8.0, xtol=1e-12)


def bench_price_parity(M, mfe, mru):
    target = opt(M.h, *M.fe_bench(), mfe)["cost"]
    g = lambda lp: float(np.min(np.where(mru, M.rub(p_ru=10.0 ** lp)[0], np.inf))) - target  # noqa: E731
    p = 10 ** brentq(g, -2.0, 7.0, xtol=1e-12)
    return dict(price_USD_kg=p, factor_vs_current=p / P_RU, Fe=opt(M.h, *M.fe_bench(), mfe),
                Ru=opt(M.h, *M.rub(p_ru=p), mru))


def ruc_price_parity(M, i, mfe, mru):
    target = opt(M.h, *M.fe_cf(i), mfe)["cost"]
    g = lambda lp: float(np.min(np.where(mru, M.ruc_cf(i, p_ru=10.0 ** lp)[0], np.inf))) - target  # noqa: E731
    if g(-6.0) > 0:      # Ru/C dearer than Fe even with free Ru: no break-even price
        return dict(price_USD_kg=None, factor_vs_current=None, gap_at_zero_Ru_price=g(-6.0),
                    Fe=opt(M.h, *M.fe_cf(i), mfe), Ru=opt(M.h, *M.ruc_cf(i, p_ru=1e-6), mru))
    p = 10 ** brentq(g, -6.0, 8.0, xtol=1e-12)
    return dict(price_USD_kg=p, factor_vs_current=p / P_RU, Fe=opt(M.h, *M.fe_cf(i), mfe),
                Ru=opt(M.h, *M.ruc_cf(i, p_ru=p), mru))


def breakeven_fin(M, mfe, mru):
    g = lambda i: pair(M, M.fe_cf(i), M.ruc_cf(i), mfe, mru)["gap"]  # noqa: E731
    lo, hi = g(0.0), g(0.30)
    if not (lo < 0 < hi):
        return dict(rate=None, gap_0=lo, gap_30=hi)
    i = brentq(g, 0.0, 0.30, xtol=1e-10)
    return dict(rate=i, **pair(M, M.fe_cf(i), M.ruc_cf(i), mfe, mru))


def close(a, b, tol, what):
    assert abs(a - b) <= tol, (what, a, b)


def main():
    h = KS.build(False)
    st = KS.state_arrays(h)
    m = masks(h)
    _, V0, _, _ = h.cost_arrays("Fe", h.frozen_state_logtof(hc.EN0_CANON["Fe"]))
    j0 = next(i for i in range(h.NSTATE) if (h.state_T[i], h.state_P[i], h.state_Tsep[i]) == KS.CAL_STATE)
    fcal = float(V0[j0])
    variants = {(s, c): Variant(h, st, s, c, fcal) for s in ("plug", "inlet") for c in ("source", "FCAL")}
    M = variants[("plug", "source")]
    out = dict(model=dict(version=KS.NM.VERSION, run=KS.NM.RUNS[KS.NM.VERSION], n_states=int(h.NSTATE)),
               fitted_ranges={k: dict(P_bar=list(v["P"]), T_C=list(v["T"]), as_published=f"{v['P_src']}, {v['T_src']}",
                                      source=v["source"]) for k, v in FIT.items()})

    # state counts inside each range
    cnt = {}
    for cat in ("Fe", "Ru"):
        for k in ("P", "PT"):
            mk = m[f"{cat}_{k}"]
            cnt[f"{cat}_{k}"] = dict(n_states=int(mk.sum()), pressures_bar=sorted(set(h.state_P[mk].tolist())),
                                     temperatures_C=sorted(set(h.state_T[mk].tolist())))
    cnt["KAAP_states"] = int(m["KAAP"].sum())
    cnt["KAAP_states_in_Fe_range"] = int((m["KAAP"] & m["Fe_P"]).sum())
    cnt["KAAP_states_in_Ru_range"] = int((m["KAAP"] & m["Ru_P"]).sum())
    cnt["grid"] = dict(T_C=sorted(set(h.state_T.tolist())), P_step_bar=5.0, P_bar=[float(h.state_P.min()), float(h.state_P.max())])
    out["state_counts"] = cnt

    # ---------------- 0. reproduce the unrestricted numbers --------------------------------------------------------
    committed = json.loads((REPO / "analysis/nh3_staged_converter_2026_10_12/nh3_1_2/kinetics_swap.json").read_text(encoding="utf-8"))
    cv = next(v for v in committed["variants"] if v["sizing"] == "plug" and v["scale"] == "source")
    fr = json.loads((REPO / "analysis/nh3_frontier_provenance_2026_10_13/nh3_1_2/frontier_swap.json").read_text(encoding="utf-8"))
    A = m["all"]
    u = {}
    u["a"] = pair(M, M.fe_bench(), M.rub(), A, A)
    u["a_100_200"] = pair(M, M.fe_bench(), M.rub(), A, m["100_200"])
    u["parity"] = parity_multiple(M, A, A)
    u["parity_variants"] = {v.name: parity_multiple(v, A, A) for v in variants.values()}
    u["bench_price_parity"] = bench_price_parity(M, A, A)
    for i in (0.0, 0.12):
        u[f"b_{int(100 * i)}"] = pair(M, M.fe_cf(i), M.ruc_cf(i), A, A)
        u[f"c_{int(100 * i)}"] = pair(M, M.fe_cf(i), M.ruc_cf(i), m["KAAP"], m["KAAP"])
        u[f"e_ruc_price_{int(100 * i)}"] = ruc_price_parity(M, i, A, A)
    u["b_breakeven"] = breakeven_fin(M, A, A)
    u["c_breakeven"] = breakeven_fin(M, m["KAAP"], m["KAAP"])
    # asserts against the committed files and the manuscript's rounded values
    close(u["a"]["Fe"]["cost"], cv["Fe"]["cost"], 1e-5, "Fe"); assert round(u["a"]["Fe"]["cost"], 2) == 14.93
    assert (u["a"]["Fe"]["T_C"], u["a"]["Fe"]["P_bar"]) == (450.0, 140.0)
    close(u["a"]["Ru"]["cost"], cv["Ru_benchmark"]["cost"], 1e-5, "Ru"); assert round(u["a"]["Ru"]["cost"], 2) == 33.07
    assert u["a"]["Ru"]["P_bar"] == 735.0
    close(u["a_100_200"]["Ru"]["cost"], cv["Ru_benchmark_best_100_200_bar"]["cost"], 1e-5, "Ru 100-200")
    assert round(u["a_100_200"]["Ru"]["cost"], 2) == 38.26
    close(u["parity"], cv["Ru_activity_multiple_for_parity"], 1e-4, "parity"); assert round(u["parity"], 2) == 13.95
    pv = sorted(u["parity_variants"].values())
    assert (round(pv[0], 2), round(pv[-1], 2)) == (13.95, 25.07), pv
    for v in committed["variants"]:
        close(u["parity_variants"][f"{v['sizing']}/{v['scale']}"], v["Ru_activity_multiple_for_parity"], 1e-4, "variant parity")
    close(u["bench_price_parity"]["price_USD_kg"], fr["3_Ru_price_parity_benchmark"]["measured_kinetics_USD_kg"], 1e-3, "price")
    gaps = [u["b_0"]["gap"], u["b_12"]["gap"], u["c_0"]["gap"], u["c_12"]["gap"]]
    assert [round(g, 2) for g in gaps] == [-3.46, 1.45, -1.41, 1.73], gaps
    close(u["b_breakeven"]["rate"], fr["1_breakeven_financing_rate"]["r 0.9555 global"]["rate"], 1e-6, "be global")
    close(u["c_breakeven"]["rate"], fr["1_breakeven_financing_rate"]["r 0.9555 KAAP"]["rate"], 1e-6, "be KAAP")
    assert round(100 * u["b_breakeven"]["rate"], 1) == 7.2 and round(100 * u["c_breakeven"]["rate"], 1) == 5.4
    out["unrestricted"] = u
    print("unrestricted numbers reproduced", flush=True)

    # ---------------- 1. in-range rule ------------------------------------------------------------------------------
    res = {}
    for rule, (mfe, mru) in {"in_range_P": (m["Fe_P"], m["Ru_P"]), "in_range_PT": (m["Fe_PT"], m["Ru_PT"])}.items():
        d = {}
        d["a"] = pair(M, M.fe_bench(), M.rub(), mfe, mru)
        d["parity"] = parity_multiple(M, mfe, mru)
        d["parity_variants"] = {v.name: parity_multiple(v, mfe, mru) for v in variants.values()}
        d["parity_variants_detail"] = {v.name: pair(v, v.fe_bench(), v.rub(), mfe, mru) for v in variants.values()}
        d["bench_price_parity"] = bench_price_parity(M, mfe, mru)
        for i in (0.0, 0.12):
            k = int(100 * i)
            d[f"b_{k}"] = pair(M, M.fe_cf(i), M.ruc_cf(i), mfe, mru)
            # KAAP-type loop: Ru/C at its in-range KAAP states; Fe has none in range -> Fe in-range optimum,
            # and Fe in-range with the same -20 C separator
            d[f"c_{k}_vs_Fe_in_range"] = pair(M, M.fe_cf(i), M.ruc_cf(i), mfe, mru & m["KAAP"])
            d[f"c_{k}_vs_Fe_in_range_sep_m20"] = pair(M, M.fe_cf(i), M.ruc_cf(i), mfe & m["sep_m20"], mru & m["KAAP"])
            d[f"c_{k}_Fe_KAAP_in_range"] = opt(h, *M.fe_cf(i), mfe & m["KAAP"])          # None: no state
            d[f"e_ruc_price_{k}"] = ruc_price_parity(M, i, mfe, mru)
            d[f"e_ruc_price_{k}_KAAP_vs_Fe_in_range"] = ruc_price_parity(M, i, mfe, mru & m["KAAP"])
        d["b_breakeven"] = breakeven_fin(M, mfe, mru)
        d["c_breakeven_vs_Fe_in_range"] = breakeven_fin(M, mfe, mru & m["KAAP"])
        d["c_breakeven_vs_Fe_in_range_sep_m20"] = breakeven_fin(M, mfe & m["sep_m20"], mru & m["KAAP"])
        res[rule] = d
    out.update(res)
    out["Ru_C_460C_cap"] = dict(max_state_T_C=float(h.state_T.max()), respected=bool(h.state_T.max() <= 460.0))
    (HERE / "results.json").write_text(json.dumps(KS._clean(out), indent=1) + "\n", encoding="utf-8")
    write_csv(out)
    print(json.dumps(KS._clean({k: out[k] for k in ("in_range_P",)}), indent=1)[:5000])


def write_csv(out):
    rows = []

    def row(comp, rule, d, quantity="", value=None):
        f, r = (d or {}).get("Fe"), (d or {}).get("Ru")
        rr = dict(comparison=comp, rule=rule, quantity=quantity, value=value,
                  Fe_cost=f and f["cost"], Fe_T_C=f and f["T_C"], Fe_P_bar=f and f["P_bar"], Fe_Tsep_C=f and f["Tsep_C"],
                  Fe_V_m3=f and f["V_m3"],
                  Ru_cost=r and r["cost"], Ru_T_C=r and r["T_C"], Ru_P_bar=r and r["P_bar"], Ru_Tsep_C=r and r["Tsep_C"],
                  Ru_V_m3=r and r["V_m3"], gap_Ru_minus_Fe=(d or {}).get("gap"))
        if f and r and rr["gap_Ru_minus_Fe"] is None:
            rr["gap_Ru_minus_Fe"] = r["cost"] - f["cost"]
        rows.append(rr)

    u = out["unrestricted"]
    sets = [("unrestricted", u), ("in_range_P", out["in_range_P"]), ("in_range_PT", out["in_range_PT"])]
    for rule, d in sets:
        row("a Fe vs bulk-price Ru (benchmark)", rule, d["a"])
        if rule == "unrestricted":
            row("a Fe vs bulk-price Ru (benchmark); Ru best at 100-200 bar", rule, d["a_100_200"])
        for name, val in d["parity_variants"].items():
            row(f"d Ru activity multiple for parity ({name}{' headline' if name == 'plug/source' else ''})", rule, None, "multiple", val)
        p = d["bench_price_parity"]
        row("e bulk Ru break-even price (benchmark)", rule, p, "Ru_USD_kg", p["price_USD_kg"])
        row("e bulk Ru break-even price factor (benchmark)", rule, None, "factor_vs_53852.5", p["factor_vs_current"])
        for k in (0, 12):
            row(f"b Fe vs supported Ru/C; cash flow {k} %/y; r 95.55%", rule, d[f"b_{k}"])
            if rule == "unrestricted":
                row(f"c KAAP-type 90 bar/-20 C; cash flow {k} %/y", rule, d[f"c_{k}"])
            else:
                row(f"c KAAP-type: Ru/C 90 bar/-20 C vs Fe in-range optimum; {k} %/y", rule, d[f"c_{k}_vs_Fe_in_range"])
                row(f"c KAAP-type: Ru/C 90 bar/-20 C vs Fe in-range at -20 C separator; {k} %/y", rule,
                    d[f"c_{k}_vs_Fe_in_range_sep_m20"])
            p = d[f"e_ruc_price_{k}"]
            row(f"e supported Ru/C break-even Ru price; cash flow {k} %/y; r 95.55%", rule, p, "Ru_USD_kg", p["price_USD_kg"])
            row(f"e supported Ru/C break-even Ru price factor; cash flow {k} %/y", rule, None, "factor_vs_53852.5",
                p["factor_vs_current"])
            if rule != "unrestricted":
                p = d[f"e_ruc_price_{k}_KAAP_vs_Fe_in_range"]
                row(f"e Ru/C KAAP-type vs Fe in-range: break-even Ru price; cash flow {k} %/y", rule, p, "Ru_USD_kg",
                    p["price_USD_kg"])
        be = d["b_breakeven"]
        row("b break-even Ru financing rate; global", rule, be, "rate_per_y", be["rate"])
        if rule == "unrestricted":
            be = d["c_breakeven"]
            row("c break-even Ru financing rate; KAAP-type", rule, be, "rate_per_y", be["rate"])
        else:
            be = d["c_breakeven_vs_Fe_in_range"]
            row("c break-even financing; Ru/C KAAP-type vs Fe in-range optimum (none in 0-30 %/y)", rule, be, "rate_per_y", be["rate"])
            be = d["c_breakeven_vs_Fe_in_range_sep_m20"]
            row("c break-even financing; Ru/C KAAP-type vs Fe in-range at -20 C separator", rule, be, "rate_per_y", be["rate"])
    keys = list(rows[0])
    with (HERE / "results.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for r in rows:
            w.writerow({k: (f"{v:.6f}" if isinstance(v, float) else ("" if v is None else v)) for k, v in r.items()})


if __name__ == "__main__":
    main()
