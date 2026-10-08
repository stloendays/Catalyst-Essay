# Verification of 2026-10-08 (advisor review): methanol treatment, printed values, conversion, gold standard, errata

Interpreter: Python 3.12 with `requirements.txt` and `pyyaml` (locally `D:\Research\CatalystForge\.venv\Scripts\python.exe`).
The report in Chinese is [`REPORT_zh.md`](REPORT_zh.md). Nothing here changes a committed result; every
script reads the committed inputs (and, for the 2026-10-07 physically constrained treatment, commit `86dcd76` of
branch `meoh-physical-lock-2026-10-07` through `git show`).

| Script | Question | Outputs |
|---|---|---|
| `meoh_decomposition.py` | Which change moves the methanol field result from 33/83 (main) to 54/82 (2026-10-07)? Seven steps, each adding one change; all entries and printed values only | `decomposition_steps.csv`, `decomposition_groups.csv`, `decomposition.json`, `cost_cache.csv` |
| `nh3_printed.py` | Ammonia field result on printed rate, temperature and outlet only | `nh3_printed_summary.json`, `nh3_printed_groups.csv` |
| `meoh_conversion_sensitivity.py` | Methanol result when each catalyst may load more catalyst and raise its conversion towards equilibrium | `conversion_sensitivity_*.{json,csv}`; `run1_single_root_solver/` keeps the first run, whose equilibrium conversion came from the single-start solver of `meoh_general_model.equilibrium_co2_conversion` (10 of 284 conditions wrong) |
| `reversal_kinds.py` | Methanol disagreements split into other catalyst (denominator: groups with at least two catalysts) and other temperature of the same catalyst (denominator: groups with a temperature series) | `reversal_kinds.csv`, `reversal_kinds_groups.csv` |
| `gold_standard_sample.py` | Human-checked gold standard: protocol fixed in the docstring, seed 20261008, 100 values from 10 papers | `gold_standard_sample.csv`, `gold_standard_sample.xlsx` (the workbook the checker fills in; PDF and SI file names refer to `agent/extraction/pdf` and `agent/extraction/si`, which are not in git) |
| `compare_outputs.py` | Compares regenerated outputs with the committed ones (counts and labels exactly, floats to a tolerance) | used by `.github/workflows/verify-2026-10-08.yml` |
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

## Reproducing in the cloud

`.github/workflows/verify-2026-10-08.yml` reruns every script on a clean runner (push to `verify-2026-10-08` touching
this folder, or manual dispatch) and compares the outputs with the committed ones. The ammonia job builds the harness
root from `provenance/` with `analysis/nh3_actual_ru_params_2026_10_07/build_harness_root.py`; nothing else outside the
repository is needed. Run order locally:

```bash
python analysis/verify_2026_10_08/meoh_decomposition.py          # ~5 min on 4 workers
python analysis/verify_2026_10_08/meoh_conversion_sensitivity.py # ~30 min on 4 workers
python analysis/verify_2026_10_08/reversal_kinds.py
NH3_HARNESS=<harness root> python analysis/verify_2026_10_08/nh3_printed.py
python analysis/verify_2026_10_08/errata_classification.py
python analysis/verify_2026_10_08/gold_standard_sample.py analysis/verify_2026_10_08/gold_standard_sample.xlsx
```

Unfinished local worktree states of 2026-10-07 are kept as tags `archive/wip-text-fixes-2026-10-07` and
`archive/wip-fix-meoh-2026-10-07` (superseded by PR #37 and by the Actions statistics run; not part of any result).

## Next steps

1. Implement the frozen version in the analysis code: step S5 (with S1-S3) for methanol, printed values only for both
   field results, the other-catalyst / other-temperature split; tag it.
2. Regenerate figures, Extended Data, Supplementary Tables (5f still carries the 2026-10-07 numbers) and Source Data
   from the tag; correct the text and table issues listed in `REPORT_zh.md` section 7.
3. Extended Data Fig. 4: separate catalyst-independent and catalyst-sensitive terms; explain the carbon-efficiency gap.
4. Confirm every erratum in `errata_rules.csv` against the paper; count errors, report cells alongside.
5. The gold standard is filled in by hand in `gold_standard_sample.xlsx`.
