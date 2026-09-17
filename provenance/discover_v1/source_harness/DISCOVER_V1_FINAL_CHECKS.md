# DISCOVER V1 — final blocking checks before the first formal LLM run (2026-09-06)

Scope: the three blocking checks and two light enhancements requested after protocol review. No Layer-A, manifest, ground-truth or manuscript
change. Policy D constants untouched. One policy-level correction (C's tie-break) is disclosed in §4.

## 1. Stopping-oracle audit — PASS
`DISCOVER_ORACLE_AUDIT.md` §1; tests `test_stopping_rule_uses_only_public_state`, `test_stop_is_allowed_with_wrong_conclusion_and_penalised_only_by_scorer`,
`test_screening_follows_public_price_and_activity_not_hidden_truth`. S1–S4 read only `optimized / activity / candidates / backward / reachability / budget /
_price` (public); `may_stop` is advisory; a wrong conclusion can be stopped on and is penalised only by the scorer.

## 2. Fixed-VOI oracle audit — PASS (audit only, no algorithm change)
`DISCOVER_ORACLE_AUDIT.md` §2; test `test_policies_never_touch_hidden_state`. u from READ_PROPERTY_UNCERTAINTY + own MC ledger; g and b from own
optimized costs; cost from the frozen cost model; the OPTIMIZE surrogate from own activities + public prices; no canonical ranking, hidden winner,
future result or ground-truth sensitivity anywhere in `policies.py`.

## 3. Anonymous closed-book variant — built and verified
`DiscoverEnv(anonymous=True, mapping_seed=20260906)`: candidate_01…15 by seeded permutation; descriptor, price, uncertainty and every process
computation identical (test `test_anonymous_variant_is_isomorphic_and_mapping_is_scorer_only`); mapping only in `identity_mapping.json` per run
and `discover/IDENTITY_MAPPING_SCORER_ONLY.json`, read by the scorer's `_demap`. `DISCOVER_TASK_V1_ANON.json` and a live anonymous
environment dump pass the leakage audit (no metal symbol anywhere). Deterministic policies give **identical CU and outcomes** on both variants
(B: 184/219/269/369 CU; D: 193/247/281 CU; C: 172/230/293/500/798/1059 CU) — the environment is isomorphic and B/C/D are label-invariant.

## 4. Disclosure: C's tie-break was label-dependent and was made label-invariant before freezing
The first C draft broke σ ties alphabetically by candidate label, so its trajectory differed between the named and anonymous variants
(named: full decision only at ≥ 1200 CU; anonymous: at 300 and ≥ 800). This is a protocol defect (a baseline must not depend on naming), not a
tuning: the tie-break is now (σ descending, descriptor value, price) — public physical data only. The superseded label-order traces are kept in
`discover_runs/superseded_C_label_tiebreak/`; the new C is identical on both variants. C remains non-monotonic in budget (full decision at 300 and
≥ 800 but not at 500) because its queue spends the 500-CU budget on 1,000-draw Monte Carlo before the parity step; recorded, not adjusted.

## 5. Random baseline, 20 independent trajectories per budget (both variants)
| budget | named: P(winner) / P(full) / mean regret | anonymous: P(winner) / P(full) / mean regret |
|---|---|---|
| 200 | 0.15 / 0.05 / 701 (∞ capped 1000) | 0.15 / 0.00 / 602 |
| 250 | 0.20 / 0.05 / 503 | 0.15 / 0.00 / 453 |
| 300 | 0.30 / 0.00 / 204 | 0.20 / 0.00 / 254 |
| 500 | 0.55 / 0.10 / 53 | 0.70 / 0.05 / 2.4 |
| 800 | 0.75 / 0.20 / 2.1 | 0.85 / 0.20 / 1.0 |
| 1200 | 0.90 / 0.50 / 0.7 | 0.95 / 0.65 / 0.3 |
| 2000 | 1.00 / 0.85 / 0.0 | 0.95 / 0.85 / 0.3 |
Random needs ≈ 2,000 CU for 85 % full decisions; D reaches 100 % at 250 CU, B at 250 CU, C at 300 (then not at 500) and ≥ 800. Variant
differences for random are sampling noise (different action-list order under the two labelings; 20 trajectories each). 322 + 14 traces, 0 action
errors, 0 schema violations.

## 6. Zero-tool prior-only probe (policy F; gpt-5-mini, n = 5 per variant; `discover_runs/PRIOR_PROBE_gpt-5-mini_2026-09-05.json`)
| variant | winner correct | atomic-best correct | reachability correct | parity guess | confidence in winner |
|---|---|---|---|---|---|
| anonymous | 5/5 (candidate_13 → the cheapest plausible candidate) | 0/5 (names the winner as the most active too) | 0/5 ("reachable") | 1.0 ×5 (log10 error 2.3) | 0.60–0.85 |
| named | 5/5 (Fe) | 4/5 (Ru) | 4/5 (unreachable) | 10³–6.7·10³ (log10 error 1.5) | 0.60–0.80 |
Read-out fixed in the pre-registration: on the named task the model recovers the textbook picture without any tool (so named results cannot
support a closed-book claim); on the anonymous task the price prior alone yields the winner but nothing of the inversion, parity or reachability.
Therefore winner accuracy alone is not evidence; pair decision, reachability class, break-even error, CU-to-stable-correct-decision,
unnecessary-CU fraction and regret on the anonymous variant are the primary evidence.

## 7. Frozen
`DISCOVER_FROZEN_V1.json` lists sha256 of task (named + anon), schema, cost model, prompt, scorer, prereg, env, policies, runner, LLM policy
interface, prior probe, identity mapping, forbidden-action note and the oracle tests; D constants; mapping seed; budget grid; 20 random
trajectories per budget. Any change = V2. No LLM policy-E run has been made.
