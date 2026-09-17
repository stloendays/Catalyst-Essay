# SI Section 1. The first-record scoring convention and capability versus scored recovery

## 1.1 What the frozen scorer reports

The frozen `final_answer()` resolves the reported break-even multiplier by taking the **first** `BACKWARD` record
matching the decision pair — `next(...)`, not the last — and the reported reachability verdict by taking the **first**
classified `TEST_REACHABILITY`. Both are first-hit lookups over the run's record list, so a later and better record of
the same type never displaces an earlier one. The convention was pre-registered with the environment and is frozen;
every score is reported under it unchanged. It has two consequences that pull in opposite directions.

## 1.2 Where the first record is the right record, correctness is monotone

In the strong `gpt-5.5-2026-04-23` cell run at a **non-binding 5000-CU allowance** (frozen policy E, tag `c1uncapped`,
n = 20), the first-record rule makes the per-run correctness flag sequence monotone: once the two records exist they
cannot be displaced, and `current_winner` does not revert in this cell. Replaying the flag sequence step by step and
testing for any `False` after the first `True` returns zero flickering runs, so **first-score-complete and first-stable
are identical in 20/20 runs**.

The first record is also the correct one there. Every run takes its decision-pair `BACKWARD` in the full window and
returns `201.2234429878986` against the frozen `GT["break_even"]` value `201.2234429878984` — numerically identical
within floating-point round-off (relative difference 9.89 × 10⁻¹⁶, 7 ULP), far inside the 1 × 10⁻⁶ relative tolerance
used by the canonical-value test.

## 1.3 Under a binding budget the first record is frequently not the best record

Below the fixed-policy threshold the agent's first `BACKWARD` is often taken in a preliminary window that does not yet
contain the parity state, and the later, correct value never reaches the scored answer. Measured across every strong
cell, the scored break-even is identical to the first `BACKWARD` in **100% of runs**, while the canonical multiplier is
computed at some point in the run far more often.

| budget | n | first `BACKWARD` = canonical | scored break-even = canonical | any `BACKWARD` = canonical |
|---|---|---|---|---|
| 50 CU | 20 | 2 | 2 | 3 |
| 75 CU | 20 | 9 | 9 | 17 |
| 100 CU | 20 | 9 | 9 | 16 |
| 125 CU | 20 | 11 | 11 | 17 |
| 150 CU | 20 | 11 | 11 | 17 |
| 175 CU | 20 | 15 | 15 | 19 |
| 225 CU | 20 | 20 | 20 | 20 |

## 1.4 How the first record goes wrong

Where the first record is wrong it is wrong in one of two ways: a preliminary window that excludes T_sep = 30 °C,
giving 157.289910, or a very small local window, giving values from 1.54 to 2205.42. The scored *decision* survives
this in almost every run, because the reachability verdict depends only on the multiplier lying far above the 2.5246
headroom and not on its exact value.

Run `E_llm_agent_anonymous_B100_r18_c1low` shows the failure case. At step 8 it ran a premature `BACKWARD` in a
not-yet-optimised window, returning 1.5424, and at step 13 classified Ru as `reachable` on that basis. At step 18 a
later `BACKWARD` returned 185.30 in a 675-state window and at step 22 `TEST_REACHABILITY` classified Ru as
`unreachable`, with 31 CU still unspent. Under the first-record convention the two early records are the scored answer,
so the run scores `reachability_correct` = false despite containing the correct result.

## 1.5 Capability versus scored recovery

Between 225 and 100 CU the agent's capability to reach the canonical multiplier degrades only from 20/20 to 16/20,
while the scored value degrades from 20/20 to 9/20. The low-budget break-even degradation across 75–175 CU is therefore
largely a scoring-convention effect: it measures which record the frozen scorer reads, not whether the agent reached
the target. It must not be described as the agent failing to find the break-even at low budget. The scores stand as
reported under the pre-registered convention, but the accompanying interpretation has to name the convention.

The reading has a lower limit. At 50 CU only 2/20 runs score the canonical value and only 3/20 compute it at any point,
against 17/20 at 75 CU. Since 50 CU sits below the 75 CU completion floor — complete decision 13/20 at 50 CU against
20/20 at 75 CU — the quantitative target degrades genuinely there, not merely as a first-record artefact. The
capability-versus-scoring split applies at and above 75 CU; at 50 CU the capability itself is gone.

Main-text cross-reference: Results §3.7 and Discussion §4.6 of `MANUSCRIPT_SKELETON_v4_2026-09-14.md` (frozen).

## Sources

- §1.1, §1.2: `docs/AGENT_METRIC_DEFINITIONS_SOURCE_OF_TRUTH_2026-09-13.md` §2, §3.2, §4 (authoritative).
- §1.3 table rows 50 and 75 CU, §1.5 50 CU and 75 CU figures:
  `docs/DISCOVER_BOUNDARY_C1_ADDENDUM_A5_2026-09-11.md` §1.
- §1.3 table rows 100–225 CU, §1.4, §1.5 capability-versus-scored contrast:
  `docs/DISCOVER_BOUNDARY_C1_ADDENDUM_A4_2026-09-11.md` §1, §1.1.
