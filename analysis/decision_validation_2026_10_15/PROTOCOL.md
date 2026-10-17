# Research protocol | decision robustness, constraint activation, NH3 evidence (2026-10-15)

**Registered before creating/committing new analysis code or producing new outcome data.** Exploratory re-analysis of existing published-model outputs; not a prospective external physical validation. This PR must remain independent from frozen experiments and the manuscript.

## Inputs and boundaries

- Immutable (read-only) MeOH printed cohort: \`analysis/meoh_literature_inversion_2026_10_05/literature_candidates.csv\`, 40 groups/28 papers, 310 operating-point rows.
- Immutable MeOH limit-sweep ledgers: \`analysis/meoh_constraint_boundary_2026_10_12/boundary_groups.csv\` and \`entry_feasibility.csv\`. These record reoptimized plant cost for each case under S5, S6 and inlet limits 4, 5, 6, 8, 10, 12, 15, 20, 25, 30 percent.
- Additional model-form alternative: \`analysis/meoh_inlet_definition_2026_10_12/entry_costs.csv\`, \`cost_true_inert_6.86\` (only CH4+N2 counted toward inlet cap). This changes the **constraint definition**, not just its threshold.
- NH3: the **existing** preregistered industrial 64-metric score \`analysis/validation_nh3_plant_2026_10_13/nh3_1_2/results_metrics.csv\` plus measured-rate-model bridge \`analysis/nh3_loop_reconciliation_2026_10_14/outputs/t3_points.csv\`, descriptor-kinetics pressure-rise \`outputs/t1_metals.csv\`, and KAAP electricity comparison \`outputs/t5.json\`. No new plant truth is invented.
- No change to code/data/manuscript/frozen figures underlying previous claims. Reproducibility of a GitHub Action means software integrity, not industrial-physics validity.

## Study 2: model-robust ranking (primary)

1. Use precisely the **40 frozen within-paper groups** at **identical entry identities**, with the minimum eligible cost at each model/limit. The reference laboratory leader is the source STY winner (same original printed candidate set), not re-picked from a new paper.
2. Include all 12 canonical scenario columns (S5, S6, ten named absolute limits); report separately an augmented 13-scenario set including CH4+N2-only cap at 6.86%.
3. Classify each group as **inverted in all**, **preserved in all**, or **model-dependent** across each set. Report whether the *identical plant-winning operating point* and whether the *same catalyst formulation* persists, separately from whether the STY leader loses. Same catalyst at different temperatures does not count as an identical point.
4. A tighter operating-envelope summary uses inlet limits **5, 6, 6.86, 8 and 10%**. Report a separate model-form intersection that also includes CH4+N2-only at 6.86%. Do not call the full range equally plausible.
5. Report each group's best- and worst-case STY regret and the S6 ordinary/near-infeasible split. Paper-cluster bootstrap intervals, 5,000 bootstrap resamples at fixed seed 20261015, are descriptive intervals *conditional on those models*, not validation uncertainty.
6. **Anchors must pass:** S5 15/40; S6 28/40; CH4+N2-only 18/40, with 40 unique groups and no silent loss of groups. Every canonical group cost and verdict must agree with the existing ledger.

## Study 3: constraint activation diagnostic and held-out-paper rules

1. Define an **ex-ante activation proxy** on the S5 STY-winning operating point: its inlet non-H2/CO2 mole fraction at its original S5 optimum exceeds the fixed 0.0686 cap. This variable uses **no S6 result**; distinct from an actual constrained-optimum purge shift.
2. Determine whether the baseline optimum was already feasible at the S6 cap. In the existing nested-feasible-set optimization, if an entrant's S5 optimum is within the cap then its S6 minimized cost cannot increase (within numerical tolerance). Count any violations, retain them as failures.
3. A simple prediction rule chooses STY if the S5 STY leader's inlet mole fraction does not exceed \`t × 0.0686\`; otherwise chooses the highest methanol-selectivity entry (tie → STY). The threshold \`t\` is selected from **{0.75, 1.0, 1.25, 1.5, 2.0}**, plus fixed always-STY and always-selectivity baselines. Calibrate on **other papers only** (leave-one-paper-out), accuracy then lower mean regret then fixed rule ordering. Predict only among entries feasible under S6 as in the frozen convention, but report this feasibility oracle explicitly; also report a no-oracle feasibility-agnostic sensitivity if possible.
4. Primary scores: accuracy and relative regret at 6.86%, paired with both always-STY and always-selectivity baselines. Report by paper and ordinary/near-infeasible stratum. Treat any improvements as **internal model-conditioned CV**, never an independent prospective claim; use PR #80 only after its frozen blind predictions and results have been committed.
5. Mechanism diagnostic: compare actual S5→S6 change in the S5 STY leader's purge and cost with the ex-ante proxy and group outcome, keeping explanatory diagnostics separate from predictors.
6. Baseline accuracy anchors: S6 always-STY 12/40, always-selectivity 23/40 from \`analysis/meoh_constraint_boundary_2026_10_12/PROTOCOL_B.md\`. Differences, including failures, are preserved.

## Study 4: NH3 industrial validity and model-form sensitivity

1. Recount all **64 preregistered** metrics, no re-tuning acceptance bands. Expected NH3-FINAL-1.2 pass total 32/64; subtotals state A 18/28, converter B 5/20, revealed design C 9/12, compressor E 0/3, separator V 0/1. Keep full per-case fail ledger, retain units and raw source values.
2. Pressure applicability gate: measured Dyson–Simon fused Fe source fit 149–309 atm (multiply by 1.01325 bar/atm); Rossetti promoted Ru/C 50–100 bar. Separate **in source pressure range**, **out of source pressure range**, and **not applicable to descriptor-only predictions**. The intervals do not overlap. A comparison at disparate source-range pressures is a technology/scenario comparison, not matched-pressure kinetics validation.
3. Reconcile *conditional* Fe–Ru differences from T3 across the declared source/cost/model bases without equating their absolute plant objectives. Flag sign switches by paired models; do not combine rows of different bases or call them ground truth.
4. Report published-vs-modeled KAAP electricity direction as an unresolved discrepancy, not a fitted correction. Identify failures in compressor, converter and separator evidence with metric IDs; do not introduce a free scale factor to improve 32/64.
5. **Anchors must pass** for the original total/subtotals and published original source ranges. Fail on missing, duplicate, nonfinite or inconsistent source rows.

## Engineering execution

Three independently runnable standard-library Python scripts with a shared test module. GitHub Actions PR/push and manual dispatch run each in isolated fresh output directories, validate anchors, upload CSV/JSON/Markdown artifacts even on failure, with **read-only repository token permissions**. Workflows never write results to \`main\`, re-fit costs to industrial data, or claim any additional external validation. Main manuscript integration requires a separate scientific review and explicit promotion decision.
