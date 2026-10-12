# Source-grounded editorial corrections (author-authorized)

**Status:** an independent, reviewable editorial patch; **not a scientific freeze** and not a regenerated S5 manuscript. This branch is based on the Claude team's verification branch and does not modify model code, experimental records, benchmark scores, figure drawings, frozen checksums or the author's gold-standard review spreadsheet.

## Corrections with source evidence

| Surface | Correction | Evidence |
|---|---|---|
| Main Abstract | The Fe-beating 3d/Cr-Mo-W alloy family is limited to 372 transition-metal surfaces excluding groups 3–5, not all 1,695 priced surfaces | NH3 alloy extension summary; 13 Fe-beating surfaces exist in unrestricted transition metals |
| Main Results/Discussion | Curated-entry recall is not 100% field-value transcription accuracy | Extracted SI X 128/129, MeOH selectivity 123/128 and STY 116/121 |
| Main Methods | Precisely identify the reviewed 150/179 unpaired records and the 87-record new-paper sample | Verification report and SI Note 6 |
| Main Methods / SI Note 9 | Methanol comparison groups need not hold temperature fixed and may compare one catalyst at multiple temperatures | S5 candidate records and PR #43 |
| Main Figure 2a | Separate descriptor-based NH3 bound from purge-wise MeOH process-cost bound | Agent Methods and original optimization code |
| Main Figure 4a / SI Note 3 | Place the 65× gain below the 70.78× band; do not infer 70.78× from a >30× lower bound | Verified Figure 4 target band and existing measurements |
| SI Notes 2–3 | Fix obvious Figure 4 panel references: activity-only target = panel a; strict scaling = panel b | Main Figure 4 caption |
| ED Figure 2b | Label all 406 feasible surfaces as 401 bimetallic plus five pure-metal | NH3 alloy extension summary |
| ED Figure 4a | Disclose the fixed-O&M substitution in the harmonized 706 EUR/t benchmark | Pérez-Fortes cost reconciliation; PR #46 |

## Remaining publication blockers

**This patch is not submission-ready.** S5 printed-only MeOH = 15/40 at laboratory conversion, 14/40 with adjustable catalyst inventory; NH3 printed-only = 7/33. Existing 33/83 and 44/124 paper text, Figure 2, ED figures and Source Data cannot be corrected by simply substituting the headline percentage. All relevant plots and their sample-specific intervals need regeneration.

SI Table 5f currently reports 54/82 and must be rerun for the chosen treatment. Keep old analysis for provenance, not as an authoritative current S5 sensitivity estimate. Source-imputation effects, the figure's lower-bound arrows, the Ru/C 8-wt% literature reference, and gold-standard samples require author validation.

## Independent CI checks

    python -m unittest discover -s analysis/review_editorial_2026_10_09/tests -v

Tests compare prose directly to versioned analysis outputs and extraction scores; passing CI does not certify a paper version. The local Claude session can cherry-pick or adapt these narrow prose changes after reconciling concurrent edits. Do not merge directly into main before author sign-off.
