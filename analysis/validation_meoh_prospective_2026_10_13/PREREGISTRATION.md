# Pre-registration: prospective out-of-sample test of the methanol field result (2026-10-13)

Committed before any new paper is downloaded, screened in full text or extracted. The commit that adds this file
contains the predictions, the fixed search and its ranked result, and the code that computed the predictions from the
frozen set; it contains no extraction and no plant-model output for a new paper. The test is reported whatever its
result. Anything not fixed here is labelled **post hoc** where it is reported.

## 1. What is tested

The frozen field result (tag `freeze/field-2026-10-12`, printed values only): within one paper's comparison group (same
pressure, H2/CO2 and space velocity), the laboratory leader by methanol space-time yield (STY) is often not the
plant-cost leader of `data/meoh/meoh_general_model.py`.

| Loop treatment | Cost column (frozen code) | Frozen result |
|---|---|---|
| **S6 (primary, supervisor decision of 2026-10-12)**: reactor-inlet (CH4 + CO + N2) fraction <= 6.86 % (`G.NONREACTIVE_MAX`) | `cost_recycled_opt_inlet` | **28 / 40 groups (70.0 %), 22 with a regret > 5 %, 21 / 28 papers** |
| S5 (alongside): no inlet limit | `cost_recycled_opt` | 15 / 40 groups (37.5 %), 7 with a regret > 5 %, 9 / 28 papers |

The question is whether a new, later set of CO2-to-methanol papers, treated by exactly the same pipeline, shows (i) the
same disagreement rate and (ii) disagreements of the predicted kind, so that a laboratory-only rule fixed on the frozen
set picks the plant-cost leader of the new groups better than chance.

## 2. Predictions (computed by `predict_from_frozen.py` → `prediction_frozen.json`)

All intervals: paper-cluster bootstrap of the frozen 40 groups / 28 papers (10,000 resamples of papers with
replacement, seed 20261006, 2.5th–97.5th percentiles; the frozen `meoh_candidates.bootstrap`). The script asserts the
frozen anchors (S5 15/40 with 15.2–57.1 %; S6 28/40 with 54.1–82.8 %; rule accuracies 25/40 and 23/40).

### (a) Disagreement rate

| | Predicted share of new groups whose STY leader is not the plant-cost leader | 95 % interval |
|---|---|---|
| **S6** | **70.0 %** | **54.1–82.8 %** |
| S5 | 37.5 % | 15.2–57.1 % |

### (b) Mechanism: which laboratory pattern makes a laboratory leader lose at plant scale

From the pre-registered laboratory-only rules of `analysis/meoh_constraint_boundary_2026_10_12/` (`PROTOCOL_B.md`,
committed before those rules were scored): leave-one-paper-out selection over nine rules picked **methanol selectivity
(rule R2 "S", ties broken by the higher STY)** in all 28 folds under S6 and **STY (R1)** in all 28 folds under S5. The
physical reading (README there, A4): under the inlet limit, CO made per pass must leave through the purge, so the more
selective, lower-CO entry wins; without the limit the higher-conversion entry wins more often.

| Prediction | Frozen value [95 % CI] |
|---|---|
| **M1 (S6)**: a group whose STY leader is *not* its most selective entry disagrees more often than a group whose STY leader is also the most selective entry | 26 / 30 = 86.7 % [73.5–96.3] vs 2 / 10 = 20.0 % [0–50] |
| **M2 (S6)**: in most disagreements the plant-cost leader is more selective than the STY leader | 19 / 28 = 67.9 % [43.6–95.5] |
| M2' (S6): …and makes less CO | 18 / 28 = 64.3 % [40.9–92.0] |
| **M3 (S5)**: in most disagreements the plant-cost leader has the higher single-pass CO2 conversion | 9 / 15 = 60.0 % [12.5–81.8] |
| S5: plant-cost leader more selective | 4 / 15 = 26.7 % [9.1–63.6] |

**Per-group rule** (the prediction committed blind for every new group, section 6):

- S6: the plant-cost leader is the entry with the highest methanol selectivity (R2; ties to the higher STY).
- S5: the plant-cost leader is the STY leader (R1).

Frozen accuracy of these rules, with the chance rate (a uniformly random entry of the group, mean of 1/n):

| | Rule accuracy | Chance | Rule minus chance [95 % CI] | STY accuracy | Rule minus STY [95 % CI] |
|---|---|---|---|---|---|
| S6 (R2) | 23 / 40 = 57.5 % | 23.1 % | +34.4 pp [+13.3, +57.0] | 12 / 40 = 30.0 % | +27.5 pp [+5.7, +52.8] |
| S5 (R1) | 25 / 40 = 62.5 % | 23.1 % | +39.4 pp [+21.9, +60.8] | 25 / 40 | 0 (same rule) |

### (c) Pass rules

The new batch is scored on its own (not pooled with the frozen set).

- **P1 (rate).** The new-batch share of scored groups with a different leader lies inside the predicted interval:
  S6 54.1–82.8 %; S5 15.2–57.1 %.
- **P2 (per-group rule).** The rule's per-group accuracy on the new groups exceeds the chance rate: the paper-cluster
  bootstrap 95 % interval of (rule correct − 1/n), averaged over the new groups (10,000 resamples of the new papers,
  seed 20261013), lies entirely above zero.
- **S6 passes** when P1 and P2 both pass under S6. S5 is evaluated by the same two rules and reported alongside.
  Each rule is reported as pass or fail separately; there is no minimum batch size that suspends the verdict, but the
  number of scored groups and papers is stated next to it.

Reported with the verdict, not part of it (secondary):
- rule minus STY accuracy with its bootstrap interval (the rule against the paper's own leaderboard);
- M1–M3 on the new groups with bootstrap intervals; M1 counts as borne out when the not-most-selective disagreement rate
  is higher than the most-selective one, M2 and M3 when the share is above 50 %;
- a predictive interval for a batch of the new batch's size: 10,000 draws of as many papers as the new batch scores,
  drawn with replacement from the 28 frozen papers (seed 20261013), share of their groups that disagree;
- disagreements with a regret > 5 %, papers with a disagreement, kinds (`mismatch_kinds.classify`), median regret;
- the near-infeasibility split of PR #69 under S6 (regret > 1 or STY leader's S6 cost > 2x its S5 cost);
- the uncorrected records (before the PDF check) and the all-entries cohort (plot readings included).

## 3. Search (fixed)

- **Window.** Published after the frozen corpus's latest paper. `corpus_dates.py` → `frozen_corpus_dates.csv`: the
  latest of the 50 papers of `agent/extraction/paper_set.txt` is Gothe et al. 2025 (10.1021/acscatal.5c05984),
  OpenAlex publication date 2025-11-04. Window: 2025-11-05 to 2026-10-13.
- **Query** (`search_openalex.py`, run once; `search_query.json`, ranked result `search_results.csv`): OpenAlex
  `/works`, `search="CO2 hydrogenation methanol catalyst"`,
  `filter=from_publication_date:2025-11-05,to_publication_date:2026-10-13,type:article,language:en`,
  `sort=relevance_score:desc`, first 800 of 3,523 matches saved.
- **Screening order.** The saved rank. Rows without a DOI and repeated DOIs (after the first) are dropped. Candidates
  are taken strictly in rank order through the stages below; the first 40 that pass every stage form the batch, and no
  candidate below the 40th inclusion is screened. If the 800 saved ranks give fewer than 25 inclusions, the batch is
  what they give (no extension, no second query). Target: 25–40 papers.

## 4. Inclusion criteria (those of the frozen corpus)

The frozen corpus is the TheMeCat v1 / Suvarna et al. 2022 curated scope plus the 2026-10-06 rules of
`agent/extraction/README.md`. A candidate is **included** when all hold:

1. a primary research article (not a review, perspective, highlight, erratum or a computation-only study);
2. heterogeneous, thermally driven hydrogenation of CO2 with H2 to methanol, measured in a continuous gas-phase flow
   reactor; methanol is a target product (studies of higher alcohols, hydrocarbons, DME or CO as the target, and
   electro-, photo-, photothermal- or plasma-driven conversion, are excluded, as Zhang 2024 was);
3. it reports measured catalytic performance (CO2 conversion and methanol selectivity, or methanol STY) at a stated
   temperature and pressure for at least one catalyst (the inputs of the extraction schema);
4. its PDF is retrieved by nus-fetch (`fetch_papers.py`, status `ok`, DOI or title verified in the PDF);
5. its Supporting Information is retrieved by `fetch_si.py` (frozen rule: Shi 2020 was dropped for having no SI, and
   batch 4 took the papers whose SI `fetch_si.py` finds).

Stages, in rank order: (S1) title and abstract against 1–2; ambiguous records go on. (S2) PDF retrieval (4); a
candidate with status `manual` or `fail` (e.g. every Elsevier title off the NUS network) is recorded as not retrieved
and the next candidate is taken; no bot check is ever automated. (S3) full text against 1–3, from the experimental
section, tables and captions, without any plant-model output. (S4) SI retrieval (5). One row per candidate reaching
S2 goes to `screening.csv` with the stage reached, the decision and a one-line reason. "Screened" counts candidates
whose full text was read (S3); "included" counts those passing S4; "scored" counts papers with at least one scored group.
Papers included but without a scored group stay counted as included.

## 5. Extraction and scoring pipeline (frozen, unchanged)

- **Extraction**: the four passes of `agent/extraction/extract_records.py` (main, figures, si, si_figures), the same
  prompts, schema, model (gpt-5.5, reasoning effort medium, streamed Responses, `store=false`) and route
  (`agent/extraction/llm_route.py`: the local API-YES gateway first, then the advisor key), as in PR #78. A wrapper
  (`pv.py`) changes only the paper list and the input/output directories, which live in this folder. Token cap 8 M in
  total, 3 M per pass, counted from this folder's `out/token_usage.csv`. Normalisation: `agent/extraction/normalize.py`
  unchanged → `out/records_normalized.csv`.
- **Candidates and groups**: `meoh_candidates.build_candidates(records, printed_only=True)` unchanged (printed-value
  cohort, comparison groups of one paper at the same P, H2/CO2 and space velocity, the frozen group STY basis and
  duplicate rule).
- **Plant costs and scoring**: `meoh_candidates.plant_costs` (latest model, S5 and S6 columns), `aggregate`,
  `mismatch_kinds.classify`; an entry infeasible in a scenario leaves both leaderboards of its group (frozen
  convention), and the rule then picks among the remaining entries.
- **Regression first**: the scoring wrapper reruns the frozen candidates through the same path and must reproduce S5
  15/40 and S6 28/40 before the new batch is scored; otherwise it stops.
- At most 8 worker processes.

## 6. Order of commits

1. This file, the predictions and the search (no new paper read).
2. Screening (`screening.csv`), PDFs/SI retrieval logs, extraction outputs and the PDF accuracy check.
3. **Blind predictions** (`blind_predictions.csv`): from the corrected records, `build_candidates` only, the S6 and S5
   rules applied to every new group, with the full ranking of each group's entries under each rule (if the predicted
   entry turns out infeasible in a scenario, the next feasible entry in the committed ranking is the prediction).
   Committed before the plant model is run on any new entry.
4. Plant model, scoring against the committed predictions, report.

`check_order.py` verifies from the git history that the blind-prediction file was committed before any plant-model
output of the new batch and is unchanged afterwards, and that this file precedes every extraction output.

## 7. Accuracy of AI-assisted extraction

A random sample (seed 20261013) of 40 printed values that enter the new batch's printed-value primary (X_CO2, S_MeOH,
S_CO, S_CH4, STY, T, P, H2/CO2, space velocity) is checked against the cited PDF page text (AI-assisted, as in PR #78),
including the unit conversion. A wrong value is corrected only through `corrections.csv`, applied by the wrapper; the
primary uses the corrected records, and the uncorrected result is reported next to it. Printed values only in the
primary; plot readings enter only the all-entries sensitivity.
