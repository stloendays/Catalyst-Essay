# Humphreys 2021 errata: impact on the manuscript — 2026-10-06

Branch `humphreys-errata` (builds on PR #27). The ten review errors in nine rows found by the PR #27 PDF check are
applied to `agent/nh3_supported/out/records.csv` (`primary_errata.csv`, column `erratum`) and the chain is rerun
(`README.md` in this folder, before/after for every table). This file lists every number the manuscript and
`docs/SOURCE_OF_TRUTH_2026-09-29.md` quote from this chain, with the old and new value. Neither document is edited
here.

## Numbers quoted in `docs/MANUSCRIPT_MAIN_TEXT.md`

Results, "Measured ammonia catalysts rank differently by laboratory rate and by plant cost":

| Quoted | Old | New | Changes |
|---|---|---|---|
| catalyst rows extracted | 164 | 164 | no |
| passes agree on numeric fields | 697 of 706 | 697 of 706 | no |
| fused-iron calibration | α = 0.64 and 0.45, within 2.2-fold | same | no |
| primary set | 75 | **73** | yes (two Ru-free ref. 104 rows leave) |
| per metal | 56 Ru, 9 Fe, 5 Co, 5 Ni | **54 Ru**, 9 Fe, 5 Co, 5 Ni | yes |
| highest-rate catalyst | Ru/AC-G, 17.53 USD/t | Ru/AC-G, 17.53 USD/t | no |
| its regret over the plant-cost leader | 21% (leader Co/CNT, 14.46) | **14%** (14.4%; leader Ru/Cs/Ba/CCHT, 15.32) | yes |
| Spearman ρ, rate vs plant cost | 0.11 | **0.16** | yes |
| same-support Fe/Ru regrets | 18.6% and 13.0% | **15.2%** and 13.0% | yes (BaTiO₃₋ₓHₓ, ref. 81: Ru loading 0.86 wt%, WHSV 66,000) |
| lowest supported Ru | 15.32 USD/t | 15.32 USD/t | no |
| Ru catalysts below Fe with 90% recovery | three | three (the same three) | no |
| "the one catalyst below Fe without recovery … BaHₓ-promoted Co … 31-fold above the volcano top (14.46 USD/t)" | 14.46 USD/t, 31-fold | **18.28 USD/t, on the volcano (α_res = 1); no catalyst below Fe** | yes — the sentence no longer holds |

Methods, "Measured ammonia catalysts":

| Quoted | Old | New |
|---|---|---|
| rows entering the chain | 85 of 161 | **83 of 161** |
| bed densities, ≥ 5 MPa, constant-multiplier variants (named, no numbers) | — | unchanged wording; values in `README.md` |

Discussion ("dispersion and metal recovery bring supported Ru to the Fe boundary"): still holds — the lowest supported
Ru is 15.32 USD/t against 15.29 for Fe, and three Ru catalysts undercut Fe at 90% recovery. No change.

Abstract: quotes no number from this chain. No change.

## `docs/SOURCE_OF_TRUTH_2026-09-29.md`

It has no entry for this chain. The only overlap is the Fig. 3a strip row "Ru/BaTiO2.5H0.5 vs Ru/BaTiO3, 8.4×, TOF,
400 C, 5 MPa, Tang et al. 2018": a TOF ratio taken from the paper itself
(`analysis/promoted_ru_literature_2026_10_05/`), not from the review's loading or WHSV. No change. If the main session
adds an SoT entry for the measured-catalyst chain, the values are those in `summary.json` of this branch.

## Proposed replacement sentences

Results, paragraph 1, second sentence (optional, states the primary-source check):

> It extracted the 164 catalyst rows tabulated in a review of ammonia-synthesis catalysts;[48] two independent
> extraction passes agree on 697 of 706 numeric fields, and every value was checked against the printed tables.
> Rows whose cited papers were read for the field analysis below were also checked against those papers, and the
> paper values replace the ten values the review misprints.

(PR #27 matched 38 review rows, citing 28 of its 30 papers; the errata come from that check. Adjust "below" to the section order.)

Results, paragraph 2, whole paragraph:

> Of the 73 catalysts in the primary set (54 Ru, 9 Fe, 5 Co and 5 Ni), the one with the highest laboratory rate,
> Ru/AC-G, costs 17.53 US dollars per tonne, 14% above the plant-cost leader, and laboratory rate and plant cost are
> nearly uncorrelated (Spearman ρ = 0.16). In both studies that test Fe and Ru on the same support, Ru has the higher
> rate and Fe the lower plant cost (15.2% and 13.0% regret). No measured catalyst undercuts the fused-iron benchmark
> without metal recovery; the closest is a promoted Ru catalyst at 15.32 US dollars per tonne, and with 90% Ru
> recovery three Ru catalysts do, the route identified in Fig. 2d.

Methods, "Measured ammonia catalysts", sentence 3 and an added sentence after sentence 1:

> … rows printed twice are counted once. Where the cited paper differs from the review (ten values in nine rows,
> including two rows the review lists as Ru catalysts that contain no Ru), the paper value is used. Catalysts with one
> model metal and a stated metal content enter the chain: 83 of 161 rows.

## Audit tool

`tools/audit_live_manuscript_truth.py` lines 536–545 read this chain's `summary.json`. After the manuscript edit:
- line 542, the token `({pm['Co']['cost_min']:.2f} US dollars per tonne)` (old 14.46) belongs to the deleted Co
  sentence; replace it with the new wording's tokens;
- line 544–545, the check "only the Co catalyst below Fe without recovery" is now false (no metal has a catalyst below
  Fe); it should assert `all(v["below_Fe"] == 0 for v in pm.values())`.
The regret token on line 537 uses `:.0f`, giving "14%"; the Spearman token gives "0.16".

## Downstream note

`agent/nh3_field/evaluate.py` scores the PR #27 extraction against `records.csv`. After the errata the record holds the
paper value, so a rerun of `evaluate.py` would score the agent against the papers on these nine rows rather than
against the review (and the two ref. 104 names now read "TiH2 (Ru-free)" and "BaTiO2.5H0.5 (Ru-free)"). The committed
PR #27 evaluation outputs were not rerun here.
