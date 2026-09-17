# DISCOVER oracle audits (blocking checks 1–2 before the first formal LLM run, 2026-09-06)

Tests: `tests/test_discover_oracle.py` (static source inspection + behavioural checks). No algorithm was changed by these audits.

## 1. Stopping-rule oracle audit (S1–S4)
Implemented in `discover/env.py::DiscoverEnv.stopping_status`, `current_winner`, `screened_dominated`. The only attributes these functions read
(static check, allowed set enforced by the test): `optimized`, `activity`, `candidates`, `backward`, `reachability`, `budget`, `_price`.

| criterion | evidence used | agent-visible? | hidden truth used? |
|---|---|---|---|
| S1 winner identified | `optimized` = results of the policy's own OPTIMIZE_PROCESS calls; winner = argmin of the feasible ones | yes (returned by OPTIMIZE_PROCESS) | no |
| S2 no unresolved candidate | candidates not optimized and not screened; screening = `activity` (own COMPUTE_ACTIVITY results) and `_price` (public candidate price from INSPECT_CANDIDATES) relative to the policy's own current leader | yes | no |
| S3 parity classified if needed | `activity` complete for all candidates (own computations); highest computed activity vs own leader; own BACKWARD and TEST_REACHABILITY records | yes | no |
| S4 value / budget | `edv_max` passed by the policy (its own score), `budget` ledger | yes | no |
| `may_stop` | (S1 ∧ S2 ∧ S3) ∨ budget exhausted — advisory only | yes | no |

Behaviour confirmed by tests: (i) a policy that has optimized only Os is reported with `current_winner = Os` and Fe/Ru unresolved — the
environment reports the policy's own leader, never the true one; (ii) perturbing the *public* price table changes the screening verdict
accordingly (Co becomes unresolved when publicly cheaper than Fe), i.e. S2 follows public data, not hidden truth; (iii) the runner never blocks a
STOP: a wrong conclusion may be stopped on and is penalised only by `DISCOVER_SCORER_V1.py` (regret, correctness, unresolved risk are scored,
not prevented). The ground-truth objects (`frozen_regression`, `activity_order_expected`, canonical results) never appear in these functions.

## 2. Fixed-VOI (policy D) oracle audit — sources of u, g, b, cost
`discover/policies.py::FixedVOIPolicy.score`. Attributes of `env` referenced (static check, allowed set enforced): `current_winner`,
`screened_dominated`, `activity`, `_price`, `candidates`, `optimized`, `uncertainty_read`, `mc`, `budget`.

| term | definition in code | source at the current step | hidden / future information? |
|---|---|---|---|
| **u** (uncertainty) | `sig = uncertainty_read[m].sigma_eV` or `half_width/√3`; `u_rem = sig/0.1 / (1 + done/50)²`, `done` = draws already spent on m | READ_PROPERTY_UNCERTAINTY output for m; own MC ledger | none |
| **g** (downstream leverage proxy) | 1 for the current leader; for others `b` (closeness to the leader) | own optimized costs | none (no ground-truth sensitivity, no lever table) |
| **b** (decision-boundary closeness) | `exp(−|ln(C_m/C_w)|/0.15)` with C from own OPTIMIZE_PROCESS results | own optimized costs | none |
| **cost** | `quote()` of the action from the frozen cost model | public cost model | none |
| OPTIMIZE value | surrogate `−activity(m) + 0.5·log10 price(m)` ranked among not-yet-optimized candidates; dominated (screen) → ≈0 | own activities + public prices | none; the surrogate is a declared prior, not the canonical ranking |
| BACKWARD / TEST_REACHABILITY value | 5.0 while S3 unsatisfied, else 0.01 | own stopping status | none |
| TEST_LEVER value | 0.05/cost when ≥ 2 feasible candidates | own state | none |
| CHECK_MODEL_VALIDITY value | 0.3/cost once any candidate is optimized | own state | none |
| STOP | S1∧S2∧S3 and best value < θ = 0.05 | own state + own scores | none |

Conclusion: every term is computed from information already returned by the environment at that step or from the public task data; no
canonical ranking, hidden winner, future action result or ground-truth sensitivity is read. Constants (θ 0.05, decay 50 draws, price weight 0.5,
boundary scale 0.15) are frozen in `DISCOVER_FROZEN_V1.json`; no further tuning.

## 3. Anonymous variant
`DiscoverEnv(anonymous=True, mapping_seed=20260906)` relabels the 15 candidates as `candidate_01…15` by a seeded permutation; descriptor, price,
uncertainty and every process computation are identical (test: same optimized cost and pressure for the real Fe under both labels; no metal
symbol in any output). The mapping is written by the runner as `identity_mapping.json` next to each trace and read only by the scorer
(`_demap`). Task file: `DISCOVER_TASK_V1_ANON.json`; mapping for the task: `discover/IDENTITY_MAPPING_SCORER_ONLY.json`. The leakage audit
scans the anonymous task and a live anonymous environment dump (structural checks added).
