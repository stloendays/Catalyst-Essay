# Ammonia within-paper field sample, batch 2: pre-registered, out-of-sample (2026-10-12)

Protocol: `PROTOCOL.md` (commit a04c3e9, before any extraction). Every number below is in `report_numbers.json`
(`report_numbers.py` collects it from the run folders); per-group detail is in `runs/<set>/group_metrics_printed.csv`.

## Result (printed-value primary, frozen definition)

| | Round 1 (frozen) | **Batch 2** | **Pooled (round 1 + batch 2)** |
|---|---:|---:|---:|
| Papers screened / included | 30 chosen / 30 | 25 / 19 | 55 / 49 |
| Papers with ≥ 1 scored group | 23 | 3 | 26 |
| Groups scored (entries) | 33 (139) | 5 (16) | 38 (155) |
| **Laboratory leader ≠ plant-cost leader** | **7 (21.2 %)** | **2 (40 %)** | **9 (23.7 %)** |
| 95 % CI (paper-cluster bootstrap) | 7.1–36.7 % | 0–100 % | **11.1–37.8 %** |
| Mismatches with regret > 5 % (papers) | 4 (3) | 2 (2) | 6 (5) |
| Papers contributing disagreements | 6 | 2 | 8 |
| Paper-weighted share (CI) | 19.9 % (5.8–36.2 %) | 44.4 % (0–100 %) | 22.8 % (8.7–39.1 %) |
| Regret of mismatched groups, median / max | 10.0 % / 31.5 % | 15.4 % / 25.4 % | 10.0 % / 31.5 % |
| Cross-metal groups (papers); of them mismatched | 4 (3); 4 | 2 (1); 1 | 6 (4); 5 |
| Mismatch kinds: different metal / fused-Fe reference / same metal and content / different content | 3 / 2 / 1 / 1 | 0 / 1 / 1 / 0 | 3 / 3 / 2 / 1 |

CI method (frozen, `run_field_chain.aggregate`, `boot=True`): 10,000 resamples of the papers with replacement, seed
20261006, 2.5th–97.5th percentiles of the share of groups with a different winner. With three scored papers the batch-2
interval spans 0–100 %.

Round 1 reproduced exactly through the wrapper before batch 2 was scored (`runs/round1_regression/`): 7/33, 6/23 papers.
`summary.json`, `summary_printed.json`, `candidates.csv`, `candidates_printed.csv`, `group_metrics.csv` and
`group_metrics_printed.csv` are byte-identical to the frozen files. The Humphreys-chain self-check passes (548 values,
max. rel. diff. 0). Its CSV differs from the frozen copy in the reference column only: 12 values of 2 rows, because
`analysis/nh3_supported_2026_10_06/supported_candidates.csv` was updated after the frozen run (commit 7e96397).

### The five batch-2 groups

| Group | n | Paper leader (USD/t) | Plant leader (USD/t) | Regret | Kind |
|---|---:|---|---|---:|---|
| Zheng 2019 (Angew., 10.1002/anie.201907171), 459 °C, 1 MPa | 3 | Ba-Ru-Li/AC, 4.8 wt% Ru (22.16) | Mittasch's Fe (17.67) | 25.4 % | fused-Fe reference vs supported catalyst |
| Abe 2017 (J. Phys. Chem. C, 10.1021/acs.jpcc.7b07268), 340 °C, 0.1 MPa | 2 | Ru/Ca₂NH, 0.1 wt% (27.18) | Ru/CaNH, 0.1 wt% (25.79) | 5.4 % | same metal and metal content |
| Zheng 2019, 400 °C, 1 MPa | 2 | Ba-Ru-Li/AC | same | 0 | – |
| Zheng 2019, 459 °C, 5 MPa | 4 | Ru-Li/MgO | same | 0 | – |
| Ogura 2018 (ACS Sustain., 10.1021/acssuschemeng.8b04683), 400 °C, 1 MPa | 5 | Ru/La₀.₅Pr₀.₅O₁.₇₅_650red | same | 0 | – |

The chain treats Mittasch's Fe as the commercial fused-iron reference: 71.51 wt% at 2,500 kg m⁻³, its frozen rule. The
paper prints L = 40.5 for that catalyst.

## Variants (as in the frozen summary): groups with a different winner / groups (papers with one / papers), CI

| Variant | Round 1 | Batch 2 | Pooled |
|---|---|---|---|
| Rate per g catalyst | 7/33 (6/23), 7.1–36.7 % | 2/5 (2/3), 0–100 % | 9/38 (8/26), 11.1–37.8 % |
| Rate per g metal | 10/33 (7/23), 12.9–48.5 % | 2/5 (2/3), 0–100 % | 12/38 (9/26), 15.6–47.5 % |
| 90 % Ru recovery | 7/33 (6/23), 7.1–36.7 % | 2/5 (2/3), 0–100 % | 9/38 (8/26), 11.1–37.8 % |
| Bed density 500 kg m⁻³ | 7/33 (6/23) | 2/5 (2/3) | 9/38 (8/26) |
| Bed density 2,500 kg m⁻³ | 5/33 (4/23) | 2/5 (2/3) | 7/38 (6/26) |
| Commercial fused-Fe references removed | 5/33 (4/23), 3.2–29.0 % | 1/5 (1/3), 0–100 % | 6/38 (5/26), 3.3–29.3 % |
| Measured at ≥ 5 MPa | 1/4 (1/4), 0–75 % | 0/1 (0/1) | 1/5 (1/5), 0–60 % |
| Without the paper with the most groups | 6/29 (5/22) | 1/2 (1/2) | 8/34 (7/25) |
| All entries (plot readings included) | 44/124 (13/28), 18.4–52.4 % | 4/28 (4/9), 2.8–40.0 % | 48/152 (17/37), 17.0–46.7 % |

Sensitivities (all identical to the primary at 2/5 for batch 2 and 9/38 for the pool):
- uncorrected records (`runs/batch2`, `runs/pooled_uncorrected`);
- the frozen normaliser's unparsed units converted (below; `runs/batch2_corrected_units`, `runs/pooled_units`);
- one chain run over the concatenated round-1 + batch-2 records, so the median NH₃ fraction is taken over the pool
  (`runs/pooled_single_chain`).

## Batch-2 pipeline counts

- **Screening** (`batch2_screening.csv`; main text only, see SI below): 25 screened, 19 included, 6 excluded:
  - Jafari 2019 (10.1007/s11144-018-1498-6): the Fe content of the fused catalysts is not stated.
  - Hasegawa 2018 (10.1021/acs.chemmater.8b01819): no H₂/N₂ ratio stated.
  - Lu 2018 (10.1021/acscatal.8b03743): no H₂/N₂ ratio stated.
  - Nat. Catal. 2021 (10.1038/s41929-021-00695-x): a 2-page Research Briefing with no metal loading.
  - Wu 2020 (10.1039/c9cc07385j): the Ru loading is in the ESI only.
  - Luz 2020 (10.1039/c9cy01303b): the Ru content is given only as "up to 80 wt%", and the rates are in the ESI.

  Two inclusions were close calls:
  - Wang 2017 (10.1002/anie.201703695): the loading is given as an Fe:LiH molar ratio.
  - Zhang 2019 (10.1021/acssuschemeng.9b04929): the Ru loading is given as a range, 0.4–1.0 wt%.
- **Extraction** (`agent/nh3_field/out_batch2/`):
  - Pass-level records: main 336, figures 529, SI 0. They merge into 513 entries from 19 papers (336 main, 177
    figures-only).
  - Chain: 209 entries mapped. 304 entries are outside: 289 without a metal content, 170 without a rate per g
    catalyst, 44 without a single model metal; an entry can have several reasons.
  - 147 primary entries with a cost and 61 flagged. After one entry per catalyst and measurement, 128 primary entries
    from 13 papers (19 removed as duplicates) and 28 groups in 9 papers.
  - Printed values: 28 entries; 16 of them fall in the 5 scored groups.
  - The set's median NH₃ fraction is 0.084 % (round 1: 0.31 %).
- **Unparsed units** (frozen `normalize.py`, unchanged for the primary): 64 rates ("mmol-NH3/g-cat/h", Javaid 2019;
  "gNH3 gC+Co⁻¹ h⁻¹", Tarka 2015) and 22 space velocities ("72 L h⁻¹ per gram of catalyst", Ogura 2018).
  `batch2_unit_completions.csv` converts them (86 values) for the sensitivity, which leaves the result unchanged. The
  normaliser also skipped 8 "normalized rate" values and 5 "% NH₃-yield" values; that is correct, because neither is a
  rate or an outlet concentration.

## Accuracy check (AI-assisted)

`batch2_pdf_check.csv`: a random sample (seed 20261012, `pdf_check_sample.py`) of 40 of the 124 printed values that
enter the batch-2 primary. The sample holds 12 P, 10 metal wt%, 9 rates, 6 T and 3 WHSV values. Two Claude agents
checked each value against the cited page text and image, including the conversion to model units.

**39/40 correct (0.975, 95 % CI 0.87–1.00, Clopper–Pearson).** The one wrong value: Qiu 2019 (10.1021/acs.chemmater.9b03099)
prints 0.27 wt% Ru only for the parent Ru SAs/S-1, and the extraction carried it over to Ba-Ru SAs/S-1.
`batch2_corrections.csv` blanks that loading in both Ba-Ru SAs/S-1 entries (648 and 673 K), which are 2 corrections,
and the scoring wrapper applies the file (`runs/batch2_corrected`). The correction changes no group.

None of the checked papers says whether a pressure above 0.1 MPa is gauge or absolute.

## SI, tokens and cost

- **SI:** not retrieved for any of the 25 candidates. `fetch_si.py` through nus-fetch failed with "EZproxy session not
  logged in" (`fetch_si_batch2.log`); no login was automated. The si and si_figures passes therefore had no input, and
  screening and extraction used the main text only (round 1 had SI for 28 of 30 papers).
- **Tokens** (`agent/nh3_field/out_batch2/token_usage.csv`): 38 logged calls, 1,508,600 tokens (30 % of the 5 M cap):

  | Pass | Calls | Tokens | Records |
  |---|---:|---:|---:|
  | main | 19 | 722,212 | 336 |
  | figures | 19 | 786,388 | 529 |
  | **Total** | **38** | **1,508,600** | **865** |

  The total splits into 904,136 prompt and 604,464 output tokens (73,584 of them reasoning). At USD 5 / 30 per M
  tokens the cost is **USD 22.65**, and the calls took 1.4 h of model time on one stream (free RAM 1.3–2.3 GB).
- **Routes:**
  - The API-YES gateway was not running at launch. The first 12 main-pass calls ran on the advisor key (456,505
    tokens) until it returned "no credits remaining".
  - I then started the local API-YES app, and the remaining 26 calls ran through API-YES (1,052,095 tokens).
  - Two calls left no usage record, so their usage is unknown: the call refused for lack of credit, and one figures
    stream (Zhang 2019) that ended without a completion event. The figures stream was rerun successfully.

## Files

- `PROTOCOL.md` (pre-registration)
- `batch2_candidates.txt`, `batch2_screening.csv`, `batch2_paper_set.txt`
- `b2.py`: pipeline wrapper (paper list and output directory only)
- `score.py`: wrapper around the frozen scoring code (input records and output folder only; applies a corrections file)
- `pdf_check_sample.py`, `batch2_pdf_check_sample.csv`, `batch2_pdf_check.csv`, `batch2_corrections.csv`
- `unit_completions.py`, `batch2_unit_completions.csv`, `batch2_corrections_plus_units.csv`
- `runs/<set>/`: the frozen outputs of each run, and the staged input records under `agent/nh3_field/out/`
- `report_numbers.py`, `report_numbers.json`
- Logs: `runs_*.log`, `fetch_si_batch2.log`, `agent/nh3_field/out_batch2/extract_*.log`

Commands, run with `D:\Research\CatalystForge\.venv\Scripts\python.exe`:

```
b2.py text
b2.py extract --pass main|figures|si|si_figures --api-yes --token-cap 5000000
b2.py normalize
score.py chain round1_regression ../../agent/nh3_field/out/records_normalized.csv
score.py chain batch2_corrected ../../agent/nh3_field/out_batch2/records_normalized.csv --paper-set batch2_paper_set.txt --corrections batch2_corrections.csv
score.py pool pooled ../nh3_field_2026_10_06 runs/batch2_corrected
report_numbers.py
```
