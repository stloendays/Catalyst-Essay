# DISCOVER compute-cost model V1 (E2) — measured once, then frozen

File: `DISCOVER_COST_MODEL_V1.json` (frozen; not to be modified after the first formal evaluation). Measurement script: `discover/measure_costs.py`
(one pass on the canonical NH3-FINAL-1.1 Layer A, this machine, 2026-09-06). Wall times are single measurements of a deterministic workload;
evaluation counts are exact (instrumented `Condition.logtof`).

## Unit
**1 CU = the wall time of 1,000 MKM state evaluations** (one `Condition.logtof` solve = one steady-state microkinetic solution of one
process state for one descriptor value). Measured: 21.8 ms per 1,000 evaluations. Evaluation-based actions are charged by their exact
evaluation count; vectorized actions (Monte Carlo, backward root search, lever re-optimization) are charged by measured wall time in the same
unit; every charge is rounded up to an integer.

## Measured workload
| action | Layer-A evaluations | wall (s) | size | frozen charge |
|---|---|---|---|---|
| INSPECT_CANDIDATES | 0 | 0.00002 | — | 0 CU (bookkeeping) |
| COMPUTE_ACTIVITY | 1 per metal | 0.0003 (15 metals) | 15 | 1 CU per metal (minimum billable unit) |
| READ_PROPERTY_UNCERTAINTY | 0 | 0.00001 | — | 0 CU |
| process-library construction (self-consistent recycle fixed point per state) | 0 MKM; 14,136 nonlinear fixed points | 2.41 | 14,136 states | BUILD_PROCESS_WINDOW: 0.00782 CU per state in the window (full domain = 111 CU) |
| OPTIMIZE_PROCESS (one metal, full window) | 28,272 (2 per state, descriptor bracketing as in the frozen closure) | 0.54 | 14,136 | 0.002 CU per not-yet-evaluated state (full window = 29 CU; a metal already evaluated in the window is not charged again) |
| READ_COST_BREAKDOWN | 0 | 0.001 | — | 0 CU |
| RUN_MC | 0 MKM (interpolation on the response-surface asset) + one full-window cost minimization per draw | 0.714 (2 metals × 100 draws) | 200 draw·metals | 0.164 CU per draw·metal (100 draws on one metal = 17 CU; 1,000 draws = 164 CU) |
| TEST_LEVER | 0 (re-optimization on stored activity vectors) | 0.0023 (2 metals) | 2 | 1 CU per metal |
| BACKWARD (pair) | 0 MKM; ~40 full-window re-optimizations in the root search | 0.015 | — | 1 CU |
| TEST_REACHABILITY, reference scope | 1,202 (descriptor grid at the reference condition) | 0.022 | — | 2 CU |
| TEST_REACHABILITY, window scope | + state-wise maximum on the response-surface asset | 0.027 | — | 2 + 2 = 4 CU |
| CHECK_MODEL_VALIDITY (edges / bed cap / vessel floor) | 0 | 0.00002 | — | 0 CU |
| CHECK_MODEL_VALIDITY (exact dominance on a not-yet-evaluated metal) | 28,272 | 0.43 | — | 28 CU (same as evaluating that metal) |

## Declared conventions
- The response-surface asset (14,136 states × 1,201 descriptor points = 17.0 M evaluations, ≈ 6 min wall) is a precomputed, shared Layer-A asset
  used by RUN_MC and window-scope reachability. It is not charged to any policy: every policy has the same access, and charging it would make the
  first MC call cost more than the entire benchmark. This is stated in the cost model and in the task's action schema.
- MC draws are charged linearly (100 / 300 / 1,000 allowed); the per-draw cost is dominated by the full-window cost minimization, which is why
  Monte Carlo on one metal (164 CU at 1,000 draws) is ≈ 6 × an optimization (29 CU). This makes "where to spend uncertainty propagation" a real
  allocation choice.
- Bookkeeping actions cost 0 CU so that reading what one already computed is never penalized; they still count as steps in the trace.
- Reference exhaustive workload for scale: window 111 + activities 15 + 15 optimizations 435 + MC 1,000 draws on all 15 metals 2,460 + backward 1
  + reachability 4 ≈ **3,030 CU**. The minimum to reach a correct, fully classified decision on this model is of order 215 CU
  (window + activities + three optimizations + backward + reachability), so budgets between ≈ 200 and ≈ 3,000 CU span the interesting range.
- Frozen budget grid for the development curves: 300, 500, 800, 1,200, 2,000 CU.

## What the cost model does not do
It does not charge LLM tokens (policy E) — those are reported separately — and it does not model parallelism. Costs are integers per action
so that traces from different policies are comparable to the unit.
