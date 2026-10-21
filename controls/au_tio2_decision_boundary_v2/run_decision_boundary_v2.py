"""Au/TiO2 decision-boundary analysis V2.0 (additive to the canonical fixed-condition control).

Pre-registered in docs/AU_TIO2_DECISION_BOUNDARY_PREREGISTRATION.md. The canonical control
(controls/au_tio2_rank_preservation_v1_1.py, data/rank_preservation_control_v1_1.csv) is read, never written.

Parts
  1. V2.0 per-candidate Monte Carlo: shared (n, m) as in the canonical control plus an independent lognormal
     activity prefactor per particle size.
  2. Channel ladder L0-L3:
       L0 inventory only (canonical numbers, read from the frozen CSV);
       L1 + price (analytic: common Au price and loading cannot differentiate; numeric check);
       L2 + lifetime/replacement: adjacent-pair flip thresholds, q* = n + m, 2-D (q, n + m) boundary map
          with the V2.0 per-candidate scatter overlaid;
       L3 + operating freedom: semi-open results read from data/rank_preservation_semiopen_v1_3_summary.csv;
       L2 + L3 combined: the semi-open objective with a lifetime factor (d / 2 nm)^-q, same seed, same draws, so
          that q = 0 must reproduce the committed 273-293 K moderate numbers exactly.
  3. Outputs under artifacts/au_tio2_decision_boundary_v2/ with FROZEN_HASHES.json.

Run from anywhere:  python controls/au_tio2_decision_boundary_v2/run_decision_boundary_v2.py
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import sys
from itertools import combinations
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CFG = json.loads((HERE / "config.json").read_text(encoding="utf-8"))
OUT = ROOT / "artifacts" / "au_tio2_decision_boundary_v2"
OUT.mkdir(parents=True, exist_ok=True)

D = np.array(CFG["candidate_diameters_nm"], dtype=float)
N_CAND = len(D)
PAIRS = list(combinations(range(N_CAND), 2))
ADJ = [(i, i + 1) for i in range(N_CAND - 1)]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_canonical_csv() -> list[dict]:
    with (ROOT / CFG["canonical_control_data"]).open(encoding="utf-8") as fh:
        return [{k: float(v) for k, v in row.items()} for row in csv.DictReader(fh)]


def spearman_from_cost(cost: np.ndarray) -> float:
    """Spearman rho between activity rank (2 nm best ... 6 nm worst, i.e. index order) and cost rank."""
    rank = np.argsort(np.argsort(cost)) + 1
    base = np.arange(1, len(rank) + 1)
    n = len(rank)
    return float(1.0 - 6.0 * ((rank - base) ** 2).sum() / (n * (n * n - 1)))


def inversion_pairs(cost: np.ndarray) -> list[tuple[int, int]]:
    """Pairs (i, j), i < j (so d_i < d_j, higher nominal activity at i), whose cost order is inverted."""
    return [(i, j) for i, j in PAIRS if cost[i] > cost[j]]


# ----------------------------------------------------------------------------------------------------------
# L0: canonical numbers
# ----------------------------------------------------------------------------------------------------------
canon = read_canonical_csv()
MASS_273 = np.array([r["required_catalyst_mass_mg"] for r in canon])
ACT_273 = np.array([r["mass_activity_umol_CO_gcat_s"] for r in canon])
BURDEN = np.array([r["procurement_burden_vs_best"] for r in canon])
assert np.allclose(np.round(MASS_273 / MASS_273.min(), 3), CFG["headline_assertions"]["l0_burden_vs_best"]), (
    "canonical burden ratios changed"
)

# ----------------------------------------------------------------------------------------------------------
# Part 1: V2.0 per-candidate Monte Carlo
# ----------------------------------------------------------------------------------------------------------
D_REF = CFG["reference_diameter_nm"]
SH = CFG["shared_exponents"]


def relative_activity(n: float, m: float) -> np.ndarray:
    """Mass activity relative to the 2.10 nm anchor under the canonical power law (dispersion cap at 1 kept)."""
    tof_scale = (D / D_REF) ** (-n)
    disp = np.minimum(1.0, 0.38 * (D_REF / D) ** m)
    return tof_scale * disp / 0.38


def mc_per_candidate(sigma: float, seed: int, draws: int, q: float = 0.0, n_fixed=None, m_fixed=None) -> dict:
    rng = np.random.default_rng(seed)
    full = 0
    rho_sum = 0.0
    pair_inv = {p: 0 for p in PAIRS}
    n_inv_hist = np.zeros(len(PAIRS) + 1, dtype=int)
    winner = np.zeros(N_CAND, dtype=int)
    log_mu = -0.5 * sigma * sigma
    for _ in range(draws):
        n = rng.uniform(SH["tof_exponent_min"], SH["tof_exponent_max"]) if n_fixed is None else n_fixed
        m = rng.uniform(SH["dispersion_exponent_min"], SH["dispersion_exponent_max"]) if m_fixed is None else m_fixed
        eps = rng.normal(log_mu, sigma, N_CAND) if sigma > 0 else np.zeros(N_CAND)
        activity = relative_activity(n, m) * np.exp(eps)
        cost = (1.0 / activity) * (D / D[0]) ** (-q)  # required mass / lifetime factor
        inv = inversion_pairs(cost)
        full += int(not inv)
        n_inv_hist[len(inv)] += 1
        for p in inv:
            pair_inv[p] += 1
        rho_sum += spearman_from_cost(cost)
        winner[int(np.argmin(cost))] += 1
    return {
        "sigma_ln": sigma,
        "q": q,
        "seed": seed,
        "draws": draws,
        "full_preservation": full / draws,
        "mean_spearman_rho": rho_sum / draws,
        "winner_2nm_probability": winner[0] / draws,
        "winner_distribution": {f"{D[i]:g}nm": int(winner[i]) for i in range(N_CAND)},
        "pairwise_inversion_rate": {f"{D[i]:g}/{D[j]:g}": pair_inv[(i, j)] / draws for i, j in PAIRS},
        "adjacent_inversion_rate": {f"{D[j]:g}/{D[i]:g}": pair_inv[(i, j)] / draws for i, j in ADJ},
        "inversion_count_distribution": {str(k): int(v) for k, v in enumerate(n_inv_hist)},
        "fully_inverted": n_inv_hist[len(PAIRS)] / draws,
        "partially_inverted": 1.0 - full / draws - n_inv_hist[len(PAIRS)] / draws,
    }


print("Part 1: V2.0 per-candidate Monte Carlo")
mc_rows = []
for sigma in CFG["per_candidate_scatter"]["sensitivity_sigma_ln"]:
    res = mc_per_candidate(sigma, CFG["mc_v2"]["seed"], CFG["mc_v2"]["draws"])
    res["primary"] = sigma == CFG["per_candidate_scatter"]["primary_sigma_ln"]
    mc_rows.append(res)
    print(
        f"  sigma={sigma:.2f}  full={res['full_preservation']:.4f}  rho={res['mean_spearman_rho']:.5f}  "
        f"adjacent={ {k: round(v, 4) for k, v in res['adjacent_inversion_rate'].items()} }"
    )
# shared-only reference (sigma = 0): reproduces the by-construction result of the canonical control
mc_shared_only = mc_per_candidate(0.0, CFG["mc_v2"]["seed"], CFG["mc_v2"]["draws"])
print(f"  sigma=0 (shared (n,m) only, as in the canonical control): full={mc_shared_only['full_preservation']:.4f}")

nominal_act = relative_activity(SH["nominal_tof_exponent"], SH["nominal_dispersion_exponent"])
point_estimate_order = [f"{D[i]:g} nm" for i in np.argsort(-nominal_act)]

with (OUT / "mc_v2_per_candidate.csv").open("w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(
        ["sigma_ln", "primary", "draws", "seed", "full_preservation", "mean_spearman_rho", "winner_2nm_probability",
         "fully_inverted", "partially_inverted"]
        + [f"inv_{D[j]:g}_over_{D[i]:g}" for i, j in ADJ]
        + [f"n_inversions_{k}" for k in range(len(PAIRS) + 1)]
    )
    for r in [mc_shared_only] + mc_rows:
        w.writerow(
            [r["sigma_ln"], r.get("primary", False), r["draws"], r["seed"], f"{r['full_preservation']:.4f}",
             f"{r['mean_spearman_rho']:.5f}", f"{r['winner_2nm_probability']:.4f}", f"{r['fully_inverted']:.4f}",
             f"{r['partially_inverted']:.4f}"]
            + [f"{r['adjacent_inversion_rate'][f'{D[j]:g}/{D[i]:g}']:.4f}" for i, j in ADJ]
            + [r["inversion_count_distribution"][str(k)] for k in range(len(PAIRS) + 1)]
        )

# ----------------------------------------------------------------------------------------------------------
# L1: price channel (analytic + numeric check)
# ----------------------------------------------------------------------------------------------------------
print("L1: price channel")
AU_FRAC = 0.0440
au_mass = MASS_273 * AU_FRAC
l1_rows = []
for p_au in (50.0, 80.0, 120.0):  # arbitrary common Au prices, USD per g: cancel in every ratio
    for c_support in (0.0, 0.5, 5.0):  # support/forming cost per g catalyst: scales with catalyst mass
        cost = au_mass * p_au + MASS_273 * c_support
        ratio = cost / cost[0]
        l1_rows.append([p_au, c_support] + [f"{x:.3f}" for x in ratio] + [spearman_from_cost(cost)])
        assert np.allclose(ratio, BURDEN, atol=5e-4), "price channel differentiated the candidates: it must not"
with (OUT / "l1_price_channel_check.csv").open("w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["au_price_common", "support_forming_cost_per_g_cat"] + [f"cost_ratio_{d:g}nm_vs_2nm" for d in D] + ["spearman"])
    w.writerows(l1_rows)
print("  cost ratio == canonical burden ratio for every common price and support cost (checked)")

# ----------------------------------------------------------------------------------------------------------
# L2: lifetime / replacement channel
# ----------------------------------------------------------------------------------------------------------
print("L2: lifetime channel")
adj_thresholds = {f"tau{D[j]:g}/tau{D[i]:g}": MASS_273[j] / MASS_273[i] for i, j in ADJ}
all_thresholds = {f"tau{D[j]:g}/tau{D[i]:g}": MASS_273[j] / MASS_273[i] for i, j in PAIRS}
q_star_pairs = {f"{D[j]:g}/{D[i]:g}": math.log(MASS_273[j] / MASS_273[i]) / math.log(D[j] / D[i]) for i, j in PAIRS}
q_star_nominal = SH["nominal_tof_exponent"] + SH["nominal_dispersion_exponent"]
for k, v in adj_thresholds.items():
    print(f"  flip threshold {k} > {v:.3f}")
print(f"  q* per pair (from canonical masses): { {k: round(v, 4) for k, v in q_star_pairs.items()} }")
exp_thr = CFG["headline_assertions"]["l2_adjacent_flip_thresholds"]
for (i, j), (k, v) in zip(ADJ, exp_thr.items()):
    assert abs(MASS_273[j] / MASS_273[i] - v) < 5e-4, f"threshold {k} drifted"
assert all(abs(v - q_star_nominal) < 2e-3 for v in q_star_pairs.values()), "q* is not common across pairs"

with (OUT / "l2_adjacent_flip_thresholds.csv").open("w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["pair_larger_over_smaller_nm", "mass_ratio", "lifetime_ratio_flip_threshold", "q_star_pair",
                "ln_mass_ratio"])
    for i, j in PAIRS:
        w.writerow([f"{D[j]:g}/{D[i]:g}", f"{MASS_273[j] / MASS_273[i]:.4f}", f"{MASS_273[j] / MASS_273[i]:.3f}",
                    f"{q_star_pairs[f'{D[j]:g}/{D[i]:g}']:.4f}", f"{math.log(MASS_273[j] / MASS_273[i]):.4f}"])

# 2-D boundary map: deterministic line q = n + m plus the V2.0 per-candidate MC on the grid
BM = CFG["boundary_map"]
print("  2-D boundary map (q, n + m) with per-candidate scatter")
map_rows = []
for nm in BM["nm_grid"]:
    # split n + m into (n, m) along the canonical nominal dispersion exponent, m = 1.0, so n = nm - 1
    n_fix, m_fix = nm - SH["nominal_dispersion_exponent"], SH["nominal_dispersion_exponent"]
    for q in BM["q_grid"]:
        res = mc_per_candidate(BM["sigma_ln"], BM["seed"], BM["draws_per_cell"], q=q, n_fixed=n_fix, m_fixed=m_fix)
        det = "preserved" if q < nm else ("fully_inverted" if q > nm else "degenerate")
        map_rows.append([q, nm, det, f"{res['full_preservation']:.4f}", f"{res['partially_inverted']:.4f}",
                         f"{res['fully_inverted']:.4f}", f"{res['winner_2nm_probability']:.4f}",
                         f"{res['mean_spearman_rho']:.4f}"])
with (OUT / "l2_boundary_map_q_vs_nm.csv").open("w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["q", "n_plus_m", "deterministic_region", "p_preserved", "p_partial", "p_fully_inverted",
                "p_winner_2nm", "mean_rho"])
    w.writerows(map_rows)

# the one-dimensional deterministic-plus-scatter cut at the canonical nominal n + m = 1.9
cut_rows = []
for q in np.round(np.arange(-1.0, 4.01, 0.1), 2):
    res = mc_per_candidate(CFG["per_candidate_scatter"]["primary_sigma_ln"], BM["seed"], BM["draws_per_cell"], q=float(q))
    cut_rows.append([q, f"{res['full_preservation']:.4f}", f"{res['partially_inverted']:.4f}",
                     f"{res['fully_inverted']:.4f}", f"{res['winner_2nm_probability']:.4f}"])
with (OUT / "l2_q_cut_shared_nm_sampled.csv").open("w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["q", "p_preserved", "p_partial", "p_fully_inverted", "p_winner_2nm"])
    w.writerows(cut_rows)

# ----------------------------------------------------------------------------------------------------------
# L3: semi-open results (read, not rerun) and the combined L2 + L3 case
# ----------------------------------------------------------------------------------------------------------
print("L3: semi-open operating freedom (read from the committed summary)")
with (ROOT / CFG["semiopen_summary"]).open(encoding="utf-8") as fh:
    semiopen = list(csv.DictReader(fh))
l3 = {f"{r['window']}|{r['stress']}": r for r in semiopen}
l3_primary = l3["primary_273_293K|moderate"]
l3_wide = l3["sensitivity_273_313K|moderate"]
assert abs(float(l3_primary["full_preservation_fraction"]) - CFG["headline_assertions"]["l3_semiopen_273_293_moderate_full_preservation"]) < 1e-9
assert abs(float(l3_wide["full_preservation_fraction"]) - CFG["headline_assertions"]["l3_semiopen_273_313_moderate_full_preservation"]) < 1e-9
print(f"  273-293 K moderate: {l3_primary['full_preservation_fraction']} full, rho {l3_primary['mean_spearman_rho']}")
print(f"  273-313 K moderate: {l3_wide['full_preservation_fraction']} full, rho {l3_wide['mean_spearman_rho']}")

# Combined L2 + L3: port of data/rank_preservation_semiopen_v1_3.py (same constants, same RNG stream) with the
# lifetime factor (d / 2 nm)^-q multiplying the catalyst-mass term. q = 0 must reproduce the committed numbers.
print("L2 + L3 combined")
T_REF = 273.15
R_GAS = 8.314
REACTIVE_MOLE_FRACTION = 0.22
O2_CO_REF = 21.0
PCO_REF = REACTIVE_MOLE_FRACTION / (1.0 + O2_CO_REF)
PO2_REF = REACTIVE_MOLE_FRACTION * O2_CO_REF / (1.0 + O2_CO_REF)
EA_D = np.array([2.2, 3.4, 4.8])
EA_KJ = np.array([25.4, 28.0, 33.7])
EA_BASE = np.polyval(np.polyfit(EA_D, EA_KJ, 1), D)
ALPHA_CO_RANGE = (0.05, 0.60)
ALPHA_O2_RANGE = (0.03, 0.40)
O2_CO_MIN, O2_CO_MAX = 1.0, 21.0
N_T, N_RATIO = 61, 81
STRESS = {"mild": (0.05, 1.0, 1), "moderate": (0.10, 2.0, 2), "strong": (0.20, 3.0, 3)}


def run_combined(tmax: float, seed: int, prefactor_cv: float, ea_sigma_kj: float, q: float, draws: int) -> dict:
    rng = np.random.default_rng(seed)
    temps = np.linspace(T_REF, tmax, N_T)
    ratios = np.geomspace(O2_CO_MIN, O2_CO_MAX, N_RATIO)
    heat_penalty = ((temps - temps[0]) / (temps[-1] - temps[0]))[:, None] ** 2
    oxygen_penalty = ((ratios - O2_CO_MIN) / (O2_CO_MAX - O2_CO_MIN))[None, :]
    pco = REACTIVE_MOLE_FRACTION / (1.0 + ratios)
    po2 = REACTIVE_MOLE_FRACTION * ratios / (1.0 + ratios)
    lifetime_factor = (D / D[0]) ** (-q)
    log_sigma = math.sqrt(math.log(1.0 + prefactor_cv ** 2))
    log_mu = -0.5 * log_sigma ** 2
    full = 0
    rho_sum = 0.0
    inv_sum = 0
    full_inv = 0
    pair_inv = {p: 0 for p in PAIRS}
    winner = np.zeros(N_CAND, dtype=int)
    for _ in range(draws):
        alpha_co = rng.uniform(*ALPHA_CO_RANGE)
        alpha_o2 = rng.uniform(*ALPHA_O2_RANGE)
        w_t = 10.0 ** rng.uniform(-1.5, 0.5)
        w_r = 10.0 ** rng.uniform(-1.5, 0.5)
        activity_factor = np.exp(rng.normal(log_mu, log_sigma, N_CAND))
        ea = np.clip(EA_BASE + rng.normal(0.0, ea_sigma_kj, N_CAND), 20.0, 45.0)
        pressure_factor = (pco / PCO_REF) ** alpha_co * (po2 / PO2_REF) ** alpha_o2
        best_cost = np.empty(N_CAND)
        for i in range(N_CAND):
            arr = np.exp((ea[i] * 1000.0 / R_GAS) * (1.0 / T_REF - 1.0 / temps))[:, None]
            activity = ACT_273[i] * activity_factor[i] * arr * pressure_factor[None, :]
            required_mass = MASS_273[i] * ACT_273[i] / activity
            objective = (required_mass / MASS_273[0]) * lifetime_factor[i] + w_t * heat_penalty + w_r * oxygen_penalty
            best_cost[i] = objective.min()
        inv = inversion_pairs(best_cost)
        full += int(not inv)
        inv_sum += len(inv)
        full_inv += int(len(inv) == len(PAIRS))
        for p in inv:
            pair_inv[p] += 1
        rho_sum += spearman_from_cost(best_cost)
        winner[int(np.argmin(best_cost))] += 1
    return {
        "q": q,
        "full_preservation_fraction": full / draws,
        "mean_spearman_rho": rho_sum / draws,
        "mean_pairwise_inversions": inv_sum / draws,
        "fully_inverted_fraction": full_inv / draws,
        "winner_2nm_probability": winner[0] / draws,
        "winner_distribution": {f"{D[i]:g}nm": int(winner[i]) for i in range(N_CAND)},
        "adjacent_inversion_rate": {f"{D[j]:g}/{D[i]:g}": pair_inv[(i, j)] / draws for i, j in ADJ},
    }


CL = CFG["combined_l2_l3"]
cv, ea_sig, off = STRESS[CL["stress"]]
seed_combined = CL["seed_base"] + off
combined_rows = []
for q in CL["q_values"]:
    res = run_combined(293.15, seed_combined, cv, ea_sig, q, CL["draws"])
    combined_rows.append(res)
    print(f"  q={q:.2f}  full={res['full_preservation_fraction']:.4f}  rho={res['mean_spearman_rho']:.5f}  "
          f"winner2nm={res['winner_2nm_probability']:.4f}  fully_inverted={res['fully_inverted_fraction']:.4f}")
q0 = next(r for r in combined_rows if r["q"] == 0.0)
assert abs(q0["full_preservation_fraction"] - CL["reproduction_check_q0_full_preservation"]) < 1e-9, (
    f"q=0 did not reproduce the committed semi-open result: {q0['full_preservation_fraction']}"
)
assert abs(round(q0["mean_spearman_rho"], 5) - CL["reproduction_check_q0_mean_rho"]) < 1e-9
print("  q = 0 reproduces the committed 273-293 K moderate semi-open numbers (checked)")

with (OUT / "l2_l3_combined_273_293K_moderate.csv").open("w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["q", "window", "stress", "seed", "draws", "full_preservation_fraction", "mean_spearman_rho",
                "mean_pairwise_inversions", "fully_inverted_fraction", "winner_2nm_probability"]
               + [f"inv_{D[j]:g}_over_{D[i]:g}" for i, j in ADJ])
    for r in combined_rows:
        w.writerow([r["q"], CL["window"], CL["stress"], seed_combined, CL["draws"],
                    f"{r['full_preservation_fraction']:.4f}", f"{r['mean_spearman_rho']:.5f}",
                    f"{r['mean_pairwise_inversions']:.4f}", f"{r['fully_inverted_fraction']:.4f}",
                    f"{r['winner_2nm_probability']:.4f}"]
                   + [f"{r['adjacent_inversion_rate'][f'{D[j]:g}/{D[i]:g}']:.4f}" for i, j in ADJ])

# ----------------------------------------------------------------------------------------------------------
# Summary, ladder table, hashes
# ----------------------------------------------------------------------------------------------------------
primary = next(r for r in mc_rows if r["primary"])
summary = {
    "version": CFG["version"],
    "point_estimate_order_nominal": point_estimate_order,
    "L0_inventory_only": {
        "burden_vs_best": [float(x) for x in np.round(MASS_273 / MASS_273.min(), 3)],
        "shared_exponent_mc_full_preservation": mc_shared_only["full_preservation"],
        "note": "strictly monotone by construction for any n + m > 0",
    },
    "V2_0_per_candidate_mc_primary": primary,
    "V2_0_per_candidate_mc_all_sigma": mc_rows,
    "L1_price": {
        "differentiates": False,
        "reason": "Au price and Au loading (4.40 wt%) are common to all sizes; support/forming cost scales with required catalyst mass; every cost ratio equals the canonical burden ratio",
    },
    "L2_lifetime": {
        "adjacent_flip_thresholds": {k: round(v, 3) for k, v in adj_thresholds.items()},
        "all_pair_flip_thresholds": {k: round(v, 3) for k, v in all_thresholds.items()},
        "q_star_nominal": q_star_nominal,
        "q_star_per_pair": {k: round(v, 4) for k, v in q_star_pairs.items()},
        "q_star_range_over_shared_exponents": [SH["tof_exponent_min"] + SH["dispersion_exponent_min"],
                                              SH["tof_exponent_max"] + SH["dispersion_exponent_max"]],
    },
    "L3_semiopen": {
        "primary_273_293K_moderate": {k: float(v) if k not in ("window", "stress") else v for k, v in l3_primary.items()},
        "sensitivity_273_313K_moderate": {k: float(v) if k not in ("window", "stress") else v for k, v in l3_wide.items()},
    },
    "L2_L3_combined_273_293K_moderate": combined_rows,
}
(OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

frozen = {
    "version": CFG["version"],
    "config_sha256": sha256(HERE / "config.json"),
    "runner_sha256": sha256(Path(__file__)),
    "canonical_control_data_sha256": sha256(ROOT / CFG["canonical_control_data"]),
    "semiopen_summary_sha256": sha256(ROOT / CFG["semiopen_summary"]),
    "outputs": {p.name: sha256(p) for p in sorted(OUT.glob("*.csv")) + [OUT / "summary.json"]},
}
(OUT / "FROZEN_HASHES.json").write_text(json.dumps(frozen, indent=2) + "\n", encoding="utf-8")
print("done ->", OUT)
