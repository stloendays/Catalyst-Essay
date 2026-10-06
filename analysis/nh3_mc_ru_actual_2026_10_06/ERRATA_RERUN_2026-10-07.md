# Actual-Ru Monte Carlo after the Humphreys errata: impact on the manuscript — 2026-10-07

`run_mc_ru_actual.py` was rerun with the same seeds on the `supported_candidates.csv` corrected by PR #28 (54 Ru
catalysts instead of 56; Ru/BaTiO2.5H0.5 at 0.86 wt%; corrected space velocities). The base reproduction still gives
P(Fe cheaper) = 1.000 and a minimum gap of 2.382 USD/t. This file lists every number in `docs/MANUSCRIPT_MAIN_TEXT.md`
that comes from this analysis, with its old and new value. Neither the manuscript nor `docs/SOURCE_OF_TRUTH_*` is edited
here.

## Numbers quoted in `docs/MANUSCRIPT_MAIN_TEXT.md`

Results, ammonia uncertainty paragraph 2 (line 41, "These draws charge Ru as the benchmark bed of pure metal…"):

| Quoted | Old | New | Changes |
|---|---|---|---|
| P(Fe cheaper), benchmark bed volume (A) | 24.0% | 24.0% (0.2396) | no |
| P(Fe cheaper), own Ru content and bed density (A_bed) | 80.4% | **80.0%** (0.7998) | yes |
| P(Ru wins), u in lowest tercile | 1.3% | 1.3% (0.0132) | no |
| P(Ru wins), u and r in top terciles | 49% | **50%** (0.498) | yes |
| P(Ru wins), < 2.5 wt% Ru | 0.6% | **0.5%** (0.0046) | yes |
| P(Ru wins), ≥ 5 wt% Ru | 39% | 39% (0.393) | no |
| measured Ru catalysts drawn from | 56 | **54** | yes |
| P(Fe cheaper), measured Ru, with recovery (B) | 94.9% | **94.6%** (0.946) | yes |
| P(Fe cheaper), measured Ru, no recovery (B0) | 98.9% | 98.9% (0.9894) | no |
| Ru wins come from five of the … catalysts | five of the 56 | five of the **54** (the same five) | yes |

Discussion (line 111, "…with the actual Ru catalyst sampled, Fe remains cheaper in…"):

| Quoted | Old | New | Changes |
|---|---|---|---|
| P(Fe cheaper), supported bed (A_bed) | 80.4% | **80.0%** | yes |
| P(Fe cheaper), measured Ru activities (B) | 94.9% | **94.6%** | yes |

Not quoted in the main text: the 0.27–13.8 wt% range and median 4 wt% (unchanged), the median per-gram Ru activity
0.22 (0.216 → 0.220, unchanged at two digits) and its ≥ 5 MPa value (0.034 for 13 catalysts → **0.060** for 11). If the
SI or a figure caption quotes the ≥ 5 MPa value, it changes.

Out of scope here but in the same text: line 99 ("Of the 75 catalysts in the primary set (56 Ru, …") comes from
`analysis/nh3_supported_2026_10_06`, not from this Monte Carlo; its replacement is in
`analysis/nh3_supported_2026_10_06/ERRATA_IMPACT_2026-10-06.md`.

## Replacement sentences

Line 41, from the third sentence on:

> With the Ru dispersion ratio u (11–50) and Ru recovery r (90–94%) added to the same 5,000 draws, Fe is cheaper in
> 24.0% of draws when the supported catalyst occupies the benchmark bed volume, and in 80.0% when its own Ru content and
> bed density set the reactor volume. Ru then wins only when both the dispersion ratio and the Ru content are high: in
> 1.3% of draws with u in its lowest tercile and 50% with u and r in their top terciles, and in 0.5% of draws below
> 2.5 wt% Ru against 39% at 5 wt% or more; recovery within its range matters little. Drawing the Ru activity and Ru
> content from the 54 measured Ru catalysts instead, Fe is cheaper in 94.6% of draws with recovery and 98.9% without,
> and the Ru wins come from five of the 54 catalysts (Ru on Ca(NH₂)₂, Ba–Ca(NH₂)₂ and BaO–CaH₂, Ba–Cs-promoted
> Ru/CCHT and Ru/AC-G).

Line 111, last clause:

> …with the actual Ru catalyst sampled, Fe remains cheaper in 80.0% of draws with the supported bed and 94.6% with the
> measured Ru activities.

## `tools/audit_live_manuscript_truth.py` on this branch (manuscript not yet edited)

73 checks, 4 failed:

- `NH3 actual-catalyst Monte Carlo` — from this rerun; missing "and in 80.0% when its own Ru content", "Fe is cheaper in
  94.6% of draws with recovery and 98.9% without", "five of the 54 catalysts".
- `NH3 actual-catalyst MC: where Ru wins` — from this rerun; missing "50% with u and r in their top terciles", "in 0.5% of
  draws below 2.5 wt% Ru".
- `NH3 measured catalysts` and `NH3 measured: only the Co catalyst below Fe without recovery` — from PR #28 (supported
  chain), not from this rerun; fixed by the line 99 replacement in `ERRATA_IMPACT_2026-10-06.md`.

The two passing MC checks (`base reproduced`, `five winning measured catalysts`) still pass.
