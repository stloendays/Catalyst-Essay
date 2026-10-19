# Follow-up research protocol: S5-to-S6 decision transfer + NH3 source-basis closure

**Written before implementing this extension or generating the new study outcomes, 2026-10-15.** This is a *prospectively specified reanalysis of already observed model data*, NOT a genuinely independent preregistered field experiment. The first pilot showed a naive STY-winner activation indicator fires in 38/40 groups, and its paper-held-out choice rule underperformed selectivity (21/40 vs 23/40). The rules below are fixed before code and outputs. Original model and manuscript stay untouched.

## H-M: process-informed proxy without a test-time S6 oracle

An S5 optimum's reactor-inlet CO+CH4+N2 fraction q, S5 cost J5 and laboratory selectivity define an activation burden when inlet cap L=0.0686 is imposed. Train on S6 *model results for OTHER PAPERS* only, then predict the held-out paper's candidates. Neither the held-out paper's S6 cost/purge, outcome, feasible set nor winning candidate may be read by its predictor or model fit. Predictions are internal, MODEL-CONDITIONAL, not plant validation.

### Data and anchors

- Original printed candidate CSV contains 351 records/81 groups; restrict exactly to the frozen **40 scored groups, 310 entries, 28 distinct DOI papers** identified by the original S6 group-metrics CSV.
- Frozen outcome/group-tie ledger is the preexisting boundary_groups.csv. S5 mismatches 15/40, S6 mismatches 28/40; STY benchmark selects the optimal cost in 12/40, selectivity's frozen tie-set criterion in 23/40.
- S5-only candidate features: S5-optimized J5, inlet non-H2/CO2 fraction q at S5 optimum, experimental SCO, SCH4, SMeOH, and S5 purge. The last variable is explanatory only, not a primary predictor. No S6 outcome in test features.
- Every group/entry is retained; invalid input aborts. Unavailable S6 evaluation cost for selected candidate is a failed selection, not quietly filtered. Original source order supplies final deterministic tie-breaker; the published frozen tie-set convention is reported separately.

### Frozen models and selection

- L=0.0686, a=max(0,ln(max(q,1e-12)/L)).
- For training-paper entries only y=ln(J6/J5). A negative y < -1e-6 violates nested optimization.
- **Primary:** nonnegative ridge model ln(Jhat6/J5) = b1*a + b2*a*SCO/(SMeOH+0.05) + b3*a*SCH4/(SMeOH+0.05). Fit each b>=0 by deterministic cyclic coordinate descent for up to 4000 sweeps, with ridge=0.10, no intercept, each DOI paper having exactly equal total training weight across its individual entries. Coefficient changes <1e-12 define convergence.
- **Secondary ablation:** same method with only feature a; no tuning or model selection on test outcomes.
- Baselines: lowest S5 cost, highest methanol selectivity, and original highest STY. All rules pick from all originally scored entries without a lookahead at S6 feasibility.
- For every held-out DOI, fit separately on all remaining DOI papers; save model coefficients, training DOI hashes/counts and every test-entry prediction BEFORE score aggregation. Use a separate outcome pass for S6 comparisons; do not peek at the held-out S6 labels while training or ranking.
- Score exact picked operating-point matches, 5%-regret events, finite average/median relative regret and infeasible picks, with held-out candidate log cost error; report tie-set baseline accuracy separately. If a selected candidate is infeasible, it is scored wrong and finite regrets exclude it with a visible failure count.
- For interpretability, report the measured S5→S6 optimal-purge shift only *after* rankings are frozen. No use of observed shift in a test feature.
- Paired paper-cluster 95% bootstrap CI (5000 resamples, seed 20261015) conditional on held-out predictions (no retraining within bootstrap).
- Fixed abstention rule: accept only if second-ranked predicted cost exceeds the predicted winning cost by >=5% of the winning cost. Coverage and regret among accepted calls; threshold NEVER selected on outcomes.
- No CPU savings claim without separate timing benchmark. S5 optimization is still needed for all candidates.

### Interpretation
If the model underperforms STY, selectivity or S5-cost selection, state it. Do not claim prospective validation: PR #80 remains a separate out-of-sample experiment. Any post hoc alternative models are explicitly labelled exploratory.

## H-N: joint, source-grounded NH3 engineering-closure audit

Independently rerun *the existing source-pinned* registered 64-metric industrial audit, 28 BASF/Ullmann VLE table points, five original/conditional separator-loop inlets, five inverse-loop separator requirements, 3 source-only stoichiometric bounds, and four Liu S-200 bed profile diagnostics, then assemble an independent no-fit report.

1. Assert 32/64 unchanged (A 18/28, B 5/20, C 9/12, E 0/3, V 0/1). Never rewrite the original source or pass rules.
2. Join all five original/conditional/required separator inlet comparisons by source metric ID and plant case. Source BASF saturation was measured in a 1:3 N2/H2 mixture and is NOT an in situ plant vapor calibration.
3. For TOP140, TOP220 and UHDE188, join source-only optimistic inlet bound and calculate observed/bound factor and minimum hypothetical separator vapor concentration at the named source design flows. The single separator, NH3-free makeup hypothesis may NOT describe actual industrial topology. Do not claim real plant conservation-law failures.
4. For both Liu S-200 conditions compute installed vs inverse-required bed-volume ratios and minimax multiplicative discrepancy under ONE shared *hypothetical* rate multiplier. Its lower bound is sqrt(max(ratio)/min(ratio)), which quantifies mismatch of the source-conditioned fixed-trajectory rate equivalents only; it does NOT validate an effectiveness factor or kinetics adjustment.
5. For E01-E03 report registered model vs reported combined compression duties and shortfalls. For E01 derive the existing generous 27->30 bar suction-ratio thought-experiment from the pinned source audit and report remaining fraction.
6. Generate standalone CSV, JSON and short Markdown, including source case IDs and uncertainty/source-scope notes. Quantitative comparisons must recompute from the original provenance-pinned scripts on GitHub Actions; do not transcribe narrative numbers.
7. New physics candidate cannot be promoted from this no-fit audit. Full flowsheet, refrigerant compression, real-mixture separator and reactor heat/hydraulics are still needed.

## Reproducibility boundaries

One new folder analysis/decision_followup_2026_10_15 and one new read-only workflow .github/workflows/decision-followup-2026-10-15.yml. Independent Actions jobs for methanol surrogate and NH3 physics. The sources in docs, data, provenance and all earlier analysis folders MUST be unchanged; checkout full history for merge-base boundary check. Artifacts uploaded regardless of job failure. Tests verify frozen anchors, evidence counts, no held-out DOI leakage and no hidden S6 feasibility filtering. Do not merge into main or promote claims to manuscript without review.
