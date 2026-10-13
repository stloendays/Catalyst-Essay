# Methanol field result: recycled CO converted up to CO-hydrogenation equilibrium (2026-10-13)

Question (anticipated referee): the frozen leaderboards convert recycled CO with `x_co='recycled_central'`, the LOWER
end of the thermodynamic window. The inert-limited result (reactor-inlet CH4 + CO + N2 <= 6.86 %, 28/40) rests on CO
build-up. What happens if recycled CO is converted more?

## Result (printed cohort, 40 comparison groups in 28 papers; `results_table.md`, `summary.json`)

| x_CO rule | no limit | 6.86 % (primary loop) | 5 % | 8 % | 10 % | 15 % |
|---|---|---|---|---|---|---|
| central (frozen) | 15/40 (7 > 5 %) | **28/40 (22)** | 26/40 (25) | 27/40 (22) | 24/40 (18) | 18/40 (12) |
| equal_X (x_CO = X, clipped into the window) | 14/40 (7) | **29/40 (21)** | 29/40 (24) | 24/40 (20) | 25/40 (16) | 17/40 (9) |
| high (x_CO at CO-hydrogenation equilibrium) | 14/40 (6) | **27/40 (19)** | 27/40 (18) | 27/40 (18) | 28/40 (15) | 18/40 (8) |

Groups whose STY leader is not the plant-cost leader (groups with that cost gap above 5 %). Infeasible entries: 0
of 351 under every rule and limit (no group lost).

At the 6.86 % limit:

| | central (frozen) | equal_X | high |
|---|---|---|---|
| different leader / > 5 % | 28/40 / 22 | 29/40 / 21 | 27/40 / 19 |
| papers with a disagreement (with > 5 %) | 21/28 (18) | 22/28 (15) | 19/28 (14) |
| other catalyst, of 32 multi-catalyst groups (> 5 %) | 16 (11) | 16 (11) | 15 (9) |
| ... same temperature / joint change | 12 (8) / 4 (3) | 13 (9) / 3 (2) | 12 (6) / 3 (3) |
| same catalyst, other temperature, of 22 (> 5 %) | 12 (11) | 12 (10) | 11 (9) |
| same catalyst, same temperature (> 5 %) | 0 | 1 (0) | 1 (1) |
| without Bansode 2013 (10.1039/c2cy20604h) | 21/32 (17) | 23/32 (16) | 20/32 (15) |
| median reactor-inlet CO at the optimum | 5.54 % | 4.31 % | 0.90 % |
| median purge at the optimum | 2.55 % | 1.55 % | 0.60 % |
| paper-cluster bootstrap 95 % CI (10,000, seed 20261006) | 54–83 % | 59–85 % | 50–81 % |

Unlimited loop: 15/40 (7) central, 14/40 (7) equal_X, 14/40 (6) high; bootstrap CI 15–57 %, 12–55 %, 12–55 %;
without Bansode 8/32 (1), 7/32 (1), 7/32 (1).

## Summary

1. The central rule reproduces the frozen `cost_recycled_opt`, `cost_recycled_opt_inlet` and `cost_recycled_opt_lim{5,8,10,15}` to 4.6e-12 relative (purges exactly), and the frozen 15/40 (7) and 28/40 (22).
2. Converting recycled CO up to CO-hydrogenation equilibrium (the upper end of the window) leaves the inert-limited disagreement in place: 27/40 groups, 19 with a cost gap above 5 %, in 19 of 28 papers (frozen: 28/40, 22, 21 papers).
3. CO converted at the CO2 per-pass fraction (equal_X): 29/40, 21 above 5 %.
4. Bootstrap 95 % CI at 6.86 %: 50–81 % (high) vs 54–83 % (central); without Bansode 2013 20/32 (15 > 5 %) vs 21/32 (17).
5. Both kinds survive under high: other catalyst 15/32 (9 > 5 %), same catalyst at another temperature 11/22 (9 > 5 %).
6. No entry becomes infeasible under any rule or limit (0/351); the limit sweep 5–10 % stays at 27–28/40 under high and falls to 18/40 at 15 %, as for central.
7. The unlimited loop is insensitive to the rule (14–15/40, 6–7 above 5 %).
8. Why the inlet-limited result holds: under high the median inlet CO share falls to 0.9 %, but in the disagreeing groups the STY leaders still carry 5.5 % inlet CO (median; plant leaders 1.7 %), because at their conditions (median 260 °C vs 240 °C, S_CO 0.37 vs 0.29) CO-hydrogenation equilibrium allows only x_CO ≈ 0.12 per pass (plant leaders 0.20).
9. So the CO build-up that penalises the STY leaders is set by CO-hydrogenation equilibrium itself, not by choosing the lower end of the window: the STY leader carries more inlet CO in 20 of the 27 disagreements and needs a larger purge in 22.
10. Plainly: yes, the inert-limited disagreement holds when recycled CO converts up to CO-hydrogenation equilibrium (27/40, 19 above 5 %); it is not an artefact of the lower-bound CO rule.

## Method

`run_co_conversion_bound.py` reads the frozen printed-cohort inputs (`analysis/meoh_literature_inversion_2026_10_05/literature_candidates.csv`,
full precision) and, for each of the 351 entries and each rule, runs `meoh_general_model.purge_sweep` exactly as
`meoh_candidates.plant_costs` does (conversion capped at the loop's CO2-hydrogenation equilibrium, canonical purge
grid 0.5–40 %, `STY_per_g_cat` = group STY basis). Minimum cost over: every finite level (no limit, as
`cost_recycled_opt`); `eligible_purges` (equilibrium feasible and CH4 + CO + N2 <= 6.86 %, as `cost_recycled_opt_inlet`);
equilibrium feasible and nonreactive <= 5 / 8 / 10 / 15 % (as `cost_recycled_opt_lim<L>`). The rules are those of
`meoh_general_model.resolve_x_co`, re-evaluated at each purge level and at the capped conversion:
`recycled_equal_X` x_CO = clip(X, x_central, x_MeOH), `recycled_high` x_CO = x_MeOH. Gate: the central columns must
reproduce the frozen ones to 1e-6 relative with the same NaN pattern, or the script stops.

Scoring with the frozen code only: `meoh_candidates.aggregate(frame, col, up_col='STY')`, `meoh_candidates.bootstrap`
(10,000 paper resamples, seed 20261006), `mismatch_kinds.classify`. "Median inlet CO / purge" is over the entries of
the scored groups at each entry's optimum. "Leaders" in `summary.json` compares the STY and plant-cost leaders of the
disagreeing groups.

## Files

- `run_co_conversion_bound.py`: the run (about 2 min on 4 cores; `COB_WORKERS`).
- `summary.json`: gate, frozen anchors, per rule x limit results, x_CO used, leader comparison, infeasible counts.
- `results_table.md`: the full rule x limit table (generated).
- `entry_costs.csv`: per-entry cost, purge, inlet CO share, nonreactive share, x_CO and X_eff at every optimum.
- `group_results.csv`: per-group leader, regret and kind for every rule x limit.
- CI: `.github/workflows/meoh-co-conversion-bound.yml` reruns, checks the gate and anchors, compares `summary.json`
  (counts exact, floats 1e-6) and checks that the frozen folders are unchanged.

No manuscript, figure, frozen output or existing folder is changed.
