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
| Extracted with gpt-5.5, first batch | 4: Gothe 2025, Wu 2017, Bansode 2013, Wang 2017 (RSC Adv.); OpenAI API, chat completions |
| Extracted with gpt-5.5, second batch | 7: Samson 2014, Chen 2019 (ACS Catal.), Wang 2017 (Sci. Adv.), Chen 2024 (Angew.), Yang 2024 (ChemPhysChem), Chen 2019 (Energy Technol.), Bahruji 2016; `--api-yes` route (local API-YES gateway, streamed Responses API), same prompt and schema |
| Adjudicated against the PDFs | all 11 |

The first batch stopped when the OpenAI organisation ran out of credit (HTTP 429 `insufficient_quota`).
The second batch was extracted later through the local gateway. All 11 papers were then scored with the same `normalize.py` and `evaluate.py`.
Every mismatch was checked in the PDF: TheMeCat errors go to `eval/themecat_errata.csv`, extraction errors to `eval/field_mismatch_review.csv` and `eval/unmatched_review.csv`.
The 11-paper results are in "Accuracy, 11 papers"; the 4-paper results from the first run are kept below them as "First batch".

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
| `STY_g_gcat_h`, `STY_g_gmetal_h` | Any of g, mg, kg, mol, mmol or umol MeOH per g or kg, per h, hour, min or s (M = 32.042 g/mol), split by basis. A basis written in the unit (`kgcat`, `gcat`, `gRe`, `gmetal`) overrides an extracted `sty_basis` of `other`/`unspecified` (the extracted label is kept in `sty_basis_extracted`). A per-metal STY is also expressed per g catalyst (x metal wt% / 100) when the record states the loading; `STY_gcat_from_metal` marks these. Per-area rates (umol m-2 h-1) stay in `STY_raw` and are flagged. |
| `metal_wt_pct` | Sum of the wt% loadings of the active metals |

Any value whose unit was not understood is reported in `flags`, never silently dropped.

Fixes made while adjudicating the second batch (genuine parsing bugs, found from unparsed units):

- `hour` / `hours` were not recognised. This dropped the GHSV of Chen 2024 and Wang 2017 Sci. Adv. (`mL gcat-1 hour-1`) and the 187.1 g gmetal-1 hour-1 STY.
- Bahruji 2016 rates in `mmol kgcat-1 h-1` were labelled `sty_basis: other` by the model, so 21 STY values were not used. The basis is now read from the unit.
- Per-metal STY (Chen 2024) had no per-catalyst value; it now gets one when the loading is stated.
- Two unanchored copies of the NmL/NL rule were removed.

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

Pilot total: 650,673 tokens (455,349 prompt, 195,324 output), 22 % of the 3 M cap.
At the list price above, that is about **USD 8.14**. Second-batch successful calls averaged 35 k prompt and 14 k output tokens per paper.

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

### Accuracy, 11 papers (10 TheMeCat DOIs + Gothe)

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
| `eval/name_aliases.json` | Catalyst-name aliases used by the matcher (with the PDF justification) |
| `eval/field_mismatch_review.csv`, `eval/make_field_mismatch_review.py` | Every strict field mismatch with the PDF reading and failure mode; the script holds the plot readings |
| `eval/evaluate_stdout.txt` | Console output of the last `evaluate.py` run |
