# Literature extraction agent: CO2-to-methanol catalyst records

First component of the agent that enlarges the methanol catalyst candidate set from the literature.
It turns a paper (DOI) into structured catalyst x condition records with the inputs the methanol plant
model needs (`data/meoh/`, `analysis/meoh_measurement_mc_2026_10_05/`), and measures its own accuracy
against TheMeCat v1 (Toldy et al., *Sci. Data* 2026, CC-BY-4.0) and a manual transcription of
Gothe et al. 2025 Table 4.

## Status (2026-10-05)

| Step | Papers |
|---|---|
| Pilot set chosen | 13 DOIs (12 TheMeCat + Gothe 2025) |
| PDFs retrieved by nus-fetch | 11 (10 TheMeCat + Gothe). The other TheMeCat candidates are ScienceDirect, which nus-fetch marks `manual` (publisher bot check) |
| Extracted with gpt-5.5 | **4**: Gothe 2025, Wu 2017, Bansode 2013, Wang 2017 (RSC Adv.) |
| Waiting for extraction | 7: `10.1021/cs500979c`, `10.1021/acscatal.9b01869`, `10.1126/sciadv.1701290`, `10.1002/anie.202401168`, `10.1002/cphc.202300530`, `10.1002/ente.201800747`, `10.1016/j.jcat.2016.03.017` |

The OpenAI organisation ran out of API credit during the run (HTTP 429 `insufficient_quota`,
`credit_balance_exhausted`, at 239,507 tokens used by this pilot). PDFs and text for the 7 waiting
papers are already prepared. Once credit is added, the rest of the pilot runs with:

```
cd agent\extraction
D:\Research\CatalystForge\.venv\Scripts\python.exe extract_records.py   # skips papers already in out/raw
D:\Research\CatalystForge\.venv\Scripts\python.exe normalize.py
D:\Research\CatalystForge\.venv\Scripts\python.exe evaluate.py
```

The accuracy numbers below cover the 4 extracted papers: 86 TheMeCat entries from 3 DOIs, plus 21 Gothe entries.

## Pipeline

| Step | File | What it does |
|---|---|---|
| 1 | `fetch_papers.py` | DOI list -> PDFs through `D:\Tools\nus-fetch` (`fetch -f <list> -o pdf --headless --json`). Reads `pdf/last_run.json` and writes `fetch_manifest.json` (status, pages, `doi_in_pdf`, note). `manual` rows are listed and never automated. |
| 2 | `pdf_to_text.py` | Writes `text/<slug>.txt` and `.json`. Running text comes from pypdfium2, which keeps two-column layouts in reading order (pdfplumber interleaves the two columns line by line). Tables come from pdfplumber `extract_tables()`. Each page gets an `=== PAGE n ===` marker and is also rendered to `text/img/<slug>_p<n>.jpg` (scale 1.5). |
| 3 | `extract_records.py` | One chat-completions call per paper: system rules, then the full text, then all page images (`detail: high`). Output is strict JSON-schema (`schema.json`). Raw output goes to `out/raw/<slug>.json`, and every call is logged to `out/token_usage.csv`. Hard caps: 15 papers and 3,000,000 tokens, both summed from the log so they hold across reruns. |
| 4 | `normalize.py` | Converts to the model basis and writes `out/records_normalized.csv` (see below). |
| 5 | `evaluate.py` | Matches extracted records to TheMeCat and to the Gothe manual table. Writes the scores to `eval/`. |

`make_schema.py` generates `schema.json`. The API key comes from the harness resolver
(`llm_client.resolve_api_key`) and is passed straight to `openai.OpenAI`. It is never printed, logged or written to disk.
The extraction prompt contains only the paper; no evaluation data is read by steps 1–4.
`pdf/` and `text/` are git-ignored because they are publisher content. DOIs, extracted JSON/CSV, evaluation files and code are committed.

### Schema (`schema.json`)

Each paper produces `{doi, title, records[], extraction_notes}`, with one record per catalyst x condition entry measured in that paper.
Literature-comparison tables, equilibrium values, DFT results and CO-only feeds are excluded.
Every numeric field is an object `{value, unit, qualifier, location, page}`:

- `value` is the number as printed. The only transformation applied is a power-of-ten multiplier from a column header. If the paper does not give the number, `value` is null.
- `qualifier` is one of `=`, `<`, `>`, `<=`, `>=`, `~`. A value read off a plot uses `~`.
- `location` names the table, figure or section, and `page` is the 1-based PDF page.

Record fields:

- Catalyst: `entry_label`, `catalyst_name`, `composition`, `components[]` (component, role active_metal/active_oxide/promoter/support, loading), `support`, `promoters[]`, `preparation`.
- Conditions: `temperature`, `pressure`, `h2_co2_ratio`, `feed_composition`, `ghsv` + `ghsv_basis`, `catalyst_mass`, `total_flow` (added in schema v2, see failure mode 3), `time_on_stream`.
- Results: `co2_conversion`, `selectivity_ch3oh`, `selectivity_co`, `selectivity_ch4`, `selectivity_basis`, `methanol_sty` + `sty_basis` (per_g_catalyst, per_g_metal, ...).
- Provenance: `data_source_type` (table, text, figure, mixed), `primary_location`, `primary_page`, `notes`.

The prompt allows two derived numbers, and each must cite its source in `location`:

- the H2/CO2 ratio computed from a stated feed composition;
- a condition stated once for a whole table, figure or series, applied to every entry it covers.

### Normalisation (`normalize.py`)

| Column | Conversion |
|---|---|
| `T_K` | °C + 273.15 |
| `P_bar` | MPa x 10, atm x 1.01325, kPa / 100, psi x 0.0689 |
| `H2_CO2` | Molar ratio, unchanged |
| `X_CO2_pct`, `S_MeOH_pct`, `S_CO_pct`, `S_CH4_pct` | % (a fraction is multiplied by 100). Each keeps its qualifier in a `*_q` column. |
| `GHSV_NL_gcat_h` | Only from a mass-based GHSV (mL, L or NL per g or kg per h, min or s), or flow / catalyst mass. A volume-based h-1 value stays in `GHSV_raw`, because converting it needs the bed density. |
| `STY_g_gcat_h`, `STY_g_gmetal_h` | Any of g, mg, kg, mol, mmol or umol MeOH per g or kg, per h, min or s (M = 32.042 g/mol), split by `sty_basis` |
| `metal_wt_pct` | Sum of the wt% loadings of the active metals |

Any value whose unit was not understood is reported in `flags`, never silently dropped.

### Model and settings

- Model: `gpt-5.5` (the API returns `gpt-5.5-2026-04-23`). It was available, so no fallback was needed.
- Settings: `reasoning_effort=medium`, `max_completion_tokens=100000`, strict `json_schema` response format, page images at `detail: high`. One call per paper, with no retries and no self-consistency voting.

## Token usage and cost

| Call | Prompt | Output (of which reasoning) | Total | Records | Time |
|---|---:|---:|---:|---:|---:|
| Smoke test | 9 | 4 | 13 | – | – |
| Wang 2017 RSC Adv. (test run, before the header-multiplier rule) | 26,652 | 5,022 (2,048) | 31,674 | 4 | 42 s |
| Wu 2017 Ind. Eng. Chem. Res. | 24,760 | 22,226 (3,717) | 46,986 | 26 | 140 s |
| Gothe 2025 ACS Catal. | 47,262 | 14,800 (1,024) | 62,062 | 21 | 87 s |
| Wang 2017 RSC Adv. (final) | 26,722 | 4,285 (1,024) | 31,007 | 4 | 31 s |
| Bansode 2013 Catal. Sci. Technol. | 33,515 | 34,250 (3,072) | 67,765 | 45 | 199 s |
| **Total** | **158,920** | **80,587** | **239,507** | | |

This is 8 % of the 3 M token cap. Cost at a list price of USD 5 per M input tokens and USD 30 per M output tokens
(gpt-5.5; the rates are set in the cost formula only and should be checked against the current price page):
158,920 x 5e-6 + 80,587 x 30e-6 = **USD 3.21**.

Per paper (n = 5 calls): about 32 k prompt tokens (text ~20 k plus 8–16 page images), about 16 k output tokens and 100 s.
That is about **USD 0.64 per paper**. Output tokens are 75 % of the cost, because every number carries its own unit, location and page.

## Accuracy

### Matching rule (`evaluate.py`)

An extracted record and a TheMeCat row form a candidate pair when all of the following hold:

- same DOI;
- catalyst names equal after normalisation (case, spaces, dashes and punctuation removed), or one contained in the other (at least 4 characters), or difflib ratio >= 0.85, or listed in `eval/name_aliases.json` (no aliases were needed);
- |dT| <= 3 K and |dP|/P <= 5 %;
- H2/CO2 within 10 % when both are present;
- GHSV within 10 % when both are on a mass basis.

A one-to-one Hungarian assignment over the candidate pairs minimises |dT|/3 + |dP|/(0.05 P) + |dX| + |dS| (in pp).
Performance values therefore only break ties between entries at identical conditions.
Matching uses TheMeCat after the verified errata are applied.

### TheMeCat errors found against the PDFs (`eval/themecat_errata.csv`)

Each disagreement between the extraction and TheMeCat was checked in the PDF. Where the PDF supports the extraction,
the correction is recorded with page-level evidence (69 cells in total). The rows are applied in file order.

| DOI | TheMeCat | PDF | Cells |
|---|---|---|---:|
| 10.1039/c2cy20604h (Bansode 2013) | pressure_bar 0.4 / 3 / 10 / 36 | 0.40 / 3 / 10 / 36 **MPa** = 4 / 30 / 100 / 360 bar (abstract p1, Experimental p4) | 60 |
| 10.1039/c2cy20604h | STY 0.0912 and 0.0735 g g-1 h-1 (Cu/Al2O3, 36 MPa, 473 / 443 K) | 103.4 and 75.0 mg gcat-1 h-1 printed in the text, p6 | 2 |
| 10.1021/acs.iecr.7b01464 (Wu 2017) | CZA200, 513 K: X_CO2 = 49.3 | Table 1 p4: X = 31.3. The value 49.3 is the CO selectivity. | 1 |
| 10.1039/c6ra28305e (Wang 2017) | STY 0.0261 and 0.0073 (CZ-550, CZ-650) | Table 2 p5: 2.41 and 1.03 x 10-7 mol s-1 g-1 = 0.0278 and 0.0119 g g-1 h-1 | 2 |
| 10.1039/c6ra28305e | H2/CO2 = 3.1 | Table 2 footnote: CO2:H2 = 1:3 | 4 |

TheMeCat GHSV values are computed by the curators rather than printed. Wu 2017 states 80 mL min-1 over 5.5 g, which gives 0.87, the TheMeCat value.
Several TheMeCat STY values are likewise computed by the curators rather than printed.

### Field-level accuracy against TheMeCat (3 DOIs, 71 matched entries)

- Strict tolerances: T ±1 K; P, GHSV and STY ±1 % relative; H2/CO2 ±0.05 (TheMeCat stores one decimal); X and S ±0.5 pp.
- Loose tolerances: T ±3 K; P, GHSV and STY ±5 %; H2/CO2 ±0.15; X and S ±2 pp.
- Accuracy is computed over the entries where the extraction gave a value. Coverage is the share of curated values for which the extraction gave a value.

| Field | Curated values | Extracted | Coverage | Strict acc. (adjudicated) | Loose acc. (adjudicated) | Strict acc. vs raw TheMeCat |
|---|---:|---:|---:|---:|---:|---:|
| T | 71 | 71 | 1.00 | **1.000** | 1.000 | 1.000 |
| P | 71 | 71 | 1.00 | **1.000** | 1.000 | 0.366 |
| H2/CO2 | 71 | 71 | 1.00 | **1.000** | 1.000 | 0.944 |
| GHSV | 71 | 0 | 0.00 | – | – | – (49 volume-basis h-1, 22 flow-only; see failure mode 3) |
| X_CO2 | 71 | 46 | 0.65 | **1.000** | 1.000 | 0.978 |
| S_MeOH | 71 | 55 | 0.77 | **0.945** | 0.982 | 0.945 |
| STY | 71 | 6 | 0.08 | **1.000** | 1.000 | 0.333 |

Results by source type (adjudicated, strict):

| Source | X_CO2 | S_MeOH |
|---|---|---|
| Table values (8 entries) | 8/8 | 8/8 |
| Plot readings (`~`) | 29/29 | 32/35 |

The three S_MeOH misses are plot readings from Bansode Fig. 6, off by 0.7, 1.0 and 2.4 pp.
`eval/field_accuracy_by_source.csv` has the full table.

### Entry-level recall and precision

| DOI | Curated | Extracted | Matched | Matched with X and S | Recall | Precision (matched only) | Precision (with spot check) |
|---|---:|---:|---:|---:|---:|---:|---:|
| 10.1021/acs.iecr.7b01464 | 22 | 26 | 22 | 22 | 1.00 | 0.85 | **1.00** |
| 10.1039/c2cy20604h | 60 | 45 | 45 | 20 | 0.75 | 1.00 | **1.00** |
| 10.1039/c6ra28305e | 4 | 4 | 4 | 4 | 1.00 | 1.00 | **1.00** |
| **Total** | 86 | 75 | 71 | 46 | **0.83** | 0.95 | **1.00** |

- The 4 unmatched extracted entries are Wu 2017 Table 2 (runs without internal cooling), which TheMeCat leaves out. All 4 match the PDF (`eval/unmatched_review.csv`).
- The 15 curated entries that were not found are all Cu–Ba/Al2O3 at temperatures other than 473 K. The main text points to ESI Table S3 for them, and the ESI is not fetched.

### Gothe 2025 Table 4 (manual transcription, 21 rows)

| Field | Correct |
|---|---|
| Rows matched (Re wt%, prereduction T, reaction T, P, CO2:H2, GHSV all exact) | 21/21 |
| X_CO2 | **21/21** |
| S_MeOH | **21/21** |
| S_CO (including the `<1` qualifier) | **21/21** |
| S_CH4 (including the `<1` qualifier) | **21/21** |
| STY (g MeOH per g Re per h) | **21/21** |

Per-row results are in `eval/gothe_table4_scores.csv`.

### CO / CH4 selectivity spot check (`eval/co_ch4_spotcheck.csv`)

20 values were drawn at random (seed 20261005) from the 71 extracted S_CO / S_CH4 values (Gothe 42, Bansode 21, Wu 8)
and checked against the PDFs by hand. All **20/20 are correct**:

- 15 are table values that match exactly, including 6 `<1` bounds;
- 2 are printed in the text;
- 3 are Fig. 7 plot readings within 1 pp.

## Failure modes seen

1. **Data in the Supporting Information.** Bansode 2013 points to ESI Tables S1–S3 for the full grid, and TheMeCat used them. The main text plots X_CO2 only for Cu/Al2O3 (Fig. 5), S_CO for Cu–K (Fig. 7), and S_MeOH for the promoted catalysts only at 473 K (Fig. 8). The SI-only values account for all 15 missed entries, all 25 missing X_CO2 values (Cu–K/Cu–Ba) and 16 missing S_MeOH values. The model left them null instead of inventing them. The fix is to fetch the SI and pass it as extra pages.
2. **Plot readings.** They are accurate (X 29/29 and S_MeOH 32/35 within 0.5 pp; all within 2.4 pp). The largest miss is one point in a crowded region of Bansode Fig. 6 (11 read vs 13.4). These values are flagged `~` so the plant model can give them a wider uncertainty.
3. **GHSV basis.** Two of the three TheMeCat papers give a volume-based GHSV (h-1) or only a flow rate. The extraction records exactly what is printed, so no mass-based GHSV could be scored. Schema v2 adds `total_flow`, and `normalize.py` now derives NL g-1 h-1 = flow / mass, so the next run covers flow-only papers such as Wu 2017 (80 mL min-1 / 5.5 g = 0.87). Volume-basis GHSV still needs a bed density from the paper.
4. **STY rarely printed.** Only 6 of the 71 curated STY values are printed in the papers; TheMeCat computes the rest from X, S and flow. The extraction does not compute anything, and the plant model can derive STY from X, S, flow and mass downstream.
5. **Retrieval.** 43 of the 52 TheMeCat DOIs are ScienceDirect. Without NUS VPN, nus-fetch marks all of them `manual`, including the open-access ones, because the OA copies also sit on ScienceDirect. Retrieval, not extraction, is the throughput limit on Elsevier-heavy sets.
6. **Text layer.** pdfplumber loses subscripts (CO2 -> CO) and interleaves columns. Using pypdfium2 text plus page images removed both problems in the 4 papers; no value had to be corrected for this reason.

## Manual-required DOIs (publisher bot check, not automated)

nus-fetch returned `manual` with the note "Elsevier API: no subscription from this network" for:

- `10.1016/j.apcatb.2017.06.069` (Rui 2017, Pd/In2O3, pilot)
- `10.1016/j.jes.2023.05.010` (Hou 2023, Au/In2O3, pilot)
- `10.1016/j.fuel.2023.127927`, `10.1016/j.cej.2022.135090`, `10.1016/j.fuel.2022.125878`, `10.1016/j.jscs.2019.09.002`, `10.1016/j.jcat.2012.05.020`, `10.1016/j.jcat.2020.01.014`, `10.1016/j.apcata.2019.117144` (substitutes, all ScienceDirect)

There are two ways to get them:

- Rerun `fetch_papers.py -f dois_pilot.txt` (and the backup lists) on NUS VPN. The Elsevier API key route only grants access from an NUS IP.
- Use nus-fetch menu 7 (open in your own browser) and then menu 8 (collect).

All 9 non-Elsevier TheMeCat DOIs are in the pilot, plus Bahruji 2016, which came from an open-access copy. That makes 10 TheMeCat papers instead of 12.

Pilot coverage by catalyst family:

| Family | Papers |
|---|---|
| Cu/ZnO/Al2O3 | Wu 2017 |
| Cu/Al2O3 + K/Ba | Bansode 2013 |
| Cu/ZrO2 | Samson 2014, Wang 2017 RSC Adv. |
| In2O3 | Chen 2019 Energy Technol., Chen 2019 ACS Catal. (In–Zr), Yang 2024 (In–Cr) |
| Pd/ZnO | Bahruji 2016 |
| ZnO–ZrO2 | Wang 2017 Sci. Adv. |
| Ir1Pd1/In2O3 | Chen 2024 |
| Re/TiO2 | Gothe 2025 |

Table-heavy papers in the set include Gothe and Wang RSC Adv.; figure-heavy ones include Bansode and Wang Sci. Adv.

## Scaling estimate (150–390 papers, `task3/CANDIDATE_SET_ESTIMATE.md`)

Measured on the 5 extraction calls: about 48 k tokens, USD 0.64 and 100 s per paper.

| Papers | Tokens | LLM cost | Wall time, sequential | Wall time, 8 parallel calls |
|---:|---:|---:|---:|---:|
| 150 | 7.2 M | ~USD 96 | 4.2 h | ~0.5 h |
| 390 | 18.7 M | ~USD 250 | 10.8 h | ~1.4 h |

That is about 36 papers per hour sequentially, or about 250 per hour with 8 concurrent calls (subject to the account rate limit).

Fetching the SI adds roughly 30–50 % more prompt tokens per paper. Cost can be cut 2–3x by sharing one location string per table instead of one per number, or by using `gpt-5.4`/`gpt-5.4-mini` for table-only papers with a gpt-5.5 check.

The rate-limiting steps are retrieval (Elsevier `manual` rows need VPN or the browser), plus human review of plot readings and of unmatched entries.
At the measured precision, review means spot-checking flagged values rather than re-transcribing.

## Files

| Path | Content |
|---|---|
| `dois_pilot.txt`, `dois_backup.txt`, `dois_backup2.txt` | Pilot and substitute DOI lists |
| `fetch_manifest.json` | Retrieval status per DOI |
| `schema.json` (from `make_schema.py`) | Extraction schema |
| `out/raw/*.json` | Raw model output per paper (with `_meta` usage) |
| `out/records_normalized.csv` | Records on the model basis |
| `out/token_usage.csv` | One row per API call |
| `eval/field_accuracy.csv`, `eval/field_accuracy_by_source.csv`, `eval/entry_metrics.csv`, `eval/summary.json` | Scores |
| `eval/matches.csv`, `eval/field_scores.csv` | Per-pair and per-field detail |
| `eval/themecat_errata.csv`, `eval/errata_applied.csv` | Verified TheMeCat corrections and the cells they change |
| `eval/unmatched_extracted.csv`, `eval/unmatched_review.csv`, `eval/unmatched_curated.csv` | Precision and recall audit |
| `eval/gothe_table4_scores.csv` | Gothe Table 4 scoring |
| `eval/co_ch4_spotcheck_sample.csv`, `eval/co_ch4_spotcheck.csv` | CO/CH4 spot check |
