# NH3-FINAL-1.1 — F1–F6 figure lock

Date: **2026-09-10**

Status: **LOCKED**

Canonical scientific version: **NH3-FINAL-1.1**  
Canonical run: `outputs/nh3_final_20260905T134204Z`

## Lock basis

The original NH3-FINAL-1.1 source-harness bundle is now vendored under:

`provenance/nh3_final_1_1/source_harness/`

GitHub Actions validation reports:

- status: `PROVENANCE_VALIDATED_READY_FOR_LOCK`;
- canonical anchors: **13/13 PASS**;
- evidence classes: **6/6 present**;
- figures mapped: **6/6**;
- manifest files: **28/28 present**;
- manifest hash mismatches: **0**;
- scientific model reruns: **0**.

The validation record is `artifacts/nh3_final_1_1_provenance/VALIDATION_REPORT.md`.

## Canonical vector assets

| Figure | Scientific role | Canonical SVG | source SHA-256 | Git blob SHA |
|---|---|---|---|---|
| F1 | Atomic-to-economic ranking propagation | `provenance/nh3_final_1_1/source_harness/outputs/nh3_final_20260905T134204Z/figures/F1_ranking_propagation_1_1.svg` | `603b883c5d438bb64f34a7f3433e625b7ac49ae3a16267b497ae98e321ccd3a0` | `bc8b90afc8d15777be0d8bc8c76ab5f5b9a7dfc0` |
| F2 | Rolling Top-K rank correlation | `provenance/nh3_final_1_1/source_harness/outputs/nh3_final_20260905T134204Z/figures/F2_rolling_topk_1_1.svg` | `731c2fbcc506f01ea7ed2bb07cc3936cc6ab8e1a7964b42d5d1f6ccc9a6180e3` | `8a371784feff2c9974003f99599f48a7c0ce6541` |
| F3 | Monte Carlo feasibility and decision stability | `provenance/nh3_final_1_1/source_harness/outputs/nh3_final_20260905T134204Z/figures/F3_mc_feasibility_1_1.svg` | `39e32260440c2a7916b4eb4ae73f6e76ce7ce9516162122d77f79cbbdbc8ef53` | `fbe16c2738de87c1aa43eb208f70b33c06c990be` |
| F4 | Pressure/operating envelopes | `provenance/nh3_final_1_1/source_harness/outputs/nh3_final_20260905T134204Z/figures/F4_pressure_envelopes_1_1.svg` | `1f95767e85ddca8fa366a7b1d5bf4baca3166a32f906f5b0e3e10bc26432cc5f` | `a5f552953639cd5b995213282c031dd616101a52` |
| F5 | Ru backward-design break-even sweep | `provenance/nh3_final_1_1/source_harness/outputs/nh3_final_20260905T134204Z/figures/F5_ru_breakeven_1_1.svg` | `c37a9d8aeb56a45c44ae61d1e889531732f33a591f7812a9d3768bdecda0b188` | `bc3c27a4e48ef66babcf85b767d79a9cbd3af8fa` |
| F6 | Scaling-manifold reachability | `provenance/nh3_final_1_1/source_harness/outputs/nh3_final_20260905T134204Z/figures/F6_scaling_reachability_1_1.svg` | `8413c367b8cb2c630d3d7f65b3d324949f5d1f8a2ed2fa5b7c68619eef2f42e0` | `ad89822ca8011d5440d127ed39ee39a64c706c5e` |

The paired PNG assets from the same canonical run remain available as raster fallbacks. The SVG files above are the manuscript-level canonical assets.

## Cross-platform byte preservation

The first Linux CI checkout exposed a line-ending normalization issue: 18/28 text-like source files had been normalized by Git and therefore did not match the original source-harness SHA-256 values. This was a repository transport issue, not a scientific discrepancy: all 13 canonical anchors, all six evidence classes and all six figure mappings already matched.

The repository now pins `provenance/nh3_final_1_1/source_harness/** -text` in `.gitattributes`. A deterministic repair action rewrote a file only when a pure LF↔CRLF transform reproduced the original source-manifest SHA-256 exactly. After this byte-level repair, all 28 manifest hashes pass in Linux CI. No scientific value, model parameter or plotted result was changed.

## Lock rule

F1–F6 are now frozen to the canonical SVG assets above. Subsequent manuscript work may change placement, panel lettering, caption wording or export format, but must not silently replace the underlying FINAL-1.1 data or scientific geometry. Any scientific-content change requires reopening the figure lock with an explicit provenance record.
