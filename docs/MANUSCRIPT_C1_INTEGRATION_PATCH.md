# Manuscript integration patch — DISCOVER-BOUNDARY-C1

Date: **2026-09-10**.

Purpose: replace the stale DISCOVER-V1-only interpretation in `docs/MANUSCRIPT_SKELETON.md` without altering the frozen scientific results. This file is an exact content patch for the Agent Results/Methods language. It exists separately first so the original skeleton is not accidentally truncated by a broad file rewrite during the audit.

## Replace Results §3.7 with

### 3.7 Decision-aware computation allocation is bounded by model capability and the fixed-policy completion threshold

DISCOVER V1 evaluates whether an AI agent can allocate limited scientific compute to the parts of the multiscale chain that determine the final industrial decision. The protocol was frozen before the cross-model evaluation: the task, prompt, 11-action schema, CU cost model, scorer, stopping rule and A–D baselines were unchanged across model tiers. On the anonymous closed-book task, complete-decision recovery was **6/35** for nano, **15/35** for mini and **35/35** for the strong model, with a pooled tier trend of **Z = 6.95**. A complete decision requires recovery of the economic winner, decision pair, backward target and reachability verdict. The original pre-registered hypothesis that adaptive policy E would robustly outperform fixed-VOI policy D across tiers was not supported.

The subsequent **DISCOVER-BOUNDARY-C1** extension keeps the same frozen DISCOVER V1 scientific environment and resolves the local budget boundary rather than redesigning the protocol. Deterministic fixed-VOI policy D reaches the complete decision at **206 CU**. Below that threshold, at **175 CU**, policy E completes the decision in **19/20** strong-model runs but **0/20** mini and **0/20** nano runs. At **225 CU**, where D can already complete, E succeeds in **20/20** strong, **6/20** mini and **0/20** nano runs.

The step-level traces identify a behavioral distinction at the below-threshold cell. At 175 CU, a narrow process-window construction is used in **20/20** strong-model runs, compared with **4/20** mini and **0/20** nano runs. The strong model can therefore redirect enough of the finite scientific-compute budget from broad process enumeration toward the backward-design and reachability chain; the two tested weaker tiers do not reliably recover the same allocation behavior.

This does not imply a universal compute-efficiency advantage. At 225 CU, where policy D itself reaches the full decision at 206 CU, the strong adaptive policy reaches the full decision at a median of approximately **218 CU**. C1 therefore supports a **model-tier-dependent, budget-localized decision-recovery advantage below the fixed policy's completion threshold**, not universal adaptive superiority or universal raw-compute saving.

Phase B was executed as a cost-motivated reduced extension at the two discriminative cells, 175 and 225 CU, with **80/80 formal runs**, **0 smoke runs**, **0 infrastructure retries**, **0 driver exceptions**, and frozen hashes **15/15 PASS** before and after. The reduction from the originally registered five-budget Phase B and the no-smoke decision were made before the first Phase B API call and are recorded transparently in `DISCOVER_BOUNDARY_C1_ADDENDUM_A2.md`; they must not be described as the original preregistered design.

Primary evidence: `CROSS_MODEL_DISCOVER_V1.md`, `CROSS_MODEL_STATS_V1.md`, `DISCOVER_BOUNDARY_C1_RESULTS.md`, `DISCOVER_BOUNDARY_C1_PHASE_B_RESULTS.md`, C1 summary tables, frozen hashes and scored traces.

## Replace Discussion §4.6 with

### 4.6 Agent claims should separate execution capability, boundary recovery and compute efficiency

The cross-model benchmark separates three questions that are easy to conflate. First, complete execution of the multistep scientific decision chain is strongly model-capability dependent. Second, the C1 boundary extension shows that a strong model can recover the full decision below the deterministic fixed-VOI completion threshold by narrowing the process search and reallocating compute toward the unresolved backward/reachability steps. Third, once the deterministic policy has enough budget to complete the same decision, the adaptive policy does not provide a universal raw-compute saving. Agent performance should therefore be reported as a decision-recovery boundary conditioned on model capability and budget, rather than as a general claim that adaptive LLM allocation is always more efficient than a deterministic VOI policy.

## Replace Methods item 13 with

13. Decision-aware AI harness, frozen DISCOVER V1 cross-model benchmark, and DISCOVER-BOUNDARY-C1 confirmatory boundary extension. Report the unchanged 11-action scientific interface, CU accounting, anonymous task, fixed scorer/stopping rule, deterministic D reference, per-tier repeated sampling, step-level `CU_to_full_decision` reconstruction, narrow-window behavior, before/after frozen-hash checks, and the Phase-B design reduction recorded in addendum A2.

## Abstract / Introduction integration rule

Do not turn C1 into a new physical-science result. The abstract may state only that the decision-aware harness reveals a model-capability-dependent ability to resolve the multiscale decision under finite compute. If a numerical Agent result is included, the most informative compact form is the fixed-policy threshold plus one below-threshold contrast (**D threshold 206 CU; strong E 19/20 at 175 CU, mini/nano 0/20**) rather than the full benchmark matrix.

## Figure rule

C1 does not create a tenth main scientific figure in the current architecture. The existing C1 figures remain supporting / Extended Data evidence unless the manuscript is later restructured around the Agent contribution.
