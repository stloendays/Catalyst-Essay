# Rank-Preservation Control V1 — Result

Branch: `rank-preservation-au-tio2-v1`  
GitHub Actions run: `34085636247`  
Runner conclusion: **success**

## Result

The frozen five-state Au/TiO2 control preserved the upstream activity order exactly after downstream inventory/economic propagation:

`2 nm > 3 nm > 4 nm > 5 nm > 6 nm`

for both intrinsic activity and lowest catalyst-dependent economic burden.

Frozen metrics:

- full-set Spearman rho = **1.000**;
- Kendall tau = **1.000**;
- pairwise inversions = **0**;
- exact Top-3 preservation = **true**;
- winner preservation = **true**;
- preregistered 10,000-draw full-rank preservation probability = **1.0000**;
- all six preregistered criteria = **PASS**.

The independent slope diagnostics at `n = 0.9`, `1.7` and `1.8` all produced the same preserved ranking with rho = 1, tau = 1 and zero inversions.

## What this result means

This is a **methodological rank-preservation control**. It demonstrates that the implementation does not intrinsically manufacture ranking inversion when:

- all candidates share the same active element and support;
- catalyst price is common across candidate states;
- stream temperature, pressure, feed and process topology are fixed externally;
- activity and dispersion map monotonically into required catalyst inventory;
- all catalyst-dependent downstream cost terms are positive functions of that inventory.

## What this result does not mean

The control is not an absolute industrial TEA and does not establish a universal particle-size law for every Au/TiO2 preparation. The upstream relation is a relative literature-anchored surrogate, and the economic output is a relative burden index rather than USD/t.

The literature-validation document therefore remains part of the result: the control is restricted to the specific monotonic series and experimentally supported size interval used in the preregistration.

## Promotion status

**Do not merge into the manuscript-facing main branch as a final cross-reaction result yet.**

The present V1 is strong enough to serve as a framework sanity / negative control, but a manuscript claim that compares it directly with the industrial NH3 and methanol cases would be stronger after one additional layer: replace the normalized treatment duty with an independently sourced fixed-condition application duty and validate the inventory/reactor scaling without introducing candidate-dependent process severity.
