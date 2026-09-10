# DISCOVER-BOUNDARY-C1 — addendum A2 (Phase B design reduction audit, 2026-09-10)

Family: **DISCOVER V1 Boundary Confirmatory Extension C1** (`DISCOVER-BOUNDARY-C1`).

## Status of this note

This note is added **after Phase B completion** to make the repository record match the experiment that was actually run. It is therefore an audit addendum, not a claim of prospective preregistration.

The operational decision itself was issued before the first Phase B API call: for cost control, Phase B was reduced to the two discriminative boundary cells, **175 CU** and **225 CU**, with **20 independent formal runs per model per budget** for `gpt-5.4-mini-2026-03-17` and `gpt-5.4-nano-2026-03-17`. No Phase B result existed when that operational reduction was chosen.

## Deviation from the original C1 preregistration

The original `DISCOVER_BOUNDARY_C1_PREREGISTRATION.md` stated that conditional Phase B would use the same five budgets as Phase A (150, 175, 200, 225, 250 CU) and would include a smoke run before formal sampling.

The executed Phase B instead used:

| model | 175 CU | 225 CU | other budgets | smoke |
|---|---:|---:|---|---|
| `gpt-5.4-mini-2026-03-17` | 20 formal | 20 formal | not run | 0 |
| `gpt-5.4-nano-2026-03-17` | 20 formal | 20 formal | not run | 0 |

Total: **80 formal runs, 0 smoke runs**.

The rationale for choosing these two cells was fixed before Phase B execution:

- **175 CU** is below the deterministic fixed-VOI policy D completion threshold (206 CU) and directly tests whether the strong-tier recovery regime transfers to weaker tiers.
- **225 CU** is above that threshold and is the control region where D completes, testing whether weaker models can execute the same adaptive policy when the scientific-compute budget itself is sufficient.

The no-smoke decision was made because the identical frozen driver, scorer and tool interface had already been exercised by the completed strong-model C1 runs; the user explicitly instructed that no additional API smoke calls be made.

## What did not change

No scientific or scoring rule was altered for Phase B. The following remained identical to the frozen protocol:

- task and anonymous mapping;
- prompt;
- 11 tools + STOP interface;
- CU cost model;
- policy E semantics;
- deterministic D reference;
- scorer and definition of `full_decision_correct`;
- stopping rule and API retry policy;
- ground truth and frozen files.

Frozen-hash checks were **15/15 PASS before and after Phase B**. There were **0 infrastructure retries** and **0 driver exceptions**.

## Consequences for interpretation

1. Phase B provides confirmatory estimates only at **175 CU** and **225 CU** for the two weaker model tiers.
2. No weak-tier estimate is claimed for 150, 200 or 250 CU in this extension.
3. The original C1 preregistration and Phase A addendum A1 remain unchanged and are retained as provenance.
4. Manuscript text must describe Phase B as a **cost-motivated reduced two-budget extension**, not as the originally planned five-budget Phase B.
5. The observed results must not be pooled with unexecuted cells or presented as evidence for the shape of the weak-tier response outside 175/225 CU.

Primary result report: `DISCOVER_BOUNDARY_C1_PHASE_B_RESULTS.md`.
