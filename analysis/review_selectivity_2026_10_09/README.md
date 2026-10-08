# Independent selectivity provenance audit

This is a **read-only QA tool** for the author's printed-value methanol
comparison cohort. It is separate from the reactor model, paper-leaderboard
builder, numerical freeze, manuscript and gold-standard workbook.

## Scientific question

Does a primary cohort described as "printed values only" contain *modeled
carbon-selectivity allocations* even though the relevant CO or CH4 component
was not reported in print? When CO **is** printed, how often does the
carbon-closure convention nevertheless allocate it as the remainder?

The extant candidate-builder has the conventions:

- if CH4 is absent but CO is given, CH4 is assigned the remaining carbon;
- if CH4 is absent and CO is also absent, CH4 is assigned zero;
- CO is ultimately assigned by carbon closure
  \`S_CO = 1 - S_MeOH - S_CH4\`;
- even when a CO selectivity was printed, its reported value does not
  necessarily equal the value passed to the plant model.

These conventions may be defensible assumptions, but they should not be
described as direct measurements.

## Source contract

The original extraction rows are loaded by \`git show\` from commit
\`86dcd76218e2fd5218d6da74e8f6092c0f1c2f3c\` (the same input pinned
in the S5 verification), not from the potentially different main branch.

The two downstream inputs are the **existing** \`conversion_sensitivity_points.csv\`
and \`conversion_sensitivity_groups.csv\`. No model or ranking calculation is
rerun; results are **not frozen**.

## Execution

~~~bash
python -m unittest discover -s analysis/review_selectivity_2026_10_09/tests -v
python analysis/review_selectivity_2026_10_09/selectivity_source_audit.py \
  --out-dir /tmp/selectivity_source_qa
~~~

The output directory receives:

- \`selectivity_source_summary.json\`: denominator, printed-versus-completed
  counts, percentage-point deviations from printed CO, leader exposure;
- \`selectivity_source_candidates.csv\`: source fields and closure flags by
  candidate, for targeted manual checking;
- \`selectivity_source_groups.csv\`: which ranking comparisons are affected
  at the laboratory and adjustable-catalyst-inventory levels.

*Do not conflate* the number of leaderboard changes with the number of
causally attributable catalyst-choice reversals. This audit diagnoses source
provenance, not economic truth or whether any closure assumption is reasonable.

The human gold-standard and all claimed errata remain an author's manual
validation task. Nothing generated here should automatically become a
published correction or a new abstract statistic.


## Candidate-completeness reranking without new plant solves

The companion \`selectivity_subset_rerank.py\` filters the existing
S5+printed candidate states and compares three distinct evidence cohorts:

1. **Printed X and MeOH selectivity:** the author's intended primary set.
2. **Both CO and CH4 printed:** permits numeric upper bounds ("<", "<=").
3. **Both CO and CH4 explicitly numeric and consistent:** requires equality
   ("=") reporting and modeled-versus-reported component differences within
   one percentage point, allowing ordinary rounding.

Within each cohort, a comparison group is retained only if it has at least
two eligible existing points. The STY and cost winners are recomputed with
the same upstream tie rule as the original analysis. *Only already computed
costs are used*:

~~~bash
python analysis/review_selectivity_2026_10_09/selectivity_subset_rerank.py \
  --out-dir /tmp/selectivity_source_qa --strict
~~~

The tool first checks that its **full-cohort recomputation agrees with the
existing leaderboard** before interpreting either restricted cohort. It
reports denominators and individual cases; an apparent change in disagreement
fraction may reflect cohort attrition. The strict cohort is an **evidence
quality sensitivity**, not a replacement of the author's selected S5 cohort.
More rigorous tests of assumptions for unreported products require
recalculating the plant costs under alternative product distributions and
are not performed here.
