"""Run the pre-registered benchmark of the latest NH3 plant model against industrial ammonia plants.

    python run_benchmark.py [--workers N]          (N <= 8; about 10 min)

Order: (1) the frozen Fe 15.29 / Ru 22.03 and measured-kinetics Fe 15.58 optima are reproduced (assertion) before
anything else; (2) every case of benchmark_cases.csv is run at the model level it names; (3) every comparison of
benchmark_metrics.csv is judged by its pre-registered rule; (4) the PR #77 column and the uncounted sensitivities.

Outputs (this folder): results_metrics.csv, results_cases.json, results_sensitivity.csv, summary.json.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import multiprocessing as mp
import re
import statistics
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import converter_sim as CS  # noqa: E402
import nh3_model as M  # noqa: E402

C, S = M.C, M.S
STAGED = M.STAGED
T_SHIFT = 25.0                    # uncounted sensitivity on T_REF


def rows(name):
    return list(csv.DictReader((HERE / name).open(encoding="utf-8")))


def fnum(x):
    return float(x) if x not in ("", None) else None


# --- converter jobs (run in worker processes) ------------------------------------------------------------------------

def design_job(job):
    """Cost-optimal converter at the plant's loop conditions, run at the model's own 1000 t/d cost basis (converter.py
    prices per tonne with the 1000 t/d annual output); volumes are reported per t/d. Best of three DE seeds."""
    t0 = time.time()
    econ = C.Econ(accounting="frozen", recovery=0.9555)
    pattern = tuple({"F": "Fe", "R": "Ru"}[c] for c in job["pattern"])
    best = None
    for seed in (1, 2, 3):
        r = M.converter_design(pattern, job["P_bar"], job["Tsep_C"], job["inerts"], tpd=1000.0, econ=econ, seed=seed)
        if best is None or r["cost"] < best["cost"]:
            best = r
    d = best["detail"]
    beds = d["beds"]
    out = dict(case_id=job["case_id"], cost=best["cost"], x=best["x"], outlet_NH3_molpct=100 * d["y_NH3_out"],
               inlet_NH3_molpct=100 * d["y_NH3_in"], bed1_T_in_C=beds[0]["T_in_C"],
               max_T_C=max(b["T_out_C"] for b in beds), V_m3_at_1000tpd=d["V_m3"], V_m3_per_tpd=d["V_m3"] / 1000.0,
               Fe_volume_fraction=1.0 - d["Ru_volume_fraction"], Ru_volume_fraction=d["Ru_volume_fraction"],
               beds=[{k: (float(v) if isinstance(v, (int, float, np.floating)) else v) for k, v in b.items()} for b in beds],
               seconds=time.time() - t0)
    return out


def minvol_job(job):
    t0 = time.time()
    r = CS.min_volume(job["P_bar"], job["inlet_Nm3_h"], job["yNH3"], job["y_out"], job["inerts"], n_beds=int(job["n_beds"]))
    r["case_id"] = job["case_id"]
    r["seconds"] = time.time() - t0
    return r


# --- judging ---------------------------------------------------------------------------------------------------------

def judge(rule, model, value, low, high, windows):
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
    if kind == "equals":
        return bool(model) == (arg == "True"), ""
    if kind == "below":
        return model < float(arg), ""
    if kind == "above":
        return model > float(arg), ""
    raise ValueError(rule)


# --- model side ------------------------------------------------------------------------------------------------------

def state_values(h, c, T=None, pr77=False, gb=False):
    """gb=True: uncounted diagnostic, the same harness with the Gillespie-Beattie gas Gibbs energy (PR #64 states)."""
    T = float(c["T_C"]) if T is None else T
    f = M.state_point_pr77 if pr77 else M.state_point
    if gb:
        with M._GBGibbs():
            d = f(h, T, float(c["P_bar"]), float(c["Tsep_C"]), float(c["capacity_tpd"]))
    else:
        d = f(h, T, float(c["P_bar"]), float(c["Tsep_C"]), float(c["capacity_tpd"]))
    if d is None:
        return None
    tpd = float(c["capacity_tpd"])
    d["fresh_plus_recycle_MW"] = (d["fresh_comp_MWh_t"] + d["recycle_comp_MWh_t"]) * tpd / 24.0
    d["recycle_MW"] = d["recycle_comp_MWh_t"] * tpd / 24.0
    d["refrigeration_MW"] = d["refrigeration_MWh_t"] * tpd / 24.0
    return d


def staged_checks():
    """C08-C10 from the committed outputs of analysis/nh3_staged_converter_2026_10_12 (reproduced by its CI)."""
    import pandas as pd
    from scipy.stats import spearmanr
    up = []
    for name, key in (("arrangements.csv", "loop"), ("sensitivities.csv", "case")):
        df = pd.read_csv(STAGED / name)
        for g, sub in df.groupby([key, "economics", "mode"]):
            best = sub.loc[sub.cost.idxmin(), "pattern"]
            first_ru = best.find("R")
            if first_ru >= 0 and "F" in best[first_ru:]:
                up.append((name, g, best))
    bs = json.loads((STAGED / "boundary_summary.json").read_text(encoding="utf-8"))
    c90 = next(e for e in bs["critical_financing_rate"]
               if e["P_bar"] == 90.0 and e["Tsep_C"] == -20.0 and e["recovery"] == 0.9555 and e["p_Ru"] == 53852.5)
    sweep = [(e["P_bar"], e["staged_beats_Fe_below_rate"]) for e in bs["pressure"] if e["Tsep_C"] == -20.0]
    rho = float(spearmanr([p for p, _ in sweep], [r for _, r in sweep]).statistic)
    n_groups = sum(pd.read_csv(STAGED / n).groupby([k, "economics", "mode"]).ngroups
                   for n, k in (("arrangements.csv", "loop"), ("sensitivities.csv", "case")))
    return dict(Ru_upstream_of_Fe_in_any_optimum=bool(up), upstream_cases=[str(u) for u in up], n_optima_checked=n_groups,
                Ru_in_optimum_at_12pct=c90["Ru_in_optimum_below"] > 0.12, Ru_in_90bar_optimum_below_rate=c90["Ru_in_optimum_below"],
                spearman_P_vs_Ru_financing_boundary=rho, pressure_sweep=sweep)


def ullmann_ratio(h):
    out = []
    for r in rows("reference_values.csv"):
        if r["record"].startswith("NH3 concentration at saturation over liquid NH3"):
            m = re.search(r"T = (-?\d+) C and total p = (\d+) MPa", r["note"])
            T, P_MPa = float(m.group(1)), float(m.group(2))
            if 10 <= P_MPa <= 30 and -30 <= T <= 30:
                y_model = 100 * h.psat_nh3_bar(T) / (10 * P_MPa)
                out.append(dict(row_id=r["row_id"], T_C=T, P_MPa=P_MPa, table=float(r["value"]), model=y_model,
                                ratio=y_model / float(r["value"])))
    return statistics.median(o["ratio"] for o in out), out


def optimum_values(h, r):
    fe = r["Fe"]
    st = M.state_point(h, fe["T_C"], fe["P_bar"], fe["Tsep_C"]) if h is not None else None
    sup0 = r["Ru_C_supported"]["cashflow 0% r 0.9555"]
    sup12 = r["Ru_C_supported"]["cashflow 12% r 0.9555"]
    return dict(
        OPT_FE=dict(P_bar=fe["P_bar"], T_C=fe["T_C"], Tsep_C=fe["Tsep_C"], cost=fe["cost"], Fe_bed_m3=fe["V_m3"],
                    Fe_bed_m3_per_tpd=fe["V_m3"] / 1000.0, outlet_NH3_molpct=st["outlet_NH3_molpct"] if st else None,
                    inlet_NH3_molpct=st["inlet_NH3_molpct"] if st else None,
                    GHSV_h=st["inlet_Nm3_h"] / fe["V_m3"] if st else None),
        OPT_RUC_0PCT=dict(P_bar=sup0["Ru_C_global"]["P_bar"], T_C=sup0["Ru_C_global"]["T_C"],
                          RuC_minus_Fe_global=sup0["Ru_minus_Fe_global"]),
        OPT_RUC_12PCT=dict(P_bar=sup12["Ru_C_global"]["P_bar"], RuC_minus_Fe_global=sup12["Ru_minus_Fe_global"]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=6)
    args = ap.parse_args()
    workers = max(1, min(8, args.workers))
    t0 = time.time()

    # (1) anchors first
    h = M.build_frozen()
    anchors = M.reproduce_anchors(h)
    print(f"anchors: frozen Fe {anchors['frozen_Fe']['cost']:.6f}, Ru {anchors['frozen_Ru']['cost']:.6f}; "
          f"measured Fe {anchors['measured']['Fe']['cost']:.6f} at {anchors['measured']['Fe']['T_C']:.0f} C / "
          f"{anchors['measured']['Fe']['P_bar']:.0f} bar / {anchors['measured']['Fe']['Tsep_C']:.0f} C", flush=True)

    cases = {c["case_id"]: c for c in rows("benchmark_cases.csv")}
    metrics = rows("benchmark_metrics.csv")
    windows = {}
    for w in rows("industrial_windows.csv"):
        windows[w["window_id"]] = dict(low=float(w["window_low"]), high=float(w["window_high"]))

    # (2) converter optimisations in parallel
    design = [dict(case_id=k, P_bar=float(c["P_bar"]), Tsep_C=float(c["Tsep_C"]), inerts=float(c["inerts"]),
                   pattern=c["pattern"]) for k, c in cases.items() if c["level"] == "converter_design"]
    minvol = [dict(case_id=k, P_bar=float(c["P_bar"]), inlet_Nm3_h=float(c["inlet_Nm3_h"]), yNH3=float(c["yNH3"]),
                   y_out=float(c["y_out"]), inerts=float(c["inerts"]), n_beds=c["n_beds"])
              for k, c in cases.items() if c["level"] == "converter_min_volume"]
    with mp.get_context("spawn").Pool(min(workers, len(design) + len(minvol))) as pool:
        ad = pool.map_async(design_job, design)
        am = pool.map_async(minvol_job, minvol)
        model = {}
        # (3a) state cases (main process, meanwhile)
        for k, c in cases.items():
            if c["level"] == "state":
                model[k] = state_values(h, c)
            elif c["level"] in ("converter_forward", "converter_inverse"):
                beds = json.loads(c["beds"])
                kw = dict(yN2=float(c["yN2"]), yH2=float(c["yH2"]))
                f = CS.forward if c["level"] == "converter_forward" else CS.inverse
                out = f(float(c["P_bar"]), float(c["inlet_Nm3_h"]), float(c["yNH3"]), float(c["inerts"]), beds, **kw)
                d = dict(beds=out, outlet_NH3_molpct=out[-1]["y_NH3_out_molpct"])
                for i, b in enumerate(out, 1):
                    d[f"bed{i}_T_out_C"] = b["T_out_C"]
                if c["level"] == "converter_inverse":
                    d["V_total_m3"] = sum(b["V_model_m3"] for b in out)
                else:
                    d["sensitivity_Fe_effectiveness_0p5"] = f(float(c["P_bar"]), float(c["inlet_Nm3_h"]), float(c["yNH3"]),
                                                              float(c["inerts"]), beds, fe_activity=0.5, **kw)
                model[k] = d
        print("state and converter forward/inverse cases done", flush=True)
        for r in ad.get():
            model[r["case_id"]] = r
            print(f"design {r['case_id']}: outlet {r['outlet_NH3_molpct']:.2f} %, bed-1 inlet {r['bed1_T_in_C']:.0f} C, "
                  f"V {r['V_m3_per_tpd']:.4f} m3/(t/d), Fe share {r['Fe_volume_fraction']:.2f} ({r['seconds']:.0f} s)", flush=True)
        for r in am.get():
            model[r["case_id"]] = r
            print(f"min volume {r['case_id']}: {r['V_total_m3']:.2f} m3 ({r['seconds']:.0f} s)", flush=True)
    model["TOP220_MINVOL/TOP140_MINVOL"] = dict(volume_ratio_220_140=model["TOP220_MINVOL"]["V_total_m3"]
                                                / model["TOP140_MINVOL"]["V_total_m3"])

    # (3b) optimum and staged
    opt = optimum_values(h, anchors["measured"])
    model.update(opt)
    st = staged_checks()
    model["STAGED_ALL"] = dict(Ru_upstream_of_Fe_in_any_optimum=st["Ru_upstream_of_Fe_in_any_optimum"])
    model["STAGED_90BAR"] = dict(Ru_in_optimum_at_12pct=st["Ru_in_optimum_at_12pct"])
    model["STAGED_PRESSURE"] = dict(spearman_P_vs_Ru_financing_boundary=st["spearman_P_vs_Ru_financing_boundary"])
    med, ull = ullmann_ratio(h)
    model["ULLMANN_T5"] = dict(median_ratio_model_to_table=med)

    # (4) PR #77 column
    h77 = M.build_pr77()
    pr77 = {}
    if h77 is not None:
        print(f"PR #77 harness: {h77.NSTATE} states (commit {h77._pr77_commit[:8]})", flush=True)
        for k, c in cases.items():
            if c["level"] == "state":
                pr77[k] = state_values(h77, c, pr77=True)
        with M._GBGibbs():
            r77 = M.optimum(h77)
        o77 = optimum_values(None, r77)
        fe77 = r77["Fe"]
        st77 = M.state_point_pr77(h77, fe77["T_C"], fe77["P_bar"], fe77["Tsep_C"])
        if st77:
            o77["OPT_FE"].update(outlet_NH3_molpct=st77["outlet_NH3_molpct"], inlet_NH3_molpct=st77["inlet_NH3_molpct"],
                                 GHSV_h=st77["inlet_Nm3_h"] / fe77["V_m3"])
        pr77.update(o77)
        pr77["_optimum_raw"] = {k: r77[k] for k in ("Fe", "Ru_benchmark", "Ru_activity_multiple_for_parity")}

    # uncounted diagnostic: Gillespie-Beattie ideal-gas loop equilibrium (PR #64), same harness otherwise
    gbi = {k: state_values(h, c, gb=True) for k, c in cases.items() if c["level"] == "state"}

    # judge
    out_rows, n_pass = [], 0
    for m in metrics:
        cid, q = m["case_id"], m["quantity"]
        val = model.get(cid, {}).get(q) if model.get(cid) else None
        ok, dev = judge(m["rule"], val, fnum(m["industrial_value"]), fnum(m["industrial_low"]), fnum(m["industrial_high"]), windows)
        v77, ok77 = None, None
        if cid in pr77 and pr77[cid] is not None and q in pr77[cid]:
            v77 = pr77[cid][q]
            ok77, _ = judge(m["rule"], v77, fnum(m["industrial_value"]), fnum(m["industrial_low"]), fnum(m["industrial_high"]), windows)
        vg, okg = None, None
        if cid in gbi and gbi[cid] is not None and q in gbi[cid]:
            vg = gbi[cid][q]
            okg, _ = judge(m["rule"], vg, fnum(m["industrial_value"]), fnum(m["industrial_low"]), fnum(m["industrial_high"]), windows)
        n_pass += ok
        out_rows.append(dict(metric_id=m["metric_id"], table=m["table"], case_id=cid, quantity=q,
                             model=val if not isinstance(val, float) else round(val, 6),
                             industrial=m["industrial_value"] or (f"{m['industrial_low']}-{m['industrial_high']}" if m["industrial_low"]
                                                                   else m["rule"]),
                             unit=m["unit"], rule=m["rule"], deviation=dev, pass_=("pass" if ok else "FAIL"),
                             pr77_model=v77 if not isinstance(v77, float) else round(v77, 6),
                             pr77_pass=("" if ok77 is None else ("pass" if ok77 else "FAIL")),
                             gb_ideal_model=vg if not isinstance(vg, float) else round(vg, 6),
                             gb_ideal_pass=("" if okg is None else ("pass" if okg else "FAIL")), ref_rows=m["ref_rows"]))
    with (HERE / "results_metrics.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(out_rows[0]))
        w.writeheader()
        w.writerows(out_rows)

    # uncounted sensitivities: T_REF +- 25 C on the state cases that use it; Fe effectiveness 0.5 (forward)
    sens = []
    for m in metrics:
        c = cases.get(m["case_id"])
        if not c or c["level"] != "state" or c["T_basis"].split()[0] != "T_REF":
            continue
        for dT in (-T_SHIFT, T_SHIFT):
            d = state_values(h, c, T=float(c["T_C"]) + dT)
            val = d.get(m["quantity"]) if d else None
            ok, dev = judge(m["rule"], val, fnum(m["industrial_value"]), fnum(m["industrial_low"]), fnum(m["industrial_high"]), windows)
            sens.append(dict(sensitivity=f"T_REF {dT:+.0f} C", metric_id=m["metric_id"], case_id=m["case_id"],
                             quantity=m["quantity"], model=val, deviation=dev, pass_=("pass" if ok else "FAIL")))
    for k in ("LIU919A_FWD", "LIU919B_FWD"):
        b = model[k]["sensitivity_Fe_effectiveness_0p5"]
        for i, bb in enumerate(b, 1):
            sens.append(dict(sensitivity="Fe effectiveness 0.5", metric_id="", case_id=k, quantity=f"bed{i}_T_out_C",
                             model=bb["T_out_C"], deviation="", pass_=""))
        sens.append(dict(sensitivity="Fe effectiveness 0.5", metric_id="", case_id=k, quantity="outlet_NH3_molpct",
                         model=b[-1]["y_NH3_out_molpct"], deviation="", pass_=""))
    with (HERE / "results_sensitivity.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(sens[0]))
        w.writeheader()
        w.writerows(sens)

    by_table = {}
    for r in out_rows:
        t = by_table.setdefault(r["table"], [0, 0])
        t[0] += r["pass_"] == "pass"
        t[1] += 1
    summary = dict(
        anchors=dict(frozen_Fe=anchors["frozen_Fe"]["cost"], frozen_Ru=anchors["frozen_Ru"]["cost"],
                     measured_Fe=anchors["measured"]["Fe"]),
        n_metrics=len(out_rows), n_pass=n_pass, by_table={k: f"{a}/{b}" for k, (a, b) in by_table.items()},
        failures=[r["metric_id"] for r in out_rows if r["pass_"] != "pass"],
        pr77=dict(commit=getattr(h77, "_pr77_commit", None), n_applicable=sum(r["pr77_pass"] != "" for r in out_rows),
                  n_pass=sum(r["pr77_pass"] == "pass" for r in out_rows)) if h77 is not None else None,
        gb_ideal_diagnostic=dict(n_applicable=sum(r["gb_ideal_pass"] != "" for r in out_rows),
                                 n_pass=sum(r["gb_ideal_pass"] == "pass" for r in out_rows)),
        staged=st, ullmann_table5=dict(median_ratio=med, n=len(ull), min_ratio=min(o["ratio"] for o in ull),
                                       max_ratio=max(o["ratio"] for o in ull)),
        sensitivity_pass={s: f"{sum(r['pass_'] == 'pass' for r in sens if r['sensitivity'] == s)}/"
                             f"{sum(1 for r in sens if r['sensitivity'] == s)}"
                          for s in sorted({r["sensitivity"] for r in sens if r["pass_"]})},
        seconds=time.time() - t0)
    (HERE / "results_cases.json").write_text(json.dumps(_clean(dict(model=model, pr77=pr77, gb_ideal=gbi, ullmann=ull)), indent=1) + "\n",
                                             encoding="utf-8")
    (HERE / "summary.json").write_text(json.dumps(_clean(summary), indent=1) + "\n", encoding="utf-8")
    print(f"\n{n_pass}/{len(out_rows)} pre-registered comparisons pass; by table {summary['by_table']}")
    if summary["pr77"]:
        print(f"PR #77 column: {summary['pr77']['n_pass']}/{summary['pr77']['n_applicable']} applicable")
    for r in out_rows:
        print(f"{r['metric_id']:4s} {r['case_id']:28s} {r['quantity']:36s} model {str(r['model']):>12.12s}  "
              f"ind {r['industrial']:>16.16s}  {r['deviation']:>22.22s}  {r['pass_']}  | PR77 {str(r['pr77_model'])[:10]} {r['pr77_pass']}")


def _clean(o):
    if isinstance(o, (float, np.floating)):
        return round(float(o), 6) if math.isfinite(o) else None
    if isinstance(o, (bool, np.bool_)):
        return bool(o)
    if isinstance(o, dict):
        return {str(k): _clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_clean(v) for v in o]
    if isinstance(o, np.integer):
        return int(o)
    return o


if __name__ == "__main__":
    main()
