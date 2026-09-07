# Data snapshot

This directory contains compact, human-readable snapshots of the current project state for the public essay repository.

These files are **not** replacements for the frozen computational harness, raw model outputs, or full benchmark traces. They exist so that the headline results in the README can be inspected in a machine-readable form.

## Files

- `canonical_results_2026-09-06.csv` — current NH3-FINAL-1.1 scientific results and cross-reaction leverage values.
- `discover_benchmark_2026-09-06.csv` — **strong-tier formal DISCOVER V1 precursor snapshot**. It records the original 70 policy-E runs and A-D comparison; it is not the final cross-model Agent claim.
- `rank_preservation_control_v1_1.csv` — literature-calibrated Au/TiO2 CO-oxidation rank-preservation control: particle size, mass activity, required catalyst mass, required Au mass, and burden relative to the best state.
- `cross_model_scores_2026-09-06.csv` — current DISCOVER cross-model scores per model × variant × budget (policy E on gpt-5.4-nano, gpt-5.4-mini, gpt-5.5; frozen A-D baselines).
- `cross_model_failure_matrix_2026-09-06.csv` — 19 failure modes × model × variant × budget.
- `cross_model_stats_2026-09-07.csv` — Wilson CIs, Fisher exact, Cochran–Armitage trend, logistic regression, Mann–Whitney/bootstrap, and the pre-registered E-vs-D Go check (long format; `section` column).
- `cross_model_metadata_2026-09-06.json` — run metadata: exact model IDs, token totals, 0 retries / 0 driver exceptions, frozen-hash checks PASS before and after.
- `discover_frozen_v1_hashes.json` — the SHA-256 pins defining DISCOVER V1. Any change to a pinned protocol component defines V2; V1 failures are retained rather than tuned away.
- `cross_model_analysis.py`, `cross_model_stats.py`, `cross_model_stats_figure.py` — read-only analysis scripts copied from the harness; they run against the harness directory, not against this repository.

### Current Agent evidence hierarchy

For manuscript-level Agent claims, use the evidence in this order:

1. `discover_frozen_v1_hashes.json` and the frozen V1 protocol;
2. per-trace scores / failure records in the full harness;
3. `cross_model_stats_2026-09-07.csv`;
4. `cross_model_scores_2026-09-06.csv` and `cross_model_failure_matrix_2026-09-06.csv`;
5. README / manuscript summaries.

The current anonymous complete-decision counts are **6/35 (nano), 15/35 (mini), 35/35 (strong)**. The pre-registered claim that adaptive policy E robustly outperforms fixed-VOI D is **not met across tiers** and must remain a negative result.

The repository should use NH3-FINAL-1.1 values for current scientific claims. NH3-FINAL-1.0 is historical only.
