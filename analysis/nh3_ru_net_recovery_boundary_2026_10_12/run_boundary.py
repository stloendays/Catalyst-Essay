"""Decision boundary for promoted spent Ru/C on its own bed, with net monetary recovery.

Run after the unchanged cloud harness preparation:
    NH3_HARNESS=/tmp/nh3_harness python analysis/nh3_ru_net_recovery_boundary_2026_10_12/run_boundary.py
Read-only frozen 14,136-state response. No rewriting of official figures or baseline.
"""
from __future__ import annotations

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
PARENT = REPO / "analysis" / "nh3_actual_ru_params_2026_10_07"
sys.path.insert(0, str(HERE))
from boundary_math import effective_credit, same_loop_gap, threshold_credit

ROOT = Path(os.environ.get("NH3_HARNESS", "/tmp/nh3_harness"))
RUN = ROOT / "outputs" / "nh3_final_20260905T134204Z"
sys.path.insert(0, str(ROOT))
import harness_core as hc

RECOVERIES = (0.0, 0.80, 0.90, 0.911, 0.9305, 0.946, 0.9555)
REALIZATIONS = (0.80, 0.90, 1.00)
LOADINGS = (0.05, 0.08, 0.10)
DENSITIES = (430.0, 490.0, 550.0)


def main():
    h = hc.NH3Harness(yaml.safe_load((RUN / "manifest_resolved.yaml").read_text(encoding="utf-8")), ROOT)
    response, _, cached = h.build_or_load_response()
    if not cached or h.NSTATE != 14136:
        raise RuntimeError("Frozen cached response surface unavailable: do not rebuild implicitly")
    v = {metal: h.interp_state_vector(response, hc.EN0_CANON[metal]) for metal in ("Fe", "Ru")}
    if not all(np.isfinite(x).all() for x in v.values()):
        raise RuntimeError("Fe/Ru frozen descriptor columns missing")
    fe_total, fe_volume, _, _ = h.cost_arrays("Fe", v["Fe"])
    valid_fe = fe_volume <= h.V_CAP
    kaap = (h.state_P == 90.0) & (h.state_Tsep == -20.0)
    fe_ref = {"main": float(np.min(np.where(valid_fe, fe_total, np.inf))),
              "KAAP": float(np.min(np.where(valid_fe & kaap, fe_total, np.inf)))}
    if abs(fe_ref["main"] - 15.291704676621144) > 1e-9 or abs(fe_ref["KAAP"] - 19.06868861189332) > 1e-9:
        raise AssertionError(f"Fe reference mismatch: {fe_ref}")
    u = 11.0
    bench_metal_per_m3 = h.ACTIVE_FRACTION * h.BED_DENSITY
    price = hc.PRICE["Ru"]
    rows = []
    boundaries = []
    def cost_fn(loop, w, density):
        bed_factor = bench_metal_per_m3 / (u * w * density)
        mask = np.ones(h.NSTATE, dtype=bool) if loop == "main" else kaap
        def f(net_credit):
            pe = price * (1.0 - net_credit) / u
            _tot, v_bench, metal, _reactor = h.cost_arrays("Ru", v["Ru"], price=pe, alpha=1.0)
            actual_volume = v_bench * bed_factor
            reactor = ((h.REACTOR_FIXED + h.REACTOR_VAR * np.power(actual_volume / h.REACTOR_REF, h.REACTOR_EXP))
                       * h.crf / h.annual_output_t + h.vessel_pressure_premium(actual_volume))
            totals = metal + reactor + h.state_process_cost
            return float(np.min(np.where(mask & (actual_volume <= h.V_CAP), totals, np.inf)))
        return f
    for loop in ("main", "KAAP"):
        for w in LOADINGS:
            for density in DENSITIES:
                f = cost_fn(loop, w, density)
                qstar = threshold_credit(f, fe_ref[loop])
                for realization in REALIZATIONS:
                    boundaries.append(dict(loop=loop, w_Ru=w, rho_kg_m3=density,
                                           net_realization=realization,
                                           effective_credit_parity=qstar if qstar is not None else "",
                                           physical_recovery_parity=(qstar / realization if qstar is not None and qstar <= realization else ""),
                                           parity_in_promoted_range=(qstar is not None and qstar <= realization * 0.9555)))
                    for r in RECOVERIES:
                        q = effective_credit(r, realization)
                        c = f(q)
                        rows.append(dict(loop=loop, recovery=r, net_realization=realization,
                                         effective_credit=q, w_Ru=w, rho_kg_m3=density,
                                         Ru_cost_USD_t=c, Fe_same_loop_USD_t=fe_ref[loop],
                                         gap_same_loop_USD_t=same_loop_gap(c, fe_ref[loop]),
                                         globally_competitive_with_Fe=(c <= fe_ref["main"])))
    def write_csv(path, data):
        with path.open("w", newline="", encoding="utf-8") as output:
            writer = csv.DictWriter(output, fieldnames=list(data[0]), lineterminator="\n")
            writer.writeheader()
            writer.writerows(data)
    write_csv(HERE / "cost_surface.csv", rows)
    write_csv(HERE / "parity_boundary.csv", boundaries)
    canonical = [r for r in rows if r["net_realization"] == 1.0 and r["w_Ru"] in (0.05, 0.08, 0.10)
                 and r["rho_kg_m3"] in (430.0, 550.0) and r["recovery"] in (0.90, 0.9555)]
    committed = {(x["loop"], float(x["recovery"]), float(x["w_Ru"]), float(x["rho_bed_kg_m3"])): float(x["cost"])
                 for x in csv.DictReader((PARENT / "promoted_recovery_check.csv").open(encoding="utf-8"))}
    for row in canonical:
        key = (row["loop"], row["recovery"], row["w_Ru"], row["rho_kg_m3"])
        if abs(row["Ru_cost_USD_t"] - committed[key]) > 1e-9:
            raise AssertionError(f"Promoted recovery regression changed {key}")
    report = {"scope": "derived exploratory overlay; frozen model unchanged",
              "number_of_process_states": h.NSTATE, "Fe_reference": fe_ref, "n_surface_rows": len(rows),
              "n_parity_rows": len(boundaries), "regression_rows": len(canonical),
              "recovery_basis": "promoted spent Ru/C upper bound 0.9555; physical metal vs salt yields must be distinguished",
              "credit_assumption": "q = physical recovery * monetary realization; realization subsumes costs/discounts as a scenario, not calibrated industrial cash flow",
              "feasibility_limitation": "Fe feasibility in a KAAP-specific vessel is a modeled constraint check, not a validated plant retrofit",
              "optimisation_limitation": "14,136 fixed states, same frozen thermal/pressure physics; not continuous process design"}
    (HERE / "summary.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
