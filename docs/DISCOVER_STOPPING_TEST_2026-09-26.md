# DISCOVER stopping test and next-stage Agent plan — 2026-09-26

**Status.** Part A (retrospective stopping test) is a **read-only replay of frozen traces, complete**. No model was
called; DISCOVER V1, DISCOVER-BOUNDARY-C1, the scorer, the stopping rule and every trace are untouched. Parts B and C
are **preregistered prospective arms, not run**: they change the protocol (B) or the model (C) and therefore carry new
family labels; they start only after the user's go and a fresh frozen-hash check.

Script: `tools/discover/c1_stopping_test.py` (harness copy `discover/c1_stopping_test.py`).
Outputs: `data/discover_stopping_test_runs_2026-09-26.csv` (one row per run, 852 runs: 297 C1 policy-E, 20 C1-E2, 3 C1 policy-D, 70 V1 policy-E, 140 cross-model V1, 280 random-A and 42 B/C/D baselines),
`data/discover_stopping_test_cells_2026-09-26.csv` (per cell), `data/discover_stopping_test_metadata_2026-09-26.json`.
Metric labels follow `AGENT_METRIC_DEFINITIONS_SOURCE_OF_TRUTH_2026-09-13.md`; every CU below is ledger-true
(`budget_CU − remaining_budget`), never the quote-based `action_cost`.

---

## 0. The observation that motivates this step, stated precisely

The 75-CU and 225-CU strong cells reach the same complete decision (20/20 each) at very different spend
(median decision-stable 52.5 versus 218 CU). The replay separates that difference into two parts that need
different fixes:

| cell | median decision-stable CU | median final CU | runs that kept paying after the public stopping rule held | where the extra compute sits |
|---|---:|---:|---:|---|
| strong 75 CU | 52.5 | 70 | 10/20 | **after** the rule: second process window + re-optimisation + repeat BACKWARD/reachability (numerical-target refinement) |
| strong 225 CU | 218 | 218 | **0/20** | **before** the rule: full 14,136-state window (111 CU) instead of a scoped one; the agent stops the moment the rule holds |
| strong non-binding 5,000 CU | 566 | 714 | 14/20 | after the rule: **RUN_MC only** (8,207 of 17,535 CU in the cell, 46.8%) |

So at 225 CU the agent already knows when it has computed enough; what it lacks there is allowance-independent
*scoping*. The missing stopping criterion shows up at the low-budget end (75 CU) and under a non-binding allowance.
Both are fixed by the same gate (Part B), but the 225-CU excess is not a stopping defect and must not be described
as one.

---

## Part A — retrospective stopping test on frozen traces

### A1. What is tested

The frozen environment computes a stopping status from the **public state only**
(`discover/env.py::stopping_status`):

- **S1** a feasible optimised lowest-cost candidate exists;
- **S2** no unresolved candidate (every candidate is optimised or screened dominated);
- **S3** if the highest-activity candidate differs from the winner, BACKWARD and a classified TEST_REACHABILITY exist for that pair.

Every trace step records this status as it stood before the agent chose that step's action
(`stopping_status_before`). The agent sees the same information and the frozen prompt tells it to stop
"only when the stopping rule allows it". The test asks, per run:

| quantity | definition |
|---|---|
| `S123_CU` | ledger spend at the first moment S1 ∧ S2 ∧ S3 held (the agent could have emitted STOP there) |
| `correct_at_S123` | the frozen scorer's full decision (winner ∧ pair ∧ reachability), replayed on the state at that moment |
| `decision_stable_CU` | quantity #4 of the source-of-truth file (ground truth; invisible to the agent) |
| `post_S123_CU` | `final_CU − S123_CU`, split by action type |
| counterfactual **"gate at S1∧S2∧S3"** | the run ends at `S123_CU` if the rule is ever satisfied, otherwise where the agent stopped |

Runs whose rule is first satisfied by their last action but that ended without a STOP step (budget exhausted) are
counted as reached at final spend with zero post-rule spend.

### A2. Strong tier, anonymous task (212 runs: C1 177 + V1 35)

| cell | n | complete (actual) | rule reached | correct at first S1∧S2∧S3 | complete under the gate | median S123 CU | median decision-stable CU | median final CU | runs paying after rule | median / max post-rule CU |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 50 | 20 | 13 | 13 | 13 | 13 | 47 | 47 | 49 | 7 | 1 / 10 |
| 75 | 20 | 20 | 20 | 20 | 20 | 52.5 | 52.5 | 70 | 10 | 3.5 / 23 |
| 100 | 20 | 19 | 19 | 18 | 19 | 65 | 71 | 81.5 | 13 | 14 / 47 |
| 125 | 20 | 20 | 17 | 17 | 20 | 73 | 79.5 | 111 | 12 | 16 / 65 |
| 150 | 20 | 20 | 20 | 20 | 20 | 102 | 102 | 124.5 | 8 | 0 / 72 |
| 175 | 20 | 19 | 19 | 19 | 19 | 124 | 124 | 163.5 | 9 | 0 / 101 |
| 200 | 8 | 8 | 1 | 1 | 8 | 65 | 189 | 189 | 1 | 74 / 74 |
| 225 | 20 | 20 | 20 | 20 | 20 | 218 | 218 | 218 | 0 | 0 / 0 |
| 250 | 9 | 9 | 8 | 8 | 9 | 218 | 218 | 218 | 1 | 0 / 33 |
| 5,000 (non-binding) | 20 | 20 | 20 | 20 | 20 | 566 | 566 | 714 | 14 | 148 / 2,455 |
| V1 200–2,000 (5 each) | 35 | 35 | 32 | 32 | 35 | — | — | — | 14 | — |

Pooled, strong anonymous: the rule was reached in **189/212** runs; the decision at that moment was already correct
in **188/189**; `S123_CU` equals the ground-truth decision-stable CU in **154/157** C1 runs (the other 3 are the one
false positive below and two 175-CU runs where the decision was correct 1–2 CU before the rule held). **89/189 runs
kept paying after the rule held, 13,634 of 51,230 CU in total (26.6%).** Under the gate the completion count is
**identical to the actual count in every cell**; only spend changes.

**What the post-rule compute is.**

- Bounded cells (50–250 CU, 1,746 CU post-rule in total): BUILD_PROCESS_WINDOW 733, RUN_MC 532, OPTIMIZE_PROCESS 414,
  TEST_REACHABILITY 94, BACKWARD 37, TEST_LEVER 9 CU; READ_* and CHECK_MODEL_VALIDITY cost 0. This is second-window
  refinement of the parity multiplier, i.e. quantitative-target work after the decision has closed
  (the same separation the manuscript already reports: parity recovered 9/20 at 75 CU versus 20/20 at 225 CU).
- Non-binding cell: **100% RUN_MC** (8,207 CU). Monte-Carlo draws cannot change winner, pair or reachability under the
  frozen scorer, so none of this spend can flip the decision.

**One false positive (F1 mechanism).** Run `B100_r18`: a 2,115-state window put Fe at 17.585 USD/t, parity 1.54×,
reachability "reachable"; the rule fired at 52 CU on a wrong verdict. The agent later rebuilt a 675-state window and
obtained 185× / "unreachable", but the frozen `final_answer` keeps the *first* BACKWARD and *first* classified
reachability, so the run is scored wrong at its own stop too. The rule is therefore blind to window-relative parity;
Part B adds the validity condition that closes this.

**Fifteen runs correct without the rule ever holding (F2 mechanism).** 7/8 at 200 CU and 3/5 at V1 200 CU stop with
one candidate unresolved (S2 false) after a full window + two optimisations (189 CU); the decision is nonetheless
correct. The gate never fires in these runs, so they are unaffected.

### A3. Weaker tiers (anonymous)

| tier | runs | complete | rule reached | correct at rule | paid after rule | complete without the rule ever holding |
|---|---:|---:|---:|---:|---:|---:|
| mini (C1 175/225/300/400 + V1) | 115 | 32 | 24 | 22 | 0 | 10 |
| nano (C1 175/225 + V1) | 75 | 6 | 6 | 6 | 0 | 0 |

Final public state of the runs that never reached the rule: mini S1 ∧ ¬S2 in 57/91 (winner found, a candidate left
unresolved because optimisation became unaffordable), ¬S1 in 13; nano ¬S1 in 33/69, S1 ∧ S2 ∧ ¬S3 in 16
(winner and pair resolved, reachability never classified). The weak tiers stop immediately once the rule holds
(0 CU post-rule). Their problem is reaching the rule, not stopping; a stopping gate does not move them, which is
consistent with the C1 interface-intervention result.

### A4. Fixed-VOI policy D

D never satisfies the public rule in the C1 cells (S2 unresolved at 214 CU with 11 CU left at 225 CU) and satisfies it
at 235 CU in the V1 ≥ 250-CU cells although its decision is stable at 206 CU. The gate does not shorten D below 206.

### A5. The agent's own expected-decision-value is not a usable soft criterion

Median self-reported EDV after the rule held is 0.25–0.55 in the strong cells (0.55 in the non-binding cell for
RUN_MC actions that cannot change the decision), comparable to the pre-rule medians. The self-estimate does not fall
when the decision closes, so an EDV threshold (frozen S4) would not have stopped these runs. The criterion has to be
structural (Part B), not confidence-based.

### A6. What Part A supports

1. The public S1 ∧ S2 ∧ S3 rule is an **almost exact stopping criterion for the strong tier**: 188/189 correct at
   first satisfaction, spend identical to the ground-truth decision-stable point in 154/157 C1 runs.
2. The strong tier **over-runs it in 89/189 runs**, and the over-run is always quantitative-target refinement
   (bounded cells) or RUN_MC (non-binding cell), never decision work.
3. Enforcing the rule would leave every completion count unchanged and remove the 148-CU median non-binding
   overrun entirely (median final 714 → 566) and the 75-CU overrun (median final 70 → 52.5).
4. The 225-CU excess over 75 CU is **pre-decision scoping**, not stopping, and needs an allowance-independent
   scoping rule instead.

---

## Part B — preregistration: DISCOVER-V2-STOP (protocol change; V1 stays frozen)

Family label reserved: **DISCOVER-V2-STOP** (a `DISCOVER V2` sub-family per `VERSION_REGISTRY.md` rule 5). Task,
prompt, 11 actions, cost model, scorer and ledger are inherited byte-for-byte from V1; only the stopping mechanism
changes. Hashes of every inherited file are recorded before and after; any mismatch voids the run.

### B1. Arms

| arm | change relative to V1 | expected from Part A |
|---|---|---|
| **S-hard** | the environment terminates the episode at the first step where S1 ∧ S2 ∧ S3 holds and takes `final_answer` from that state | strong 75 CU: 20/20 at median 52.5; non-binding: 20/20 at median 566, zero RUN_MC overrun; 100-CU false positive remains |
| **S-gate** (primary) | after S1 ∧ S2 ∧ S3 holds, a *paid* action is admissible only if it is flip-capable: `CHECK_MODEL_VALIDITY` (0 CU), re-`OPTIMIZE_PROCESS` when the validity check reports the winner optimum on a window edge, `BUILD_PROCESS_WINDOW` when that re-optimisation needs one, and `BACKWARD`/`TEST_REACHABILITY` whenever the winner's optimum changed. `RUN_MC`, `TEST_LEVER` and repeat windows on a validated optimum are rejected (0 CU, turn consumed, reason returned). The rule itself gains **S3′ = S3 ∧ validity check passed for the winner's optimum**. | same completion; removes the F1 false positive (the 100-CU run would have been forced to re-optimise after the edge check); spend ≤ S-hard + the cost of the validity-driven re-optimisation |
| **S-anytime** (scoping) | prompt addendum only: reach S1 ∧ S2 ∧ S3′ at minimum spend first, then widen only if the validity check fails. Allowance is still shown. | tests whether 225-CU spend collapses toward the 75-CU value; the allowance-invariance endpoint below |

### B2. Cells and sample size

Strong tier only (the weak tiers never reach the rule; adding them tests allocation, not stopping): 75, 225 and
5,000 CU × 20 runs × 3 arms = **180 runs**, anonymous variant, same sampling settings as C1. n = 20 per cell is the
C1 convention and gives a Wilson 95% CI of [0.84, 1.00] for 20/20.

### B3. Endpoints and gates (fixed before any result is read)

| endpoint | pass | fail |
|---|---|---|
| complete-decision count per cell (frozen scorer) | ≥ 19/20 in every cell and arm | any cell < 19/20 → the gate harms completion; report as a negative result |
| post-rule spend | median 0 CU in S-hard and S-gate at 75 and 5,000 CU | — |
| false-positive rate of S3′ | 0/60 across S-gate cells | ≥ 1 → report the mechanism; do not tune the rule after the fact |
| allowance invariance (S-anytime) | median final spend at 225 CU within 25 CU of the 75-CU median | otherwise the scoping is allowance-driven and the manuscript keeps the current "budget-induced search compression" wording |
| parity multiplier recovery | reported, not gated (decision and target recovery stay separate) | — |

Cost: the strong model is the only API spend (≈ 180 runs × 10–30 turns); the scientific compute is the harness cache.

---

## Part C — preregistration: open-weights cross-model validation on the unchanged V1 protocol

### C1. What stays fixed

DISCOVER V1 frozen protocol, anonymous variant, policy E, driver `discover/formal_e2.py` unchanged. The driver already
takes `--model` and honours `OPENAI_BASE_URL`, so an open-weights model is reached through an OpenAI-compatible
tool-calling endpoint (vLLM with `--enable-auto-tool-choice` and the model's tool-call parser) without touching the
driver. Sampling at API defaults, as for the three closed tiers. Traces carry `stopping_status_before`, so Part A's
test applies unchanged.

### C2. Model selection rule (decided before results)

Candidate set: open-weights models with a permissive licence, native function calling, and a footprint that fits the
8 × RTX 3090 node (192 GB): Qwen3-32B (dense, bf16, tensor-parallel 4) as the **primary**; gpt-oss-120b (MXFP4) as the
**second open tier**; a Qwen3-235B-A22B quantised build only if both run cleanly. Admission is a tool-interface smoke
test: 3 dry runs at 225 CU with **zero malformed or undeclared-argument calls** (the failure class that dominated
the weak closed tiers). A model that fails admission is recorded and replaced, not retried on the formal cells.

### C3. Cells and endpoints

75, 175, 225 CU × 20 runs (60 runs per model), plus 5,000 CU × 20 if the model completes ≥ 19/20 at 225 CU.
Endpoints, all with Wilson CIs and Fisher tests against the matching closed-tier cells: P(full), P(win), P(pair),
P(reach); canonical narrow-window use; rule-reach rate and post-rule spend (Part A metrics); tool-interface error
count. Hypotheses, both informative:

- **H-transfer**: an open model of comparable capability reproduces the strong-tier regime (≥ 19/20 at 75 CU with
  narrow-window use) → the decision-recovery result is not vendor-specific.
- **H-tier**: it does not, and its failures are the weak-tier modes (¬S2 / ¬S3) → the result is capability-tiered
  across vendors, which strengthens the current "model-tier dependent" wording.

Reporting uses the same tables as `CROSS_MODEL_DISCOVER_V1.md` and `CROSS_MODEL_STATS_V1.md`.

### C4. Infrastructure requirements (to verify before the smoke test, not assumed)

vLLM with the model's tool parser on the GPU node; the harness (`Catalyst_Economic_Leverage_Automation_Harness_v0.1`)
reachable from the driver host with its `cache/` response surfaces; `OPENAI_BASE_URL` set to the vLLM endpoint and a
placeholder key; `tests/test_frozen_untouched.py` green before and after.

---

## Execution order

1. **Done** — Part A replay; outputs committed with this note.
2. Manuscript: add the Part A statement to the Agent Results paragraph and Methods (wording in `RESULTS_AT_A_GLANCE`
   style: "the public S1–S3 rule is satisfied in 189/212 strong runs, with the decision already correct in 188 of
   them; 26.6% of strong-tier spend, and 46.8% under the non-binding allowance, follows the rule and is
   quantitative-target or Monte-Carlo work"). Keep the 225-versus-75 difference described as scoping.
3. Part C smoke test on the GPU node (no protocol change, cheapest, and it decides whether an open tier exists).
4. Part B S-gate and S-anytime arms on the strong tier; S-hard only as the control.
5. Then Part C formal cells on the admitted open model, followed by the Part B gate on that model if it reaches the
   strong regime.

Steps 3–5 need the user's go: they call models and mint new family labels.

---

## Files added by this step

| file | content |
|---|---|
| `tools/discover/c1_stopping_test.py` | replay script (read-only; imports the frozen scorer and the frozen extension metric) |
| `data/discover_stopping_test_runs_2026-09-26.csv` | 852 rows: every E and A–D run in V1, cross-model V1 and C1 (anonymous + named) |
| `data/discover_stopping_test_cells_2026-09-26.csv` | per-cell aggregates used in the tables above |
| `data/discover_stopping_test_metadata_2026-09-26.json` | generation time, globs, scorer statement |
