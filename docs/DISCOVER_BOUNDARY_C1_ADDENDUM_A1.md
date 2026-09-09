# DISCOVER-BOUNDARY-C1 — addendum A1 (design reduction, 2026-09-09)

**Decision (user, cost-motivated, taken during the batch before any C1 result had been scored or inspected):**
stop the 150, 200 and 250 CU strong-model processes; continue 175 and 225 CU to the pre-registered 20 runs each.

Counts at the moment of the stop (runs with a complete trace):

| budget | completed / planned | status after A1 |
|---|---|---|
| 150 | 7 / 20 | stopped; reduced-n exploratory endpoint |
| 175 | 6 / 20 → continues to 20 | confirmatory |
| 200 | 8 / 20 | stopped; reduced-n; V1's five historical runs remain a separate series and are not pooled |
| 225 | 10 / 20 → continues to 20 | confirmatory |
| 250 | 9 / 20 | stopped; reduced-n exploratory endpoint |

Consequences, stated in advance:
- The pre-registered REPLICATED-200 threshold (k ≥ 14/20) cannot be evaluated as written; the 200-CU cell is reported as
  k/8 with its Wilson interval and labelled reduced-n. The teacher's core question (does the 200-CU advantage survive
  higher n) is answered with n = 8 new runs, not 20, and the report says so.
- The COHERENT LOCAL REGION / ISOLATED SPIKE classification is evaluated on 175 / 200 / 225 (adjacent-budget criterion),
  with 150 and 250 shown as reduced-n endpoints.
- Every completed trace is kept and scored; any directory interrupted mid-run (no `trace.json`) is listed in the
  metadata as interrupted and excluded from all counts. No completed run is discarded.
- Nothing else in the pre-registration changes (endpoints, D reference, scorer, sampling protocol, integrity rules).
