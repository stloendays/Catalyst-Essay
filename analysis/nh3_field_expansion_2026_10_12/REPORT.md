# Ammonia within-paper field sample, batch 2: protocol committed before extraction, out-of-sample (2026-10-12)

Protocol: `PROTOCOL.md`, committed before extraction (local commit a04c3e9; the branch was first pushed after the
main-text result). Every number below is in `report_numbers.json`
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

## With Supporting Information (2026-10-13)

Protocol step 1 foresaw SI, but the first batch-2 run had to use the main text only because the NUS proxy was logged
out. Once the session was valid again, the SI of the 19 included papers was fetched and the frozen pipeline repeated:
the `si` and `si_figures` passes (same prompts, schema and model settings), `normalize.py` and the frozen scoring
through the same wrappers. Before batch 2 was rescored, round 1 was rerun through the wrapper
(`runs/round1_regression_si/`): 7/33, and all six output files are byte-identical to the frozen ones. The screening
decisions were not revisited.

### Result (printed-value primary, frozen definition)

| | Round 1 (frozen) | Batch 2, main text only | **Batch 2 with SI** | Pooled, main text only | **Pooled with SI** |
|---|---:|---:|---:|---:|---:|
| Papers with ≥ 1 scored group | 23 | 3 | **6** | 26 | **29** |
| Groups scored (entries) | 33 (139) | 5 (16) | **9 (35)** | 38 (155) | **42 (174)** |
| **Laboratory leader ≠ plant-cost leader** | 7 (21.2 %) | 2 (40 %) | **4 (44.4 %)** | 9 (23.7 %) | **11 (26.2 %)** |
| 95 % CI (paper-cluster bootstrap) | 7.1–36.7 % | 0–100 % | **12.5–77.8 %** | 11.1–37.8 % | **12.8–40.9 %** |
| Mismatches with regret > 5 % (papers) | 4 (3) | 2 (2) | 4 (3) | 6 (5) | 8 (6) |
| Papers contributing disagreements | 6 | 2 | 3 | 8 | 9 |
| Paper-weighted share (CI) | 19.9 % (5.8–36.2 %) | 44.4 % (0–100 %) | 38.9 % (5.6–72.2 %) | 22.8 % (8.7–39.1 %) | 23.9 % (10.1–39.7 %) |
| Regret of mismatched groups, median / max | 10.0 % / 31.5 % | 15.4 % / 25.4 % | 13.6 % / 25.4 % | 10.0 % / 31.5 % | 10.0 % / 31.5 % |
| Cross-metal groups (papers); of them mismatched | 4 (3); 4 | 2 (1); 1 | 4 (2); 3 | 6 (4); 5 | 8 (5); 7 |
| Mismatch kinds: different metal / fused-Fe reference / same metal and content / different content | 3 / 2 / 1 / 1 | 0 / 1 / 1 / 0 | 0 / 3 / 1 / 0 | 3 / 3 / 2 / 1 | 3 / 5 / 2 / 1 |

Same CI method as above (10,000 paper resamples, seed 20261006). Sensitivities, all at 4/9 for batch 2 and 11/42 for
the pool:
- uncorrected records (`runs/batch2_si`, `runs/pooled_si_uncorrected`);
- the unparsed units converted (`runs/batch2_si_corrected_units`, `runs/pooled_si_units`);
- one chain run over the concatenated records (`runs/pooled_si_single_chain`).

### The nine batch-2 groups with SI

| Group | n | Paper leader (USD/t) | Plant leader (USD/t) | Regret | Kind | Source |
|---|---:|---|---|---:|---|---|
| Zheng 2019 (10.1002/anie.201907171), 459 °C, 1 MPa | 3 | Ba-Ru-Li/AC, 4.8 wt% Ru (22.16) | Mittasch's Fe (17.67) | 25.4 % | fused-Fe reference vs supported catalyst | main text |
| Hattori 2020 (Nat. Commun., 10.1038/s41467-020-15868-8), 340 °C, 0.1 MPa | 8 | Ru (10%)/Ba-Ca(NH₂)₂ (16.95) | commercial Fe catalyst (14.18) | 19.5 % | fused-Fe reference vs supported catalyst | SI Tables 2–4 |
| Hattori 2020, 300 °C, 0.1 MPa | 7 | Ru (12%)/CaFH (15.30) | commercial Fe catalyst (14.21) | 7.6 % | fused-Fe reference vs supported catalyst | SI Table 2 |
| Abe 2017 (10.1021/acs.jpcc.7b07268), 340 °C, 0.1 MPa | 2 | Ru/Ca₂NH, 0.1 wt% (27.18) | Ru/CaNH, 0.1 wt% (25.79) | 5.4 % | same metal and metal content | main text |
| Zheng 2019, 400 °C, 1 MPa | 2 | Ba-Ru-Li/AC | same | 0 | – | main text |
| Zheng 2019, 459 °C, 5 MPa | 4 | Ru-Li/MgO | same | 0 | – | main text |
| Ogura 2018 (10.1021/acssuschemeng.8b04683), 400 °C, 1 MPa | 5 | Ru/La₀.₅Pr₀.₅O₁.₇₅_650red | same | 0 | – | main text |
| Qiu 2019 (10.1021/acs.chemmater.9b03099), 375 °C, 0.1 MPa | 2 | Ru SAs/S-1 | same | 0 | – | SI Table S2 |
| Ye 2020 (10.1021/jacs.0c06624), 400 °C, 0.9 MPa | 2 | Ni/CeN NPs | same | 0 | – | SI Table S2 |

The five main-text groups are unchanged. The SI adds four groups from three papers. Two of them disagree, and in both
the commercial fused-Fe reference in Hattori 2020 is the plant-cost leader. At 340 °C the paper's highest printed rate,
Ru/CaFH (15,000 µmol g⁻¹ h⁻¹), is excluded by the frozen "outlet near equilibrium" flag, so Ru (10%)/Ba-Ca(NH₂)₂ leads
that group.

### Variants with SI: groups with a different winner / groups (papers with one / papers), CI

| Variant | Batch 2 with SI | Pooled with SI |
|---|---|---|
| Rate per g catalyst | 4/9 (3/6), 12.5–77.8 % | 11/42 (9/29), 12.8–40.9 % |
| Rate per g metal | 5/9 (4/6), 25.0–88.9 % | 15/42 (11/29), 20.0–52.1 % |
| 90 % Ru recovery | 3/9 (3/6), 12.5–57.1 % | 10/42 (9/29), 11.6–37.0 % |
| Bed density 500 kg m⁻³ | 4/9 (3/6) | 11/42 (9/29) |
| Bed density 2,500 kg m⁻³ | 4/9 (3/6) | 9/42 (7/29) |
| Commercial fused-Fe references removed | 1/9 (1/6), 0–42.9 % | 6/42 (5/29), 2.9–26.7 % |
| Measured at ≥ 5 MPa | 0/1 (0/1) | 1/5 (1/5), 0–60 % |
| Without the paper with the most groups | 3/6 (2/5) | 10/38 (8/28) |
| All entries (plot readings included) | 6/47 (5/12), 3.4–32.3 % | 50/171 (18/40), 15.8–43.6 % |

### Pipeline counts with SI

- **SI fetch** (`fetch_si.py` through `b2.py si-fetch`, nus-fetch browser profile, read-only; `batch2_si_manifest.json`,
  `fetch_si_batch2_si.log`):
  - ok for 17 papers;
  - no SI link on the publisher page for 2 papers, Tarka 2015 (10.1002/cctc.201500309) and Raróg-Pilecka 2011
    (10.1007/s10562-011-0564-8);
  - 0 failures and no bot check.

  One Word SI (Zhao 2017) was exported with `si_docx2pdf.ps1`. One Nature Communications file was the peer-review file,
  which was moved to `si/_not_si/` as in round 1.
- **Extraction** (`out_batch2/raw_si/`, `raw_si_figures/`):
  - si: 17 calls, 279 records;
  - si_figures: 11 calls, 176 records;
  - 7 calls returned no records (characterisation-only SI or figures).

  With the main-text records, 677 entries merge from 19 papers: main 336, figures 163, SI 149, SI figures 29; 76 entries
  carry fields filled from another pass.
- **Chain** (`runs/batch2_si_corrected`):
  - 290 entries mapped and 387 outside: 363 without a metal content, 174 without a rate per g catalyst, 47 without a
    single model metal, 16 without T or P;
  - 204 primary entries with a cost and 85 flagged;
  - after deduplication, 186 primary entries from 15 papers;
  - the set's median NH₃ fraction is 0.078 %.
- **Unparsed units:** only two new values, both "normalized NH₃ synthesis rate" (Zhang 2019, SI Fig. S3), correctly left
  unparsed. `batch2_si_corrections_plus_units.csv` is therefore the main-text units file plus the SI correction below.

### Accuracy check of the SI-derived values (AI-assisted)

`batch2_si_pdf_check.csv` is a new random sample (`pdf_check_sample_si.py`, seed 20261013) of 20 of the 108 printed
values that come from the SI (source pass `si` after the merge) and enter the batch-2 primary. As in
`pdf_check_sample.py`, the sample was drawn from the uncorrected run (`runs/batch2_si`). It holds 5 rates, 5 P, 4 WHSV,
4 metal wt% and 2 T values. Each value was checked against the cited SI or main-text page.

**19/20 correct (0.95, 95 % CI 0.75–1.00, Clopper–Pearson).** The wrong value comes from Zheng 2019. The SI prints
"63.0 mmol g⁻¹ h⁻¹" for Ba-Ru/AC at 0 % Li in main-text Fig. 1a, which was measured at 5 MPa (Fig. 1a caption). The
extraction took 1 MPa from the Fig. S11 caption, and the merge attached the value to the 10-bar point of Fig. S3b.
`batch2_si_corrections.csv` (the two main-text corrections plus 5 field rows for this entry) restores that point's own
plot reading, about 16,000. The entry then leaves the printed primary, and Ba-Ru-Li/AC is again the paper leader of
that group. The disagreement count does not change: Mittasch's Fe is the plant leader before and after the correction,
and the regret is 24.5 % before and 25.4 % after.

### Tokens and route (SI task)

- 28 calls and 807,563 tokens (496,070 prompt, 311,493 output). This is 27 % of the task's 3 M cap and USD 11.83 at
  USD 5 / 30 per M.
- The batch-2 log now totals 2,316,163 tokens, within the protocol's 5 M cap.
- All calls went through API-YES. `NH3_API_YES_ONLY=1` (in `b2.py`) removed the fallback to the advisor key for this
  run, and `llm_route.py` is unchanged. API-YES did not run out.
- The calls ran on one stream (2.5–3 GB free RAM).

Commands (in addition to those below):

```
nus-fetch python: b2.py si-fetch ; pwsh -File agent/nh3_field/si_docx2pdf.ps1
b2.py si-text
NH3_API_YES_ONLY=1 b2.py extract --pass si|si_figures --api-yes --token-cap 4508600
b2.py normalize
score.py chain round1_regression_si ../../agent/nh3_field/out/records_normalized.csv
score.py chain batch2_si_corrected ../../agent/nh3_field/out_batch2/records_normalized.csv --paper-set batch2_paper_set.txt --corrections batch2_si_corrections.csv
score.py chain batch2_si ../../agent/nh3_field/out_batch2/records_normalized.csv --paper-set batch2_paper_set.txt
score.py pool pooled_si ../nh3_field_2026_10_06 runs/batch2_si_corrected
pdf_check_sample_si.py
report_numbers.py
```

`agent/nh3_field/out_batch2/records_normalized.csv` now holds the merge with SI. The main-text-only records used by
the runs above stay staged under `runs/batch2*/agent/nh3_field/out/` and in git history (commit 8a55444).

## Verification follow-up (2026-10-13)

Protocol: committed before extraction (local commit a04c3e9; the branch was first pushed after the main-text result).

An independent verification of PR #78 raised two findings, both now closed:
1. A Qiu 2019 correction wrongly blanked a printed Ru loading.
2. The screening had not been revisited with the SI.

Before rescoring, round 1 was rerun through the wrapper (`runs/round1_regression_fix/`): 7/33 again. The six output
files are byte-identical to the frozen ones; the self-check CSV differs exactly as described above.

### Result (printed-value primary, frozen definition)

Qiu 2019 Ba-Ru SAs/S-1 enters the primary with its printed Ru loading, 0.23 wt% (Finding 1).

| | Batch 2 with SI (above) | **Batch 2, follow-up** | Pooled with SI (above) | **Pooled, follow-up** |
|---|---:|---:|---:|---:|
| Papers screened / included | 25 / 19 | **25 / 22** | 55 / 49 | **55 / 52** |
| Papers with ≥ 1 scored group | 6 | **8** | 29 | **31** |
| Groups scored (entries) | 9 (35) | **11 (40)** | 42 (174) | **44 (179)** |
| **Laboratory leader ≠ plant-cost leader** | 4 (44.4 %) | **5 (45.5 %)** | 11 (26.2 %) | **12 (27.3 %)** |
| 95 % CI (paper-cluster bootstrap) | 12.5–77.8 % | **12.5–77.8 %** | 12.8–40.9 % | **14.3–41.7 %** |
| Mismatches with regret > 5 % (papers) | 4 (3) | 4 (3) | 8 (6) | 8 (6) |
| Papers contributing disagreements | 3 | 4 | 9 | 10 |
| Paper-weighted share (CI) | 38.9 % (5.6–72.2 %) | 41.7 % (12.5–75.0 %) | 23.9 % (10.1–39.7 %) | 25.5 % (11.8–40.9 %) |
| Regret of mismatched groups, median / max | 13.6 % / 25.4 % | 7.6 % / 25.4 % | 10.0 % / 31.5 % | 8.8 % / 31.5 % |
| Cross-metal groups (papers); of them mismatched | 4 (2); 3 | 4 (2); 3 | 8 (5); 7 | 8 (5); 7 |
| Mismatch kinds: different metal / fused-Fe reference / same metal and content / different content | 0 / 3 / 1 / 0 | 0 / 3 / 2 / 0 | 3 / 5 / 2 / 1 | 3 / 5 / 3 / 1 |
| **Commercial fused-Fe references removed** | 1/9 (1/6), 0–42.9 % | **2/11 (2/8), 0–50.0 %** | 6/42 (5/29), 2.9–26.7 % | **7/44 (6/31), 5.0–28.0 %** |

Round 1 alone stays at 7/33, or 5/33 with the fused-Fe references removed (CI 3.2–29.0 %).

The two findings act separately:
- **Finding 1 alone** (19-paper records; `runs/batch2_vf_qiu023`, `runs/pooled_vf_qiu023`) leaves the counts at 4/9 and
  11/42.
- **Finding 2** adds Lu 2018 and Wu 2020 as scored papers, and one disagreement.

### Finding 1: Qiu 2019 Ru loading

`batch2_si_corrections.csv` had blanked the Ru loading of Ba-Ru SAs/S-1 (two entries, 648 K and 673 K) as "not
printed". That correction came from the main-text check (`batch2_pdf_check.csv` id 20), but SI Table S2 (p26) prints
0.23 wt% Ru for this catalyst (ICP-MS, footnote a). The 0.27 wt% that the extraction carried over belongs to the parent
Ru SAs/S-1.

**The primary uses the printed 0.23 wt%.** The blanking rows were removed, and `batch2_si_corrections.csv`,
`batch2_si_corrections_plus_units.csv` and `batch2_vf_sens_wu_pressure.csv` each carry three rows per entry:
- `metal_wt_pct` 0.27 → 0.23;
- `rate_umol_gmetal_h` rederived as rate per g catalyst / 0.0023, as `normalize.py` derives it: 297,222 → 348,913 and
  514,630 → 604,130 µmol g⁻¹ h⁻¹ at 648 and 673 K;
- `metal_loading_raw` "0.27 wt %" → "0.23 wt %".

The plant cost uses only the loading; the other two rows keep `candidates.csv` consistent. `batch2_corrections.csv`,
the main-text-only file, is unchanged: without the SI the loading was indeed not printed.

The Qiu 375 °C group has 3 entries:

| Qiu 2019, 375 °C, 0.1 MPa | Extracted 0.27 wt% (superseded) | **Printed 0.23 wt% (primary)** |
|---|---:|---:|
| Ba-Ru SAs/S-1, plant cost | 24.74 USD/t | **25.21 USD/t** |
| Ru SAs/S-1, 0.27 wt% | 25.38 USD/t | 25.38 USD/t |
| Cs-Ru/MgO, 0.27 wt% | 25.71 USD/t | 25.71 USD/t |
| Paper leader = plant leader | Ba-Ru SAs/S-1 | Ba-Ru SAs/S-1 |
| 90 % Ru recovery: Ba-Ru SAs/S-1 / Ru SAs/S-1 | 23.75 / 24.21 USD/t, no disagreement | 24.28 / 24.21 USD/t, disagreement, regret 0.28 % |

With 0.23 wt% every primary number of the follow-up is unchanged: batch 2 5/11 (4/8 papers, CI 12.5–77.8 %), pooled
12/44 (10/31, CI 14.3–41.7 %), fused-Fe references removed 2/11 and 7/44 (CI 5.0–28.0 %). Two variants register the
lower loading:
- **90 % Ru recovery** gains the Qiu group: batch 2 3/11 → 4/11 (CI 10.0–46.2 % → 12.5–60.0 %), pooled 10/44 → 11/44
  (CI 11.3–35.0 % → 13.2–37.8 %).
- **Bed density 2,500 kg m⁻³:** the Qiu group already disagreed (6/11 and 11/44 are unchanged). Its kind changes from
  "same metal and metal content" to "same metal, different metal content", and its regret from 0.53 % to 2.27 %.

**Superseded record.** The first follow-up run (commit 249051f) carried the extracted 0.27 wt%. Its outputs were
reproduced through the same wrapper before the 0.23 rows were added:
- `runs/batch2_vf_screen_corrected_qiu027`, with `batch2_si_corrections_qiu027.csv` (the corrections file of 249051f):
  all nine output files equal the committed `runs/batch2_vf_screen_corrected`, and the console log is identical.
- `runs/pooled_vf_screen_qiu027`: equal to the committed `runs/pooled_vf_screen` except the `pooled_from` path in
  `summary.json`.

The finding-1-only runs with 0.27 wt% stay in `runs/batch2_vf_corrected` and `runs/pooled_vf`. `report_numbers.json`
holds them as `*_extracted027` and the Qiu entries' costs under `qiu_loading`.

### Finding 2: screening revisited with the SI

The pre-registered inclusion rule (PROTOCOL.md section 2) was re-applied, exactly as written, to the four excluded
papers whose exclusion depended on the SI. Each decision is in `batch2_screening.csv` in the new columns
`with_si_decision`, `with_si_reason` and `with_si_screened_from`. The other 21 rows are unchanged and marked "not
revisited".

| Paper | Main-text decision | With SI | Reason (one line) | SI route |
|---|---|---|---|---|
| Hasegawa 2018 (10.1021/acs.chemmater.8b01819) | exclude | **include** | SI p5 states H₂/N₂ = 3 (60 mL/min, 0.1 g), 5 wt% Ru, rates recalculated to 0.1 MPa; main Fig. 3b compares Ru@C12A7 and Ru@re-C12A7 against temperature | ACS SI, public Figshare mirror (10.1021/acs.chemmater.8b01819.s001) |
| Lu 2018 (10.1021/acscatal.8b03743) | exclude | **include** | SI Table S2 p16: four Ru(10 wt%)/Y₅Si₃ catalysts, r(340 °C) at 0.1 MPa with "H₂ : N₂ = 1 : 3" stated | ACS SI, public Figshare mirror (10.1021/acscatal.8b03743.s001) |
| Wu 2020 (10.1039/c9cc07385j) | exclude | **include** | ESI p2: Ru ≈ 3 wt% (impregnation); ESI Table S4 p11: rates of Ru/Ti-Ce-E, Ru/Ti-Ce-S, Ru/CeO₂ and Ru/TiO₂ at 1 MPa, 400 °C; main Fig. 4 caption: H₂/N₂ 3:1, 36,000 mL g⁻¹ h⁻¹ | RSC ESI through nus-fetch (EZproxy) |
| Luz 2020 (10.1039/c9cy01303b) | exclude | exclude | ESI Table S3 gives two BaCs-RuC catalysts (Ru 58.5 and 23.1 wt%) with rates at 300/400 °C and 95 bar, but the H₂/N₂ ratio of the test feed is stated in neither the article nor the ESI (only the 75 % H₂/25 % N₂ reduction gas) | RSC ESI through nus-fetch (EZproxy) |

**SI fetch** (`b2.py si-fetch-screen`; `batch2_screening_si_manifest.json`, `fetch_si_batch2_screen.log`):
- The two RSC ESI files came through the nus-fetch browser profile.
- For the two ACS papers the profile was in use by another session's batch download. A direct request to the
  publisher pages returned a bot check, which was not retried. The SI PDFs were instead taken from ACS's public
  Figshare deposit, with Figshare `resource_doi` equal to the article DOI.
- SHA-256 of the two ACS files:
  - `10_1021_acs_chemmater_8b01819__si1.pdf`: 93f9db88…c2b17;
  - `10_1021_acscatal_8b03743__si1.pdf`: 5706f88a…cd5.
- Batch 2 now has 25 screened and 22 included papers.

**Extraction** of the three new papers: four passes (`out_batch2/extract_*_vf*.log`), same prompts, schema and model
settings, `B2_SCREEN=with_si`. Records per paper:
- Hasegawa: main 26, figures 16, si 0.
- Lu: main 13, figures 9, si 5, si_figures 16.
- Wu: main 32, figures 24, si 6.

The pass selector found no SI figure with data for Hasegawa or Wu, so neither had an si_figures call.

**Normalisation:** 792 entries merge from 22 papers.

**Chain** (`runs/batch2_vf_screen_corrected`):
- 333 entries mapped and 459 outside;
- 247 primary entries with a cost and 85 flagged;
- after deduplication, 206 primary entries from 18 papers;
- the set's median NH₃ fraction is 0.097 %.

The two new scored groups:

| Group | n | Paper leader (USD/t) | Plant leader (USD/t) | Regret | Kind | Source |
|---|---:|---|---|---:|---|---|
| Lu 2018, 340 °C, 0.1 MPa | 2 | Ru(10 wt%)/Y₅Si₃-NPs (22.23) | Ru(10 wt%)/Y₅Si₃ bulk (21.77) | 2.1 % | same metal and metal content | main text p3 |
| Wu 2020, 400 °C, 1 MPa | 2 | Ru/CeO₂ | same (22.22) | 0 | – | ESI Table S4 |

- **Hasegawa 2018** contributes no scored group: all of its rates are plot readings. It stays counted as included,
  as PROTOCOL.md section 2 requires.
- **Wu 2020:** the merge filled the printed Table S4 rates of Ru/Ti-Ce-E and Ru/Ti-Ce-S into the main-text Fig. 4a
  entries. It did not fill the pressure, which the Fig. 4 caption does not give, so these two entries fall outside
  ("no T or P").
  - Sensitivity `runs/batch2_vf_sens_wu_pressure` (file `batch2_vf_sens_wu_pressure.csv`) sets 1 MPa from Table S4.
  - The printed primary is unchanged, because the temperature of these entries is a Fig. 4a plot reading.
  - Counts stay at 5/11 and 12/44.
- **Lu 2018:** the extraction left H₂/N₂ blank, and the frozen chain used its default of 3.

### Accuracy check of the new papers (AI-assisted)

`batch2_vf_pdf_check.csv`: 10 values per newly included paper (`pdf_check_sample_vf.py`, seed 20261013). It uses the
population and lookup of `pdf_check_sample.py` on the uncorrected run `runs/batch2_vf_screen`.

- **Lu 2018:** 10 printed primary values.
- **Wu 2020:** all 10 of its printed primary values.
- **Hasegawa 2018:** it has no printed primary value, so its 10 come from its primary entries in the all-entries run.
  These are plot readings, judged correct within ±5 % of the point read from the figure rendered at 6×.

**29/30 correct** (Lu 10/10, Wu 10/10, Hasegawa 9/10). The wrong value is a plot reading in Hasegawa Fig. 3b
(Ru@C12A7 at 360 °C): 3.2 extracted, 3.45 mmol g⁻¹ h⁻¹ read. It was corrected in `batch2_si_corrections.csv` (3 field
rows). It is not a printed value, so it does not enter the primary.

### Sensitivities

All give 5/11 for batch 2 and 12/44 pooled. All but the uncorrected records carry the Qiu 0.23 wt% rows.
- uncorrected records (`runs/batch2_vf_screen`, `runs/pooled_vf_screen_uncorrected`);
- unparsed units converted (`runs/batch2_vf_screen_corrected_units`, `runs/pooled_vf_screen_units`);
- one chain run over the concatenated records (`runs/pooled_vf_screen_single_chain`);
- the Wu pressure fill (`runs/batch2_vf_sens_wu_pressure`, `runs/pooled_vf_sens_wu_pressure`).

### Variants, follow-up: groups with a different winner / groups (papers with one / papers), CI

| Variant | Batch 2, follow-up | Pooled, follow-up |
|---|---|---|
| Rate per g catalyst | 5/11 (4/8), 12.5–77.8 % | 12/44 (10/31), 14.3–41.7 % |
| Rate per g metal | 6/11 (5/8), 25.0–87.5 % | 16/44 (12/31), 20.9–52.1 % |
| 90 % Ru recovery | 4/11 (4/8), 12.5–60.0 % | 11/44 (10/31), 13.2–37.8 % |
| Bed density 500 kg m⁻³ | 5/11 (4/8) | 12/44 (10/31) |
| Bed density 2,500 kg m⁻³ | 6/11 (5/8) | 11/44 (9/31) |
| Commercial fused-Fe references removed | 2/11 (2/8), 0–50.0 % | 7/44 (6/31), 5.0–28.0 % |
| Measured at ≥ 5 MPa | 0/1 (0/1) | 1/5 (1/5), 0–60 % |
| Without the paper with the most groups | 4/8 (3/7) | 11/40 (9/30) |
| All entries (plot readings included) | 11/53 (7/15), 6.8–45.0 % | 55/177 (20/43), 17.8–45.3 % |

### Tokens and route (follow-up)

- 10 calls and 274,511 tokens (177,062 prompt, 97,449 output), USD 3.81 at USD 5 / 30 per M.
- The batch-2 log now totals 2,590,674 tokens, within the protocol's 5 M cap.
- All calls went through API-YES (`NH3_API_YES_ONLY=1`), and API-YES did not run out.
- At most two streams ran at once, with about 4.9 GB of RAM free.

Commands (with `D:\Research\CatalystForge\.venv\Scripts\python.exe`; nus-fetch interpreter for the fetch):

```
score.py chain round1_regression_fix ../../agent/nh3_field/out/records_normalized.csv
score.py chain batch2_vf_corrected ../../agent/nh3_field/out_batch2/records_normalized.csv --paper-set batch2_paper_set.txt --corrections batch2_si_corrections.csv   # finding 1 only (19-paper records; Qiu at 0.27 wt%, superseded; the file then held the 5 Zheng rows)
score.py pool pooled_vf ../nh3_field_2026_10_06 runs/batch2_vf_corrected
nus-fetch python: b2.py si-fetch-screen 10.1039/c9cc07385j 10.1039/c9cy01303b   # ACS SI: Figshare (see above)
b2.py si-text
NH3_API_YES_ONLY=1 B2_SCREEN=with_si b2.py extract --pass main|figures|si|si_figures --api-yes --token-cap 5000000 --doi ...
B2_SCREEN=with_si b2.py normalize
score.py chain batch2_vf_screen ../../agent/nh3_field/out_batch2/records_normalized.csv --paper-set batch2_paper_set_vf.txt
score.py chain batch2_vf_screen_corrected ../../agent/nh3_field/out_batch2/records_normalized.csv --paper-set batch2_paper_set_vf.txt --corrections batch2_si_corrections.csv
score.py pool pooled_vf_screen ../nh3_field_2026_10_06 runs/batch2_vf_screen_corrected
pdf_check_sample_vf.py
report_numbers.py
```

The finding-1 runs (`runs/batch2_vf_corrected*`, `runs/batch2_vf_qiu023`, `runs/pooled_vf*` without `_screen`) used
the 19-paper records. They are staged in each run folder. `agent/nh3_field/out_batch2/records_normalized.csv` now holds
the 22-paper merge.

Qiu printed loading (0.23 wt%) in the primary: commands, run with the NH3-FINAL-1.1 harness
(`NH3_HARNESS=D:\论文-AI4S\Catalyst_Economic_Leverage_Automation_Harness_v0.1`; no response surface is rebuilt). Round 1
was rerun first (`runs/round1_regression_qiu/`): 7/33, the six output files equal the frozen ones, and the self-check
CSV differs exactly as described above.

```
score.py chain round1_regression_qiu ../../agent/nh3_field/out/records_normalized.csv
score.py chain batch2_vf_screen_corrected_qiu027 ../../agent/nh3_field/out_batch2/records_normalized.csv --paper-set batch2_paper_set_vf.txt --corrections batch2_si_corrections_qiu027.csv   # superseded 0.27 wt%, reproduction
score.py pool pooled_vf_screen_qiu027 ../nh3_field_2026_10_06 runs/batch2_vf_screen_corrected_qiu027
score.py chain batch2_vf_screen_corrected ../../agent/nh3_field/out_batch2/records_normalized.csv --paper-set batch2_paper_set_vf.txt --corrections batch2_si_corrections.csv
score.py chain batch2_vf_screen_corrected_units ../../agent/nh3_field/out_batch2/records_normalized.csv --paper-set batch2_paper_set_vf.txt --corrections batch2_si_corrections_plus_units.csv
score.py chain batch2_vf_sens_wu_pressure ../../agent/nh3_field/out_batch2/records_normalized.csv --paper-set batch2_paper_set_vf.txt --corrections batch2_vf_sens_wu_pressure.csv
score.py chain pooled_vf_screen_single_chain runs/pooled_vf_screen_single_chain_input.csv --paper-set pooled_paper_set_vf.txt --corrections batch2_si_corrections.csv
score.py pool pooled_vf_screen ../nh3_field_2026_10_06 runs/batch2_vf_screen_corrected
score.py pool pooled_vf_screen_units ../nh3_field_2026_10_06 runs/batch2_vf_screen_corrected_units
score.py pool pooled_vf_sens_wu_pressure ../nh3_field_2026_10_06 runs/batch2_vf_sens_wu_pressure
score.py pool pooled_vf_qiu023 ../nh3_field_2026_10_06 runs/batch2_vf_qiu023   # finding 1 alone, pooled
report_numbers.py
```

## Files

- `PROTOCOL.md` (protocol committed before extraction)
- `batch2_candidates.txt`, `batch2_screening.csv`, `batch2_paper_set.txt`
- `b2.py`: pipeline wrapper (paper list and output directory only)
- `score.py`: wrapper around the frozen scoring code (input records and output folder only; applies a corrections file)
- `pdf_check_sample.py`, `batch2_pdf_check_sample.csv`, `batch2_pdf_check.csv`, `batch2_corrections.csv`
- `unit_completions.py`, `batch2_unit_completions.csv`, `batch2_corrections_plus_units.csv`
- `runs/<set>/`: the frozen outputs of each run, and the staged input records under `agent/nh3_field/out/`
- `report_numbers.py`, `report_numbers.json`
- Follow-up: `batch2_screening_si_manifest.json`, `fetch_si_batch2_screen.log`, `batch2_paper_set_vf.txt`,
  `pooled_paper_set_vf.txt`, `pdf_check_sample_vf.py`, `batch2_vf_pdf_check_sample.csv`, `batch2_vf_pdf_check.csv`,
  `batch2_vf_sens_wu_pressure.csv`, `batch2_vf_sens_qiu023.csv`
- Qiu printed loading: `batch2_si_corrections_qiu027.csv` (superseded corrections file, commit 249051f),
  `runs/batch2_vf_screen_corrected_qiu027/`, `runs/pooled_vf_screen_qiu027/`, `runs/pooled_vf_qiu023/`,
  `runs/round1_regression_qiu/`
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
