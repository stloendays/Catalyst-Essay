# SI §2 — The two non-complete strong-tier runs

Two strong-tier runs in the DISCOVER-BOUNDARY-C1 budget sweep do not produce a complete decision:
`E_llm_agent_anonymous_B175_r16_c1_20260909T131633Z` at 175 CU and `E_llm_agent_anonymous_B100_r18_c1low` at 100 CU.
Each is the single failure of its cell — both cells score 19/20 complete decisions (P = 0.95; CI 0.76–0.99 at 100 CU) —
and in both the winner and the decision pair are scored correct, so the reachability verdict is the only element lost.
Both are ordering failures around `BACKWARD`, in opposite directions.

**175 CU, r16 — the probe precedes the target.** Step 3 built the full 14,136-state window for 111 CU, leaving 49 of the
175 CU. Step 7 called `TEST_REACHABILITY` on Ru with `scope: "reference"` and no `required_multiplier`; the result
carried the reference-condition scaling headroom 1.0899 but no `classification` field, which S3 requires. `BACKWARD` ran
only at steps 12–13, returning the canonical 201.223443 inside a 1,211-state narrow window. By then 0 CU remained, so
the 2-CU `TEST_REACHABILITY` re-call that would have classified Ru as `unreachable` was unaffordable. The run stopped
with `winner_correct` = true, `pair_decision_correct` = true and `reachability_correct` = false. The 1.0899 value
recorded here is the `scope: "reference"` quantity; this 175 CU cell, together with the frozen NH3-FINAL-1.1
consistency record, is its evidence.

**100 CU, r18 — the correction arrives after the scored record.** Step 8 ran a premature `BACKWARD` in a
not-yet-optimised window, returning 1.5424, and step 13 classified Ru as `reachable` on that basis. The run then
repaired itself: step 18 `BACKWARD` returned 185.30 over a 675-state window and step 22 classified Ru as `unreachable`,
with 31 CU still unspent. The frozen `final_answer()` reports the **first** `BACKWARD` record matching the decision pair
and the **first** classified `TEST_REACHABILITY`, so the two early records are the scored answer and the run scores
`reachability_correct` = false while containing the correct verdict. The 185.30 multiplier is not the canonical
201.223443, but the verdict does not depend on it: classification turns only on the multiplier being far above the
2.5246 headroom, not on its exact value.

| | r16 (175 CU) | r18 (100 CU) |
|---|---|---|
| run tag | `E_llm_agent_anonymous_B175_r16_c1_20260909T131633Z` | `E_llm_agent_anonymous_B100_r18_c1low` |
| first `BACKWARD` | steps 12–13; 201.223443; 1,211-state narrow window | step 8; 1.5424; not-yet-optimised window |
| first reachability probe | step 7; `scope: "reference"`, no `required_multiplier`; headroom 1.0899, no classification | step 13; `reachable`, on the step-8 multiplier |
| later correction | none; the 2-CU re-call was unaffordable | step 18 `BACKWARD` 185.30 in a 675-state window; step 22 `unreachable` |
| remaining budget | 0 CU after `BACKWARD` (steps 12–13) | 31 of 100 CU unspent at step 22 |
| scored reachability | unclassified → false | first record `reachable` → false |
| ordering defect | probe before `BACKWARD` produced the multiplier, then no budget to re-classify | premature `BACKWARD` never displaced by the later correct record |

Opening with the full window is not the discriminator. Seven of the 20 strong runs at 175 CU built the full window
first, and six of those seven still completed. What distinguishes r16 is calling the reachability probe before
`BACKWARD` had produced the multiplier it needs, leaving no budget to re-classify. In r18 the premature call is
`BACKWARD` itself, taken in a not-yet-optimised window with budget to spare, so the decision is lost to the
first-record scoring convention rather than to compute. Neither failure is a capability or budget-size failure.

Cell-level context for the two host budgets:

| budget | n | complete decision | median decision-stable CU (ledger-true) | mean spent (CU) | scored break-even = canonical | any `BACKWARD` = canonical | narrow-window (canonical) | action errors |
|---|---|---|---|---|---|---|---|---|
| 100 CU | 20 | 19/20 (P = 0.95, CI 0.76–0.99) | 71 | 81.8 | 9/20 | 16/20 | 20/20 | 4 |
| 175 CU | 20 | 19/20 (P = 0.95) | 124 | 150.6 | 15/20 | 19/20 | 20/20 | 10 |

The 10 action errors of the 175 CU cell are 4 interface errors and 6 sequencing errors, all six of the latter premature
`BACKWARD` calls, with **zero** budget errors; the cell also carries 11 no-tool-call turns. Zero budget errors is the
strong-tier value in every cell of the trace-level taxonomy (150–250 CU, 64 runs, 12 action errors in total), so r16's
missed re-call is a stopping condition rather than a rejected call.

Sources: `DISCOVER_BOUNDARY_C1_ADDENDUM_A3_2026-09-11.md` §2, §3, §3.2;
`DISCOVER_BOUNDARY_C1_ADDENDUM_A4_2026-09-11.md` §1, §1.1;
metric definitions and the ledger-true 175 CU median from `AGENT_METRIC_DEFINITIONS_SOURCE_OF_TRUTH_2026-09-13.md`
§3.3, §4.2. Cross-reference: manuscript §3.7 and §4.6 (frozen).
