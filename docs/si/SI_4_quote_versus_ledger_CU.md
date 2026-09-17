# SI §4 — Quote-based versus ledger-true compute accounting

The per-step `action_cost` field written by the frozen driver `discover/formal_e.py` is `env.quote(name, args)`,
evaluated **before** the action executes. For `OPTIMIZE_PROCESS` the quote counts every state in the process window,
while the environment charges only the states not yet computed for that metal. A run that optimises repeatedly over
overlapping windows is therefore quoted more than it is charged. The environment ledger and `spent_CU` always reconcile
exactly; the step-level `action_cost` field does not.

| reconciliation check | result |
|---|---|
| `Σ` ledger `cost_CU` == `spent_CU`, per run | holds in all scored runs |
| `Σ` step `action_cost` == `spent_CU`, per run | fails in 32 of 317 scored runs |

Two decision-stable quantities inherit this split. The frozen extension metric
`discover/boundary_c1_metrics.cu_to_full` sums `action_cost` and is therefore quote-based (quantity #3 below).
`tools/discover/c1_overrun_analysis.py` replays the identical stability criterion but takes the cumulative spend at
step *j* as `budget_CU − step["remaining_budget"]`, which reconciles with the environment ledger and with `spent_CU`
(quantity #4).

Measured over the 317 scored runs: 32 runs carry any inflation; the per-cell median inflation is **0 CU in every
cell**; the largest single-run inflation is **58 CU** (mini 400 CU cell, run 8, quoted 272 CU against an actual
214 CU). Only two cell medians change.

| cell | quote-based median decision-stable CU | ledger-true median decision-stable CU |
|---|---|---|
| strong 175 CU | 140 | **124** |
| strong 150 CU | 106 | **102** |
| strong 225 CU | 218 | 218 |
| strong 250 CU | 218 | 218 |
| strong, non-binding 5000-CU allowance | 566 | 566 |

`discover/boundary_c1_metrics.py` was **not** modified; its SHA-256 is recorded in every hash-check record. The
ledger-true value is computed alongside it, with the quoted value retained as `decision_stable_CU_quoted` and an
explicit `quote_inflation_CU` column, so the difference stays visible in the data rather than being silently absorbed.
**All manuscript figures use the ledger-true quantity #4.** Addendum A5 §4 records that the earlier figures of 140 CU
(strong 175 CU) and 106 CU (strong 150 CU) in Addendum A4, in Results §3.7 and in
`DISCOVER_BOUNDARY_C1_PHASE_B_RESULTS.md` are quote-inflated and are superseded by 124 CU and 102 CU. No completion
rate, break-even value, reachability verdict, narrow-window count or error count is affected; none of these ever
depended on `action_cost`.

## The five CU-to-X quantities

Five distinct quantities in the frozen scorer and extension metrics could each loosely be called "the CU at which the
agent reached the answer", and they take different values on the same runs. Every published number must name which one
it is.

| # | quantity | source | what it measures | median CU | range CU |
|---|---|---|---|---|---|
| 1 | `CU_to_first_correct_winner` | frozen `DISCOVER_SCORER_V1` | first step where `current_winner` equals the ground truth; winner only, no stability requirement | 503 | 155–503 |
| 2 | `CU_to_stable_correct_winner` | frozen `DISCOVER_SCORER_V1` | cumulative CU from which the winner stays correct to the end; winner only | 503 | 155–503 |
| 3 | `CU_to_full_decision` | `discover/boundary_c1_metrics.cu_to_full` | full-decision stability (winner + decision pair + reachability); sums the quote-based `action_cost` | 566 | 218–714 |
| 4 | **`decision_stable_CU`** | `tools/discover/c1_overrun_analysis.py` | full-decision stability, ledger-true, from `budget_CU − remaining_budget` | **566** | 218–714 |
| 5 | `CU_after_stable_winner` | frozen `DISCOVER_SCORER_V1` | `spent_CU` minus quantity #2: spend after the **winner** stabilised, not after the full decision | 211 | 63–2518 |

All five rows are reported for the strong-tier, non-binding 5000-CU allowance cell, n = 20.

Quantity #4 is the manuscript's first-stable / decision-stable CU; #1, #2 and #5 must never be quoted as if they were
it. In particular, **`CU_after_stable_winner` (median 211 CU) is not the post-stability overrun (median 148 CU)**: the
first is measured from the step at which the winner stabilises, the second from the step at which the full decision
stabilises. In this cell quantities #3 and #4 coincide exactly, because quote inflation is 0 CU in every run of it;
their medians differ only in the strong 175 CU and strong 150 CU cells. The 218 CU at the bottom of the #3/#4 range is
the **minimum** first-stable value in this cell, reached by 6 of its 20 runs, and is a different statistic from the
218 CU median of the 225 CU cell.

Sources: `AGENT_METRIC_DEFINITIONS_SOURCE_OF_TRUTH_2026-09-13.md` §1, §4.1, §4.2 and §5 (authoritative);
`DISCOVER_BOUNDARY_C1_ADDENDUM_A5_2026-09-11.md` §4; `data/discover_boundary_c1_cu_quantities.csv`.
Cross-references: frozen Results §3.7 and Discussion §4.6 of `MANUSCRIPT_SKELETON_v4_2026-09-14.md`.
