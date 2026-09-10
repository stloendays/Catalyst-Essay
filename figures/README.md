# Figures

This directory contains manuscript and supporting figures generated from the frozen project evidence.

Audit status: **2026-09-10 second-pass claim-to-evidence audit**. A figure is marked `LOCKED` only when the current canonical numerical evidence and a concrete figure asset are both present and the scientific role/caption boundary is fixed. `HOLD` means the scientific claim may be internally consistent but the direct source/provenance chain or final asset is not yet closed. `METRIC_EQUIVALENCE_NOT_ESTABLISHED` means the archived numerical result cannot be promoted because the exact historical metric implementation is not recoverable from the retained repository evidence; the current manuscript must remain qualitative for that comparison.

## Main manuscript figure set

| Figure | Working title | Current status |
|---|---|---|
| F1 | NH3 atomic vs economic ranking | **HOLD** — NH3-FINAL-1.1 values are frozen, but the direct current raw provenance and manuscript-ready asset are not present in this repository |
| F2 | Rolling Top-K rank correlation | **HOLD** — current rho/tau values are frozen; direct FINAL-1.1 source and final asset still need provenance closure |
| F3 | NH3 uncertainty / decision stability | **HOLD** — 79.9% / 28.2% / 94.0% are current headline values; direct FINAL-1.1 MC source and final asset are not present here |
| F4 | Fe / Ru / Os operating envelopes | **HOLD** — current operating-point claims are frozen; pressure-envelope source data and final asset still need to be linked/imported |
| F5 | Ru backward-design activity sweep | **HOLD** — 201.22x is current; activity-sweep source and final asset still need to be linked/imported |
| F6 | Scaling-manifold reachability | **HOLD** — 1.090x / 2.525x / 21.398 USD/t are current; direct scaling output and final asset still need to be linked/imported |
| F7 | CO2-to-MeOH catalyst-state ranking reshuffle | **LOCKED CURRENT ASSET** — direct D01 v3 workbook/CSV/script provenance and `MeOH_F03_UpstreamToEconomicRanking_D01v3.png` are present; a publication vector export may be added without changing the scientific lock |
| F8 | Methane accumulation / purge / selectivity leverage | **LOCKED** — GitHub Actions run 34449914480 rendered and verified `F08_MeOH_selectivity_recycle_D01v3.svg/.pdf/.png`; SHA-256 manifest is `F08_RENDER_SHA256.txt` and the canonical SVG blob is pinned in the figure registry. |
| F9A | Cross-reaction catalyst-to-process pathways | **QUALITATIVE-ONLY / METRIC_EQUIVALENCE_NOT_ESTABLISHED** — legacy 273–410 (~328 midpoint) is archived pre-FINAL-1.1 evidence and is excluded from the current manuscript; no substitute ratio is introduced |
| F9B | Au/TiO2 rank-preservation control | **LOCKED** — direct CSV, generator and canonical SVG are present; V1.3 remains a supporting annotation/SI result |

The current scientific role and canonical values are defined in [`../docs/FIGURE_MAP.md`](../docs/FIGURE_MAP.md). The detailed provenance audit is [`../docs/CLAIM_EVIDENCE_AUDIT_2026-09-10.md`](../docs/CLAIM_EVIDENCE_AUDIT_2026-09-10.md), with the second-pass exception recorded separately. The machine-readable state is [`../data/figure_lock_registry_2026-09-10.csv`](../data/figure_lock_registry_2026-09-10.csv).

## NH3 provenance requirement

The compact file [`../data/canonical_results_2026-09-06.csv`](../data/canonical_results_2026-09-06.csv) is the current manuscript-facing numerical snapshot for validated FINAL-1.1 quantities, but it is not a substitute for the frozen NH3-FINAL-1.1 raw output/generator. Before F1–F6 are marked locked, add an immutable provenance record for canonical run `outputs/nh3_final_20260905T134204Z`, including the relevant raw result paths/hashes and figure-generating inputs.

The cross-reaction rows in that compact CSV are now explicitly marked as **legacy pre-FINAL-1.1 normalization values on hold**. They are historical placeholders, not current manuscript evidence.

Any NH3 figure added here must state or encode **NH3-FINAL-1.1** provenance. NH3-FINAL-1.0 figures must remain historical and must not be silently reused.

Recommended filename convention:

```text
F01_atomic_vs_economic_NH3_FINAL_1_1.svg
F02_rolling_topk_NH3_FINAL_1_1.svg
...
```

For raster exports, keep the editable vector and source-data/generator alongside the PNG/TIFF whenever possible.

## MeOH figures (`meoh/`)

Current assets:

- `MeOH_F03_UpstreamToEconomicRanking_D01v3.png` — direct upstream STY-per-g-Re rank -> NPC-at-2%-purge rank reconstruction; locked F7 source.
- `MeOH_F01_ExplicitLoopEconomics_v3.0.png` — restored explicit-loop economics source.
- `MeOH_F02_Purge_MethaneAccumulation_FINAL_v3.0.png` — restored purge/methane-accumulation reference source for F8.
- `MeOH_SF01_ProductResolvedNetwork_v2.0.png` — supporting network figure.
- `render_F08_selectivity_recycle.R` — frozen-data renderer for final F8 SVG/PDF/PNG assets.

Direct source data and provenance are in `../data/meoh/`, including the frozen D01 v3 workbook, extracted candidate-ranking CSV, provenance JSON, purge robustness outputs and analysis scripts.

### Figure 8 locked render

The Figure 8 scientific composition remains the frozen specification in [`../docs/F8_METHANOL_FIGURE_LOCK_SPEC.md`](../docs/F8_METHANOL_FIGURE_LOCK_SPEC.md):

- **Panel A:** NPC versus purge across the four literature catalyst–temperature states, with 2% marked as the canonical source point;
- **Panel B:** dot/lollipop comparison of local economic leverage for STY, single-pass conversion and CH4 suppression at 5 wt% Re / 250 C.

GitHub Actions run **34449914480** rendered and verified:

- `F08_MeOH_selectivity_recycle_D01v3.svg`
- `F08_MeOH_selectivity_recycle_D01v3.pdf`
- `F08_MeOH_selectivity_recycle_D01v3.png`
- `F08_RENDER_SHA256.txt`

The render passed the frozen 396-level purge-envelope and leverage-value checks. No scientific calculation or metric selection was changed during rendering.

## Cross-reaction Figure 9A

The archived **273–410** ratio is not lockable as a current FINAL-1.1 result. GitHub Actions run **34449914480** searched full repository history under a conservative provenance rule and classified the result **METRIC_EQUIVALENCE_NOT_ESTABLISHED**: no pre-audit implementation of the historical NH3 TOF economic-leverage metric was recovered, while the frozen FINAL-1.1 config/output tree is not present in this repository.

F9A is therefore a **qualitative catalyst-to-process pathway panel** in the current manuscript. It may contrast NH3 activity–inventory/reactor-demand coupling with MeOH selectivity–feed-loss/purge/recycle coupling, but it must not plot 273–410 as current or substitute a newly defined cross-reaction ratio.

See [`../docs/CROSS_REACTION_LEVERAGE_PROVENANCE_POINTER.md`](../docs/CROSS_REACTION_LEVERAGE_PROVENANCE_POINTER.md) and [`../artifacts/f9a_ci/CROSS_REACTION_FINAL1_1_CI_ATTEMPT.md`](../artifacts/f9a_ci/CROSS_REACTION_FINAL1_1_CI_ATTEMPT.md).

## Rank-preservation control (`rank_preservation_control/`)

Canonical main-panel source:

- `RP1_AuTiO2_rank_preservation_V1_1.svg` — mirror rank-flow figure showing exact preservation of the 2–6 nm activity order after literature-calibrated fixed-condition physical propagation.

Source data: [`../data/rank_preservation_control_v1_1.csv`](../data/rank_preservation_control_v1_1.csv). Generator: [`../controls/au_tio2_rank_preservation_v1_1.py`](../controls/au_tio2_rank_preservation_v1_1.py).

V1.1 headline values:

- activity order = burden order = **2 > 3 > 4 > 5 > 6 nm**;
- Spearman rho = **1.000**;
- Kendall tau = **1.000**;
- pairwise inversions = **0**;
- 10,000/10,000 predefined literature-envelope draws preserve the full ranking;
- 6 nm / 2 nm required-mass ratio = **8.064x**.

V1.3 is a supporting semi-open robustness extension. It may appear as a compact F9B annotation or in Supporting Information, but it does not replace V1.1 as the canonical control.

## DISCOVER figures

### `discover_cross_model/`

These figures report the frozen DISCOVER V1 cross-model benchmark and remain valid historical/canonical V1 evidence. The manuscript interpretation now also includes the completed DISCOVER-BOUNDARY-C1 extension.

### `discover_boundary_c1/`

Current C1 assets:

- `figA_delta_pfull_vs_CU.png`
- `figB_strong_efficiency.png`
- `figC_pfull_vs_CU.png`
- `figD_cu_to_full_distribution.png`
- `figP1_pfull_vs_CU_cross_model.png`
- `figP2_175CU_recovery.png`
- `figP3_225CU_control.png`
- `figP4_cu_to_full_and_failure_taxonomy.png`

These are supporting Agent figures rather than a new tenth main scientific figure under the current nine-figure architecture. The central C1 claim is that the below-threshold adaptive decision-recovery advantage is model-tier dependent: at 175 CU strong/mini/nano complete **19/20 / 0/20 / 0/20**, while at 225 CU they complete **20/20 / 6/20 / 0/20**; fixed-VOI D reaches the full decision at **206 CU**.

## Locking rule

A figure is final only when all four items are present:

1. canonical numerical source;
2. generator or immutable provenance pointer;
3. manuscript-ready asset, preferably vector plus raster export;
4. caption/claim wording consistent with the evidence boundary.

Do not mark a figure locked solely because a visually finished PNG exists.
