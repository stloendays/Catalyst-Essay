# Non-figure upgrades on NH3-FINAL-1.2

The NH3 rows of this folder's decision-regret, transfer-index, cost-MC and descriptor-sensitivity outputs, recomputed on
NH3-FINAL-1.2 (canonical run `nh3_final_1_2_20261013`, `provenance/nh3_final_1_2/`). The file names are those of the
1.1 files one level up. The MeOH and Au/TiO2 rows do not depend on the ammonia model and are copied verbatim from the 1.1
files.

## Commands

    set NH3_MODEL=1.2
    set NH3_HARNESS_1_2=<repo>\provenance\nh3_final_1_2\source_harness      (optional; this is the default)
    python analysis/nonfigure_upgrades_2026_09_29/reproduce_nh3_cost_mc.py          (about 45 s; --write regenerates the summary)
    python analysis/nonfigure_upgrades_2026_09_29/reproduce_nonfigure_upgrades.py   (about 10 s)
    python analysis/nonfigure_upgrades_2026_09_29/validate_nonfigure_upgrades.py

With `NH3_MODEL=1.1` (the default) the same three scripts reproduce the committed 1.1 files: `git diff` is empty, and the
1.1 draw table is byte-identical to the one the pre-port script writes. No response surface is built. The cost Monte
Carlo re-optimizes the Fe and Ru state vectors at their canonical E_N over all 14,510 process states, as in 1.1.

## Key numbers, NH3-FINAL-1.1 → NH3-FINAL-1.2

| Quantity | 1.1 | 1.2 |
|---|---:|---:|
| Fe / Ru feasible cost (USD t⁻¹) | 15.2917 / 22.0306 | 11.5158 / 16.6327 |
| NH3 decision regret R = (C_Ru − C_Fe)/C_Fe | 44.07 % | 44.43 % |
| Cost-side MC (5,000 draws, seed 20260920): R > 0 | 5,000 / 5,000 | 5,000 / 5,000 |
| R p05 / median / p95 | 30.48 / 40.89 / 54.25 % | 31.52 / 42.21 / 56.99 % |
| R min / max | 25.35 / 64.54 % | 27.37 / 66.24 % |
| Ru − Fe gap: min; p05 / median / p95 (USD t⁻¹) | 2.382; 3.488 / 7.110 / 11.379 | 1.995; 2.898 / 5.464 / 8.780 |
| Fe cost p05 / median / p95 (USD t⁻¹) | 9.596 / 17.546 / 24.819 | 7.310 / 13.178 / 18.522 |
| Ru cost p05 / median / p95 (USD t⁻¹) | 13.241 / 24.919 / 35.478 | 10.405 / 18.812 / 26.780 |
| Optimum pressure in the MC draws, Fe / Ru, median (p05–p95) | 175 (170–195) / 385 (220–430) bar | 105 (100–110) / 215 (170–250) bar |
| Atomic-reference log10 TOF at 673 K, Ru / Fe | −3.4512 / −5.3100 | −2.4552 / −5.2380 |
| Activity ratio s_Ru / s_Fe | 72.24 | 606.50 |
| Cost ratio J_Ru / J_Fe | 1.4407 | 1.4443 |
| Pairwise transfer index χ (Ru vs Fe) | +0.0853 | +0.0574 |
| Descriptor copula, ρ = 0: P(Ru > Os > Fe) | 40.40 % | 40.64 % |
| ρ = 0: atomistic top-1 Ru / Os / Fe | 45.98 / 43.32 / 10.71 % | 44.99 / 45.50 / 9.51 % |
| ρ = 0.9: P(Ru > Os > Fe) | 36.29 % | 36.23 % |
| ρ = 0.9: atomistic top-1 Ru / Os / Fe | 39.72 / 38.61 / 21.68 % | 39.42 / 43.63 / 16.95 % |
| Frozen 1,000-draw descriptor MC: atomistic winner Ru / Os / Fe | 46.5 / 42.3 / 11.2 % | 47.4 / 43.5 / 9.1 % |
| Common-shift window that keeps Ru > Os > Fe | −0.0573 < δE_N < +0.1030 eV | −0.0298 < δE_N < +0.1302 eV |
| Switch points Ru=Os / Fe=Os / Fe=Ru | −0.0573 / +0.1030 / +0.1107 eV | −0.0298 / +0.1302 / +0.1379 eV |
| Peak of the 673 K one-descriptor volcano (0.005 eV grid) | −1.18 eV | −1.15 eV |
| MeOH R / χ; Au/TiO2 R / χ | 1.93 % / +0.0149; 0 / −1.0000 | unchanged |

The 673 K volcano peak moved from −1.18 to −1.15 eV, which puts it between Ru (−1.1333 eV) and Os (−1.1095 eV). Two
consequences follow.

- **Atomistic top-1 at ρ = 0.** Ru and Os are nearly tied, with Os marginally ahead: Os 45.50 % against Ru 44.99 % on the
  committed 10⁵-draw stream. A 10⁷-draw numpy check of the same marginals (`default_rng(20261013)`) gives Os 45.37 % against
  Ru 45.11 %, a 0.26 pp gap (about 9 SE). In 1.1, Ru led clearly: 46.00 % against 43.18 % on the same check.
- **Most frequent full order.** This is now Os > Ru > Fe, not the canonical Ru > Os > Fe:

  | Stream | Os > Ru > Fe | Ru > Os > Fe |
  |---|---:|---:|
  | Committed stream, ρ = 0 | 41.10 % | 40.64 % |
  | 10⁷-draw numpy check, ρ = 0 | 40.87 % | 40.71 % (gap 0.16 pp, about 5.5 SE) |
  | Committed stream, ρ = 0.9 | 43.03 % | 36.23 % |

  On the committed stream, Os > Ru > Fe is the most frequent order at every ρ from 0 to 0.9. In 1.1, Ru > Os > Fe led at
  ρ = 0 (40.40 % against 38.40 %) and ρ = 0.25 (39.10 % against 38.21 %); Os > Ru > Fe led from ρ = 0.5.

`reproduce_nonfigure_upgrades.py` prints the frequencies of all six full orders for each ρ on the committed stream.
The CSV keeps its six 1.1 columns.

## What was re-derived and how

- **Decision regret and χ.** These are computed from the 1.2 `results.json`. The upstream winner is `activity_order[0]` (Ru) and
  the downstream winner is `feasible_economic_order[0]` (Fe). s is the ratio of the atomic-reference TOFs
  (`activity_logTOF`, 673 K, 24.5 / 74.25 / 1 bar N₂ / H₂ / NH₃). For 1.1 this is exactly `fig1_metals.csv` logTOF_673K.
  In 1.2 the reference gas activities carry the Newton–Cooper fugacities, and the NH₃ formation free energy is the
  Gillespie–Beattie value. Together these raise Ru's reference TOF by a factor of 9.9 and Fe's by a factor of 1.18.
- **Cost-side MC.** It uses the same seed, priors, block draw order and objective as 1.1. The harness core, manifest
  (F_CAL 74,351.6) and process states are those of 1.2. The baseline gate reproduces the 1.2 anchors (Fe 11.515783597179267, Ru
  16.632749358902807) to 1e-10. There was no earlier 1.2 summary, so `nh3_cost_mc_regret_summary.json` is written on the
  first run, and later runs gate against it to 1e-12. It keeps the 1.1 schema. The 1.1 `validation_against_existing_summary` block is replaced by
  `gap_and_cost_quantiles`, and the summary adds `model`, `run`, `deterministic_regret` and the optimum-pressure quantiles. The draw table
  `nh3_cost_mc_draws_reproduced.csv` is not committed (as for 1.1); its SHA-256 on the generating machine is recorded.
- **Kinetic extract.** `nh3_cost_mc_repro_inputs.json` is a byte copy of the 1.1 extract. 1.2 uses the same workbook
  (SHA-256 fc259c53…). Re-parsing it with the 1.2 harness gives the same gas records, frequencies and activity order. The
  scaling fits agree to ≤ 2.2e-16 (scipy linregress last bit).
- **Descriptor-correlation table.** It uses the same LCG stream, seeds and marginals (Fe σ 0.2271 eV, others ±0.15 eV).
  These are confirmed equal in the 1.2 manifest and harness. Only the volcano is swapped to the 1.2
  `closure/scaling_reachability.csv`.
- **Common-mode switch points.** The 1.1 bisection brackets ([−0.075, −0.05] and [0.10, 0.125] eV) were picked around the
  1.1 roots, and the 1.2 roots lie outside them. Brackets now come from a 0.0025 eV scan of [−0.6, +0.6] eV, which finds
  one root per pair, followed by the same 80 bisection steps. On 1.1 this reproduces the committed switch points to 1e-12.
