# DISCOVER protocol V1 — no-LLM dry-run report (2026-09-06)

Purpose: prove that budget accounting, the action space, the stopping rule, the trace schema and the scorer work end to end before any LLM run.
Policies A–D only (deterministic; A averaged over three seeds). No prompt, tool, cost or scorer change was made in response to any score.
Ground truth was read only by `DISCOVER_SCORER_V1.py`. Layer A untouched (31 tests pass).

## What was exercised
- 42 runs: budgets {200, 250, 300, 500, 800, 1200, 2000} CU × {A × 3 seeds, B, C, D}; 639+ trace steps, **0 schema violations** (all 16 E6 fields on every step; final block with why_stop, remaining_budget, unresolved_decision_risk, answer, ledger).
- Budget accounting: every action charged from the frozen cost model; over-budget attempts raise `BudgetExceeded` and are recorded (random policy hits them at the end of every budget); no run overspent.
- Stopping rule: S1–S3 evaluated by the environment after every step; policies stop for one of four recorded reasons (S1–S3 satisfied; S1–S3 satisfied and expected decision value < θ; queue exhausted; no affordable action).
- Scorer: winner, feasible-ranking Kendall τ + coverage, pair decision, reachability class, break-even relative error, CU consumed, CU→first / stable correct winner, decision-relevant and unnecessary CU fractions, regret, stopping efficiency; curves budget → P(full decision correct) and budget → regret (`discover_runs/CURVES_V1.png`).

## Development curves (single deterministic runs; A = mean of 3 seeds)
| policy | first budget with full decision correct | CU actually spent there | CU → first correct winner | unnecessary CU fraction (at 800) | note |
|---|---|---|---|---|---|
| A random | 2000 (all 3 seeds); 1/3 at 500–1200 | 1476 (mean) | varies; wrong winners (Os, Ru, none) below 300 | 0.4–0.7 | no allocation: spends on dominated candidates and 1,000-draw MC |
| B activity-first | 250 | 219 | 213 (optimizes in atomic order: Ru, Os, then Fe) | 0.21 | at 200 CU it stops on Ru (wrong) because Fe is third in atomic order |
| C uncertainty-first | 1200 | 1063 | 155 | 0.59 | winner correct early *by coincidence* (the largest-σ candidate is also the winner in this model), but it spends 3 × 164 CU on 1,000-draw MC and optimizes every candidate before the parity question; full decision only at ≥ 1200 CU |
| D fixed VOI heuristic | 250 | 247 (281 when unconstrained) | 155 | 0.10 | window → activities → uncertainties → cheapest-surrogate candidate → validity check → MC on the leader → challenger → BACKWARD → TEST_REACHABILITY → third candidate → four lever probes → stop by θ |

Pre-registered hypothesis check (development evidence only): "largest uncertainty ≠ highest decision value" — C reaches the *winner* as early as D
because the largest-σ candidate happens to be the winner, but it needs ≈ 4 × the compute of D for the *full decision* (parity + reachability),
and 51–59 % of its budget goes to calculations that cannot change the decision. This is the pattern the formal benchmark must reproduce with E.

## Caveats found in the dry run (recorded, not patched away)
1. The coincidence above (largest σ = winner) weakens C as a null policy for the *winner* metric on this reaction; the *full-decision* and
   *compute-to-stable* metrics still separate it. A negative-control reaction (later) will not have this coincidence.
2. D's constants (surrogate price weight 0.5, boundary scale 0.15, MC decay 50 draws, θ = 0.05) are declared heuristics fixed before any LLM
   run; they were set once during development to make D stop (the first draft never stopped: repeated 100-draw MC on the leader). They are
   frozen with the protocol.
3. Random-policy regret is ∞ when no feasible candidate was optimized; the curve caps it at 1,000 USD/t (mean at 200 CU shows 667).
4. Below ≈ 215 CU no policy can complete S3 (window 111 + activities 15 + three optimizations 87 + backward 1 + reachability 4); the 200-CU
   point is a deliberate failure region.
5. Only the "full" window was used by the deterministic policies; narrower windows (cheaper BUILD/OPTIMIZE) are available to E.

## Deliverables (this protocol version)
DISCOVER_LEAKAGE_AUDIT.md (PASS) · DISCOVER_COST_MODEL_V1.json + REPORT · DISCOVER_TASK_V1.json · DISCOVER_ACTION_SCHEMA_V1.json ·
DISCOVER_PROMPT_V1.md · DISCOVER_SCORER_V1.py · DISCOVER_PREREGISTRATION_V1.md · discover/ (env, policies, run, llm_policy interface, README) ·
discover_runs/ (42 traces, SCORES_V1.md/json, CURVES_V1.png/json).

## Not done, awaiting protocol review
No LLM run; no freezing hash list yet (`DISCOVER_FROZEN_V1.json` is written at the first formal run after review); no model tiers.
