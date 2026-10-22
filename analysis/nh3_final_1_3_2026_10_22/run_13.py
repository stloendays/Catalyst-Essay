"""NH3-FINAL-1.3 against NH3-FINAL-1.2 on one code path (PREREGISTRATION.md).

    set NH3_MODEL=1.2          (the 1.2 core and manifest; 1.3 is the subclass in harness13.py)
    D:\\Research\\CatalystForge\\.venv\\Scripts\\python.exe -X utf8 run_13.py   -> results.json, benchmark_rescore.csv

1. Gates: VLE hold-out (Uhde Figure 57 streams 5 and 6), compression items E01-E03, re-score of the registered
   state-level benchmark items (Tables A, E, V) with their registered rules.
2. Descriptor model, 1.2 and 1.3 on direct state kinetics (the 1.2 canonical anchors use the cached interpolated
   surface; the direct path is reported next to them): Fe, Ru, Os costs and optima, gap decomposition, Ru price parity
   and activity multiple.
3. Measured rate laws (Keestra KM1R-1964 Fe in 1-324 bar, Rossetti Ru/C in 50-100 bar, plug flow): Fe and Ru/C costs at
   0, 2.10 and 12 %/y, break-even financing rate on own optima and in the KAAP-type loop, bulk-Ru parity.
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

os.environ["NH3_MODEL"] = "1.2"
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
AN = REPO / "analysis"
for p in (HERE, AN, AN / "nh3_staged_converter_2026_10_12", AN / "nh3_frontier_provenance_2026_10_13",
          AN / "nh3_fitted_range_2026_10_19", AN / "nh3_fe_inrange_kinetics_2026_10_19",
          AN / "validation_nh3_plant_2026_10_13"):
    sys.path.insert(0, str(p))
import harness13 as H13  # noqa: E402
import kinetics_swap as KS  # noqa: E402
import keestra_fe as KF  # noqa: E402
KS.rate_fe_m3 = lambda T, P, a, b, y: KF.rate(T, P, a, b, y, catalyst="KM1R_1964", eq="source", per="m3")
import frontier_swap as FS  # noqa: E402
import fitted_range as FR  # noqa: E402

hc = H13.hc
NM = H13.NM
REF_RATE = 0.0210
FE_P, RU_P = (1.0, 324.0), (50.0, 100.0)
VB = AN / "validation_nh3_plant_2026_10_13"


# ---------------------------------------------------------------------------------------------------------- gates
def vle_holdout():
    out = []
    for sid, T, P_MPa, obs in ((5, 21.0, 18.02, 8.51), (6, 0.0, 17.88, 4.18)):
        y = 100.0 * H13.y_sep(T, P_MPa * 10.0)
        out.append(dict(stream=sid, T_C=T, P_MPa=P_MPa, observed=obs, model_1_2=100 * H13.psat_bar(T) / (P_MPa * 10),
                        model_1_3=y, dev_1_3=(y - obs) / obs, ok=abs(y - obs) / obs <= 0.20))
    return out


def _rows(name):
    return list(csv.DictReader((VB / name).open(encoding="utf-8")))


def _f(x):
    return float(x) if x not in ("", None) else None


def judge(rule, model, value, low, high, windows):
    """validation_nh3_plant_2026_10_13/run_benchmark.judge, copied (that module cannot be imported next to this one)."""
    if model is None or (isinstance(model, float) and not math.isfinite(model)):
        return False, "no model value"
    kind, _, arg = rule.partition(":")
    if kind == "rel":
        tol = float(arg)
        if value is not None:
            dev = (model - value) / value
            return abs(dev) <= tol + 1e-12, f"{100 * dev:+.1f} %"
        lo, hi = low * (1 - tol), high * (1 + tol)
        return lo - 1e-12 <= model <= hi + 1e-12, f"band {lo:.4g}-{hi:.4g}"
    if kind == "factor":
        ratio = model / value
        return 1 / float(arg) <= ratio <= float(arg), f"ratio {ratio:.2f}"
    if kind == "abs":
        dev = model - value
        return abs(dev) <= float(arg) + 1e-12, f"{dev:+.1f}"
    if kind == "range":
        return low <= model <= high, f"range {low:.4g}-{high:.4g}"
    if kind == "window":
        w = windows[arg]
        return w["low"] <= model <= w["high"], f"{arg} {w['low']:.4g}-{w['high']:.4g}"
    raise ValueError(rule)


def state_values(h, c):
    """validation nh3_model.state_point + _state_dict + fe_bed_m3 (Dyson-Simon plug flow), copied."""
    import kinetics as K
    tpd = float(c["capacity_tpd"])
    s = h.self_consistent_process_state(float(c["T_C"]), float(c["P_bar"]), float(c["Tsep_C"]))
    if s is None:
        return None
    X, ysep = s["X"], s["ysep"]
    nA = ysep / (1.0 - ysep) * 2.0 * (1.0 - X) / X
    tot_in = 2.0 / X + nA
    tot_out = tot_in - 1.0
    y_in, y_out = nA / tot_in, (nA + 1.0) / tot_out
    el = h.ELECTRICITY
    d = dict(inlet_NH3_molpct=100 * y_in, outlet_NH3_molpct=100 * y_out, delta_NH3_molpct=100 * (y_out - y_in),
             inlet_to_makeup=tot_in / 2.0, inlet_Nm3_h=s["inlet_Nm3_h"] * tpd / h.PLANT_TPD,
             fresh_comp_MWh_t=s["fresh_comp"] / el, recycle_comp_MWh_t=s["recycle_comp"] / el)
    st = dict(T=np.array([s["T_C"] + 273.15]), P=np.array([s["P_bar"]]), yN=np.array([(0.5 / X) / tot_in]),
              yH=np.array([(1.5 / X) / tot_in]), yA=np.array([max(nA / tot_in, 1e-12)]), xi_out=np.array([0.5 / tot_in]),
              F_in=np.array([h.nh3_mol_s * tot_in]), X=np.array([X]))
    V = float(KS.amount(st, lambda T, P, a, b, y: K.rate_fe_dyson_simon(T, P, a, b, y, per="m3"), h, "plug")[0]) * tpd / h.PLANT_TPD
    d.update(Fe_bed_m3=V, GHSV_h=d["inlet_Nm3_h"] / V if V > 0 and math.isfinite(V) else math.nan)
    d["fresh_plus_recycle_MW"] = (d["fresh_comp_MWh_t"] + d["recycle_comp_MWh_t"]) * tpd / 24.0
    d["recycle_MW"] = d["recycle_comp_MWh_t"] * tpd / 24.0
    return d


def benchmark(h, label):
    cases = {r["case_id"]: r for r in _rows("benchmark_cases.csv")}
    windows = {r["window_id"]: dict(low=float(r["window_low"]), high=float(r["window_high"]))
               for r in _rows("industrial_windows.csv")}
    vals = {k: state_values(h, c) for k, c in cases.items() if c["level"] == "state"}
    rows = []
    for m in _rows("benchmark_metrics.csv"):
        if m["table"] not in ("A", "E", "V"):
            continue
        if m["table"] == "V":
            rat = []
            for (t, p), v in H13.TAB.items():
                if 10 <= p <= 30 and -30 <= t <= 30:
                    model = 100.0 * (H13.y_sep(t, 10.0 * p) if label == "1.3" else H13.psat_bar(t) / (10.0 * p))
                    rat.append(model / v)
            model = float(np.median(rat))
        else:
            d = vals.get(m["case_id"])
            model = None if d is None else d.get(m["quantity"])
        if model is None:
            rows.append(dict(metric=m["metric_id"], quantity=m["quantity"], model=None, ok=False, note="no state"))
            continue
        ok, note = judge(m["rule"], float(model), _f(m["industrial_value"]), _f(m["industrial_low"]),
                         _f(m["industrial_high"]), windows)
        rows.append(dict(metric=m["metric_id"], quantity=m["quantity"], value=m["industrial_value"], model=float(model),
                         ok=bool(ok), note=note))
    return rows


# --------------------------------------------------------------------------------------------- descriptor model
def descriptor(h):
    out = {}
    lv = {m: h.direct_state_logtof(hc.EN0_CANON[m]) for m in h.activity_order}
    det = {}
    for m in h.activity_order:
        tot, V, metal, reactor = h.cost_arrays(m, lv[m])
        ok = V <= h.V_CAP
        if not ok.any():
            det[m] = None
            continue
        i = int(np.argmin(np.where(ok, tot, np.inf)))
        det[m] = dict(cost=float(tot[i]), T_C=float(h.state_T[i]), P_bar=float(h.state_P[i]), Tsep_C=float(h.state_Tsep[i]),
                      V_m3=float(V[i]), breakdown=h.cost_breakdown_at(m, V, metal, reactor, i))
    order = sorted([m for m in det if det[m]], key=lambda m: det[m]["cost"])
    out["metals"] = det
    out["order"] = order
    fe = det["Fe"]["cost"]
    out["Ru_minus_Fe"] = det["Ru"]["cost"] - fe
    out["gap_pools"] = {k: det["Ru"]["breakdown"][k] - det["Fe"]["breakdown"][k] for k in det["Fe"]["breakdown"]}

    def ru_min(price=None, alpha=1.0):
        tot, V, _, _ = h.cost_arrays("Ru", lv["Ru"], price=price, alpha=alpha)
        return float(np.min(np.where(V <= h.V_CAP, tot, np.inf)))
    out["Ru_price_parity_USD_kg"] = 10 ** brentq(lambda lp: ru_min(price=10 ** lp) - fe, 0.0, 6.0, xtol=1e-10)
    g = lambda la: (lambda v: (v if math.isfinite(v) else 1e9) - fe)(ru_min(alpha=10 ** la))  # noqa: E731
    out["Ru_activity_multiple_for_parity"] = 10 ** brentq(g, -3.0, 6.0, xtol=1e-10)
    out["Ru_priced_as_Fe"] = ru_min(price=hc.PRICE["Fe"])
    return out


# ------------------------------------------------------------------------------------------- measured rate laws
def measured(h):
    st = KS.state_arrays(h)
    M = FR.Variant(h, st, "plug", "source", None)
    P = h.state_P
    mfe = (P >= FE_P[0] - 1e-6) & (P <= FE_P[1] + 1e-6)
    mru = (P >= RU_P[0] - 1e-6) & (P <= RU_P[1] + 1e-6)
    kaap = (P == 90.0) & (h.state_Tsep == -20.0)
    out = dict(Fe_benchmark=FR.opt(h, *M.fe_bench(), mfe))
    for i in (0.0, REF_RATE, 0.12):
        out[f"own_optima_{100 * i:.2f}"] = FR.pair(M, M.fe_cf(i), M.ruc_cf(i), mfe, mru)
        out[f"KAAP_{100 * i:.2f}"] = FR.pair(M, M.fe_cf(i), M.ruc_cf(i), mfe & kaap, mru & kaap)
    out["breakeven_own_optima"] = FR.breakeven_fin(M, mfe, mru)
    out["breakeven_KAAP"] = FR.breakeven_fin(M, mfe & kaap, mru & kaap)
    out["bulk_Ru_price_parity"] = FR.bench_price_parity(M, mfe, mru)
    out["bulk_Ru_activity_parity"] = FR.parity_multiple(M, mfe, mru)
    return out


def brief(d):
    if isinstance(d, dict):
        return {k: brief(v) for k, v in d.items() if not k.startswith("_")}
    if isinstance(d, (np.floating, np.integer)):
        return float(d)
    return d


def main():
    res = dict(gates={})
    res["gates"]["G1_vle_holdout"] = vle_holdout()
    h12 = NM.harness()
    h13 = H13.build()
    res["model"] = {"1.2": dict(n_states=int(h12.NSTATE), F_CAL=float(h12.F_CAL)),
                    "1.3": dict(n_states=int(h13.NSTATE), F_CAL=float(h13.F_CAL))}
    bench = {}
    for lab, h in (("1.2", h12), ("1.3", h13)):
        bench[lab] = benchmark(h, lab)
    with (HERE / "benchmark_rescore.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["metric", "quantity", "value", "model_1_2", "pass_1_2", "model_1_3", "pass_1_3", "note_1_3"])
        for a, b in zip(bench["1.2"], bench["1.3"]):
            w.writerow([a["metric"], a["quantity"], a.get("value"), a.get("model"), a["ok"], b.get("model"), b["ok"], b.get("note")])
    res["gates"]["G2_compression"] = {r["metric"]: dict(model=r.get("model"), ok=r["ok"], note=r.get("note"))
                                      for r in bench["1.3"] if r["metric"].startswith("E")}
    res["gates"]["G3_state_items_pass"] = {lab: f"{sum(r['ok'] for r in b)}/{len(b)}" for lab, b in bench.items()}
    print(json.dumps(res["gates"], indent=1, default=float), flush=True)
    res["descriptor"] = {"1.2_direct": descriptor(h12), "1.3": descriptor(h13),
                         "1.2_canonical_anchors": {k: v for k, v in NM.anchors().items() if k in ("Fe", "Ru", "Os")}}
    res["measured"] = {"1.2": measured(h12), "1.3": measured(h13)}
    (HERE / "results.json").write_text(json.dumps(brief(res), indent=1, default=float) + "\n", encoding="utf-8")
    for lab in ("1.2_direct", "1.3"):
        d = res["descriptor"][lab]
        print(lab, "order", d["order"][:4], {m: round(d["metals"][m]["cost"], 3) for m in ("Fe", "Ru", "Os") if d["metals"][m]},
              "gap", round(d["Ru_minus_Fe"], 3), "price parity", round(d["Ru_price_parity_USD_kg"], 1),
              "activity", round(d["Ru_activity_multiple_for_parity"], 1),
              "Fe opt", (d["metals"]["Fe"]["T_C"], d["metals"]["Fe"]["P_bar"]), "Ru opt", (d["metals"]["Ru"]["T_C"], d["metals"]["Ru"]["P_bar"]))
    for lab in ("1.2", "1.3"):
        m = res["measured"][lab]
        print(lab, "Fe", round(m["Fe_benchmark"]["cost"], 3), "gap0", round(m["own_optima_0.00"]["gap"], 3),
              "gap2.1", round(m["own_optima_2.10"]["gap"], 3), "KAAP2.1", round(m["KAAP_2.10"]["gap"], 3),
              "gap12", round(m["own_optima_12.00"]["gap"], 3), "BE", m["breakeven_own_optima"].get("rate"),
              "BE KAAP", m["breakeven_KAAP"].get("rate"), "bulk price", round(m["bulk_Ru_price_parity"]["price_USD_kg"], 0),
              "bulk act", round(m["bulk_Ru_activity_parity"], 2))


if __name__ == "__main__":
    main()
