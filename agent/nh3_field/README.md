# ACSA: experimental ammonia catalysts from 30 primary papers (nh3-field-30, 2026-10-06)

The ammonia analogue of the methanol extraction agent (`agent/extraction/`): same architecture, passes, model routes,
token log and caps; NH₃ prompts, NH₃ schema and NH₃ units. It supplies the within-paper field statistic in
`analysis/nh3_field_2026_10_06/`.

## Pipeline

| Step | File | What it does |
|---|---|---|
| 0 | `paper_set.txt`, `paper_set.py` | 30 DOIs; second column = overlap with the Humphreys 2021 tables (`humphreys:<ref. no.>` or `none`). |
| 1 | `fetch_papers.py` | DOI list → PDFs through `D:\Tools\nus-fetch` (`fetch --headless --json`); `--from-csv` rebuilds `fetch_manifest.json` from nus-fetch's own `pdf/manifest.csv`. |
| 1b | `fetch_si.py`, `si_docx2pdf.ps1` | SI through the publisher page in the nus-fetch browser profile (read-only); Word SI exported with WPS. A browser error on one paper is recorded and retried on the next run. Bot checks are never automated. |
| 2 | `pdf_to_text.py` | Page-tagged text, pdfplumber tables and page images (`text/`, `text_si/`, git-ignored). |
| 3 | `make_schema.py` → `schema.json`, `extract_records.py` | gpt-5.5, one strict-JSON call per paper and pass (`main`, `figures`, `si`, `si_figures`), streamed Responses API with `store=false`, `reasoning_effort=medium`. Route: local API-YES gateway first, the advisor's OpenAI key once API-YES is used up (`llm_route.py`). Keys are never printed, logged or stored. Every call is logged to `out/token_usage.csv`; cap 6 M tokens counted from the log. |
| 4 | `normalize.py` | Units → model basis, pass merge (printed main text > SI > plot reading) → `out/records_normalized.csv`. |
| 5 | `evaluate.py` | Accuracy against the adjudicated Humphreys records (`eval/humphreys_*`) and the random PDF-check sample (`eval/pdf_check_sample.csv`). |

### Schema (`schema.json`)

One record per catalyst × condition. Every number is `{value, unit, qualifier, location, page}` (value as printed;
`~` for a plot reading). Fields: catalyst name, composition, **active metal**, **metal loading**, components
(active metal / promoter / support with loading), support, promoters, preparation; **T, P, H₂/N₂**, feed, **space
velocity** + basis (mass / volume), catalyst mass, total flow, time on stream; **outlet NH₃**, **rate** + basis
(per g catalyst / per g metal / per mol metal / per m² / per mL), **TOF** + basis; operation mode (steady thermal,
chemical looping, plasma, electric field, microwave, photo); source type, primary location and page, notes.
Literature-comparison rows, equilibrium curves, decomposition, electro- and photochemical NH₃ are excluded by the
prompt.

### Normalisation (`normalize.py`)

| Column | Conversion |
|---|---|
| `T_C` | K − 273.15 |
| `P_MPa` | bar/10, atm × 0.101325, kPa/1000; a gauge pressure ("MPa (gauge pressure)", barg) + 0.101325 MPa |
| `WHSV_mL_g_h` | mass-based space velocity, or total flow / catalyst mass (`WHSV_derived`); a volumetric GHSV stays in `SV_raw` |
| `outlet_nh3_vol_pct` | vol% (ppm/10⁴); "% NH₃ yield" is not an outlet concentration and is flagged |
| `rate_umol_gcat_h`, `rate_umol_gmetal_h` | mol/mmol/µmol/nmol or STP volume (22,414 mL mol⁻¹) per g or kg per h/min/s; a basis written in the unit (gcat, gRu, gFe …) overrides the label; per-metal ↔ per-catalyst with the stated wt% (`rate_cat_from_metal`, `rate_metal_from_cat`) |
| `metal_wt_pct` | metal loading when its unit is wt% (a bare "%", as in "1.25%Ru/BaCeO₃", counts as wt%; a ratio to the support does not) |
| `TOF_s` | s⁻¹ |

Rates above 1 mol g⁻¹ h⁻¹ are flagged as implausible and not used (none in this set). Every unit of the 2,358
pass-level records was parsed; no record carries a unit flag except the 45 "% NH₃ yield" values.

## Paper set and downloads

All 30 papers are non-Elsevier (ACS 12, RSC 10, Wiley 4, Springer Nature 3, Springer 1) and were fetched by
nus-fetch; every PDF carries its DOI and matches its Crossref title (`eval/pdf_identity.csv`; title-word overlap on
the first two pages 1.00, Chem. Asian J. 0.91). No Elsevier paper was needed, so there is no manual-download list.
28 of 30 have SI (Nature 583, 391 and Chem. Commun. 2002 have none on the publisher page); a peer-review file and an
accepted manuscript were moved to `si/_not_si/`.

Selection: the 60-DOI candidate list (`candidates_round1.txt`) is the non-Elsevier primary papers cited in Humphreys
Tables 1–6 plus well-known papers; 55 were retrieved (failures: the 2001 Bielawa Angew. SICI DOI, three MDPI papers,
one Nano Res.). The 30 were chosen for side-by-side comparisons with rates and metal loadings, diverse groups
(Hosono/Kitano, Kageyama/Kobayashi, Nagaoka, Jiang/Lin (Fuzhou), Chen (DICP), Chorkendorff, Schlögl, Tao) and
metals: 20 Ru papers (two also test Fe and Co on the same support), 7 Co, 2 Fe, 1 Ni (which also tests Fe, Co and Ru).

| Paper | DOI | Humphreys | Records | Primary entries | Groups | Different winner |
|---|---|---|---:|---:|---:|---:|
| Kitano et al., Nat. Chem. 4, 934 (2012) | 10.1038/nchem.1476 | – | 31 | 19 | 3 | 1 |
| Inoue et al., ACS Catal. 4, 674 (2014) | 10.1021/cs401044a | ref. 96 | 22 | 12 | 1 | 0 |
| Kitano et al., Chem. Sci. 7, 4036 (2016) | 10.1039/c6sc00767h | ref. 115 | 35 | 15 | 3 | 1 |
| Inoue et al., ACS Catal. 6, 7577 (2016) | 10.1021/acscatal.6b01940 | ref. 116 | 38 | 16 | 4 | 2 |
| Wu et al., Adv. Mater. 29, 1700924 (2017) | 10.1002/adma.201700924 | ref. 119 | 27 | 13 | 1 | 0 |
| Kitano et al., Angew. Chem. Int. Ed. 57, 2648 (2018) | 10.1002/anie.201712398 | ref. 106 | 93 | 58 | 12 | 12 |
| Hattori et al., ACS Catal. 8, 10977 (2018) | 10.1021/acscatal.8b02839 | ref. 105 | 41 | 22 | 4 | 0 |
| Kobayashi et al., J. Am. Chem. Soc. 139, 18240 (2017) | 10.1021/jacs.7b08891 | ref. 104 | 23 | 2 | 1 | 0 |
| Tang et al., Adv. Energy Mater. 8, 1801772 (2018) | 10.1002/aenm.201801772 | ref. 81 | 38 | 35 | 6 | 6 |
| Kitano et al., J. Am. Chem. Soc. 141, 20344 (2019) | 10.1021/jacs.9b10726 | ref. 82 | 56 | 21 | 6 | 6 |
| Sato et al., Chem. Sci. 8, 674 (2017) | 10.1039/c6sc02382g | ref. 171 | 18 | 16 | 5 | 2 |
| Ogura et al., Chem. Sci. 9, 2230 (2018) | 10.1039/c7sc05343f | ref. 77 | 48 | 38 | 7 | 3 |
| Lin et al., Ind. Eng. Chem. Res. 57, 9127 (2018) | 10.1021/acs.iecr.8b02126 | ref. 100 | 10 | 10 | 5 | 0 |
| Wang et al., Inorg. Chem. Front. 6, 396 (2019) | 10.1039/c8qi01244j | ref. 101 | 28 | 20 | 5 | 1 |
| Lin et al., ACS Catal. 9, 1635 (2019) | 10.1021/acscatal.8b03554 | ref. 175 | 24 | 24 | 6 | 0 |
| Lin et al., Ind. Eng. Chem. Res. 58, 10285 (2019) | 10.1021/acs.iecr.9b01610 | ref. 174 | 6 | 4 | 1 | 0 |
| Ma et al., Catal. Sci. Technol. 7, 191 (2017) | 10.1039/c6cy02089e | ref. 178 | 55 | 53 | 7 | 3 |
| Liu et al., Catal. Lett. 149, 1007 (2019) | 10.1007/s10562-019-02674-1 | ref. 186 | 26 | 23 | 4 | 0 |
| Ma et al., RSC Adv. 9, 22045 (2019) | 10.1039/c9ra03097b | ref. 191 | 29 | 8 | 2 | 0 |
| Li et al., Chem. Asian J. 14, 2815 (2019) | 10.1002/asia.201900618 | ref. 184 | 49 | 48 | 4 | 0 |
| Inoue et al., ACS Catal. 9, 1670 (2019) | 10.1021/acscatal.8b03650 | ref. 197 | 57 | 24 | 6 | 2 |
| Gao et al., ACS Catal. 7, 3654 (2017) | 10.1021/acscatal.7b00284 | ref. 199 | 62 | 4 | 1 | 0 |
| Wang et al., Nat. Commun. 11, 653 (2020) | 10.1038/s41467-020-14287-z | ref. 200 | 34 | 13 | 4 | 0 |
| Wang et al., Chem. Commun. 55, 474 (2019) | 10.1039/c8cc07130f | ref. 201 | 20 | 5 | 0 | 0 |
| Lin et al., RSC Adv. 4, 38093 (2014) | 10.1039/c4ra06175f | ref. 129 | 12 | 0 | 0 | 0 |
| Hagen et al., Chem. Commun. 1206 (2002) | 10.1039/b202781j | ref. 122 | 62 | 5 | 1 | 0 |
| Sato et al., ACS Catal. 11, 13050 (2021) | 10.1021/acscatal.1c02887 | – | 41 | 26 | 8 | 4 |
| Ye et al., Nature 583, 391 (2020) | 10.1038/s41586-020-2464-9 | ref. 134 | 43 | 23 | 3 | 0 |
| Humphreys et al., J. Mater. Chem. A 8, 16676 (2020) | 10.1039/d0ta05238h | ref. 84 | 108 | 64 | 8 | 2 |
| Fan et al., ACS Sustain. Chem. Eng. 5, 10900 (2017) | 10.1021/acssuschemeng.7b02812 | ref. 159 | 40 | 28 | 6 | 0 |

Records = merged entries after the four passes (1,176 from 2,358 pass-level records). Primary entries = entries in
the plant chain's primary set after one entry per catalyst and comparison group; groups and winners are defined in
`analysis/nh3_field_2026_10_06/README.md`.

## Token usage and cost

All 110 calls ran on the advisor's OpenAI key: API-YES answered every call with HTTP 429 `usage_limit_reached`
(team plan, reset 23:17 on 2026-10-06), and `llm_route.Router` switched automatically.

| Pass | Calls | Prompt | Output (reasoning) | Total | Records | Cost at USD 5 / 30 per M |
|---|---:|---:|---:|---:|---:|---:|
| main (full text + all page images) | 30 | 811,866 | 526,011 | 1,337,877 | 648 | USD 19.84 |
| figures (main-text plots, 2.2× images) | 30 | 832,201 | 659,058 | 1,491,259 | 967 | USD 23.93 |
| si (SI text + images) | 28 | 500,145 | 348,675 | 848,820 | 475 | USD 12.96 |
| si_figures (SI plots) | 22 | 318,300 | 194,684 | 512,984 | 268 | USD 7.43 |
| **Total** | **110** | **2,462,512** | **1,728,428 (310,392)** | **4,190,940** | **2,358** | **USD 64.17** |

70 % of the 6 M cap; 0.14 M tokens and USD 2.14 per paper; 3.6 h of model time (three parallel streams for the
main pass, one or two for the others, because the machine's 15 GB of RAM is shared with other sessions: two figure
streams and one SI download hit `MemoryError` / `ERR_INSUFFICIENT_RESOURCES` and were rerun; failed attempts never
reached the API and are not in the log). Ten calls returned no records, all legitimately (for example "SI contains
only characterisation", "main-text figures are characterisation only").

## Accuracy

### (a) Against the adjudicated Humphreys records

38 Humphreys rows cite 28 of the 30 papers. Matching: same DOI, |ΔT| ≤ 1.5 K, |ΔP| ≤ max(1 %, 0.102 MPa), then the
best name match. For the review's generic names the PDF identified the entry meant (`eval/humphreys_adjudication.csv`:
"1% Fe/BaTiO₃₋ₓHₓ" is Fe/BaTiO₂.₃₅H₀.₆₅, "Co/C" is Ba₀.₈Co₁.₀/C). Every disagreement was checked in the PDF.

| Field | Values | Equal (≤ 1 %) | Within 10 % | Disagreements checked | Extraction wrong | Review wrong | Extraction correct after adjudication |
|---|---:|---:|---:|---:|---:|---:|---:|
| Metal content (wt%) | 29 | 27 | 28 | 2 (+2 rows the agent left empty) | 0 | 4 | **29/29** |
| T | 38 | 38 | 38 | 0 | 0 | 0 | **38/38** |
| P | 38 | 36 | 38 | 0 (gauge → absolute, +0.1 MPa) | 0 | 0 | **38/38** |
| WHSV | 30 | 27 | 27 | 3 (+2 the agent left empty) | 0 | 5 | **30/30** |
| Outlet NH₃ | 1 | 1 | 1 | 0 | 0 | 0 | 1/1 |
| Rate per g catalyst | 38 | 33 | 36 | 5 | 1 | 1 | **37/38** |

The one extraction error: Lin 2014 Fig. 9a — the agent read the axis unit "mol g⁻¹ h⁻¹" as mmol and the 430 °C
point as 0.059 instead of about 0.052. Two other rate disagreements are plot readings within 3 % of each other, and
one is a basis difference (Fan 2017 per g Fe converted with the measured 21.8 wt% Fe; the review used the nominal 25).

**Errors in Humphreys et al. 2021** (all verified in the PDFs; `eval/humphreys_adjudication.csv`):

| Review row | Review | Paper |
|---|---|---|
| ref. 104, "Ru/TiH₂ 0.9 wt%", 2.8 mmol g⁻¹ h⁻¹ | Ru catalyst | Ru-free TiH₂ (the 0.9 wt% Ru catalyst is Ru/BaTiO₃, 4.1 mmol g⁻¹ h⁻¹) |
| ref. 104, "Ru/BaTiO₂.₅H₀.₅ 0.9 wt%", 1.4 | Ru catalyst | Ru-free BaTiO₂.₅H₀.₅ |
| ref. 199, 5.2 wt% Co/CNT (BaH₂-promoted) | WHSV 6,000 mL g⁻¹ h⁻¹ | 60,000 (Table 1 note, Fig. 5 caption) |
| ref. 186, Ru/CeO₂–CS | WHSV 70,000 | 24,000 |
| ref. 100, Ru/CeO₂-r, 10 MPa | WHSV 70,000 | 70 dm³ h⁻¹ over 0.30 g = 233,000 |
| ref. 159, FeOOH(-K)/Al₂O₃ | WHSV 26,400 | 12,000 (26,400 is the reduction flow, 440 NmL min⁻¹) |
| ref. 81, Ru/BaTiO₂.₅H₀.₅ | 1.0 wt%, WHSV 36,000 | 0.86 wt% (nominal 1), WHSV 66,000 (0.1 g, 110 mL min⁻¹; the review's Fe and Co rows of the same paper use 66,000) |
| ref. 81, Co/BaTiO₃₋ₓHₓ | 5,700 µmol g⁻¹ h⁻¹ | 5,500 (text p2) |
| ref. 200, Co–N–C | 3.4 wt% Co | 3.73 wt% (ICP, text p2) |

Effect on the Humphreys chain (`analysis/nh3_supported_2026_10_06`, not changed here; recomputed with this
branch's mapping function, which reproduces that chain exactly):
- The BaHₓ-promoted Co/CNT, "the only catalyst below Fe" there (14.46 USD/t), costs **18.28 USD/t** with the
  paper's WHSV of 60,000 (outlet NH₃ 0.18 % instead of 1.79 %); with it, no primary catalyst of that chain falls below
  the 15.29 USD/t Fe benchmark.
- The two ref. 104 rows (25.73 and 27.50 USD/t) are not Ru catalysts and leave the Ru set.
- Ru/CeO₂–CS: 23.43 → 22.66 USD/t; Ru/BaTiO₂.₅H₀.₅: 23.65 → 22.98; Co–N–C: 22.60 → 22.54; Ru/CeO₂-r (10 MPa):
  23.26 → 28.16 USD/t.

### (b) Random PDF check of the other entries

40 entries drawn at random (seed 20261006) from the 1,176 merged entries with a rate, excluding the 38 matched to
Humphreys, were checked by hand against the page (`eval/pdf_check_sample.csv`, page and evidence per entry). An entry
is correct when every value it carries equals the page (printed values) or lies within plot-reading precision on the
right series (about 2 % of the axis range).

**35/40 correct (0.875, 95 % CI 0.73–0.96, Clopper–Pearson).** 30 of the 40 are plot readings (26 correct) and 10
printed values (9 correct).
The five wrong entries:

| Entry | Error |
|---|---|
| Ogura 2018, Ru/La₀.₅Ce₀.₅O₁.₇₅_650red, 0.1 MPa | space velocity "2880 NL h⁻¹ g⁻¹" is not printed (0.1 g, 120 NmL min⁻¹ = 72 NL h⁻¹ g⁻¹) |
| Ye 2020, Fe/LaN (ED Fig. 6i) | rate 1,777 correct, but T and P are not given for that panel; the agent inferred 400 °C, 0.1 MPa |
| Gao 2017, 3BaH₂-10%Co/CNTs (SI Fig. S6) | rate correct; "10 %" is the Co:CNT mass ratio, the catalyst holds 5.20 wt% Co |
| Kitano 2018, Ru/Ba-Ca(NH₂)₂ (Fig. 1A) | point placed at 330 °C; the plotted points are at 320 and 340 °C |
| Hagen 2002, Ba–Co/C 440 °C (Fig. 1) | two neighbouring points merged into one (19 at 1.35 % NH₃) |

Errors seen outside the sample while checking groups: Sato 2021 Fig. 1a gives Co@BaO/MgO-700red 5 wt% Co (the 5 wt%
is the Ru loading of the reference catalysts; Co is 20 wt%); Lin 2014 (above). They are left as extracted, like
every other value; the field statistic is reported with and without plot readings.

## Judgement calls

- The Humphreys-cited Elsevier papers (for example the Kowalczyk / Raróg-Pilecka J. Catal. and Kojima & Aika Appl.
  Catal. A papers) were not used, so no manual download was needed; the non-Elsevier set reaches 30 papers.
- Every PDF was matched to its DOI by the DOI printed in it and by its Crossref title.
- A bare "%" loading counts as wt% (the papers' convention); this turned one Co:CNT ratio into a metal content
  (sample entry above).
- A gauge pressure is converted to absolute; the review prints gauge values unchanged, which makes two P values
  differ by 0.1 MPa.
- `extract_records.py` skips a paper whose page rendering fails with `MemoryError` (rerun retries it) instead of
  stopping the batch.
