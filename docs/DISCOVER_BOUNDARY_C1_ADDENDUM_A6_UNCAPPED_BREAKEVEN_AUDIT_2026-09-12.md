# DISCOVER-BOUNDARY-C1 Addendum A6 — exact break-even / reachability audit of the non-binding-allowance cell (2026-09-12)

Per-run audit of all 20 strong runs at the **non-binding 5000-CU allowance**. Read-only replay of the existing traces:
no model was called, no frozen file was modified, no scientific value was recomputed. Every audited quantity is taken
from the trace and compared against the frozen reference in `DISCOVER_SCORER_V1.GT`.

Generator: `tools/discover/c1_uncapped_breakeven_audit.py`.
Data: `data/discover_boundary_c1_uncapped_breakeven_audit.csv`, `..._metadata.json`.

## 1. Frozen reference

| quantity | frozen value |
|---|---|
| economic winner | `Fe` |
| decision pair (atomic best, winner) | `(Ru, Fe)` |
| Ru→Fe break-even / parity multiplier | **201.2234429878984** |
| reachability verdict | **`unreachable`** |
| scaling headroom across process states | **2.5245651130943445** |

## 2. Result: the audit passes on every run, with no missing fields

| check | result |
|---|---|
| scored winner == frozen `Fe` | **20/20** |
| scored reachability == frozen `unreachable` | **20/20** |
| scored break-even == canonical 201.2234429878984 | **20/20** |
| any decision-pair `BACKWARD` canonical | **20/20** |
| scored break-even == first decision-pair record (frozen convention holds) | **20/20** |
| headroom returned by the environment | **2.5246 in 20/20**, matching the frozen 2.52456511… |
| fields not establishable from the raw trace | **0** |

The maximum relative error of the scored break-even against the frozen reference is **9.89 × 10⁻¹⁶** in every run — the
float round-trip of writing and re-reading the trace, i.e. bit-exact agreement, not an approximation.

## 3. Per-run record

`stable` = ledger-true first-stable CU (`budget_CU − remaining_budget` at the first step from which the full decision
stays correct to the end). `final` = `spent_CU` at stop. `over` = final − stable.

| run | steps | winner | scored break-even | rel. error | reachability | stable CU | final CU | overrun CU |
|---|---|---|---|---|---|---|---|---|
| 0 | 16 | Fe | 201.223443 | 9.89e-16 | unreachable | 218 | 218 | 0 |
| 1 | 17 | Fe | 201.223443 | 9.89e-16 | unreachable | 218 | 366 | 148 |
| 2 | 29 | Fe | 201.223443 | 9.89e-16 | unreachable | 566 | 1057 | 491 |
| 3 | 29 | Fe | 201.223443 | 9.89e-16 | unreachable | 566 | 3021 | 2455 |
| 4 | 29 | Fe | 201.223443 | 9.89e-16 | unreachable | 566 | 714 | 148 |
| 5 | 15 | Fe | 201.223443 | 9.89e-16 | unreachable | 218 | 218 | 0 |
| 6 | 30 | Fe | 201.223443 | 9.89e-16 | unreachable | 566 | 1794 | 1228 |
| 7 | 29 | Fe | 201.223443 | 9.89e-16 | unreachable | 566 | 1303 | 737 |
| 8 | 29 | Fe | 201.223443 | 9.89e-16 | unreachable | 714 | 714 | 0 |
| 9 | 29 | Fe | 201.223443 | 9.89e-16 | unreachable | 566 | 714 | 148 |
| 10 | 14 | Fe | 201.223443 | 9.89e-16 | unreachable | 366 | 366 | 0 |
| 11 | 16 | Fe | 201.223443 | 9.89e-16 | unreachable | 218 | 709 | 491 |
| 12 | 17 | Fe | 201.223443 | 9.89e-16 | unreachable | 218 | 857 | 639 |
| 13 | 29 | Fe | 201.223443 | 9.89e-16 | unreachable | 566 | 714 | 148 |
| 14 | 29 | Fe | 201.223443 | 9.89e-16 | unreachable | 714 | 714 | 0 |
| 15 | 28 | Fe | 201.223443 | 9.89e-16 | unreachable | 566 | 714 | 148 |
| 16 | 30 | Fe | 201.223443 | 9.89e-16 | unreachable | 566 | 1107 | 541 |
| 17 | 28 | Fe | 201.223443 | 9.89e-16 | unreachable | 566 | 1303 | 737 |
| 18 | 16 | Fe | 201.223443 | 9.89e-16 | unreachable | 218 | 366 | 148 |
| 19 | 28 | Fe | 201.223443 | 9.89e-16 | unreachable | 566 | 566 | 0 |

Medians: stable **566 CU**, final **714 CU**, overrun **148 CU** (33.3% of spend). All 20 runs stopped on their own
rule; none reached the `MAX_TURNS = 60` cap; remaining allowance at stop ranged from 1979 to 4782 CU, so the allowance
never bound.

## 4. The premature-first-record pathology is itself budget-induced

Every run in this cell executed **exactly one** decision-pair `BACKWARD` and **exactly one** classified
`TEST_REACHABILITY`, and the `BACKWARD` was taken in the **full 14,136-state window** in all 20 runs.

This is the cleanest available control on the first-record effect documented in Addenda A4 and A5. At low budgets the
scored break-even falls to 9–11 of 20 because the agent's *first* decision-pair `BACKWARD` is often taken in a
preliminary window that does not yet contain the parity state (T 425 °C, P 190 bar, T_sep 30 °C). When the allowance
does not bind, the agent affords the full window immediately, computes the canonical multiplier on its first and only
attempt, and there is no premature record to discard. The pathology therefore belongs to the constrained regime, not to
the policy or to the scoring convention alone.

It also isolates what the extra compute in this cell does **not** buy: accuracy is already perfect at 218 CU of
decision-stable spend, so the additional median 148 CU — and the 2455 CU of the most extreme run — purchases no
improvement in the winner, the decision pair, the break-even value or the reachability verdict.

## 5. Completeness statement

Nothing required for this audit was missing from the raw traces. Specifically, all of the following were present and
used for every one of the 20 runs: the scorer-only `identity_mapping.json`; every `BACKWARD` result with its
multiplier, window id and parity state; every `TEST_REACHABILITY` result with its classification, required multiplier
and max-gain value; per-step `remaining_budget`; and the frozen `final.answer` block. The audit therefore rests on
direct trace evidence with **no inferred or reconstructed quantity**, and the `NOT_IN_TRACE` sentinel was emitted zero
times.

One limitation is recorded rather than worked around: the reference-condition headroom of **1.0899** does not appear in
this cell, because every classified `TEST_REACHABILITY` here used `scope: "window"` and therefore returned
`max_gain_across_process_states` (2.5246). The 1.0899 value is the `scope: "reference"` quantity and is evidenced in
the 175 CU cell and in the frozen NH3-FINAL-1.1 record, not here. `DISCOVER_SCORER_V1.GT["headroom"]` likewise holds
only the across-states value, so the 1.0899 anchor cannot be verified against `GT` from this cell's traces.
