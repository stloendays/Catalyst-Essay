"""Figure 2d inputs: Ru at its actual catalyst cost, and the activity Ru needs at each price.

The canonical NH3-FINAL-1.1 benchmark gives every metal the formulation of the industrial
fused-iron catalyst: one global calibration (Fe, 65 m3 bed, 400 C, 80 bar) maps per-site TOF to
kilograms of active metal, the bed is 71.51 wt% metal at 2,500 kg m-3, and spent metal is not
recovered. A real Ru catalyst is supported, far better dispersed, and refined back after use. In
the harness the metal-inventory term is

    metal cost = m_active * price * (1 - r) / life / annual output,   m_active ∝ 1 / (F_CAL * TOF)

so a catalyst that exposes u times more of its Ru atoms than fused iron exposes of its Fe atoms
needs m_active / u, and recovering a fraction r leaves a net metal charge equal to the benchmark
at an effective price

    p_eff = p_Ru * (1 - r) / u.

The Fig. 3d price sweep is therefore read on p_eff (benchmark-formulation reading: the bed keeps the
benchmark formulation and the volume of the undivided metal mass). The supported bed itself is larger
(Ru is 3.2 wt% of the catalyst, not 71.5 wt%); it enters the reactor term and is computed here for the
actual Ru/C catalyst (fig2_ru_bed_sensitivity.csv: cost, Fe reference of the same loop, activity
multiple for parity), and shown in Fig. 3d next to the benchmark reading.

Literature values
  u    >= 11      Ru dispersion 11% (O2 chemisorption) for a Ba-Cs-K promoted Ru/C ammonia
                  catalyst with 3.2 wt% Ru: Rossetti, Pernicone, Ferrero & Forni, Ind. Eng.
                  Chem. Res. 45, 4150-4155 (2006), doi:10.1021/ie051398g; fewer than 1% of Fe
                  atoms are exposed in reduced fused-iron catalyst: Liu, Li, Suzuki, Ohnishi &
                  Ichikawa, CIESC J. 51, 462 (2000). u = 0.11 / 0.01 is a lower bound.
  r    0.90-0.94  more than 94% of Ru recovered from spent promoted Ru ammonia catalyst:
                  US 6,673,732 B2 (Haldor Topsoe, 2004); 0.90 is the lower end used here.
  KAAP 91 bar, Tsep -20 C   Kellogg Advanced Ammonia Process synthesis loop at 9.1 MPa with a
                  -20 C condenser: Humphreys, Lan & Tao, Adv. Energy Sustain. Res. 2, 2000043
                  (2021), doi:10.1002/aesr.202000043. Grid point 90 bar is used.

Read-only with respect to the harness; refuses to rebuild the cached response surface.

    CatalystForge/.venv/python fig2_ru_actual_cost.py [harness_root]
      -> fig2_ru_alpha_sweep.csv, fig2_ru_actual_cost_points.csv, fig2_ru_bed_sensitivity.csv
"""
import csv
import json
import math
import os
import sys
from pathlib import Path

import numpy as np
import yaml
from scipy.optimize import brentq

HERE = Path(__file__).resolve().parent
HARNESS = Path(sys.argv[1] if len(sys.argv) > 1 else
               os.environ.get("NH3_HARNESS", r"D:/论文-AI4S/Catalyst_Economic_Leverage_Automation_Harness_v0.1"))
sys.path.insert(0, str(HARNESS))
from harness_core import EN0_CANON, PRICE, NH3Harness  # noqa: E402

RUN = HARNESS / "outputs" / "nh3_final_20260905T134204Z"
cfg = yaml.safe_load((RUN / "manifest_resolved.yaml").read_text(encoding="utf-8"))
h = NH3Harness(cfg, HARNESS)
assert h.NSTATE == 14136, "process-state library changed"
_resp, _cp, cached = h.build_or_load_response()
if not cached:
    raise SystemExit("response surface is not cached; refusing to rebuild a frozen asset")

FE_COST = 15.291704676621144
ALPHA_STAR_CANON = 201.22
P_RU = PRICE["Ru"]                       # 53,852.5 USD/kg, frozen
U_MIN = 0.11 / 0.01                      # dispersion ratio, lower bound
R_HI, R_LO = 0.94, 0.90                  # Ru recovery
W_RU = 0.032                             # Ru mass fraction of the Ru/C catalyst (Rossetti 2006)
RHO_SUPPORTED = (500.0, 1000.0)          # assumed bulk density range of a carbon-supported bed, kg/m3
KAAP_P, KAAP_TSEP = 90.0, -20.0
BENCH_METAL_PER_M3 = h.ACTIVE_FRACTION * h.BED_DENSITY   # 1,787.75 kg metal per m3 of benchmark bed

logvec = {m: h.frozen_state_logtof(EN0_CANON[m]) for m in ("Fe", "Ru")}


def reactor_cost(V):
    return ((h.REACTOR_FIXED + h.REACTOR_VAR * np.power(V / h.REACTOR_REF, h.REACTOR_EXP)) * h.crf
            / h.annual_output_t + h.vessel_pressure_premium(V))


def optimum(price, alpha=1.0, bed_factor=1.0, mask=None):
    """Ru optimum at a metal price; bed_factor scales the bed volume of the benchmark formulation."""
    total, V, metal_cost, reactor = h.cost_arrays("Ru", logvec["Ru"], price=price, alpha=alpha)
    if bed_factor != 1.0:
        V = V * bed_factor
        reactor = reactor_cost(V)
        total = metal_cost + reactor + h.state_process_cost
    ok = V <= h.V_CAP
    if mask is not None:
        ok &= mask
    i = int(np.argmin(np.where(ok, total, np.inf)))
    return dict(cost=float(total[i]), T_C=float(h.state_T[i]), P_bar=float(h.state_P[i]),
                Tsep_C=float(h.state_Tsep[i]), V_m3=float(V[i]), metal_cost=float(metal_cost[i]))


def alpha_star(price, mask=None, bed_factor=1.0, target=None):
    """Ru intrinsic-activity multiplier at which the reoptimized Ru cost equals the Fe optimum (or `target`)
    (inf when even an unlimited activity leaves the restricted process above it)."""
    target = FE_COST if target is None else target
    if optimum(price, 1e12, bed_factor=bed_factor, mask=mask)["cost"] > target:
        return math.inf
    return 10.0 ** brentq(lambda la: optimum(price, 10.0 ** la, bed_factor=bed_factor, mask=mask)["cost"] - target,
                          -6.0, 12.0, xtol=1e-11)


# ---- frozen anchors reproduce --------------------------------------------------
fe = h.cost_arrays("Fe", logvec["Fe"])
assert abs(float(np.min(np.where(fe[1] <= h.V_CAP, fe[0], np.inf))) - FE_COST) < 1e-9
assert abs(optimum(P_RU)["cost"] - 22.03059478781101) < 1e-9
a0 = alpha_star(P_RU)
assert abs(a0 - ALPHA_STAR_CANON) < 0.005, a0
print("anchors: Fe %.6f, Ru %.6f, alpha* %.4f" % (FE_COST, optimum(P_RU)["cost"], a0))

# ---- alpha* along the Fig. 2d price axis ----------------------------------------
sweep_prices = [float(r["price_USD_kg"]) for r in csv.DictReader(open(HERE / "fig2_ru_price_sweep.csv", encoding="utf-8"))]
rows = []
for p in sweep_prices:
    a = alpha_star(p)
    o = optimum(p, a)
    rows.append(dict(price_USD_kg=p, alpha_star=a, T_C=o["T_C"], P_bar=o["P_bar"], Tsep_C=o["Tsep_C"], V_m3=o["V_m3"]))
al = np.array([r["alpha_star"] for r in rows])
assert np.all(np.diff(al[:-1]) >= -1e-9), "alpha* is not monotone in price"
with open(HERE / "fig2_ru_alpha_sweep.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
print("alpha* sweep: %d prices, %.4g at 1 USD/kg -> %.4g at 3e5 USD/kg" % (len(rows), al[0], al[-2]))

# ---- actual-cost points ------------------------------------------------------------
kaap = (h.state_P == KAAP_P) & (h.state_Tsep == KAAP_TSEP)
assert kaap.any()
SCEN = [  # key, label, u, r, mask
    ("pure", "Pure Ru, benchmark formulation (canonical)", 1.0, 0.0, None),
    ("supported", "Supported Ru/C, no recovery", U_MIN, 0.0, None),
    ("supp_rec90", "Supported Ru/C, 90% recovery", U_MIN, R_LO, None),
    ("supp_rec94", "Supported Ru/C, 94% recovery", U_MIN, R_HI, None),
    ("kaap90", "Supported Ru/C, 90% recovery, KAAP loop (90 bar, Tsep -20 C)", U_MIN, R_LO, kaap),
    ("kaap94", "Supported Ru/C, 94% recovery, KAAP loop (90 bar, Tsep -20 C)", U_MIN, R_HI, kaap),
]
pts = []
for key, label, u, r, mask in SCEN:
    pe = P_RU * (1.0 - r) / u
    o = optimum(pe, mask=mask)
    a = alpha_star(pe, mask=mask)
    pts.append(dict(key=key, label=label, u=u, recovery=r, p_eff_USD_kg=pe, cost=o["cost"],
                    gap_to_Fe=o["cost"] - FE_COST, alpha_star=a, T_C=o["T_C"], P_bar=o["P_bar"],
                    Tsep_C=o["Tsep_C"], V_m3_benchmark=o["V_m3"], metal_cost=o["metal_cost"]))
    print("%-11s p_eff %10.2f  cost %.4f (%+.3f)  alpha* %8.3f  %3.0f C %4.0f bar Tsep %3.0f C  V %.3f"
          % (key, pe, o["cost"], o["cost"] - FE_COST, a, o["T_C"], o["P_bar"], o["Tsep_C"], o["V_m3"]))
# Fe in the same KAAP loop, for the like-for-like comparison at that condition
t_fe, V_fe, mc_fe, _ = h.cost_arrays("Fe", logvec["Fe"])
ok_fe = (V_fe <= h.V_CAP) & kaap
i_fe = int(np.argmin(np.where(ok_fe, t_fe, np.inf)))
pts.append(dict(key="fe_kaap", label="Fe (fused iron), KAAP loop (90 bar, Tsep -20 C)", u=1.0, recovery=0.0,
                p_eff_USD_kg=PRICE["Fe"], cost=float(t_fe[i_fe]), gap_to_Fe=float(t_fe[i_fe]) - FE_COST,
                alpha_star=math.nan, T_C=float(h.state_T[i_fe]), P_bar=float(h.state_P[i_fe]),
                Tsep_C=float(h.state_Tsep[i_fe]), V_m3_benchmark=float(V_fe[i_fe]), metal_cost=float(mc_fe[i_fe])))
print("fe_kaap     cost %.4f  %3.0f C  V %.2f m3" % (t_fe[i_fe], h.state_T[i_fe], V_fe[i_fe]))
# Strict-scaling reach: the audited lifecycle boundary gives the effective Ru price (10-y basis) below which a
# scaling-consistent Ru descriptor matches Fe over all 14,136 states. Metal cost scales with p (1 - r) / (u L), so
# the same boundary applies to p_eff. Ru/C points above it miss Fe even after scaling-consistent tuning.
REACH_JSON = HERE.parents[2] / "analysis" / "fe_bridge_backward_2026_09_29" / "scaling_lifecycle_exact_summary.json"
reach = json.loads(REACH_JSON.read_text(encoding="utf-8"))
assert abs(reach["Fe_reference_cost_USD_t"] - FE_COST) < 1e-12
P_REACH = reach["equivalent_effective_Ru_price_at_10y_USD_kg"]
pts.append(dict(key="strict_scaling_reach", label="Strict-scaling reach: scaling-consistent Ru matches Fe at or below this p_eff",
                u=math.nan, recovery=math.nan, p_eff_USD_kg=P_REACH, cost=FE_COST, gap_to_Fe=0.0, alpha_star=math.nan,
                T_C=reach["strict_scaling_parity_state"]["T_C"], P_bar=reach["strict_scaling_parity_state"]["P_bar"],
                Tsep_C=reach["strict_scaling_parity_state"]["Tsep_C"],
                V_m3_benchmark=reach["strict_scaling_parity_state"]["V_m3"], metal_cost=math.nan))
for r in (R_LO, R_HI):
    print("strict-scaling reach %.1f USD/kg needs u >= %.1f at r = %.2f" % (P_REACH, P_RU * (1 - r) / P_REACH, r))
floor = optimum(1e-9, 1e12, mask=kaap)
print("KAAP loop floor (free, infinitely active catalyst): %.4f USD/t at %3.0f C (%+.3f vs Fe)"
      % (floor["cost"], floor["T_C"], floor["cost"] - FE_COST))
# u needed for parity at each recovery, with the benchmark bed
p_star = float(list(csv.DictReader(open(HERE / "fig2_ru_price_sweep.csv", encoding="utf-8")))[-1]["price_USD_kg"])
for r in (0.0, R_LO, R_HI):
    print("parity needs u = %.1f at r = %.2f" % (P_RU * (1 - r) / p_star, r))
with open(HERE / "fig2_ru_actual_cost_points.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(pts[0]), lineterminator="\n")
    w.writeheader()
    w.writerows(pts)

# ---- the supported Ru/C bed ------------------------------------------------------------
# The price reading above keeps the benchmark formulation (71.51 wt% metal at 2,500 kg m-3, bed of the undivided metal
# mass). The real Ru/C catalyst carries its m_Ru / u of Ru at 3.2 wt% in a 500-1,000 kg m-3 bed, i.e. the benchmark
# bed volume times bed_factor = 1,787.75 / (u w rho); this enters the reactor term. Each row also gives the Fe
# reference of its loop (the Fe optimum, or Fe in the same KAAP loop), the gap and the Ru activity multiple needed for
# parity with that reference on the supported-bed basis.
fe_ref = {False: (FE_COST, "Fe optimum"), True: (float(t_fe[i_fe]), "Fe in the KAAP loop")}
sens = []
for key, label, u, r, mask in SCEN[1:]:
    pe = P_RU * (1.0 - r) / u
    base = optimum(pe, mask=mask)
    ref, ref_label = fe_ref[mask is not None]
    for rho in RHO_SUPPORTED:
        k = BENCH_METAL_PER_M3 / (u * W_RU * rho)
        o = optimum(pe, bed_factor=k, mask=mask)
        a_s = alpha_star(pe, mask=mask, bed_factor=k, target=ref)
        sens.append(dict(key=key, rho_bed_kg_m3=rho, bed_factor=k, cost=o["cost"], delta_vs_benchmark_bed=o["cost"] - base["cost"],
                         T_C=o["T_C"], P_bar=o["P_bar"], Tsep_C=o["Tsep_C"], V_m3=o["V_m3"], Fe_reference=ref_label,
                         Fe_reference_cost=ref, gap_to_Fe_reference=o["cost"] - ref, alpha_star_supported_bed=a_s))
        print("  bed x%.2f (rho %4.0f): %-11s cost %.4f (%+.4f)  %4.0f bar  V %.2f m3  vs %s %.4f: %+.4f  alpha* %.3f"
              % (k, rho, key, o["cost"], o["cost"] - base["cost"], o["P_bar"], o["V_m3"], ref_label, ref,
                 o["cost"] - ref, a_s))
with open(HERE / "fig2_ru_bed_sensitivity.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(sens[0]), lineterminator="\n")
    w.writeheader()
    w.writerows(sens)
print("wrote fig2_ru_alpha_sweep.csv, fig2_ru_actual_cost_points.csv, fig2_ru_bed_sensitivity.csv")
