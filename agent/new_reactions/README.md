# AI-run pipeline on two new reactions: propane dehydrogenation and CO2 methanation (2026-11-10)

The paper's chain (literature -> extracted records -> plant model -> paper ranking vs plant-cost ranking -> where the
cost sits -> what a catalyst would need) run end to end by the agent on two reactions the paper does not cover.
Same logic as the NH3 and methanol chains; the steps that changed are the OCR (Docling instead of page images) and
the two plant models. Everything below was produced in one session, 20:01-21:05 (UTC+8), without hand edits to the
extracted data.

## Pipeline

| Stage | Tool | Output |
|---|---|---|
| 1 search + screening | `search_openalex.py`, `pick.py` (OpenAlex, open-access filter, title search) | `candidates_*.csv`, `selected_*.json` |
| 2 download | `fetch_oa.py` (every OpenAlex OA location, PDF checked against DOI/title), then `nus-fetch` headless | `pdf/` (git-ignored), `fetch_*.json` |
| 3 OCR / layout | [Docling](https://github.com/docling-project/docling) 2.x on GPU (TableFormer ACCURATE, OCR on, figure crops at 4x) in `D:\Tools\docling-env` | `ocr/` (git-ignored) |
| 4 extraction | `extract_new.py`: gpt-5.5, strict JSON schema per reaction, Docling Markdown + up to 12 performance-figure crops per paper, same copy-as-printed rules as `agent/extraction` | `raw/<rxn>/*.json`, `token_usage.csv` |
| 5 normalisation | `normalize.py`: units, composition by element, productivity from printed rate or feed flow x X x S (flagged), deactivation constant from initial/final conversion; physical gate: printed rate > 50 kg kg-1 h-1 is a unit error | `data/<rxn>_records.csv` |
| 6 self-check | `verify.py`: every value marked as printed must appear as a number in the Docling text or the PDF text layer | `results/verify_*.csv` |
| 7 plant models | `plant_models.py`, `params_process.json` + `build_params.py` (metal prices = frozen NH3 set + USGS MCS 2026, as in `analysis/meoh_catalyst_cost_2026_10_06`) | `params.json` |
| 8 analysis | `analyze.py`, `sensitivity.py`, `make_figure.py` | `results/` |
| ledger | `ledger_report.py`, `stages.json` | `results/ledger_*.json/csv` |

Plant models. PDH: Oleflex-type plant, 600 kt/y, 1.5 bar, H2/C3H8 = 0.5, per-pass conversion optimised up to
0.9 x equilibrium; propane, energy (reaction heat + throughput-proportional reheating/compression/separation), capital
scaled with reactor throughput and with the off-stream fraction of cyclic regeneration, catalyst (base + metals, Pt
recovered), H2 and light-ends fuel credits. CO2 methanation: staged plant to grid quality (99 % overall), 10 bar;
H2, CO2, power, capital (recycle and reactor volume scale), catalyst. Activity moves from the lab to the plant by a
first-order approach to equilibrium (`activity_scale`), so a kinetic-regime test (low conversion) is not charged a
recycle it would not have in a plant; selectivity keeps its lab value. Reference plants: 846 USD/t propylene
(propane 640); 2,021 USD/t CH4 = 131 USD/MWh HHV at 3 USD/kg H2 (Becker, Penev & Braun 2019 report 132 USD/MWh at
3 USD/kg).

## Numbers

| | PDH | CO2 methanation |
|---|---:|---:|
| papers selected / downloaded / with usable records | 11 / 9 / 6 | 24 / 10 / 8 |
| records extracted / usable for the plant model | 109 / 59 | 329 / 255 |
| printed values found in the paper (self-check) | 326 / 326 | 525 / 570 (38 of the 45 are x-axis temperatures of plots) |
| plot readings (not checkable this way) | 97 | 664 |
| reference plant cost, largest share | 846 USD/t, propane 76 % | 2,021 USD/t, H2 75 % |
| within-paper groups; productivity leader is not the cheapest plant option | 3 of 5 (2 other catalyst, 1 other T); worst regret 91 % | 4 of 10; regret <= 0.3 % |
| selectivity leader is not the cheapest | 2 of 5 | 7 of 10; worst regret 51 % |
| share of the cost gap to the reference (one-at-a-time swaps) | selectivity 50 %, activity 37 %, temperature 9 %, stability 2 %, metal 1.5 % | activity 98 %, temperature 2 % |
| cost change at the reference | +1 pt selectivity -3.5; activity x2 -2.1; cycle x10 -0.3; propane -10 USD/t -11.6 | best literature catalyst -74.6 (-3.7 %); activity x2 -29; H2 -0.25 USD/kg -127 |

Sensitivity (`results/sensitivity_*.csv`; propane 400-650 USD/t, gas 3-12 USD/GJ, capex x0.5-1.5, approach 0.8,
3 bar, catalyst life 1 y, 2 h regeneration; H2 1.5-6 USD/kg, CO2 100 USD/t, capex x0.5-2, 1-30 bar): the largest cost
share stays propane (67-88 %) and H2 (60-86 %); the productivity leader differs from the cheapest option in 3-5 of 5
PDH groups and 4-5 of 10 methanation groups; +1 point selectivity is worth 1.2-6.3 USD/t propylene against 0.3-0.7
for a 10 % activity gain.

Read with the numbers: lab selectivities are initial gas-phase values; the industrial 0.90 includes coke and
separation losses, so "below the reference" (15 of 59 PDH records) compares different bases. 18 of 59 PDH records were
measured at less than half the plant per-pass conversion.

## Time and cost

| | |
|---|---:|
| wall clock, search to figures (includes two superseded runs and writing the code) | 64 min |
| Docling, 19 PDFs / 251 pages on the RTX 5060 | 390 s (1.6 s per page) |
| extraction, final pass, 19 papers, 6 in parallel | 9.5 min wall; 116 s and 36 k tokens per paper |
| LLM cost, final pass | USD 9.83 (USD 0.52 per paper) |
| LLM cost, everything logged incl. the superseded first pass | USD 15.17 (1.06 M tokens) |
| methanol extraction (page images, 4 passes incl. SI), for comparison | ~150 k tokens, USD 2.2 per paper |
| manual baseline (single extraction + verification, Gartlehner et al.) | 107 min per paper |

Prices: gpt-5.5 at USD 5 / 30 per M input / output tokens. Two killed first-pass calls are not in the log.

## Not covered

Main text only (no SI pass). Elsevier, RSC and MDPI PDFs that need a browser check were skipped rather than handed
to the user; Docling crops are main-text figures only. Plant parameters are open-literature values (see
`SOURCES.md`); none were checked with plant operators.
