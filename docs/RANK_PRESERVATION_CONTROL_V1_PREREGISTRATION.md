# Rank-Preservation Control V1 — preregistration

Reaction: **CO oxidation on Au/TiO2**  
Control purpose: test whether the multiscale implementation preserves an upstream catalyst ordering when the downstream mapping is intentionally fixed and monotonic.

## Candidate set

Representative Au/TiO2 particle-size states within the common monotonic interval supported by the literature validation:

`2, 3, 4, 5, 6 nm`

The candidates share the same active element and support. Particle size is the controlled catalyst-state variable.

## Frozen upstream activity relation

Nominal relative intrinsic activity:

`TOF_rel(d) = (d / 2 nm)^(-n)`

V1 nominal `n = 1.7`, with literature sensitivity bounds described in the validation document.

V1.1 is a registered literature-calibration layer that replaces the V1 nominal slope with the closest-loading literature slope and introduces absolute experimental anchors. It does not change the candidate set, fixed-condition control logic, or rank-preservation criteria.

## Fixed downstream mapping

The control deliberately holds process severity and topology fixed across candidate states:

- same reaction;
- same active element and support;
- same Au price basis;
- same feed composition;
- same temperature and pressure;
- same conversion duty;
- no candidate-specific severity optimization;
- no recycle or separation topology change.

Catalyst-dependent downstream burden may change only through the catalyst amount / Au inventory required to satisfy the same reaction duty.

## Predefined rank-preservation criteria

The control passes only if all six conditions are met:

1. **C1 — winner preserved:** the highest-activity candidate is also the lowest-burden candidate.
2. **C2 — full Spearman rho >= 0.95.**
3. **C3 — Kendall tau >= 0.90.**
4. **C4 — zero pairwise inversions.**
5. **C5 — exact Top-3 ordering preserved.**
6. **C6 — at least 95% full-rank preservation under the predefined common-series uncertainty envelope.**

## Interpretation rule

A PASS supports only the methodological statement that the multiscale implementation does not intrinsically force a ranking inversion when no competing downstream penalty is present.

A PASS does **not** establish a universal size–activity law for Au/TiO2, does not imply that every CO-oxidation process preserves this order, and does not justify unsupported absolute industrial economics.

## Versioning

- V1: relative methodological control.
- V1.1: literature-calibrated physical mapping using published absolute activity / reactor-condition anchors and the closest-loading particle-size relation.

The V1.1 calibration magnitude must be reported explicitly rather than silently replacing V1 parameters.
