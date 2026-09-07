# Figures

This directory is reserved for manuscript-ready figures generated from the frozen project outputs.

## Planned figure set

| Figure | Working title | Current status |
|---|---|---|
| F1 | NH3 atomic vs economic ranking | canonical logic frozen; image pending repository upload |
| F2 | Rolling Top-K rank correlation | canonical logic frozen; image pending repository upload |
| F3 | NH3 uncertainty / decision stability | canonical logic frozen; image pending repository upload |
| F4 | Fe / Ru / Os operating envelopes | canonical logic frozen; image pending repository upload |
| F5 | Ru backward-design activity sweep | canonical logic frozen; image pending repository upload |
| F6 | Scaling-manifold reachability | canonical logic frozen; image pending repository upload |
| F7 | CO2-to-MeOH recycle / separation economics | benchmark logic frozen; image pending repository upload |
| F8 | Methane accumulation / purge / leverage | benchmark logic frozen; image pending repository upload |
| F9 | Cross-reaction leverage | benchmark logic frozen; image pending repository upload |

The current scientific role and canonical values for each figure are documented in [`../docs/FIGURE_MAP.md`](../docs/FIGURE_MAP.md).

## Versioning rule

Any ammonia figure added here should state or encode **NH3-FINAL-1.1** provenance. Figures generated from NH3-FINAL-1.0 should be archived separately and not silently reused in the current manuscript.

Recommended filename convention:

```text
F01_atomic_vs_economic_NH3_FINAL_1_1.svg
F02_rolling_topk_NH3_FINAL_1_1.svg
...
```

For raster exports, keep the editable vector or source-data version alongside the PNG/TIFF whenever possible.

## Rank-preservation control (`rank_preservation_control/`)

The literature-calibrated Au/TiO2 CO-oxidation control is kept separate from the nine-figure manuscript map until final figure placement is decided.

| File | Content |
|---|---|
| `RP1_AuTiO2_rank_preservation_V1_1.svg` | mirror rank-flow figure showing exact preservation of the 2–6 nm activity order after fixed-condition physical propagation |

Source data: [`../data/rank_preservation_control_v1_1.csv`](../data/rank_preservation_control_v1_1.csv).

Current V1.1 headline values:

- activity order: **2 > 3 > 4 > 5 > 6 nm**;
- downstream catalyst-burden order: **2 > 3 > 4 > 5 > 6 nm**;
- Spearman rho = **1.000**;
- Kendall tau = **1.000**;
- pairwise inversions = **0**;
- 10,000/10,000 predefined literature-envelope draws preserve the full ranking;
- literature recalibration reduces the 6 nm / 2 nm required-mass ratio from **19.42x to 8.064x (-58.5%)** without changing the ordering.

## DISCOVER cross-model figures (`discover_cross_model/`)

Generated 2026-09-06/07 from `DISCOVER_CROSS_MODEL_V1` on the frozen DISCOVER V1 protocol (NH3-FINAL-1.1 ground truth, scorer unchanged).

| File | Content |
|---|---|
| `X_cross_model_curves_{anonymous,named}.png` | six-panel budget curves, three tiers |
| `X1`–`X6` | single panels: P(full decision), P(reachability), break-even error, CU to stable winner, unnecessary-CU fraction, regret |
| `X7_failure_mode_matrix.png` | 19 failure modes × model × variant |
| `X8_failure_by_budget_anonymous.png` | failure modes by budget, anonymous task |
| `X9_wilson_ci_pooled.png` | pooled / ≤300 CU / ≥500 CU outcomes with Wilson 95 % CI, all tiers (statistics page) |

## Negative control N2O figures (`negative_control_n2o/`)

Model N2O-NEGCTRL-0.2 unless suffixed `_V0_1`. F1 atomic-vs-economic rank; F2 rolling Top-K (N2O vs NH3-FINAL-1.1); F3 cost pools at each candidate's own optimum; F4 cost-vs-temperature envelopes; F5 Monte-Carlo rank preservation (1000 draws, ±0.30 eV).

## MeOH figures (`meoh/`)

`MeOH_F03_UpstreamToEconomicRanking_D01v3.png` — candidate-state upstream (STY per g Re) rank → economic (NPC, 2 % purge) rank, rebuilt 2026-09-07 from the frozen D01 v3 workbook (see `docs/MEOH_RANKING_INVERSION.md`). `MeOH_F01_ExplicitLoopEconomics_v3.0.png` (= manuscript Figure 7 source), `MeOH_F02_Purge_MethaneAccumulation_FINAL_v3.0.png` (Figure 8 source), `MeOH_SF01_ProductResolvedNetwork_v2.0.png` (supporting) are restored from the 2026-08-19 v1.0 archive.
