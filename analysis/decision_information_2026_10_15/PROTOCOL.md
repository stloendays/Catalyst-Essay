# Protocol | robust catalyst decisions and discrete ranking-boundary topology (2026-10-15)

**Committed before any new research code/output.** These are model-conditional, retrospective analyses on the existing, immutable 40-group published methanol cohort. They do not establish which industrial inlet cap or which chemical-species definition is physically correct, nor constitute validation against a new plant.

## Motivation and falsifiable questions

Previously: S5 STY leaders disagree with plant selection in 15/40, S6 (cap CH4+CO+N2 at 6.86%) in 28/40, alternative CH4+N2 cap in 18/40. Model-aware predictors in draft PR #100 did not beat selectivity. Can a single candidate be chosen under explicitly unknown engineering assumptions while controlling **worst-case economic regret**, and do optimal catalyst identities switch non-monotonically as reactor-inlet cap is relaxed?

This is a mathematical *decision-support certificate under a specified uncertainty set*, not an agent speedup, Bayes expected value of information, or physical claim that CO is an inert molecule. Recycled CO is reactive; the two model constraints are treated as different engineering policy choices.

## Fixed source contract

- Read-only original cohort from 'analysis/meoh_literature_inversion_2026_10_05/literature_candidates.csv' (351 printed records), restricted to the frozen 40 scored groups, 310 candidate operating-point entries and 28 DOI papers from 'group_metrics_inlet_limit.csv'. There are 41 unscored singleton groups.
- Canonical group-level source tie choices and score anchors from 'analysis/meoh_constraint_boundary_2026_10_12/boundary_groups.csv'. Use **original row index** plant_idx to recover ties exactly and verify its constrained cost against the minimum candidate cost in the original CSV. The source STY leader is the S5 lab_idx. Preserve candidate identity as (group, original entry); record catalyst_key as formulation family.
- Alternate CH4+N2-only model: 'analysis/meoh_inlet_definition_2026_10_12/entry_costs.csv', align by (group,entry) and 'scan_groups.csv' (definition=true_inert, limit=6.86); use ledger's original plant_leader to recover tie resolution and independently assert its minimum cost.
- Required anchors: 40 distinct groups, 310 candidates, 28 papers; S5=15/40, S6=28/40 and alternate form=18/40 STY reversals (each source's native tie convention); no change to frozen source rows.
- Canonical scenarios explicitly ordered by increasing allowed inlet CH4+CO+N2: **lim5, lim6, S6 (6.8625%, corresponding frozen cost_recycled_opt_inlet), lim8, lim10**. No inference that 5-10% is a verified physical plausibility range; it is the previously declared engineering comparison envelope.
- Structural-scope augmented set is exactly those 5 canonical cap scenarios plus **true_inert_S6** (at approximately 6.86%, CH4+N2-only). This is asymmetric; the alternate form is available at the 6.86% limit only. Do NOT infer what the alternative would do at 5%,6%,8%,10% without running those alternate cases.
- A separate fixed **two-form reference** compares canonical S6 vs true_inert_S6 only. Wider 12-scenario sensitivity is descriptive and must not redefine the primary set.

## Study A: scenario-robust candidate decisions (primary)

- For each within-paper group g and scenario s, define the attainable optimum J*(g,s) as the minimum strictly-positive finite source cost across the same ORIGINAL candidates. For any candidate i, regret R(i,s)=J(i,s)/J*(g,s)-1 if finite, else R=+infinity; check R>=-1e-6 (clamp numerical ~0 to 0).
- Do not omit an infeasible candidate from STY/selection/S5 baseline; a candidate infeasible in one scenario has infinite worst-case regret.
- Within a specified scenario set S, choose *one existing operating-point entry*, not a different per-scenario candidate, to minimize max_s R(i,s). Tie broken by original row order; no post hoc epsilon retuning. **Primary minimax set** S=5 canonical caps + one alternative at 6.86%. Three secondary sets: five canonical caps only; two-form reference only; all twelve published canonical scenarios (lim4,5,6,S6,8,10,12,15,20,25,30 and S5).
- Baseline fixed decisions: published S5/STY leader (original lab_idx), methanol selectivity leader (max SMeOH, tie max STY, then original row order), S5 cost leader (original plant_idx), canonical-S6 cost leader (original plant_idx), and alternative true-inert6.86 cost leader (its source ledger). Score each baseline by *the same* scenario max-regret metric, accounting for any infeasible entry as +infinity.
- Report per group: robust winner entry/catalyst_key, maximum regret; worst-regret case; STY/S5/S6/alt baseline worst regret, number of scenarios in which robust winner actually wins, robust risk 5% acceptance and all-model common feasible counts; tie count at exactly minimum risk; cost winner vs formulation winner separately. Summary: 40-group coverage with worst regret <=5%, <=10%, zero to tolerance 1e-7, no common feasible group count, per-method median finite worst regret and infeasible worst-risk number, with and without DOI Bansode 10.1039/c2cy20604h.
- Distinguish in-sample mathematical optimizer (uses full scenario cost oracle during **decision calculation**) from future predictive/field-deployable rule. No direct predictive claim or experimental cost saving.
- Robust identification sensitivity: label a candidate 'decision-equivalent' if its max regret <=5% (not exactly the single cheapest), report count/choice-set stability and material formulation diversity. 5% is fixed from the original manuscript's decision-relevant regret threshold, not tuned after the analysis.
- The economic objective is the source's *model-responsive cost per tonne*, NOT a complete independently validated plant cash cost. Worst-case across scenarios is a conservative mathematical set criterion, not a probability or expected risk.
- Paper-cluster 95% percentile bootstrap: 5000 resamples of 28 papers (seed 20261015) for robust <=5% coverage and proportion of groups materially sensitive to model identity. Conditioned on the entire specified scenario set, no new physical uncertainty is represented.

## Study B: information-resolution upper bounds

Define r_full(g)=min_i max_{s in augmented six} R(i,s), r_cap(g)=min_i max_{s in canonical five} R(i,s), and r_form(g)=min_i max_{s in {S6,true_inert_S6}} R(i,s).

- **Reveal model-form identity** counterfactual for the augmented six scenarios: optimal policy chooses a robust cap-only candidate if "CO included" and the alternate-form scenario winner if "CH4+N2-only" (latter only has 6.86% published). Residual worst-case regret =r_cap; mathematical reduction (r_full-r_cap)>=0. Source-form identity resolution does NOT remove cap uncertainty under canonical model. The comparison is asymmetric and is not a field-measured cost or an experimental-information acquisition.
- **Reveal exact cap** counterfactual within canonical five: per-cap optimum gives zero relative regret. The mathematically available reduction of worst-case regret under a perfect information oracle is r_cap; it is an **upper bound** on any imperfect measurement at unspecified cost.
- **Reveal form** under the two-form-at-6.86 reference reduces the worst-case regret to zero, with reduction r_form.
- No probability distribution over scenarios, no information-observation model, no price/time/cost for measuring model identity. Thus report **perfect-knowledge worst-case regret reduction**, never Bayesian expected value of information (EVI) or recommendations to commission an experiment based on numerical EVI.
- Require nesting r_full >= r_cap >= 0 and r_full >= r_form >=0; report how often form knowledge changes the robust minimax choice and where it materially (>5 percentage points) reduces risk.

## Study C: discrete optimal-path topology (secondary, mechanistic)

- Verify for *each scored entry* that model J_i(s) is nonincreasing as the inlet cap is relaxed in canonical ordered 5 scenarios, with the correct convention for previously infeasible states. Numerical relative tolerance=1e-6; any actual monotonicity violation FAILS the study.
- From the frozen per-scenario plant_idx winners, construct each group's **exact operating-point path** and **material-key path** along the five caps. Count unique point winners, changes, and returns A-B-A (point, material separately). Since a numeric tie can cause a switch of zero economic significance, mark each consecutive switch economically material only if retaining the previous winner at the new cap incurs >1% relative regret. Also provide >5% thresholds.
- Report all four adjacent cap intervals separately (5->6,6->6.86,6.86->8,8->10), and a per-group path ledger with scenario-optimum cost and winner. Count paper-level distribution; flag if a qualitative mechanism disappears when excluding Bansode.
- "Each candidate's optimal cost is monotone with a relaxed nested constraint" is compatible with "winning candidate can switch non-monotonically"; this is a **numerical result over these source scenarios**, not a theorem for arbitrary reaction models. If no material re-entrance occurs, explicitly state the negative finding.

## Engineering and scientific promotion gate

- New folder 'analysis/decision_information_2026_10_15/' only, plus one read-only GitHub workflow '.github/workflows/decision-information-2026-10-15.yml'. Standard-library Python, deterministic, independent tests, GitHub Actions upload CSV/JSON/Markdown artifacts including failures. Code and data pins/frozen manuscript unchanged.
- Separate jobs for robust model-information decisions and cap-transition path topology; no external web fetching or API keys needed. The original frozen optimizer and old PR #99/#100 remain entirely unchanged.
- This is an exploratory extension, not yet ready for manuscript promotion. Explicitly record disappointing/zero-information results.
