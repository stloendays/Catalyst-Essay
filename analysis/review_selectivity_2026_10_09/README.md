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
