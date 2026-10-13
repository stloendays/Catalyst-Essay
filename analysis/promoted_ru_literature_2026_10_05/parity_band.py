"""Ru activity parity band for the Fig. 3a literature strip, for the selected NH3 model.

The literature points in fig3_literature_points.csv are measured activity gains and do not depend on the model. What
depends on it is the band they are read against:

  * baseline alpha*: the direct Ru activity multiplier at which Ru, reoptimized over the full process library and the
    90 m3 bed cap, reaches the Fe cost (harness backward_and_reachability definition; results.json of the run);
  * 5,000-draw economic band: the preregistered cost-side Monte Carlo (docs/SUPERVISOR_COST_MC_PREREG_2026-09-20.md;
    draw construction as in analysis/nonfigure_upgrades_2026_09_29/reproduce_nh3_cost_mc.py, seed 20260920): per draw
    Fe and Ru are reoptimized with sampled metal prices, CAPEX multiplier, electricity price and catalyst life, and
    alpha* is recomputed against that draw's Fe cost with Ru reoptimized at every alpha.

Under NH3_MODEL=1.1 the script must reproduce the frozen 1.1 values (alpha* 201.22, p05-p95 70.78-462.00 from
analysis/supervisor_2026_09_20/nh3_cost_mc_summary.json); the gate below fails otherwise. Under 1.2 the same
definitions are evaluated on the NH3-FINAL-1.2 process library and calibration.

    NH3_MODEL=1.1 python parity_band.py      # writes parity_band.json, literature_vs_parity.csv, alpha_star_draws.csv here
    NH3_MODEL=1.2 python parity_band.py      # writes the same files to nh3_1_2/ (+ an unchanged copy of the literature CSV)

Read-only on the harness roots: only the two descriptor grid points bracketing E_N(Fe) and E_N(Ru) are evaluated
(frozen_state_logtof); no response surface is built or loaded.
"""
from __future__ import annotations

import csv
import json
import math
import shutil
import sys
import time
from pathlib import Path

import numpy as np
from scipy.optimize import brentq

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "analysis"))
import nh3_model as NM  # noqa: E402

OUT = NM.out_dir(HERE)
A = NM.anchors()
hc = NM.core()
t0 = time.time()
h = NM.harness()
assert h.NSTATE == A["NSTATE"], (h.NSTATE, A["NSTATE"])
print(f"{NM.LABEL}: {h.NSTATE} process states ({time.time() - t0:.0f} s)", flush=True)

fe_vec = h.frozen_state_logtof(h.EN0["Fe"])
ru_vec = h.frozen_state_logtof(h.EN0["Ru"])
print(f"state logTOF vectors ({time.time() - t0:.0f} s)", flush=True)


def evaluate(metal, vec, *, price, life_y, capex_multiplier, electricity, alpha=1.0):
    """Feasible minimum cost with the preregistered cost-MC scalings (reproduce_nh3_cost_mc.py formula)."""
    _, V, metal_cost, reactor = h.cost_arrays(metal, vec, price=price, life_y=life_y, alpha=alpha)
    opex = (h.state_fresh + h.state_reccomp + h.state_refrig) * (float(electricity) / h.ELECTRICITY)
    total = metal_cost + capex_multiplier * (reactor + h.state_compcapex) + opex
    ok = V <= h.V_CAP
    if not np.any(ok):
        return math.inf, -1
    i = int(np.argmin(np.where(ok, total, np.inf)))
    return float(total[i]), i


# ---- baseline: regression gate against the run's results.json ------------------------------------------------------
fe0 = h.eval_scenario("Fe", fe_vec)
ru0 = h.eval_scenario("Ru", ru_vec)
assert abs(fe0["total_cost"] - A["Fe"]) < 1e-10, (fe0["total_cost"], A["Fe"])
assert abs(ru0["total_cost"] - A["Ru"]) < 1e-10, (ru0["total_cost"], A["Ru"])
assert (fe0["T_C"], fe0["P_bar"], fe0["Tsep_C"]) == tuple(A["Fe_optimum"])
assert (ru0["T_C"], ru0["P_bar"], ru0["Tsep_C"]) == tuple(A["Ru_optimum"])


def alpha_star_base():
    FE = fe0["total_cost"]

    def gap(loga):
        try:
            return h.eval_scenario("Ru", ru_vec, alpha=10.0 ** loga)["total_cost"] - FE
        except RuntimeError:
            return 1e100
    return 10.0 ** brentq(gap, -6.0, 12.0, xtol=1e-11)


a_base = alpha_star_base()
assert abs(a_base / A["alpha"] - 1.0) < 1e-9, (a_base, A["alpha"])
ru_at_base = h.eval_scenario("Ru", ru_vec, alpha=a_base)
print(f"baseline alpha* = {a_base:.6f} (results.json {A['alpha']:.6f})", flush=True)

# ---- preregistered 5,000-draw cost Monte Carlo ----------------------------------------------------------------------
N = 5000
rng = np.random.default_rng(20260920)
fe_pm = np.exp(rng.uniform(math.log(0.5), math.log(2.0), N))
ru_pm = np.exp(rng.uniform(math.log(0.5), math.log(2.0), N))
cap = rng.uniform(0.8, 1.2, N)
elec = rng.uniform(20.0, 100.0, N)
life = rng.uniform(5.0, 20.0, N)

draws = []
for d in range(N):
    kw = dict(life_y=float(life[d]), capex_multiplier=float(cap[d]), electricity=float(elec[d]))
    fe, fi = evaluate("Fe", fe_vec, price=hc.PRICE["Fe"] * float(fe_pm[d]), **kw)
    p_ru = hc.PRICE["Ru"] * float(ru_pm[d])
    ru1, _ = evaluate("Ru", ru_vec, price=p_ru, **kw)

    def gap(loga):
        c, _ = evaluate("Ru", ru_vec, price=p_ru, alpha=10.0 ** loga, **kw)
        return (c - fe) if math.isfinite(c) else 1e100
    a = 10.0 ** brentq(gap, -6.0, 12.0, xtol=1e-11)
    _, ri = evaluate("Ru", ru_vec, price=p_ru, alpha=a, **kw)
    draws.append(dict(draw=d, Fe_price_multiplier=float(fe_pm[d]), Ru_price_multiplier=float(ru_pm[d]),
                      capex_multiplier=float(cap[d]), electricity_USD_MWh=float(elec[d]), catalyst_life_y=float(life[d]),
                      Fe_cost_USD_t=fe, Ru_cost_alpha1_USD_t=ru1, alpha_star=a,
                      Fe_P_bar=float(h.state_P[fi]), Ru_P_bar_at_alpha_star=float(h.state_P[ri])))
    if (d + 1) % 500 == 0:
        print(f"  draws {d + 1}/{N} ({time.time() - t0:.0f} s)", flush=True)

al = np.array([r["alpha_star"] for r in draws])
fe_c = np.array([r["Fe_cost_USD_t"] for r in draws])
ru_c = np.array([r["Ru_cost_alpha1_USD_t"] for r in draws])
QS = {"p05": 0.05, "p10": 0.10, "p25": 0.25, "p50": 0.50, "p75": 0.75, "p90": 0.90, "p95": 0.95}
aq = {k: float(np.quantile(al, q)) for k, q in QS.items()}
aq.update(mean=float(np.mean(al)), min=float(np.min(al)), max=float(np.max(al)))

# 1.1 gate: the frozen supervisor summary must be reproduced before anything is written
if NM.VERSION == "1.1":
    ref = json.loads((REPO / "analysis/supervisor_2026_09_20/nh3_cost_mc_summary.json").read_text(encoding="utf-8"))
    for k in ("p05", "p10", "p25", "p50", "p75", "p90", "p95", "mean", "min", "max"):
        assert abs(aq[k] / ref["alpha_star"][k] - 1.0) < 1e-8, (k, aq[k], ref["alpha_star"][k])
    for q, k in ((0.05, "p05"), (0.50, "p50"), (0.95, "p95")):
        assert abs(float(np.quantile(fe_c, q)) - ref["Fe_cost_USD_t_quantiles"][k]) < 1e-10
        assert abs(float(np.quantile(ru_c, q)) - ref["Ru_cost_USD_t_quantiles"][k]) < 1e-10
    assert float(np.mean(ru_c <= fe_c)) == ref["P_Ru_le_Fe_at_alpha_1"]
    print("PASS 1.1 gate: alpha* quantiles, Fe/Ru cost quantiles and P(Ru<=Fe at alpha=1) reproduce "
          "supervisor_2026_09_20/nh3_cost_mc_summary.json", flush=True)

summary = {
    "schema": "promoted-ru-parity-band-v1",
    "model": NM.LABEL,
    "run": NM.RUNS[NM.VERSION],
    "process_states": h.NSTATE,
    "F_CAL": h.F_CAL,
    "baseline": {
        "Fe_cost_USD_t": fe0["total_cost"], "Fe_optimum": [fe0["T_C"], fe0["P_bar"], fe0["Tsep_C"]],
        "Ru_cost_USD_t": ru0["total_cost"], "Ru_optimum": [ru0["T_C"], ru0["P_bar"], ru0["Tsep_C"]],
        "alpha_star": a_base,
        "Ru_optimum_at_alpha_star": [ru_at_base["T_C"], ru_at_base["P_bar"], ru_at_base["Tsep_C"]],
    },
    "cost_mc": {
        "draws": N, "seed": 20260920, "preregistration": "docs/SUPERVISOR_COST_MC_PREREG_2026-09-20.md",
        "alpha_star": aq,
        "Fe_cost_USD_t_quantiles": {k: float(np.quantile(fe_c, QS[k])) for k in ("p05", "p50", "p95")},
        "Ru_cost_alpha1_USD_t_quantiles": {k: float(np.quantile(ru_c, QS[k])) for k in ("p05", "p50", "p95")},
        "P_Ru_le_Fe_at_alpha_1": float(np.mean(ru_c <= fe_c)),
    },
}
if NM.VERSION == "1.1":
    summary["gate_1_1"] = "PASS against analysis/supervisor_2026_09_20/nh3_cost_mc_summary.json (rel. 1e-8)"

# ---- literature points against the band -----------------------------------------------------------------------------
P05, P50, P95 = aq["p05"], aq["p50"], aq["p95"]


def position(f):
    if f < P05:
        return "below band"
    if f > P95:
        return "above band"
    return "in band"


lit = list(csv.DictReader((HERE / "fig3_literature_points.csv").open(encoding="utf-8")))
rows = []
for r in lit:
    lo, hi = float(r["factor_low"]), float(r["factor_high"])
    rows.append(dict(
        id=r["id"], row=r["row"], label=r["label"], factor_low=r["factor_low"], factor_high=r["factor_high"],
        lower_bound=r["lower_bound"], reference=r["reference"],
        position_vs_band=position(hi),
        reaches_alpha_star=int(hi >= a_base),
        factor_high_over_alpha_star=hi / a_base,
        share_of_draws_with_alpha_star_le_factor=float(np.mean(al <= hi)),
    ))
summary["band"] = {"p05": P05, "p50": P50, "p95": P95, "alpha_star": a_base}
summary["literature"] = {r["id"]: {k: r[k] for k in ("label", "factor_high", "position_vs_band", "reaches_alpha_star",
                                                       "share_of_draws_with_alpha_star_le_factor")} for r in rows}

with (OUT / "literature_vs_parity.csv").open("w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
with (OUT / "alpha_star_draws.csv").open("w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(draws[0]), lineterminator="\n")
    w.writeheader()
    w.writerows(draws)
(OUT / "parity_band.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
if OUT != HERE:  # the measured gains do not change with the model; the 1.2 folder carries the same file
    shutil.copyfile(HERE / "fig3_literature_points.csv", OUT / "fig3_literature_points.csv")

print(f"alpha* baseline {a_base:.2f}; cost MC p05/p50/p95 = {P05:.2f} / {P50:.2f} / {P95:.2f}")
for r in rows:
    print(f"  {r['id']:4s} {r['label']:28s} {float(r['factor_high']):7.1f}x  {r['position_vs_band']:10s} "
          f"alpha*-reached={r['reaches_alpha_star']}  share={r['share_of_draws_with_alpha_star_le_factor']:.3f}")
print(f"wrote {OUT} ({time.time() - t0:.0f} s)")
