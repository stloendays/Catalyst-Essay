# DISCOVER-BOUNDARY-C1 — manuscript claim summary

Snapshot: **2026-09-10**

Use this page as the compact manuscript-facing interpretation of the C1 confirmatory extension. It does not replace the preregistration, raw traces, scorer outputs or full Phase A / Phase B reports.

## Core result

The deterministic fixed-VOI policy D reaches the complete scientific decision at **206 CU**. Under the identical frozen DISCOVER V1 protocol, adaptive policy E shows a strong-tier recovery regime below this threshold but the same regime does not transfer to the two tested weaker tiers.

| tier / policy | 175 CU | 225 CU |
|---|---:|---:|
| strong E | **19/20** | **20/20** |
| mini E | **0/20** | **6/20** |
| nano E | **0/20** | **0/20** |
| fixed-VOI D | incomplete | complete |

At 175 CU, narrow-window construction occurs in **20/20** strong runs, **4/20** mini runs and **0/20** nano runs. This provides trace-level evidence that the strong-tier advantage is associated with identifying and exploiting a smaller, decision-relevant process window rather than with receiving more scientific-compute budget.

At budgets where D already resolves the decision, strong E is not a universal compute-saving strategy: C1 strong runs reach full decision at roughly **218-221 CU**, whereas D reaches it at **206 CU**.

## Manuscript-safe interpretation

> Under the frozen benchmark protocol, the adaptive decision-recovery advantage below the fixed policy's completion threshold is model-tier dependent. The strong model exploits a narrow-window allocation strategy that does not transfer to the two tested weaker tiers. The benefit is therefore a localized decision-completion advantage under constrained scientific compute, not a universal raw-compute saving.

Report **policy advantage**, **model capability** and **raw compute efficiency** as separate quantities.

## Evidence boundary

- DISCOVER V1 remains the frozen canonical benchmark.
- DISCOVER-BOUNDARY-C1 is a confirmatory extension on the unchanged V1 protocol; it is not DISCOVER V2.
- Phase B provides weak-tier estimates only at **175 and 225 CU**.
- The Phase B reduction from the originally registered five budgets, and the removal of smoke runs, were operationally chosen before the first Phase B API call for cost control but remain a deviation from the original preregistration; see `DISCOVER_BOUNDARY_C1_ADDENDUM_A2.md`.
- No claim should be made about weak-tier response shape at 150, 200 or 250 CU from C1 Phase B.
