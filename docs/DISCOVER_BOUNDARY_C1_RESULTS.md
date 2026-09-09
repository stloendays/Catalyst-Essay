# DISCOVER-BOUNDARY-C1 — results (strong model Phase A, 2026-09-09)

Family: DISCOVER V1 Boundary Confirmatory Extension C1. Branch `experiment/discover-boundary-c1`.
Pre-registration: `DISCOVER_BOUNDARY_C1_PREREGISTRATION.md` (commit `05544fe`, before any run); design reduction:
`DISCOVER_BOUNDARY_C1_ADDENDUM_A1.md`. DISCOVER V1 itself is untouched.

## 1. Question
Does the strong-model 200-CU advantage of adaptive policy E over fixed-VOI policy D (frozen V1: E 5/5, D 0/1) reproduce
under higher-n independent sampling, and is it a coherent local budget regime or an isolated cell?

## 2. Frozen protocol inheritance
Task, prompt, 11 tools + STOP, cost model, scorer, stopping rule, policies A–D, ground truth NH3-FINAL-1.1: all pinned in
`DISCOVER_FROZEN_V1.json`. Hash check **PASS 15/15 before the first run and after the last run** (`data/discover_boundary_c1/
metadata/hashcheck_before_smoke2_*.json`, `hashcheck_after_*.json`). Driver `discover/formal_e.py` sha `d4451c42…`, reused by
import; sampling as in V1 (chat.completions, tool_choice auto, API-default temperature / reasoning, no seed, ≤ 5 infra retries).

## 3. Pre-registration and deviations
Frozen before any run: endpoints, ΔP_full contrast, CU_to_full_decision definition and validation gate, outcome classes,
Phase B gating. Deviation A1 (user, cost, decided during the batch before any C1 result was scored): 150 / 200 / 250 CU
stopped early (7 / 8 / 9 complete runs), 175 and 225 CU continued to 20. Three directories interrupted mid-run (no trace)
are listed in the metadata and excluded; no completed run was discarded. The 200-CU cell is therefore **reduced-n**.

## 4. New runs
| item | value |
|---|---|
| model | `gpt-5.5-2026-04-23` (response_model identical in every trace), anonymous task |
| confirmatory runs (complete) | **64**: 150 CU 7, 175 CU 20, 200 CU 8, 225 CU 20, 250 CU 9 |
| smoke | 5 (run index 99, excluded) + 7 zero-token `insufficient_quota` failures from 2026-09-08 kept on disk |
| infrastructure | 0 API retries, 0 driver exceptions, 0 malformed traces in the 64 runs |
| tokens | 5.25 M prompt, 0.70 M completion |
| D reference | frozen policy: 150 / 175 / 200 CU incomplete (winner only at 175/200); 225 / 250 CU complete, CU_to_full = **206** |

## 5. 200-CU replication
New runs: **8/8** complete decisions, Wilson 95 % CI [0.68, 1.00]; ΔP_full = **+1.00** [+0.68, +1.00] against D = 0.
The pre-registered substantive threshold (k ≥ 14/20 ≡ Wilson lower bound ≥ 0.48) is met in its lower-bound form (0.68) but
with n = 8, not 20. Together with V1's separate 5/5, 13 of 13 independent strong-model runs at 200 CU have completed the
decision D cannot complete at that budget. The historical series is not pooled into the estimate.

## 6. Local budget shape (Figure A)
| budget | E k/n | P_full E [Wilson] | D | ΔP_full [CI] | regime |
|---|---|---|---|---|---|
| 150 | 7/7 | 1.00 [0.65, 1.00] | 0 | +1.00 [+0.65, +1.00] | reduced-n |
| 175 | **19/20** | 0.95 [0.76, 0.99] | 0 | **+0.95 [+0.76, +0.99]** | confirmatory |
| 200 | 8/8 | 1.00 [0.68, 1.00] | 0 | +1.00 [+0.68, +1.00] | reduced-n |
| 225 | **20/20** | 1.00 [0.84, 1.00] | 1 | **0.00 [−0.16, 0.00]** | confirmatory |
| 250 | 9/9 | 1.00 [0.70, 1.00] | 1 | 0.00 [−0.30, 0.00] | reduced-n |

Classification (pre-defined): **COHERENT LOCAL REGION** — ΔP_full > 0 at the adjacent budgets 175 and 200 (and at 150),
not the single 200-CU cell, and ΔP_full = 0 at 225 and 250. The shape is a plateau that ends where D first completes
(D's CU_to_full is 206, so D completes exactly when the budget exceeds 206), not a symmetric bump: at every budget below
D's completion point E completes and D does not; at every budget above it both complete.

The single failure (175 CU, run 16): winner and pair correct, reachability never classified — the run exhausted its
budget before TEST_REACHABILITY.

## 7. Accuracy ceiling and efficiency (Figure B, D)
Where both complete (225, 250 CU) the difference must be read as efficiency, and there **E is not faster**:

| budget | E CU_to_full (n) | D CU_to_full | ΔCU_full = D − E | relative saving |
|---|---|---|---|---|
| 225 | 217.8 (20): 216 ×2, 218 ×18 | 206 | **−11.8** | **−5.7 %** (bootstrap CI degenerate, 18/20 identical) |
| 250 | 221.0 (9): 216, 218 ×7, 247 | 206 | −15.0 | −7.3 % [−10.5, −5.5] |

Above D's completion point E takes the same route as D (full 111-CU window, three optimizations, BACKWARD,
TEST_REACHABILITY; narrow windows in 3/20 and 0/9 runs) and finishes 10–15 CU later. Below it E completes by building
narrow windows (150 CU: 7/7 runs; 175 CU: 20/20; 200 CU: 3/8) with CU_to_full 53–172 (median 128 at 150, 140 at 175,
189 at 200). The advantage is therefore **decision completion under a budget that the fixed-VOI policy cannot use**, not a
same-quality compute saving. Break-even exact in 55/64 runs; regret 0 in 64/64; action errors 12 in 64 runs (10 at 175 CU:
6 BACKWARD before both metals were optimized, 4 malformed BUILD_PROCESS_WINDOW bounds), 0 at 225/250.

## 8. Capability gating (Phase B)
Not run. The pre-registered trigger (coherent region) is met, so Phase B (nano, mini; 175 / 225 CU × 20) is warranted;
it was held for the user's cost decision after the strong-tier reduction A1.

## 9. Statistical results
Wilson intervals and ΔP_full intervals as in §6. Exact binomial P(k ≥ 8 | n = 8, p_D → 0): < 10⁻⁷ (reduced-n; degenerate
against a deterministic 0). Logistic slope of P_full on budget across the 64 strong runs: +0.78 per 25 CU (63/64 successes;
weak identification). Bootstrap (seed 20260908, 10 000 resamples) for ΔCU_full at 250 CU: [−10.5 %, −5.5 %]; at 225 CU
18/20 values are identical so the interval collapses to the point.

## 10. Interpretation
- The 200-CU advantage is real, not sampling noise: 8/8 new runs, 19/20 at 175 CU, and 7/7 at 150 CU, all against D = 0.
- The regime is bounded by D's completion budget (206 CU): E's advantage exists exactly where the budget is too small for
  the fixed-VOI route, and vanishes once D can afford its full route.
- Above that point E has **no efficiency advantage**; it is 6–7 % later to the complete decision than D.
- The strong-tier 35/35 of V1 was a ceiling effect on P_full; C1 shows that the discriminating quantity in that regime is
  CU_to_full, and on that quantity D wins.

## 11. Manuscript-safe statement
> With the frozen DISCOVER V1 protocol and 64 additional independent runs of the strong model at 150–250 CU, adaptive
> allocation completes the full scientific decision (winner, decision pair, reachability) in 7/7, 19/20 and 8/8 runs at
> 150, 175 and 200 CU, budgets at which the deterministic fixed-VOI policy cannot complete it (its completion requires
> 206 CU); at 225 and 250 CU both policies complete and the adaptive policy reaches the complete decision 12–15 CU
> (6–7 %) later. The adaptive advantage is therefore a budget-localized decision-completion advantage below the fixed
> policy's completion threshold, not a general compute saving.

## 12. Answers to the original questions
- **Q1 (35/35 = saturated?)** Yes for P_full: the strong tier is at the ceiling at every budget ≥ 150 CU, so success rate
  cannot separate E from D above 206 CU. The separating quantity there is CU_to_full.
- **Q2 (which metric carries the 200-CU advantage?)** Full-decision correctness (winner ∧ pair ∧ reachability). The
  winner alone is not it: D also identifies the winner at 175 and 200 CU (CU_to_stable 155). The pair decision and the
  reachability verdict are what D cannot afford below 206 CU and what E obtains through narrow windows.
- **Q3 (once both correct, compare efficiency?)** Yes, and the answer is negative for E: at 225/250 CU E reaches the
  complete decision at 218–221 CU versus D's 206 (−5.7 % / −7.3 %).
- **Q4 (real or luck?)** Real: 8/8 new at 200 CU (Wilson lower bound 0.68), 19/20 at 175, 7/7 at 150.
- **Q5 (a bump?)** A coherent region 150–200 CU with ΔP_full ≈ +1, ending at 225 CU where D completes. It is a plateau
  bounded by D's completion threshold rather than a peaked bump.

## 13. Files / provenance
`data/discover_boundary_c1_runs.csv` (one row per run, 64 C1 + 5 smoke + 15 V1 historical), `data/discover_boundary_c1_summary.csv`,
`data/discover_boundary_c1_D_reference.csv`, `data/discover_boundary_c1_metadata.json` (gate, classification, hash checks,
interrupted dirs, package versions, code hashes), `data/discover_boundary_c1/{runs,smoke,logs,metadata,D_reference}/` (all
traces), `discover/boundary_c1_{metrics,runner,analysis}.py`, `figures/discover_boundary_c1/fig{A,B,C,D}_*.png`.
Validation gate of CU_to_full: PASS on 224 frozen traces (224/224 replayed answers identical; flag agreement 224/224).
