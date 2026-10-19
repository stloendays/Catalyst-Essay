# Registered-extension protocol: fully crossed inlet-limit x CO-inclusion sensitivity

**Extension declared on 2026-10-15, AFTER seeing initial 6-scenario experiment but BEFORE coding or running the 10-scenario result.** Exploratory post-hoc extension, not a fresh externally independent preregistration. Do not erase or reinterpret the 6-scenario outcomes; retain them as a sensitivity analysis. This extension fixes a DATA-COVERAGE issue identified in the initial experiment: the source already reports both formulations for all 5 cap values, whereas the original primary 6-scenario set considered the CH4+N2-only definition only at 6.86%.

## Sources and design

- Same fixed cohort, 40 multi-entry groups, 310 original scored candidates, 28 DOI papers, no editing source models.
- The FULL Cartesian scenario set: definition D in {frozen: cap CH4+CO+N2, true_inert: cap CH4+N2}, and cap L in {5%, 6%, 6.86%, 8%, 10%}. Exactly 10 scenarios; avoid hindsight scenario subset changes.
- Primary per-entry source is 'analysis/meoh_inlet_definition_2026_10_12/entry_costs.csv' columns cost_frozen_5, cost_frozen_6, cost_frozen_6.86, cost_frozen_8, cost_frozen_10 and corresponding cost_true_inert_{limit}. These are independent candidate-specific purge reoptimizations already on file, not in-situ conditional magic.
- Original winner/tie source ledger is 'scan_groups.csv': require exactly one row per model-definition/cap/group; use source's plant_leader identity to check optimizer minimum cost under that scenario. In addition, validate all five frozen-definition cost columns against earlier 'literature_candidates.csv' columns at identical candidate identity (limit 6.86 maps cost_recycled_opt_inlet); abort on source drift >1e-6 or missing/extra groups.
- At each scenario, original STY-inversion count source anchors (out of 40): frozen [26,27,28,27,24] for 5,6,6.86,8,10; CH4+N2-only [18,18,18,15,15], from frozen inlet-definition analysis. FAIL loudly on drift.
- For each candidate the optimized cost must NOT increase as the admissible cap gets less restrictive, **within each fixed definition**. Check finite/NaN nesting and relative 1e-6 tolerance. Do not compare monotonicity *across* different model forms.

## Decision questions and metrics

- Per original group and scenario, define relative regret R_i,scenario = J_i/J_opt,scenario-1, infinity if infeasible. Select one operating point for all 10 scenarios by min_i max_s R_i,s. Retain original row index tie-breaker. Group certification if worst-case R <=5% (fixed original paper decision threshold). Report >10%, 0%, and median risk, material identity and outlier paper sensitivity.
- Compare already reported six-scenario minimax from the independently implemented reference, and the same fixed STY, selectivity, S5-cost, S6-cost baselines. Distinguish source-formulation/operating-point identity from economic equivalence.
- Denote r_all=min_i max_{D,L} R(i;D,L). If a perfect diagnostic reveals the **form D** but not L, the policy can choose an optimum worst-case candidate separately for each model family. Residual worst-case risk r_after_form=max_D min_i max_L R(i;D,L). Decrease r_all-r_after_form >=0. The exactly analogous perfect knowledge of **cap L** but not definition gives r_after_cap=max_L min_i max_D R(i;D,L). Decrease r_all-r_after_cap >=0. Learning *both* yields zero regret by construction.
- These are nonprobabilistic perfect-knowledge counterfactual reductions under a **fixed hypothetical model set**; no experimental costs, no real measurement likelihood, no external model validity, no Bayesian expected-value-of-information claim. If model-form vs cap information has different numerical payoff, it does NOT automatically recommend a cheaper real experiment.
- Report per-group two information reductions, number >5 percentage points, n form better vs cap better (>1e-9 risk difference), per-paper-cluster 95% bootstrap CI (5000 resamples seed 20261015) for 5% certification and positive form/cap perfect-information risk reduction.
- For each definition separately, trace the five optimal catalyst-key paths, exact point switches, returns A-B-A and >1%,>5% consequential switches. A direct comparison of alternative and frozen path topology is secondary.
- Explicitly report where primary 6-scenario and 10-scenario certifications disagree; never replace six-scenario 24/40 with a stronger-looking subset silently.

## Gate and publication

- New implementation files only within existing 'analysis/decision_information_2026_10_15', plus a new 'factorial' GitHub Actions job added to the same read-only workflow. No source/model/manuscript changes. Outputs: 40-group ten-scenario ledger, path audit, JSON summary and limitations in Markdown.
- Test all 310 source rows and 40×10 source winner labels against original ledgers, 10 inversion anchors, economic regret monotonicity, and information reduction inequalities. If the full ten-model test weakens 6-scenario claims, that is the primary result of this extension.
- This paper-conditional exploratory extension is NOT an independent prospectively blinded engineering validation. Scientific review required before manuscript promotion.
