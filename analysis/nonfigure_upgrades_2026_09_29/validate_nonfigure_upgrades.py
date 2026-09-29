"""Validate all promoted non-figure derived diagnostics from frozen repository sources.

No DFT, process optimization or LLM calls are executed.
"""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
RUN = ROOT / "provenance/nh3_final_1_1/source_harness/outputs/nh3_final_20260905T134204Z"


def rows(path):
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def close(a, b, tol=1e-10):
    return abs(float(a) - float(b)) <= tol


# ---- decision regret ---------------------------------------------------------
reg = {r["system"]: r for r in rows(HERE / "decision_regret_summary.csv")}
res = json.loads((RUN / "results.json").read_text(encoding="utf-8"))
fe = float(res["deterministic"]["metals"]["Fe"]["feasible"]["total_cost"])
ru = float(res["deterministic"]["metals"]["Ru"]["feasible"]["total_cost"])
r_nh3 = (ru - fe) / fe
assert close(reg["NH3"]["normalized_decision_regret"], r_nh3, 1e-12)

meoh = {r["candidate"]: r for r in rows(ROOT / "data/meoh/meoh_candidate_ranking_D01v3.csv")}
up = float(meoh["1 wt% Re | 250 C"]["NPC_EUR_t_2pct_purge"])
best = float(meoh["5 wt% Re | 200 C"]["NPC_EUR_t_2pct_purge"])
r_meoh = (up - best) / best
assert close(reg["MeOH"]["normalized_decision_regret"], r_meoh, 1e-12)
assert close(reg["AuTiO2"]["normalized_decision_regret"], 0.0, 0.0)

# ---- pairwise transfer index ------------------------------------------------
tr = {r["system"]: r for r in rows(HERE / "pairwise_inversion_index.csv")}
fig1 = {r["metal"]: r for r in rows(ROOT / "figures/composite/fig1/fig1_metals.csv")}
s_nh3 = 10 ** (float(fig1["Ru"]["logTOF_673K"]) - float(fig1["Fe"]["logTOF_673K"]))
chi_nh3 = math.log(ru / fe) / math.log(s_nh3)
assert close(tr["NH3"]["pairwise_transfer_index_chi"], chi_nh3, 1e-12)

s_meoh = 65.0 / 18.0
chi_meoh = math.log(up / best) / math.log(s_meoh)
assert close(tr["MeOH"]["pairwise_transfer_index_chi"], chi_meoh, 1e-12)

au = {int(float(r["diameter_nm"])): r for r in rows(ROOT / "data/rank_preservation_control_v1_1.csv")}
s_au = float(au[2]["mass_activity_umol_CO_gcat_s"]) / float(au[6]["mass_activity_umol_CO_gcat_s"])
j_au = float(au[2]["required_catalyst_mass_mg"]) / float(au[6]["required_catalyst_mass_mg"])
chi_au = math.log(j_au) / math.log(s_au)
assert close(tr["AuTiO2"]["pairwise_transfer_index_chi"], chi_au, 1e-12)

# ---- descriptor correlation sensitivity ------------------------------------
sc = rows(RUN / "closure/scaling_reachability.csv")
x = [float(r["E_N_eV"]) for r in sc]
y = [math.log(float(r["gain_673K"])) for r in sc]


def interp(v):
    if v <= x[0]:
        return y[0]
    if v >= x[-1]:
        return y[-1]
    lo, hi = 0, len(x) - 1
    while hi - lo > 1:
        m = (lo + hi) // 2
        if x[m] <= v:
            lo = m
        else:
            hi = m
    t = (v - x[lo]) / (x[hi] - x[lo])
    return y[lo] * (1 - t) + y[hi] * t


def phi(z):
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))


class LCGNormal:
    def __init__(self, seed):
        self.seed = int(seed) & 0xFFFFFFFF

    def uniform(self):
        self.seed = (1664525 * self.seed + 1013904223) & 0xFFFFFFFF
        return self.seed / 4294967296.0

    def normal(self):
        u = 0.0
        v = 0.0
        while u == 0.0:
            u = self.uniform()
        while v == 0.0:
            v = self.uniform()
        return math.sqrt(-2 * math.log(u)) * math.cos(2 * math.pi * v)


cent = {"Fe": -1.392120623747696, "Ru": -1.1333, "Os": -1.1095}
sig_fe = 0.2271258177356984
half = 0.15
corr_rows = {float(r["latent_pairwise_correlation"]): r for r in rows(HERE / "descriptor_correlation_sensitivity.csv")}

for rho in (0.0, 0.25, 0.5, 0.75, 0.9):
    rng = LCGNormal(20260929 + round(rho * 1000))
    n = 100000
    cnt = {"Ru": 0, "Os": 0, "Fe": 0}
    full = 0
    sr, si = math.sqrt(rho), math.sqrt(1 - rho)
    for _ in range(n):
        g0 = rng.normal()
        z = {m: sr * g0 + si * rng.normal() for m in ("Fe", "Ru", "Os")}
        E = {
            "Fe": cent["Fe"] + sig_fe * z["Fe"],
            "Ru": cent["Ru"] + half * (2 * phi(z["Ru"]) - 1),
            "Os": cent["Os"] + half * (2 * phi(z["Os"]) - 1),
        }
        order = sorted(E, key=lambda m: interp(E[m]), reverse=True)
        cnt[order[0]] += 1
        full += order == ["Ru", "Os", "Fe"]

    rr = corr_rows[rho]
    assert close(rr["P_canonical_Ru_gt_Os_gt_Fe"], full / n, 5e-8)
    assert close(rr["P_atomic_top1_Ru"], cnt["Ru"] / n, 5e-8)
    assert close(rr["P_atomic_top1_Os"], cnt["Os"] / n, 5e-8)
    assert close(rr["P_atomic_top1_Fe"], cnt["Fe"] / n, 5e-8)

# ---- common additive descriptor bias ----------------------------------------
common = json.loads((HERE / "common_mode_descriptor_shift.json").read_text(encoding="utf-8"))


def diff(delta, a, b):
    return interp(cent[a] + delta) - interp(cent[b] + delta)


def bisect(lo, hi, a, b):
    flo = diff(lo, a, b)
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        fm = diff(mid, a, b)
        if flo * fm <= 0:
            hi = mid
        else:
            lo, flo = mid, fm
    return 0.5 * (lo + hi)


sw = common["switch_points_eV"]
assert close(sw["Ru_Os_equal_activity_delta"], bisect(-0.075, -0.05, "Ru", "Os"), 1e-12)
assert close(sw["Fe_Os_equal_activity_delta"], bisect(0.10, 0.125, "Fe", "Os"), 1e-12)
assert close(sw["Fe_Ru_equal_activity_delta"], bisect(0.10, 0.125, "Fe", "Ru"), 1e-12)

# ---- agent stopping efficiency ----------------------------------------------
src = rows(ROOT / "provenance/discover_v1/source_harness/DISCOVER_BOUNDARY_C1/data/discover_boundary_c1_uncapped_breakeven_audit.csv")
stable = [float(r["first_stable_CU"]) for r in src]
final = [float(r["final_CU"]) for r in src]
over = [float(r["overrun_CU"]) for r in src]


def median(v):
    s = sorted(v)
    n = len(s)
    return s[n // 2] if n % 2 else 0.5 * (s[n // 2 - 1] + s[n // 2])


stop = json.loads((HERE / "agent_stopping_efficiency.json").read_text(encoding="utf-8"))
assert len(src) == stop["runs"] == 20
assert close(stop["decision_stable_CU_median"], median(stable), 1e-12)
assert close(stop["final_CU_median"], median(final), 1e-12)
assert close(stop["post_stability_overrun_CU_median"], median(over), 1e-12)
assert stop["runs_with_positive_overrun"] == sum(v > 0 for v in over)
assert stop["runs_with_zero_overrun"] == sum(v == 0 for v in over)
assert close(stop["total_final_CU"], sum(final), 1e-12)
assert close(stop["total_post_stability_overrun_CU"], sum(over), 1e-12)
assert close(stop["fraction_total_compute_after_hindsight_stability"], sum(over) / sum(final), 1e-12)

print("PASS non-figure scientific upgrade audit")
print(f"NH3/MeOH/Au regret: {r_nh3:.6f}, {r_meoh:.6f}, 0")
print(f"pairwise chi: NH3={chi_nh3:.6f}, MeOH={chi_meoh:.6f}, Au={chi_au:.6f}")
print("descriptor correlation table: 5/5 rho cells reproduced")
print(f"Agent post-stability: {sum(v > 0 for v in over)}/20 runs; {sum(over)/sum(final):.3%} of total CU")
