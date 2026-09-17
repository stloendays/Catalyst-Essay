# SI Section 6. Pre-registration deviations and infrastructure record

Scope: the DISCOVER-BOUNDARY-C1 Agent line. Results §3.7 and Discussion §4.6 are frozen and are cross-referenced,
not restated, here.

## 6.1 Phase B was executed as a cost-motivated reduced extension

`DISCOVER_BOUNDARY_C1_PREREGISTRATION.md` stated that the conditional Phase B would use the same five budgets as
Phase A — 150, 175, 200, 225 and 250 CU — and would include a smoke run before formal sampling. Neither was executed.
Phase B instead ran at two budgets, 175 CU and 225 CU, with 20 independent formal runs per model per budget for
`gpt-5.4-mini-2026-03-17` and `gpt-5.4-nano-2026-03-17`, and with no smoke runs.

| model | 175 CU | 225 CU | other registered budgets | smoke |
|---|---:|---:|---|---:|
| `gpt-5.4-mini-2026-03-17` | 20 formal | 20 formal | not run | 0 |
| `gpt-5.4-nano-2026-03-17` | 20 formal | 20 formal | not run | 0 |

Both decisions were operational and were issued before the first Phase B API call; no Phase B result existed when the
reduction was chosen. The two retained cells bracket the deterministic fixed-VOI policy D completion threshold of
206 CU: 175 CU lies below it and tests whether the strong-tier recovery regime transfers to weaker tiers, while 225 CU
lies above it and is the control region in which D completes. Smoke runs were dropped because the identical frozen
driver, scorer and tool interface had already been exercised by the completed strong-model C1 runs, and no additional
API smoke calls were authorised.

No scientific or scoring rule was altered: the task and anonymous mapping, prompt, 11 tools plus STOP interface, CU cost
model, policy E semantics, deterministic D reference, scorer, definition of `full_decision_correct`, stopping rule, API
retry policy, ground truth and frozen files were identical to the frozen protocol. Phase B integrity counts:
**80 formal runs, 0 smoke runs**, frozen-hash checks **15/15 PASS before and after Phase B**, **0 infrastructure
retries**, **0 driver exceptions**.

Phase B accordingly supports confirmatory weak-tier estimates at 175 and 225 CU only. No weak-tier estimate is claimed
at 150, 200 or 250 CU, and these cells are not pooled with unexecuted cells or used to infer the weak-tier response
outside 175/225 CU. The original preregistration and the Phase A addendum are retained unchanged as provenance.

## 6.2 Aborted 75 CU batch of 2026-09-11

The first attempt at the strong-tier 75 CU floor-probe cell (`gpt-5.5-2026-04-23`, frozen policy E, tag `c1low`, 20
runs requested) was stopped mid-batch when the API account exhausted its credits; subsequent calls returned HTTP 429
`insufficient_quota` after 5 retries. Three runs had completed, one was truncated mid-run, and the remaining 16
produced zero-step traces.

| run index | steps | spent CU | disposition |
|---|---:|---:|---|
| 0 | 23 | 75.0 | valid; set aside as superseded partial batch |
| 1 | 12 | 52.0 | valid; set aside as superseded partial batch |
| 2 | 13 | 73.0 | valid; set aside as superseded partial batch |
| 3 | 11 | 51.0 | truncated mid-run; quarantined |
| 4–19 (16 runs) | 0 | 0.0 | zero-step infrastructure failure; quarantined |

No result was derived from this batch and nothing was deleted. The 17 infrastructure-failed traces were preserved
verbatim and moved out of the scored glob path under a manifest
(`data/discover_boundary_c1_quarantine_2026-09-11.json`, written 2026-09-11T08:13:05Z), so no analysis can pool them
into a 75 CU cell. The 3 valid runs were recorded as a superseded partial batch
(`data/discover_boundary_c1_superseded_B75_2026-09-11.json`, 2026-09-11T08:56:31Z) rather than carried forward, so that
the reported cell comes from one complete batch and never mixes two. The cell was re-run in full as r0–r19 after a
credit top-up, and that replacement batch is the n = 20 75 CU cell reported in Results §3.7.

The 2026-09-11 batch series containing the replacement cell records **118/118 formal runs completed, 0 infrastructure
retries, 0 driver exceptions and no run discarded**, with frozen hashes **15/15 PASS** before and after every batch and
the `discover/formal_e.py` SHA-256 unchanged throughout. Each new cell is independently tagged (`c1low`;
`c1uncapped` for the non-binding 5000-CU allowance cell; `c1mini300`; `c1mini400`) and keyed separately, so no new
cell is pooled with an existing E or E2 cell.

## 6.3 Corrections to previously published quantities

Two code-level defects were found after the corresponding addenda were issued.

The per-step `action_cost` field is the pre-execution `env.quote()`, which for `OPTIMIZE_PROCESS` counts every state in
the window while the environment charges only the states not yet computed. The environment ledger and `spent_CU`
reconcile exactly; the step-level field does not. Across all 297 scored runs, 31 carry inflation, the per-cell median
inflation is 0 CU in every cell, and the single-run maximum is 58 CU (mini 400 CU, r8: quoted 272 against an actual
214). Two published cell medians change:

| cell | quote-based median | ledger-true median |
|---|---:|---:|
| strong 150 CU | 106 CU | 102 CU |
| strong 175 CU | 140 CU | 124 CU |

All manuscript figures use the ledger-true decision-stable CU. The frozen extension metric
`discover/boundary_c1_metrics.py` was not modified; the ledger-true value is computed alongside it and the quoted value
is retained with an explicit inflation column (SI §4). No completion rate, break-even value, reachability verdict,
narrow-window count or error count depended on `action_cost`, and none changes.

The error-taxonomy generator computed `min_window_states_median` as `sorted(values)[n // 2]`, an upper median, which
disagreed with the true median in 5 of the 10 strong cells (125 CU: 2,100 against 1,950; 150 CU: 1,291 against
1,261.5). The generator now uses `statistics.median` and the CSVs were regenerated; the prose in Addendum A5 and in the
F10 figure spec had quoted true medians and is unaffected.
