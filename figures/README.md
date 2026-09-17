# Figures

This directory contains manuscript figure assets, renderers and figure-specific provenance.

Scientific values are frozen independently from publication styling. Typography, spacing, annotation placement and export quality may be revised, but each redraw must remain traceable to its canonical source.

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
| F10 | Agent capability-bounded operating envelope | **LOCKED** |

The current scientific role and canonical values are defined in [`../docs/FIGURE_MAP.md`](../docs/FIGURE_MAP.md). Superseded figure claims are centralized in [`../docs/RETIRED_RESULTS.md`](../docs/RETIRED_RESULTS.md).

## NH3 — F1 to F6

Canonical source bundle:

`../provenance/nh3_final_1_1/source_harness/`

Repository validation reports **13/13 canonical anchors, 6/6 evidence classes, 6/6 figure mappings, 28/28 manifest files and 0 source-manifest hash mismatches**.

Relevant records:

- [`../docs/NH3_FINAL_1_1_PROVENANCE_POINTER.md`](../docs/NH3_FINAL_1_1_PROVENANCE_POINTER.md)
- [`../docs/NH3_FINAL_1_1_FIGURE_LOCK_2026-09-10.md`](../docs/NH3_FINAL_1_1_FIGURE_LOCK_2026-09-10.md)
- [`../data/figure_lock_registry_2026-09-10.csv`](../data/figure_lock_registry_2026-09-10.csv)

## Methanol — F7 and F8

Directory: [`meoh/`](meoh/)

### F7

Current source asset:

- `MeOH_F03_UpstreamToEconomicRanking_D01v3.png`

Source data/provenance are in `../data/meoh/`.

### F8

Frozen R renderer:

- `meoh/render_F08_selectivity_recycle.R`

Canonical outputs:

- `F08_MeOH_selectivity_recycle_D01v3.svg`
- `F08_MeOH_selectivity_recycle_D01v3.pdf`
- `F08_MeOH_selectivity_recycle_D01v3.png`
- `F08_RENDER_SHA256.txt`

Panel A reports NPC versus purge over the 396-level 0.5-40% sweep; Panel B reports local leverage for STY, single-pass conversion and CH4 suppression.

## Figure 9

### F9A — pathway comparison

Current content is qualitative:

```text
NH3  : activity -> catalyst inventory / reactor demand
MeOH : selectivity -> feed loss / purge / recycle
```

No quantitative cross-reaction leverage ratio is plotted in the current panel.

### F9B — Au/TiO2 rank-preservation control

Directory: [`rank_preservation_control/`](rank_preservation_control/)

Canonical asset:

- `RP1_AuTiO2_rank_preservation_V1_1.svg`

Source data: [`../data/rank_preservation_control_v1_1.csv`](../data/rank_preservation_control_v1_1.csv)  
Generator: [`../controls/au_tio2_rank_preservation_v1_1.py`](../controls/au_tio2_rank_preservation_v1_1.py)

Canonical result: full preservation of the 2-6 nm order with rho = 1.000, tau = 1.000 and 0 pairwise inversions.

## Agent figure — F10

Directory: [`agent/`](agent/)

Canonical scientific panel data:

- [`../data/agent_figure_panel_data_2026-09-13.csv`](../data/agent_figure_panel_data_2026-09-13.csv)

Renderer:

- `agent/render_F10_agent_envelope.py`

Canonical asset:

- `agent/F10_agent_capability_bounded_envelope.svg`
- PDF and 600-dpi PNG exports are stored alongside the SVG
- hash manifest: `agent/F10_RENDER_SHA256.txt`

Final caption:

- [`agent/F10_CAPTION.md`](agent/F10_CAPTION.md)

F10 keeps the **206 CU** fixed-policy threshold distinct from adaptive decision-stable spend and final spend. The strong tier has a lowest tested stable complete-decision budget of **75 CU**; under the non-binding 5000-CU allowance, median final spend is **714 CU**.

## Agent Extended Data

- `agent/ED1_mini_interface_intervention.svg`
- `agent/ED2_failure_mechanism_by_tier.svg`
- `agent/ED3_non_binding_per_run_spread.svg`

Renderer: `agent/render_ED_agent_panels.py`  
Manifest: `agent/ED_RENDER_SHA256.txt`

Earlier benchmark-development panels remain under `discover_cross_model/` and `discover_boundary_c1/` for Supporting Information and provenance inspection; they are not substitutes for F10.

## Publication redraws

Current visual refresh should follow these rules:

1. use one publication typography and panel system across F1-F10;
2. de-emphasize non-decision-critical candidates where appropriate;
3. highlight Fe / Ru / Os consistently in NH3 figures;
4. prefer direct labels over unnecessary legends;
5. export SVG/PDF plus high-resolution PNG;
6. retain a direct link from every redrawn panel to canonical source data or a locked asset.

A redraw is a presentation layer. It does not replace the scientific lock or provenance record.

## Figure locking rule

A manuscript figure is final only when all four are present:

1. canonical numerical source;
2. generator or immutable provenance pointer;
3. manuscript-ready asset;
4. caption/claim wording consistent with the evidence.

Current figure roles and values: [`../docs/FIGURE_MAP.md`](../docs/FIGURE_MAP.md).  
Current numerical summary: [`../docs/RESULTS_AT_A_GLANCE.md`](../docs/RESULTS_AT_A_GLANCE.md).  
Current machine-readable headlines: [`../data/manuscript_headline_results_2026-09-17.csv`](../data/manuscript_headline_results_2026-09-17.csv).
