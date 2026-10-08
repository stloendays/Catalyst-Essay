# Verification of 2026-10-08 (advisor review): methanol treatment, printed values, conversion, gold standard, errata

Interpreter: `D:\Research\CatalystForge\.venv\Scripts\python.exe`. Nothing here changes a committed result; every
script reads the committed inputs (and, for the 2026-10-07 physically constrained treatment, commit `86dcd76` of
branch `meoh-physical-lock-2026-10-07` through `git show`).

| Script | Question | Outputs |
|---|---|---|
| `meoh_decomposition.py` | Which change moves the methanol field result from 33/83 (main) to 54/82 (2026-10-07)? Seven steps, each adding one change; all entries and printed values only | `decomposition_steps.csv`, `decomposition_groups.csv`, `decomposition.json`, `cost_cache.csv` |
| `nh3_printed.py` | Ammonia field result on printed rate, temperature and outlet only | `nh3_printed_summary.json`, `nh3_printed_groups.csv` |
| `meoh_conversion_sensitivity.py` | Methanol result when each catalyst may load more catalyst and raise its conversion towards equilibrium | `conversion_sensitivity_*.{json,csv}`; `run1_single_root_solver/` keeps the first run, whose equilibrium conversion came from the single-start solver of `meoh_general_model.equilibrium_co2_conversion` (10 of 284 conditions wrong) |
| `reversal_kinds.py` | Methanol disagreements split into other catalyst (denominator: groups with at least two catalysts) and other temperature of the same catalyst (denominator: groups with a temperature series) | `reversal_kinds.csv`, `reversal_kinds_groups.csv` |
| `gold_standard_sample.py` | Human-checked gold standard: protocol fixed in the docstring, seed 20261008, 100 values from 10 papers | `gold_standard_sample.csv` (+ the checker's workbook outside the repository) |
| `errata_classification.py` | First-pass classification of every correction to TheMeCat, Suvarna 2022 and the Humphreys 2021 review; every row still needs a check against the paper | `errata_classification.csv`, `errata_rules.csv`, `errata_summary.json` |

## Decisions (author, 2026-10-08)

- Methanol is frozen on the thermodynamically consistent treatment, step S5 of `meoh_decomposition.py`: the
  extraction unit-parsing fixes, the group-basis check and one count per repeated print (S1-S3), recycled CO bounded
  by CO-hydrogenation equilibrium (S4) and the single-pass conversion capped at the loop's CO2-hydrogenation
  equilibrium (S5). The 6.86 % inlet limit (S6) is a sensitivity, not the primary.
- The field results of both methanol and ammonia use printed values only; plot readings enter sensitivity analyses.
- Methanol disagreements are reported separately as other catalyst and other temperature of the same catalyst, each
  with its denominator and with the count whose cost gap exceeds 5 %.
- Nothing here is frozen yet; the frozen version will be implemented in the analysis code and tagged.
