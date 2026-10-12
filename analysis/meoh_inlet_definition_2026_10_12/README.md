# Methanol inlet limit: which species it counts, and how 83 groups become 40 (2026-10-12)

Two questions from the supervisor about the inert-limited loop, which the supervisor has chosen as the primary loop.
**Q1:** the frozen inlet limit caps (CH4 + CO + N2) / reactor inlet, but recycled CO is converted per pass. Is
counting CO consistent? What happens if only the true inerts (CH4 + N2) are counted? **Q2:** how do the 83 groups of
2026-10-08 become the 40 of the frozen primary?

Nothing frozen is changed. This folder only reads `analysis/meoh_literature_inversion_2026_10_05/` and scores it with
that folder's own code (`meoh_candidates.aggregate(frame, col, up_col='STY')`, `mismatch_kinds.classify`).

**Reproduction.** The frozen definition (CH4 + CO + N2) re-derives `cost_recycled_opt` (S5),
`cost_recycled_opt_inlet` (6.86 %) and `cost_recycled_opt_lim{4..30}` for all 351 printed-cohort rows with the same
NaN pattern and a maximum relative difference of 2.3e-11, below the 1e-6 tolerance. The anchors all match: S5 15/40,
6.86 % 28/40, lim4 28/40, lim10 24/40, lim30 16/40.

## 1. Definition x limit (printed cohort, 40 groups, 28 papers)

The 6.86 % limit is the anchor loop's exact value (`G.NONREACTIVE_MAX` = 6.8625 %). "none" is S5, which is the same for
both definitions. Bracketed ranges are paper-cluster bootstrap 95 % intervals (28 papers resampled, 10,000 draws, seed
20261012, the same resamples for every row). Kinds are given as groups (of which > 5 %). Other catalyst has a
denominator of 32 multi-catalyst groups; other temperature has 22 temperature-series groups. The split is ordinary vs
near-infeasible, each with its count > 5 %. Shares are the medians of CO and of CH4+N2 in the reactor inlet at each
entry's optimum. "Binds" counts entries whose cost rises above S5.

| definition | limit % | different leader /40 [CI] | regret > 5 % [CI of fraction] | papers with disagreement /28 | without Bansode /32: diff, > 5 % | other cat., same T | other T | other cat. and T | median regret (disagreements) | ordinary / near-infeasible | CO / CH4+N2 share % | binds /310 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| — | none (S5) | 15 [15-57%] | 7 [0-38%] | 9 | 8, 1 | 6 (0) | 5 (3) | 4 (4) | 3.5% | 15 (7) / 0 (0) | 7.1 / 4.3 | 0 |
| CH4+CO+N2 | 4 | 28 [58-84%] | 25 [49-76%] | 23 | 23, 20 | 12 (10) | 11 (11) | 5 (4) | 63.5% | 8 (6) / 20 (19) | 3.3 / 0.6 | 278 |
| CH4+CO+N2 | 5 | 26 [52-78%] | 25 [49-76%] | 21 | 21, 20 | 12 (11) | 11 (11) | 3 (3) | 67.4% | 7 (7) / 19 (18) | 4.1 / 0.7 | 274 |
| CH4+CO+N2 | 6 | 27 [56-81%] | 24 [46-73%] | 22 | 22, 19 | 12 (9) | 11 (11) | 4 (4) | 34.6% | 14 (12) / 13 (12) | 4.9 / 0.8 | 264 |
| CH4+CO+N2 | **6.86** | **28 [54-83%]** | **22 [41-69%]** | 21 | 21, 17 | 12 (8) | 12 (11) | 4 (3) | 22.4% | 17 (12) / 11 (10) | 5.5 / 1.0 | 260 |
| CH4+CO+N2 | 8 | 27 [54-80%] | 22 [38-69%] | 21 | 21, 16 | 12 (8) | 12 (11) | 3 (3) | 14.3% | 20 (16) / 7 (6) | 6.2 / 1.1 | 251 |
| CH4+CO+N2 | 10 | 24 [44-73%] | 18 [29-58%] | 18 | 18, 13 | 11 (8) | 10 (7) | 3 (3) | 9.7% | 16 (10) / 8 (8) | 6.9 / 1.6 | 241 |
| CH4+CO+N2 | 12 | 24 [47-73%] | 13 [17-46%] | 19 | 19, 9 | 13 (6) | 7 (3) | 4 (4) | 7.3% | 20 (9) / 4 (4) | 7.2 / 2.1 | 211 |
| CH4+CO+N2 | 15 | 18 [29-58%] | 12 [15-43%] | 14 | 13, 8 | 10 (6) | 4 (2) | 4 (4) | 8.9% | 17 (11) / 1 (1) | 7.1 / 2.7 | 125 |
| CH4+CO+N2 | 20 | 19 [26-65%] | 10 [5-45%] | 13 | 12, 4 | 9 (2) | 6 (4) | 4 (4) | 5.0% | 17 (8) / 2 (2) | 7.1 / 3.7 | 77 |
| CH4+CO+N2 | 25 | 17 [20-61%] | 9 [3-42%] | 11 | 10, 3 | 7 (1) | 6 (4) | 4 (4) | 5.0% | 17 (9) / 0 (0) | 7.1 / 3.9 | 49 |
| CH4+CO+N2 | 30 | 16 [18-59%] | 8 [0-40%] | 10 | 9, 2 | 6 (0) | 6 (4) | 4 (4) | 4.3% | 16 (8) / 0 (0) | 7.1 / 4.1 | 34 |
| CH4+N2 | 4 | 19 [23-69%] | 8 [0-39%] | 12 | 11, 2 | 9 (1) | 6 (3) | 4 (4) | 4.8% | 19 (8) / 0 (0) | 7.2 / 3.6 | 160 |
| CH4+N2 | 5 | 18 [23-63%] | 8 [0-39%] | 12 | 11, 2 | 9 (1) | 5 (3) | 4 (4) | 3.4% | 18 (8) / 0 (0) | 7.2 / 4.3 | 130 |
| CH4+N2 | 6 | 18 [23-63%] | 8 [0-39%] | 12 | 11, 2 | 9 (1) | 5 (3) | 4 (4) | 2.4% | 18 (8) / 0 (0) | 7.1 / 4.3 | 105 |
| CH4+N2 | **6.86** | **18 [23-63%]** | **8 [0-39%]** | 12 | 11, 2 | 9 (1) | 5 (3) | 4 (4) | 2.1% | 18 (8) / 0 (0) | 7.1 / 4.3 | 90 |
| CH4+N2 | 8 | 15 [15-57%] | 8 [0-39%] | 9 | 8, 2 | 6 (1) | 5 (3) | 4 (4) | 8.3% | 15 (8) / 0 (0) | 7.1 / 4.3 | 72 |
| CH4+N2 | 10 | 15 [15-57%] | 8 [0-39%] | 9 | 8, 2 | 6 (1) | 5 (3) | 4 (4) | 6.7% | 15 (8) / 0 (0) | 7.1 / 4.3 | 50 |
| CH4+N2 | 12 | 16 [18-59%] | 8 [0-39%] | 10 | 9, 2 | 7 (1) | 5 (3) | 4 (4) | 3.9% | 16 (8) / 0 (0) | 7.1 / 4.3 | 34 |
| CH4+N2 | 15 | 15 [15-57%] | 8 [0-39%] | 9 | 8, 2 | 6 (1) | 5 (3) | 4 (4) | 5.0% | 15 (8) / 0 (0) | 7.1 / 4.3 | 24 |
| CH4+N2 | 20 | 15 [15-57%] | 7 [0-38%] | 9 | 8, 1 | 6 (0) | 5 (3) | 4 (4) | 3.6% | 15 (7) / 0 (0) | 7.1 / 4.3 | 21 |
| CH4+N2 | 25 | 15 [15-57%] | 7 [0-38%] | 9 | 8, 1 | 6 (0) | 5 (3) | 4 (4) | 3.5% | 15 (7) / 0 (0) | 7.1 / 4.3 | 14 |
| CH4+N2 | 30 | 15 [15-57%] | 7 [0-38%] | 9 | 8, 1 | 6 (0) | 5 (3) | 4 (4) | 3.5% | 15 (7) / 0 (0) | 7.1 / 4.3 | 13 |

Every row scores 40 groups from 28 papers. Under CH4+CO+N2 at 4 %, 6 candidates have no eligible purge level, and under
CH4+N2 at 4 %, 1 does, but no group is lost. The same-catalyst, same-temperature kind is 0 in every row.

**What binds.** At the S5 optimum the reactor inlet holds a median of 7.1 % CO (10th-90th percentile 0.5-22 %) and
4.3 % CH4+N2 (0.6-12 %). CO is the larger part in 198 of 310 entries. At the frozen 6.86 % optimum, CO is a median 84 %
of the limited quantity. The model meets the limit by purging more (median purge 2.6 % against 0.5 % at S5), which
flushes CH4+N2 down to about 1 %. Under the CH4+N2 definition the median purge stays at 0.5 % (0.6 % at 4 %), and the
inlet CO stays at its S5 level, which is bounded only by RWGS and CO-hydrogenation equilibrium.

## 2. Stability scan, 5-15 % (the supervisor's request)

| limit % | CH4+CO+N2: diff /40 [CI] | > 5 % [CI] | ordinary / near-inf. | without Bansode /32 (diff, > 5 %) | CH4+N2: diff /40 [CI] | > 5 % [CI] | ordinary / near-inf. | without Bansode /32 |
|---|---|---|---|---|---|---|---|---|
| 5 | 26 [52-78%] | 25 [49-76%] | 7 / 19 | 21, 20 | 18 [23-63%] | 8 [0-39%] | 18 / 0 | 11, 2 |
| 6 | 27 [56-81%] | 24 [46-73%] | 14 / 13 | 22, 19 | 18 [23-63%] | 8 [0-39%] | 18 / 0 | 11, 2 |
| 6.86 | 28 [54-83%] | 22 [41-69%] | 17 / 11 | 21, 17 | 18 [23-63%] | 8 [0-39%] | 18 / 0 | 11, 2 |
| 8 | 27 [54-80%] | 22 [38-69%] | 20 / 7 | 21, 16 | 15 [15-57%] | 8 [0-39%] | 15 / 0 | 8, 2 |
| 10 | 24 [44-73%] | 18 [29-58%] | 16 / 8 | 18, 13 | 15 [15-57%] | 8 [0-39%] | 15 / 0 | 8, 2 |
| 12 | 24 [47-73%] | 13 [17-46%] | 20 / 4 | 19, 9 | 16 [18-59%] | 8 [0-39%] | 16 / 0 | 9, 2 |
| 15 | 18 [29-58%] | 12 [15-43%] | 17 / 1 | 13, 8 | 15 [15-57%] | 8 [0-39%] | 15 / 0 | 8, 2 |

Over 5-15 %, CH4+CO+N2 gives 18-28/40 with 12-25 above 5 %. CH4+N2 gives 15-18/40 with 8 above 5 %, which is S5
(15/40, 7 above 5 %) plus at most three small disagreements.

## 3. Near-infeasibility split (rule of draft PR #69)

A disagreement is near-infeasible when its regret is > 1 or the STY leader's cost under the limit is more than 2x its
S5 cost. At the frozen 6.86 %, 11 of the 28 disagreements are near-infeasible (10 above 5 %): 3 by regret > 1 and 11 by
the 2x-cost rule. The other 17 are ordinary (12 above 5 %). At 4-5 %, near-infeasible ones are the majority (19-20).
Under the CH4+N2 definition no disagreement is near-infeasible at any limit. Its ordinary count (15-19) is close to the
ordinary count under CH4+CO+N2 at 6-15 % (14-20), but fewer of them are above 5 % (8 against 9-16).

## 4. The 83 -> 40 ledger (`group_ledger.csv`, `ledger_summary.json`)

| | groups | entries | papers |
|---|---|---|---|
| all entries, plot readings included (2026-10-08) | 83 | 909 | 44 |
| printed primary (frozen) | 40 | 310 | 28 |
| dropped | 43 | 599 | 16 |

- **Groups dropped, by reason (43):**
  - 20 belong to papers without printed values. These are 11 papers whose entries are all plot readings or have a
    non-printed selectivity.
  - 23 have fewer than 2 printed entries in a paper that does have printed values: 11 groups with 0 and 12 with 1.
  - No group has 2 or more printed entries and is still unscored.
  - 15 of the 43 are in papers that stay in the primary; 28 are in the 16 dropped papers.
- **Kept groups also lose entries.** The 40 kept groups hold 478 entries in the all-entries cohort, of which 310 are
  printed. The other 168 are plot readings or entries with a non-printed CO/CH4 selectivity.
- **Papers dropped (16):** 11 have no printed values. 5 have printed entries but never 2 in one group:
  10.1002/anie.202401168, 10.1016/j.apcatb.2019.118367, 10.1016/j.fuel.2023.128376, 10.1016/j.mcat.2020.111105 and
  10.1126/sciadv.1701290. All 8 Bansode 2013 groups are kept.
- **The grouping rule is identical in both cohorts.** It is the same paper, pressure, H2/CO2 and space velocity, from
  the same `build_candidates`, which differs only by `printed_only`. The following checks all pass:
  - the group key of every row of both tables can be rebuilt from its columns;
  - all 351 printed-cohort rows sit in the all-entries table under the same group;
  - rebuilding both cohorts from `agent/extraction/out/records_normalized.csv` gives exactly the frozen entries and
    groups.
- **All-entries result (frozen columns):**
  - S5 gives 35/83 (14 above 5 %, 24/44 papers). Of these, 18/40 are in the kept groups (15/40 printed) and 17/43 in
    the dropped groups.
  - At 6.86 % it gives 54/82 (46 above 5 %; one group loses an entry to infeasibility). Of these, 32/40 are in the
    kept groups (28/40 printed) and 22/42 in the dropped groups.
  - In the kept groups at S5, removing the plot readings changes the answer in 5 groups: 4 lose a disagreement and 1
    gains one.

## Answers in plain language

**Q1. Is counting CO consistent, and does excluding it change the conclusion?**

Counting CO is consistent with *why* the limit exists, though not with CO being inert:

- The limit stands in for dilution. The model holds the per-pass CO2 conversion at its laboratory value however much
  non-H2/CO2 gas the inlet carries. CO dilutes CO2 and H2 just as much as N2 does, and the model's handling of
  recycled CO (converted per pass up to RWGS equilibrium) does not change that.
- The published reference, 6.86 % (Campos et al. 2022), is itself CO + N2 (1.5 + 4.9 %). A CH4+N2 limit of 6.86 % is
  therefore looser than the reference loop. The like-for-like true-inert value of that loop is about 4.9-5.0 %.

Excluding CO does change the conclusion:

- The inert-limited result falls back almost to S5: 18/40 with 8 above 5 % at 5-6.86 % (15/40 with 7 above 5 % at
  S5). Without Bansode it is 11/32 with 2 above 5 %, against 21/32 and 17 for the frozen definition.
- The reason is that CO is what binds. Under CH4+N2 the loop keeps a median 7 % CO at the inlet (up to 22 % at the
  90th percentile) while still running at the laboratory conversion, which is the very dilution the limit is meant to
  prevent.
- So the 28/40 of the inert-limited primary depends on counting CO. If the primary is the inert-limited loop, the
  frozen definition (CH4 + CO + N2) is the one that matches its rationale and its reference value. The CH4+N2 result
  should be reported as the sensitivity that shows the effect comes from CO build-up.

**Q2. How do 83 groups become 40?**

Only by the printed-value rule. The grouping is unchanged. The 43 dropped groups lack two printed entries, either
because the whole paper has no printed values (20 groups, 11 papers) or because the group has 0-1 printed entries (23
groups). That removes 16 of the 44 papers. The remaining 168 plot-read or non-printed entries come out of the 40 kept
groups.

## Files

| file | content |
|---|---|
| `common.py` | definitions, limits, anchors |
| `run_inlet_definition.py` | Task 1: model sweep, reproduction check, scoring, bootstrap |
| `run_group_ledger.py` | Task 2: ledger and grouping checks |
| `check_anchors.py` | anchors; with `--committed DIR`, regenerated outputs must equal the committed ones |
| `definition_scan.csv` | one row per definition x limit (all metrics above) |
| `stability_5_15.csv` | the 5-15 % table |
| `scan_groups.csv` | per definition x limit x group: leaders, regret, kind, ordinary/near-infeasible |
| `entry_costs.csv` | per entry and definition x limit: cost, purge, CO / CH4+N2 / total non-H2/CO2 inlet share |
| `summary.json` | everything, with kinds and bootstrap per scenario |
| `group_ledger.csv`, `ledger_summary.json` | Task 2 |

Rerun (Python 3.12, `pip install -r requirements.txt pyyaml`):

```bash
python analysis/meoh_inlet_definition_2026_10_12/run_inlet_definition.py   # ~40 s with 4 workers
python analysis/meoh_inlet_definition_2026_10_12/run_group_ledger.py
python analysis/meoh_inlet_definition_2026_10_12/check_anchors.py
```

The `meoh-inlet-definition` workflow runs all three and checks that the regenerated outputs equal the committed ones.
