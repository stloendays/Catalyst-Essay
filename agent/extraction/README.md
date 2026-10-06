# Literature extraction agent: CO2-to-methanol catalyst records

First component of the agent that enlarges the methanol catalyst candidate set from the literature.
It turns a paper (DOI) into structured catalyst x condition records with the inputs the methanol plant
model needs (`data/meoh/`, `analysis/meoh_measurement_mc_2026_10_05/`), and measures its own accuracy
against TheMeCat v1 (Toldy et al., *Sci. Data* 2026, CC-BY-4.0) and a manual transcription of
Gothe et al. 2025 Table 4.

## 40-paper set (2026-10-06, current)

The set is defined in `paper_set.txt` (DOI and the reference it is scored against); `extract_records.py`,
`pdf_to_text.py`, `normalize.py` and `evaluate.py` use only these DOIs.

| Reference | Papers | Curated entries |
|---|---:|---:|
| Gothe 2025 Table 4 (manual) | 1 | 21 |
| TheMeCat v1 | 18 (the earlier 19 minus Shi 2020) | 406 |
| Suvarna, Araújo & Pérez-Ramírez 2022 curated set (*Appl. Catal. B* 315, 121530; Zenodo 10.5281/zenodo.6541445, CC-BY-4.0; STY, T, P, H2/CO2, GHSV, composition; no conversion or selectivity) | 20 | 194 |
| None (scored by PDF review only): Lam et al. 2018 *JACS* 10.1021/jacs.8b05595 | 1 | – |
| **Total** | **40** | **600** (+21 Gothe) |

- Shi 2020 (10.1016/j.jscs.2019.09.002) is dropped: it has no Supporting Information (user, 2026-10-06). Its raw files stay in `out/` and are not merged.
- Batch 4 (21 papers, `dois_batch4.txt`, `dois_batch4b.txt`). The 12 TheMeCat papers not used before that have SI
  on the Elsevier CDN all ended `manual` at the ScienceDirect bot check, so the batch takes non-Elsevier papers from
  the Suvarna set that nus-fetch retrieves and whose SI `fetch_si.py` finds (20), plus Lam 2018.
  Six Suvarna candidates have no SI on the publisher page and were not used
  (aic.16490, ente.201402091, er.7246, acs.iecr.0c04688, acs.iecr.8b01246, c9ra00658c).
  Every PDF was checked against its Crossref title.
- `fetch_si.py` now also collects Nature/Springer ESM files (`*_MOESM<k>_ESM.*`). Files that are not SI (peer-review
  files, Nature "description of additional files", RSC accepted manuscripts) were moved to `si/_not_si/`.
- Same model, prompt, schema and four passes as before. 76 calls (21 main, 21 figures, 21 SI, 13 SI-figure pages),
  3,198,197 tokens (2,000,247 prompt, 1,197,950 output), about 0.15 M tokens per paper, USD 45.9 at USD 5 / 30 per M.
  30 calls ran on API-YES; it reached its usage limit and the other 46 ran on the advisor's OpenAI key (`llm_route.py`).
  One figure call returned no response object and was rerun. Caps for this batch: `--token-cap 9000000 --pass-cap 3200000`.

### Scoring against Suvarna

The Suvarna rows have no catalyst names, so `match_doi_suvarna` pairs on conditions (|dT| <= 3 K, |dP|/P <= 5 %,
H2/CO2 and mass GHSV within 10 %) and then minimises 3 x (element-set difference) + relative loading difference +
|ln STY ratio| (tie-break). Bimetallic catalysts that Suvarna lists twice (once per family) are counted once.
An extracted record with no pressure can pair; P then scores as missing (Ni-In-Al/SiO2 states "ambient pressure"
once and the extraction left P empty).

Suvarna errors found in the PDFs (`eval/suvarna_errata.csv`, 9 rules):

| Paper | Suvarna | PDF |
|---|---|---|
| Karelovic 2015 (c4cy00848k) | 7 MPa | 7 bar (p1, p4) |
| Karelovic 2015 | the 2000 L kg-1 h-1 rates one temperature step low (433/453/473 K) | Fig. 3a: the same rates at 180/200/225 C |
| Sharma 2021 (acsami.1c05586) | rows at 533 and 573 K | tested at 190-290 C only; rows dropped |
| Sharma 2021 | STY per g catalyst | Table 6 and Fig. 7D per g Cu, text per g catalyst, neither equals X x S x F; STY of these rows not scored |
| Shen 2021 (acscatal.0c05628) | 0.326 g g-1 h-1 under Ir/In2O3-1 | pristine In2O3 (SI p2 table); Ir/In2O3-1 gives 0.512 |
| Shen 2021 | 0.608 under Ir 10.8 wt% | Ir/In2O3-5 |
| Hengne 2018 (acsomega.8b00211) | 10.7 mg g-1 h-1 for Sn-free 5Ni/10InZrO2 | 5Ni/10InZrO2 makes no methanol (99 % CH4); the value is 5Ni10Sn/10InZrO2 |

### Results (40 papers)

| | TheMeCat (18) | Suvarna (20) | All 38 scored |
|---|---:|---:|---:|
| Curated entries recovered | 389 / 406 = 0.958 | 192 / 194 = 0.990 | **581 / 600 = 0.968** |
| Recovered with conversion and selectivity | 365 | 152 | 517 |

Gothe Table 4: 21/21 on every field.

Field accuracy (adjudicated, strict / loose):

| Field | TheMeCat | Suvarna |
|---|---|---|
| T, P, H2/CO2 | 1.000 | 1.000 |
| GHSV | 0.990 | 1.000 |
| X_CO2 | 0.913 / 0.987 | – |
| S_MeOH | 0.734 / 0.910 | – |
| STY, all | 0.713 / 0.771 | 0.530 / 0.799 |
| STY, printed in a table, the text or the SI | 141/143 | 28/31 (loose 31/31) |
| STY, read from a plot | 18/80 | 43/103 (loose 76/103) |

Printed values stay exact. The Suvarna STY mismatches are almost all plot readings on both sides (Suvarna digitised
the same figures); 17 of the 63 differ by more than 10 %.

Precision on the 21 new papers. 423 extracted entries have no Suvarna partner, mostly because the Suvarna set keeps
only the entries it used for its model. A random sample of 60 (`eval/batch4_unmatched_sample.csv`, seed 20261006) was
checked against the PDFs: **52/60 correct (0.87, 95 % CI 0.76-0.93)**. The 8 wrong ones:
- 3 with no temperature (a CH4-productivity-vs-conversion plot);
- 2 with the pressure left empty although the caption states ambient pressure;
- 2 plot misreads;
- 1 series confusion.

With the 192 matched entries, the estimated precision of the batch is (192 + 0.867 x 423) / 615 = 0.91.

## Status (2026-10-05)

| Step | Papers |
|---|---|
| Pilot set chosen | 13 DOIs (12 TheMeCat + Gothe 2025) |
| PDFs retrieved by nus-fetch | 11 (10 TheMeCat + Gothe). The other TheMeCat candidates are ScienceDirect, which nus-fetch marks `manual` (publisher bot check) |
| Extracted with gpt-5.5, first batch | 4: Gothe 2025, Wu 2017, Bansode 2013, Wang 2017 (RSC Adv.); OpenAI API, chat completions |
| Extracted with gpt-5.5, second batch | 7: Samson 2014, Chen 2019 (ACS Catal.), Wang 2017 (Sci. Adv.), Chen 2024 (Angew.), Yang 2024 (ChemPhysChem), Chen 2019 (Energy Technol.), Bahruji 2016; `--api-yes` route (local API-YES gateway, streamed Responses API), same prompt and schema |
| Extracted with gpt-5.5, third batch | 9 ScienceDirect papers downloaded by hand and re-identified by the DOI printed in each PDF: Rui 2017, Ghosh 2022, Sharma 2023, Zaman 2023, Ota 2012, Jiang 2020, Hou 2024, Shi 2020, Chou 2019; `--api-yes` route |
| Adjudicated against the PDFs | all 20 |
| Recall passes (figures, SI, SI figures) | all 20 papers; SI obtained for 19 (Shi 2020 has none on the public CDN) |

The first batch stopped when the OpenAI organisation ran out of credit (HTTP 429 `insufficient_quota`).
The second batch was extracted later through the local gateway. All 11 papers were then scored with the same `normalize.py` and `evaluate.py`.
Every mismatch was checked in the PDF: TheMeCat errors go to `eval/themecat_errata.csv`, extraction errors to `eval/field_mismatch_review.csv` and `eval/unmatched_review.csv`.
The current results are in "Recall passes". The 20-paper single-pass results, the 11-paper results and the 4-paper first run are kept below as the earlier stages.

## Pipeline

| Step | File | What it does |
|---|---|---|
| 1 | `fetch_papers.py` | DOI list -> PDFs through `D:\Tools\nus-fetch` (`fetch -f <list> -o pdf --headless --json`). Reads `pdf/last_run.json` and writes `fetch_manifest.json` (status, pages, `doi_in_pdf`, note). `manual` rows are listed and never automated. |
| 2 | `pdf_to_text.py` | Writes `text/<slug>.txt` and `.json`. Running text comes from pypdfium2, which keeps two-column layouts in reading order (pdfplumber interleaves the two columns line by line). Tables come from pdfplumber `extract_tables()`. Each page gets an `=== PAGE n ===` marker and is also rendered to `text/img/<slug>_p<n>.jpg` (scale 1.5). |
| 3 | `extract_records.py` | One chat-completions call per paper: system rules, then the full text, then all page images (`detail: high`). Output is strict JSON-schema (`schema.json`). Raw output goes to `out/raw/<slug>.json`, and every call is logged to `out/token_usage.csv`. Hard caps: 15 papers and 3,000,000 tokens, both summed from the log so they hold across reruns. |
| 1b | `fetch_si.py` (+ `si_docx2pdf.ps1`, `pdf_to_text.py --si`) | SI files into the git-ignored `si/`. Elsevier SI from the public CDN `ars.els-cdn.com/content/image/1-s2.0-<PII>-mmc<k>`; ACS, RSC, Wiley and Science SI through the publisher page in the nus-fetch browser profile (EZproxy), imported read-only (cookies not written back). Word SI is exported to PDF with WPS (read-only), then converted to `text_si/` with continuous page numbers. Bot checks are never automated; `si_manifest.json` records status per DOI. |
| 3b | `extract_records.py --pass figures / si / si_figures` | Recall passes, same schema and model. `figures`: full text plus high-resolution (2.2x) images of the main-text pages that carry a figure caption; the model digitises every plotted performance point (qualifier `~`) -> `out/raw_figures/`. `si`: SI text plus images of SI pages that mention performance quantities -> `out/raw_si/`. `si_figures`: the figure prompt on SI pages whose captions describe catalytic performance -> `out/raw_si_figures/`. Each pass is told the catalyst names the main pass used. |
| 4 | `normalize.py` | Converts to the model basis and merges the passes into `out/records_normalized.csv` (see below). |
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
| `STY_g_gcat_h`, `STY_g_gmetal_h` | Any of g, mg, kg, mol, mmol or umol MeOH per g or kg, per h, hour, min or s (M = 32.042 g/mol), split by basis. A basis written in the unit (`kgcat`, `gcat`, `gRe`, `gmetal`) overrides an extracted `sty_basis` of `other`/`unspecified` (the extracted label is kept in `sty_basis_extracted`). A per-metal STY is also expressed per g catalyst (x metal wt% / 100) when the record states the loading; `STY_gcat_from_metal` marks these. Per-area rates (umol m-2 h-1) stay in `STY_raw` and are flagged. |
| `metal_wt_pct` | Sum of the wt% loadings of the active metals |

Any value whose unit was not understood is reported in `flags`, never silently dropped.

Fixes made while adjudicating the second batch (genuine parsing bugs, found from unparsed units):

- `hour` / `hours` were not recognised. This dropped the GHSV of Chen 2024 and Wang 2017 Sci. Adv. (`mL gcat-1 hour-1`) and the 187.1 g gmetal-1 hour-1 STY.
- Bahruji 2016 rates in `mmol kgcat-1 h-1` were labelled `sty_basis: other` by the model, so 21 STY values were not used. The basis is now read from the unit.
- Per-metal STY (Chen 2024) had no per-catalyst value; it now gets one when the loading is stated.
- Two unanchored copies of the NmL/NL rule were removed.

Pass merge (recall work): records of the four passes are merged per entry (same paper; same catalyst by name key or word prefix; T within 1.5 K; P within 1 %; H2/CO2 within 2 %; GHSV within 5 % on either basis; time on stream within 0.5 h when both are given). A value printed in the main text beats a value printed in the SI, which beats any plot reading; a lower-ranked pass only fills empty or plot-read fields. `pass` gives the origin of an entry, `filled` the fields taken from another pass, `<field>_src` the source of each value (table, text, mixed, plot, SI, SI-plot). A converted STY above 10 g g-1 h-1 (5000 per g metal) is flagged `STY_implausible` and not used (Zaman SI Fig. SF9 prints its axis as "kg/g_cat/h").

Fixes made while adjudicating the third batch:

- `(STP)`, the hyphenated `g-cat`, `.` as a multiplication dot (`mmol/kgcat.h`, `mL/gcat.h`) and `.` as an abbreviation point (`gcat.-1`) were not parsed. This dropped the Jiang 2020 GHSV, the Shi 2020 STY and GHSV values, and the Chou 2019 GHSV and STY values from Fig. 5.
- A molar space velocity (`10 mmol gcat-1 min-1`, Ota 2012) is now converted at 22.414 NL/mol (0 °C, 1 atm).
- `GHSV_inert_free_NL_gcat_h` gives the same GHSV counted on reactants only, when the feed composition names N2/Ar/He (`inert_frac`). TheMeCat uses this convention for some papers (Chen 2024: 9000 x 0.96 = 8.64; Hou 2024: 18000 x 5/6 = 15; Jiang 2020: 26000 x 5/6.5 = 20) and the total feed for others (Yang 2024, Wu 2017).

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

Second batch (7 papers, `--api-yes` gateway, streamed Responses API). Three first attempts (anie, cphc, ente) returned no records and were rerun; they are kept in the log.

| Paper | Prompt | Output (of which reasoning) | Total | Records | Time |
|---|---:|---:|---:|---:|---:|
| Failed first attempts (3 calls) | 50,550 | 14,206 | 64,756 | 0 | 267 s |
| Chen 2024 Angew. | 37,157 | 13,300 (2,307) | 50,457 | 15 | 244 s |
| Yang 2024 ChemPhysChem | 29,440 | 25,331 (1,692) | 54,771 | 24 | 459 s |
| Chen 2019 Energy Technol. | 30,217 | 5,380 (1,552) | 35,597 | 5 | 49 s |
| Bahruji 2016 J. Catal. | 39,104 | 14,441 (1,549) | 53,545 | 21 | 262 s |
| Chen 2019 ACS Catal. | 39,165 | 25,355 (2,409) | 64,520 | 40 | 464 s |
| Samson 2014 ACS Catal. | 38,164 | 12,167 (1,034) | 50,331 | 19 | 224 s |
| Wang 2017 Sci. Adv. | 32,632 | 4,557 (1,351) | 37,189 | 4 | 106 s |
| **Second batch total** | **296,429** | **114,737** | **411,166** | | |

Third batch (9 Elsevier papers, `--api-yes`, one call each):

| Paper | Prompt | Output (of which reasoning) | Total | Records | Time |
|---|---:|---:|---:|---:|---:|
| Rui 2017 Appl. Catal. B | 30,522 | 4,888 (1,034) | 35,410 | 5 | 93 s |
| Ghosh 2022 Chem. Eng. J. | 37,810 | 12,318 (2,185) | 50,128 | 14 | 226 s |
| Sharma 2023 Fuel | 36,816 | 7,587 (2,510) | 44,403 | 7 | 65 s |
| Zaman 2023 Fuel | 26,390 | 21,023 (1,245) | 47,413 | 28 | 381 s |
| Ota 2012 J. Catal. | 34,718 | 7,671 (2,070) | 42,389 | 7 | 141 s |
| Jiang 2020 J. Catal. | 40,165 | 8,361 (1,034) | 48,526 | 10 | 155 s |
| Hou 2024 J. Environ. Sci. | 31,199 | 12,614 (1,428) | 43,813 | 15 | 233 s |
| Shi 2020 J. Saudi Chem. Soc. | 27,787 | 7,022 (1,784) | 34,809 | 8 | 130 s |
| Chou 2019 Appl. Catal. A | 29,670 | 23,625 (1,547) | 53,295 | 20 | 430 s |
| **Third batch total** | **295,077** | **105,109** | **400,186** | | |

Pilot total: 1,050,859 tokens (750,426 prompt, 300,433 output), 35 % of the 3 M cap.
At the list price above, that is about **USD 12.77**. Third-batch calls averaged 33 k prompt and 12 k output tokens per paper.

Recall passes (figure digitisation, SI and SI figures, all through `--api-yes`; `pass` column in `out/token_usage.csv`):

| Pass | Calls | Prompt | Output | Total | Cost at USD 5 / 30 per M |
|---|---:|---:|---:|---:|---:|
| figures (main-text plots) | 20 | 724,843 | 326,093 | **1,050,936** | USD 13.41 |
| si (SI text and tables) | 19 | 298,511 | 139,208 | **437,719** | USD 5.67 |
| si_figures (SI plots; Sci. Adv. and Ghosh rerun after widening the caption filter) | 12 | 224,255 | 140,063 | **364,318** | USD 5.32 |
| **Recall passes total** | 51 | 1,247,609 | 605,364 | **1,852,973** | **USD 24.40** |

The figure pass stayed under the 1.5 M stop threshold. The API-YES team plan hit its 300-minute usage window once (HTTP 429 `usage_limit_reached`); the remaining 18 calls ran after the reset. Pilot total: 2,903,832 tokens (USD 37.16), 48 % of the 6 M cap now set in `extract_records.py`.

Per paper (first batch, n = 5 calls): about 32 k prompt tokens (text ~20 k plus 8–16 page images), about 16 k output tokens and 100 s.
That is about **USD 0.64 per paper**. Output tokens are 75 % of the cost, because every number carries its own unit, location and page.

## Accuracy

### Matching rule (`evaluate.py`)

An extracted record and a TheMeCat row form a candidate pair when all of the following hold:

- same DOI;
- catalyst names match by one of these rules:
  - equal after normalisation (case, spaces, dashes and punctuation removed);
  - the shorter name's word tokens are a prefix of the longer name's tokens ('Cat-4.5' ~ 'Cat-4.5 H-In2O3/Al2O3/Al-fiber');
  - one edit apart with identical digits. This rule applies only when neither name has an exact or prefix partner in the same paper;
  - listed in `eval/name_aliases.json`.

  The aliases are the two Bahruji 2016 Table 4 / Table 5–6 name pairs, which the PDF shows are the same catalysts under the same conditions.
- |dT| <= 3 K and |dP|/P <= 5 %;
- H2/CO2 within 10 % when both are present;
- GHSV within 10 % when both are on a mass basis.

A one-to-one Hungarian assignment over the candidate pairs minimises |dT|/3 + |dP|/(0.05 P) + |dX| + |dS| (in pp).
Performance values therefore only break ties between entries at identical conditions.
Matching uses TheMeCat after the verified errata are applied.

The name rules were tightened during the second-batch adjudication, because the earlier rules paired different catalysts:

- 'contained anywhere' paired 'Ir1Pd1-In2O3(CP-PD)' with '2Ir1Pd1-In2O3(CP-PD)';
- difflib >= 0.85 paired '13% ZnO-ZrO2' with '10% ZnO-ZrO2' and 'In0.25/ZrO2' with 'In0.5/ZrO2', which hid a series-label error by pairing each value with the curve it was actually read from;
- the one-edit rule alone paired the 'PM' and 'GM' mixtures of Chen 2024.

The first-batch results are unchanged by the stricter rule.

Third-batch changes:

- The prefix rule is now also limited to names without an exact or alias partner. Otherwise 'In2O3' (pure oxide) paired with 'In2O3/HZSM-5' in Ghosh 2022.
- GHSV counts as matching when either the total-feed or the inert-free value is within tolerance (for candidate pairs: 10 %).
- A value printed as a bound ('>20 %', '<1') is correct when the curated value satisfies the bound.
- New aliases (all checked in the PDF): Jiang 'Cat-A(In2O3/ZrO2)' = 'In2O3/ZrO2'; Sharma 'In2O3' = 'bulk In2O3'; Ghosh 'In2O3/HZSM(Zeolite)' = 'In2O3/HZSM-5'; Zaman 'PZC(PdZn/CeO2)' = 'PZC'; Chou '1.5YIn2O3/ZrO2' (Table 1) = '1.5Y9In/ZrO2' (text).
- The 24 Chen 2024 GHSV errata cells from the second batch are withdrawn: TheMeCat's 8.64 and 51.84 are the printed values on the inert-free basis, not errors.

### Recall passes: figures and Supporting Information (20 papers, current)

Before = the main pass alone, scored with the same (current) errata, matcher and normaliser; after = main + SI + figures + SI figures merged.

#### Recall and precision, before vs after

| Paper | Curated | Recall before | Recall after | Extracted before / after | Precision (matched) before / after | Precision (reviewed) before / after |
|---|---:|---:|---:|---:|---:|---:|
| Wu 2017 | 22 | 22/22 = 1.00 | 22/22 = 1.00 | 26 / 26 | 0.85 / 0.85 | 1.00 / 1.00 |
| Bansode 2013 | 60 | 45/60 = 0.75 | 60/60 = 1.00 | 45 / 60 | 1.00 / 1.00 | 1.00 / 1.00 |
| Wang 2017 RSC Adv. | 4 | 4/4 = 1.00 | 4/4 = 1.00 | 4 / 12 | 1.00 / 0.33 | 1.00 / 1.00 |
| Chen 2024 | 26 | 11/26 = 0.42 | 26/26 = 1.00 | 15 / 51 | 0.73 / 0.51 | 0.80 / 0.90 |
| Yang 2024 | 24 | 24/24 = 1.00 | 24/24 = 1.00 | 24 / 24 | 1.00 / 1.00 | 1.00 / 1.00 |
| Chen 2019 Energy Technol. | 30 | 5/30 = 0.17 | 30/30 = 1.00 | 5 / 32 | 1.00 / 0.94 | 1.00 / 1.00 |
| Bahruji 2016 | 19 | 19/19 = 1.00 | 19/19 = 1.00 | 21 / 31 | 0.91 / 0.61 | 1.00 / 1.00 |
| Chen 2019 ACS Catal. | 17 | 16/17 = 0.94 | 16/17 = 0.94 | 40 / 47 | 0.40 / 0.34 | 0.72 / 0.68 |
| Samson 2014 | 20 | 18/20 = 0.90 | 18/20 = 0.90 | 19 / 19 | 0.95 / 0.95 | 1.00 / 1.00 |
| Wang 2017 Sci. Adv. | 49 | 1/49 = 0.02 | 43/49 = 0.88 | 4 / 71 | 0.25 / 0.61 | 1.00 / 0.69 |
| Rui 2017 | 15 | 5/15 = 0.33 | 15/15 = 1.00 | 5 / 39 | 1.00 / 0.39 | 1.00 / 1.00 |
| Ghosh 2022 | 14 | 7/14 = 0.50 | 7/14 = 0.50 | 14 / 14 | 0.50 / 0.50 | 0.86 / 0.86 |
| Sharma 2023 | 23 | 7/23 = 0.30 | 23/23 = 1.00 | 7 / 23 | 1.00 / 1.00 | 1.00 / 1.00 |
| Zaman 2023 | 28 | 28/28 = 1.00 | 28/28 = 1.00 | 28 / 46 | 1.00 / 0.61 | 1.00 / 0.65 |
| Ota 2012 | 3 | 3/3 = 1.00 | 3/3 = 1.00 | 7 / 13 | 0.43 / 0.23 | 1.00 / 1.00 |
| Jiang 2020 | 2 | 2/2 = 1.00 | 2/2 = 1.00 | 10 / 10 | 0.20 / 0.20 | 1.00 / 1.00 |
| Hou 2024 | 30 | 14/30 = 0.47 | 29/30 = 0.97 | 15 / 30 | 0.93 / 0.97 | 0.93 / 0.97 |
| Shi 2020 | 7 | 7/7 = 1.00 | 7/7 = 1.00 | 8 / 8 | 0.88 / 0.88 | 1.00 / 1.00 |
| Chou 2019 | 20 | 20/20 = 1.00 | 20/20 = 1.00 | 20 / 20 | 1.00 / 1.00 | 1.00 / 1.00 |
| **Total** | 413 | 258/413 = 0.62 | 396/413 = 0.96 | 317 / 576 | 0.81 / 0.69 | 0.95 / 0.89 |

- Recall rose from 0.62 to **0.96** (258 -> 396 of 413 curated entries). Gothe Table 4 stays 21/21 on every field.
- Precision on matched entries fell (0.81 -> 0.69) because the passes add many genuine entries that TheMeCat does not list. After PDF review of the 180 unmatched extracted entries, precision is **0.89** (0.95 before):
  - 120 are correct: 74 genuine entries TheMeCat omits (for example Rui GHSV and pressure series, Bahruji Fig. 10a, Jiang H2O series), 43 additional time-on-stream points (first/last point of stability runs; Chen 2024 SI Figs. S21–S29, Ota Fig. 11A, c6ra SI Fig. S4), 3 duplicates;
  - 61 are wrong: 22 plot misreads (Sci. Adv. SI figs. S17/S18 above all), 19 entries without a temperature (Zaman SI Fig. SF8 plots selectivity against conversion), 13 series confusions, 4 incomplete, 3 wrong names.

#### The 17 curated entries still missing

| Cause | Entries |
|---|---:|
| Values the paper quotes from another study (Ghosh pure In2O3, ref. [21]; excluded by the prompt) | 7 |
| Wang Sci. Adv.: curated duplicates of the 330 C / 2 MPa centre point (3 series), the 30 % and 38 % composition points the figure pass skipped, the 4:1 330 C point, the supported 13%ZnO/ZrO2 row | 6 |
| Zero-activity rows (Samson 2, bulk ZrO2 1) | 3 |
| TheMeCat label error (Hou Au/In2O3-NP 200 C listed as Au/In2O3-HM) | 1 |

#### Field accuracy, before vs after

| Field | Coverage before -> after | Strict adjudicated before -> after | Loose adjudicated before -> after | Strict raw before -> after |
|---|---|---|---|---|
| T | 1.00 -> 1.00 | 1.000 -> 1.000 | 1.000 -> 1.000 | 1.000 -> 1.000 |
| P | 1.00 -> 1.00 | 1.000 -> 1.000 | 1.000 -> 1.000 | 0.826 -> 0.848 |
| H2/CO2 | 1.00 -> 0.99 | 1.000 -> 1.000 | 1.000 -> 1.000 | 0.984 -> 0.990 |
| GHSV | 0.60 -> 0.79 | 0.979 -> **0.990** | 0.979 -> 0.990 | 0.846 -> 0.927 |
| X_CO2 | 0.80 -> **1.00** | 0.913 -> **0.914** | 0.995 -> 0.987 | 0.869 -> 0.891 |
| S_MeOH | 0.88 -> **1.00** | 0.739 -> **0.739** | 0.913 -> 0.911 | 0.720 -> 0.731 |
| STY | 0.49 -> 0.60 | 0.436 -> **0.697** | 0.573 -> 0.754 | 0.094 -> 0.075 |

Strict accuracy by source of the value (adjudicated), after:

| Source | X_CO2 | S_MeOH | STY | GHSV |
|---|---|---|---|---|
| Table (main text) | 58/58 | 58/58 | 34/40 | 33/36 |
| Text | 5/5 | 5/5 | 0/1 | 5/5 |
| Mixed (text + figure) | 22/24 | 23/25 | 12/19 | 16/16 |
| Plot (main-text figures) | 131/153 (loose 152) | 59/131 (loose 106) | 6/61 (loose 14) | 183/183 |
| SI (printed) | **117/117** | **113/114** | **107/107** | 34/34 |
| SI plot | 29/39 (loose 35) | 17/39 (loose 31) | - | 26/26 |

Values printed in the SI are as exact as those in main-text tables; plot readings are what limits accuracy. Before the recall passes, plot readings scored X 99/115, S 64/116, STY 5/57.

#### Field mismatches and failure modes (`eval/field_mismatch_review.csv`, all 203 strict mismatches)

| Failure mode | All | From the recall passes |
|---|---:|---:|
| Plot reading error on the right series and point | 118 | 59 |
| Paper internally inconsistent (Chou, Shi, Ghosh) | 24 | 0 |
| Axis misread (secondary or broken axis) | 18 | 18 |
| TheMeCat differs from the plotted value; extraction follows the plot | 18 | 9 |
| Series or point confusion | 17 | 4 |
| Basis conversion | 5 | 0 |
| Printed value rounded | 2 | 0 |
| TheMeCat rounding | 1 | 0 |

New failure mode from the figure passes, **axis misread**:
- Sharma Fig. 10b: the red series belong to the right axis.
- Rui Fig. 1a: selectivity on the right axis, 4–5 pp off.
- Sci. Adv. SI fig. S2: broken right axis, X about 30 % high.
- Sharma's case also exposed a TheMeCat error (below).

#### TheMeCat errors found in this round (`eval/themecat_errata.csv`)

111 new errata cells in 111 rows (179 rows, 271 cells in total). Most come from SI tables that TheMeCat transcribed with recomputed or coarse values:

| Paper | TheMeCat | PDF / SI | Cells |
|---|---|---|---:|
| Bansode 2013 | STY in steps of about 0.003 g g-1 h-1 | ESI Tables S1–S3 print CH3OH yield in mg gcat-1 h-1 (e.g. 1.8 vs 2.9) | 52 |
| Chen 2019 Energy Technol. | STY about 6 % high | SI Table S1 (printed STY agrees with X x S x F) | 30 |
| Chen 2019 ACS Catal. | STY of 15 entries; second In0.1/ZrO2 553 K row | SI Table S5 STY; that row is bulk In2O3 at 280 C (renamed instead of dropped; STY 0.171) | 17 |
| Sharma 2023 | ZrO2 and In1/ZrO2 selectivity read on the wrong axis | Fig. 10b red series use the right axis (confirmed by the printed 57.3 %) | 6 |
| Wang 2017 Sci. Adv. | table S2 STY | SI table S2 printed STY (mg/(g h)) | 5 |
| Rui 2017 | In2O3 and Pd-I/In2O3 STY at 300 C | SI Tables S1/S2: 0.352 and 0.814 | 2 |

`evaluate.py` gained an errata action `rename` (a row that carries another catalyst's data).

#### SI files

| Status | DOIs |
|---|---|
| Obtained, public CDN (Elsevier mmc1, Word or PDF) | 10.1016/j.apcata.2019.117144, j.apcatb.2017.06.069, j.cej.2022.135090, j.fuel.2022.125878, j.fuel.2023.127927, j.jcat.2012.05.020, j.jcat.2016.03.017, j.jcat.2020.01.014, j.jes.2023.05.010 |
| Obtained through the publisher page (EZproxy, nus-fetch profile, read-only) | 10.1021/acs.iecr.7b01464, acscatal.5c05984, acscatal.9b01869, cs500979c (2 files); 10.1039/c2cy20604h, c6ra28305e; 10.1002/anie.202401168, cphc.202300530, ente.201800747; 10.1126/sciadv.1701290 |
| Not found / manual check | 10.1016/j.jscs.2019.09.002 (Shi 2020): no mmc file on the public CDN; the ScienceDirect page is bot-checked and was not automated. The article may have no SI |

No bot check was met on any SI download.

#### Code changes in this round

- `extract_records.py`: `--pass figures/si/si_figures`, `--pass-cap` (1.5 M), cap raised to 6 M, `pass` column in the usage log.
- `fetch_si.py`, `si_docx2pdf.ps1`, `pdf_to_text.py --si`.
- `normalize.py`: pass merge, STY range check.
- `evaluate.py`: per-field source, a 0.05 cost tie-break that prefers the main pass, errata action `rename`.

The prompts contain only the paper (main text or SI) and the catalyst names of the main pass. No TheMeCat or evaluation data enters any prompt.

### Accuracy, 20 papers (single main pass, as reported before the recall passes)

TheMeCat has 413 entries for the 19 DOIs; one is dropped after adjudication, leaving 412.
Tolerances: T ±1 K; P, GHSV and STY ±1 % (loose ±5 %); H2/CO2 ±0.05; X and S ±0.5 pp (loose ±2 pp).

#### Field-level accuracy (257 matched entries)

| Field | Curated | Extracted | Coverage | Strict (adjudicated) | Loose (adjudicated) | Strict (raw TheMeCat) | Loose (raw TheMeCat) |
|---|---:|---:|---:|---:|---:|---:|---:|
| T | 257 | 257 | 1.00 | **1.000** | 1.000 | 1.000 | 1.000 |
| P | 257 | 257 | 1.00 | **1.000** | 1.000 | 0.825 | 0.825 |
| H2/CO2 | 257 | 257 | 1.00 | **1.000** | 1.000 | 0.984 | 1.000 |
| GHSV | 239 | 143 | 0.60 | **0.979** | 0.979 | 0.846 | 0.846 |
| X_CO2 | 257 | 206 | 0.80 | **0.913** | 0.995 | 0.869 | 0.961 |
| S_MeOH | 233 | 206 | 0.88 | **0.743** | 0.913 | 0.723 | 0.883 |
| STY | 239 | 117 | 0.49 | **0.410** | 0.564 | 0.094 | 0.282 |

- GHSV: 74 curated values are not comparable because the paper gives only a volume-based GHSV (h-1). The 3 GHSV misses are the Ota molar space velocity converted at 0 °C (TheMeCat at about 25 °C).
- Third batch alone (9 papers, 93 matched entries, adjudicated strict / loose):
  - X_CO2 0.907 / 0.988
  - S_MeOH 0.605 / 0.919
  - STY 0.375 / 0.411
  - GHSV 0.964 / 0.964
- STY below 0.5 is driven by two papers whose printed or plotted methanol rates disagree with their own X x S x F (Chou 2019: 18 values, about 25–30 % lower; Shi 2020: 5 values, 2–3x higher). TheMeCat recomputes these from X x S x F; the extraction reports the paper's numbers.

Strict accuracy (adjudicated) by source type of the extracted value:

| Source | X_CO2 | S_MeOH | STY |
|---|---|---|---|
| Table | 58/58 | 58/58 | 34/40 |
| Text | 5/5 | 5/5 | 0/1 |
| Mixed (text + figure) | 26/28 | 26/28 | 9/19 |
| Figure (plot reading, `~`) | 99/115 | 64/115 | 5/57 |

All six table-STY misses are reproduced exactly from the PDF:

- 5 are Shi 2020 yields, where the paper's printed methanol yield is 2-3x its own X x S x F;
- 1 is Ota PdMgAl, which TheMeCat rounds to 4 decimals.

#### Entry-level recall and precision

| DOI | Curated | Extracted | Matched | Matched with X and S | Recall | Precision (matched only) | Precision (with PDF review) |
|---|---:|---:|---:|---:|---:|---:|---:|
| 10.1021/acs.iecr.7b01464 (Wu 2017) | 22 | 26 | 22 | 22 | 1.00 | 0.85 | 1.00 |
| 10.1039/c2cy20604h (Bansode 2013) | 60 | 45 | 45 | 20 | 0.75 | 1.00 | 1.00 |
| 10.1039/c6ra28305e (Wang 2017 RSC Adv.) | 4 | 4 | 4 | 4 | 1.00 | 1.00 | 1.00 |
| 10.1002/anie.202401168 (Chen 2024) | 26 | 15 | 11 | 10 | 0.42 | 0.73 | 0.80 |
| 10.1002/cphc.202300530 (Yang 2024) | 24 | 24 | 24 | 0 | 1.00 | 1.00 | 1.00 |
| 10.1002/ente.201800747 (Chen 2019) | 30 | 5 | 5 | 2 | 0.17 | 1.00 | 1.00 |
| 10.1016/j.jcat.2016.03.017 (Bahruji 2016) | 19 | 21 | 19 | 19 | 1.00 | 0.90 | 1.00 |
| 10.1021/acscatal.9b01869 (Chen 2019) | 16 | 40 | 15 | 0 | 0.94 | 0.38 | 0.73 |
| 10.1021/cs500979c (Samson 2014) | 20 | 19 | 18 | 18 | 0.90 | 0.95 | 1.00 |
| 10.1126/sciadv.1701290 (Wang 2017 Sci. Adv.) | 49 | 4 | 1 | 1 | 0.02 | 0.25 | 1.00 |
| 10.1016/j.apcatb.2017.06.069 (Rui 2017) | 15 | 5 | 5 | 1 | 0.33 | 1.00 | 1.00 |
| 10.1016/j.cej.2022.135090 (Ghosh 2022) | 14 | 14 | 7 | 7 | 0.50 | 0.50 | 0.86 |
| 10.1016/j.fuel.2022.125878 (Sharma 2023) | 23 | 7 | 7 | 2 | 0.30 | 1.00 | 1.00 |
| 10.1016/j.fuel.2023.127927 (Zaman 2023) | 28 | 28 | 28 | 28 | 1.00 | 1.00 | 1.00 |
| 10.1016/j.jcat.2012.05.020 (Ota 2012) | 3 | 7 | 3 | 3 | 1.00 | 0.43 | 1.00 |
| 10.1016/j.jcat.2020.01.014 (Jiang 2020) | 2 | 10 | 2 | 2 | 1.00 | 0.20 | 1.00 |
| 10.1016/j.jes.2023.05.010 (Hou 2024) | 30 | 15 | 14 | 14 | 0.47 | 0.93 | 0.93 |
| 10.1016/j.jscs.2019.09.002 (Shi 2020) | 7 | 8 | 7 | 7 | 1.00 | 0.88 | 1.00 |
| 10.1016/j.apcata.2019.117144 (Chou 2019) | 20 | 20 | 20 | 20 | 1.00 | 1.00 | 1.00 |
| **Total** | **412** | **317** | **257** | **180** | **0.62** | **0.81** | **0.95** |

The 60 unmatched extracted entries (`eval/unmatched_review.csv`):

- 43 are confirmed correct by the PDF. Of these, 18 are from the third batch:
  - Ghosh Fig. 8b 3:1 bed (5);
  - the Ota CuZnAl reference and 3 steady-state rates from the text;
  - Jiang's H2O co-feed series (8);
  - Shi Fig. 7 at GHSV 3000.
- 17 are wrong (3 in the third batch): 2 Ghosh Fig. 8b misreads, and the Hou Au/In2O3-NP 200 °C selectivity, extracted as 70 % where the plot shows about 48 %.

#### Third batch: what the per-paper gaps were

- **Hou 2024** (0/30 matched before review, 14/30 after):
  - The paper prints GHSV = 18,000 mL gcat-1 h-1 (60 mL/min over 0.2 g, p3 and p8). TheMeCat's 15 is the inert-free value (H2:CO2:Ar = 4:1:1), so the 10 % GHSV gate rejected every pair. Matching now accepts either basis.
  - The 16 curated entries still missing: 15 pure In2O3-HM/NP/NS rows from Appendix A Fig. S4 (SI), and one second 'Au/In2O3-HM' 473 K row that is the NP point under the wrong label in TheMeCat.
- **Jiang 2020** (10 extracted vs 2 curated):
  - TheMeCat 'Cat-A(In2O3/ZrO2)' is the paper's In2O3/ZrO2; an alias was added.
  - The 8 extra entries are the H2O co-feed series of Fig. 1 (0.1–3.8 mol% H2O). All are correct against the plot; TheMeCat keeps only the dry runs.
  - The GHSV unit `mL (STP) g-cat-1 h-1` was a normalisation bug, now fixed.
- **Ghosh 2022** (precision 0.5 -> 0.86):
  - The 7 unmatched extracted entries are a second catalyst bed (In2O3:HZSM-5 = 3:1, Fig. 8b) that TheMeCat does not list; 5 are correct, 2 misread.
  - The 7 missed curated entries are pure In2O3 from Fig. 2a/c. The paper marks them as data from its ref. [21], and the prompt excludes values quoted from other papers.
  - TheMeCat's methanol selectivity for In2O3/HZSM-5 is 100x too high (see errata).
- **Ota 2012** (7 vs 3): the 4 extra entries are the CuZnAl reference in Table 2 (TheMeCat omits it) and the three steady-state rates printed in Section 3.4.1. These belong to the same catalysts as Table 2 but come from the Fig. 11A time-on-stream runs.
- **Rui 2017** (5 vs 15): TheMeCat's 15 entries come from main-text Fig. 1a/b. The model did not digitise that figure ("small plotted points"). It extracted the 4 Table 2 rates and the printed 300 °C headline values; the 10 missing entries are Fig. 1 points.
- **Chou 2019** (20 vs 20): every Fig. 5 point matched after the `gcat.-1` unit fix and the Table 1 name alias. The STY values are the Fig. 5c rates, which the paper itself prints in Table 1 (0.465 / 0.420 / 0.420 / 0.241). TheMeCat's STY is about 25–30 % higher because it recomputes from X x S x F, which the paper's own rates do not satisfy. This is classified as a paper inconsistency, not an errata.
- **Sharma 2023** (7 vs 23): all 16 missing entries are main-text Fig. 9/10 points, which the model chose not to digitise. Every value it took from the text is correct, and five of them corrected TheMeCat.

#### Where all 155 missing curated entries come from

| Cause | Entries | Papers |
|---|---:|---|
| Main-text figure not digitised | 74 | Wang Sci. Adv. Fig. 1 (32), Chen 2019 Energy Technol. Fig. 4a/b (16), Sharma Fig. 9/10 (16), Rui Fig. 1 (10) |
| Supporting Information only (not fetched) | 67 | Bansode (15), Chen 2019 Energy Technol. (9), Chen 2024 (12), Wang Sci. Adv. (16), Hou Fig. S4 (15) |
| Values quoted from another paper (excluded by the prompt) | 7 | Ghosh pure In2O3 (ref. [21]) |
| Zero-activity rows skipped | 3 | Samson (2), Chen 2019 ACS Catal. (1) |
| Extracted under the wrong catalyst name | 3 | Chen 2024 Fig. 4b |
| TheMeCat label error | 1 | Hou: Au/In2O3-NP 200 °C listed as a second Au/In2O3-HM row |

#### Field mismatches checked against the PDF (`eval/field_mismatch_review.csv`)

| Failure mode | 20 papers | Third batch | Where (third batch) |
|---|---:|---:|---|
| Plot reading error on the right series and point | 69 | 38 | Zaman Fig. 6A/7b (16), Hou Fig. 6a (16), Chou Fig. 5 (4), Ghosh, Jiang |
| Series or point confusion | 26 | 3 | Ghosh Fig. 2b selectivity series read in reverse order (2), Hou NP point read from the NS curve (1) |
| Paper internally inconsistent | 24 | 24 | Chou rates vs its own X x S x F (18); Shi printed yields (5); Ghosh Fig. 2c vs Fig. 8b conversion for the same bed (1) |
| TheMeCat value differs from the plotted value; extraction closer to the plot | 12 | 9 | Hou Fig. 6b STY. TheMeCat computes STY from X x S x feed; differences are below the errata threshold |
| Printed value rounded | 6 | 2 | Ghosh text "25 %", Sharma text "68 %" |
| Basis conversion | 5 | 3 | Ota molar space velocity, 0 °C vs 25 °C molar volume |
| TheMeCat rounding (4 decimals) | 1 | 1 | Ota PdMgAl STY |

Rule for STY errata: a printed STY overrides TheMeCat unless it disagrees with the paper's own X x S x F by more than about 20 %. Those cases are classified as paper inconsistency. Bansode (9 %), Bahruji (6 %) and Rui (1 %) pass this check; Shi and Chou do not.

#### TheMeCat errors found against the PDFs (third batch)

There are 160 corrected cells in 68 errata rows. The third batch adds 40 cells in 28 rows. The 24 Chen 2024 GHSV cells of batch 2 are withdrawn (inert-free basis).

| DOI | TheMeCat | PDF | Cells |
|---|---|---|---:|
| Ghosh 2022 | In2O3/HZSM-5 S(CH3OH) 0–90 % and the STY computed from it | Fig. 2b p5: the selectivity is on the 0–1 % segment of the broken axis, so TheMeCat is 100x too high | 14 |
| Zaman 2023 | 0.5Ca-PZC X at 5 / 10 / 40 / 50 bar: 2.5 / 8.6 / 11.8 / 5.4 % | Fig. 7b p8: 8.4 / 11.8 / 13.7 / 10.0 %; p7 text "~9 % at 5 bar", "~14 % at 40 bar" | 4 |
| Zaman 2023 | STY at 5 bar 0.0188; Table 1 STY of five catalysts | p7 text 62.66 g/kgcat/h; Table 1 p3 printed 105.0 / 89.6 / 122.1 / 116.4 / 90.7 g/kgcat/h | 6 |
| Rui 2017 | STY of Pd-I and Pd-P at 200 / 225 C and Pd-P at 300 C | Table 2 p8 rates (1.9 / 7.4 / 4.1 / 16.7 x 10-7 mol s-1 gcat-1); 0.89 g h-1 gcat-1 in the abstract | 5 |
| Sharma 2023 | In13/ZrO2 X 0.68 / 8.1 / 12.8 %; STY 0.1498 and 0.0040 | p8 text: 0.6 / 7.9 / 12.7 %; 0.17 and 0.007 gMeOH h-1 gcat-1 | 5 |
| Hou 2024 | Au/In2O3-NS STY 0.3028 at 300 C; three 275 C STY values | p8 text: 0.32; Fig. 6b bars 0.161 / 0.106 / 0.089 | 4 |
| Ota 2012 | PdMgGa STY 0.0229 | Table 2 p11: 10.5 umol min-1 gcat-1 = 0.0202 | 1 |
| Jiang 2020 | In2O3/ZrO2 STY 0.0815 | p3 text: 2.75 mol kg-1 h-1 = 0.0881 | 1 |

### Accuracy, 11 papers (second stage, kept as reported)

Computed before the third-batch rule changes. Two things have changed since: the Chen 2024 GHSV errata in this section are withdrawn, and GHSV is now scored on either basis.

Tolerances, accuracy and coverage are defined as in the first batch below.
TheMeCat has 271 entries for the 10 DOIs; one is dropped after adjudication (see errata), leaving 270.

#### Field-level accuracy (164 matched entries)

| Field | Curated | Extracted | Coverage | Strict (adjudicated) | Loose (adjudicated) | Strict (raw TheMeCat) | Loose (raw TheMeCat) |
|---|---:|---:|---:|---:|---:|---:|---:|
| T | 164 | 164 | 1.00 | **1.000** | 1.000 | 1.000 | 1.000 |
| P | 164 | 164 | 1.00 | **1.000** | 1.000 | 0.726 | 0.726 |
| H2/CO2 | 164 | 164 | 1.00 | **1.000** | 1.000 | 0.976 | 1.000 |
| GHSV | 146 | 60 | 0.41 | **1.000** | 1.000 | 0.500 | 0.683 |
| X_CO2 | 164 | 120 | 0.73 | **0.917** | 1.000 | 0.875 | 0.967 |
| S_MeOH | 140 | 120 | 0.86 | **0.842** | 0.908 | 0.842 | 0.908 |
| STY | 146 | 61 | 0.42 | **0.443** | 0.705 | 0.115 | 0.361 |

- GHSV: 64 curated values are not comparable because the paper gives only a volume-based GHSV (h-1).
- Second batch alone (7 papers, 93 matched entries, adjudicated strict / loose):
  - X_CO2 0.865 / 1.000
  - S_MeOH 0.754 / 0.846
  - STY 0.382 / 0.673
  - GHSV 1.000 / 1.000

Strict accuracy (adjudicated) by source type of the extracted value:

| Source | X_CO2 | S_MeOH | STY |
|---|---|---|---|
| Table | 45/45 | 45/45 | 23/23 |
| Text | 5/5 | 5/5 | 0/1 (printed value rounded to 2 significant figures) |
| Mixed (text + figure) | 13/14 | 14/14 | 3/9 |
| Figure (plot reading, `~`) | 47/56 | 37/56 | 1/28 |

Every value printed in a table is exact. All remaining errors are plot readings, printed values rounded to two significant figures, or a per-metal to per-catalyst conversion.
`eval/field_accuracy_by_source.csv` has the full table.

#### Entry-level recall and precision

| DOI | Curated | Extracted | Matched | Matched with X and S | Recall | Precision (matched only) | Precision (with PDF review) |
|---|---:|---:|---:|---:|---:|---:|---:|
| 10.1021/acs.iecr.7b01464 (Wu 2017) | 22 | 26 | 22 | 22 | 1.00 | 0.85 | 1.00 |
| 10.1039/c2cy20604h (Bansode 2013) | 60 | 45 | 45 | 20 | 0.75 | 1.00 | 1.00 |
| 10.1039/c6ra28305e (Wang 2017 RSC Adv.) | 4 | 4 | 4 | 4 | 1.00 | 1.00 | 1.00 |
| 10.1002/anie.202401168 (Chen 2024) | 26 | 15 | 11 | 10 | 0.42 | 0.73 | 0.80 |
| 10.1002/cphc.202300530 (Yang 2024) | 24 | 24 | 24 | 0 | 1.00 | 1.00 | 1.00 |
| 10.1002/ente.201800747 (Chen 2019) | 30 | 5 | 5 | 2 | 0.17 | 1.00 | 1.00 |
| 10.1016/j.jcat.2016.03.017 (Bahruji 2016) | 19 | 21 | 19 | 19 | 1.00 | 0.90 | 1.00 |
| 10.1021/acscatal.9b01869 (Chen 2019) | 16 | 40 | 15 | 0 | 0.94 | 0.38 | 0.73 |
| 10.1021/cs500979c (Samson 2014) | 20 | 19 | 18 | 18 | 0.90 | 0.95 | 1.00 |
| 10.1126/sciadv.1701290 (Wang 2017 Sci. Adv.) | 49 | 4 | 1 | 1 | 0.02 | 0.25 | 1.00 |
| **Total** | **270** | **203** | **164** | **96** | **0.61** | **0.81** | **0.93** |

Notes on the metrics:

- Precision with review counts as correct the unmatched extracted entries that the PDF confirms. There are 25 of these:
  - 23 genuine entries that TheMeCat leaves out (Wu Table 2 x4, 14 Fig. 5a temperatures in Chen 2019 ACS Catal., the ZrO2 support run in Samson, 3 printed values in Wang Sci. Adv., the 100 h point in Chen 2024);
  - 2 correct but duplicated Bahruji reference runs (the same 5% Pd/ZnO SI measurement is repeated in Tables 4, 5 and 6).
- 14 unmatched extracted entries are wrong (`eval/unmatched_review.csv`):
  - 9 series confusions in Chen 2019 ACS Catal. Fig. 5a. The figure has no In0.25/ZrO2 curve, and the model shifted the In0.5 and In1 curves one label down.
  - 2 plot misreads (2.8 and 3.8 pp).
  - 3 Chen 2024 Fig. 4b points with correct STY values whose catalyst_name lacks the loading prefix (2Ir1Pd1 / 4Ir1Pd1 / 10Ir1Pd1).
- Recall counts an entry as found when it matches, even if some of its values are wrong. Value errors are counted in the field table.

#### Where the missing curated entries come from

106 of the 270 curated entries were not found:

| Cause | Entries | Papers |
|---|---:|---|
| Supporting Information only (not fetched) | 52 | Bansode ESI Table S3 (15); Chen 2019 Energy Technol. Table S1 (9: H-In2O3/Al2O3 powder and In2O3-IWI reference); Chen 2024 Figs. S22, S24-S29 (12); Wang Sci. Adv. fig. S2 and table S2 (16) |
| Main-text figure the model chose not to digitise | 48 | Wang Sci. Adv. Fig. 1A (12) and Fig. 1B (20); Chen 2019 Energy Technol. Fig. 4a/b (16) |
| Zero-activity rows skipped | 3 | Samson Table 6 (Cu/ZrO2(I) at 473 and 493 K, X = 0); bulk ZrO2 in Chen 2019 ACS Catal. |
| Extracted under the wrong catalyst name | 3 | Chen 2024 Fig. 4b (2Ir1Pd1 / 4Ir1Pd1 / 10Ir1Pd1) |

The three large gaps:

- **Wang 2017 Sci. Adv.** (4 extracted, 49 curated):
  - Fig. 1A gives the composition series at 320 C (12 entries) and Fig. 1B the temperature series at H2/CO2 = 3 and 4 (21 entries). Both are main-text plots, and the model skipped them; its extraction note says they are dense and not printed as numbers. One Fig. 1B point (315 C, 4:1) is printed in the text and was matched.
  - The remaining 16 entries are not in the main text. They are the pressure, H2/CO2 and GHSV series (fig. S2, 11), the mechanically mixed and supported catalysts (table S2, 4), and one 13 % ZnO-ZrO2 point at 300 C / 2 MPa.
  - The model did not miss any number printed in the text: all 4 of its text values are correct.
- **Chen 2019 Energy Technol.** (5 vs 30):
  - The paper lists the full data set in SI Table S1 (p4 text), and TheMeCat transcribes it.
  - 20 of the 30 points (Cat-1.5/3.0/4.5/6.0 at 250-350 C) are also plotted in main-text Fig. 4a/b, which the model did not digitise. Its four 325 C entries came from the printed bar labels of Fig. 4c and from the text.
  - The 10 H-In2O3/Al2O3 and In2O3-IWI rows are SI-only, apart from the IWI 325 C values printed in the text, which were extracted.
- **Chen 2024 Angew.** (15 vs 26):
  - 12 TheMeCat entries come from SI figures: In2O3, Ir1- and Pd1-single-atom catalysts (Fig. S22); Pd1Ir1/Pd1Pd1/Ir1Ir1 (Figs. S24-S25); GHSV 18 and 36 L g-1 h-1 (Figs. S27-S28); 225 and 275 C (Fig. S29).
  - The other 3 are main-text Fig. 4b points whose names the model got wrong.
  - Every number printed in the main text (10.5 / 97 / 43.7 at the standard condition, the 54 L g-1 h-1 values, the 200 and 300 C values, the 100 h values) was extracted.

#### Field mismatches checked against the PDF (`eval/field_mismatch_review.csv`)

63 strict mismatches remain after the errata (11 papers):

| Failure mode | Count | Where |
|---|---:|---|
| Plot reading precision (right series and point, outside the strict tolerance) | 31 | Yang Fig. 9a/b (20), Chen 2019 ACS Catal. Fig. 5a/b (5), Chen 2024 Fig. 4a (3), Bansode Fig. 6/8 (3) |
| Series or point confusion (value belongs to another curve, bar or temperature) | 23 | Yang Fig. 9b crossing STY curves (8) and Fig. 9a (3); Chen 2019 ACS Catal. Fig. 5a, no In0.25 curve (8); Chen 2024 Fig. 4a GM/PM bars swapped (4) |
| Printed value rounded to 2 significant figures; TheMeCat uses the SI table | 4 | Chen 2019 Energy Technol. STY 0.14 / 0.16 / 0.20 / 0.11 |
| Main-text bar and TheMeCat (SI) disagree; extraction is closer to the bar | 3 | Chen 2019 ACS Catal. Fig. 5b STY (In0.5, In1, In5); cannot be resolved without the SI |
| Basis conversion: paper prints STY per g metal; per g catalyst depends on the loading used | 2 | Chen 2024 (0.69 wt% from the text; TheMeCat implies 0.67-0.68) |

Rule used: a plot reading more than 5 % of the axis range from the correct point, and closer to another plotted point, counts as a confusion.
The plot readings used for the review are in `eval/make_field_mismatch_review.py`.

#### TheMeCat errors found against the PDFs (all 11 papers)

There are 144 corrected cells in 42 errata rows. The second batch adds 75 cells in 35 rows; the first batch is listed further down.

| DOI | TheMeCat | PDF | Cells |
|---|---|---|---:|
| 10.1016/j.jcat.2016.03.017 (Bahruji 2016) | GHSV 36.2 NL g-1 h-1 | 30 ml/min over 0.5 g = 3.6 (p3; Tables 4-6 footnotes p10-11) | 19 |
| 10.1016/j.jcat.2016.03.017 | STY 0.010-0.79 g g-1 h-1 | Printed CH3OH rates 52-2470 mmol kgcat-1 h-1 = 0.0017-0.079 (Tables 4-6). TheMeCat is about 10x high, consistent with its 10x GHSV | 16 |
| 10.1002/cphc.202300530 (Yang 2024) | X_CO2 of In0.25Cr1.75O3 and In0.12Cr1.88O3 | Fig. 9a p7: the two curves are swapped in TheMeCat (its STY for the same rows follows Fig. 9b under the right names) | 8 |
| 10.1002/cphc.202300530 | In2O3 STY at 533 / 553 / 573 K | Fig. 9b p7: 0.57 / 0.43 / 0.72 mmol g-1 h-1; TheMeCat rotates the three values | 3 |
| 10.1002/anie.202401168 (Chen 2024) | GHSV 8.64 and 51.84 | 9000 and 54000 mL gcat-1 hour-1 printed (p7-p9) | 24 |
| 10.1002/anie.202401168 | 473 K: 5.6 / 99.7; 573 K: 14.4 / 71.2 | p9 text: 5.5 / 100 and 14.3 / 71.3 | 4 |
| 10.1021/acscatal.9b01869 (Chen 2019) | Second In0.1/ZrO2 553 K row: X 2.2, S 60.7 | Contradicts Fig. 5a (S = 21 %), the p5 text (CO selectivity close to 80 %) and TheMeCat's own first row; dropped | 1 row |

#### STY: why accuracy was low and what changed

Before this adjudication, strict STY accuracy was 0.20 on 40 compared values. Three causes, in order of size:

1. **Normalisation bugs (fixed in `normalize.py`).** These hid 21 values:
   - Bahruji `mmol kgcat-1 h-1` rates labelled basis `other`: 19 compared;
   - the unparsed `hour`;
   - per-metal STY with no per-catalyst value: 2 compared.

   There was no mg/g, per-mL or per-metal mix-up in the conversion itself: every STY printed as a number in a table or text converts exactly.
2. **TheMeCat STY errors.** 25 cells are corrected: Bahruji 10x (16), Yang In2O3 rotation (3), and the 6 first-batch cells. Raw strict accuracy is 0.115; adjudicated it is 0.443.
3. **Plot readings.** 30 of the 61 compared STY values are read off bar or line plots (Yang Fig. 9b, Chen 2019 ACS Catal. Fig. 5b). Only 2/30 are within ±1 %, and 14/30 within ±5 %. Yang Fig. 9b has six crossing curves on a 0-3 mmol axis; 8 of its 24 readings sit on the wrong curve or temperature.

STY by source:

| Source | Strict | Within ±5 % |
|---|---|---|
| Printed in a table or text | 25/25 | 25/25 |
| Printed but rounded (Chen 2019 Energy Technol.) | 0/4 | 2/4 |
| Derived from a per-metal value (Chen 2024) | 0/2 | 2/2 |
| Plot readings | 2/30 | 14/30 |

### First batch (4 papers, first run)

These are the results reported after the first run. They are unchanged by the second-batch fixes.

#### TheMeCat errors found against the PDFs (first batch)

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

#### Field-level accuracy against TheMeCat (3 DOIs, 71 matched entries)

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

#### Entry-level recall and precision

| DOI | Curated | Extracted | Matched | Matched with X and S | Recall | Precision (matched only) | Precision (with spot check) |
|---|---:|---:|---:|---:|---:|---:|---:|
| 10.1021/acs.iecr.7b01464 | 22 | 26 | 22 | 22 | 1.00 | 0.85 | **1.00** |
| 10.1039/c2cy20604h | 60 | 45 | 45 | 20 | 0.75 | 1.00 | **1.00** |
| 10.1039/c6ra28305e | 4 | 4 | 4 | 4 | 1.00 | 1.00 | **1.00** |
| **Total** | 86 | 75 | 71 | 46 | **0.83** | 0.95 | **1.00** |

- The 4 unmatched extracted entries are Wu 2017 Table 2 (runs without internal cooling), which TheMeCat leaves out. All 4 match the PDF (`eval/unmatched_review.csv`).
- The 15 curated entries that were not found are all Cu–Ba/Al2O3 at temperatures other than 473 K. The main text points to ESI Table S3 for them, and the ESI is not fetched.

#### Gothe 2025 Table 4 (manual transcription, 21 rows)

| Field | Correct |
|---|---|
| Rows matched (Re wt%, prereduction T, reaction T, P, CO2:H2, GHSV all exact) | 21/21 |
| X_CO2 | **21/21** |
| S_MeOH | **21/21** |
| S_CO (including the `<1` qualifier) | **21/21** |
| S_CH4 (including the `<1` qualifier) | **21/21** |
| STY (g MeOH per g Re per h) | **21/21** |

Per-row results are in `eval/gothe_table4_scores.csv`.

#### CO / CH4 selectivity spot check (`eval/co_ch4_spotcheck.csv`)

20 values were drawn at random (seed 20261005) from the 71 extracted S_CO / S_CH4 values (Gothe 42, Bansode 21, Wu 8)
and checked against the PDFs by hand. All **20/20 are correct**:

- 15 are table values that match exactly, including 6 `<1` bounds;
- 2 are printed in the text;
- 3 are Fig. 7 plot readings within 1 pp.

## Failure modes seen

1. **Data in the Supporting Information.** Bansode 2013 points to ESI Tables S1–S3 for the full grid, and TheMeCat used them. The main text plots X_CO2 only for Cu/Al2O3 (Fig. 5), S_CO for Cu–K (Fig. 7), and S_MeOH for the promoted catalysts only at 473 K (Fig. 8). The SI-only values account for all 15 missed entries, all 25 missing X_CO2 values (Cu–K/Cu–Ba) and 16 missing S_MeOH values. The model left them null instead of inventing them. The fix is to fetch the SI and pass it as extra pages.
2. **Plot readings.** In the first batch they were accurate (X 29/29 and S_MeOH 32/35 within 0.5 pp). Over 11 papers, strict accuracy for plot-read values is 47/56 for X, 37/56 for S_MeOH and 2/30 for STY.
   - The errors split into plain reading imprecision (31 values) and series or point confusion (23 values).
   - Confusion means a value taken from a neighbouring curve, a swapped bar, or the next temperature. It happens on crowded or crossing curves (Yang Fig. 9b), on legends whose entries do not match the plotted series (Chen 2019 ACS Catal. Fig. 5a, where the model invented an In0.25 curve), and on adjacent bars (Chen 2024 Fig. 4a, GM/PM).
   - All such values carry the `~` qualifier, so they can be routed to review or given a wider uncertainty.
3. **GHSV basis.** Two of the three TheMeCat papers give a volume-based GHSV (h-1) or only a flow rate. The extraction records exactly what is printed, so no mass-based GHSV could be scored. Schema v2 adds `total_flow`, and `normalize.py` now derives NL g-1 h-1 = flow / mass, so the next run covers flow-only papers such as Wu 2017 (80 mL min-1 / 5.5 g = 0.87). Volume-basis GHSV still needs a bed density from the paper.
4. **STY rarely printed.** Only 6 of the 71 curated STY values are printed in the papers; TheMeCat computes the rest from X, S and flow. The extraction does not compute anything, and the plant model can derive STY from X, S, flow and mass downstream.
5. **Retrieval.** 43 of the 52 TheMeCat DOIs are ScienceDirect. Without NUS VPN, nus-fetch marks all of them `manual`, including the open-access ones, because the OA copies also sit on ScienceDirect. Retrieval, not extraction, is the throughput limit on Elsevier-heavy sets.
6. **Text layer.** pdfplumber loses subscripts (CO2 -> CO) and interleaves columns. Using pypdfium2 text plus page images removed both problems in the 4 papers; no value had to be corrected for this reason.
7. **Inconsistent decision to digitise plots.** The model digitised dense line plots in some papers (Yang Fig. 9, Chen 2019 ACS Catal. Fig. 5a, Bansode Figs. 5-8) but declined others (Wang Sci. Adv. Fig. 1A/B, Chen 2019 Energy Technol. Fig. 4a/b), saying the values were not printed. These skipped plots cost 48 entries.
8. **Entry identity.** Three Fig. 4b points of Chen 2024 carry the right STY values and the right loading in `entry_label`, but `catalyst_name` lacks the loading prefix (2Ir1Pd1 etc.). Separately, one reference run in Bahruji 2016 is repeated in three tables and was extracted three times. Records need a de-duplication step on (catalyst, conditions, values).
9. **Zero-activity entries** (X = 0) were skipped (3 entries: two Samson Table 6 rows, the inert bulk ZrO2 in Chen 2019 ACS Catal.). The prompt excludes support blanks without products, and the model extended this to catalysts that show zero conversion at low temperature.
10. **Rounded printed values.** When the main text prints two significant figures (0.20 g g-1 h-1) and the SI holds more digits, the extraction is faithful to the text but outside the 1 % tolerance.
11. **GHSV convention.** Curated data mix total-feed and reactant-only GHSV. Both are now computed, and scoring accepts either.
12. **STY basis left unlabelled.** For `mol kg-1 h-1` without `cat` in the unit (Jiang 2020), the model set `sty_basis: other`. The 10 STY values stay unused rather than being assumed to be per catalyst.
13. **Papers that contradict themselves.** Shi 2020's printed methanol yields are 2–3x what its own X, S and GHSV give. Ghosh 2022 plots two different conversions for the same bed (Fig. 2c vs Fig. 8b). The extraction reports what is printed; these cases are classified separately, not as extraction errors.
14. **Figure pass: axis and series errors.** Readings on secondary or broken axes and dense legends are the main error source of the recall passes (18 axis misreads, 4 series confusions, 22 wrong unmatched plot readings). SI pages rendered at 1.5x were too small for the SI text pass; a dedicated SI-figure pass at 2.2x was needed.
15. **Plots without a condition axis.** Selectivity-vs-conversion plots (Zaman SI Fig. SF8) yield points with no temperature; these 16 entries are unusable.

## Manual-required DOIs (publisher bot check, not automated)

nus-fetch returned `manual` with the note "Elsevier API: no subscription from this network" for:

- `10.1016/j.apcatb.2017.06.069` (Rui 2017, Pd/In2O3, pilot)
- `10.1016/j.jes.2023.05.010` (Hou 2023, Au/In2O3, pilot)
- `10.1016/j.fuel.2023.127927`, `10.1016/j.cej.2022.135090`, `10.1016/j.fuel.2022.125878`, `10.1016/j.jscs.2019.09.002`, `10.1016/j.jcat.2012.05.020`, `10.1016/j.jcat.2020.01.014`, `10.1016/j.apcata.2019.117144` (substitutes, all ScienceDirect)

Update (third batch): the user downloaded the ScienceDirect papers by hand. Each file was re-identified by the DOI printed in the PDF, because nus-fetch `collect` had mis-claimed several by title similarity. All nine, including Chou 2019, are now extracted.

For future Elsevier papers, there are two routes:

- Rerun `fetch_papers.py` on NUS VPN. The Elsevier API key route only grants access from an NUS IP.
- Use nus-fetch menu 7 (open in your own browser) and then menu 8 (collect). Check each collected file against the DOI printed in the PDF.

All 9 non-Elsevier TheMeCat DOIs are in the pilot, plus Bahruji 2016 (open-access copy) and, since the third batch, 9 hand-downloaded ScienceDirect papers: 19 TheMeCat papers in total.

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
| Pd/In2O3, Au/In2O3 | Rui 2017, Hou 2024 (third batch) |
| In2O3 on ZrO2/CeO2, promoted In2O3/ZrO2 | Sharma 2023, Jiang 2020 (H2O co-feed), Chou 2019 (Y/La) (third batch) |
| In2O3/HZSM-5 tandem bed | Ghosh 2022 (third batch) |
| PdZn and Pd2Ga intermetallics, Ca-PdZn/CeO2 | Ota 2012, Zaman 2023 (third batch) |
| Cu/ZnO morphology | Shi 2020 (third batch) |

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
| `eval/name_aliases.json` | Catalyst-name aliases used by the matcher (with the PDF justification) |
| `eval/field_mismatch_review.csv`, `eval/make_field_mismatch_review.py` | Every strict field mismatch with the PDF reading and failure mode; the script holds the plot readings |
| `eval/evaluate_stdout.txt` | Console output of the last `evaluate.py` run |
| `out/raw_figures/`, `out/raw_si/`, `out/raw_si_figures/` | Raw outputs of the recall passes (provenance per pass) |
| `si_manifest.json` | SI retrieval status per DOI (files, route, note) |
| `eval/before_recall/` | Scores before the recall passes: as committed after batch 3, and main pass alone under the current errata |
