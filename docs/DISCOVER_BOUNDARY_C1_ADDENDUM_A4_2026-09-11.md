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
| **125 CU** | 20 | **20/20** (P = 1.00, CI 0.84–1.00) | **80 CU** | 104.7 | 11/20 | 20/20 | 2 |
| **150 CU** | 20 | **20/20** (P = 1.00, CI 0.84–1.00) | 106 CU | 117.5 | 11/20 | 20/20 | 4 |
| 175 CU | 20 | 19/20 (P = 0.95) | 140 CU | 150.6 | 15/20 | 20/20 | 10 |
| 200 CU | 8 | 8/8 | 189 CU | 182.8 | 7/8 | 1/8 | 1 |
| 225 CU | 20 | 20/20 | 218 CU | 217.8 | **20/20** | 0/20 | 0 |
| 250 CU | 9 | 9/9 | 218 CU | 224.7 | 9/9 | 0/9 | 0 |
| D fixed-VOI | — | complete at **206 CU** | 206 CU | — | exact | n/a | n/a |

**The answer depends on what "completion" means, and both versions must be reported.**

- If completion is the scored full decision (winner + decision pair + reachability verdict), the strong tier is at
  **20/20 down to 125 CU**, the lowest budget tested — **60.7%** of the fixed policy's 206 CU threshold. At 125 CU the
  median run reaches the complete decision after only **80 CU**, i.e. **39%** of D's threshold. **The lower failure edge
  has not been located.** 125 CU is not a measured floor; it is the bottom of the tested range.
- If completion additionally requires the canonical Ru→Fe break-even multiplier, the lowest stable budget is **225 CU**,
  above D's threshold. Break-even exactness degrades monotonically as budget falls: 20/20 at 225 CU, 15/20 at 175 CU,
  11/20 at 150 CU, 11/20 at 125 CU.

At 125 and 150 CU the non-canonical break-even values are no longer confined to the two discrete window-scope artefacts
seen at 175 CU. The 150 CU cell contains values spanning 2.67 to 2205.42. These come from windows so narrow that the
parity state is far outside them, so the scalar is no longer conservative — it is simply not the canonical target. The
scored decision is still correct because the reachability verdict (`unreachable`) does not depend on the exact
multiplier, only on its being far above the 2.5246 headroom.

**Read-out.** Complete decision *recovery* extends much further below the fixed-policy threshold than C1 previously
established — to at least 125 CU, and in the median to 80 CU of actually-spent compute. The quantitative break-even
*target* does not: it needs 225 CU to be stable. The paper claim must separate these two.

Narrow-window allocation is now 20/20 at all three below-threshold budgets (125, 150, 175 CU), 1/8 at 200 CU and 0/20
and 0/9 at 225 and 250 CU. The median smallest window shrinks as the budget shrinks — 1,950 states at 125 CU, 1,262 at
150 CU, 1,122 at 175 CU, out of 14,136 — which is the allocation mechanism made quantitative.

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

## 4. Remaining items

| item | status |
|---|---|
| 1 | strong 125/150 CU done at n = 20; **the completion floor is still below the tested range** and needs 75/100 CU to locate |
| 2 | 175-vs-225 consistency closed in Addendum A3; **uncapped strong runs still pending** |
| 3 | closed, negative: the E2 interface does not move mini across the 175 CU boundary |
| 4 | mini 300/400 CU saturation sweep pending; to be run on the **frozen E interface** for comparability with the existing mini 175/225 cells |
| 7 | open-source strong-tier control deferred to the reproducibility-package stage |
