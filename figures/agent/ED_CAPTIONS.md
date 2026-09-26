# Extended Data — captions and Table 1

Assets: `ED1_mini_interface_intervention.{svg,pdf,png}`, `ED2_failure_mechanism_by_tier.{svg,pdf,png}`,
`ED3_non_binding_per_run_spread.{svg,pdf,png}`, `ED4_v2stop_stopping_arms.{svg,pdf,png}`. Manifest: `ED_RENDER_SHA256.txt`.
Renderers: `render_ED_agent_panels.py` (ED1–ED3), `render_ED4_v2stop.py` (ED4). Metric definitions: `docs/AGENT_METRIC_DEFINITIONS_SOURCE_OF_TRUTH_2026-09-13.md`.

All counts are runs out of *n* in that cell. Every plotted value is read from a committed CSV; none is hand-entered.

---

## Extended Data Fig. 1

**Extended Data Fig. 1 | A typed, budget-annotated tool interface removes the mini tier's interface failures without
moving it into the strong regime.** Both arms use the frozen DISCOVER V1 environment at 175 CU with *n* = 20 runs; the
E2 arm changes only the tool-parameter schema and adds an explicit remaining-budget block, leaving prompt, task, action
schema, cost model, environment and scorer verbatim.
**a**, Runs reaching each stage of the decision chain. Both arms build a process window in 20/20 runs. Correct winner
identification rises from 14/20 to 19/20 under E2. `BACKWARD` is executed in **0/20** runs under both arms, and because
`BACKWARD` is a precondition of the reachability verdict, classified reachability and complete decisions are 0/20 under
both.
**b**, Where the failures moved. Undeclared-argument interface errors fall from 18 to 0 and turns with no tool call from
16 to 4, while budget errors rise from 36 to 51 and sequencing errors from 18 to 71, of which premature
`OPTIMIZE_PROCESS` calls account for 13 rising to 67. The intervention therefore succeeded on the layer it targeted; the
residual failure mass moved to budget allocation and chain ordering rather than disappearing. Total action errors are not
comparable as a single figure between the arms and are not presented as one.

## Extended Data Fig. 2

**Extended Data Fig. 2 | The three model tiers fail at different layers.** 0-CU action errors on the frozen interface,
decomposed into interface (undeclared or wrong-typed argument, unknown action), budget (a legal call whose quoted cost
exceeded the remaining budget) and sequencing (a legal, affordable call that violated an evidence precondition), summed
over each cell and annotated with the cell total. Turns with no tool call are interface failures but are not 0-CU action
errors and are excluded here so that the totals stay comparable with the frozen Phase A/B summaries. The nano tier is
dominated by budget errors and never enters the decision chain; the mini tier carries all three mechanisms and does enter
the chain; the strong tier records no budget error at any budget.

## Extended Data Fig. 3

**Extended Data Fig. 3 | Under a non-binding allowance the stopping point becomes bimodal while the decision does not
change.** Per-run decision-stable CU (the ledger-true cumulative spend from which the full decision stays correct to the
end) against final spend, for all 20 strong runs at the non-binding 5000-CU allowance, ordered by final spend; the
connector is that run's post-stability overrun. All 20 runs complete the decision and all 20 stop on their own rule, none
reaching the 60-turn cap. Six runs stop at 218 CU with 14–17 steps, matching the behaviour of the budget-constrained
cells; the remainder continue to 28–30 steps and 566 CU or beyond, with the most extreme single run at 3,021 CU. Every
run in this cell recovers the canonical Ru→Fe parity multiplier and the `unreachable` verdict, so the spread is in cost
alone. The dashed line is policy D's 206 CU completion threshold.

## Extended Data Fig. 4

**Extended Data Fig. 4 | Enforcing or gating the S1–S3 stopping rule removes post-decision compute without changing
the decision; prompt-level scoping removes most of the allowance-driven spend.** DISCOVER-V2-STOP inherits the frozen
V1 task, actions, cost model, environment, scorer and ledger and changes only the stopping mechanism; strong tier,
anonymous task, *n* = 20 per cell, 180 runs. S-hard: the environment ends the episode when S1 ∧ S2 ∧ S3 first holds.
S-gate: after the rule holds, a paid action executes only if it can still change the winner, decision pair or
reachability verdict (validity checks; re-optimisation of the winner or atomic-best candidate while its optimum or the
parity state sits on a window edge; the backward and reachability steps that follow such a re-optimisation); everything
else is rejected at 0 CU. S-anytime: prompt addendum only, asking for minimum-spend scoping and widening only on an edge
flag.
**a**, Final spend per run (log scale) for the frozen protocol and the three arms at the 75-, 225- and 5,000-CU
allowances, cell medians as bars and complete-decision counts in the margin. Under the non-binding 5,000-CU allowance
both S-hard and S-gate complete 20/20 with no compute after the rule (medians 566 CU and a 218/566 bimodal split against
714 CU under the frozen protocol; the frozen cell's 8,207 CU of post-rule Monte Carlo has no counterpart). At 75 CU the
S-hard median is unchanged (71 versus 70 CU) because the policy defers the reachability test to the end of a binding
allowance. S-anytime lowers the 225-CU median from 218 to 158 CU and the non-binding median to 216 CU, completing 20/20
in every cell, but does not reach the 75-CU value (73.5 CU).
**b**, Runs using a canonical narrow process window. S-anytime raises narrow-window use at 225 CU from 0/20 to 16/20
and at 5,000 CU from 0/20 to 4/20. Runs paying for any action after the rule first held: S-hard 0/20 in every cell;
S-gate 5/20 at 75 CU (all edge-flag re-optimisations) and 0/20 elsewhere; S-anytime 8/20, 2/20 and 0/20. Sources:
`data/discover_v2_stop/v2_stop_runs_2026-09-26.csv`, `data/discover_boundary_c1_overrun_runs.csv`,
`data/discover_boundary_c1_error_taxonomy_runs.csv`; protocol and gates in `docs/DISCOVER_V2_STOP_RESULTS_2026-09-26.md`.

---

## Extended Data Table 1

**Extended Data Table 1 | Five distinct compute-to-decision quantities on the non-binding-allowance cell.** All five are
present in the frozen outputs and take different values on the same 20 runs, so any reported figure must name which one
it is. Quantity 4 is the one used throughout this work. Source: `data/discover_boundary_c1_cu_quantities.csv`, generated
by `tools/discover/c1_cu_quantities_table.py`.

| # | quantity | what it measures | median (CU) | range (CU) |
|---|---|---|---|---|
| 1 | `CU_to_first_correct_winner` | first step at which the winner is correct; **winner only**, no stability requirement | 503 | 155–503 |
| 2 | `CU_to_stable_correct_winner` | spend from which the **winner** stays correct to the end; winner only | 503 | 155–503 |
| 3 | `CU_to_full_decision` | spend from which the **full decision** stays correct to the end; sums the quote-based per-step field | 566 | 218–714 |
| 4 | **`decision_stable_CU`** | as 3, but ledger-true, from `budget_CU − remaining_budget` | **566** | 218–714 |
| 5 | `CU_after_stable_winner` | `spent_CU` minus quantity 2; spend after the **winner** stabilised | 211 | 63–2,518 |

Quantity 5 is not the post-stability overrun. The overrun reported in the main text is measured from full-decision
stability (quantity 4) and has a median of 148 CU; quantity 5 is measured from winner stability and has a median of
211 CU. Quantities 3 and 4 coincide in this cell because its quote inflation is zero in every run; they diverge
elsewhere, and the main text uses quantity 4 throughout.

**Placement note.** The allocation contract assigned this table to Extended Data. Its content is also developed in
SI §4, which covers the quote-versus-ledger accounting in full. To avoid duplication, Extended Data Table 1 is the
canonical presentation of the five quantities and SI §4 cross-references it rather than repeating the table.
