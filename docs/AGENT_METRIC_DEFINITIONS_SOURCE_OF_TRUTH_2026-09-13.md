# Agent metric definitions and source of truth — 2026-09-13

**Status: AUTHORITATIVE for every Agent number in the manuscript.** This file supersedes the metric *labels* used in
Addenda A3–A6 and in the capability-bounded Results framing where they disagree with it. It does not change any run, any
trace, any scored value or any frozen file, and it does not overwrite any earlier document: the earlier records stand as
the execution history and carry one-line pointers here.

Scope: the DISCOVER-BOUNDARY-C1 Agent line only. Derived read-only from existing traces.
Verification script: `tools/discover/c1_uncapped_breakeven_audit.py` plus the definition checks recorded in §5.

---

## 1. The five CU-to-X quantities that exist in the frozen outputs

This is the core hazard. Five distinct quantities live in the frozen scorer and extension metrics, all of which could
loosely be called "the CU at which the agent got the answer". They take **different values on the same runs**. Every
published number must name which one it is.

| # | quantity | source | what it measures | uncapped cell (n = 20) |
|---|---|---|---|---|
| 1 | `CU_to_first_correct_winner` | frozen `DISCOVER_SCORER_V1` | cumulative CU at the **first** step where `current_winner` equals the ground-truth winner. **Winner only** — ignores decision pair and reachability. First-hit, no stability requirement. | median **503**, range 155–503 |
| 2 | `CU_to_stable_correct_winner` | frozen `DISCOVER_SCORER_V1` | cumulative CU from which the **winner** stays correct to the end. **Winner only.** | median **503**, range 155–503 |
| 3 | `CU_to_full_decision` | `discover/boundary_c1_metrics.cu_to_full` (frozen extension metric) | cumulative CU from which the **full decision** (winner + decision pair + reachability) stays correct to the end. Sums the per-step `action_cost` field, which is **quote-based**. | median **566**, range 218–714 |
| 4 | **`decision_stable_CU`** | `tools/discover/c1_overrun_analysis.py` (ledger-true) | identical replay to #3, but the cumulative spend at step *j* is `budget_CU − step["remaining_budget"]`, which reconciles exactly with the environment ledger and with `spent_CU`. | median **566**, range 218–714 |
| 5 | `CU_after_stable_winner` | frozen `DISCOVER_SCORER_V1` | `spent_CU −` quantity #2. Spend after the **winner** stabilised. | median **211**, range 63–2518 |

**Quantity #4 is the manuscript's `first-stable` / decision-stable CU.** Quantities #1, #2 and #5 must never be quoted as
if they were it. In particular **`CU_after_stable_winner` (median 211) is not the post-stability overrun (median 148)** —
the first is measured from winner stability, the second from full-decision stability.

In the uncapped cell #3 and #4 coincide exactly (quote inflation is 0 CU in every run of this cell), so the ledger-true
value is also the frozen-metric value there. They diverge in other cells: see §4.

## 2. Is there a first-correct / first-score-complete / first-stable conflation?

Three notions are logically distinct:

- **first-correct (winner)** — first step where the winner is right (quantity #1);
- **first-score-complete** — first step where the *full* decision is right, with no requirement that it remain right;
- **first-stable** — first step from which the full decision remains right to the end (quantities #3/#4).

**Checked directly on all 20 uncapped runs: first-score-complete and first-stable are identical in 20/20 runs.** The
per-run correctness flag sequence is monotone — once the full decision becomes correct it never reverts, so there is no
flicker for a "first hit" to differ from a "last crossing". This was verified by replaying the flag sequence per step and
testing for any `False` after the first `True`: zero runs flicker.

Monotonicity here is structural, not luck: the frozen `final_answer()` reports the **first** matching `BACKWARD` and the
**first** classified `TEST_REACHABILITY`, so once those two records exist they cannot be displaced, and `current_winner`
does not revert in this cell.

**first-correct (winner) is a different number and does differ**: median 503 against 566. The 63 CU gap is real — the
winner is identified before the backward/reachability chain closes.

**Verdict: no conflation exists inside the reported uncapped numbers (218 / 566 / 714 / 148), all of which derive from
quantity #4 or from `spent_CU`.** Two labelling defects did exist and are corrected in §3.

## 3. Corrections to previously published labels

### 3.1 The "33%" is a mean of per-run ratios, not a median, and must not be paired with the median overrun

Four defensible aggregations of the post-stability overrun share exist, and they differ materially:

| aggregation | value |
|---|---|
| **mean of per-run ratios** `mean(overrun_i / final_i)` | **33.29%** ← this is the published "33.3%" |
| median of per-run ratios | 30.58% |
| ratio of the medians `median(overrun) / median(final)` = 148 / 714 | **20.73%** |
| pooled ratio `Σ overrun / Σ final` | 46.80% |

Two defects follow:

1. **Addendum A5 §2 places 33.3% in a table column headed "median".** It is a mean of per-run ratios. The column header
   is wrong for that row.
2. **`MANUSCRIPT_SKELETON_v2_2026-09-12.md` §3.7 writes "a median of 148 CU, 33% of spend"**, which reads as though 33%
   were 148/714. It is not: 148/714 = 20.7%. A median CU and a mean-of-ratios share are juxtaposed as one statistic.

**Required wording.** Report the overrun in CU as a median, and if a share is wanted, label its aggregation explicitly:

> a median **148 CU** is spent after the decision is already complete (median final spend 714 CU; mean per-run
> post-stability share **33%**, median per-run share 31%)

Do not write "148 CU, 33% of spend".

### 3.2 "bit-exact" is withdrawn for the break-even agreement

Addendum A6 and the audit-resolution appendix to the capability-bounded framing document state that the uncapped
break-even agrees with the frozen reference "bit-exactly". **That claim is wrong and is withdrawn.** A genuine binary
comparison was run:

| | value |
|---|---|
| frozen `GT["break_even"]` | `201.2234429878984`, IEEE-754 bits `4069272671e8b16a` |
| value in every uncapped trace | `201.2234429878986`, IEEE-754 bits `4069272671e8b171` |
| bitwise identical | **0/20 runs** |
| absolute difference | 1.9895 × 10⁻¹³ |
| relative difference | 9.8871 × 10⁻¹⁶ |
| difference in units in the last place | **exactly 7.00 ULP** |

**Required wording:** *numerically identical within floating-point round-off (relative difference 9.89 × 10⁻¹⁶, 7 ULP)*.
Permitted alternatives: "agrees to 15 significant figures", "identical to within double-precision round-off". **Do not
write "bit-exact", "bit-identical" or "exactly equal".** The agreement is nonetheless far tighter than the 1 × 10⁻⁶
relative tolerance used by the canonical-value test, so every scored conclusion is unaffected.

The 7-ULP offset is a round-trip artefact of writing the value to JSON and re-reading it, not a numerical discrepancy in
the model; no scientific interpretation attaches to it.

### 3.3 The headroom 1.0899 is not verified by the uncapped cell

**The reference-condition scaling headroom 1.0899 is not evidenced anywhere in the uncapped cell and must not be
attributed to it.** Every classified `TEST_REACHABILITY` in these 20 runs used `scope: "window"` and therefore returned
`max_gain_across_process_states` = **2.5246**, which is the only headroom value present. `DISCOVER_SCORER_V1.GT["headroom"]`
likewise stores only the across-states value (2.5245651130943445), so 1.0899 cannot be checked against `GT` from these
traces either.

1.0899 is the `scope: "reference"` quantity (673 K reference condition). Its evidence is the 175 CU cell and the frozen
NH3-FINAL-1.1 consistency record. Any manuscript sentence citing 1.0899 must point there, not at the uncapped control.

## 4. Frozen values for the uncapped cell, with per-run derivation

Cell: strong `gpt-5.5-2026-04-23`, frozen policy E, **non-binding 5000-CU allowance**, tag `c1uncapped`, n = 20.
All 20 runs stopped on their own rule (`agent STOP`); none reached `MAX_TURNS = 60`; remaining allowance at stop
1979–4782 CU, so the allowance never bound.

Per run: `first_stable` = quantity #4; `final` = `spent_CU`; `overrun` = final − first_stable; `share` = overrun / final.

| run | steps | first_stable CU | final CU | overrun CU | share |
|---|---|---|---|---|---|
| 0 | 16 | 218 | 218 | 0 | 0.0% |
| 1 | 17 | 218 | 366 | 148 | 40.4% |
| 2 | 29 | 566 | 1057 | 491 | 46.5% |
| 3 | 29 | 566 | 3021 | 2455 | 81.3% |
| 4 | 29 | 566 | 714 | 148 | 20.7% |
| 5 | 15 | 218 | 218 | 0 | 0.0% |
| 6 | 30 | 566 | 1794 | 1228 | 68.5% |
| 7 | 29 | 566 | 1303 | 737 | 56.6% |
| 8 | 29 | 714 | 714 | 0 | 0.0% |
| 9 | 29 | 566 | 714 | 148 | 20.7% |
| 10 | 14 | 366 | 366 | 0 | 0.0% |
| 11 | 16 | 218 | 709 | 491 | 69.3% |
| 12 | 17 | 218 | 857 | 639 | 74.6% |
| 13 | 29 | 566 | 714 | 148 | 20.7% |
| 14 | 29 | 714 | 714 | 0 | 0.0% |
| 15 | 28 | 566 | 714 | 148 | 20.7% |
| 16 | 30 | 566 | 1107 | 541 | 48.9% |
| 17 | 28 | 566 | 1303 | 737 | 56.6% |
| 18 | 16 | 218 | 366 | 148 | 40.4% |
| 19 | 28 | 566 | 566 | 0 | 0.0% |

**Aggregation rule: all headline CU figures are medians over the 20 runs, each run contributing one value. No run is
weighted, pooled or dropped.**

| published figure | definition | aggregation |
|---|---|---|
| **566 CU** | quantity #4, decision-stable CU | median of 20 per-run values |
| **714 CU** | `spent_CU` at stop | median of 20 per-run values |
| **148 CU** | final − first_stable, per run | median of 20 per-run values |
| **33%** | overrun / final, per run | **mean** of 20 per-run ratios (label required) |
| **3.5×** | median final 714 ÷ D's threshold 206 | ratio of a median to a fixed constant |
| **3021 CU / 14.7×** | maximum `spent_CU` in the cell, and 3021 ÷ 206 | single-run extremum, explicitly labelled as such |

### 4.1 What "218 CU" means, and the value collision

**218 CU carries two different meanings in the manuscript and they must be distinguished at every use.**

| context | statistic | value |
|---|---|---|
| **225 CU cell** | median decision-stable CU (and median final spend) | 218 |
| **uncapped cell** | **minimum** first_stable CU; 6 of 20 runs sit exactly there | 218 |

The coincidence is not accidental: 218 CU is the cost of completing the chain over the **full 14,136-state window**
(activity 15 CU + full window 111 CU + optimisations + `BACKWARD` 1 CU + `TEST_REACHABILITY`), so any run that affords
full enumeration lands on it. But the two numbers are different statistics of different cells.

The sentence "the decision-stable point moves from 218 CU to a median of 566 CU" is a **cross-cell comparison of two
medians**: 218 is the *225 CU cell* median, 566 is the *uncapped cell* median. It must name the cells, otherwise 218
reads as the uncapped minimum.

### 4.2 Quote-based versus ledger-true, per cell

The step-level `action_cost` field is the pre-execution `env.quote()` and overstates the real charge for
`OPTIMIZE_PROCESS`. Quantities #3 and #4 therefore diverge in some cells. Affected: 31 of 297 scored runs; per-cell
median inflation 0 CU in every cell; single-run maximum 58 CU. Only two cell medians differ: strong 175 CU (quote 140,
**ledger 124**) and strong 150 CU (quote 106, **ledger 102**). **All manuscript figures use the ledger-true quantity #4.**

## 5. Self-consistency checks performed

| check | result |
|---|---|
| `Σ ledger cost_CU` == `spent_CU` per run | holds in all scored runs |
| `Σ` step `action_cost` == `spent_CU` | fails in 31/297 runs (quote inflation) — reason #4 is used |
| first-score-complete == first-stable, uncapped cell | 20/20 identical; zero flicker |
| quantity #3 == quantity #4, uncapped cell | identical (0 CU inflation in this cell) |
| median 148 / median 714 | 20.73%, ≠ the 33.29% mean-of-ratios — labels separated in §3.1 |
| break-even bitwise comparison against `GT` | 0/20 identical; 7.00 ULP; wording corrected in §3.2 |
| headroom values present in uncapped traces | {2.5246} only; 1.0899 absent — recorded in §3.3 |
| all 20 uncapped runs self-stopped, none at turn cap | confirmed |
| fields unestablishable from raw traces | 0 |

## 6. Freeze decision

With §3.1–§3.3 applied, the Agent numbers are mutually consistent and each has a single named definition and a single
named aggregation. **§3.7 and §4.6 are frozen as of this file** in
`MANUSCRIPT_SKELETON_v3_2026-09-13.md`, which carries the corrected wording. No further Agent experiment is authorised;
the remaining Agent work is figure and Extended Data / SI assembly.

Superseded label usages, retained as history with pointers to this file: Addendum A5 §2 (33.3% column header),
Addendum A6 §2 ("bit-exact"), and the audit-resolution appendix of the capability-bounded framing document
("i.e. bit-exact"). The underlying run data in all three is unchanged and remains valid.
