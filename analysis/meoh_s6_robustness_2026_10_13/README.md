# Methanol robustness checks under the inlet-limited loop S6 (2026-10-13)

The supervisor's decision of 2026-10-12/13 makes the inert-limited loop S6 the primary methanol result. S6 optimizes the
purge only over levels whose reactor-inlet CH4 + CO + N2 fraction is <= 6.86 %; frozen column
`cost_recycled_opt_inlet`. Everything else is the frozen treatment. This folder reruns every robustness check of the
manuscript's robustness paragraph under S6 with the same code paths, and keeps S5 alongside. Every S5 value below is the
frozen number, reproduced through these wrappers before any S6 number was computed. Nothing frozen is changed: the
manuscript, figures, frozen outputs and existing analysis folders are only imported or read.

Cohort: the printed primary (40 comparison groups, 310 entries, 28 papers).

### Items 1–7: S5 (frozen, reproduced) and S6

| Item | S5 (frozen, reproduced) | S6 (inlet-limited, primary) |
|---|---|---|
| 1 Point estimate | 15/40 (7 > 5 %), 9 papers | 28/40 (22 > 5 %), 21 papers (18 with > 5 %) |
| 1A Paper-cluster bootstrap 95 % CI (10,000, seed 20261006) | 15.2 %–57.1 % (paper-weighted 26.9 %, 12.6 %–43.2 %) | 54.1 %–82.8 % (paper-weighted 69.2 %, 52.7 %–84.5 %) |
| 1B Regret-threshold curve (groups, papers) | 0 %: 15 (9 p.) · 0.1 %: 14 (8 p.) · 0.5 %: 13 (7 p.) · 1 %: 12 (6 p.) · 2 %: 8 (2 p.) · 5 %: 7 (2 p.) · 10 %: 6 (2 p.) | 0 %: 28 (21 p.) · 0.1 %: 27 (21 p.) · 0.5 %: 26 (20 p.) · 1 %: 25 (19 p.) · 2 %: 25 (19 p.) · 5 %: 22 (18 p.) · 10 %: 20 (16 p.) |
| 1C Disagreements kept in ≥ 90 % of re-measurements, ×1 | 11 of 15 (median regret 11.6 %, 7 > 5 %, 5 papers); mean 16.5 [13–20] | 24 of 28 (median regret 37.0 %, 22 > 5 %, 19 papers); mean 27.8 [25–30] |
| 1C … ×2 | 9 of 15 (median regret 11.6 %, 6 > 5 %, 4 papers); mean 17.4 [13–21] | 20 of 28 (median regret 29.8 %, 18 > 5 %, 16 papers); mean 27.5 [24–31] |
| 1C … ×4 | 5 of 15 (median regret 16.8 %, 5 > 5 %, 2 papers); mean 18.0 [13–22] | 14 of 28 (median regret 29.8 %, 13 > 5 %, 13 papers); mean 27.0 [23–31] |
| 1C Noise floor (re-measured STY leader ≠ reported), mean [95 %] | ×1: 4.2 [1–8] · ×2: 8.0 [4–12] · ×4: 13.7 [9–19] | ×1: 4.2 [1–8] · ×2: 8.0 [4–12] · ×4: 13.7 [9–19] |
| 1C Surface vs exact: group verdicts differing / compared | 1/600 | 7/600 |
| 2 Pairwise orderings inverted | 304/1997 | 707/1997 |
| 3 Ranking by methanol selectivity: disagreements, median regret | 31/40 (24 > 5 %), 19.9 % | 17/40 (11 > 5 %), 51.2 % |
| 3 Ranking by conversion: disagreements, median regret | 12/40 (8 > 5 %), 8.9 % | 27/40 (24 > 5 %), 37.6 % |
| 3 (reference) Ranking by STY: median regret | 3.5 % | 22.4 % |
| 4 Unreported CO/CH4 split: all CO – all CH4 | 14–18/40 (6–12 > 5 %) | 26–29/40 (22–23 > 5 %; infeasible entries 0 / 0) |
| 5 Products close to MeOH + CO + CH4 (≥ 95 %) | 11/28 (6 > 5 %) | 17/28 (13 > 5 %) |
| 6 Catalyst priced from composition (3-year life) | 16/40 (8 > 5 %), median regret 5.5 % | 25/40 (22 > 5 %), median regret 25.8 % |
| 7 Recycled CO treated as inert (same limit for S6) | 21/40 (13 > 5 %) | 28/40 (24 > 5 %) |
| 7 Limit counts CH4 + N2 only (CO excluded), 6.86 % | = S5 (no limit) | 18/40 (8 > 5 %) |

### Item 8–9: kinds, mechanism, near-infeasibility

| | S5 (frozen, reproduced) | S6 |
|---|---|---|
| Disagreements (> 5 %), papers | 15 (7), 9 | 28 (22), 21 |
| Other catalyst / multi-catalyst groups (> 5 %) | 10/32 (4) | 16/32 (11) |
| … same temperature (> 5 %, papers of > 5 %) | 6 (0, 0) | 12 (8, 8) |
| … other temperature too (> 5 %) | 4 (4) | 4 (3) |
| Same catalyst, other temperature / temperature-series groups (> 5 %) | 5/22 (3) | 12/22 (11) |
| Plant leader more selective (share of disagreements) | 4 (27 %) | 19 (68 %) |
| Plant leader makes less CO | 3 (20 %) | 18 (64 %) |
| Plant leader has higher single-pass conversion | 9 (60 %) | 7 (25 %) |
| Plant leader runs cooler | 3 (20 %) | 11 (39 %) |
| Median regret of disagreements | 3.5 % | 22.4 % |
| Without Bansode 2013: disagreements (> 5 %) | 8/32 (1) | 21/32 (17) |
| Near-infeasible disagreements (PR #69 rule; > 5 %) | 0 | 11 (10) |
| Ordinary disagreements (> 5 %) | 15 (7) | 17 (12) |
| Noise-robust disagreements (×1, ≥ 90 %) that are ordinary | 11 of 11 | 13 of 24 |


Notes on the tables:
- Item 1C counts how many of the disagreements stay disagreements in at least 90 % of 2,000 re-measurements. The
  frozen error model is used at ×1, ×2 and ×4 (seed 20261006, frozen per-scenario streams). Under S6, every perturbed
  entry is re-costed with the constrained purge. An entry with no eligible purge level in a draw leaves both
  leaderboards of that draw (frozen rule).
- The noise floor depends only on the STY draws, so it is the same under S5 and S6.
- Regrets of the 24 S6 disagreements kept at ×1 (%): 2.6, 3.7, 8.2, 9.6, 11.9, 12.9, 13.3, 13.6, 14.5, 21.7, 23.1,
  36.4, 37.6, 53.1, 54.9, 61.3, 62.8, 78.5, 79.6, 83.1, 98.3, 108.8, 157.6, 299.4. Of these 24, 13 are ordinary and
  11 are near-infeasible under the PR #69 rule (regret > 1, or the STY leader's S6 cost > 2× its S5 cost). All 11
  near-infeasible disagreements are noise-robust.
- The four S6 disagreements that are not robust have probabilities 0.48–0.64. The kept ones start at 0.938.
- **Response-surface accuracy is lower under S6.** The constraint makes cost jump where a purge level enters or leaves
  the eligible set.
  - Against exact runs of 5 complete replicates per scenario, 7 of 600 group verdicts differ (S5: 1 of 600). At ×1 it
    is 4 of 200.
  - At ×1 the 99th percentile of the per-entry cost error is 3.4–5.8 % (S5: ≤ 0.5 %); it reaches 26 % at ×4.
  - About 1–2 % of verdicts disagree. Given the gap between 0.64 and 0.94, that cannot plausibly move the ×1 count of
    24. The ×4 counts are the least certain.
  - The ×1 figure has the same validation basis as the frozen S5 result. Use it, not ×4, for the text.
- Item 3: under S6 the conversion ranking disagrees more often than STY (27/40). The selectivity ranking disagrees
  less often (17/40), but its misses are larger (median regret 51 %).
- Item 4: neither bound makes any entry infeasible under S6.
- Item 7, CO-excluded: limiting only CH4 + N2 at 6.86 % gives 18/40, 8 above 5 %. That reproduces merged
  `analysis/meoh_inlet_definition_2026_10_12`.

## Plain summary

1. Every frozen S5 number reproduces exactly through the wrappers. The S6 anchors also reproduce: 28/40, 22 above
   5 %, 21 papers (18 with a disagreement above 5 %).
2. Under S6 the paper's STY leader is not the plant-cost leader in 28/40 groups. The paper-cluster 95 % interval is
   54–83 %; S5 gives 15/40 (15–57 %).
3. 707 of 1,997 pairwise orderings invert under S6, against 304 under S5.
4. Under measurement noise of the papers' own size, 24 of the 28 S6 disagreements persist in ≥ 90 % of
   re-measurements; S5 keeps 11 of 15. The noise floor (4.2 groups) is far below both.
5. 13 of those 24 noise-robust S6 disagreements are ordinary. The other 11 come from near-infeasibility under the
   6.86 % limit, so quote counts, not maxima.
6. Under S6, ranking by conversion is no better than ranking by STY (27/40). Ranking by selectivity disagrees less
   often (17/40) but with larger misses.
7. Under S6 the result does not depend on how unreported CO/CH4 is split (26–29/40), or on pricing each catalyst
   from its composition (25/40, 22 above 5 %).
8. Under S6 the result also holds in the closure ≥ 95 % subset (17/28) and with recycled CO treated as inert (28/40).
   Counting only CH4 + N2 brings it down to 18/40 (8 above 5 %).
9. The S6 disagreements are another catalyst in 16/32 multi-catalyst groups (11 above 5 %). Twelve of these are at
   the same temperature (8 above 5 %, from 8 papers). The rest are the same catalyst at another temperature in 12/22
   temperature-series groups (11 above 5 %).
10. Under S6 the plant leader is mostly more selective (68 %) and makes less CO (64 %); it has higher conversion in
    only 25 % (S5: 60 %). Without Bansode 2013 there are 21/32 disagreements (17 above 5 %), and the median regret
    is 22 % (S5: 3.5 %).

## Files and how to run

| Script | Items | Wraps (imported unchanged) | Swap |
|---|---|---|---|
| `run_stats_wrapper.py s5` / `s6` | 1 (A bootstrap, B regret curve, C noise) | `meoh_main_result_stats_2026_10_06/run_main_result_stats.py` | `exact_cost` → constrained optimum on the same capped sweep; `load` → `cost_recycled_opt_inlet`, `group_metrics_inlet_limit.csv` |
| `run_frozen_columns.py` | 2, 3, 5, 7, 8, 9 | `meoh_candidates.aggregate/bootstrap`, `mismatch_kinds.classify/leader_differences`, PR #69 `run_boundary` thresholds | cost column only |
| `run_selectivity_split_wrapper.py` | 4 | `run_selectivity_split.py` (`split`, `aggregate`, `classify`) | `lab_cost` → constrained optimum |
| `run_catalyst_cost_wrapper.py` | 6 | `run_catalyst_cost_inversion.py` (`build_candidates`, prices, `VARIANTS`, `_one` for S5) | eligible purge levels in `_one` |
| `verify_cache_sample.py` | cache check | – | recomputes 300 cached S6 runs; checks the S5 cost of every S6 run against the frozen cache |
| `build_report.py` | all | – | writes `results.json` and `results_tables.md`; checks every anchor |

Outputs:
- `stats_s5/` and `stats_s6/`: the frozen output set of the statistics script.
- `stats_s6/exact_cache.csv.gz`: 28,680 exact S6 runs. `s5_crosscheck.csv.gz` holds the S5 cost of each; 28,623 of
  them overlap the frozen cache and all agree to 1e-9.
- `frozen_columns.json`, `s6_groups.csv` (per-group S6 kind and near-infeasibility class), `selectivity_split.json`,
  `catalyst_cost.json`, `results.json`, `results_tables.md`.

Python 3.12, `pip install -r requirements.txt pyyaml`. Run order: `run_frozen_columns.py`, `run_stats_wrapper.py s5`,
`run_stats_wrapper.py s6` (about 75 min on 4 cores from nothing), `run_selectivity_split_wrapper.py`,
`run_catalyst_cost_wrapper.py`, `build_report.py`.

The workflow `.github/workflows/meoh-s6-robustness.yml` does the following:
- reruns all of it, rebuilding the noise statistics from the exact-run caches (`fresh=true` on dispatch recomputes
  every S6 run);
- recomputes a sample of the cache;
- checks the S5 anchors (15/40, 304/1,997, 31/40, 12/40, 11 of 15, 16/40, 14–18/40, 11/28) and the S6 anchors
  (28/40, 22 > 5 %);
- compares the regenerated outputs with the committed ones;
- confirms that the frozen folders are unchanged.
