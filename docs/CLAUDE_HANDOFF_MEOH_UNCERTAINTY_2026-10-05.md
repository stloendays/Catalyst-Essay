# Claude handoff — MeOH performance-input uncertainty

Date: 2026-10-05

## Immediate author instruction

Do **not** frame the MeOH uncertainty result around the word "assumption" in reader-facing text. The active editorial lock is in `docs/MANUSCRIPT_EDITORIAL_LOCKS.md` (LOCK-05).

Preferred reader-facing names:
- performance-input uncertainty propagation
- published-data-resolution uncertainty

The uncertainty-source caveat belongs once in Methods / Supporting Information, not as the headline interpretation.

## What is already established in the repository

Canonical MeOH candidate-state costs at 2% purge:
- 5 wt% Re / 200 C: ~943 EUR/t (economic rank 1)
- 1 wt% Re / 200 C: ~967 EUR/t (rank 2)
- 1 wt% Re / 250 C: ~975 EUR/t (rank 3)
- 5 wt% Re / 250 C: ~1258 EUR/t (rank 4)

The existing supervisor-era cost-side Monte Carlo keeps the canonical order in 5000/5000 draws. That calculation mainly perturbs economic coefficients and is now supporting evidence, not the preferred test of MeOH ranking uncertainty.

The repository already encodes one performance-side uncertainty datum in `data/meoh/meoh_d01_v3.json`:
- `1wtRe_200C.S_CH4`: source Table 3 "<1 %"; central handling includes `sigma = 0.005` with source label "reported rounding".

## Current scientific direction

The primary MeOH uncertainty analysis should perturb the **published catalytic-performance inputs** that drive the recycle/economic model, rather than relying only on common cost-side perturbations.

Source-supported information for constructing the propagated input envelope:
1. catalytic conversion/selectivity values are reported at integer percentage precision;
2. entries such as "<1%" are censored rather than exact zeroes;
3. Table 4 provides a multi-condition internal-consistency check across STY, conversion, selectivity, GHSV/feed composition and Re loading.

Do not describe these constructed input ranges as experimentally reported replicate SD/SEM unless the source explicitly reports those statistics.

## Result under active review

The author reports a newer 5000-draw performance-input propagation with the following qualitative/quantitative behavior:
- 5 wt% Re / 200 C remains rank 1 in ~97.0% of draws;
- 5 wt% Re / 250 C remains rank 4 essentially always;
- the two middle candidates exchange ranks in ~47.8% of draws.

This is scientifically preferable to using the old invariant 5000/5000 cost-side matrix as the primary MeOH ranking-robustness statement because it directly tests uncertainty in the upstream catalyst-performance measurements that drive the selectivity-recycle pathway.

Before promotion into the manuscript, Claude should:
1. locate the exact script/output bundle that generated the ~97.0% / ~47.8% result, or reproduce it deterministically from the agreed source-derived input ranges;
2. record seed, distributions/ranges, candidate-input mapping and draw-level rank table;
3. verify that the central/canonical ranking remains the D01 v3 ranking;
4. distinguish the primary performance-input MC from the older economic-parameter MC;
5. update the MeOH uncertainty paragraph, figure/caption source, RESULTS_AT_A_GLANCE and source-of-truth documents only after the new bundle is reproducible and audited.

## Wording rule

Reader-facing Results should emphasize the **decision result**, e.g.:
"Propagating uncertainty in the published catalytic-performance inputs leaves the 5 wt% Re / 200 C state as the economic winner in ~97% of draws, while the two intermediate states exchange rank frequently."

Methods/SI can then explain the source resolution/censoring and internal-consistency construction.

Avoid phrases such as:
- assumption-aware uncertainty
- assumption-derived uncertainty
- arbitrary uncertainty
- experimental standard deviation (unless directly reported)

## Existing files to inspect first

- `data/meoh/meoh_d01_v3.json`
- `data/meoh/MeOH_D01_ExplicitRecycleSeparationEconomics_v3.0.xlsx`
- `docs/MEOH_RANKING_INVERSION.md`
- `analysis/supervisor_2026_09_20/README.md`
- `analysis/supervisor_2026_09_20/meoh_rank_probability_matrix.csv`
- `docs/MANUSCRIPT_EDITORIAL_LOCKS.md`

