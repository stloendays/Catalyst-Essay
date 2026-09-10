# Figures

This directory contains manuscript and supporting figures generated from the frozen project evidence.

Audit status: **2026-09-10 final claim-to-evidence closure**. A figure is marked `LOCKED` only when the current canonical numerical evidence and a concrete figure asset are both present and the scientific role/caption boundary is fixed. `METRIC_EQUIVALENCE_NOT_ESTABLISHED` means an archived numerical result cannot be promoted because the exact historical metric implementation is not recoverable from the retained evidence; the current manuscript remains qualitative for that comparison.

## Main manuscript figure set

| Figure | Working title | Current status |
|---|---|---|
| F1 | NH3 atomic vs economic ranking | **LOCKED** — canonical NH3-FINAL-1.1 source bundle validated; SVG `F1_ranking_propagation_1_1.svg` pinned by source SHA-256 and Git blob SHA |
| F2 | Rolling Top-K rank correlation | **LOCKED** — `rolling_topk_rho_tau.csv` and canonical FINAL-1.1 SVG are content-addressed and validated |
| F3 | NH3 uncertainty / decision stability | **LOCKED** — FINAL-1.1 MC source files and canonical SVG are content-addressed and validated |
| F4 | Fe / Ru / Os operating envelopes | **LOCKED** — FINAL-1.1 pressure/CAPEX record, canonical result bundle and SVG are content-addressed and validated |
| F5 | Ru backward-design activity sweep | **LOCKED** — FINAL-1.1 break-even sweep and canonical SVG are content-addressed and validated |
| F6 | Scaling-manifold reachability | **LOCKED** — FINAL-1.1 scaling output and canonical SVG are content-addressed and validated |
| F7 | CO2-to-MeOH catalyst-state ranking reshuffle | **LOCKED CURRENT ASSET** — direct D01 v3 workbook/CSV/script provenance and `MeOH_F03_UpstreamToEconomicRanking_D01v3.png` are present; a publication vector export may be added without changing the scientific lock |
| F8 | Methane accumulation / purge / selectivity leverage | **LOCKED** — GitHub Actions run 34449914480 rendered and verified `F08_MeOH_selectivity_recycle_D01v3.svg/.pdf/.png`; SHA-256 manifest is `F08_RENDER_SHA256.txt` and the canonical SVG blob is pinned in the figure registry |
| F9A | Cross-reaction catalyst-to-process pathways | **QUALITATIVE-ONLY / METRIC_EQUIVALENCE_NOT_ESTABLISHED** — legacy 273–410 (~328 midpoint) is archived pre-FINAL-1.1 evidence and is excluded from the current manuscript; no substitute ratio is introduced |
| F9B | Au/TiO2 rank-preservation control | **LOCKED** — direct CSV, generator and canonical SVG are present; V1.3 remains a supporting annotation/SI result |

The current scientific role and canonical values are defined in [`../docs/FIGURE_MAP.md`](../docs/FIGURE_MAP.md). The detailed provenance audit is [`../docs/CLAIM_EVIDENCE_AUDIT_2026-09-10.md`](../docs/CLAIM_EVIDENCE_AUDIT_2026-09-10.md). The machine-readable state is [`../data/figure_lock_registry_2026-09-10.csv`](../data/figure_lock_registry_2026-09-10.csv).

## NH3 provenance closure and F1-F6 lock

The original NH3-FINAL-1.1 source-harness bundle is now vendored under:

`../provenance/nh3_final_1_1/source_harness/`

The final Linux CI validation reports:

- `PROVENANCE_VALIDATED_READY_FOR_LOCK`;
- **13/13** canonical anchors PASS;
- **6/6** evidence classes present;
- **6/6** figures mapped;
- **28/28** manifest files present;
- **0** source-manifest hash mismatches;
- **0** scientific model reruns.

F1-F6 are therefore locked to the canonical SVG assets from `outputs/nh3_final_20260905T134204Z/figures/`. Exact source SHA-256 values and Git blob SHAs are recorded in [`../docs/NH3_FINAL_1_1_FIGURE_LOCK_2026-09-10.md`](../docs/NH3_FINAL_1_1_FIGURE_LOCK_2026-09-10.md).

A cross-platform transport issue was found during closure: Git line-ending normalization changed 18 text-like files. `.gitattributes` now pins `provenance/nh3_final_1_1/source_harness/** -text`. CI rewrote a file only when a pure LF↔CRLF transformation reproduced the original source-manifest SHA-256 exactly. This restored byte identity without changing any scientific value or plotted geometry.

The compact file [`../data/canonical_results_2026-09-06.csv`](../data/canonical_results_2026-09-06.csv) remains the manuscript-facing numerical snapshot, while the vendored bundle is the direct provenance source. NH3-FINAL-1.0 assets remain historical and must not be substituted.

For publication layout, the canonical vector assets may be copied or renamed into a final submission directory, but the underlying locked SVG bytes and scientific geometry must remain traceable to the lock record.

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

The archived **273–410** ratio is not lockable as a current FINAL-1.1 result. GitHub Actions run **34449914480** classified the retained evidence as **METRIC_EQUIVALENCE_NOT_ESTABLISHED** because no pre-audit implementation of the historical NH3 TOF economic-leverage metric was recovered. The NH3-FINAL-1.1 source-harness provenance is now present, but that does not establish the missing historical metric definition.

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

All current main scientific assets except the deliberately qualitative F9A comparison now satisfy the scientific lock requirement. Publication-layout changes must not silently change the locked data or claims.
