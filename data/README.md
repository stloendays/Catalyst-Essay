# Data snapshot

This directory contains compact, human-readable snapshots of the current project state for the public essay repository.

These files are **not** replacements for the frozen computational harness, raw model outputs, or full benchmark traces. They exist so that the headline results in the README can be inspected in a machine-readable form.

## Files

- `canonical_results_2026-09-06.csv` — current NH3-FINAL-1.1 scientific results and cross-reaction leverage values.
- `discover_benchmark_2026-09-06.csv` — current formal DISCOVER benchmark summary.
- `rank_preservation_control_v1_1.csv` — literature-calibrated Au/TiO2 CO-oxidation rank-preservation control: particle size, mass activity, required catalyst mass, required Au mass, and burden relative to the best state.
- `cross_model_scores_2026-09-06.csv` — DISCOVER cross-model scores per model × variant × budget (policy E on gpt-5.4-nano, gpt-5.4-mini, gpt-5.5; frozen A–D baselines).
- `cross_model_failure_matrix_2026-09-06.csv` — 19 failure modes × model × variant × budget.
- `cross_model_stats_2026-09-07.csv` — Wilson CIs, Fisher exact, Cochran–Armitage trend, logistic regression, Mann–Whitney/bootstrap, pre-registered Go check (long format; `section` column).
- `cross_model_metadata_2026-09-06.json` — run metadata: exact model IDs, token totals, 0 retries / 0 driver exceptions, frozen-hash checks PASS before and after.
- `discover_frozen_v1_hashes.json` — the 15 SHA-256 hashes that define DISCOVER V1.
- `cross_model_analysis.py`, `cross_model_stats.py`, `cross_model_stats_figure.py` — the read-only analysis scripts (copied from the harness; they run against the harness directory, not against this repository).

The repository should use NH3-FINAL-1.1 values for current ammonia claims. NH3-FINAL-1.0 is historical only.
