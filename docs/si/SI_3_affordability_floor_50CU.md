# SI 3. The 50 CU affordability floor

The strong-tier completion plateau of 19–20 of 20 runs holds from 75 CU to 250 CU. At 50 CU it breaks: the strong
model (`gpt-5.5-2026-04-23`, frozen policy E, tag `c1low`, n = 20) completes the decision in **13/20** runs
(P = 0.65, CI 0.43–0.82). This is the first cell to leave the plateau and the first whose interval excludes 0.9,
which is why 75 CU — 36.4% of the deterministic policy D threshold of 206 CU — is the lowest stable completion
threshold rather than the lowest budget tested.

| budget | n | complete decision | decision-stable CU (median) | mean spent | narrow window |
|---|---|---|---|---|---|
| 50 CU | 20 | 13/20 (P = 0.65, CI 0.43–0.82) | 47 | 48.2 | 20/20 |
| 75 CU | 20 | 20/20 (P = 1.00, CI 0.84–1.00) | 52 | 64.3 | 20/20 |
| 100 CU | 20 | 19/20 (P = 0.95) | 71 | 81.8 | 20/20 |
| 125 CU | 20 | 20/20 | 80 | 104.7 | 20/20 |
| 150 CU | 20 | 20/20 | 102 | 117.5 | 20/20 |
| 175 CU | 20 | 19/20 | 124 | 150.6 | 20/20 |
| 225 CU | 20 | 20/20 | 218 | 217.8 | 0/20 |

## Only reachability fails

The 50 CU failures are affordability failures on the closing link of the chain, not reasoning failures. All 20 runs
stopped on their own stopping rule. The economic winner is correct in 20/20 runs and the decision pair in 20/20 runs
at 50 CU; reachability is the only component that fails, at 13/20.

| component | 50 CU | 75 CU |
|---|---|---|
| winner correct | 20/20 | 20/20 |
| decision pair correct | 20/20 | 20/20 |
| reachability correct | 13/20 | 20/20 |
| complete decision | 13/20 | 20/20 |
| built process window | 20/20 | 20/20 |
| ran `BACKWARD` | 19/20 | 20/20 |
| ran `TEST_REACHABILITY` | 13/20 | 20/20 |

Six of the seven incomplete runs execute `BACKWARD` successfully and then cannot afford the 2–4 CU
`TEST_REACHABILITY` classification; several stop messages state the remaining budget explicitly. The seventh never
reaches `BACKWARD`, consistent with the 19/20 `BACKWARD` execution count. The agent is not thrashing against the
constraint: the whole cell contains **3** action errors in **3** runs, of which **1** is a budget error
(`unaffordable_OPTIMIZE_PROCESS`) and **2** are undeclared-argument errors on `BUILD_PROCESS_WINDOW`, with **0**
validation rejections. Post-stability overrun is correspondingly minimal: the cell reports a median decision-stable
spend of **47 CU**, a median final-used spend of **49 CU**, a median overrun of **1 CU** and a mean per-run overrun
share of **5.8%**, with 20/20 self-stop (these are separate per-run aggregates and are not a subtraction of one
another). Runs that fail stop because the closing step is unaffordable, not because they exhaust the budget on
wasted actions.

## The arithmetic spine

The floor follows from the mandatory action sequence. `COMPUTE_ACTIVITY` over the 15 candidates costs 15 CU; a
small process window is then built (the median smallest window at 50 CU is **633** of the 14,136 admissible states,
and 20/20 runs use narrow-window allocation); three optimisations follow; `BACKWARD` costs 1 CU; and
`TEST_REACHABILITY` costs 2–4 CU. The lowest decision-stable spend observed in any cell is **32 CU**, and the mean
spend at 50 CU is already **48.2** of the 50 available, leaving nothing for the final classification in roughly a
third of runs. The hard floor therefore lies between approximately **35 CU and 50 CU**. The same chain executed over
the full 14,136-state window costs 218 CU (activity 15 CU, full window 111 CU, optimisations, `BACKWARD` 1 CU,
`TEST_REACHABILITY`), which is the median decision-stable spend of the 225 CU cell.

## The scored break-even collapses in the same cell

The quantitative target degrades with completion, and the degradation is genuine rather than an artefact of the
frozen `final_answer()` reporting the first `BACKWARD` record.

| budget | first `BACKWARD` = canonical | scored break-even = canonical | any `BACKWARD` = canonical |
|---|---|---|---|
| 50 CU | 2/20 | 2/20 | 3/20 |
| 75 CU | 9/20 | 9/20 | 17/20 |
| 100 CU | 9/20 | 9/20 | 16/20 |
| 175 CU | 15/20 | 15/20 | 19/20 |
| 225 CU | 20/20 | 20/20 | 20/20 |

At 75 CU the first-record convention alone explains the gap: the canonical break-even multiplier
(`GT["break_even"]` = 201.2234429878984) is recovered at some point in 17/20 runs while only 9/20 are scored
canonical. At 50 CU that explanation is unavailable — only 3/20 runs compute the canonical value at any point, so
2/20 scored canonical reflects a real loss of the quantitative result below the completion floor.

Cross-references: frozen Results §3.7 and Discussion §4.6 of `MANUSCRIPT_SKELETON_v4_2026-09-14.md`.
Sources: `DISCOVER_BOUNDARY_C1_ADDENDUM_A5_2026-09-11.md`, `data/discover_boundary_c1_decision_components.csv`,
`data/discover_boundary_c1_error_taxonomy_summary.csv`, `AGENT_METRIC_DEFINITIONS_SOURCE_OF_TRUTH_2026-09-13.md`.
