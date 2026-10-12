# Independent Fe-reference denominator audit for actual Ru/C

Read-only QA. This directory does **not** change the ammonia model,
experimentally assumed Ru loading/recovery, frozen ammonia states, figures,
source CSVs, author manuscript or SI.

## Why a second Fe comparator matters

The canonical \`fig2_ru_actual_cost_points.csv\` uses
\`gap_to_Fe = Ru_cost - Fe_main_loop_optimum\` for *all* rows, including
a Ru catalyst evaluated in the 90 bar KAAP loop and the \`fe_kaap\` row itself.

Comparing catalysts **within the same KAAP operating envelope** instead
requires \`Ru_cost_KAAP - Fe_cost_KAAP\`, the convention already used by
the separate supported-bed sensitivity table. Confusing the two comparisons
can invert the sign of the Ru/Fe difference even though the underlying
plant-cost calculations are identical.

## Audit

~~~bash
python -m unittest discover -s analysis/review_ru_cost_2026_10_09/tests -v
python analysis/review_ru_cost_2026_10_09/ru_cost_reference_audit.py \
  --out-dir /tmp/ru_cost_reference_audit --strict
~~~

It checks:

- which Fe baseline every stored cost difference corresponds to;
- the global/loop-matched gap arithmetic for canonical Ru points;
- source-table parity against \`fig2_ru_bed_sensitivity.csv\`;
- every R_all own-bed entry in \`fig3d_readings.csv\` against the frozen
  grid: Ru 5/8/10 wt%, recoveries 90/97%, densities 430/550 kg/m3,
  in both plant loops;
- the 8 wt% range and the fraction of corner cases favoring Ru.

Outputs: \`ru_reference_audit_summary.json\` and \`ru_reference_gaps.csv\`,
only in the caller's scratch directory. Published metrics remain untouched.

This script proves **internal source-data consistency**, not external
experimental validation of commercial Ru loading or metal recovery, and not
a claim that catalyst-dependent costs are full-plant ammonia production costs.
The intended comparison should be stated explicitly before the author
finalizes Figure 3d and its Source Data.
