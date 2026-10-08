# Verification of 2026-10-08 (advisor review): methanol treatment, printed values, conversion, gold standard, errata

Interpreter: `D:\Research\CatalystForge\.venv\Scripts\python.exe`. Nothing here changes a committed result; every
script reads the committed inputs (and, for the 2026-10-07 physically constrained treatment, commit `86dcd76` of
branch `meoh-physical-lock-2026-10-07` through `git show`).

| Script | Question | Outputs |
|---|---|---|
| `meoh_decomposition.py` | Which change moves the methanol field result from 33/83 (main) to 54/82 (2026-10-07)? Seven steps, each adding one change; all entries and printed values only | `decomposition_steps.csv`, `decomposition_groups.csv`, `decomposition.json`, `cost_cache.csv` |
| `nh3_printed.py` | Ammonia field result on printed rate, temperature and outlet only | `nh3_printed_summary.json`, `nh3_printed_groups.csv` |
| `meoh_conversion_sensitivity.py` | Methanol result when each catalyst may load more catalyst and raise its conversion towards equilibrium | `conversion_sensitivity_*.{json,csv}`; `run1_single_root_solver/` keeps the first run, whose equilibrium conversion came from the single-start solver of `meoh_general_model.equilibrium_co2_conversion` (10 of 284 conditions wrong) |
| `gold_standard_sample.py` | Human-checked gold standard: protocol fixed in the docstring, seed 20261008, 100 values from 10 papers | `gold_standard_sample.csv` (+ the checker's workbook outside the repository) |
| `errata_classification.py` | First-pass classification of every correction to TheMeCat, Suvarna 2022 and the Humphreys 2021 review; every row still needs a check against the paper | `errata_classification.csv`, `errata_rules.csv`, `errata_summary.json` |
