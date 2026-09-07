# CO2-to-MeOH: candidate-state upstream ranking → economic ranking (D01 v3)

Restored 2026-09-07. The 2026-08-19 v1.0 and 2026-08-22 v2.2 archives contain the MeOH inversion evidence only as Figure 11
panel D ("economic ranking flips with operating temperature") and the workbook column `rank within T`; no dedicated
upstream-rank → economic-rank figure existed. `figures/meoh/MeOH_F03_UpstreamToEconomicRanking_D01v3.png` is rebuilt from the
frozen workbook `data/meoh/MeOH_D01_ExplicitRecycleSeparationEconomics_v3.0.xlsx` (sheets Candidate_Inputs, Purge_Sweep at
2 % purge, Methanol_Leverage) by `data/meoh/make_meoh_ranking_figure.py`; SHA-256 of the workbook is in the provenance JSON.

Sources: catalyst data Gothe et al., ACS Catal. 2025, Table 3 (Re/TiO2, 100 bar, CO2/H2 = 1:4, 500 °C prereduction);
process anchor Processes 2022, 10, 1535 (explicit loop, NPC at 2 % purge, calibration error −0.01 %).

| candidate | STY (g MeOH / g Re / h) | X_CO2 | S_MeOH | S_CH4 | upstream rank (STY) | NPC €/t (2 % purge) | economic rank |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1 wt% Re, 250 °C | 65 | 0.23 | 0.97 | 0.03 | **1** | 975 | 3 |
| 1 wt% Re, 200 °C | 55 | 0.19 | 0.99 | 0.00 | 2 | 967 | 2 |
| 5 wt% Re, 200 °C | 18 | 0.33 | 0.97 | 0.03 | 3 | **943** | **1** |
| 5 wt% Re, 250 °C | 16 | 0.40 | 0.74 | 0.25 | 4 | 1258 | 4 |

- Upstream winner (intrinsic productivity, STY per g Re) 1 wt% Re / 250 °C → economic rank 3; economic winner is 5 wt% Re / 200 °C.
- Spearman ρ = 0.20, Kendall τ = 0.00, 3 of 6 pairs inverted (1%-200 vs 5%-200; 1%-200 vs 1%-250; 5%-200 vs 1%-250).
- The same metrics hold if the upstream metric is single-pass yield X·S or STY per g catalyst (ρ = 0.20, τ = 0, 3/6), but then the
  upstream winner coincides with the economic winner; the inversion at the top is specific to the *intrinsic per-Re* metric.
- Mechanism: cost follows CH4 selectivity (H2 feed loss, loop inert accumulation, purge), not productivity: 5 wt% Re / 250 °C has
  the highest conversion (0.40) and the highest cost (1258 €/t) because S_CH4 = 0.25 raises the loop non-H2/CO2 fraction to 0.52
  and H2 feed cost to 886 €/t. Local leverage at 5 wt% Re / 250 °C: STY 0.00289, conversion 0.0588, CH4 suppression 0.376.
- Boundary: NPC is a near-full-plant cost (H2/CO2 feed + compression + equipment ACC + direct OPEX residual); Re purchase price is
  excluded by design; T and P are measured points, not re-optimized. This is the selectivity–recycle pathway case of the paper.

## Purge invariance and per-candidate purge reoptimization (added 2026-09-07)

The source loop exposes one process variable, the purge fraction; the D01 v3 workbook sweeps it from 0.5 % to 40 % for every state
(396 levels, `data/meoh/meoh_purge_robustness_D01v3.csv`, summary JSON alongside, script `meoh_purge_robustness.py`).

| purge range | economic order | rho | inversions |
|---|---|---:|---:|
| 0.5–0.9 % | 1%-200 > 5%-200 > 1%-250 > 5%-250 | 0.40 | 2/6 |
| 1.0–2.8 % (incl. canonical 2 %) | 5%-200 > 1%-200 > 1%-250 > 5%-250 | 0.20 | 3/6 |
| 2.9–14.3 % | 5%-200 > 1%-250 > 1%-200 > 5%-250 | 0.40 | 2/6 |
| 14.4–21.3 % | 5%-200 > 1%-250 > 5%-250 > 1%-200 | 0.00 | 3/6 |
| 21.4–40 % | 5%-200 > 5%-250 > 1%-250 > 1%-200 | −0.60 | 4/6 |

- The intrinsic per-Re winner (1 wt% Re / 250 °C) is never the economic winner at any purge level; the highest-conversion state
  (5 wt% Re / 250 °C) is never the economic winner; rho ≤ 0.40 and ≥ 2/6 pairs inverted everywhere.
- Per-candidate purge reoptimization (the MeOH analogue of NH3 candidate-specific reoptimization): every state's NPC minimum lies at
  the 0.5 % lower bound (895 / 907 / 918 / 1233 €/t for 1%-200 / 5%-200 / 1%-250 / 5%-250), a boundary optimum, so the 2 %
  source-anchored comparison remains canonical and the sweep is reported as robustness.
- Design logic of the NH3/MeOH pair: NH3 reoptimizes T / P / T_sep per catalyst identity (activity → inventory → severity channel);
  MeOH holds T / P at the four measured points (no T/P kinetic model exists) and reoptimizes the loop variable per state
  (selectivity → feed loss / accumulation / purge / recycle channel). The two cases are complementary tests of two channels, not
  the same protocol at two fidelities.
