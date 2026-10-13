"""Check: the Fig. 3d own-bed reading at the Ru recoveries measured for promoted spent Ru/C ammonia catalysts.

The recovery range of the literature parameter set (0.90-0.97, run_params.py set R_all) takes its upper end from
CN 1872418 A Example 4, an unpromoted Ru/C (97.61 %). The promoted (Ba, K, Mg) spent catalysts of the two Chinese
recovery patents give 93.05-95.55 % (CN 1872418 A Examples 1-3) and 91.1-95.4 % (CN 101638727 B Examples 1-3)
(independent review of PR #42; work/expert_check_2026-10-07 notes). This script evaluates the same reading as
run_params.py (same harness, same code path: effective price p (1 - r) / u, own bed at w and rho, main loop and KAAP
loop at 90 bar, Tsep -20 C, each against Fe in the same loop) at r = 0.911, 0.9305 and 0.9555, for the R_all corners
w 5 / 8 / 10 wt% and rho 430 / 550 kg m-3. It writes promoted_recovery_check.csv and does not change any canonical
output. (Since 2026-10-12 set R_all itself uses 0.90-0.9555; the 24 R_all corners at r = 0.90 and 0.9555 are the
cross-check, and the 0.97 rows are kept for comparison.)

Model: NH3_MODEL=1.1 (default; NH3-FINAL-1.1, output in this folder, cross-checked against fig3d_readings.csv here) or
NH3_MODEL=1.2 (NH3-FINAL-1.2, output in nh3_1_2/, cross-checked against nh3_1_2/fig3d_readings.csv), through
analysis/nh3_model.py. The Fe reference is the selected run's results.json (nh3_model.anchors()), reproduced first.

    NH3_HARNESS=<root> python promoted_recovery_check.py
    NH3_MODEL=1.2 NH3_HARNESS_1_2=<1.2 root> python promoted_recovery_check.py
"""
import csv
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "analysis"))
import nh3_model as NM  # noqa: E402

HARNESS = NM.root()
sys.path.insert(0, str(HARNESS))
hc = NM.core()
OUT = NM.out_dir(HERE)

FE_COST = NM.anchors()["Fe"]
U_MIN = 0.11 / 0.01
KAAP_P, KAAP_TSEP = 90.0, -20.0
RECOVERY = (0.911, 0.9305, 0.9555, 0.90, 0.97)      # promoted examples; the R_all corners for the cross-check
W = (0.05, 0.08, 0.10)
RHO = (430.0, 550.0)


def main():
    h = NM.harness()
    assert h.NSTATE == NM.anchors()["NSTATE"], h.NSTATE
    response, _cp, cached = h.build_or_load_response()
    if not cached:
        raise SystemExit("response surface is not cached; refusing to rebuild a frozen asset")
    vec = {m: h.interp_state_vector(response, hc.EN0_CANON[m]) for m in ("Fe", "Ru")}
    p_ru = hc.PRICE["Ru"]
    bench_metal_per_m3 = h.ACTIVE_FRACTION * h.BED_DENSITY

    def reactor_cost(V):
        return ((h.REACTOR_FIXED + h.REACTOR_VAR * np.power(V / h.REACTOR_REF, h.REACTOR_EXP)) * h.crf
                / h.annual_output_t + h.vessel_pressure_premium(V))

    def optimum(price, bed_factor, mask=None):
        total, V, metal_cost, _ = h.cost_arrays("Ru", vec["Ru"], price=price, alpha=1.0)
        V = V * bed_factor
        total = metal_cost + reactor_cost(V) + h.state_process_cost
        ok = V <= h.V_CAP
        if mask is not None:
            ok &= mask
        return float(np.min(np.where(ok, total, np.inf)))

    t_fe, V_fe, _, _ = h.cost_arrays("Fe", vec["Fe"])
    assert abs(float(np.min(np.where(V_fe <= h.V_CAP, t_fe, np.inf))) - FE_COST) < 1e-9
    kaap = (h.state_P == KAAP_P) & (h.state_Tsep == KAAP_TSEP)
    fe_kaap = float(np.min(np.where((V_fe <= h.V_CAP) & kaap, t_fe, np.inf)))
    rows = []
    for loop, mask, ref in (("main", None, FE_COST), ("KAAP", kaap, fe_kaap)):
        for r in RECOVERY:
            for w in W:
                for rho in RHO:
                    c = optimum(p_ru * (1.0 - r) / U_MIN, bench_metal_per_m3 / (U_MIN * w * rho), mask)
                    rows.append(dict(loop=loop, recovery=r, w_Ru=w, rho_bed_kg_m3=rho, cost=c, Fe_same_loop=ref,
                                     gap_to_Fe_same_loop=c - ref))
    # the R_all corners must reproduce the committed readings of the selected model (run_params.py)
    committed = {(x["loop"], float(x["recovery"]), float(x["w_Ru"]), float(x["rho_bed_kg_m3"])): float(x["cost"])
                 for x in csv.DictReader(open(OUT / "fig3d_readings.csv", encoding="utf-8")) if x["set"] == "R_all"}
    n = 0
    for x in rows:
        k = (x["loop"], x["recovery"], x["w_Ru"], x["rho_bed_kg_m3"])
        if k in committed:
            assert abs(committed[k] - x["cost"]) < 1e-9, (k, committed[k], x["cost"])
            n += 1
    assert n == 24, n
    with open(OUT / "promoted_recovery_check.csv", "w", newline="", encoding="utf-8") as fh:
        wr = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator="\n")
        wr.writeheader()
        wr.writerows(rows)
    for loop in ("main", "KAAP"):
        for lo, hi in ((0.911, 0.9555), (0.9305, 0.9555), (0.90, 0.97)):
            sel = [x for x in rows if x["loop"] == loop and lo - 1e-9 <= x["recovery"] <= hi + 1e-9
                   and x["recovery"] in (lo, hi)]
            s8 = [x for x in sel if x["w_Ru"] == 0.08]
            print(f"{loop:4s} r {lo:.4f}-{hi:.4f}: cost {min(x['cost'] for x in sel):.3f}-{max(x['cost'] for x in sel):.3f}"
                  f" (8 wt%: {min(x['cost'] for x in s8):.3f}-{max(x['cost'] for x in s8):.3f}) vs Fe {sel[0]['Fe_same_loop']:.3f};"
                  f" corners below Fe {sum(x['gap_to_Fe_same_loop'] < 0 for x in sel)}/{len(sel)}")


if __name__ == "__main__":
    main()
