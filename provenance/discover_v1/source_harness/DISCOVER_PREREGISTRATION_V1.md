# DISCOVER pre-registration V1 (E8) — written before any formal policy-E run

## Question
Given a fixed scientific-compute budget, can a decision-aware agent allocate calculations more efficiently toward the downstream industrial
decision than non-decision-aware acquisition policies? (RQ4: where should compute go — to the largest uncertainty, or to the uncertainty that
can change the decision?)

## Frozen artefacts (hash-listed in `DISCOVER_FROZEN_V1.json` at the first formal run)
DISCOVER_TASK_V1.json · DISCOVER_ACTION_SCHEMA_V1.json · DISCOVER_COST_MODEL_V1.json · DISCOVER_PROMPT_V1.md · DISCOVER_SCORER_V1.py ·
discover/env.py · discover/policies.py · discover/run.py. Ground truth = the pinned canonical NH3-FINAL-1.1 run (scorer only).

## Policies (same initial information, action space, cost model, budget grid, scorer, stopping constraints)
A random (20 independent trajectories per budget) · B activity-first · C uncertainty-first · D fixed deterministic decision-value heuristic
(u·g·b/cost, no LLM) · E LLM decision-aware agent · **F prior-only (zero-tool)**: the model answers the task without any action; quantifies
how much of the decision comes from priors (run before freezing; `discover/prior_probe.py`).

## Task variants
**Named** (metal symbols) and **anonymous** (candidate_01…15, seeded permutation, identity mapping held by the scorer only; all descriptor,
price, uncertainty and process behaviour identical). Both are run and reported; **the closed-book claim rests on the anonymous variant**.
Pre-freeze prior probe (gpt-5-mini, n = 5): on the anonymous task the model names the cheapest plausible candidate as winner 5/5 (correct by
price prior) but calls it also the highest-activity candidate, guesses parity multiplier 1 and "reachable" (all wrong); on the named task it
recovers the textbook picture (atomic-best Ru 4/5, unreachable 4/5, parity guesses 10³–10⁴). Consequence, fixed here: **winner accuracy alone
is not evidence of decision-aware allocation** (a price prior gets it); the discriminating metrics are pair decision, reachability class,
break-even error, CU-to-stable-correct-decision, unnecessary-CU fraction and regret, evaluated on the anonymous variant.

## Primary metrics (scorer V1)
industrial winner accuracy; full-decision correctness (winner ∧ pair decision ∧ reachability class); break-even relative error; CU consumed;
CU to first / stable correct winner; decision-relevant CU fraction; unnecessary CU fraction; decision regret (USD/t); stopping efficiency.
Curves: budget → P(full decision correct); budget → regret. Development stage: deterministic single runs (A averaged over seeds).
Formal stage (later): 3 model tiers × 5 independent runs for E ("independent runs", not "seeds", unless the API exposes a controllable seed).

## Pre-registered Go / No-Go
**Scientific Go** — decision-aware policies (D and/or E) reach a stable correct full decision at a lower budget than A, B and C on the budget
grid (lower CU-to-stable-correct-winner and higher P(full decision correct) at ≤ 500 CU), with lower unnecessary-CU fraction.
**Agent-specific Go** — E shows a repeatable gain over D in at least one of: fewer CU to a stable correct decision; lower regret at fixed budget;
correct use of model-validity checks (window edge / bed cap / vessel floor / dominance) where D does not; adaptive reallocation after an
unexpected result (e.g. an infeasible optimization); fewer unnecessary calculations. "Repeatable" = holds in ≥ 4 of 5 independent runs at
the same budget for at least two model tiers.
**Expected outcome if D ≈ E** — the decision-aware allocation metric itself carries the scientific value; no claim that the LLM is superior
to a deterministic acquisition policy. **If E < D** — recorded as a negative result; no prompt tuning toward the frozen ground truth.

## Central hypothesis to test explicitly
largest uncertainty ≠ highest decision value: the candidate with the largest descriptor uncertainty (a normal 0.23 eV distribution) is not the
one whose uncertainty propagation changes the winner most cheaply; a policy that resolves the largest sigma first (C) should spend more CU for
the same decision quality than one that targets the decision boundary (D/E).

## Failure modes to record (not to remove)
malformed actions, budget-exceeded attempts, optimizing dominated candidates, MC on candidates that cannot change the decision, stopping before
S3 with an unclassified parity question, misreading a window-edge optimum as a model optimum, and (for E) reasons that contradict the chosen action.

## What is fixed in development vs formal
Development (mini): schema bugs, tool failures, malformed actions, trace parsing, budget accounting. Not allowed: changing prompt, tools, cost
model or scorer in response to scientific mistakes against the frozen ground truth. After the structure works, freeze V1 and run the formal
benchmark (single model first; tiers later).
