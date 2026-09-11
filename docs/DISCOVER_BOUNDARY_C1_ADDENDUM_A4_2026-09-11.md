# DISCOVER-BOUNDARY-C1 Addendum A4 — low-budget strong cells and the E2 interface intervention (2026-09-11)

New formal runs executed on 2026-09-11 under the frozen DISCOVER V1 scientific environment. Frozen hashes **15/15 PASS**
before the batch. **53 formal runs, 0 infrastructure retries, 0 driver exceptions.** No NH3, MeOH, Au/TiO2 or figure
result was recomputed; `configs/nh3_final.yaml`, the cost model, the prompt, the task, the action schema, the
environment and the scorer were used verbatim.

| batch | model | policy | budget | runs |
|---|---|---|---|---|
| 1 | gpt-5.5-2026-04-23 | E (frozen) | 125 CU | 20 (r0–r19, new cell) |
| 2 | gpt-5.5-2026-04-23 | E (frozen) | 150 CU | 13 (r7–r19, completing the cell to n = 20) |
| 3 | gpt-5.4-mini-2026-03-17 | **E2** (budget-aware typed tools) | 175 CU | 20 (r0–r19, new arm) |

One non-formal verification run of the never-before-executed E2 driver was made first (r99, written to
`DISCOVER_BOUNDARY_C1/e2_smoke/`, excluded from every formal count).

## 1. Strong-tier completion floor was not reached (item 1)

| budget | n | complete decision | CU to full decision (median) | mean spent | canonical break-even 201.223443 | narrow-window (canonical) | action errors |
|---|---|---|---|---|---|---|---|
| **100 CU** | 20 | **19/20** (P = 0.95, CI 0.76–0.99) | **71 CU** | 81.8 | 9/20 | 20/20 | 4 |
| **125 CU** | 20 | **20/20** (P = 1.00, CI 0.84–1.00) | **80 CU** | 104.7 | 11/20 | 20/20 | 2 |
| **150 CU** | 20 | **20/20** (P = 1.00, CI 0.84–1.00) | 106 CU | 117.5 | 11/20 | 20/20 | 4 |
| 175 CU | 20 | 19/20 (P = 0.95) | 140 CU | 150.6 | 15/20 | 20/20 | 10 |
| 200 CU | 8 | 8/8 | 189 CU | 182.8 | 7/8 | 1/8 | 1 |
| 225 CU | 20 | 20/20 | 218 CU | 217.8 | **20/20** | 0/20 | 0 |
| 250 CU | 9 | 9/9 | 218 CU | 224.7 | 9/9 | 0/9 | 0 |
| D fixed-VOI | — | complete at **206 CU** | 206 CU | — | exact | n/a | n/a |

**The answer depends on what "completion" means, and both versions must be reported.**

- If completion is the scored full decision (winner + decision pair + reachability verdict), the strong tier holds at
  **20/20 at 125 and 150 CU** and **19/20 at 100 CU** — **48.5%** of the fixed policy's 206 CU threshold. At 100 CU the
  median run reaches the complete decision after only **71 CU**, i.e. **34%** of D's threshold. **The lower failure edge
  has not been located.** 100 CU is not a measured floor; it is the bottom of the tested range.
- If completion additionally requires the canonical Ru→Fe break-even multiplier, the lowest stable budget is **225 CU**,
  above D's threshold. Scored break-even exactness degrades monotonically as budget falls: 20/20 at 225 CU, 15/20 at
  175 CU, 11/20 at 150 and 125 CU, 9/20 at 100 CU.

**The break-even degradation is mostly a scoring-convention effect, not an inability to compute the target.** The frozen
`final_answer()` reports the **first** `BACKWARD` record matching the decision pair (`next(...)`, not the last), and the
same for the first classified `TEST_REACHABILITY`. At low budgets the agent's first `BACKWARD` is often taken in a
preliminary window that does not yet contain the parity state, and the later, correct value never reaches the scored
answer. Measured across every strong cell, the scored break-even is identical to the first `BACKWARD` in 100% of runs,
while the canonical value is computed *at some point in the run* far more often:

| budget | n | first BACKWARD = canonical | scored break-even = canonical | **any** BACKWARD = canonical |
|---|---|---|---|---|
| 100 CU | 20 | 9 | 9 | **16** |
| 125 CU | 20 | 11 | 11 | **17** |
| 150 CU | 20 | 11 | 11 | **17** |
| 175 CU | 20 | 15 | 15 | **19** |
| 225 CU | 20 | 20 | 20 | 20 |

So the agent's *capability* to reach 201.223443 degrades only from 20/20 to 16/20 between 225 and 100 CU, while the
*scored* value degrades from 20/20 to 9/20. The frozen first-record convention was pre-registered and the scores stand
as reported, but the degradation must not be described as the agent failing to find the break-even at low budget.

Where the first record is wrong it is wrong in one of two ways: a preliminary window that excludes T_sep = 30 °C, giving
157.289910, or a very small local window, giving values from 1.54 to 2205.42. The scored *decision* survives this in
almost every run because the reachability verdict depends only on the multiplier being far above the 2.5246 headroom,
not on its exact value.

**Read-out.** Complete decision *recovery* extends much further below the fixed-policy threshold than C1 previously
established — to at least 125 CU, and in the median to 80 CU of actually-spent compute. The quantitative break-even
*target* does not: it needs 225 CU to be stable. The paper claim must separate these two.

Narrow-window allocation is 20/20 at every below-threshold budget tested (100, 125, 150, 175 CU), 1/8 at 200 CU and
0/20 and 0/9 at 225 and 250 CU. The median smallest window shrinks as the budget shrinks — 1,950 states at 125 CU,
1,262 at 150 CU, 1,122 at 175 CU, out of 14,136 — which is the allocation mechanism made quantitative.

### 1.1 The single 100 CU failure is a premature first BACKWARD

Run `E_llm_agent_anonymous_B100_r18_c1low` is the 1/20 non-complete run at 100 CU, and it fails differently from the
single 175 CU failure. It **did** reach the correct verdict: at step 18 `BACKWARD` returned 185.30 in a 675-state window
and at step 22 `TEST_REACHABILITY` classified Ru as `unreachable`, with 31 CU still unspent. But at step 8 it had
already run a premature `BACKWARD` in a not-yet-optimised window, returning 1.5424, and at step 13 classified Ru as
`reachable` on that basis. Under the first-record convention those two early records are the scored answer, so the run
scores `reachability_correct` = false despite containing the correct result. The 175 CU failure (`r16`) is the opposite
case: it never obtained a classification at all, because it probed reachability before `BACKWARD` produced the required
multiplier and then ran out of budget for the 2-CU re-call.

Both failures are therefore ordering failures around `BACKWARD`, in opposite directions: probing too early and never
correcting (100 CU), and probing too early and having no budget left to correct (175 CU).

## 2. The E2 interface intervention does not move mini across the boundary (item 3)

This is a **negative result** and is reported as one.

| metric | mini E (frozen interface) | mini E2 (budget-aware typed tools) |
|---|---|---|
| complete decision | 0/20 | **0/20** |
| correct winner | 14/20 | **19/20** |
| decision pair correct | 0/20 | 0/20 |
| reachability correct | 0/20 | 0/20 |
| built a process window | 20/20 | 20/20 |
| **ran BACKWARD at all** | **0/20** | **0/20** |
| action errors | 133 → per-cell 72 | **122** |
| — interface errors | 18 | **0** |
| — no-tool-call turns | 16 | **4** |
| — budget errors | 36 | 51 |
| — sequencing errors | 18 | **71** |
| — of which premature OPTIMIZE_PROCESS | 13 | **67** |
| validation rejections | n/a | 0 |
| median steps | 8 | 13 |

The intervention did exactly what it was designed to do on its own layer, and that is what makes the result
interpretable:

- **the interface failure mode was eliminated outright.** Typed tool parameters with `additionalProperties: false`
  removed all 18 undeclared-argument errors, including every one of the 16 calls that had passed arguments to the
  argument-free `INSPECT_CANDIDATES`. Zero validation rejections were needed — the typed schema prevented the malformed
  calls upstream rather than catching them. No-tool-call turns fell from 16 to 4;
- **budget visibility did not produce budget discipline.** With an explicit `_budget` block listing remaining CU and the
  quoted cost of every affordable action, budget errors *rose* from 36 to 51;
- **the freed turns went into worse ordering.** Premature `OPTIMIZE_PROCESS` calls rose from 13 to 67, and total
  sequencing errors from 18 to 71. Median steps rose from 8 to 13, so mini issued more legal-looking calls per run in
  the wrong order;
- **the decision chain never starts.** Under *both* interfaces, mini ran `BACKWARD` in **0/20** runs at 175 CU. Since
  `BACKWARD` is a precondition of the reachability verdict, no interface change can produce a complete decision while
  this holds.

The one genuine gain is winner identification, 14/20 → 19/20: removing interface noise lets mini reliably reach the
optimise-and-compare stage. It does not reach the backward-design stage.

**Read-out.** mini's barrier at 175 CU is not interface expressiveness and not budget visibility. It is the inability to
plan and hold the `BUILD_PROCESS_WINDOW → OPTIMIZE_PROCESS → BACKWARD → TEST_REACHABILITY` ordering under a binding
budget. This strengthens the model-tier-dependence claim rather than weakening it: the below-threshold advantage is a
capability property, not an artefact of a weak tool interface that better scaffolding would remove.

## 3. Integrity record

- frozen hashes 15/15 PASS **before and after** the batch (`metadata/hashcheck_{before,after}_2026-09-11_extension_*.json`), with `discover/formal_e.py` SHA-256 unchanged at `d4451c42...`;
- 53/53 formal runs completed; 0 infrastructure retries; 0 driver exceptions; no run discarded;
- the E2 arm writes policy `E2_llm_agent_budget_aware` and is never pooled with frozen policy-E runs;
- E2 changes only the interface: prompt, task, action schema, cost model, environment and scorer are imported verbatim,
  and `discover/formal_e.py` is unmodified (its own SHA-256 is recorded in every E2 trace for comparison);
- generators: `tools/discover/formal_e2.py`, `tools/discover/llm_policy_v2.py`, `tools/discover/c1_error_taxonomy.py`;
- data: `data/discover_boundary_c1_error_taxonomy_runs.csv`, `data/discover_boundary_c1_error_taxonomy_summary.csv`.

### 3.1 Aborted 75 CU batch (infrastructure, not science)

A first 75 CU batch was launched on 2026-09-11 and aborted mid-batch when the API account exhausted its credits
(HTTP 429, "You have no credits remaining"). Of 20 requested runs, 3 completed, 1 was truncated at step 11, and 16
produced zero-step traces. **No 75 CU result was derived from that batch**; n = 3 is not a cell.

Nothing was deleted. The 17 infrastructure-failed traces were moved verbatim to
`DISCOVER_BOUNDARY_C1/quarantine_infra_failed_2026-09-11/` with a `QUARANTINE_MANIFEST.json`, out of the scored glob
path so that no analysis can pool zero-step traces into a 75 CU cell and report 3/20. The 3 valid runs were separately
moved to `DISCOVER_BOUNDARY_C1/superseded_partial_B75_2026-09-11/` with a `SUPERSEDED_MANIFEST.json`, so that the
re-run 75 CU cell comes from one complete batch rather than mixing two. Frozen hashes were 15/15 PASS before and after
the aborted batch.

## 4. Remaining items

| item | status |
|---|---|
| 1 | strong 100/125/150 CU done at n = 20; **the completion floor is still below the tested range**; the 75 CU cell was aborted by API credit exhaustion and is being re-run |
| 2 | 175-vs-225 consistency closed in Addendum A3; **uncapped strong runs still pending** |
| 3 | closed, negative: the E2 interface does not move mini across the 175 CU boundary |
| 4 | mini 300/400 CU saturation sweep pending; to be run on the **frozen E interface** for comparability with the existing mini 175/225 cells |
| 7 | open-source strong-tier control deferred to the reproducibility-package stage |
