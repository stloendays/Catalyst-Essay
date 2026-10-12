# Claude handoff — MeOH performance-input uncertainty

Date: 2026-10-05 (numbers updated after the Table 3 input correction, PR #7)

## Immediate author instruction

Do **not** frame the MeOH uncertainty result around the word "assumption" in reader-facing text. The active editorial lock is in `docs/MANUSCRIPT_EDITORIAL_LOCKS.md` (LOCK-05).

Preferred reader-facing names:
- performance-input uncertainty propagation
- published-data-resolution uncertainty

The uncertainty-source caveat belongs once in Methods / Supporting Information, not as the headline interpretation.

## What is established in the repository

The 1 wt% Re / 250 C state now carries its Table 3 selectivities (Gothe et al., ACS Catal. 2025: CH3OH 97 %, CO 1 %, CH4 1 %); the workbook previously carried CH4 3 %. All workbook values were recomputed with `data/meoh/meoh_d01_model.py` (`data/meoh/regenerate_d01_values.py --check` reproduces the pre-correction stored values to < 1e-10 EUR/t).

Canonical MeOH candidate-state costs at 2 % purge (`data/meoh/meoh_candidate_ranking_D01v3.csv`):
- 5 wt% Re / 200 C: 943.30 EUR/t (economic rank 1)
- 1 wt% Re / 250 C: 961.51 EUR/t (rank 2)
- 1 wt% Re / 200 C: 966.96 EUR/t (rank 3)
- 5 wt% Re / 250 C: 1258.17 EUR/t (rank 4)

STY-per-g-Re vs economic ranking: rho = 0.40, tau = 0.33, 2/6 pairs inverted; the upstream winner is economic #2.

The supervisor-era cost-side Monte Carlo (`analysis/supervisor_2026_09_20/meoh_rank_probability_matrix.csv`, 5000/5000 invariant order) was computed on the previous inputs (CH4 3 % for 1 wt% Re / 250 C) and is superseded by the performance-input Monte Carlo. If an economic-parameter robustness statement is wanted as supporting evidence, it must be rerun on the corrected inputs first.

`data/meoh/meoh_d01_v3.json` still carries the earlier single performance-side datum (`1wtRe_200C.S_CH4`, "<1 %", `sigma = 0.005`, "reported rounding"); the Monte Carlo below supersedes it by sampling "<1 %" over 0–1 %.

## Performance-input Monte Carlo (committed, primary MeOH uncertainty result)

Bundle: `analysis/meoh_measurement_mc_2026_10_05/` (`meoh_measurement_mc.py`, `derive_uncertainty_basis.py`, `uncertainty_basis.json`, `mc_summary.json`, `mc_rank_probability_matrix.csv`, `mc_pairwise_inversion.csv`, `mc_scale_sweep.csv`, draw-level `mc_draws_canonical_k1.csv`, Fig. 4d renders).

Construction (source-derived; the paper reports no error bars):
- each state's CO2 conversion and MeOH / CH4 selectivities are sampled independently and the full D01 v3 recycle / purge / separation model is re-solved per draw, with every cost parameter at its canonical value;
- reporting resolution: integer values ± 0.5 pt; "<1 %" sampled over 0–1 %;
- conversion: 5.2 % relative uncertainty from STY / conversion consistency across the 21 runs of Table 4;
- selectivity: 0.85-pt MeOH <-> CH4 exchange from the 11 runs of a single catalyst;
- STY follows conversion x MeOH selectivity; N = 5000, seed 20261005; the centre is asserted equal to the canonical ranking table.

Results at k = 1 (all widths as derived):
- 5 wt% Re / 200 C remains rank 1 in 4,559/5,000 draws (91.2 %);
- 5 wt% Re / 250 C remains rank 4 in 5,000/5,000;
- ranks 2 and 3 (1 wt% Re / 250 C vs 1 wt% Re / 200 C, 5.5 EUR/t apart) exchange in 1,054/5,000 (21.1 %);
- the STY winner becomes the economic optimum in 413/5,000 (8.3 %); the full STY ranking is recovered in 24/5,000 (0.5 %);
- width x0.5 / x2: winner kept first in 99.3 % / 78.4 %.

These numbers replace the earlier ~97.0 % / ~47.8 % figures, which were computed on the uncorrected inputs. Authoritative registry: `docs/SOURCE_OF_TRUTH_2026-09-29.md`, section "Methanol — Table 3 input correction and measurement Monte Carlo — 2026-10-05".

Done: bundle located and reproducible (seed, distributions, input mapping, draw-level table), centre equals the D01 v3 ranking, cost-side MC separated from the primary result, and the main text, captions, RESULTS_AT_A_GLANCE, STATUS and SOURCE_OF_TRUTH carry the corrected numbers. The manuscript currently names the analysis "measurement uncertainty" / "measurement Monte Carlo".

## Wording rule

Reader-facing Results should emphasize the **decision result**, e.g.:
"Propagating uncertainty in the published catalytic-performance inputs leaves the 5 wt% Re / 200 C state as the economic winner in 91.2 % of 5,000 draws; the two intermediate states, 5.5 EUR/t apart, exchange rank in 21.1 %, and 5 wt% Re / 250 C stays last in every draw."

Methods/SI can then explain the source resolution/censoring and internal-consistency construction.

Avoid phrases such as:
- assumption-aware uncertainty
- assumption-derived uncertainty
- arbitrary uncertainty
- experimental standard deviation (unless directly reported)

## Files to inspect first

- `analysis/meoh_measurement_mc_2026_10_05/mc_summary.json`
- `analysis/meoh_measurement_mc_2026_10_05/uncertainty_basis.json`
- `data/meoh/meoh_candidate_ranking_D01v3.csv`
- `data/meoh/meoh_d01_model.py`
- `docs/SOURCE_OF_TRUTH_2026-09-29.md`
- `docs/MEOH_RANKING_INVERSION.md`
- `docs/MANUSCRIPT_EDITORIAL_LOCKS.md`
