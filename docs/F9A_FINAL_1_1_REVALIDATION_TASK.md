# F9A targeted revalidation task — NH3-FINAL-1.1

Use this task in the **local NH3 source harness**. This is deterministic scientific computation only; **no LLM/API calls are needed**.

## Objective

Recompute the NH3 side of the cross-reaction TOF economic-leverage comparison under the already frozen **NH3-FINAL-1.1** model, using exactly the same leverage definition and denominator-alignment convention as the earlier pre-FINAL-1.1 analysis.

The old 273–410 ratio is on HOLD until this task closes.

## Frozen inputs that must not change

- canonical NH3 config: `configs/nh3_final.yaml` = **NH3-FINAL-1.1**;
- canonical run anchor: `outputs/nh3_final_20260905T134204Z`;
- existing FINAL-1.1 process/economic equations, pressure-CAPEX implementation and optimizer;
- candidate identities and economic boundary;
- original TOF-leverage perturbation / finite-difference definition used in the historical cross-reaction calculation;
- denominator harmonization fractions: **0.02, 0.025, 0.03**;
- MeOH numerator: **0.3757939247335326** (CH4-suppression leverage from frozen D01 v3).

Do not tune any parameter to preserve the previous 273–410 result.

## Step 1 — inspect and identify the exact historical metric

Before computing anything, locate the code, worksheet, function or calculation that generated the historical NH3 TOF normalized leverage **0.000916–0.001374**.

Record:

- exact source file/path;
- function/formula;
- finite-difference or perturbation size and direction;
- whether the economic cost is reoptimized after the TOF/activity perturbation;
- raw reduced-cost leverage before the 2–3% denominator conversion;
- units and sign convention;
- file SHA-256 and current git commit if available.

If no exact historical definition can be recovered, **STOP** and report `METRIC_EQUIVALENCE_NOT_ESTABLISHED`. Do not create a new proxy metric.

## Step 2 — archived regression check if possible

If the harness retains an immutable archived FINAL-1.0 config and the same leverage code can run against it, reproduce the historical result as a regression check.

Expected historical normalized envelope is approximately:

- 2% fraction: **0.000916-ish** or the matching end implied by the original sign/normalization convention;
- 3% fraction: **0.001374-ish**;
- corresponding MeOH/NH3 ratio envelope: approximately **273–410**.

Do not force exact agreement by modifying code. Report the actual reproduction error.

If FINAL-1.0 cannot be rerun cleanly, note `ARCHIVED_REGRESSION_UNAVAILABLE` and continue only if Step 1 established the metric exactly.

## Step 3 — FINAL-1.1 calculation

Run the exact same TOF/activity perturbation and economic reoptimization under `configs/nh3_final.yaml` / NH3-FINAL-1.1.

Record at minimum:

- baseline optimized NH3 cost state used by the metric;
- perturbed optimized cost state(s);
- raw reduced-cost elasticity/leverage;
- any process-state movement caused by the perturbation;
- numerical convergence / boundary status;
- exact result before denominator harmonization.

Do not modify the pressure upper bound, bed cap, recovery, lifetime or other levers during this calculation.

## Step 4 — denominator alignment

Using the same historical conversion rule, calculate the FINAL-1.1 normalized NH3 TOF leverage at:

- reduced/full fraction = **0.020**;
- reduced/full fraction = **0.025**;
- reduced/full fraction = **0.030**.

Keep MeOH fixed:

`L_MeOH_CH4 = 0.3757939247335326`

For each fraction calculate:

`ratio = L_MeOH_CH4 / L_NH3_TOF_normalized`

Do not reorder or cherry-pick the bounds. Report all three values.

## Step 5 — required outputs

Create a dedicated bundle that can be copied into `Catalyst-Essay`, preferably:

- `cross_reaction_final1_1_inputs.csv`
- `cross_reaction_final1_1_results.csv`
- `cross_reaction_final1_1_provenance.json`
- `CROSS_REACTION_FINAL1_1_REVALIDATION.md`

The provenance JSON must include:

- timestamp;
- git commit / repository state;
- SHA-256 of `configs/nh3_final.yaml`;
- SHA-256 of the metric implementation;
- canonical run anchor;
- historical metric source/path;
- perturbation definition;
- denominator fractions;
- MeOH source/value;
- regression-check status;
- FINAL-1.1 numerical result status.

## Step 6 — result classification

Classify the result as exactly one of:

### PASS_REVALIDATED
The historical metric is exactly identified and reproducible enough to establish equivalence, and the FINAL-1.1 run produces a valid new quantitative result. Report the **new** three-point normalized envelope and ratios. Do not privilege agreement with 273–410.

### METRIC_EQUIVALENCE_NOT_ESTABLISHED
The historical calculation cannot be identified sufficiently to guarantee the same metric. Do not create a new F9A quantitative value. Recommend qualitative-only cross-reaction pathway comparison.

### FINAL1_1_CALCULATION_FAILED
The metric is identified, but the frozen FINAL-1.1 calculation cannot be completed or fails numerical/model validity checks. Preserve logs and report the failure without changing the model.

## Step 7 — repository handoff

After completion, provide a concise report containing:

1. classification;
2. historical metric definition;
3. archived regression result, if available;
4. FINAL-1.1 raw NH3 TOF leverage;
5. normalized NH3 values at 2%, 2.5%, 3%;
6. MeOH/NH3 ratios at the same three fractions;
7. config/code hashes;
8. generated file paths;
9. whether F9A can now be promoted from HOLD.

Do **not** change any other manuscript result, figure or Agent benchmark as part of this task.