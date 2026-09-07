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
