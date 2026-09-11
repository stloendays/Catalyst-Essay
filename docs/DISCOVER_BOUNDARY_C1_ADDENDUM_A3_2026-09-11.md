# DISCOVER-BOUNDARY-C1 Addendum A3 — error taxonomy, canonical narrow-window rule, 175-vs-225 consistency (2026-09-11)

Scope: trace-level analysis of the **existing** frozen C1 runs. No model was called, no scientific value was recomputed,
no frozen file was modified (`DISCOVER_FROZEN_V1.json` = **15/15 PASS** before and after this analysis). This addendum
answers items 2, 5 and 6 of the 2026-09-11 supervisor request; items 1, 3, 4 and 7 require new runs and are listed as
pending at the end.

Generator: `discover/c1_error_taxonomy.py` (harness, non-frozen).
Data: `data/discover_boundary_c1_error_taxonomy_runs.csv`, `data/discover_boundary_c1_error_taxonomy_summary.csv`.

## 1. Canonical narrow-window rule (item 6)

The previous C1 flag counted a run as using a narrow window whenever a `BUILD_PROCESS_WINDOW` call carried a non-empty
`bounds` argument. That flag is not sound: bounds can also select the entire admissible domain, so full-domain windows
were counted as narrow.

**Canonical rule, fixed here.** A run uses narrow-window allocation if and only if

1. it builds at least one process window whose `n_states` is strictly smaller than the full admissible state set
   (**14,136** states), **and**
2. at least one later scoped action (`OPTIMIZE_PROCESS`, `RUN_MC`, `TEST_LEVER`, `BACKWARD`, `CHECK_MODEL_VALIDITY`)
   succeeds against that window.

Condition 2 matters: building a narrow window costs CU but only changes the decision path if it is actually used.

| tier | budget | n | narrow-window (canonical) | narrow-window (legacy bounds flag) |
|---|---|---|---|---|
| strong | 150 | 7 | **7/7** | 7/7 |
| strong | 175 | 20 | **20/20** | 20/20 |
| strong | 200 | 8 | **1/8** | 3/8 |
| strong | 225 | 20 | **0/20** | 3/20 |
| strong | 250 | 9 | **0/9** | 0/9 |
| mini | 175 | 20 | **0/20** | 4/20 |
| mini | 225 | 20 | **0/20** | 3/20 |
| nano | 175 | 20 | **0/20** | 0/20 |
| nano | 225 | 20 | **0/20** | 0/20 |

Two corrections to the previously reported numbers follow:

- **mini at 175 CU is 0/20, not 4/20.** All four legacy hits were full-domain bounds. No tested weaker tier ever
  completes a scoped action against a genuinely narrow window.
- **strong at 225 CU is 0/20.** Above the fixed-policy completion threshold the strong model stops narrowing and
  optimises over the full 14,136-state domain in every run.

This strengthens rather than weakens the mechanism claim: narrow-window allocation is used **only** below the
fixed-policy completion threshold (7/7 at 150 CU, 20/20 at 175 CU, 1/8 at 200 CU, 0/20 at 225 CU, 0/9 at 250 CU), and
only by the strong tier.

## 2. Break-even and reachability consistency, 175 vs 225 CU (item 2)

Decision-relevant verdict — **invariant across the two budgets**:

| quantity | strong 175 CU | strong 225 CU |
|---|---|---|
| Ru reachability classification | `unreachable` **20/20** | `unreachable` **20/20** |
| scaling headroom at reference (673 K) | 1.0899 | 1.0899 |
| scaling headroom across process states | 2.5246 | 2.5246 |

Both headroom values equal the frozen NH3-FINAL-1.1 anchors exactly, at both budgets.

Quantitative break-even target — **budget-sensitive, but discretely and diagnosably so**:

| scored Ru→Fe break-even multiplier | strong 175 CU | strong 225 CU |
|---|---|---|
| 201.223443 (canonical) | **15/20** | **20/20** |
| 157.289910 | 4/20 | 0/20 |
| 209.602546 | 1/20 | 0/20 |

The deviations are not stochastic scatter. Every run that returns a non-canonical value computed `BACKWARD` inside a
window that excludes the true parity state (T 425 °C, P 190 bar, T_sep 30 °C):

- **157.289910** comes from windows that exclude T_sep = 30 °C, which relocates parity to T_sep 0 °C / 190 → 110 bar;
- **209.602546** comes from a single-state window (`incumbent_state`, `n_states` = 1) at 180 bar.

At 225 CU every strong run optimises over the full domain and recovers 201.223443 exactly, 20/20.

**Read-out.** Below the fixed-policy threshold the agent recovers the complete *decision* — winner, decision pair and
`unreachable` verdict — with the same reachability numbers as above the threshold. What degrades below the threshold is
the precision of the scalar break-even target, in 5/20 runs, by a window-scope artefact that is identifiable from the
trace. This trade-off must be stated with the decision-recovery claim.

## 3. Error taxonomy (item 5)

Every 0-CU action error is assigned to exactly one mechanism. Turns with no tool call are interface failures but are not
0-CU action errors, so they are counted separately; this keeps the action-error totals byte-identical to the frozen
Phase A/B summaries.

- **interface** — the model could not express a legal call: undeclared or wrong-typed argument, unknown action.
- **budget** — the call was legal but its quoted cost exceeded the remaining budget (`BudgetExceeded`).
- **sequencing** — the call was legal and affordable but violated an evidence precondition, split into premature
  `BACKWARD`, premature `OPTIMIZE_PROCESS`, and other premature calls.

| tier | budget | n | action errors | interface | budget | sequencing | premature BACKWARD | premature OPTIMIZE | no-tool-call turns |
|---|---|---|---|---|---|---|---|---|---|
| strong | 150 | 7 | 1 | 1 | 0 | 0 | 0 | 0 | 3 |
| strong | 175 | 20 | 10 | 4 | 0 | 6 | 6 | 0 | 11 |
| strong | 200 | 8 | 1 | 0 | 0 | 1 | 0 | 0 | 2 |
| strong | 225 | 20 | 0 | 0 | 0 | 0 | 0 | 0 | 7 |
| strong | 250 | 9 | 0 | 0 | 0 | 0 | 0 | 0 | 3 |
| **strong total** | | 64 | **12** | 5 | **0** | 7 | 6 | 0 | 26 |
| mini | 175 | 20 | 72 | 18 | 36 | 18 | 3 | 13 | 16 |
| mini | 225 | 20 | 61 | 20 | 32 | 9 | 3 | 6 | 14 |
| **mini total** | | 40 | **133** | 38 | 68 | 27 | 6 | 19 | 30 |
| nano | 175 | 20 | 50 | 5 | 39 | 6 | 0 | 3 | 9 |
| nano | 225 | 20 | 59 | 4 | 49 | 6 | 0 | 1 | 3 |
| **nano total** | | 40 | **109** | 9 | 88 | 12 | 0 | 4 | 12 |

The **133 errors** of the supervisor request are the mini tier total (72 at 175 CU + 61 at 225 CU). The strong tier
produces **12** action errors over 64 runs, and **zero** budget errors at any budget.

### 3.1 nano and mini fail in different ways

Both weaker tiers fail, but not for the same reason, and the difference is quantitative:

- **nano is budget-blind.** 88/109 errors (**81%**) are unaffordable requests, overwhelmingly `OPTIMIZE_PROCESS`
  (39 at 175 CU, 46 at 225 CU). nano repeatedly re-requests the same unaffordable full-window optimisation until the
  three-consecutive-unaffordable rule ends the run. Interface errors are rare (9/109, 8%). nano never runs `BACKWARD`
  at 175 CU and completes 0/40 decisions overall.
- **mini is interface- and sequencing-limited as well as budget-limited.** Budget errors fall to 68/133 (**51%**),
  while interface errors rise to 38/133 (**29%**) and sequencing errors to 27/133 (**20%**), including 19 premature
  `OPTIMIZE_PROCESS` calls before any window exists and 6 premature `BACKWARD` calls before both metals are optimised.
  The single most repeated interface error is passing arguments to the argument-free `INSPECT_CANDIDATES`
  (16 at 175 CU, 17 at 225 CU). mini does reach the decision chain — 6/20 complete at 225 CU, 14/20 identify the
  winner at 175 CU — but spends its budget on rejected calls before closing `BACKWARD` → `TEST_REACHABILITY`.

So nano fails at the *accounting* layer and never reaches the scientific decision chain; mini reaches the chain and
fails at the *interface and ordering* layer. This is the measured motivation for the item-3 intervention (typed tool
parameters plus an explicit remaining-budget block), which targets exactly these two dominant mechanisms.

### 3.2 The single strong-model failure at 175 CU

Run `E_llm_agent_anonymous_B175_r16_c1_20260909T131633Z` (`run_index` 16) is the 1/20 non-complete strong run. It is a
**probe-before-target ordering failure**, not a capability or budget-size failure:

1. step 3 built the **full** 14,136-state window for 111 CU, leaving 49 of 175 CU;
2. step 7 called `TEST_REACHABILITY` on Ru with `scope: "reference"` and **no `required_multiplier`**, so the result
   carried headroom (1.0899) but no `classification` field — S3 cannot be satisfied without it;
3. `BACKWARD` only ran at steps 12–13, returning the correct 201.223443 inside a 1,211-state narrow window;
4. by then 0 CU remained, so the 2-CU `TEST_REACHABILITY` re-call that would have classified Ru as `unreachable` was
   unaffordable. The run stopped with the correct winner and correct decision pair but an unclassified reachability
   verdict.

Opening with the full window is not itself the discriminator: 7/20 strong runs at 175 CU did so and 6 of the 7 still
completed. The discriminator is calling the reachability probe before `BACKWARD` had produced the multiplier it needs,
leaving no budget to re-classify. Scored: `winner_correct` = true, `pair_decision_correct` = true,
`reachability_correct` = false.

## 4. Claim wording

Supported by C1 as of this addendum:

> Under the frozen benchmark protocol, the decision-aware agent enables **complete decision recovery below the
> fixed-policy compute threshold**: at 175 CU, where the deterministic fixed-VOI policy cannot complete (threshold
> 206 CU), the strong model completes the decision in 19/20 runs, with the reachability verdict and its scaling-headroom
> values identical to the above-threshold cell, and recovers the canonical break-even target in 15/20 runs. This
> recovery is model-tier dependent (0/20 mini, 0/20 nano at 175 CU) and is obtained by narrow-window allocation, which
> the canonical rule shows is used only below the threshold (20/20 at 175 CU, 0/20 at 225 CU) and only by the strong
> tier (0/20 mini, 0/20 nano).

Not supported, and not to be written:

> a universal compute saving, or a general claim that adaptive LLM allocation is more compute-efficient than the
> deterministic VOI policy. At 225 CU the strong agent reaches the full decision at a median of 218 CU against D's
> 206 CU.

## 5. Pending items requiring new runs

| item | requirement | status |
|---|---|---|
| 1 | strong 125 and 150 CU, 20 runs each, lowest stable completion threshold | pending; 150 CU already has n = 7 (7/7), needs 13 more for n = 20 |
| 2b | uncapped strong runs to locate the natural stopping point | pending |
| 3 | mini at 175 CU, 20 runs, with the E2 budget-aware typed-tool interface | interface implemented (`discover/formal_e2.py`, `discover/llm_policy_v2.py`), runs pending |
| 4 | mini at 300 and 400 CU, saturation against strong-175 | pending |
| 7 | one open-source model in the strong tier as a reproducible control | pending; provider and endpoint not yet chosen |

The E2 interface arm is implemented and unit-checked but **not yet executed**. It writes traces under policy
`E2_llm_agent_budget_aware` so that no analysis can pool them with frozen policy-E runs, and it modifies no frozen
file: the prompt, task, action schema, cost model, environment and scorer are imported verbatim.
