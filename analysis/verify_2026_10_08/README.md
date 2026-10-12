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
| `errata_adjudication.py` | Final class of every rule (error, derived, convention, minor), one root cause per confirmed error, the STY derivation test on TheMeCat and the check that the methanol groups carry the paper values | `errata_adjudication.csv`, `errata_cells_audit.csv`, `errata_adjudication_summary.json`; reads `themecat_v1_subset.csv` (TheMeCat v1 columns used by the STY test, Toldy et al., Sci. Data 2026, CC BY 4.0) |
| `leave_one_paper_out.py` | Methanol field result with the comparisons of one paper removed at a time (Bansode 2013 alone gives 8 of 40), for the S5 primary, the 6.86 % inlet limit and the extended purge grid | `leave_one_paper_out.csv`, `leave_one_paper_out_summary.json` |

## Decisions (author, 2026-10-08)

- Methanol is frozen on the thermodynamically consistent treatment, step S5 of `meoh_decomposition.py`: the
  extraction unit-parsing fixes, the group-basis check and one count per repeated print (S1-S3), recycled CO bounded
  by CO-hydrogenation equilibrium (S4) and the single-pass conversion capped at the loop's CO2-hydrogenation
  equilibrium (S5). The 6.86 % inlet limit (S6) is a sensitivity, not the primary.
- The field results of both methanol and ammonia use printed values only; plot readings enter sensitivity analyses.
- Methanol disagreements are reported separately as other catalyst and other temperature of the same catalyst, each
  with its denominator and with the count whose cost gap exceeds 5 %.
- The frozen scientific-analysis version was implemented and tagged as `freeze/field-2026-10-12`; the final author-confirmed gold-standard source audit is archived additively under `gold_standard_human_review_2026_10_12/`.

- Errata are counted by root cause (one mechanism in one source paper), with rules and cells alongside. TheMeCat's
  STY is the dataset's own derivation (yield x GHSV x CO2 fraction x 32.04 / 24.05 on 704 of 712 rows); a printed STY
  that differs from it is an error only when the yield it uses is wrong or a confirmed input error of the row explains
  the gap.

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
python analysis/verify_2026_10_08/errata_adjudication.py
python analysis/verify_2026_10_08/leave_one_paper_out.py
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
4. Done (2026-10-12, `errata_adjudication.py`): 26 root causes, 45 error rules, 169 value cells and 8 dropped
   records; 18 further rules (24 cells) are STY values derived from a confirmed input error. Counted by root cause,
   rules and cells alongside.
5. **Completed 2026-10-12 (author-confirmed):** 100 sampled methanol fields have been manually reviewed and accepted by the author. See [`gold_standard_human_review_2026_10_12/HUMAN_REVIEW_CONFIRMATION.md`](gold_standard_human_review_2026_10_12/HUMAN_REVIEW_CONFIRMATION.md), the final row-level original-PDF/SI workbook, the CSV evidence export, and preserved audit history. The source workbook's original human signoff columns were not retroactively populated by AI; author completion is recorded separately and explicitly.

## Human gold-standard completion (author confirmation, 2026-10-12)

The author confirmed that manual review of all 100 randomly sampled methanol literature fields is complete and acceptable. The final machine-assisted 100-row source audit and the author's explicit human-review completion record are archived at [`gold_standard_human_review_2026_10_12/`](gold_standard_human_review_2026_10_12/). This does not imply full-dataset 100% accuracy or that all 100 source values are verbatim printed: 91 printed/unit-equivalent, 6 derived ratios, and 3 source-provenance/qualification distinctions. Original sampled values and the frozen field economics are not changed by this documentation update.
