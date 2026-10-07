"""Actual-Ru ammonia analysis with literature-checked Ru loading, bed density and Ru recovery.

A primary-literature check (2026-10-07) found three inputs of the actual-Ru analysis that differ from the literature:

  input                                   used            literature
  Ru loading of the supported Ru/C        3.2 wt%         ~8 wt% (commercial BP/Kellogg catalyst), 5-10 wt% overall
  bed (bulk) density of the Ru/C bed      500-1,000       no published value; ~430-520 derived -> 430-550 kg m-3
  Ru recovery from spent catalyst         0.90-0.94       0.89-0.976 (CN 1872418 A, Ru/C ammonia catalyst)

Each set below changes only those inputs; the dispersion ratio u (11 in the Fig. 3d reading, log-uniform 11-50 in the
Monte Carlo) and everything else stay as in the baseline.

  baseline  r 0.90-0.94, rho 500-1,000, w 3.2 wt%
  R1        r 0.90-0.97
  R2        rho 430-550
  R3        w 8 wt% (also 5 and 10 wt%); in the Monte Carlo the extra variant A_comm draws w uniform 5-10 wt%
  R_all     R1 + R2 + R3

Readings (same code as figures/composite/fig2/fig2_ru_actual_cost.py):
  * Fig. 3d own-bed reading, main loop and KAAP loop (90 bar, Tsep -20 C): the Ru/C catalyst carries m_Ru / u of Ru at
    w in a bed of density rho, i.e. the benchmark bed volume times 1,787.75 / (u w rho); range over the corners of the
    set, gap to the Fe reference of the same loop, and the Ru activity multiple alpha* needed for parity.
  * Benchmark-bed reading: p_eff = p_Ru (1 - r) / u against the parity price of the Fig. 2d sweep (163.76 USD/kg).
  * Monte Carlo (5,000 draws; seeds 20260920 and 20261006 as in analysis/nh3_mc_ru_actual_2026_10_06; A_comm's Ru
    content from a third generator, seed 20261007). The uniforms are drawn once and rescaled to each set's range, so
    every set sees the same draws (common random numbers); with the baseline ranges the draws are bit-identical to
    run_mc_ru_actual.py, which is checked against its committed summary.json.

Needs a harness root with the cached response columns (build_harness_root.py); the response surface is not rebuilt.

    NH3_HARNESS=<root> python run_params.py   -> summary.json, fig3d_readings.csv, mc_variants.csv, results_table.md
"""
import csv
import json
import math
import os
import platform
import sys
from pathlib import Path

import numpy as np
import yaml
from scipy.optimize import brentq
from scipy.stats import beta as beta_dist

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
HARNESS = Path(os.environ.get("NH3_HARNESS", r"D:/论文-AI4S/Catalyst_Economic_Leverage_Automation_Harness_v0.1"))
sys.path.insert(0, str(HARNESS))
import harness_core as hc  # noqa: E402

sys.path.insert(0, str(REPO / "agent"))
from selfcheck_gate import require  # noqa: E402

RUN = HARNESS / "outputs" / "nh3_final_20260905T134204Z"
FIG2 = REPO / "figures" / "composite" / "fig2"
MC_BASE = REPO / "analysis" / "nh3_mc_ru_actual_2026_10_06" / "summary.json"
SUPPORTED = REPO / "analysis" / "nh3_supported_2026_10_06" / "supported_candidates.csv"

FE_COST = 15.291704676621144
RU_COST = 22.03059478781101
U_MIN = 0.11 / 0.01
KAAP_P, KAAP_TSEP = 90.0, -20.0
N = 5000
U_RANGE = (11.0, 50.0)
W_COMM = (0.05, 0.10)

SETS = {  # recovery corners, bed-density corners, Ru mass fractions for the Fig. 3d reading; headline w
    "baseline": dict(r=(0.90, 0.94), rho=(500.0, 1000.0), w=(0.032,), w_head=0.032),
    "R1": dict(r=(0.90, 0.97), rho=(500.0, 1000.0), w=(0.032,), w_head=0.032),
    "R2": dict(r=(0.90, 0.94), rho=(430.0, 550.0), w=(0.032,), w_head=0.032),
    "R3": dict(r=(0.90, 0.94), rho=(500.0, 1000.0), w=(0.05, 0.08, 0.10), w_head=0.08),
    "R_all": dict(r=(0.90, 0.97), rho=(430.0, 550.0), w=(0.05, 0.08, 0.10), w_head=0.08),
}


def main():
    require()
    h = hc.NH3Harness(yaml.safe_load((RUN / "manifest_resolved.yaml").read_text(encoding="utf-8")), HARNESS)
    assert h.NSTATE == 14136
    response, _cp, cached = h.build_or_load_response()
    if not cached:
        raise SystemExit("response surface is not cached; refusing to rebuild a frozen asset")

    def vector(x):
        v = h.interp_state_vector(response, x)
        assert np.isfinite(v).all(), f"response column missing at descriptor {x}"
        return v

    vec = {m: vector(hc.EN0_CANON[m]) for m in ("Fe", "Ru")}
    P_RU = hc.PRICE["Ru"]
    bench_metal_per_m3 = h.ACTIVE_FRACTION * h.BED_DENSITY

    # ---------------------------------------------------------------- Fig. 3d readings
    def reactor_cost(V):
        return ((h.REACTOR_FIXED + h.REACTOR_VAR * np.power(V / h.REACTOR_REF, h.REACTOR_EXP)) * h.crf
                / h.annual_output_t + h.vessel_pressure_premium(V))

    def optimum(price, alpha=1.0, bed_factor=1.0, mask=None):
        total, V, metal_cost, _ = h.cost_arrays("Ru", vec["Ru"], price=price, alpha=alpha)
        if bed_factor != 1.0:
            V = V * bed_factor
            total = metal_cost + reactor_cost(V) + h.state_process_cost
        ok = V <= h.V_CAP
        if mask is not None:
            ok &= mask
        i = int(np.argmin(np.where(ok, total, np.inf)))
        return dict(cost=float(total[i]), T_C=float(h.state_T[i]), P_bar=float(h.state_P[i]),
                    Tsep_C=float(h.state_Tsep[i]), V_m3=float(V[i]))

    def alpha_star(price, mask=None, bed_factor=1.0, target=FE_COST):
        if optimum(price, 1e12, bed_factor=bed_factor, mask=mask)["cost"] > target:
            return math.inf
        return 10.0 ** brentq(lambda la: optimum(price, 10.0 ** la, bed_factor=bed_factor, mask=mask)["cost"] - target,
                              -6.0, 12.0, xtol=1e-11)

    t_fe, V_fe, _, _ = h.cost_arrays("Fe", vec["Fe"])
    assert abs(float(np.min(np.where(V_fe <= h.V_CAP, t_fe, np.inf))) - FE_COST) < 1e-9
    assert abs(optimum(P_RU)["cost"] - RU_COST) < 1e-9
    kaap = (h.state_P == KAAP_P) & (h.state_Tsep == KAAP_TSEP)
    i_fe = int(np.argmin(np.where((V_fe <= h.V_CAP) & kaap, t_fe, np.inf)))
    fe_kaap = float(t_fe[i_fe])
    loops = {"main": (None, FE_COST), "KAAP": (kaap, fe_kaap)}
    p_parity = float(list(csv.DictReader(open(FIG2 / "fig2_ru_price_sweep.csv", encoding="utf-8")))[-1]["price_USD_kg"])

    readings = []
    for s, cfg in SETS.items():
        for loop, (mask, ref) in loops.items():
            for w in cfg["w"]:
                for r in cfg["r"]:
                    for rho in cfg["rho"]:
                        pe = P_RU * (1.0 - r) / U_MIN
                        k = bench_metal_per_m3 / (U_MIN * w * rho)
                        o = optimum(pe, bed_factor=k, mask=mask)
                        readings.append(dict(set=s, loop=loop, reading="own_bed", w_Ru=w, recovery=r, rho_bed_kg_m3=rho,
                                             p_eff_USD_kg=pe, bed_factor=k, cost=o["cost"], Fe_reference_cost=ref,
                                             gap_to_Fe=o["cost"] - ref, alpha_star=alpha_star(pe, mask, k, ref),
                                             T_C=o["T_C"], P_bar=o["P_bar"], Tsep_C=o["Tsep_C"], V_m3=o["V_m3"]))
    # benchmark-bed reading: bed keeps the benchmark formulation, so only r (and u) enter
    for r in (0.90, 0.94, 0.97):
        pe = P_RU * (1.0 - r) / U_MIN
        for loop, (mask, ref) in loops.items():
            o = optimum(pe, mask=mask)
            readings.append(dict(set="benchmark_bed", loop=loop, reading="benchmark_bed", w_Ru=math.nan, recovery=r,
                                 rho_bed_kg_m3=math.nan, p_eff_USD_kg=pe, bed_factor=1.0, cost=o["cost"],
                                 Fe_reference_cost=ref, gap_to_Fe=o["cost"] - ref,
                                 alpha_star=alpha_star(pe, mask, 1.0, ref), T_C=o["T_C"], P_bar=o["P_bar"],
                                 Tsep_C=o["Tsep_C"], V_m3=o["V_m3"]))

    # baseline own-bed reading reproduces the committed Fig. 3d series
    committed = list(csv.DictReader(open(FIG2 / "fig2_ru_bed_sensitivity.csv", encoding="utf-8")))
    key_of = {("main", 0.90): "supp_rec90", ("main", 0.94): "supp_rec94", ("KAAP", 0.90): "kaap90", ("KAAP", 0.94): "kaap94"}
    n_cmp = 0
    for x in readings:
        if x["set"] == "baseline":
            c = next(c for c in committed if c["key"] == key_of[(x["loop"], x["recovery"])]
                     and float(c["rho_bed_kg_m3"]) == x["rho_bed_kg_m3"])
            assert abs(float(c["cost"]) - x["cost"]) < 1e-9, (c, x)
            assert abs(float(c["alpha_star_supported_bed"]) - x["alpha_star"]) < 1e-6 * x["alpha_star"], (c, x)
            n_cmp += 1
    assert n_cmp == 8

    def span(rows):
        c = [x["cost"] for x in rows]
        g = [x["gap_to_Fe"] for x in rows]
        a = [x["alpha_star"] for x in rows]
        return dict(cost=[min(c), max(c)], gap_to_Fe=[min(g), max(g)], alpha_star=[min(a), max(a)],
                    Fe_reference=rows[0]["Fe_reference_cost"], corners=len(rows))

    fig3d = {}
    for s, cfg in SETS.items():
        fig3d[s] = {}
        for loop in loops:
            rows = [x for x in readings if x["set"] == s and x["loop"] == loop]
            fig3d[s][loop] = {"headline_w": cfg["w_head"],
                              "at_headline_w": span([x for x in rows if x["w_Ru"] == cfg["w_head"]])}
            if len(cfg["w"]) > 1:
                fig3d[s][loop]["by_w"] = {f"{w * 100:g}wt%": span([x for x in rows if x["w_Ru"] == w]) for w in cfg["w"]}
                fig3d[s][loop]["envelope_all_w"] = span(rows)
    bench = {f"r{r:.2f}": {loop: {k: x[k] for k in ("p_eff_USD_kg", "cost", "gap_to_Fe", "alpha_star")}
                           for loop in loops for x in readings
                           if x["set"] == "benchmark_bed" and x["loop"] == loop and x["recovery"] == r}
             for r in (0.90, 0.94, 0.97)}
    bench["parity_price_USD_kg"] = p_parity

    # ---------------------------------------------------------------- Monte Carlo
    def evaluate(metal, v, *, price, life_y, cap, elec, alpha=1.0, recovery=None, w=None, bed=None):
        af, bd = h.ACTIVE_FRACTION, h.BED_DENSITY
        if w is not None:
            h.ACTIVE_FRACTION, h.BED_DENSITY = w, bed
        try:
            _, V, metal_cost, reactor = h.cost_arrays(metal, v, price=price, life_y=life_y, recovery=recovery, alpha=alpha)
        finally:
            h.ACTIVE_FRACTION, h.BED_DENSITY = af, bd
        opex = (h.state_fresh + h.state_reccomp + h.state_refrig) * (elec / h.ELECTRICITY)
        total = metal_cost + cap * (reactor + h.state_compcapex) + opex
        ok = V <= h.V_CAP
        if not ok.any():
            return math.inf
        return float(np.min(np.where(ok, total, np.inf)))

    rng = np.random.default_rng(20260920)  # preregistered columns, preregistered order
    fe_pm = np.exp(rng.uniform(math.log(0.5), math.log(2.0), N))
    ru_pm = np.exp(rng.uniform(math.log(0.5), math.log(2.0), N))
    cap = rng.uniform(0.8, 1.2, N)
    elec = rng.uniform(20.0, 100.0, N)
    life = rng.uniform(5.0, 20.0, N)
    rng2 = np.random.default_rng(20261006)  # u, r, bed, measured catalyst: same stream as run_mc_ru_actual.py
    U_u, U_r, U_bed = rng2.random(N), rng2.random(N), rng2.random(N)
    lo, hi = math.log(U_RANGE[0]), math.log(U_RANGE[1])
    u = np.exp(lo + (hi - lo) * U_u)
    meas = [x for x in csv.DictReader(SUPPORTED.open(encoding="utf-8"))
            if x["status"].startswith("primary") and x["active_metals"] == "Ru" and x["cost_USD_t"] != ""]
    kk = rng2.integers(0, len(meas), N)
    U_w = np.random.default_rng(20261007).random(N)
    w_comm = W_COMM[0] + (W_COMM[1] - W_COMM[0]) * U_w
    mvec = [vector(float(x["E_eff_eV"])) for x in meas]
    m_ares = [10.0 ** float(x["log10_alpha_res"]) for x in meas]
    m_w = [float(x["metal_wt_pct"]) / 100.0 for x in meas]

    fe = np.empty(N)
    base = np.empty(N)
    for d in range(N):
        kw = dict(life_y=float(life[d]), cap=float(cap[d]), elec=float(elec[d]))
        fe[d] = evaluate("Fe", vec["Fe"], price=hc.PRICE["Fe"] * float(fe_pm[d]), **kw)
        base[d] = evaluate("Ru", vec["Ru"], price=P_RU * float(ru_pm[d]), **kw)

    ref = json.loads(MC_BASE.read_text(encoding="utf-8"))
    assert float(np.mean(base - fe > 0)) == ref["base_reproduced"]["P_Fe_cheaper"] == 1.0
    assert abs(float((base - fe).min()) - ref["base_reproduced"]["min_gap_USD_t"]) < 1e-9

    def ci95(k, n):
        return [float(beta_dist.ppf(0.025, k, n - k + 1)) if k > 0 else 0.0,
                float(beta_dist.ppf(0.975, k + 1, n - k)) if k < n else 1.0]

    mc, mc_rows = {}, []
    for s, cfg in SETS.items():
        r = cfg["r"][0] + (cfg["r"][1] - cfg["r"][0]) * U_r
        bed = cfg["rho"][0] + (cfg["rho"][1] - cfg["rho"][0]) * U_bed
        res = {n_: np.empty(N) for n_ in ("A", "A_bed", "A_comm", "B", "B0")}
        for d in range(N):
            kw = dict(life_y=float(life[d]), cap=float(cap[d]), elec=float(elec[d]))
            p_ru = P_RU * float(ru_pm[d])
            k = kk[d]
            res["A"][d] = evaluate("Ru", vec["Ru"], price=p_ru * (1.0 - float(r[d])) / float(u[d]), recovery=0.0, **kw)
            res["A_bed"][d] = evaluate("Ru", vec["Ru"], price=p_ru, alpha=float(u[d]), recovery=float(r[d]), w=m_w[k],
                                       bed=float(bed[d]), **kw)
            res["A_comm"][d] = evaluate("Ru", vec["Ru"], price=p_ru, alpha=float(u[d]), recovery=float(r[d]),
                                        w=float(w_comm[d]), bed=float(bed[d]), **kw)
            res["B"][d] = evaluate("Ru", mvec[k], price=p_ru, alpha=m_ares[k], recovery=float(r[d]), w=m_w[k],
                                   bed=float(bed[d]), **kw)
            res["B0"][d] = evaluate("Ru", mvec[k], price=p_ru, alpha=m_ares[k], recovery=0.0, w=m_w[k],
                                    bed=float(bed[d]), **kw)
        mc[s] = {"r": list(cfg["r"]), "bed_density_kg_m3": list(cfg["rho"])}
        for name, ru in res.items():
            gap = ru - fe
            kfe = int(np.sum(gap > 0))
            mc[s][name] = {"P_Fe_cheaper": kfe / N, "CI95_Clopper_Pearson": ci95(kfe, N),
                           "gap_quantiles_USD_t": {q: float(np.quantile(gap, p)) for q, p in
                                                   (("p05", .05), ("p50", .5), ("p95", .95))}}
            mc_rows.append(dict(set=s, variant=name, P_Fe_cheaper=kfe / N, CI95_lo=mc[s][name]["CI95_Clopper_Pearson"][0],
                                CI95_hi=mc[s][name]["CI95_Clopper_Pearson"][1],
                                **{"gap_" + q: v for q, v in mc[s][name]["gap_quantiles_USD_t"].items()}))
        if s == "baseline":  # bit-identical draws -> the committed summary must be reproduced exactly
            for name in ("A", "A_bed", "B", "B0"):
                assert mc[s][name]["P_Fe_cheaper"] == ref[name]["P_Fe_cheaper"], (name, mc[s][name], ref[name])
                for q, v in ref[name]["gap_quantiles_USD_t"].items():
                    assert abs(mc[s][name]["gap_quantiles_USD_t"][q] - v) < 1e-9, (name, q)
        print(s, {n_: mc[s][n_]["P_Fe_cheaper"] for n_ in res}, flush=True)

    out = {
        "workflow_run": {k: os.environ.get(k) for k in ("GITHUB_RUN_ID", "GITHUB_SHA", "GITHUB_REPOSITORY")},
        "platform": platform.platform(), "python": platform.python_version(), "numpy": np.__version__,
        "validation": {"selfcheck_gate": "passed (require())",
                       "baseline_fig3d_own_bed_rows_matched_to_committed_csv": n_cmp,
                       "baseline_MC_matches_committed_summary": True,
                       "committed_MC_summary_P": {n_: ref[n_]["P_Fe_cheaper"] for n_ in ("A", "A_bed", "B", "B0")}},
        "fixed": {"u_fig3d": U_MIN, "u_MC_loguniform": U_RANGE, "A_comm_w": W_COMM, "draws": N,
                  "Fe_main_loop": FE_COST, "Fe_KAAP_loop": fe_kaap, "measured_Ru_catalysts": len(meas)},
        "sets": {s: {k: v for k, v in c.items()} for s, c in SETS.items()},
        "fig3d_own_bed": fig3d, "benchmark_bed": bench, "monte_carlo": mc,
    }
    (HERE / "summary.json").write_text(json.dumps(out, indent=1, default=float) + "\n", encoding="utf-8")
    for name, rows in (("fig3d_readings.csv", readings), ("mc_variants.csv", mc_rows)):
        with (HERE / name).open("w", newline="", encoding="utf-8") as f:
            wr = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
            wr.writeheader()
            wr.writerows(rows)
    (HERE / "results_table.md").write_text(table(out), encoding="utf-8")
    print(table(out))


def table(o):
    S = list(SETS)
    f = lambda a: f"{a[0]:.2f}–{a[1]:.2f}"  # noqa: E731
    L = ["| Quantity | " + " | ".join(S) + " |", "|---|" + "---|" * len(S)]
    for loop, label in (("main", "Fig. 3d main loop, Ru/C cost (USD/t)"), ("KAAP", "KAAP loop, Ru/C cost (USD/t)")):
        fe = o["fig3d_own_bed"]["baseline"][loop]["at_headline_w"]["Fe_reference"]
        L.append(f"| {label}, headline w; Fe {fe:.2f} | " +
                 " | ".join(f(o["fig3d_own_bed"][s][loop]["at_headline_w"]["cost"]) for s in S) + " |")
        L.append(f"| gap to Fe ({loop}) | " +
                 " | ".join(f"{o['fig3d_own_bed'][s][loop]['at_headline_w']['gap_to_Fe'][0]:+.2f} to "
                            f"{o['fig3d_own_bed'][s][loop]['at_headline_w']['gap_to_Fe'][1]:+.2f}" for s in S) + " |")
        L.append(f"| alpha* for parity ({loop}) | " +
                 " | ".join(f(o["fig3d_own_bed"][s][loop]["at_headline_w"]["alpha_star"]) for s in S) + " |")
        L.append(f"| {loop}, envelope over 5–10 wt% | " +
                 " | ".join(f(o["fig3d_own_bed"][s][loop]["envelope_all_w"]["cost"])
                            if "envelope_all_w" in o["fig3d_own_bed"][s][loop] else "–" for s in S) + " |")
    for v in ("A", "A_bed", "A_comm", "B", "B0"):
        L.append(f"| P(Fe cheaper), {v} [95% CI] | " +
                 " | ".join(f"{o['monte_carlo'][s][v]['P_Fe_cheaper']:.4f} "
                            f"[{o['monte_carlo'][s][v]['CI95_Clopper_Pearson'][0]:.3f}, "
                            f"{o['monte_carlo'][s][v]['CI95_Clopper_Pearson'][1]:.3f}]" for s in S) + " |")
    b = o["benchmark_bed"]
    L += ["", f"Benchmark-bed reading (independent of w and rho), parity price {b['parity_price_USD_kg']:.2f} USD/kg:", "",
          "| r | p_eff (USD/kg) | main-loop cost (gap to Fe) | KAAP cost (gap to Fe in KAAP) |", "|---|---|---|---|"]
    for r in ("r0.90", "r0.94", "r0.97"):
        L.append(f"| {r[1:]} | {b[r]['main']['p_eff_USD_kg']:.1f} | {b[r]['main']['cost']:.3f} ({b[r]['main']['gap_to_Fe']:+.3f})"
                 f" | {b[r]['KAAP']['cost']:.3f} ({b[r]['KAAP']['gap_to_Fe']:+.3f}) |")
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    main()
