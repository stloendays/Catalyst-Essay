"""Exploratory semi-open Au/TiO2 rank-preservation stress test (V1.3).

This does NOT replace frozen/canonical V1.1. It tests whether the 2-6 nm
Au/TiO2 ordering survives when operating conditions are allowed to move
within literature-supported low-temperature CO-oxidation ranges.

Important modeling choice:
At fixed plant feed duty and target conversion, catalyst inventory/reactor
volume and space velocity are not independent degrees of freedom. Allowing
both required catalyst mass and GHSV to vary independently would double-count
residence time. Therefore this script optimizes T and O2/CO ratio explicitly;
the resulting required catalyst mass is the inverse residence-time / relative
space-velocity coordinate at fixed duty.

The scalar objective is a family of monotone robustness objectives, not an
industrial TEA:

    J = m_required / m_ref + w_T * H(T) + w_R * O(O2/CO)

w_T and w_R are swept randomly over a broad log-uniform range; they are not
fitted to preserve the ranking.

Literature anchors used in the report:
- Janssens et al., J Catal 240 (2006) 108-113, DOI 10.1016/j.jcat.2006.03.008
  (V1.1 absolute-rate anchor, 273.15 K, 1% CO / 21% O2 / 78% Ar).
- Shao et al., Small Methods 2 (2018) 1800273, DOI 10.1002/smtd.201800273
  (Ea = 25.4, 28.0, 33.7 kJ/mol for 2.2, 3.4, 4.8 nm; 253-293 K;
   1% CO / 20% O2 / 79% He; 20,000 mL gcat^-1 h^-1).
- Diemant et al., ChemPhysChem 22 (2021) 542-552,
  DOI 10.1002/cphc.202000960 and cited low-T powder studies
  (low-temperature empirical reaction-order ranges used as stress bounds).
- Emmanuel et al., J Catal 369 (2019) 175-180,
  DOI 10.1016/j.jcat.2018.10.038
  (monotonic smaller-is-more-active ordering across 80/170 C, 0.06-1.5 mbar,
   and multiple O2:CO ratios over ca. 1.5-6 nm).

Outputs data/rank_preservation_semiopen_v1_3_summary.csv.
"""
from __future__ import annotations

import csv
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "rank_preservation_semiopen_v1_3_summary.csv"

DIAMETER_NM = np.array([2., 3., 4., 5., 6.])
ACTIVITY_273 = np.array([9.6548, 4.4686, 2.5869, 1.6930, 1.1973])
MASS_273_MG = np.array([19.505, 42.143, 72.797, 111.235, 157.284])

T_REF = 273.15
R = 8.314
REACTIVE_MOLE_FRACTION = 0.22
O2_CO_REF = 21.0
PCO_REF = REACTIVE_MOLE_FRACTION / (1.0 + O2_CO_REF)
PO2_REF = REACTIVE_MOLE_FRACTION * O2_CO_REF / (1.0 + O2_CO_REF)

# Shao et al. 2018 apparent Ea points.
EA_D = np.array([2.2, 3.4, 4.8])
EA_KJ = np.array([25.4, 28.0, 33.7])
EA_COEF = np.polyfit(EA_D, EA_KJ, 1)
EA_BASE = np.polyval(EA_COEF, DIAMETER_NM)

# Low-temperature empirical reaction-order bounds collected in Diemant 2021
# from Au/TiO2 powder studies in/near the 273-313 K regime.
ALPHA_CO_RANGE = (0.05, 0.60)
ALPHA_O2_RANGE = (0.03, 0.40)

# Near-stoichiometric to strongly O2-rich envelope used in Au/TiO2 literature.
O2_CO_MIN = 1.0
O2_CO_MAX = 21.0

STRESS_LEVELS = {
    "mild": {"prefactor_cv": 0.05, "ea_sigma_kj": 1.0},
    "moderate": {"prefactor_cv": 0.10, "ea_sigma_kj": 2.0},
    "strong": {"prefactor_cv": 0.20, "ea_sigma_kj": 3.0},
}

WINDOWS = {
    "primary_273_293K": {"tmax": 293.15, "seed": 20260907},
    "sensitivity_273_313K": {"tmax": 313.15, "seed": 20260908},
}

N_DRAWS = 10_000
N_T = 61
N_RATIO = 81


def rank_from_cost(cost: np.ndarray) -> np.ndarray:
    return np.argsort(np.argsort(cost)) + 1


def spearman_from_rank(rank: np.ndarray) -> float:
    base = np.arange(1, len(rank) + 1)
    d2 = ((rank - base) ** 2).sum()
    n = len(rank)
    return float(1.0 - 6.0 * d2 / (n * (n * n - 1)))


def inversion_count(rank: np.ndarray) -> int:
    n = len(rank)
    return sum(rank[i] > rank[j] for i in range(n) for j in range(i + 1, n))


def run_window(name: str, tmax: float, seed: int, stress: str, prefactor_cv: float, ea_sigma_kj: float) -> dict:
    rng = np.random.default_rng(seed + {"mild": 1, "moderate": 2, "strong": 3}[stress])
    temps = np.linspace(T_REF, tmax, N_T)
    ratios = np.geomspace(O2_CO_MIN, O2_CO_MAX, N_RATIO)

    heat_penalty = ((temps - temps[0]) / (temps[-1] - temps[0]))[:, None] ** 2
    oxygen_penalty = ((ratios - O2_CO_MIN) / (O2_CO_MAX - O2_CO_MIN))[None, :]

    pco = REACTIVE_MOLE_FRACTION / (1.0 + ratios)
    po2 = REACTIVE_MOLE_FRACTION * ratios / (1.0 + ratios)

    full = 0
    rho_ge_09 = 0
    rho_sum = 0.0
    inv_sum = 0.0
    max_inv = 0
    min_rho = 1.0

    log_sigma = np.sqrt(np.log(1.0 + prefactor_cv**2))
    log_mu = -0.5 * log_sigma**2

    for _ in range(N_DRAWS):
        alpha_co = rng.uniform(*ALPHA_CO_RANGE)
        alpha_o2 = rng.uniform(*ALPHA_O2_RANGE)

        # Generic monotone process-penalty weights, deliberately not fitted.
        w_t = 10.0 ** rng.uniform(-1.5, 0.5)
        w_r = 10.0 ** rng.uniform(-1.5, 0.5)

        activity_factor = np.exp(rng.normal(log_mu, log_sigma, len(DIAMETER_NM)))
        ea = np.clip(EA_BASE + rng.normal(0.0, ea_sigma_kj, len(DIAMETER_NM)), 20.0, 45.0)

        pressure_factor = (pco / PCO_REF) ** alpha_co * (po2 / PO2_REF) ** alpha_o2

        best_cost = []
        for i in range(len(DIAMETER_NM)):
            arr = np.exp((ea[i] * 1000.0 / R) * (1.0 / T_REF - 1.0 / temps))[:, None]
            activity = ACTIVITY_273[i] * activity_factor[i] * arr * pressure_factor[None, :]
            required_mass = MASS_273_MG[i] * ACTIVITY_273[i] / activity

            # At fixed feed duty, smaller required mass means higher achievable
            # space velocity; do not add a second independent GHSV variable.
            objective = required_mass / MASS_273_MG[0] + w_t * heat_penalty + w_r * oxygen_penalty
            best_cost.append(float(objective.min()))

        rank = rank_from_cost(np.asarray(best_cost))
        rho = spearman_from_rank(rank)
        inv = inversion_count(rank)

        full += int(inv == 0)
        rho_ge_09 += int(rho >= 0.9)
        rho_sum += rho
        inv_sum += inv
        max_inv = max(max_inv, inv)
        min_rho = min(min_rho, rho)

    return {
        "window": name,
        "stress": stress,
        "n_draws": N_DRAWS,
        "temperature_min_K": T_REF,
        "temperature_max_K": tmax,
        "O2_CO_min": O2_CO_MIN,
        "O2_CO_max": O2_CO_MAX,
        "prefactor_cv": prefactor_cv,
        "ea_sigma_kJ_mol": ea_sigma_kj,
        "full_preservation_fraction": full / N_DRAWS,
        "mean_spearman_rho": rho_sum / N_DRAWS,
        "fraction_rho_ge_0_9": rho_ge_09 / N_DRAWS,
        "mean_pairwise_inversions": inv_sum / N_DRAWS,
        "max_pairwise_inversions_observed": max_inv,
        "min_spearman_rho_observed": min_rho,
    }


def main() -> None:
    rows = []
    for wname, wcfg in WINDOWS.items():
        for sname, scfg in STRESS_LEVELS.items():
            rows.append(run_window(wname, wcfg["tmax"], wcfg["seed"], sname, **scfg))

    with OUT.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    for row in rows:
        print(row)


if __name__ == "__main__":
    main()
