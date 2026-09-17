# Figures

This directory contains manuscript figure assets, renderers and figure-specific provenance for the current project.

The scientific values are frozen independently from publication styling. A figure may be redrawn for typography, spacing, annotation placement or export quality, but the underlying data and scientific geometry must remain traceable to the canonical source.

## Current main figure set

| Figure | Scientific role | Status |
|---|---|---|
| F1 | NH3 atomic-to-economic ranking propagation | **LOCKED** |
| F2 | Rolling Top-K rank correlation | **LOCKED** |
| F3 | NH3 uncertainty / decision stability | **LOCKED** |
| F4 | Fe / Ru / Os operating envelopes | **LOCKED** |
| F5 | Ru backward-design activity sweep | **LOCKED** |
| F6 | Scaling-manifold reachability | **LOCKED** |
| F7 | CO2-to-MeOH upstream-to-economic ranking reshuffle | **LOCKED** |
| F8 | Methane accumulation / purge / selectivity leverage | **LOCKED** |
| F9A | Cross-reaction catalyst-to-process pathway comparison | **QUALITATIVE CURRENT PANEL** |
| F9B | Au/TiO2 rank-preservation control | **LOCKED** |
| F10 | Agent capability-bounded operating envelope | **DRAFT / FINAL CAPTION LOCK PENDING** |

The scientific role and canonical values for each panel are defined in [`../docs/FIGURE_MAP.md`](../docs/FIGURE_MAP.md).

## NH3 — F1 to F6

The canonical **NH3-FINAL-1.1** source-harness bundle is stored under:

`../provenance/nh3_final_1_1/source_harness/`

Repository validation reports:

- **13/13** canonical anchors present;
- **6/6** evidence classes present;
- **6/6** figure mappings present;
- **28/28** manifest files present;
- **0** source-manifest hash mismatches.

F1-F6 are therefore locked to the FINAL-1.1 scientific source. The provenance closure did not rerun the scientific model.

Relevant records:

- [`../docs/NH3_FINAL_1_1_PROVENANCE_POINTER.md`](../docs/NH3_FINAL_1_1_PROVENANCE_POINTER.md)
- [`../docs/NH3_FINAL_1_1_FIGURE_LOCK_2026-09-10.md`](../docs/NH3_FINAL_1_1_FIGURE_LOCK_2026-09-10.md)
- [`../data/figure_lock_registry_2026-09-10.csv`](../data/figure_lock_registry_2026-09-10.csv)

## Methanol — F7 and F8

Directory: [`meoh/`](meoh/)

### F7

Current source asset:

- `MeOH_F03_UpstreamToEconomicRanking_D01v3.png`

It reconstructs the upstream STY-per-g-Re ranking and the 2%-purge economic ranking for the four canonical Re/TiO2 catalyst-temperature states.

### F8

The frozen R renderer is:

- `meoh/render_F08_selectivity_recycle.R`

Canonical outputs:

- `F08_MeOH_selectivity_recycle_D01v3.svg`
- `F08_MeOH_selectivity_recycle_D01v3.pdf`
- `F08_MeOH_selectivity_recycle_D01v3.png`
- `F08_RENDER_SHA256.txt`

F8 contains:

- Panel A: NPC versus purge over the 396-level 0.5-40% sweep;
- Panel B: local leverage comparison for STY, single-pass conversion and CH4 suppression.

## Figure 9

### F9A — pathway comparison

The current panel is intentionally qualitative:

```text
NH3  : activity -> catalyst inventory / reactor demand
MeOH : selectivity -> feed loss / purge / recycle
```

The historical normalized leverage ratio 273-410 is archived but is not plotted as a current manuscript result because its original NH3 metric implementation could not be established sufficiently.

### F9B — Au/TiO2 rank-preservation control

Directory: [`rank_preservation_control/`](rank_preservation_control/)

Canonical asset:

- `RP1_AuTiO2_rank_preservation_V1_1.svg`

Source data:

- [`../data/rank_preservation_control_v1_1.csv`](../data/rank_preservation_control_v1_1.csv)

Generator:

- [`../controls/au_tio2_rank_preservation_v1_1.py`](../controls/au_tio2_rank_preservation_v1_1.py)

Canonical result: full preservation of the 2-6 nm order with rho = 1.000, tau = 1.000 and 0 pairwise inversions.

## Agent figure — F10

Directory: [`agent/`](agent/)

Current scientific panel data:

- [`../data/agent_figure_panel_data_2026-09-13.csv`](../data/agent_figure_panel_data_2026-09-13.csv)

Current renderer:

- `agent/render_F10_agent_envelope.py`

Scientific/caption specification:

- [`../docs/F10_AGENT_FIGURE_SPEC_AND_ED_SI_PLAN_2026-09-13.md`](../docs/F10_AGENT_FIGURE_SPEC_AND_ED_SI_PLAN_2026-09-13.md)
- [`../docs/AGENT_METRIC_DEFINITIONS_SOURCE_OF_TRUTH_2026-09-13.md`](../docs/AGENT_METRIC_DEFINITIONS_SOURCE_OF_TRUTH_2026-09-13.md)

The current F10 claim is budget-localized and model-tier dependent. The figure should keep the 206-CU fixed-policy completion threshold distinct from adaptive final spend and decision-stable spend.

## Supporting Agent figures

Directories:

- `discover_cross_model/`
- `discover_boundary_c1/`

These contain the earlier cross-model and boundary-diagnostic panels used to develop the current F10 architecture. They remain useful for Extended Data / Supporting Information and benchmark inspection, but F10 is the current main-text Agent figure.

## Publication redraws

Current work includes a visual refresh of the manuscript figure set. Redraws should follow these principles:

1. use a consistent publication typography and panel system;
2. de-emphasize non-decision-critical candidates where appropriate;
3. highlight Fe / Ru / Os consistently in NH3 figures;
4. avoid unnecessary legends when direct labels are clearer;
5. export vector SVG/PDF plus high-resolution PNG;
6. retain a direct link from every redrawn panel to its canonical source data or locked asset.

A redraw is a presentation layer. It does not replace the scientific lock or provenance record.

## Figure locking rule

A manuscript figure is final only when the following are all present:

1. canonical numerical source;
2. generator or immutable provenance pointer;
3. manuscript-ready asset;
4. caption/claim wording consistent with the evidence.

Current figure roles and values: [`../docs/FIGURE_MAP.md`](../docs/FIGURE_MAP.md).  
Current numerical snapshot: [`../docs/RESULTS_AT_A_GLANCE.md`](../docs/RESULTS_AT_A_GLANCE.md).  
Consolidated machine-readable headlines: [`../data/manuscript_headline_results_2026-09-17.csv`](../data/manuscript_headline_results_2026-09-17.csv).
