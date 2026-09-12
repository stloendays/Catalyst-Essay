# Adaptive compute allocation has a capability-bounded operating envelope

**Version note — 2026-09-12.** This is a new Results framing. It does **not** replace or overwrite `DISCOVER_BOUNDARY_C1_ADDENDUM_A5_2026-09-11.md`; the earlier document remains the frozen execution record.

## What changed in the scientific claim

The Agent result is no longer adequately summarized as “the strong model can complete the decision below the fixed-policy compute threshold.” The stronger result is a three-part operating-envelope characterization:

1. **Advantage inside the envelope.** Under the frozen protocol, the strong model first reaches stable end-to-end completion at 75 CU (20/20), versus the fixed-VOI policy-D threshold of 206 CU. This is 36.4% of D’s threshold; median decision-stable spend at 75 CU is 52 CU.
2. **Boundary 1 — no intrinsic stopping efficiency.** With a non-binding 5000-CU allowance, the same strong policy still completes 20/20 decisions, but self-terminates after a median 714 CU (range 218–3021), about 3.5× D’s 206-CU threshold. Median decision stability is reached at 566 CU, followed by a median 148 CU of additional spend. All 20 runs self-stop; none hits the 5000-CU budget or the 60-turn limit.
3. **Boundary 2 — capability dependence.** The operating regime does not transfer to the mini model. A targeted interface intervention removes the measured interface failure mode, but does not recover end-to-end completion at 175 CU; increasing compute to 225–400 CU also fails to move mini into the strong model’s regime.

Together, these are the Result: **adaptive compute allocation has a capability-bounded operating envelope.** The contribution is not a generic claim that “agents save compute.” It is a characterization of when adaptive allocation works, when it over-computes, and when scaffolding cannot substitute for model capability.

## Three checks required before manuscript wording

### 1. Did extra compute change break-even or reachability?

**Reachability and the complete downstream decision are verified as unchanged/correct in the non-binding-budget runs.** The 20/20 `full_decision_correct` result includes winner correctness, decision-pair ordering, and reachability.

**Exact break-even/parity multiplier is not yet independently audited in the committed uncapped summary.** The current `full_decision_correct` predicate does not require exact parity-multiplier equality. Therefore the manuscript can currently say:

> Additional compute did not change the winner, decision-pair ordering, or reachability conclusion.

Do **not** yet write “the exact break-even point was unchanged” or “the extra compute bought literally nothing” until the uncapped raw traces are explicitly audited for the canonical break-even value.

### 2. Was 3.5× caused by a hard cap?

No. The 5000-CU allowance is non-binding: maximum observed final spend is 3021 CU. `MAX_TURNS=60` is the only remaining hard turn limit, and no run reaches it. All 20 runs terminate by `self_stop`.

This supports the stronger interpretation that the excess spend is a stopping-policy property, not budget exhaustion.

The literal word **“unlimited”** has not been verified in the currently committed prompt artifacts. Use **“non-binding 5000-CU allowance”** or **“effectively uncapped condition”** in the paper rather than claiming the prompt said “unlimited.”

### 3. Did the mini intervention reduce errors but remain unsuccessful?

The precise answer is more informative than a simple yes/no.

At 175 CU, baseline mini → interface intervention E2:

- complete decision: 0/20 → 0/20
- correct winner: 14/20 → 19/20
- interface errors: 18 → 0
- no-tool-call turns: 16 → 4
- BACKWARD execution: 0/20 → 0/20
- budget errors: 36 → 51
- premature `OPTIMIZE`: 13 → 67

Thus the targeted interface failure is eliminated and local task performance improves, yet end-to-end decision recovery does not improve. The remaining failure mass shifts to budget allocation and sequencing/planning. It would be inaccurate to say that *overall* errors simply decreased.

The independent compute intervention gives the second piece of evidence: mini complete-decision rates are 6/20 at 225 CU, 4/20 at 300 CU, and 7/20 at 400 CU, while BACKWARD execution is flat at 7/20 across all three budgets. More compute therefore gives no monotonic rescue and remains far below strong at 175 CU (19/20).

The supported claim is:

> Removing interface friction and increasing budget are both insufficient to move the weaker model into the strong model’s operating regime; the residual bottleneck is capability-dependent planning and compute allocation.

Do **not** write “both interventions remained 0/20”: that is true for the interface intervention at 175 CU, but false for the higher-budget mini sweep.

## Paper-ready Results framing

### Proposed subsection title

**Adaptive compute allocation has a capability-bounded operating envelope**

### Draft paragraph

Adaptive allocation exhibited a bounded rather than universal advantage. Under the frozen protocol, the strong model first achieved stable end-to-end completion at 75 CU (20/20), only 36.4% of the 206-CU threshold required by fixed-VOI policy D. Yet this advantage did not imply self-regulating compute use. With a non-binding 5000-CU allowance, the same strong policy still completed all 20 decisions, but self-terminated after a median 714 CU—3.5× D’s threshold—and spent a median 148 CU after the decision had already become stable. Nor did the regime transfer to the mini model. Eliminating its measured interface failure mode reduced interface errors from 18 to 0 and improved winner identification from 14/20 to 19/20, but complete decisions and BACKWARD execution remained 0/20 at 175 CU; increasing the budget to 225–400 CU produced only 4–7/20 complete decisions and a flat 7/20 BACKWARD rate. Together, these results define a capability-bounded operating envelope for adaptive compute allocation rather than a universal compute-efficiency advantage.

Until the exact uncapped parity multiplier is audited, “unchanged decision” in this paragraph refers to winner, decision-pair ordering, and reachability, not exact break-even equality.

## Connection to the manuscript’s main scientific line

The Agent result now uses the same logic as the catalyst result:

- the catalyst line asks **when atomic ranking survives multiscale propagation and when it inverts**;
- the Agent line asks **when adaptive allocation outperforms a fixed policy and where that advantage ceases to hold**.

Both contributions are therefore conditional-envelope characterizations rather than universal superiority claims. This is consistent with the project’s original problem-first framing: AI is valuable at scientific decision interfaces and for decision-aware compute allocation only insofar as those choices improve the downstream industrial decision.

## Wording to avoid in the manuscript

- “universal compute saving”
- “LLM agents efficiently allocate compute” as a general claim
- “unlimited budget” unless the literal frozen prompt is verified
- “the two mini interventions both stayed at 0/20”
- “overall mini errors decreased”
- “the exact break-even point was unchanged” before the explicit uncapped parity audit

## One remaining audit before hardening the Results text

Extract the canonical break-even/parity multiplier from every uncapped raw trace and compare it with the frozen reference decision, alongside reachability. A small dedicated artifact such as `data/discover_boundary_c1_uncapped_decision_invariance.csv` should record, per run, the canonical break-even value, reachability result, first-stable step, and final spend. Once exact parity invariance is confirmed, the Result can be strengthened from “extra compute did not change the complete decision” to “extra compute did not change the decision boundary or reachability result.”

---

## Audit resolution — 2026-09-12 (appended; nothing above is modified)

The "one remaining audit before hardening the Results text" is **done and passed**. Record:
`DISCOVER_BOUNDARY_C1_ADDENDUM_A6_UNCAPPED_BREAKEVEN_AUDIT_2026-09-12.md`; generator
`tools/discover/c1_uncapped_breakeven_audit.py`; per-run artefact
`data/discover_boundary_c1_uncapped_breakeven_audit.csv` (this is the file proposed above as
`discover_boundary_c1_uncapped_decision_invariance.csv`, under a different name; it carries the specified columns —
canonical break-even value, reachability result, first-stable CU and final spend, per run).

All 20 non-binding-allowance runs were audited against the frozen reference in `DISCOVER_SCORER_V1.GT`:

| check | result |
|---|---|
| scored winner == frozen `Fe` | 20/20 |
| scored reachability == frozen `unreachable` | 20/20 |
| scored break-even == canonical **201.2234429878984** | **20/20** |
| max relative error vs the frozen value | **9.89 × 10⁻¹⁶** (float round-trip, i.e. bit-exact) |
| headroom returned == frozen 2.5246 | 20/20 |
| fields not establishable from the raw traces | **0** |

**Two gates in the list above are therefore discharged.** The Results text may now state that additional compute left
the **decision boundary** unchanged, not merely the winner, decision-pair ordering and reachability: the exact parity
multiplier is bit-exact canonical in every run. The wording "the exact break-even point was unchanged" is now
supported. The other avoid-items stand unchanged.

Two findings the audit added beyond pass/fail:

- **the premature-first-record pathology is budget-induced.** Every run in this cell executed exactly one decision-pair
  `BACKWARD`, in the full 14,136-state window. At constrained budgets the scored break-even falls to 9–11/20 because the
  agent's *first* decision-pair `BACKWARD` is often taken in a preliminary window lacking the parity state; with a
  non-binding allowance it affords the full window immediately and there is no premature record to discard;
- **the excess compute buys nothing measurable.** Accuracy is already complete at 218 CU of decision-stable spend, so
  the additional median 148 CU — and the 2455 CU of the most extreme run — improves no scored component.

One limitation is recorded rather than worked around: the **reference-condition headroom 1.0899** does not appear in this
cell, because every classified `TEST_REACHABILITY` here used `scope: "window"` and returned
`max_gain_across_process_states` (2.5246). `GT["headroom"]` likewise holds only the across-states value, so the 1.0899
anchor cannot be verified against `GT` from these traces; it is evidenced in the 175 CU cell and the frozen
NH3-FINAL-1.1 record.

The Results and Discussion rewrite built on this framing is `MANUSCRIPT_SKELETON_v2_2026-09-12.md` (§3.7 at 6 paragraphs
/ 706 words, §4.6 retitled to this document's proposed title). `MANUSCRIPT_SKELETON.md` is left unchanged as v1.
