# Paper leaderboards versus plant-cost leaderboards (CO2-to-methanol) — frozen treatment of 2026-10-12

`run_literature_inversion.py` takes the literature-extraction Agent's output (`agent/extraction/out/records_normalized.csv`,
used as extracted) through the methanol recycle-economics model (`data/meoh/meoh_general_model.py`) and compares,
within each paper, the paper's own leaderboard with the plant-cost leaderboard.

Treatment (author decisions of 2026-10-08; step S5 of `analysis/verify_2026_10_08/meoh_decomposition.py`):

- **Cohort: printed values only.** CO2 conversion and methanol selectivity printed, and every CO / CH4 selectivity the
  paper reports printed too; a printed STY sets a group's basis only where it is itself printed. Plot readings enter
  the all-entries sensitivity. 351 entries from 33 studies; 40 comparison groups with 310 entries in 28 papers.
- **Comparison groups:** entries of one paper at the same P, H2/CO2 and space velocity (the comparison the paper itself
  makes: catalysts, and temperatures of one catalyst). One measurement printed in several places counts once (same
  catalyst, temperature and values).
- **Paper leaderboard:** methanol STY per g catalyst (printed when every entry of the group prints it and printed STY /
  conversion-derived productivity varies by no more than 3x; otherwise derived from the space velocity).
- **Plant leaderboard:** net production cost at each entry's own T, P and H2/CO2; recycled CO bounded by RWGS and
  CO-hydrogenation equilibrium; per-pass CO2 conversion = the laboratory value, capped where the loop outlet reaches
  CO2-hydrogenation equilibrium; cost-optimal purge over the canonical grid (0.5–40 %).

The extracted Gothe et al. (2025) Table 4 entries reproduce the frozen Table 4 costs to 2.3e-13 EUR/t; the four
canonical states are 943.30, 961.51, 966.96 and 1258.17 EUR/t (`selfcheck_gothe_table4.csv`).

## Result

| Leaderboard / treatment | Groups with a different winner | Papers | Regret, median of mismatched / max | Regret > 5 % | Pairwise orderings inverted |
|---|---|---|---|---|---|
| **STY (primary)** | **15 / 40 (38 %)** | **9 / 28** | **3.5 % / 83 %** | **7 (2 papers)** | **304 / 1,997** |
| single-pass yield X·S_MeOH | 15 / 40 | 9 / 28 | 3.5 % / 83 % | 7 | 309 / 1,997 |
| conversion X | 12 / 40 | 8 / 28 | 8.9 % / 131 % | 8 | 261 / 1,997 |
| methanol selectivity S_MeOH | 31 / 40 (78 %) | 22 / 28 | 19.9 % / 2,617 % | 24 | 1,112 / 1,997 |

Paper-cluster bootstrap of the primary (10,000 resamples of papers): 95 % CI 15–57 %. Paper-weighted share 27 %.

Disagreements of the primary by kind (`mismatch_kinds.py`, `summary.json` primary.kinds), with denominators:

| Kind | Groups | Regret > 5 % |
|---|---|---|
| other catalyst, same temperature | 6 | 0 |
| other catalyst and temperature (joint change) | 4 | 4 |
| other catalyst, total (of 32 groups with ≥ 2 catalysts) | 10 / 32 | 4 |
| same catalyst at another temperature (of 22 groups with a temperature series) | 5 / 22 | 3 |
| same catalyst, same temperature | 0 | 0 |

Six of the seven disagreements with a regret above 5 % are groups of Bansode 2013 (10.1039/c2cy20604h); without that
paper the result is 8 / 32 groups, one with a regret above 5 % (h-In2O3-R, Dang 2020, 11.6 %).

Sensitivities (printed cohort unless stated; `summary.json` variants, limit_sweep, isothermal):

| Variant | Different winner |
|---|---|
| inert CO | 21 / 40 |
| 2 % purge | 12 / 40 |
| laboratory conversion uncapped (step S4) | 16 / 40 |
| reactor-inlet non-H2/CO2 limit 6.86 % (step S6) | 28 / 40 |
| inlet limit 4–30 % (absolute) | 28 → 16 / 40 |
| bulk density 0.5 / 2.0 g/mL | 15 / 40, 14 / 40 |
| reported selectivities sum to ≥ 95 % | 11 / 28 |
| isothermal catalyst comparisons (one temperature, ≥ 2 catalysts) | 21 / 62 |
| all entries, plot readings included | 35 / 83 (24 / 44 papers) |
| all entries, inlet limit 6.86 % | 54 / 82 |

At the primary optimum every entry sits at the lowest purge level of the grid (0.5 %), with a median reactor-inlet
non-H2/CO2 fraction of 13.6 % (`summary.json` thermodynamics); the inlet-limit sweep above shows how the result moves
when that fraction is bounded. The two checks below (author decision 2026-10-12: S5 stays the pre-specified primary)
test that purge optimum.

## Purge boundary and inlet-constrained optimization (`run_purge_boundary.py`, ED Fig. 8)

Same model and treatment as S5; the purge grid is extended below 0.5 % (120 log-spaced levels down to 1e-4 %, 516
levels in all). The canonical part of the grid reproduces the primary costs to < 1e-6 EUR/t.

**1. Purge boundary.** The 0.5 % optimum is the edge of the grid, not a minimum of the cost: on the extended grid the
optimum lies below 0.5 % for 309 of the 310 scored entries (median 0.048 % purge, none at the new floor), and the cost at
0.5 % exceeds it by a median 10.9 % (> 1 % for 299 entries, > 10 % for 159). Above 0.5 % the cost rises monotonically for
every entry. At the extended optimum the reactor inlet carries a median 40 % of species other than H2 and CO2 (10th–90th
percentile 28–64 %) and the recycle ratio (recycle / fresh make-up, molar) is a median 44 (the anchor loop: 2.85). The
leaderboard count barely moves (14 / 40, regret > 5 % in 2; plant-cost winner changed in 6 groups), because the
optimum moves for all entries of a group together.

**2. Inlet-constrained optimization.** Minimum cost over the extended grid with the reactor-inlet non-H2/CO2 fraction
within published CO2-to-methanol loop designs (`inlet_inert_literature.csv`): the cost model's anchor loop (Campos et
al. 2022 one-step, 6.86 % as reproduced by the model) and the envelope of the four published designs (4.92 % Nieminen et
al. 2019 to 10.25 % Campos et al. 2022 three-step). No entry is infeasible.

| Inlet limit | Different winner | Regret > 5 % | Other catalyst / of 32 | Other T / of 22 | Winner changed vs S5 | Median purge | Median recycle ratio | Mean inlet CO / CH4 / N2 (mol%) |
|---|---|---|---|---|---|---|---|---|
| none, grid 0.5–40 % (S5) | 15 / 40 | 7 | 10 | 5 | — | 0.5 % | 27.6 | 9.8 / 2.7 / 4.1 |
| none, extended grid | 14 / 40 | 2 | 7 | 7 | 6 | 0.048 % | 43.9 | 15.2 / 6.5 / 21.3 |
| ≤ 10.25 % (highest published) | 24 / 40 | 18 | 14 | 10 | 18 | 1.0 % | 16.7 | 6.6 / 0.6 / 2.7 |
| ≤ 6.86 % (anchor loop) | 28 / 40 | 22 | 16 | 12 | 24 | 2.55 % | 13.4 | 4.8 / 0.3 / 1.6 |
| ≤ 4.92 % (lowest published) | 26 / 40 | 25 | 16 | 10 | 24 | 4.2 % | 9.6 | 3.5 / 0.2 / 1.1 |

Paper-cluster 95 % CI: 44–73 % (10.25 %), 54–83 % (6.86 %), 52–78 % (4.92 %). Under the constraint the result no longer
rests on one paper: Bansode 2013 contributes 5–7 disagreements and without it 18–21 / 32 remain (13–20 with a regret
above 5 %). The plant-cost leader is now the more selective catalyst (17–21 of the disagreements; under S5, 4 of 15)
and the one making less CO (16–20; S5 3): CO and CH4 must leave through the purge to hold the inlet composition, which
costs H2. Sweep of the limit on the extended grid: 3 % 27 / 39, 4–10 % 25–28 / 40, 15 % 22, 20 % 19, 25–30 % 16, 40 % 15.

Outputs: `purge_boundary_summary.json`, `purge_boundary_entries.csv` (one row per scored entry, every treatment),
`purge_boundary_curves.csv` (cost and loop state along the grid), `group_metrics_purge_{extended,published_min,anchor,
published_max}.csv`. About 3.5 min on 6 workers.

Further sensitivities on the frozen candidates:

- `run_conversion_sensitivity.py`: each catalyst may load more catalyst and raise its conversion towards equilibrium
  (calibrated first-order approach, measured selectivities held): 14 / 40, regret > 5 % in 3; other catalyst 5 / 32,
  same catalyst at another temperature 9 / 22. Caps 0.90, 0.95 and 0.99 X_eq give the same result.
- `run_selectivity_split.py`: 176 of the 310 entries print no CH4 selectivity. All unreported carbon as CO: 14 / 40
  (regret > 5 % in 6); all as CH4: 18 / 40 (12).

Statistics (`analysis/meoh_main_result_stats_2026_10_06`), pruning (`analysis/meoh_pruning_2026_10_06`), catalyst
charges (`analysis/meoh_catalyst_cost_2026_10_06`) and plant-term variants (`analysis/meoh_plant_benchmark_2026_10_06`)
run on the same candidates.

## Outputs

`literature_candidates.csv` (printed cohort, the primary), `literature_candidates_all_entries.csv`, `group_metrics.csv`,
`group_metrics_all_entries.csv`, `group_metrics_inlet_limit.csv`, `group_metrics_isothermal.csv`,
`selfcheck_gothe_table4.csv`, `summary.json`, `mismatch_kinds.json`, `conversion_sensitivity_*`,
`selectivity_split_*`. About 5.5 min on 4 workers (`INV_WORKERS`); the conversion sensitivity about 16 min.
`.github/workflows/methanol-main-result.yml` reruns the field result on ubuntu-latest and compares it with the committed
summary.

## History

| Treatment | Groups with a different winner |
|---|---|
| original treatment, all entries (main until 2026-10-08) | 33 / 83 |
| thermodynamic treatment with the 6.86 % inlet limit (2026-10-07, closed PR #36) | 54 / 82 |
| frozen: printed values, step S5 (2026-10-12) | 15 / 40 |

The step-by-step decomposition between them is `analysis/verify_2026_10_08/meoh_decomposition.py`.
