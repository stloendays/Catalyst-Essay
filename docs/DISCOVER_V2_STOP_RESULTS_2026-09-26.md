# DISCOVER-V2-STOP results — 2026-09-26

**Status: complete.** 180 new strong-tier runs (`gpt-5.5-2026-04-23`, anonymous task, API-default sampling), preregistered in
`provenance/discover_v2_stop/PREREG_V2_STOP.json` before the first formal run and scored with the **unchanged**
`DISCOVER_SCORER_V1`. Frozen V1 hashes 15/15 PASS before and after
(`provenance/discover_v2_stop/hashcheck_v2stop_{before,after}_*.json`). 0 API retries, 0 driver exceptions,
13.31 M prompt + 1.47 M completion tokens. Preregistration and motivating replay:
`DISCOVER_STOPPING_TEST_2026-09-26.md`.

Files: driver `tools/discover/v2_stop_runner.py`, analysis `tools/discover/v2_stop_analysis.py`, prompt addenda
`provenance/discover_v2_stop/DISCOVER_V2_STOP_PROMPT_ADDENDA.json`, per-run table
`data/discover_v2_stop/v2_stop_runs_2026-09-26.csv`, per-cell table `v2_stop_cells_2026-09-26.csv`, raw traces
`data/discover_v2_stop/runs/<arm>/traces/anonymous/` (trace + messages + scorer-only identity mapping), batch logs
`provenance/discover_v2_stop/stdout_<arm>.txt`.

## 1. Protocol delta (everything else inherited byte-for-byte from DISCOVER V1)

| arm | change |
|---|---|
| **S-hard** | the environment ends the episode after the first executed action after which S1 ∧ S2 ∧ S3 holds; the addendum tells the model so |
| **S-gate** | after S1 ∧ S2 ∧ S3 first holds, a *paid* action executes only if it is flip-capable: `CHECK_MODEL_VALIDITY`; `BUILD_PROCESS_WINDOW` / `OPTIMIZE_PROCESS` of the winner or atomic-best candidate only while an edge flag is pending (their optimum or the parity state on a window edge that is not a full-domain bound), in a different window; `BACKWARD` only after such a re-optimisation; `TEST_REACHABILITY` only after a new `BACKWARD`. Everything else paid is rejected at 0 CU with the reason; 3 consecutive rejections end the run. S3′ = S3 ∧ no pending edge flag ∧ parity/reachability current is reported to the model |
| **S-anytime** | prompt addendum only: reach the rule at minimum spend, widen only on an edge flag, stop when S3′ holds |
| all arms | `final_answer` uses the **last** matching `BACKWARD` / classified reachability for the pair (V1: first). The V1 first-record answer is stored beside it; it differs in 14/180 runs (12 at 75 CU, 2 at 225 CU: only the parity multiplier changes) and never changes a reachability verdict |

## 2. Results (n = 20 per cell; C1 = frozen V1-protocol policy-E cell, same model)

| arm | CU | complete | reach | canonical parity | median final CU (C1) | median rule-armed CU | runs paying after rule | max post-rule CU | narrow window | S3′ at stop | S3′ false positive |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| S-hard | 75 | 19/20 | 19 | 11 | 71 (70) | 71 | 0 | 0 | 20 | 4 | 0 |
| S-hard | 225 | 20/20 | 20 | 20 | 218 (218) | 218 | 0 | 0 | 0 | 20 | 0 |
| S-hard | 5000 | 20/20 | 20 | 20 | **566 (714)** | 566 | 0 | 0 | 0 | 20 | 0 |
| S-gate | 75 | 19/20 | 19 | 9 | 72.5 (70) | 71.5 | 5 | 26 | 20 | 4 | 0 |
| S-gate | 225 | 20/20 | 20 | 19 | 218 (218) | 218 | 0 | 0 | 3 | 18 | 0 |
| S-gate | 5000 | 20/20 | 20 | 20 | **bimodal: 10 runs at 216–218, 9 at 564–566, 1 at 274 (714)** | — | 0 | 0 | 0 | 20 | 0 |
| S-anytime | 75 | 20/20 | 20 | 15 | 73.5 (70) | 70.5 | 8 | 31 | 20 | 11 | 0 |
| S-anytime | 225 | 20/20 | 20 | 18 | **158 (218)** | 152 | 2 | 114 | **16** | 20 | 0 |
| S-anytime | 5000 | 20/20 | 20 | 20 | **216 (714)** | 216 | 0 | 0 | 4 | 20 | 0 |

Per-run final spend, sorted:

- S-hard 5000: 218 ×5, 566 ×9, 616 ×3, 714 ×2, 3021 ×1 (the 3021 run optimised every candidate in the full window before the rule held; nothing was spent after it).
- S-gate 5000: 216–218 ×9, 274, 564–566 ×10.
- S-anytime 225: 32, 89, 97, 105, 112, 122, 136, 148, 154, 154, 162, 168, 174, 176, 180, 204, 218 ×4.
- S-anytime 5000: 146, 151, 154, 215–218 ×16, 263.

Gate activity in S-gate: 1 rejection in 60 runs (a 5000-CU run asked for `RUN_MC` once after arming and then stopped). The
5 post-arm paid runs at 75 CU all followed an edge flag: re-window, re-optimise, new `BACKWARD`/reachability, all admissible.

## 3. Preregistered gates

| gate | criterion | result |
|---|---|---|
| completion | ≥ 19/20 in every cell and arm | **pass** (all 9 cells) |
| post-rule spend | median 0 CU in S-hard and S-gate at 75 and 5000 CU | **pass** (0 CU in 40/40 runs at 5000; 0 median at 75) |
| S3′ false positives | 0/60 in S-gate | **pass** (0/60; 0/180 over all arms) |
| allowance invariance | S-anytime median final at 225 CU within 25 CU of the 75-CU median | **fail**: 158 vs 73.5 |
| parity recovery | reported, not gated | S-hard 11/20, S-gate 9/20, S-anytime 15/20 at 75 CU (C1 9/20); 18–20/20 elsewhere |

## 4. The two incorrect runs

- **S-hard 75 r12** (F1, the mechanism the S-hard arm cannot repair): a 1,525-state window put Fe at 30.68 USD/t, parity
  2.69×, verdict "marginal"; the rule held at 44 CU and the episode ended with all three edge flags pending. The gate arm
  would have required re-optimisation here; the forced stop cannot.
- **S-gate 75 r16** (budget, not gate): one invalid `bounds` argument cost a turn, three windows and six optimisations
  reached the canonical Fe and Ru optima, `BACKWARD` returned no parity within 10¹² in the last narrow window, and 1 CU
  remained for `TEST_REACHABILITY` (2 CU). The gate never armed.

## 5. What the arms establish

1. **The post-rule overrun is removable without cost to the decision.** Under a non-binding allowance both S-hard and
   S-gate complete 20/20 with 0 CU spent after the rule; median final spend falls from 714 to 566 CU (S-hard) and to a
   216/566 bimodal split (S-gate). The 8,207 CU of post-rule `RUN_MC` in the C1 non-binding cell has no counterpart in
   any of the 40 gated runs.
2. **A hard stop is gamed at low budget.** Told that the episode ends when the rule holds, the strong model defers
   `TEST_REACHABILITY` until its refinement is done: the S-hard 75-CU arming point has median 71 CU (C1 first-rule point
   52.5 CU), and final spend is unchanged (71 vs 70). The gate arm, which leaves the stop to the model but restricts
   what can be paid for afterwards, behaves the same way at 75 CU (71.5). The saving of a stopping criterion is therefore
   confined to the regime where the allowance is not binding.
3. **The validity condition closes the window-relative false positive.** S3′ was true at stop in 137/180 runs and never
   on a wrong decision; the only F1-type run (S-hard r12) ended with S3′ false and edge flags pending, which is the
   signal the gate arm acts on.
4. **Allowance-independent scoping is reachable by instruction, but not fully.** With the S-anytime addendum the strong
   model builds narrow windows at 225 CU in 16/20 runs (C1: 0/20) and at 5,000 CU in 4/20 (C1: 0/20); median final spend
   drops from 218 to 158 CU at 225 CU and from 714 to 216 CU under the non-binding allowance, with 20/20 completion in
   every cell and the highest 75-CU parity recovery of the three arms (15/20). It does not reach the 75-CU spend
   (73.5): at 225 CU the model still uses a median 152 CU before the rule holds, and 4/20 runs fall back to the full
   window. The "budget-induced search compression" wording of the manuscript therefore stands, with the qualification
   that roughly two thirds of the compression can be induced by instruction alone.

## 6. Manuscript-facing statements supported

- "When the S1–S3 stopping rule is enforced or gated, the strong policy completes 20/20 decisions under the non-binding
  allowance with no compute spent after the rule (median final 566 CU versus 714 CU under the frozen protocol)."
- "A prompt-level instruction to scope for minimum spend raises narrow-window use at 225 CU from 0/20 to 16/20 and
  lowers median spend from 218 to 158 CU, without loss of completion."
- "Under a forced stop the policy defers the reachability test to the end of a binding allowance; the low-budget
  spend is unchanged."

Not supported: any claim that a stopping criterion reduces spend below the 75-CU C1 value, or that S-anytime achieves
allowance-invariant spend.

## 7. Next

- Add the three statements above to the v8 Agent Results paragraph and Methods; extend Fig. 6 with one panel
  (final spend by arm at 5,000 CU, C1 alongside). Run `tools/check_manuscript_numbers.py` after editing.
- Part C (open-weights cross-model) proceeds on the unchanged V1 protocol as preregistered; the S-gate arm is the
  one to repeat on an admitted open model.
