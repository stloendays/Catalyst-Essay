# DISCOVER V1 — cross-model stability (PHASE E-2, 2026-09-06)

Protocol: `DISCOVER_FROZEN_V1.json`, hashes verified before and after the runs (PASS/PASS). Nothing in NH3-FINAL-1.1, the frozen task/prompt/
tools/cost model/scorer/stopping rule, policies A–D or the V1 formal results was modified. Driver `discover/formal_e.py` is byte-identical to
the V1 formal run (sha `d4451c42…`). New analysis code: `discover/cross_model_analysis.py` (scores through the frozen scorer only).
Runs: `DISCOVER_CROSS_MODEL_V1/<model>/traces/<variant>/`, metadata `DISCOVER_CROSS_MODEL_V1/metadata/cross_model_metadata.json`.
Tables: `CROSS_MODEL_SCORES_V1.csv` (per model × variant × budget), `CROSS_MODEL_FAILURE_MATRIX_V1.csv` (19 modes × model × variant × budget),
per-trace `DISCOVER_CROSS_MODEL_V1/scores/failure_per_trace.csv`. Figures: `DISCOVER_CROSS_MODEL_V1/figures/X_cross_model_curves_{anonymous,named}.png`
(6-panel), single panels X1–X6, failure matrices X7 (model × variant) and X8 (anonymous, by budget).

## 1. Design
| item | value |
|---|---|
| tiers (exact IDs) | weak `gpt-5.4-nano-2026-03-17`; medium `gpt-5.4-mini-2026-03-17`; strong `gpt-5.5-2026-04-23` (V1 formal traces re-scored, not re-run) |
| per new model | policy E only: 5 independent runs × 7 budgets × {anonymous, named} = 70 runs (140 new traces); A–D reused from the frozen V1 baselines |
| sampling | API defaults (temperature / reasoning not set), tool_choice auto, same 11 frozen tools + STOP |
| infrastructure | 0 API retries, 0 driver exceptions; 8.13 M prompt + 0.31 M completion tokens for the two new tiers |
| scoring | `DISCOVER_SCORER_V1.score_trace` unchanged; gpt-5.5 rows reproduce the V1 tables exactly |

## 2. Primary result — anonymous task, policy E (n = 5 per cell)
P(full) = winner ∧ pair ∧ reachability. "stable" = CU to stable correct winner (mean over runs that reached it). unnec. = unnecessary-CU fraction.

| budget | nano P(win)/P(pair)/P(reach)/**P(full)** | mini P(win)/P(pair)/P(reach)/**P(full)** | gpt-5.5 **P(full)** | D | nano stable / unnec. | mini stable / unnec. | 5.5 stable / unnec. |
|---|---|---|---|---|---|---|---|
| 200 | 0.2 / 0.0 / 0.0 / **0.0** | 0.8 / 0.4 / 0.2 / **0.2** | **1.0** | 0 | 184 (1/5) / 0.28 | 148 (4/5) / 0.18 | 115 / 0.02 |
| 250 | 0.8 / 0.2 / 0.0 / **0.0** | 0.6 / 0.4 / 0.4 / **0.4** | **1.0** | 1 | 228 / 0.34 | 145 / 0.25 | 167 / 0.13 |
| 300 | 0.8 / 0.6 / 0.0 / **0.0** | 1.0 / 0.2 / 0.2 / **0.2** | **1.0** | 1 | 206 / 0.37 | 151 / 0.27 | 155 / 0.12 |
| 500 | 1.0 / 1.0 / 0.6 / **0.6** | 1.0 / 0.6 / 0.4 / **0.4** | **1.0** | 1 | 225 / 0.55 | 287 / 0.35 | 161 / 0.11 |
| 800 | 1.0 / 1.0 / 0.0 / **0.0** | 1.0 / 1.0 / 0.8 / **0.8** | **1.0** | 1 | 300 / 0.60 | 245 / 0.39 | 364 / 0.39 |
| 1200 | 1.0 / 1.0 / 0.0 / **0.0** | 0.8 / 0.8 / 0.4 / **0.4** | **1.0** | 1 | 242 / 0.50 | 242 / 0.39 | 364 / 0.29 |
| 2000 | 1.0 / 1.0 / 0.6 / **0.6** | 1.0 / 0.6 / 0.6 / **0.6** | **1.0** | 1 | 271 / 0.58 | 304 / 0.27 | 364 / 0.29 |

Break-even: every reported parity multiplier of nano (6/35 runs report one) and mini (18/35) is the exact full-domain value 201.22× except two
mini runs at 300 CU that ran BACKWARD on the degenerate pair (candidate_13, candidate_13) and reported 1.0× (rel. error 1.0). Regret: nano 800
(200 CU, four runs with no winner), 1.3 (250, one run chose Ru), 200 (300, one run no winner), 0 at ≥ 500 CU; mini 200 / 201 / 0 / 0 / 0 /
200 / 0. gpt-5.5: 0 everywhere. Pooled: P(full) at ≤ 300 CU = 0.00 (nano) / 0.27 (mini) / 1.00 (5.5); at ≥ 500 CU = 0.30 / 0.55 / 1.00.

## 3. Secondary — named task
nano: P(win) 1.0 at every budget (price/name prior), P(full) 0 / 0.2 / 0.2 / 0.2 / 0.4 / 0.6 / 0.6; mini: P(full) 0.4 / 0.2 / 0.4 / 0.8 / 0.8 /
0.8 / 1.0; gpt-5.5: 1.0 everywhere. Names raise winner accuracy (nano 1.00 vs 0.60 at ≤ 300 CU anonymous) and pooled P(full) at ≥ 500 CU
(nano 0.45 vs 0.30, mini 0.85 vs 0.55) but leave the weak tiers far from the strong tier. Named results are prior-contaminated by construction
(zero-tool probe, V1 §6) and do not support the closed-book claim; they show that a name prior partially substitutes for tool-driven evidence
in weak models.

## 4. Failure-mode matrix (fraction of the 35 runs per model × variant; `X7`, full table in the CSV)
| class | mode | nano anon | nano named | mini anon | mini named | 5.5 anon | 5.5 named |
|---|---|---|---|---|---|---|---|
| decision | wrong winner (incl. no winner) | 0.17 | 0.00 | 0.11 | 0.09 | 0 | 0 |
| decision | wrong / unformed pair decision | 0.31 | 0.29 | 0.43 | 0.14 | 0 | 0 |
| decision | wrong or missing reachability | 0.83 | 0.69 | 0.57 | 0.37 | 0 | 0 |
| decision | BACKWARD never executed | 0.63 | 0.43 | 0.37 | 0.29 | 0 | 0 |
| decision | stated winner ≠ environment winner | 0.20 | 0.09 | 0.03 | 0.00 | 0 | 0 |
| fidelity | parity window-relative (F1) | 0.00 | 0.00 | 0.06 | 0.00 | 0.03 | 0.09 |
| fidelity | parity not reported | 0.83 | 0.66 | 0.49 | 0.34 | 0 | 0 |
| stopping | unresolved-candidate stop (F2) | 0.20 | 0.14 | 0.54 | 0.26 | 0.09 | 0 |
| stopping | over-confirmation, unnec. > 0.25 (F3/F4) | 0.89 | 0.43 | 0.54 | 0.43 | 0.23 | 0.34 |
| stopping | > 100 CU after stable winner (F4) | 0.51 | 0.31 | 0.29 | 0.37 | 0.54 | 0.66 |
| interpretability | lever used (F5) | 0.00 | 0.03 | 0.00 | 0.00 | 0.03 | 0.00 |
| allocation | Fe optimized first (F6) | 0.03 | 0.89 | 0.69 | 0.57 | 0.66 | 0.69 |
| allocation | non-canonical order | 0.74 | 0.51 | 0.54 | 0.46 | 0 | 0 |
| allocation | narrow window built | 0.00 | 0.00 | 0.00 | 0.00 | 0.06 | 0.14 |
| protocol | ended without STOP (budget_exhausted / malformed limit) | 0.26 | 0.14 | 0.11 | 0.20 | 0 | 0 |
| protocol | ≥ 1 invalid / unaffordable action | 0.83 | 0.69 | 0.77 | 0.86 | 0 | 0 |

What the weak-tier failures are (from the traces, `failure_per_trace.csv`):
- **Tool-interface errors dominate** (nano 118, mini 148 errored calls in 70 runs each): unaffordable OPTIMIZE_PROCESS requests (61 / 43), INSPECT_CANDIDATES
  called with an undeclared argument (`metals`, `ids`, `candidate_ids`… 24 / 55), TEST_REACHABILITY with an undeclared `window` argument or a
  string instead of a number for `required_multiplier` (19 / 7), OPTIMIZE before any window was built (4 / 27). Errors cost 0 CU but consume
  turns and end the run by the three-consecutive-unaffordable rule in 14 (nano) / 9 (mini) runs; 2 mini runs hit the no-tool-call limit.
- **No-winner runs (11)** all follow the same path: full 111-CU window + 15-CU activity screen, then OPTIMIZE requests the budget cannot cover
  (58–116 CU spent on partial optimization, zero feasible optimized candidate). Neither weak tier ever built a narrow window (0/140 runs);
  gpt-5.5 did so at 200 CU (2/5 anonymous, 5/5 named) — this is the entire 200-CU difference.
- **Missing reachability (nano 29/35 anonymous)**: BACKWARD skipped (22) or attempted with an unoptimized pair (5), then STOP with the environment's
  S3 false (16 of 35 nano anonymous runs ended in the S1 ∧ S2 ∧ ¬S3 state, i.e. winner resolved, reachability never classified). Wrong "reachable" classifications (nano 4, mini 5 across
  variants) all came from `required_multiplier = 1.0` or `0.0` — the agent asked whether the winner can reach its own activity, or ran
  BACKWARD on the wrong pair (Fe–Os, Ru–Os, Fe–Fe) — i.e. a formulation error, not a numerical one.
- **Wrong winner with a formed answer**: 2 runs (nano and mini at 250 CU, anonymous) reported Ru; both had optimized Ru before Fe and stopped
  with Fe unresolved.

## 5. Answers
**Is the core industrial decision stable across models?** No as a property of "an LLM agent"; yes as a property of the strong tier on this
protocol. With the same prompt, tools and budgets, complete correct decisions go 35/35 (gpt-5.5) → 15/35 pooled 0.43 (gpt-5.4-mini) → 9/35
0.26 (gpt-5.4-nano) on the anonymous task. The winner alone is more robust (nano 1.0 at ≥ 500 CU, mini ≥ 0.8 at all budgets) but the V1 prior
probe already showed winner accuracy is price-prior-recoverable; the discriminating components — pair decision and reachability — are where
the weak tiers fail. The claim for the paper is therefore tier-conditional: "a frontier model recovers the mismatch → backward → reachability
chain closed-book at every budget; smaller models of the same family recover the winner but not the reachability verdict."

**Does a stronger model improve final correctness or allocation efficiency?** Both, in this order. Correctness first: at ≥ 500 CU, where budget
is not binding, P(full) still rises 0.30 → 0.55 → 1.00, and the weak-tier failures at high budget are formulation errors (no BACKWARD, wrong
pair, self-parity) and interface errors, not budget shortage. Allocation efficiency second: unnecessary-CU fraction at ≥ 500 CU is 0.56 (nano)
/ 0.35 (mini) / 0.27 (5.5); CU to a stable winner is comparable (259 / 270 / 313 CU, gpt-5.5 higher because it optimizes more candidates
before stopping at ≥ 800 CU). The strong tier's efficiency advantage is concentrated at 200–500 CU (unnec. 0.02–0.13 vs 0.18–0.55) and vanishes
at ≥ 800 CU where all three tiers over-confirm.

**Is the 200-CU adaptive-scope advantage strong-model-only?** Yes. Narrow process windows were built in 0/70 nano and 0/70 mini runs versus
7/70 gpt-5.5 runs, all at 200 CU. Every weak-tier run at 200 CU paid the 111-CU full window, which leaves ≤ 74 CU for optimization — below the
87 CU needed for the three feasible candidates — so 200-CU completion is impossible on that path (nano 0/5, mini 1/5 by stopping after two
optimizations). The window-relative parity cost (F1) of the shortcut is likewise strong-tier-only (0.03–0.09 vs 0.00).

**Does under-resolution → over-confirmation reproduce across models?** The over-confirmation half reproduces and is amplified: unnecessary-CU
fraction > 0.25 in 89 % (nano) / 54 % (mini) / 23 % (5.5) of anonymous runs, and > 100 CU spent after the stable winner in 51 / 29 / 54 %.
The under-resolution half changes character: for gpt-5.5 it is a deliberate 200-CU shortcut with the decision kept (F1/F2); for the weak tiers
it is the default state at every budget — unresolved-candidate stops in 20 % (nano) / 54 % (mini) of runs, spread over all budgets (mini: 2–4 of
5 runs at each of 200–800 CU), and often with a stop text claiming S1–S3 satisfied. So the regime pair is not "low budget → under-resolve, high
budget → over-confirm" for weak models; they do both simultaneously (spend on non-competitive candidates while leaving the decision pair or
the reachability step unresolved).

## 6. Classification of V1 imperfections in the light of the cross-model result (paper wording)
| class | V1 items | cross-model status |
|---|---|---|
| decision correctness | none for gpt-5.5 (70/70) | tier-dependent: missing/wrong reachability 0.37–0.83, wrong pair 0.14–0.43, wrong winner ≤ 0.17 in the weak tiers |
| quantitative fidelity | F1 window-relative parity (4/70, 200 CU, reachability verdict kept) | strong-tier-specific by-product of adaptive scope; weak tiers instead fail to report parity (0.34–0.83) |
| stopping efficiency | F2 unresolved stop (3/70), F3/F4 over-confirmation at ≥ 800 CU | both reproduce and worsen in weaker tiers; F2 becomes a dominant mode (mini 0.54) |
| interpretability | F5 lever rarely used (1/70) | unchanged (≤ 1/70 per tier) — the lever is an interpretability tool, not a decision step |
| allocation path | F6 named prior orders Fe first | reproduces (nano named 0.89 vs anonymous 0.03); anonymous results remain the closed-book evidence |
| protocol / interface | 0 errors for gpt-5.5 | new class for weak tiers: undeclared tool arguments and unaffordable requests in 69–86 % of runs; scored as-is (cost 0, turns consumed) |

Caveats: n = 5 per cell (a single run moves P by 0.2; the non-monotonic nano/mini curves are within that noise); three tiers of one vendor
family; the medium tier is `gpt-5.4-mini`, not the full `gpt-5.4`; no seed control at the API. Nothing was retried or re-run to improve a cell.
Cross-model V1 is complete; the negative-control reaction is not started; any protocol change (e.g. scorer weighting of unresolved risk, argument
schema hardening) is DISCOVER V2 and must not overwrite V1.
