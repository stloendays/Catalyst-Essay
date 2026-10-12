# Pre-registration: ammonia within-paper field sample, batch 2 (2026-10-12)

Committed before any batch-2 extraction, screening against plant cost, or scoring. The batch is reported whatever its
result.

## 1. Candidate list (fixed)

The 25 DOIs of `agent/nh3_field/fetch_manifest.json` with status `ok` that are not in
`agent/nh3_field/paper_set.txt`: downloaded in round 1 from the 60-DOI candidate list (`candidates_round1.txt`) and not
chosen. No other paper enters batch 2.

| DOI | First author, year | Title (from the PDF file name) |
|---|---|---|
| 10.1002/anie.201703695 | Wang 2017 | The Formation of Surface Lithium-Iron Ternary Hydride and its Function on Catalytic ... |
| 10.1002/anie.201907171 | Zheng 2019 | Efficient Nondissociative Activation of Dinitrogen to Ammonia over Lithium-Promoted ... |
| 10.1002/cctc.201500309 | Tarka 2015 | Effect of a Barium Promoter on the Stability and Activity of Carbon-Supported Cobalt ... |
| 10.1002/cctc.201700353 | Li 2017 | Chlorine-Tolerant Ruthenium Catalyst Derived Using the Unique Anion-Exchange Properties ... |
| 10.1002/cctc.201800556 | Nishi 2018 | A Mesoporous Carbon-Supported and Cs-promoted Ru Catalyst with Enhanced Activity ... |
| 10.1002/slct.201803813 | Javaid 2019 | Influence of Reaction Conditions and Promoting Role of Ammonia Produced at Higher ... |
| 10.1007/s10562-011-0564-8 | Raróg-Pilecka 2011 | Cobalt Catalyst Doped with Cerium and Barium Obtained by Co-Precipitation Method |
| 10.1007/s10562-017-2045-1 | Zhao 2017 | Controllable Synthesis of Ru Nanocrystallites on Graphene Substrate as a Catalyst ... |
| 10.1007/s11144-018-1498-6 | Jafari 2019 | Effect of iron oxide precursor on the properties and ammonia synthesis activity ... |
| 10.1021/acs.chemmater.8b01819 | Hasegawa 2018 | Topotactic Synthesis of Mesoporous 12CaO·7Al2O3 Mesocrystalline Microcubes toward ... |
| 10.1021/acs.chemmater.9b03099 | Qiu 2019 | Pure Siliceous Zeolite-Supported Ru Single-Atom Active Sites for Ammonia Synthesis |
| 10.1021/acs.jpcc.7b07268 | Abe 2017 | Anchoring Bond between Ru and N Atoms of Ru/Ca2NH Catalyst Crucial for the High ... |
| 10.1021/acscatal.8b03743 | Lu 2018 | Synthesis of Rare-Earth-Based Metallic Electride Nanoparticles and Their Catalytic ... |
| 10.1021/acssuschemeng.8b04683 | Ogura 2018 | Ru/La0.5Pr0.5O1.75 Catalyst for Low-Temperature Ammonia Synthesis |
| 10.1021/acssuschemeng.9b04929 | Zhang 2019 | Barium-Promoted Ruthenium Catalysts on Yttria-Stabilized Zirconia Supports for ... |
| 10.1021/jacs.0c06624 | Ye 2020 | Contribution of Nitrogen Vacancies to Ammonia Synthesis over Metal Nitride Catalysts |
| 10.1021/jacs.1c06657 | Ye 2021 | Dissociative and Associative Concerted Mechanism for Ammonia Synthesis over Co-Based ... |
| 10.1021/jacs.6b00124 | Lu 2016 | Water Durable Electride Y5Si3: Electronic Structure and Catalytic Activity for ... |
| 10.1038/nchem.2595 | Wang 2017 | Breaking scaling relations to achieve low-temperature ammonia synthesis through ... |
| 10.1038/ncomms7731 | Kitano 2015 | Electride support boosts nitrogen dissociation over ruthenium catalyst and shifts ... |
| 10.1038/s41467-020-15868-8 | Hattori 2020 | Solid solution for catalytic ammonia synthesis from nitrogen and hydrogen gases ... |
| 10.1038/s41929-021-00695-x | (2021) | Ammonia synthesis by ternary ruthenium complex hydrides |
| 10.1039/c9cc07385j | Wu 2020 | Enhanced ammonia synthesis performance of ceria-supported Ru catalysts via ... |
| 10.1039/c9cy01303b | Luz 2020 | MOF-derived nanostructured catalysts for low-temperature ammonia synthesis |
| 10.1039/c9cy02326g | Morlanés 2020 | Development of catalysts for ammonia synthesis based on metal phthalocyanine materials |

## 2. Inclusion rule (the round-1 rule, applied before any plant cost is seen)

Include a paper when it is a primary research paper on thermal catalytic NH₃ synthesis from N₂ and H₂ that reports,
side by side, at least two catalysts or two temperatures under one stated pressure and H₂/N₂ ratio, with a rate (or an
outlet NH₃ concentration with a space velocity) and the metal loading of the catalysts.

Exclude reviews; electrochemical, photochemical, plasma or chemical-looping-only papers; and NH₃ decomposition.

The decision is taken from the paper text (main text and, where available, SI) by reading the experimental section,
tables and figure captions, before extraction and without any plant-model output. One row per paper with
include/exclude and a one-line reason goes to `batch2_screening.csv`. Papers that pass the screen but yield no scored
group after the frozen chain stay counted as included; the report lists screened / included / with at least one scored
group.

## 3. Pipeline and analysis (frozen, unchanged)

- Extraction: the four passes of `agent/nh3_field/extract_records.py` (main, figures, si, si_figures) with the same
  prompts, schema, model (gpt-5.5, reasoning medium, streamed Responses, `store=false`) and route
  (`llm_route.py`: API-YES first, then the advisor key). Only the output directory (`agent/nh3_field/out_batch2/`) and
  the paper list (batch-2 included DOIs) change, through a wrapper. Token cap 5 M, counted from
  `out_batch2/token_usage.csv`. Normalisation: `normalize.py` unchanged → `out_batch2/records_normalized.csv`.
- Scoring: `analysis/nh3_field_2026_10_06/run_field_chain.py` then `run_printed_primary.py`, imported unchanged by a
  thin wrapper that only redirects input records and output folder. No threshold, definition or grouping changes.
  The chain's data-dependent default (median laboratory NH₃ fraction of the set, used only for entries without an
  outlet or space velocity) is computed by the frozen code over the input set, as in round 1.
- Primary definition: the frozen printed-value primary (`run_printed_primary.py`): rate per g catalyst printed (qualifier
  `=`, not a plot reading), temperature printed, printed outlet when the entry uses it; groups of the all-entries run
  scored when at least two printed entries remain; leaderboard on the paper's own rate basis; plant cost without metal
  recovery. Variants exactly as in the frozen `summary_printed.json`: per g catalyst, per g metal, 90 % Ru recovery,
  bed density 500 and 2,500 kg m⁻³, commercial fused-Fe references removed, measured at ≥ 5 MPa, without the paper
  with the most groups, and all entries (plot readings included).
- Reported sets: (a) round 1 (frozen, reproduced through the wrapper as a regression check: 7/33 must reproduce
  exactly, else the run stops); (b) batch 2 alone; (c) pooled = round 1 + batch 2. The pooled set is the union of the
  scored entries of each batch's own chain run (round-1 costs exactly the frozen ones), aggregated with the frozen
  `aggregate` and printed-primary code. A single chain run over the concatenated records is reported as a sensitivity.
- Confidence interval: the frozen method — paper-cluster bootstrap, 10,000 resamples of the papers with
  replacement, seed 20261006, 2.5th–97.5th percentiles of the share of groups whose laboratory leader is not the
  plant-cost leader (`run_field_chain.aggregate`, `boot=True`); the paper-weighted share with its bootstrap CI as well.
- Accuracy: random sample (seed 20261012) of 40 printed values that enter the batch-2 primary (rate, T, P,
  WHSV/outlet NH₃, metal wt%), each checked against the cited PDF page (AI-assisted check, `batch2_pdf_check.csv`).
  A wrong value is corrected only through `batch2_corrections.csv`, applied by the scoring wrapper, and counted in the
  report; the uncorrected result is reported next to it.

## 4. Prior

The frozen round-1 printed-value result: 7 of 33 within-paper groups (21 %) have a laboratory leader that is not the
plant-cost leader (6 of 23 papers; bootstrap CI 7–37 %). Batch 2 is reported in full whatever its result, alone and
pooled.
