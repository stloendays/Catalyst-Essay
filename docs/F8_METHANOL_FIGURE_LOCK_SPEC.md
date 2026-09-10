# Figure 8 lock specification — MeOH selectivity–recycle pathway

Date: **2026-09-10**

Status: **SCIENTIFIC DESIGN FROZEN; FINAL VECTOR RENDER PENDING**

Figure 8 should explain the mechanism behind the CO2-to-MeOH catalyst-state rank reshuffle using only the frozen D01 v3 evidence. No new scientific calculation is required.

## Panel A — purge-dependent economic burden

Source: `data/meoh/meoh_purge_robustness_D01v3.csv`.

Plot NPC (EUR/t MeOH) versus purge fraction for all four literature catalyst–temperature states across the full **0.5–40%** sweep. Mark **2% purge** as the source-anchored canonical comparison.

Required message:

- the upstream STY-per-g-Re winner, **1 wt% Re / 250 C**, is never the economic winner over the full purge sweep;
- the highest-conversion state, **5 wt% Re / 250 C**, is never the economic winner and carries the largest economic burden;
- economic rank reshuffling persists over all 396 purge levels, with Spearman rho <= **0.40** and at least **2/6** pairwise inversions.

Do not present the 0.5% candidate-specific optimum as the new canonical operating point. It is a lower-bound optimum of the robustness sweep; **2% remains canonical**.

## Panel B — local catalyst-economic leverage

Source: `data/meoh/meoh_candidate_ranking_D01v3.csv`, benchmark state **5 wt% Re / 250 C**.

Use a dot/lollipop-style comparison rather than a bar chart. Prefer a logarithmic x-axis because the three frozen leverage magnitudes span >2 orders of magnitude:

- STY: **0.0028943**
- single-pass conversion: **0.0588278**
- CH4 suppression: **0.3757939**

Derived comparisons for annotation only:

- CH4 suppression / conversion ~= **6.39x**
- CH4 suppression / STY ~= **129.84x**

Required message: in this process regime, selectivity-driven methane suppression controls a much larger downstream economic pathway than increasing production rate alone.

## Panel C — optional compact pathway annotation

Only if needed for readability, add a small non-quantitative pathway annotation:

`CH4 selectivity -> H2 loss / inert accumulation -> purge + recycle -> compression/equipment burden -> NPC`

This is an explanatory annotation, not an additional numerical result.

## Visual and caption constraints

- Main text should use **Panel A + Panel B** as the default Figure 8 composition.
- Keep all text black; use the established manuscript palette only for candidate identities/highlights.
- Do not use a new upstream metric in this figure.
- Do not add Re purchase price; it is excluded from the frozen NPC by design.
- Do not imply that T/P were reoptimized for the four MeOH literature states.
- Caption must call these **catalyst–temperature states**.

## Evidence chain

- raw/frozen workbook: `data/meoh/MeOH_D01_ExplicitRecycleSeparationEconomics_v3.0.xlsx`
- extracted candidate table: `data/meoh/meoh_candidate_ranking_D01v3.csv`
- purge robustness: `data/meoh/meoh_purge_robustness_D01v3.csv`
- purge analysis code: `data/meoh/meoh_purge_robustness.py`
- existing reference asset: `figures/meoh/MeOH_F02_Purge_MethaneAccumulation_FINAL_v3.0.png`

The final lock requires an editable/vector render generated from the frozen CSVs plus a raster export. The scientific panel design and numerical annotations are frozen by this document.