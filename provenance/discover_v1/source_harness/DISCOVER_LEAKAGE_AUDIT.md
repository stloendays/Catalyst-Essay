# DISCOVER closed-book leakage audit (E0, 2026-09-06)

Ground truth hidden from every policy: economic winner, feasible ranking, Top-3 ρ, break-even multiplier, headroom, reachability, Fe feasibility.
The agent-visible surface is exactly: `DISCOVER_TASK_V1.json`, `DISCOVER_ACTION_SCHEMA_V1.json`, the `actions` block of `DISCOVER_COST_MODEL_V1.json`, `DISCOVER_PROMPT_V1.md`, and the JSON returned by each action of `discover/env.py`. Policies and the runner never open a results.json, the manifest, the scenario registry or any output directory; only `DISCOVER_SCORER_V1.py` reads the pinned canonical run.

## 1. Surfaces scanned (characters)
| surface | chars |
|---|---|
| DISCOVER_TASK_V1.json | 5876 |
| DISCOVER_ACTION_SCHEMA_V1.json | 8350 |
| DISCOVER_PROMPT_V1.md | 2529 |
| DISCOVER_COST_MODEL_V1.json (actions block) | 1916 |
| discover/env.py string literals | 7025 |
| live action outputs (structure + strings, numeric values excluded) | 11570 |
| exception messages | 374 |
| DISCOVER_TASK_V1_ANON.json | 6079 |
| anonymous live action outputs (numeric values excluded) | 6705 |

## 2. Forbidden-token hits after whitelist (must be empty or explained)
none

## 3. Structural checks
| check | pass |
|---|---|
| candidate ordering is alphabetical (not the internal activity order) | PASS |
| task provides no cost / feasibility / ranking fields | PASS |
| environment never exposes the manifest object (no attribute 'cfg' in public_state) | PASS |
| uncertainty is returned per candidate, not by a metal-named manifest key | PASS |
| no action returns another candidate's optimized result | PASS |
| MC output names no default pair; pairwise keys only for the requested set | PASS |
| BACKWARD/TEST_REACHABILITY have no default pair or metal | PASS |
| cost model actions block carries no metal-specific example | PASS |
| policies/runner/env never open results.json, the scenario registry or a frozen_regression block (code lines; docstrings excluded) | PASS |
| scorer is the only reader of the ground truth | PASS |
| trace files live outside the agent's inputs (discover_runs/, never passed back) | PASS |
| anonymous task carries no metal symbol as a candidate id or in any string | PASS |
| anonymous environment outputs contain no metal symbol | PASS |

## 4. Items reviewed by hand
- Action names: `BACKWARD`, `TEST_REACHABILITY` and the classification vocabulary reachable / marginal / unreachable name the scientific question the task itself poses (parity through intrinsic activity); no default pair, metal or property is pre-filled, and the classification is only returned when the agent supplies a multiplier it computed.
- Candidate identities (15 metal symbols) are allowed; they are listed alphabetically with descriptor value, descriptor source and price only.
- `READ_PROPERTY_UNCERTAINTY` returns a per-candidate distribution (one candidate happens to carry a normal distribution with a larger sigma). This is declared input data, identical to what the frozen model uses; it does not state which candidate wins or which pair to compare. The manifest key name that would single out that candidate is not exposed.
- The declared screening rule in the stopping rule (lower reference activity AND higher price ⇒ cannot beat the current lowest-cost candidate) is a property of the shared cost model, stated generically; it names no candidate.
- `TEST_LEVER` lists the four admissible levers with plausible ranges; no lever is marked important.
- Cost model: per-action integer costs only; measurement metadata (`measurement` block) mentions the metals used for timing and is NOT part of the agent-visible surface (the agent receives only `actions`).
- Exceptions: messages echo the offending argument and the admissible list; none contains a result.
- Trace template fields (E6) are structural; `current_winner` is the policy's own running lowest-cost candidate, not a hint.
- Scenario registry, cached output names, canonical run summaries, benchmark metadata and regression expectations are file-system artefacts never handed to a policy: the environment computes from the harness object in memory and returns JSON.

## 5. Verdict: PASS — no leak found
