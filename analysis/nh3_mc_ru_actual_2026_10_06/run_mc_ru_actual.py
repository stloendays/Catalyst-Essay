"""NH3 economic Monte Carlo with the actual Ru catalyst: dispersion ratio u and Ru recovery r sampled from their
literature ranges, and a variant that draws the Ru activity from the measured Ru catalysts.

Base: the preregistered 5,000-draw cost Monte Carlo (seed 20260920; Fe and Ru price multipliers log-uniform 0.5-2,
CAPEX multiplier 0.8-1.2, electricity 20-100 USD/MWh, catalyst life 5-20 y; full reoptimization over the 14,136
states; analysis/nonfigure_upgrades_2026_09_29/reproduce_nh3_cost_mc.py). Those five columns are drawn first, exactly as
preregistered, so every draw keeps its values; the new inputs come from a second generator (seed 20261006) and,
for the commercial Ru content of A_bed, a third (seed 20261007).
The base result (P(C_Fe < C_Ru) = 1.000, minimum gap 2.382 USD/t) is reproduced before anything is added.

Variants (Fe is the benchmark fused-iron catalyst in every variant):
  A  Ru/C with recovery, benchmark-formulation reading of Fig. 3d: only the metal price is lowered, to the effective
       price p_Ru (1 - r) / u; the bed keeps the benchmark formulation and the benchmark (undivided) volume, exactly as
       figures/composite/fig2/fig2_ru_actual_cost.py reads the price sweep. (Before 2026-10-07 this variant divided the
       metal mass and the bed volume by u, a different convention from Fig. 3d.)
       u = D_Ru / f_Fe, log-uniform 11-50: D_Ru from 11 % (Ba-Cs-K promoted Ru/C, 3.2 wt% Ru; Rossetti et al. 2006)
       to 50 % (2 nm Ru particles in Ba-Ru/C; Nishi, Chen & Takagi, Catalysts 9, 480, 2019; D ~ 1/d[nm]), f_Fe = 1 % (exposed
       Fe atoms of reduced fused iron < 1 %; Liu et al. 2000). r uniform 0.90-0.97: 89-97.6 % of the Ru recovered
       from spent activated-carbon-supported Ru ammonia catalyst (CN 1872418 A).
  A_bed  as A, with the supported bed: Ru content and bed density of the commercial supported catalyst instead of the
       benchmark 71.51 wt% at 2,500 kg m-3. Ru content uniform 5-10 wt% (commercial carbon-supported Ru ammonia
       catalyst ~8 wt%; Brown et al., Catal. Lett. 144, 545, 2014; US 4,600,571), bed density uniform 430-550 kg m-3
       (no published value; derived for a promoted Ru/graphitised-carbon bed). Before 2026-10-07 the Ru content was
       drawn from the measured catalysts (r 0.90-0.94, bed 500-1,000 kg m-3).
  B  measured Ru catalysts: each draw takes one of the measured Ru catalysts of the primary set
       (analysis/nh3_supported_2026_10_06), with its effective descriptor, residual multiplier and Ru content, bed
       density uniform 430-550 kg m-3, r uniform 0.90-0.97. Dispersion is part of the measured rate, so u is not
       applied.
  B0 as B without recovery.

Outputs: draws.csv, summary.json.
"""
import csv
import json
import math
import os
import sys
from pathlib import Path

import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
HARNESS = Path(os.environ.get("NH3_HARNESS", r"D:/论文-AI4S/Catalyst_Economic_Leverage_Automation_Harness_v0.1"))
sys.path.insert(0, str(HARNESS))
import harness_core as hc  # noqa: E402

sys.path.insert(0, str(REPO / "agent"))
from selfcheck_gate import require  # noqa: E402

RUN = HARNESS / "outputs" / "nh3_final_20260905T134204Z"
BASE = REPO / "analysis" / "supervisor_2026_09_20" / "nh3_cost_mc_summary.json"
SUPPORTED = REPO / "analysis" / "nh3_supported_2026_10_06" / "supported_candidates.csv"
N = 5000
U_RANGE, R_RANGE, BED_RANGE = (11.0, 50.0), (0.90, 0.97), (430.0, 550.0)
W_COMM = (0.05, 0.10)  # Ru mass fraction of the commercial supported catalyst, variant A_bed


def main():
    require()
    h = hc.NH3Harness(yaml.safe_load((RUN / "manifest_resolved.yaml").read_text(encoding="utf-8")), HARNESS)
    response, _cp, cached = h.build_or_load_response()
    if not cached:
        raise SystemExit("response surface is not cached; refusing to rebuild a frozen asset")

    def vector(x):
        v = h.interp_state_vector(response, x)
        assert np.isfinite(v).all(), f"response column missing at descriptor {x}"
        return v

    vec = {m: vector(hc.EN0_CANON[m]) for m in ("Fe", "Ru")}

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
            return math.inf, -1
        i = int(np.argmin(np.where(ok, total, np.inf)))
        return float(total[i]), i

    fe0, _ = evaluate("Fe", vec["Fe"], price=hc.PRICE["Fe"], life_y=h.CATALYST_LIFE_Y, cap=1.0, elec=h.ELECTRICITY)
    ru0, _ = evaluate("Ru", vec["Ru"], price=hc.PRICE["Ru"], life_y=h.CATALYST_LIFE_Y, cap=1.0, elec=h.ELECTRICITY)
    assert abs(fe0 - 15.291704676621144) < 1e-9 and abs(ru0 - 22.03059478781101) < 1e-9, (fe0, ru0)

    # preregistered draws, in the preregistered order
    rng = np.random.default_rng(20260920)
    fe_pm = np.exp(rng.uniform(math.log(0.5), math.log(2.0), N))
    ru_pm = np.exp(rng.uniform(math.log(0.5), math.log(2.0), N))
    cap = rng.uniform(0.8, 1.2, N)
    elec = rng.uniform(20.0, 100.0, N)
    life = rng.uniform(5.0, 20.0, N)
    # added inputs, second generator
    rng2 = np.random.default_rng(20261006)
    u = np.exp(rng2.uniform(math.log(U_RANGE[0]), math.log(U_RANGE[1]), N))
    r = rng2.uniform(*R_RANGE, N)
    bed = rng2.uniform(*BED_RANGE, N)
    meas = [x for x in csv.DictReader(SUPPORTED.open(encoding="utf-8"))
            if x["status"].startswith("primary") and x["active_metals"] == "Ru" and x["cost_USD_t"] != ""]
    k = rng2.integers(0, len(meas), N)
    w_comm = np.random.default_rng(20261007).uniform(*W_COMM, N)  # third generator: earlier draws keep their values
    mvec = [vector(float(x["E_eff_eV"])) for x in meas]
    m_ares = [10.0 ** float(x["log10_alpha_res"]) for x in meas]
    m_w = [float(x["metal_wt_pct"]) / 100.0 for x in meas]

    rows = []
    for d in range(N):
        kw = dict(life_y=float(life[d]), cap=float(cap[d]), elec=float(elec[d]))
        p_ru = hc.PRICE["Ru"] * float(ru_pm[d])
        fe, _ = evaluate("Fe", vec["Fe"], price=hc.PRICE["Fe"] * float(fe_pm[d]), **kw)
        base, _ = evaluate("Ru", vec["Ru"], price=p_ru, **kw)
        a, ia = evaluate("Ru", vec["Ru"], price=p_ru * (1.0 - float(r[d])) / float(u[d]), recovery=0.0, **kw)
        ab, _ = evaluate("Ru", vec["Ru"], price=p_ru, alpha=float(u[d]), recovery=float(r[d]), w=float(w_comm[d]),
                         bed=float(bed[d]), **kw)
        b, _ = evaluate("Ru", mvec[k[d]], price=p_ru, alpha=m_ares[k[d]], recovery=float(r[d]), w=m_w[k[d]],
                        bed=float(bed[d]), **kw)
        b0, _ = evaluate("Ru", mvec[k[d]], price=p_ru, alpha=m_ares[k[d]], recovery=0.0, w=m_w[k[d]],
                         bed=float(bed[d]), **kw)
        rows.append(dict(draw=d, Fe_price_multiplier=fe_pm[d], Ru_price_multiplier=ru_pm[d], capex_multiplier=cap[d],
                         electricity_USD_MWh=elec[d], catalyst_life_y=life[d], u=u[d], r=r[d], bed_density=bed[d],
                         A_bed_wt_pct=w_comm[d] * 100, measured_catalyst=meas[k[d]]["catalyst"],
                         measured_wt_pct=m_w[k[d]] * 100,
                         p_eff_USD_kg=p_ru * (1 - r[d]) / u[d], Fe=fe, Ru_base=base, Ru_A=a, Ru_A_bed=ab, Ru_B=b,
                         Ru_B0=b0, Ru_A_P_bar=float(h.state_P[ia])))

    gap0 = np.array([x["Ru_base"] - x["Fe"] for x in rows])
    ref = json.loads(BASE.read_text(encoding="utf-8"))["full_14136_state_direct_cost_verification"]
    assert float(np.mean(gap0 > 0)) == ref["P_C_Fe_lt_C_Ru"] == 1.0
    assert abs(float(gap0.min()) - ref["minimum_Ru_minus_Fe_USD_t"]) < 1e-9

    fe = np.array([x["Fe"] for x in rows])
    U, R, PE = np.array([x["u"] for x in rows]), np.array([x["r"] for x in rows]), np.array([x["p_eff_USD_kg"] for x in rows])
    out = {"draws": N, "base_reproduced": {"P_Fe_cheaper": 1.0, "min_gap_USD_t": float(gap0.min())},
           "ranges": {"u": U_RANGE, "r": R_RANGE, "bed_density_kg_m3": BED_RANGE,
                      "A_bed_Ru_wt_pct": [W_COMM[0] * 100, W_COMM[1] * 100], "measured_Ru_catalysts": len(meas)}}
    for name in ("A", "A_bed", "B", "B0"):
        ru = np.array([x["Ru_" + name] for x in rows])
        gap = ru - fe
        reg = gap / fe
        out[name] = {"P_Fe_cheaper": float(np.mean(gap > 0)),
                     "gap_quantiles_USD_t": {q: float(np.quantile(gap, p)) for q, p in (("p05", .05), ("p50", .5), ("p95", .95))},
                     "regret_quantiles": {q: float(np.quantile(reg, p)) for q, p in (("p05", .05), ("p50", .5), ("p95", .95))}}
    # where Ru wins, for the two u-and-r variants
    t_u, t_r = np.quantile(U, [1 / 3, 2 / 3]), np.quantile(R, [1 / 3, 2 / 3])
    W = np.array([x["A_bed_wt_pct"] for x in rows])
    order = np.argsort(PE)
    for name in ("A", "A_bed"):
        win = np.array([x["Ru_" + name] < x["Fe"] for x in rows])
        grid = {}
        for iu, (ulo, uhi) in enumerate(((U.min(), t_u[0]), (t_u[0], t_u[1]), (t_u[1], U.max() + 1))):
            for ir, (rlo, rhi) in enumerate(((R.min(), t_r[0]), (t_r[0], t_r[1]), (t_r[1], R.max() + 1))):
                m = (U >= ulo) & (U < uhi) & (R >= rlo) & (R < rhi)
                grid[f"u_tercile{iu + 1}_r_tercile{ir + 1}"] = {"n": int(m.sum()), "P_Ru_wins": float(win[m].mean())}
        top_both = (U >= t_u[1]) & (R >= t_r[1])
        out[name + "_where_Ru_wins"] = {
            "P_Ru_wins": float(win.mean()),
            "u_r_tercile_grid": grid,
            "P_Ru_wins_given_u_lowest_tercile": float(win[U < t_u[0]].mean()),
            "P_Ru_wins_given_u_top_tercile": float(win[U >= t_u[1]].mean()),
            "P_Ru_wins_given_r_lowest_tercile": float(win[R < t_r[0]].mean()),
            "P_Ru_wins_given_r_top_tercile": float(win[R >= t_r[1]].mean()),
            "share_of_Ru_wins_with_u_and_r_in_top_tercile": float(top_both[win].mean()) if win.any() else None,
            "P_Ru_wins_given_u_and_r_top_tercile": float(win[top_both].mean()),
            "P_Ru_wins_given_u_or_r_bottom_tercile": float(win[(U < t_u[0]) | (R < t_r[0])].mean()),
            "median_u_r_when_Ru_wins": [float(np.median(U[win])), float(np.median(R[win]))] if win.any() else None,
            "median_u_r_when_Fe_wins": [float(np.median(U[~win])), float(np.median(R[~win]))],
            "P_Ru_wins_by_p_eff_quintile": [float(win[order[i * N // 5:(i + 1) * N // 5]].mean()) for i in range(5)],
            "u_terciles": t_u.tolist(), "r_terciles": t_r.tolist(),
        }
        if name == "A_bed":  # the Ru content only enters through the supported bed
            out[name + "_where_Ru_wins"].update({
                "P_Ru_wins_given_Ru_content_lt_7.5_wt_pct": float(win[W < 7.5].mean()),
                "P_Ru_wins_given_Ru_content_ge_7.5_wt_pct": float(win[W >= 7.5].mean()),
            })
    out["p_eff_quantiles_USD_kg"] = {q: float(np.quantile(PE, p)) for q, p in (("p05", .05), ("p50", .5), ("p95", .95))}
    winB = np.array([x["Ru_B"] < x["Fe"] for x in rows])
    out["B_Ru_winning_catalysts"] = sorted({x["measured_catalyst"] for x, w_ in zip(rows, winB) if w_})
    with (HERE / "draws.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    (HERE / "summary.json").write_text(json.dumps(out, indent=1, default=float) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=1, default=float))


if __name__ == "__main__":
    main()
