"""Partial-relaxation robustness test for the Au/TiO2 rank-preservation control.

This script does NOT replace or modify frozen V1.1. It asks how much
candidate-specific downstream freedom can be introduced before the V1.1
particle-size ranking materially changes.

Baseline downstream burden = required catalyst mass from
rank_preservation_control_v1_1.csv.

For each candidate i, apply an independent multiplicative downstream factor
f_i ~ Uniform(1-delta, 1+delta). This deliberately permits candidate-specific
process/equipment advantages or penalties without correlating them with
activity. The factor is a robustness envelope, not a fitted physical model.

Outputs rank-preservation statistics for a sweep of delta values.
"""
from __future__ import annotations

import csv
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent
BASE = ROOT / "rank_preservation_control_v1_1.csv"
OUT = ROOT / "rank_preservation_partial_relaxation.csv"

N_DRAWS = 100_000
BASE_SEED = 20260907
DELTAS = [0.10, 0.15, 0.17, 0.20, 0.25, 0.30, 0.40]


def load_required_mass() -> np.ndarray:
    vals = []
    with BASE.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            vals.append(float(row["required_catalyst_mass_mg"]))
    return np.asarray(vals, dtype=float)


def guaranteed_delta(mass: np.ndarray) -> tuple[float, list[float]]:
    ratios = mass[1:] / mass[:-1]
    thresholds = ((ratios - 1.0) / (ratios + 1.0)).tolist()
    return min(thresholds), thresholds


def run_delta(mass: np.ndarray, delta: float) -> dict[str, float | int]:
    rng = np.random.default_rng(BASE_SEED + int(round(delta * 1000)))
    factors = rng.uniform(1.0 - delta, 1.0 + delta, size=(N_DRAWS, len(mass)))
    burden = mass[None, :] * factors

    # rank 1 = lowest downstream burden; no ties for continuous random factors
    ranks = np.argsort(np.argsort(burden, axis=1), axis=1) + 1
    base_rank = np.arange(1, len(mass) + 1)

    full = np.all(ranks == base_rank[None, :], axis=1)

    # Spearman rho for n=5 without ties.
    d2 = ((ranks - base_rank[None, :]) ** 2).sum(axis=1)
    n = len(mass)
    rho = 1.0 - 6.0 * d2 / (n * (n * n - 1))

    inversions = np.zeros(N_DRAWS, dtype=int)
    for i in range(n):
        for j in range(i + 1, n):
            inversions += ranks[:, i] > ranks[:, j]

    return {
        "delta": delta,
        "n_draws": N_DRAWS,
        "full_preservation_fraction": float(full.mean()),
        "mean_spearman_rho": float(rho.mean()),
        "median_spearman_rho": float(np.median(rho)),
        "fraction_rho_ge_0_9": float((rho >= 0.9).mean()),
        "mean_pairwise_inversions": float(inversions.mean()),
        "fraction_inversions_le_1": float((inversions <= 1).mean()),
        "max_pairwise_inversions_observed": int(inversions.max()),
    }


def main() -> None:
    mass = load_required_mass()
    guarantee, thresholds = guaranteed_delta(mass)
    print(f"Analytical full-order guarantee for arbitrary candidate-specific factors: delta < {guarantee:.6f}")
    print("Adjacent-pair thresholds:", ", ".join(f"{x:.6f}" for x in thresholds))

    rows = [run_delta(mass, delta) for delta in DELTAS]
    fieldnames = list(rows[0])
    with OUT.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    for row in rows:
        print(row)


if __name__ == "__main__":
    main()
