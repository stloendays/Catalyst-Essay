# DISCOVER-BOUNDARY-C1 Addendum A5 — 75 CU floor probe, uncapped condition, mini saturation sweep (2026-09-11)

New formal runs on the frozen DISCOVER V1 environment, all through the frozen `discover/formal_e.run_one` driver with only
budget, run index, tag and output directory set. Frozen hashes **15/15 PASS** before and after every batch, with
`discover/formal_e.py` SHA-256 unchanged. **98 formal runs, 0 infrastructure retries, 0 driver exceptions.** No NH3,
MeOH, Au/TiO2 or figure result was recomputed.

| cell | model | policy | budget | runs | tag |
|---|---|---|---|---|---|
| floor probe | gpt-5.5-2026-04-23 | E (frozen) | 75 CU | 20 | `c1low` |
| uncapped | gpt-5.5-2026-04-23 | E (frozen) | 5000 CU | 20 | `c1uncapped` |
| mini saturation | gpt-5.4-mini-2026-03-17 | E (frozen) | 300 CU | 20 | `c1mini300` |
| mini saturation | gpt-5.4-mini-2026-03-17 | E (frozen) | 400 CU | 20 | `c1mini400` |

## 1. The strong-tier completion floor is still below the tested range (item 1)

| budget | n | complete decision | decision-stable CU (median) | mean spent | scored break-even canonical | narrow window |
|---|---|---|---|---|---|---|
| **75 CU** | 20 | **20/20** (P = 1.00, CI 0.84–1.00) | **52 CU** | 64.3 | 9/20 | 20/20 |
| 100 CU | 20 | 19/20 (P = 0.95) | 71 CU | 81.8 | 9/20 | 20/20 |
| 125 CU | 20 | 20/20 | 80 CU | 104.7 | 11/20 | 20/20 |
| 150 CU | 20 | 20/20 | 102 CU | 117.5 | 11/20 | 20/20 |
| 175 CU | 20 | 19/20 | 124 CU | 150.6 | 15/20 | 20/20 |
| 225 CU | 20 | 20/20 | 218 CU | 217.8 | 20/20 | 0/20 |
| D fixed-VOI | — | complete at **206 CU** | 206 CU | — | exact | n/a |

At 75 CU — **36.4%** of the fixed policy's 206 CU threshold — the strong model completes the decision in **20/20** runs,
with the median run closing it after **52 CU** of actual spend, **25%** of D's threshold, and the fastest run after
32 CU. Across the whole 75–250 CU range complete-decision recovery stays at 19–20/20 with no downward trend; the 19/20
cells at 100 and 175 CU are single ordering failures, not a decline (all confidence intervals overlap).

**The lower failure edge has still not been located.** 75 CU is the bottom of the tested range, not a measured floor.
The observed minimum decision-stable spend of 32 CU, together with the fixed action costs (`COMPUTE_ACTIVITY` over 15
candidates = 15 CU, `BACKWARD` = 1 CU, `TEST_REACHABILITY` = 2–4 CU, plus a small window and three optimisations),
places a hard arithmetic floor somewhere near **35–40 CU**. Bracketing it requires a 50 CU cell, which has not been run.

The capability-versus-scoring split reported in Addendum A4 holds at 75 CU:

| budget | n | first BACKWARD = canonical | scored break-even = canonical | **any** BACKWARD = canonical |
|---|---|---|---|---|
| **75 CU** | 20 | 9 | 9 | **17** |
| 100 CU | 20 | 9 | 9 | 16 |
| 125 CU | 20 | 11 | 11 | 17 |
| 150 CU | 20 | 11 | 11 | 17 |
| 175 CU | 20 | 15 | 15 | 19 |
| 225 CU | 20 | 20 | 20 | 20 |

At 75 CU the agent still computes the canonical 201.223443 multiplier at some point in 17/20 runs. The scored value is
lower only because the frozen `final_answer()` reports the first `BACKWARD` record for the decision pair.

## 2. Uncapped condition: the agent is efficient *because* the budget binds (item 2b)

20 runs at 5000 CU, which is far above any reachable spend, so the budget never binds. `MAX_TURNS = 60` is the only
remaining limit and **no run reached it**; all 20 stopped on their own stopping rule.

| quantity | median | range |
|---|---|---|
| complete decision | **20/20** | — |
| decision-stable CU | **566** | 218–714 |
| final-used CU | **714** | 218–3021 |
| overrun CU (final-used − decision-stable) | **148** | 0–2455 |
| overrun as fraction of spend | **33.3%** | 0–81.3% |
| steps | 29 | 14–30 |

**All 20 runs spent more than policy D's 206 CU.** The median 714 CU is **3.5×** D's threshold for the same decision;
the most extreme run spent 3021 CU, **14.7×** D, of which 2455 CU (81%) was spent after the decision was already
complete and stayed complete to the end.

Placed against the constrained cells, the pattern is unambiguous:

| budget | decision-stable CU | final-used CU | overrun | overrun % | stop mode |
|---|---|---|---|---|---|
| 75 CU | 52 | 70 | 4 | 12.9% | 20/20 self-stop |
| 100 CU | 71 | 82 | 13 | 17.6% | 20/20 self-stop |
| 125 CU | 80 | 111 | 12 | 16.2% | 20/20 self-stop |
| 150 CU | 102 | 124 | 0 | 11.2% | 20/20 self-stop |
| 175 CU | 124 | 164 | 2 | 16.9% | 20/20 self-stop |
| 225 CU | 218 | 218 | **0** | **0.0%** | 20/20 self-stop |
| 250 CU | 218 | 218 | 0 | 1.5% | 9/9 self-stop |
| **uncapped** | **566** | **714** | **148** | **33.3%** | 20/20 self-stop |

The agent's stopping discipline is a function of the constraint, not a property of the policy. Where the budget binds
tightly it stops within 13–18% of the decision-stable point, and at 225 CU it stops essentially exactly there. Remove
the constraint and the decision-stability point itself moves from 218 CU to 566 CU and total spend rises to 3.5× the
deterministic policy's.

**This is the decisive evidence for the revised claim.** The agent's advantage is confined to completing the decision
*below* the fixed-policy threshold. Given no compute pressure it is not merely no better than the fixed policy — it is
substantially worse, by a factor of 3.5 in the median. Any wording resembling a general compute saving is contradicted
by this cell.

Run distribution is bimodal: 6 runs stop at 218 CU with 14–17 steps, like the constrained cells; 14 runs continue to
28–30 steps and 566 CU or more. The behaviour is therefore not a uniform drift but a failure of the stopping rule to
trigger in the absence of budget pressure.

## 3. mini does not reach strong-175 level at any tested budget (item 4)

| cell | n | complete decision | winner | pair | reachability | **ran BACKWARD** | ran TEST_REACHABILITY | action errors | mean spent |
|---|---|---|---|---|---|---|---|---|---|
| mini 175 CU | 20 | 0/20 (P = 0.00) | 14 | 0 | 0 | **0/20** | 0/20 | 72 | 159 |
| mini 225 CU | 20 | 6/20 (P = 0.30) | 14 | 7 | 6 | **7/20** | 8/20 | 61 | 208 |
| mini 300 CU | 20 | 4/20 (P = 0.20) | 17 | 10 | 4 | **7/20** | 6/20 | 71 | 278 |
| mini 400 CU | 20 | 7/20 (P = 0.35) | 11 | 9 | 7 | **7/20** | 7/20 | 49 | 354 |
| **strong 175 CU** | 20 | **19/20** | 20 | 20 | 19 | 20/20 | 19/20 | 10 | 151 |

**`BACKWARD` execution is pinned at exactly 7/20 at 225, 300 and 400 CU.** Increasing the budget from 225 to 400 CU —
a 78% increase, and 2.3× the strong tier's 175 CU — moves it not at all. Completion oscillates 6, 4, 7 of 20 with
fully overlapping confidence intervals; the honest reading is a **plateau at roughly 5–7/20**, not a trend toward the
strong tier.

The compute required for mini to reach strong-175 performance therefore **does not exist within the tested range**, and
the flat `BACKWARD` rate gives no basis for expecting it at higher budgets. Together with the negative E2 interface
result in Addendum A4 — where typed tool parameters and an explicit budget display eliminated the interface failure
mode entirely and still left `BACKWARD` at 0/20 and completion at 0/20 — two independent interventions now fail to move
the mini tier: **more compute, and a better interface.** The barrier is the ability to plan and hold the
`BUILD_PROCESS_WINDOW → OPTIMIZE_PROCESS → BACKWARD → TEST_REACHABILITY` chain, which is a model-capability property.

## 4. Metric correction: the trace's per-step `action_cost` is quote-based

While computing the overrun metric a real defect surfaced in an existing published quantity, and it is corrected here.

`discover/formal_e.py` records `action_cost` as `env.quote(name, args)`, evaluated **before** the action executes. For
`OPTIMIZE_PROCESS` the quote counts every state in the window, while the environment charges only the states not yet
computed for that metal. When a run optimises repeatedly over overlapping windows the quoted cost therefore exceeds the
actual charge. The environment ledger and `spent_CU` always reconcile exactly; the step-level `action_cost` field does
not.

The frozen extension metric `discover/boundary_c1_metrics.cu_to_full` sums `action_cost`, so `CU_to_full_decision`
inherits the inflation. Measured over all 297 scored runs:

- 31/297 runs carry any inflation; the per-cell median inflation is **0 CU** in every cell;
- the maximum single-run inflation is **58 CU** (mini 400 CU, r8: quoted 272 vs actual 214);
- only two published cell medians change: **strong 175 CU, 140 → 124 CU**, and **strong 150 CU, 106 → 102 CU**. Every
  other cell median is unchanged, including 218 CU at 225/250 CU and 566 CU uncapped.

`discover/boundary_c1_metrics.py` was **not** modified — its SHA-256 is recorded in every hash-check record. Instead
`tools/discover/c1_overrun_analysis.py` computes the ledger-true value from `budget_CU - step["remaining_budget"]` and
reports the quoted value alongside it as `decision_stable_CU_quoted` with an explicit `quote_inflation_CU` column, so
the difference stays visible in the data rather than being silently absorbed. All decision-stable figures in this
addendum are ledger-true. The earlier figures of 140 CU (strong 175) and 106 CU (strong 150) in Addendum A4, in
Results §3.7 and in `DISCOVER_BOUNDARY_C1_PHASE_B_RESULTS.md` are quote-inflated and are superseded by 124 CU and
102 CU.

This does not affect any completion rate, break-even value, reachability verdict, narrow-window count or error count —
those never depended on `action_cost`.

## 5. Integrity record

- frozen hashes 15/15 PASS before and after each batch; `discover/formal_e.py` SHA-256 `d4451c42…` unchanged throughout;
- 98/98 formal runs completed; 0 infrastructure retries; 0 driver exceptions; no run discarded;
- every new cell is independently tagged (`c1low`, `c1uncapped`, `c1mini300`, `c1mini400`) and keyed separately in the
  analysis, so no new cell is pooled with an existing E or E2 cell;
- generators: `tools/discover/c1_overrun_analysis.py`, `tools/discover/c1_error_taxonomy.py`;
- data: `data/discover_boundary_c1_overrun_runs.csv`, `data/discover_boundary_c1_overrun_summary.csv`,
  `data/discover_boundary_c1_error_taxonomy_runs.csv`, `data/discover_boundary_c1_error_taxonomy_summary.csv`.

## 6. Remaining items

| item | status |
|---|---|
| 1 | 75/100/125/150 CU done at n = 20; floor still below range; a **50 CU** cell would bracket the arithmetic floor near 35–40 CU |
| 2 | closed: 175-vs-225 consistency in A3; uncapped condition quantified here |
| 3 | closed, negative: the E2 interface does not move mini across the 175 CU boundary |
| 4 | closed, negative: mini plateaus at 5–7/20 with `BACKWARD` pinned at 7/20 across 225/300/400 CU |
| 7 | open-source strong-tier control still deferred to the reproducibility-package stage |
