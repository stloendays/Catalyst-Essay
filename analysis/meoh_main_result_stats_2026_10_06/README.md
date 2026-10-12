# How firm is the methanol field result? — 2026-10-06, updated 2026-10-07

Field result (`analysis/meoh_literature_inversion_2026_10_05/`, 50-paper set, primary treatment of 2026-10-07):
within published CO2-to-methanol comparisons, the paper's space-time-yield (STY) leader is not the plant-cost leader
in **54 of 82** comparison groups (37 of 44 papers). The primary caps the per-pass CO2 conversion at
CO2-hydrogenation equilibrium, converts recycled CO only up to reverse-water-gas-shift and CO-hydrogenation
equilibrium, and optimizes the purge only where the reactor inlet holds no more species other than H2 and CO2 than
the calibrated reference loop (6.86 %). This folder asks four questions of that number:
- its sampling uncertainty;
- how large the disagreements are;
- whether they survive measurement noise;
- whether they survive the agent's extraction errors.

The plant model, candidate construction and group definitions are those of the field-result script and are not
changed.

## Running it

`run_main_result_stats.py` writes `summary.json`, `regret_threshold_curve.csv`, `group_noise_probabilities.csv`,
`validation.csv`, `grid_costs.csv` (the exact runs behind the response surface) and `scenario_*.json` (each finished
noise scenario). Every exact plant-model run (about 1.5e5) is stored in `exact_cache.csv.gz` under a key made of the
entry state and the perturbation, so no run is repeated and the work can be split:

- **GitHub Actions** (`.github/workflows/methanol-stats.yml`): push a commit whose message contains `[ci stats]`
  (add `[fresh]` to rebuild the cache from nothing), or dispatch the workflow. It lists the missing grid runs, runs
  them on a 20-job matrix, lists every draw outside the grid and the validation replicates, runs those on a second
  20-job matrix, then runs the full analysis from the cache and commits the outputs back to the branch. The result
  is identical to one serial run: the draws come from the same per-scenario random streams and do not depend on
  exact results, only on the completed grid.
- **Locally**: `python run_main_result_stats.py` computes whatever the cache lacks with `STATS_WORKERS` processes
  (default 4). Use no more than 8 on the 15 GB laptop: each worker commits about 0.8 GB, and 24 workers exhausted it
  (`run_aborted_24workers.log`). The modes behind the workflow are `STATS_MODE=enumerate`, `compute JOBS SHARD N OUT`
  and `merge PART...`.

`run_failed_infeasible.log` is a run that stopped when an extreme perturbation left the plant model's feasible loop.
Such states are treated as missing, and the entry leaves both leaderboards of that draw.

## Result (current primary; GitHub Actions run 37598533207)

| Question | Result |
|---|---|
| Point estimate | 54 / 82 groups (65.9 %), 37 / 44 papers; paper-weighted 74.6 % |
| **Sampling uncertainty** (paper-cluster bootstrap, 10,000 resamples) | **95 % CI 51.5–80.0 %** (paper-weighted 62.7–85.7 %) |
| **Size**: mismatches whose regret is at least | 1 %: 51 (36 papers) · 2 %: 50 · 5 %: 46 · **10 %: 42 (31 papers)** |
| **Measurement noise** (each entry re-measured, measured error ×1) | 54.0 mismatched groups on average (95 % range 50–58); **47 of the 54 stay mismatched in ≥ 90 % of re-measurements**, all with regret ≥ 1 % (median 45 %) |
| Noise floor (re-measurement alone changes the reported STY leader) | 12.1 groups (7–17) at ×1 · 21.2 (15–28) at ×2 · 33.6 (26–41) at ×4 |
| **Extraction error** (plot readings resampled from the agent's measured errors, plus noise ×1) | 55.6 mismatched groups (50–61); 40 stay mismatched in ≥ 90 % of draws |
| Response surface against exact runs | 18 of 1,640 group verdicts differ (5 exact replicates per scenario) |

Even at four times the measured error, the noise floor (33.6) stays below the observed 54.

## Result of the previous treatment (33 / 83; superseded by the CI run of the current primary)

| Question | Result |
|---|---|
| Point estimate | 33 / 83 groups (39.8 %), 19 / 44 papers; paper-weighted 36.9 % |
| **Sampling uncertainty** (paper-cluster bootstrap, 10,000 resamples) | **95 % CI 23.7–55.1 %** (paper-weighted 23.6–50.3 %) |
| **Size**: mismatches whose regret is at least | 0.5 %: 27 (32.5 %) · **1 %: 23 (27.7 %, 12 papers)** · 2 %: 16 (19.3 %) · 5 %: 9 (10.8 %) · 10 %: 4 (one paper) |
| **Measurement noise** (each entry re-measured, measured error ×1) | 37.3 mismatched groups on average (95 % range 31–43); **15 of the 33 stay mismatched in ≥ 90 % of re-measurements**, all with regret ≥ 1 % (median 5.9 %), from 8 papers |
| Noise floor (how often re-measurement alone changes the reported STY leader) | 13.4 groups (8–19) at ×1 · 22.4 (16–29) at ×2 · 34.1 (27–42) at ×4 |
| **Extraction error** (plot readings resampled from the agent's measured errors, plus noise ×1) | 38.5 mismatched groups (31–45); 10 stay mismatched in ≥ 90 % of draws |

### How to read the noise rows

**Re-measurement.** Each entry's conversion, selectivity and STY are drawn again from the measurement error, and both
leaderboards are rebuilt from the same drawn entry.

**Noise floor.** It counts the groups whose reported STY leader changes under that re-measurement. It is an upper
bound on the disagreement that measurement noise alone could create if the plant leader were always the true STY
leader:

| Measured error | Noise floor (groups) | Compared with the observed 33 |
|---|---|---|
| ×1 | 13 (95 % range 8–19) | well below |
| ×2 | 22 (16–29) | below |
| ×4 | 34 (27–42) | reaches it |

The disagreement is therefore not explained by measurement noise of the size the papers' own data imply.

**Groups that disagree in only some draws.** These are near-ties in STY or in plant cost; their regret is small
(median 0.9 % for the 18 observed mismatches that are not robust). The 15 robust disagreements carry the cost
consequence.

## Error model

From `analysis/meoh_measurement_mc_2026_10_05/uncertainty_basis.json`, derived from the Re/TiO2 paper's own data:
- relative CO2-conversion error r_X = 5.21 % (log-normal);
- sum-conserving MeOH → CH4 selectivity transfer, σ = 0.847 percentage points (absolute; for the few entries with
  methanol selectivity of a few percent this is a large relative error, which only adds noise);
- printed STY: an independent relative error r_X (cross-detector scatter);
- STY derived from space velocity follows the perturbed X·S_MeOH.

Scales ×2 and ×4 multiply all three.

Extraction errors: the adjudicated plot and SI-plot readings in `agent/extraction/eval/field_scores.csv`:
- 258 conversion ratios (ln extracted/curated);
- 240 methanol-selectivity differences (applied as a MeOH ↔ CO transfer, the closure residual);
- 190 STY ratios.

They are resampled for the 534 plot-read entries; the STY error applies only where the group uses printed STY.

## Response surface and its validation

- **The surface.** Each of the 906 entries gets an additive, piecewise-linear response from exact runs of the plant
  model on a grid in each perturbation coordinate: ln X, MeOH→CH4, MeOH→CO, ln STY. The grid spans ±2.5 in ln and up
  to ±0.15 in selectivity, inside each entry's physical range.
- **Off-grid draws.** Every draw outside the grid is run exactly: 14,202 to 46,173 runs per scenario.
- **Unperturbed costs.** At zero perturbation the surface equals the frozen candidate costs to 4.9e-6 (relative,
  6-digit CSV).
- **Validation.** For each scenario, 5 complete replicates were run exactly with the same draws. Of 1,660 group
  verdicts, the surface and the exact model differ in 6 (0.4 %), all at ×2 and ×4 or with extraction errors.
  Per-entry cost errors have a 99th percentile of 0.3–0.5 % at ×1 and ≤ 7 % at ×4 (`validation.csv`).
