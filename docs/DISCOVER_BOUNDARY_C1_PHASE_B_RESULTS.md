# DISCOVER-BOUNDARY-C1 — Phase B results: capability gating (2026-09-10)

Family: DISCOVER V1 Boundary Confirmatory Extension C1, Phase B. Branch `experiment/discover-boundary-c1`.
Trigger: the Phase A pre-registered condition (coherent local region) was met (`DISCOVER_BOUNDARY_C1_RESULTS.md`).
Protocol: identical to Phase A and to frozen DISCOVER V1 — same task, prompt, 11 tools + STOP, CU cost model, scorer,
stopping rule, driver (`discover/formal_e.py`, sha `d4451c42…`), sampling (API defaults, no seed), infrastructure retry
≤ 5 as frozen. No smoke runs. No prompt tuning. Frozen-hash check **PASS 15/15 before and after** Phase B
(`data/discover_boundary_c1/metadata/hashcheck_{before,after}_phaseB_*.json`).

## 1. Runs
| model | budgets | runs | complete traces | API requests | infra retries | driver exceptions |
|---|---|---|---|---|---|---|
| `gpt-5.4-mini-2026-03-17` | 175, 225 CU | 20 + 20 | 40/40 | 290 | 0 | 0 |
| `gpt-5.4-nano-2026-03-17` | 175, 225 CU | 20 + 20 | 40/40 | 254 | 0 | 0 |
| **total Phase B** | | **80** | **80/80** | 544 | 0 | 0 |

D reference reused (frozen, deterministic): 175 CU incomplete (winner only), 225 CU complete, CU_to_full = 206.

## 2. Core matrix — full decision (winner ∧ pair ∧ reachability), k/n [Wilson 95 %]
| tier | 175 CU (below D's threshold) | 225 CU (D completes) |
|---|---|---|
| strong `gpt-5.5` (Phase A) | **19/20** [0.76, 0.99] | **20/20** [0.84, 1.00] |
| mini `gpt-5.4-mini` | **0/20** [0.00, 0.16] | **6/20** [0.15, 0.52] |
| nano `gpt-5.4-nano` | **0/20** [0.00, 0.16] | **0/20** [0.00, 0.16] |
| D fixed-VOI | 0 | 1 |

ΔP_full vs D: strong +0.95 / 0.00; mini 0.00 / −0.70; nano 0.00 / −1.00.
Secondary (Fisher exact, two-sided): 175 CU mini vs strong p = 3 × 10⁻¹⁰, nano vs strong 3 × 10⁻¹⁰, nano vs mini 1.0;
225 CU mini vs strong 3 × 10⁻⁶, nano vs strong 1 × 10⁻¹¹, nano vs mini 0.020. Budget effect 175 → 225: strong +0.05,
mini +0.30, nano 0.00.

## 3. Component recovery (runs out of 20)
| tier / budget | winner | pair | BACKWARD run | reachability | break-even exact | narrow window | runs with ≥ 1 error | errors |
|---|---|---|---|---|---|---|---|---|
| strong 175 | 20 | 20 | 20 | 19 | 15 | 20 | 8 | 10 |
| strong 225 | 20 | 20 | 20 | 20 | 20 | 3 | 0 | 0 |
| mini 175 | 14 | 0 | 0 | 0 | 0 | 4 | 19 | 72 |
| mini 225 | 14 | 7 | 7 | 6 | 7 | 3 | 20 | 61 |
| nano 175 | 0 | 0 | 0 | 0 | 0 | 0 | 20 | 50 |
| nano 225 | 9 | 6 | 1 | 0 | 0 | 0 | 20 | 59 |

## 4. Failure taxonomy (first failing component, non-full runs)
| tier / budget | no winner | wrong winner | pair unresolved | BACKWARD never run | reachability never classified | reachability wrong |
|---|---|---|---|---|---|---|
| strong 175 (1 non-full) | 0 | 0 | 0 | 0 | 1 (budget exhausted) | 0 |
| mini 175 (20) | 5 | 1 | **14** | – | – | – |
| mini 225 (14) | 5 | 1 | 7 | 0 | 1 (agent STOP) | 0 |
| nano 175 (20) | **20** | 0 | – | – | – | – |
| nano 225 (20) | 9 | 2 | 3 | 5 (budget exhausted) | 0 | 1 |

Interface / tool errors (0-CU, turns consumed): mini 175 — 35 unaffordable OPTIMIZE_PROCESS requests, 16 INSPECT_CANDIDATES
called with an undeclared argument, 13 OPTIMIZE before a window existed, 3 BACKWARD before both metals were optimized,
2 TEST_REACHABILITY with undeclared arguments; mini 225 — 31 unaffordable OPTIMIZE, 17 undeclared-argument INSPECT, 6
premature OPTIMIZE, 3 premature BACKWARD; nano 175 — 39 unaffordable OPTIMIZE, 5 undeclared-argument INSPECT, 6
precondition errors; nano 225 — 46 unaffordable OPTIMIZE, 4 undeclared-argument INSPECT, 6 precondition errors.
Stop reasons: budget_exhausted by three consecutive unaffordable actions in 9 / 8 (mini 175 / 225) and 9 / 11 (nano)
runs; the rest are agent STOPs with an unresolved decision; one mini 175 run hit the no-tool-call limit.

## 5. Where the weak tiers fail, from the traces
- **Nano at 175 CU never identifies a winner (0/20).** Every run pays the 111-CU full window plus the 15-CU activity
  screen, leaving 49 CU, below the 29 CU × 2 needed to optimize the decision pair after the first candidate; the runs then
  request optimizations they cannot afford (39 BudgetExceeded errors) and end by the three-unaffordable rule or by STOP with
  no feasible candidate. Zero narrow windows in 40 nano runs.
- **Mini at 175 CU finds the winner in 14/20 but never resolves the pair (0/20).** Mini builds a narrow window in only
  4/20 runs (strong: 20/20) and otherwise follows the full-window route, which cannot reach the second optimization; 13
  premature OPTIMIZE calls and 16 malformed INSPECT calls consume turns. No mini run at 175 CU executed BACKWARD.
- **At 225 CU the budget is sufficient for D, yet mini completes only 6/20 and nano 0/20.** The extra 50 CU let mini
  complete the pair in 7/20 and reachability in 6/20 (CU_to_full 187–218, median 189); nano reaches a winner in 9/20 and
  runs BACKWARD once. The dominant losses are the same interface and sequencing errors as at 175 CU (unaffordable
  requests 31 / 46, undeclared arguments 18 / 4), i.e. the frozen tool contract is the binding constraint, not the budget.
- Unnecessary-CU fraction: mini 0.10 / 0.25, nano 0.19 / 0.29 (strong 0.06 / 0.13).

## 6. CU_to_full (full runs only)
| tier / budget | n full | median | IQR | range |
|---|---|---|---|---|
| strong 175 | 19 | 140 | 94–164 | 73–172 |
| strong 225 | 20 | 218 | 218–218 | 216–218 |
| mini 175 | 0 | – | – | – |
| mini 225 | 6 | 189 | 189–209 | 187–218 |
| nano 175 / 225 | 0 / 0 | – | – | – |

## 7. Tokens and requests (from `llm_meta`; cached-input tokens are not stored by the frozen driver, so cost cannot be
computed to the cent here — use the billing page)
| model | formal runs | API requests | prompt tokens | completion tokens | mean / median tokens per run |
|---|---|---|---|---|---|
| nano | 40 | 254 | 1,366,514 | 34,037 | 35.0 k / 32.2 k |
| mini | 40 | 290 | 1,693,635 | 96,222 | 44.7 k / 38.9 k |
| strong (Phase A) | 64 | 578 | 5,253,485 | 700,575 | 93.0 k / 71.3 k |

Per cell: nano 175 0.58 M / 0.02 M, nano 225 0.79 M / 0.02 M, mini 175 0.74 M / 0.04 M, mini 225 0.96 M / 0.05 M
(prompt / completion).

## 8. Answers
- **Q1 (does the 175-CU recovery reproduce in mini / nano?)** No. 0/20 and 0/20 against strong 19/20. The narrow-window
  behaviour that produces the recovery appears in 4/20 mini and 0/20 nano runs, and even those mini runs do not reach the
  pair decision.
- **Q2 (at 225 CU, where D completes, do weak tiers complete with E?)** Mini 6/20, nano 0/20, against D = 1. Adaptive
  allocation with a weak model is *worse* than the deterministic policy in the control region; the losses are interface
  errors (undeclared arguments, unaffordable requests, premature BACKWARD / OPTIMIZE) and unresolved candidate sets.
- **Q3 (capability threshold?)** Outcome **A / C**: strong ≫ mini > nano at 225 CU and strong ≫ mini = nano at 175 CU.
  The adaptive policy requires reasoning and tool-use capability that the two weaker tiers of the same family do not have;
  the advantage is not a property of the workflow alone.
- **Q4 (175 vs 225?)** For the strong tier the 175-CU cell is the decision-recovery regime and 225 CU the control region
  where D catches up. For the weak tiers there is no recovery regime: at 175 CU they cannot complete at all, and at 225 CU
  they underperform the fixed policy. The capability × budget interaction is therefore one-sided: budget helps mini
  (+0.30) but not nano (0.00), and neither reaches D's completion at the budget where D completes.

## 9. Interpretation and boundary
The budget-localized decision-recovery advantage established in Phase A is a **capability-dependent agent effect**, not a
model-independent workflow effect. Three quantities must stay separate in the manuscript:
1. *Policy advantage*: exists only where the budget is below D's completion threshold (150–200 CU) and only for the
   strong tier.
2. *Model capability*: the same frozen policy yields 0/20 (nano, mini) at 175 CU and 0/20 (nano), 6/20 (mini) at 225 CU;
   the deterministic policy D completes at 225 CU with no model at all.
3. *Raw compute efficiency*: above D's threshold the strong tier is 6–7 % later than D; the weak tiers do not reach a
   comparable state.

## 10. Manuscript-safe statement
> The adaptive decision-recovery regime below the fixed policy's 206-CU completion threshold is model-capability
> dependent: with the identical frozen protocol, gpt-5.5 completes the full decision in 19/20 runs at 175 CU, whereas
> gpt-5.4-mini and gpt-5.4-nano complete 0/20 each; at 225 CU, where the deterministic fixed-VOI policy completes, the
> weak tiers reach 6/20 and 0/20. Adaptive allocation is therefore an agent capability that a sufficiently strong model
> can exploit, not a property of the workflow that transfers to weaker models, and it does not translate into a raw
> compute saving.

## 11. Files
`data/discover_boundary_c1_phase_b_{runs,summary,tokens}.csv`, `data/discover_boundary_c1_phase_b_metadata.json`,
`data/discover_boundary_c1/runs/gpt-5.4-{mini,nano}-2026-03-17/` (80 traces), `data/discover_boundary_c1/logs/`,
`data/discover_boundary_c1/metadata/hashcheck_*phaseB*.json`, `discover/boundary_c1_phase_b_analysis.py`,
`figures/discover_boundary_c1/figP1_pfull_vs_CU_cross_model.png`, `figP2_175CU_recovery.png`, `figP3_225CU_control.png`,
`figP4_cu_to_full_and_failure_taxonomy.png`.
