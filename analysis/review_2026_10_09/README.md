# Independent methanol comparison audit

This directory contains a **read-only QA check**, intentionally separate from the
working decomposition, thermodynamic model, conversion sensitivity and manuscript.
It is designed for parallel review without touching the local author's worktree.

## Inputs

The script reads existing \`analysis/verify_2026_10_08/conversion_sensitivity_points.csv\`
and \`conversion_sensitivity_groups.csv\`. It does **not** recalculate costs or
change the primary source-of-truth. The defaults select \`thermo + printed\` and
compare laboratory conversion with conversion optimisation to 0.95 times the
equilibrium limit. All resulting numbers remain provisional until author
verification and repository freeze.

## Run

~~~bash
python -m unittest discover -s analysis/review_2026_10_09/tests -v
python analysis/review_2026_10_09/field_comparison_audit.py \
  --out-dir /tmp/meoh_audit --strict
python analysis/review_2026_10_09/field_comparison_audit.py \
  --out-dir /tmp/meoh_audit_all --mode all
~~~

Outputs go only to the chosen output directory:
\`audit_summary.json\` (denominators/counts/anomalies) and
\`audit_groups.csv\` (case-level leader temperatures and classifications).

## Checks and interpretation

- Count a *temperature series* only when the **same catalyst identity has at
  least two genuinely different temperatures** (default tolerance 0.05 °C);
  repeated rows at one temperature do not suffice.
- Keep four mutually exclusive mismatch classes:
  \`different_catalyst_same_temperature\`,
  \`different_catalyst_and_temperature\`,
  \`same_catalyst_different_temperature\`, and
  \`same_catalyst_same_temperature_different_record\`.
- Treat missing/ambiguous leader temperature as an explicit audit error rather
  than inferring temperature from a table label.
- Preserve the manuscript's **different-catalyst** numerator across both
  different-catalyst classes, but disclose joint temperature changes when
  describing the mechanism. Never call a joint change a purely
  catalyst-driven inversion.
- Count cost regrets exceeding 5% with the existing strict \`> 0.05\` rule.

This audit verifies classification of *existing observations*. It **cannot**
demonstrate that the cost model, catalyst-label normalization or earlier
candidate de-duplication is physically correct. Its role is to expose those
unknowns for an independent author/Claude review before results are frozen.


## Paired stage-transition audit

Use the complementary \`paired_transition_audit.py\` to join the *same
comparison group* before and after allowing catalyst inventory to change:

~~~bash
python analysis/review_2026_10_09/paired_transition_audit.py \
  --out-dir /tmp/meoh_paired_audit --strict
~~~

The paired audit records:
- retained, newly appearing, and disappearing ranking disagreements;
- material-to-temperature and temperature-to-material type switches;
- winner changes combining material **and** temperature, separately from
  strictly isothermal material changes;
- >5% cost-regret counts before and after, plus concentration by DOI;
- unchanged laboratory STY leader and fixed candidate-group eligibility.

It uses existing output tables only. Group-by-group transitions must be
interpreted as model sensitivity outcomes, not as causal evidence that any
single catalyst property caused a particular inversion. GitHub Actions uploads
both audit reports as temporary reviewer artifacts; no headline or manuscript
results are overwritten.
