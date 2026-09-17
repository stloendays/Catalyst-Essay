# SI 5. Numerical agreement of the recovered break-even multiplier

This section records the per-run audit of the Ru→Fe break-even multiplier recovered by the agent in the
non-binding-allowance control cell, and states the exact sense in which the recovered value agrees with the frozen
reference. It supports the audit sentence in §3.7 of `MANUSCRIPT_SKELETON_v4_2026-09-14.md` (frozen) and the envelope
statement in §4.6 (frozen); neither is restated here.

Cell: strong `gpt-5.5-2026-04-23`, frozen policy E, **non-binding 5000-CU allowance**, tag `c1uncapped`, n = 20. The
audit is a read-only replay of the existing traces — no model call, no recomputation of any scientific value, no
modification of any frozen file. Generator: `tools/discover/c1_uncapped_breakeven_audit.py`; data:
`data/discover_boundary_c1_uncapped_breakeven_audit.csv`.

## 5.1 Frozen reference

| quantity | frozen value |
|---|---|
| economic winner | `Fe` |
| decision pair (atomic best, winner) | `(Ru, Fe)` |
| Ru→Fe break-even / parity multiplier | 201.2234429878984 |
| reachability verdict | `unreachable` |
| scaling headroom across process states | 2.5245651130943445 |

## 5.2 Per-run audit

Every run returns the frozen winner, the frozen reachability verdict, the canonical break-even multiplier on its single
decision-pair `BACKWARD`, and the across-states headroom. All 20 runs stopped on their own rule; none reached
`MAX_TURNS = 60`.

| run | steps | winner | scored break-even | rel. error | reachability | headroom | remaining allowance at stop (CU) |
|---|---|---|---|---|---|---|---|
| 0 | 16 | Fe | 201.2234429878986 | 9.89e-16 | unreachable | 2.5246 | 4782 |
| 1 | 17 | Fe | 201.2234429878986 | 9.89e-16 | unreachable | 2.5246 | 4634 |
| 2 | 29 | Fe | 201.2234429878986 | 9.89e-16 | unreachable | 2.5246 | 3943 |
| 3 | 29 | Fe | 201.2234429878986 | 9.89e-16 | unreachable | 2.5246 | 1979 |
| 4 | 29 | Fe | 201.2234429878986 | 9.89e-16 | unreachable | 2.5246 | 4286 |
| 5 | 15 | Fe | 201.2234429878986 | 9.89e-16 | unreachable | 2.5246 | 4782 |
| 6 | 30 | Fe | 201.2234429878986 | 9.89e-16 | unreachable | 2.5246 | 3206 |
| 7 | 29 | Fe | 201.2234429878986 | 9.89e-16 | unreachable | 2.5246 | 3697 |
| 8 | 29 | Fe | 201.2234429878986 | 9.89e-16 | unreachable | 2.5246 | 4286 |
| 9 | 29 | Fe | 201.2234429878986 | 9.89e-16 | unreachable | 2.5246 | 4286 |
| 10 | 14 | Fe | 201.2234429878986 | 9.89e-16 | unreachable | 2.5246 | 4634 |
| 11 | 16 | Fe | 201.2234429878986 | 9.89e-16 | unreachable | 2.5246 | 4291 |
| 12 | 17 | Fe | 201.2234429878986 | 9.89e-16 | unreachable | 2.5246 | 4143 |
| 13 | 29 | Fe | 201.2234429878986 | 9.89e-16 | unreachable | 2.5246 | 4286 |
| 14 | 29 | Fe | 201.2234429878986 | 9.89e-16 | unreachable | 2.5246 | 4286 |
| 15 | 28 | Fe | 201.2234429878986 | 9.89e-16 | unreachable | 2.5246 | 4286 |
| 16 | 30 | Fe | 201.2234429878986 | 9.89e-16 | unreachable | 2.5246 | 3893 |
| 17 | 28 | Fe | 201.2234429878986 | 9.89e-16 | unreachable | 2.5246 | 3697 |
| 18 | 16 | Fe | 201.2234429878986 | 9.89e-16 | unreachable | 2.5246 | 4634 |
| 19 | 28 | Fe | 201.2234429878986 | 9.89e-16 | unreachable | 2.5246 | 4434 |

Aggregate verdicts:

| check | result |
|---|---|
| scored winner == frozen `Fe` | 20/20 |
| scored reachability == frozen `unreachable` | 20/20 |
| scored break-even == canonical 201.2234429878984 | 20/20 |
| any decision-pair `BACKWARD` canonical | 20/20 |
| scored break-even == first decision-pair record (frozen convention holds) | 20/20 |
| headroom returned by the environment | 2.5246 in 20/20 |
| fields not establishable from the raw trace | 0 |

Nothing needed for the audit was missing. The scorer-only `identity_mapping.json`, every `BACKWARD` result with its
multiplier, window id and parity state, every `TEST_REACHABILITY` result with its classification, required multiplier
and max-gain value, the per-step `remaining_budget`, and the frozen `final.answer` block were present and used in all
20 runs; the `NOT_IN_TRACE` sentinel was emitted zero times. No audited quantity is inferred or reconstructed.

## 5.3 Binary comparison against the frozen reference

A genuine binary comparison was run rather than a printed-decimal comparison.

| | value |
|---|---|
| frozen `GT["break_even"]` | 201.2234429878984, IEEE-754 bits `4069272671e8b16a` |
| value in every trace of this cell | 201.2234429878986, IEEE-754 bits `4069272671e8b171` |
| bitwise identical | 0/20 runs |
| absolute difference | 1.9895 × 10⁻¹³ |
| relative difference | 9.8871 × 10⁻¹⁶ |
| difference in units in the last place | exactly 7.00 ULP |

The required wording is therefore: *numerically identical within floating-point round-off (relative difference
9.89 × 10⁻¹⁶, 7 ULP)*. Permitted alternatives are "agrees to 15 significant figures" and "identical to within
double-precision round-off". The terms "bit-exact", "bit-identical" and "exactly equal" must not be used for this
agreement; the "bit-exact agreement" claim in Addendum A6 §2 is withdrawn.

The 7-ULP offset is a round-trip artefact of writing the value to JSON and re-reading it, not a numerical discrepancy
in the model, and carries no scientific interpretation. The canonical-value test accepts a relative tolerance of
1 × 10⁻⁶, so the observed 9.89 × 10⁻¹⁶ agreement is far tighter than the test requires and no scored conclusion —
winner, decision pair, break-even or reachability verdict — is affected.

## 5.4 One decision-pair `BACKWARD` per run, in the full window

Every run in this cell executed exactly one decision-pair `BACKWARD` and exactly one classified `TEST_REACHABILITY`,
and in all 20 runs the `BACKWARD` was taken in the full 14,136-state window. This is the cleanest available control on
the first-record effect documented in Addenda A4 and A5: at low budgets the scored break-even falls to 9–11 of 20
because the agent's *first* decision-pair `BACKWARD` is often taken in a preliminary window that does not yet contain
the parity state (T 425 °C, P 190 bar, T_sep 30 °C). When the allowance does not bind, the agent affords the full
window immediately and computes the canonical multiplier on its first and only attempt, so there is no premature record
to discard. The premature-first-record pathology is thus budget-induced: it belongs to the constrained regime, not to
the policy or to the scoring convention alone.

The same audit bounds what the extra compute buys in this cell. Accuracy is already complete at 218 CU of
decision-stable spend — the minimum first-stable value of the non-binding cell, reached by 6 of its 20 runs, and a
different statistic from the 225 CU cell median that happens to share the value — so the additional median 148 CU, and
the 2,455 CU of the most extreme run, purchase no change in the winner, the decision pair, the break-even multiplier or
the reachability verdict.

## 5.5 Headroom limitation

Every classified `TEST_REACHABILITY` in this cell used `scope: "window"` and therefore returned
`max_gain_across_process_states` = 2.5246; that is the only headroom value present in these traces, and
`DISCOVER_SCORER_V1.GT["headroom"]` likewise stores only the across-states value (2.5245651130943445). The
reference-condition headroom 1.0899 is the `scope: "reference"` quantity, is absent from this cell, and must not be
attributed to it; its evidence is the 175 CU cell and the frozen NH3-FINAL-1.1 consistency record.

---

Metric definitions and aggregations follow `docs/AGENT_METRIC_DEFINITIONS_SOURCE_OF_TRUTH_2026-09-13.md`, which is
authoritative wherever Addendum A6 disagrees with it.
