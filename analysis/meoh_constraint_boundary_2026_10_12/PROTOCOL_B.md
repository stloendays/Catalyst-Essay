# Protocol B (pre-registered): can a laboratory-only rule predict the plant-cost leader?

Committed on 2026-10-12, before any quantity of Task B was computed. The commit that adds this file contains no
Task B code and no Task B output; `run_rules.py` and its outputs are added in later commits and must follow this
file. Any analysis not fixed here is labelled **post hoc** wherever it is reported.

## What was known when this protocol was written

- The frozen S5 result scores four paper leaderboards (README of `analysis/meoh_literature_inversion_2026_10_05`):
  the plant-cost leader differs from the leader by STY in 15 / 40 groups, by single-pass yield X·S in 15 / 40, by
  conversion X in 12 / 40 and by methanol selectivity in 31 / 40.
- Under the reactor-inlet limits only the STY leaderboard has been scored (frozen `summary.json` limit_sweep, S6
  28 / 40, and the Task A reproduction of this branch: lim4 28 / 40, lim10 24 / 40, lim20 19 / 40, lim30 16 / 40).
- No other rule has been scored by this branch on any scenario, and no out-of-paper selection has been run.

## Data and units of analysis

- Candidates: `analysis/meoh_literature_inversion_2026_10_05/literature_candidates.csv` (frozen, printed cohort),
  read as it is; nothing is re-extracted or re-costed.
- Comparison groups: the 40 groups of 28 papers scored by `meoh_candidates.aggregate` (groups with at least two
  entries with a finite cost in the scenario column). Within a scenario only the entries with a finite cost in that
  scenario's column are candidates of their group (frozen convention: an infeasible entry leaves both leaderboards).
- Plant-cost leader of a group: the entry with the lowest cost in the scenario column. An entry is one operating
  point (catalyst at its temperature); "the rule chose the plant-cost leader" means the same entry.

## Scenarios (12)

| Scenario | Cost column |
|---|---|
| S5 (no inlet limit, frozen primary) | `cost_recycled_opt` |
| S6 (reactor-inlet non-H2/CO2 fraction <= 6.86 %) | `cost_recycled_opt_inlet` |
| lim4, lim5, lim6, lim8, lim10, lim12, lim15, lim20, lim25, lim30 | `cost_recycled_opt_lim{4,...,30}` |

## Candidate laboratory-only rules (9)

Each rule uses only the candidate-file columns `STY`, `X`, `SMeOH`, `SCH4` and `T_C` (laboratory quantities as the
plant model receives them: closed selectivities; `SCH4` is the frozen model input, imputed from the residual where
the paper prints no CH4 selectivity). Each rule picks, within a group, the entry with the best score.

| Rule | Picks the entry with the |
|---|---|
| R1 `STY` (baseline: the paper's own leaderboard) | highest STY |
| R2 `S` | highest methanol selectivity |
| R3 `STY*S` | highest STY x S |
| R4 `STY*S^2` | highest STY x S^2 |
| R5 `STY*S^4` | highest STY x S^4 |
| R6 `STY*S^8` | highest STY x S^8 |
| R7 `X*S` | highest single-pass methanol yield X x S |
| R8 `lowCH4` | lowest CH4 selectivity |
| R9 `lowT` | lowest reaction temperature |

**Ties.** Entries within a relative 1e-9 of the rule's best score are tied; ties are broken by the higher STY.
Entries still tied (equal score and equal STY) form the rule's choice set, scored as the frozen `group_metrics`
scores the STY leaderboard: the group counts as correct when the plant-cost leader is in the set, and the regret is
that of the cheapest member. Sensitivity (reported, not used for decisions): the expected value under a uniform
choice from the set.

## Metrics

Per group and rule: **correct** (the rule's choice is the plant-cost leader) and **regret** = (cost of the rule's
choice - cost of the plant-cost leader) / cost of the plant-cost leader.

Per scenario: **accuracy** = correct groups / 40 (primary) and **mean regret** over the 40 groups (primary);
median regret and the number of groups with a regret above 5 % (secondary).

## Selection procedure: leave one paper out

Run separately in each scenario, with that scenario's costs.

1. For each of the 28 papers p: the training set is the groups of the other 27 papers. Score every rule R1-R9 on it.
2. Choose the rule with the highest training accuracy; ties go to the lower training mean regret, then to the earlier
   rule in the order R1 ... R9 (a tie therefore keeps the STY baseline).
3. Apply the chosen rule to the groups of paper p and record correct and regret.
4. Out-of-paper accuracy = correct held-out groups summed over the 28 folds / 40; out-of-paper mean regret = mean of
   the 40 held-out regrets. The rule chosen in each fold is reported.

Secondary selection criterion (reported alongside, designated secondary): the lowest training mean regret, ties to
the higher training accuracy, then the rule order.

**Baseline.** R1 (STY) on all 40 groups, no selection. Anchor: under S5 it must give 25 / 40 correct (the frozen
15 / 40 different leaders), under S6 12 / 40, and under each limit 40 minus the Task A count of different leaders.

**Comparison with the baseline, per scenario.** Difference in correct groups (out-of-paper selection minus STY);
exact two-sided McNemar test on the discordant groups; paper-cluster bootstrap 95 % interval of the accuracy
difference and of the mean-regret difference (10,000 resamples of the 28 papers with replacement, seed 20261012).
The selection is re-run inside every resample: a fold leaves out every copy of the held-out paper, and the training
accuracies and regrets are weighted by the resample multiplicities.

Also reported for every rule: its accuracy and mean regret on all 40 groups (a fixed rule is not fitted, so this is
an out-of-sample figure for that rule; picking the best of them after the fact is not, and is labelled as such).

## Loop-aware rule (fixed here, not selected from data)

- **LA1 (primary).** S5 (no inlet limit): rank by STY (R1). Every inlet-limited scenario (S6, lim4-lim30): rank by
  methanol selectivity (R2, ties by STY).
- **LA2 (secondary).** Group by group: rank by R2 when the scenario's limit is below the reactor-inlet non-H2/CO2
  fraction of the group's STY leader at its S5 optimum (`nonreactive_at_opt_recycled`), that is, when the limit binds
  on the laboratory leader; otherwise rank by R1. In S5 always R1.

**Test.** LA1 "beats every single rule across scenarios" when its pooled accuracy over the 12 scenarios (480
group-scenarios, scenarios weighted equally) is strictly higher than the pooled accuracy of each of R1-R9. Reported
with it: the pooled mean regret of LA1 and each rule, the per-scenario accuracy of LA1 against the best single rule of
that scenario, and paper-cluster bootstrap 95 % intervals (10,000 resamples, seed 20261012, the same resamples for
all rules) of LA1 minus each rule in pooled accuracy. The difference is called clear only when every interval
excludes zero. LA2 is reported the same way.

## Reporting

Every number above is reported whatever its direction, negative results included, per scenario next to the STY
baseline. No rule, scenario, metric, tie convention or selection criterion is added or changed after the results are
seen, except as an analysis labelled post hoc.
