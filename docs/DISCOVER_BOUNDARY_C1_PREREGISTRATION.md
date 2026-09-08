# DISCOVER-BOUNDARY-C1 — pre-registration (frozen before any new run)

Family: **DISCOVER V1 Boundary Confirmatory Extension C1** (`DISCOVER-BOUNDARY-C1`).
Registered: 2026-09-08, before the first C1 API call. Branch `experiment/discover-boundary-c1`.
This is additional confirmatory sampling **on the frozen DISCOVER V1 task**. It is not part of DISCOVER V1's reported
sample, and it is not DISCOVER V2 (no protocol element is redesigned).

## 0. What is inherited unchanged (hash-pinned, checked before and after the runs)
`DISCOVER_FROZEN_V1.json` (15 SHA-256 pins): task (named + anonymous), prompt, action schema / 11 tools + STOP, cost model,
scorer `DISCOVER_SCORER_V1.py`, stopping rule, `discover/env.py`, `discover/policies.py` (A–D), `discover/run.py`,
`discover/llm_policy.py`, identity mapping, forbidden-action list, oracle tests. Driver `discover/formal_e.py`
(sha `d4451c42…`, byte-identical to the V1 formal and cross-model runs) is reused through import; the C1 batch runner only
sets budget, run index, output directory and tag. Ground truth = NH3-FINAL-1.1 canonical run (unchanged).
Sampling protocol as in V1: OpenAI chat.completions, `tool_choice="auto"`, temperature / reasoning at API defaults, no seed
(the API exposes none; V1 set none), infrastructure retry ≤ 5 with backoff, 0-cost agent errors never retried.
Original frozen traces (`DISCOVER_FORMAL_RUNS_V1`, `DISCOVER_CROSS_MODEL_V1`) are not touched.

## 1. Primary question
Does the strong-model 200-CU adaptive advantage (frozen V1: E 5/5 vs D 0/1 complete decisions) reproduce under higher-n
independent sampling, and does it extend to adjacent budgets as a coherent local regime rather than an isolated cell?

## 2. Design
| item | value |
|---|---|
| Phase A (primary, confirmatory) | `gpt-5.5-2026-04-23`, anonymous variant only |
| budgets | **150, 175, 200, 225, 250 CU** |
| runs | **20 NEW independent policy-E runs per budget = 100 new runs**; V1's five 200/250-CU runs are shown only as historical exploratory points and are never pooled into the confirmatory estimate (an optional descriptive n = 25 line may be printed, labelled) |
| D reference | policy `D_fixed_voi`, deterministic, unmodified: frozen V1 traces reused at 200 and 250 CU; one new run each at 150, 175, 225 CU |
| smoke | one E run per budget (run index 99, tag `smoke`) before the sample, kept on disk in `smoke/`, never scored into the sample |
| Phase B (conditional) | `gpt-5.4-nano-2026-03-17`, `gpt-5.4-mini-2026-03-17`, same budgets, 20 new runs each, anonymous — executed **only if** Phase A yields REPLICATED-200 or a COHERENT LOCAL REGION (§6); otherwise stop and report the negative result |

## 3. Endpoints
Primary endpoint: `full_decision_correct` from the **frozen scorer**, i.e. winner_correct ∧ pair_decision_correct ∧ reachability_correct.

Primary contrast: ΔP_full(B) = P_full^E(B) − P_full^D(B). D is deterministic, so the 95 % interval of ΔP_full is the Wilson
interval of E shifted by −P_full^D(B).

Secondary endpoints (frozen scorer): total spent CU; unnecessary_CU_fraction; CU_to_stable_correct_winner; decision regret
(USD/t); break-even relative error; action / interface errors; why_stop.

Derived endpoint (extension scorer `discover/boundary_c1_metrics.py`, the frozen scorer is not modified):
**CU_to_full_decision** = cumulative CU at the first step after which winner, pair decision and reachability are all correct
and remain correct at every later step up to STOP. It is reconstructed by replaying the frozen `final_answer` logic on the
step-level state (winner, feasible-cost table, COMPUTE_ACTIVITY / BACKWARD / TEST_REACHABILITY results) and de-anonymizing
with the scorer-only identity mapping.
Validation gate (must pass on all 210 frozen E traces and the 14 frozen D traces before C1 data are analysed):
(i) the replayed answer at the last step equals the frozen `final.answer`; (ii) CU_to_full is non-null **iff** the frozen
scorer returns full_decision_correct = 1. If the gate fails, CU_to_full is dropped and only total spent CU is used,
labelled as descriptive total-compute efficiency.

## 4. Efficiency analysis (ceiling handling)
For budgets where **both** E and D are fully correct: ΔCU_full = CU_to_full_D − CU_to_full_E (positive = E completes the
scientific decision earlier) and relative saving = (CU_D − CU_E)/CU_D, using CU_to_full if validated, otherwise mean total
spent CU. For budgets where D is not fully correct, the E-vs-D difference is reported as a **decision-completion advantage**,
never as a same-quality compute saving. Runs are also reported as ITT (all runs) and clean-infrastructure sensitivity
(runs with infra_retries = 0 and no driver exception); infrastructure-failed runs are kept on disk, replacements get
run indices ≥ 100, and both analyses are reported.

## 5. Statistics
Per budget: k/20, P_full, Wilson 95 % CI, ΔP_full with shifted CI. Effect sizes are reported with intervals; no single
p-threshold decides the outcome. Secondary only: exact binomial test of P_full^E > P_full^D at 200 CU; logistic regression
of full on budget (C1 strong runs only); non-parametric bootstrap (seed 20260908, 10 000 resamples) of ΔCU_full.
Historical V1 points are plotted as a separate, faded series.

## 6. Pre-defined outcome classes (decided by the C1 sample, not by V1)
- **REPLICATED-200**: at 200 CU, k/20 gives a Wilson lower bound of P_full^E above P_full^D = 0 (k ≥ 1 already satisfies
  this formally; the substantive threshold used for the paper is k ≥ 14/20, i.e. Wilson lower bound ≥ 0.48).
- **COHERENT LOCAL REGION**: ΔP_full > 0 (point estimate) at **≥ 2 adjacent budgets** among 150/175/200/225/250, and the
  region is not the single 200-CU cell.
- **ISOLATED SPIKE**: only one budget shows ΔP_full > 0 and both neighbours do not.
- **NO ADAPTIVE REGION**: the 200-CU advantage does not reproduce (k/20 fails the substantive threshold).
Expected shape if the effect is real (not fitted to): low budget both fail / E weak → intermediate E advantage → higher
budget D catches up and Δ → 0. The data decide; the report states which class occurred.

## 7. Integrity rules
No failed run is deleted or rerun to raise a success rate. Every run stores model ID, budget, run index, timestamp, full
trace, token usage, spent CU, tool calls, interface errors, STOP reason and scorer output. Hash check of the 15 frozen
files before the first run and after the last run; both results recorded in the C1 metadata. Analysis code uses fixed
seeds (bootstrap only); no CSV or figure value is edited by hand.

## 8. Files (to be produced)
`data/discover_boundary_c1_runs.csv`, `data/discover_boundary_c1_summary.csv`, `data/discover_boundary_c1_D_reference.csv`,
`data/discover_boundary_c1_metadata.json`, `discover/boundary_c1_metrics.py`, `discover/boundary_c1_runner.py`,
`discover/boundary_c1_analysis.py`, figures A–D in `figures/discover_boundary_c1/`, report `docs/DISCOVER_BOUNDARY_C1_RESULTS.md`.
