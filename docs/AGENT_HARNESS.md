# Decision-aware Agent Harness

## Role in the project

The **Decision-aware Agent Harness** is the workflow-automation layer used to make the deterministic multiscale framework repeatedly executable. It does not replace the physics, process model or economics; instead, it orchestrates reaction-specific scientific tools under a shared decision logic.

```text
Layer A — deterministic multiscale harness
frozen inputs
 -> scaling / BEP
 -> MKM
 -> reactor / process optimization
 -> economics
 -> ranking / uncertainty / backward design
 -> reproducible outputs

Layer B — decision layer
inspect current evidence
 -> identify the unresolved decision component
 -> choose an admissible scientific action
 -> execute Layer A calculation
 -> update ranking / feasibility / reachability
 -> stop / continue / redirect
```

The central AI question is:

> Given a finite scientific-compute budget, can an agent allocate calculations according to their value to the downstream industrial decision, so that the same ranking–parity–reachability workflow can be reused across repeated screening tasks?

## Benchmark families

The Agent benchmark families have distinct roles:

- **DRIFT v2** — supporting model/interface drift diagnosis
- **TRANSFER v1** — supporting reaction-transfer and minimum-sufficient-model selection
- **DISCOVER V1** — frozen formal closed-book decision-allocation benchmark
- **DISCOVER-BOUNDARY-C1** — confirmatory boundary extension on the unchanged DISCOVER V1 protocol
- **DISCOVER V2** — reserved for a future protocol redesign; not a current result

Version labels are family-specific. See [`VERSION_REGISTRY.md`](VERSION_REGISTRY.md).

## DRIFT v2

DRIFT v2 tests whether the decision layer can diagnose model/interface inconsistencies and choose the appropriate response after inspecting evidence. It supports the broader provenance/interface role of the Agent Harness but is not the manuscript's formal decision-allocation benchmark.

## TRANSFER v1

TRANSFER v1 tests reaction transfer through a structured decision chain:

```text
inspect reaction case
 -> record transfer hypothesis
 -> build causal graph
 -> classify REUSE / ADAPT / REBUILD / NOT_NEEDED
 -> propose minimum sufficient model
 -> identify catalyst levers
 -> score next calculations
 -> propose next calculation
```

Its purpose is to avoid automatically rebuilding every upstream layer when the downstream decision requires only a subset of the model.

## DISCOVER V1 environment

DISCOVER V1 exposes 11 fine-grained actions:

1. `INSPECT_CANDIDATES`
2. `COMPUTE_ACTIVITY`
3. `READ_PROPERTY_UNCERTAINTY`
4. `BUILD_PROCESS_WINDOW`
5. `OPTIMIZE_PROCESS`
6. `READ_COST_BREAKDOWN`
7. `RUN_MC`
8. `TEST_LEVER`
9. `BACKWARD`
10. `TEST_REACHABILITY`
11. `CHECK_MODEL_VALIDITY`

Ground truth is hidden from the agent and read only by the scorer. The agent cannot call a single tool that reveals the complete answer.

### Compute units

The frozen cost model defines **1 CU = 1000 MKM state solves**. CU is a scientific-compute budget, not an LLM-token budget.

Representative frozen costs include a full-domain process window of about 111 CU, single-candidate optimization of about 29 CU, a 100-draw MC action of about 17 CU, and low-cost backward/reachability actions that close the decision once the candidate pair is known.

### Primary endpoint

Named catalysts leak domain priors, so the principal closed-book result uses an anonymous candidate permutation.

The frozen primary endpoint is:

`full_decision_correct = winner_correct ∧ pair_decision_correct ∧ reachability_correct`

The economic winner, decision pair and reachability verdict must all be correct. Numerical recovery of the backward parity multiplier is a separate quantitative secondary endpoint.

## DISCOVER V1 cross-model result

Anonymous complete-decision recovery is:

```text
nano        6/35
mini       15/35
strong     35/35
```

This establishes a clear model-capability dependence in executing the full decision chain. The original stronger hypothesis that adaptive policy E would outperform fixed-VOI policy D across model tiers was **not supported** and remains a negative result of the frozen V1 benchmark.

## DISCOVER-BOUNDARY-C1

C1 keeps the DISCOVER V1 task, prompt, 11-action schema, CU accounting, scorer and stopping rule unchanged. It resolves where adaptive decision recovery appears relative to deterministic fixed-VOI policy D.

Policy D reaches the complete decision at **206 CU**.

Boundary cells:

| Tier / policy | 175 CU | 225 CU |
|---|---:|---:|
| strong adaptive | **19/20** | **20/20** |
| mini adaptive | **0/20** | **6/20** |
| nano adaptive | **0/20** | **0/20** |
| fixed-VOI | incomplete | complete |

### Decision recovery and quantitative-target recovery separate

For the strong tier:

- **75 CU** is the lowest tested stable complete-decision budget
- at **50 CU**, complete decisions fall to **13/20**, while winner and decision pair remain correct in 20/20 runs
- **225 CU** is the lowest tested budget with 20/20 recovery of the canonical Ru→Fe backward parity multiplier

The downstream industrial decision can therefore converge before the numerical design target is fully recovered.

### Canonical narrow-window mechanism

A run counts as using narrow-window allocation only when it:

1. builds a process window strictly smaller than the full **14,136-state** domain; and
2. successfully uses that window in a later scoped action.

Under this definition, the strong tier uses narrow-window allocation in:

- **20/20** runs at 50, 75, 100, 125, 150 and 175 CU
- **1/8** at 200 CU
- **0/20** at 225 CU
- **0/9** at 250 CU
- **0/20** under the non-binding 5000-CU allowance

The weaker tiers have no canonical narrow-window use in their measured C1 cells.

This localizes the adaptive mechanism to the below-threshold strong-tier regime.

### Upper cost boundary

The adaptive result is not a universal raw-compute saving. Under the **non-binding 5000-CU allowance**:

- strong completes **20/20** runs
- median decision-stable spend is **566 CU**
- median final spend is **714 CU**
- the median post-stability overrun is **148 CU**
- the most extreme single run spends **3,021 CU**

The scientific decision remains the same. Releasing the budget constraint increases compute consumption, showing that the advantage below 206 CU is decision completion under a binding constraint rather than intrinsic efficiency.

### Model-capability boundary

The weaker tiers do not reproduce the strong-tier regime. At 175 CU, mini and nano are both **0/20**. At 225 CU, mini reaches **6/20** and nano remains **0/20**.

A separate interface intervention improved mini-tier tool validity and winner recovery without moving complete-decision recovery above 0/20 at 175 CU. Additional compute also failed to reproduce the strong-tier below-threshold regime. These results separate model capability from simple interface or budget effects.

## Manuscript claim

The supported Agent statement has two levels:

> **Benchmark result:** under the frozen benchmark, adaptive complete-decision recovery below the fixed-policy completion threshold is model-tier dependent and budget localized.
>
> **Workflow result:** separating deterministic scientific modules from decision-level orchestration turns the framework into a reusable execution pattern for repeated and batch screening tasks. Scientific truth remains in the reaction-specific tools.

This wording separates three quantities that should not be conflated:

- **decision completion** — whether the correct winner, pair and reachability verdict are recovered
- **quantitative-target recovery** — whether the canonical backward parity multiplier is numerically recovered
- **compute consumption** — decision-stable and final CU spend

## Figure and Extended Data mapping

**Source F10 — Agent capability-bounded operating envelope**

- Panel A: complete-decision recovery versus CU budget
- Panel B: canonical narrow-window allocation
- Panel C: decision-stable versus final spend and the non-binding allowance control

Canonical panel data: `../data/agent_figure_panel_data_2026-09-13.csv`  
Final caption: `../figures/agent/F10_CAPTION.md`

Extended Data:

- **ED1** — mini interface intervention
- **ED2** — failure mechanism by tier and budget
- **ED3** — per-run non-binding-allowance spread

## Evidence hierarchy

For manuscript-level Agent claims, use evidence in this order:

1. frozen DISCOVER V1 protocol hashes and source harness
2. raw/scored traces and C1 ledger records
3. current machine-readable summary tables, especially `../data/agent_figure_panel_data_2026-09-13.csv`
4. F10 / Extended Data renderers and captions
5. manuscript-facing summaries

The full frozen evidence bundle is under `../provenance/discover_v1/`.

## Production state

DISCOVER V1 remains frozen. DISCOVER-BOUNDARY-C1 is complete. The current manuscript uses these frozen results to support the Agent as the workflow-scaling layer; the publication-facing composite Figure 6 combines the locked F10 source asset with the 22-CU oracle framing. Current work is manuscript integration, composite-figure assembly and Supporting Information packaging rather than additional benchmark tuning.

Superseded intermediate claims and corrected definitions are centralized in [`RETIRED_RESULTS.md`](RETIRED_RESULTS.md).
