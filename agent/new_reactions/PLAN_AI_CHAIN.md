# AI-run catalyst economics: plan (2026-11-11)

Goal: an agent that collects the evidence, extracts the experimental data, calls fixed engineering models and, with
limited information and budget, decides which catalyst and operating condition a plant should use - with its speed,
cost and scale measured. It is an extension of the NCE paper (same chain, same metrics, same three-optima framing:
atomic, laboratory and plant optima), not a new framework. All of it goes into the NCE paper (the ICML line excluded).

## Principles

- The agent only chooses: which papers to keep, which masked cells to reveal, when to stop, which catalyst and
  condition. Search, download, OCR, unit handling, extraction validation and every cost number come from fixed code.
- Every reaction reports the NCE metrics: within-paper disagreement between the paper ranking and the plant-cost
  ranking with its denominator, split into "other catalyst" and "same catalyst at another temperature" (as in
  `analysis/meoh_literature_inversion_2026_10_05/mismatch_kinds.py`); regret R = (J_paper leader - J_plant leader) /
  J_plant leader; cost attribution and leverage L = -dlnC/dlnx (`data/meoh/meoh_d01_model.leverage_increase`);
  backward design (break-even); sensitivity; printed values as the primary data, plot readings as sensitivity.
- Every number traces to the paper page and table/figure (`location`, `page` in the extraction schema, carried into
  the normalised records).
- Model version and parameter table are saved with every result (framework version, config SHA-256).

## 1. Agent (cost of the decision part)

- No critic, one short plan, tool outputs as summaries only, no re-reading of files. Token report split into
  extraction (per paper) and the agent's decisions (target 0.2-0.3 M per reaction).

## 2. Paper yield

- Screening asks for experimental papers with feed, conversion, selectivity and flow / space velocity / mass
  (data_likelihood). After download a fixed check tests each paper for those fields; a paper without them is
  replaced and the reason logged. Every reaction reports screened / downloaded / usable / replaced (with reasons).

## 3. Five reactions, fixed plant models

PDH, CO2 methanation (both in `plant_framework.py`, configs `<rxn>_ours.json`, reproduced to 5e-14), ammonia
decomposition, RWGS, ethanol dehydration (to build). New models reuse existing modules instead of rewriting them:
- ammonia decomposition: equilibrium from the NH3 harness (`gillespie_beattie_dG_form`, `newton_cooper_phi`,
  `provenance/nh3_final_1_2/source_harness/harness_core.py`), Ru price 53,852.5 USD/kg (harness `PRICE`) and the
  Ru recovery convention r = 0.90-0.9555, u >= 11 (`figures/composite/fig2/fig2_ru_actual_cost.py`);
- RWGS: `K_rwgs` and `gas_activities` from `data/meoh/meoh_general_model.py`, CO handled as in the methanol loop;
- ethanol dehydration: van 't Hoff from standard data (no existing module).
Each model is checked against a published plant or techno-economic cost. Parameters and sources in the config.

## 4. One engineering calculation

The agent calls the plant-model tool (framework + frozen config); it never writes cost formulas.

## 5. Budgeted decisions on the masked database (REVEAL)

- Visible: paper code, catalyst, composition, conditions, conversion, reactant conversion rate. Masked: selectivity,
  stability; one cell = 1 unit.
- Decision = catalyst and operating condition (a record), not a process-route comparison.
- Value of information, defined before the runs, for a masked cell given what is revealed:
  - flip value: 1 if the cell's best case (selectivity 1, best stability) is cheaper than the current best known
    record, i.e. revealing it can change the choice, else 0;
  - expected regret reduction: E[max(0, J_best - J(cell))] with selectivity drawn from the revealed selectivities
    of the same paper (uniform 0.5-1 when fewer than three are revealed).
- Logged per step: cell revealed, units spent, current choice, both values of information for the revealed cell.
- Stop rule, mapped from DISCOVER (`provenance/discover_v1/source_harness/discover/env.py` `stopping_status`):
  S1 an exactly costed record exists; S2 no masked record has a lower bound below the best known (no unresolved
  candidate); S3 the laboratory optimum (highest lab rate, the paper's own ranking) is the plant choice, or its
  selectivity is revealed and its backward design (selectivity needed to match the choice) has been computed.
  Metrics as in `tools/discover/v2_stop_analysis.py`: rule-armed units, units spent after the rule, decision correct.
  Arms: no rule (S-anytime prompt only) / check before reveal (S-gate: after arming, a reveal runs only if its flip
  value is 1) / forced stop (S-hard).

## 6. Validation

- Multi-budget REVEAL: PDH and CO2 methanation, budgets 10 %, 30 % and unlimited of the masked cells, 20 repeats per
  cell with shuffled paper codes and record order; first the no-rule arm; when it holds, a preregistration
  (`PREREG_REVEAL.json`), then the gate and hard arms. A weaker model (API-YES gpt-5.6-luna or gpt-5.2) as control.
  Deterministic baselines with the same model: lower-bound branch and bound, lab-rate greedy, random.
- Scaling: 10, 30, 100 papers (100 only for PDH and methanation; Elsevier needs the user's browser check; others
  10-30): papers -> time and cost, and the paper count after which the conclusions stop changing.
- Fully autonomous mode (from the reaction name): 3 runs per reaction, compared layer by layer with the masked runs:
  paper overlap, extracted-value differences on shared papers, bottleneck agreement, final choice.
- Calibration before the new reactions: the agent tools on the NCE data sets (NH3 field records, methanol literature
  records) must reproduce the NCE numbers through the same deterministic chain (manuscript: methanol 26/63 catalyst
  level, NH3 field 12/44; FINAL-1.2 Fe/Ru/Os 11.52/16.63/19.75 USD/t).

## Order

1. Five plant models (three new, sourced and checked). 2. Agent rebuilt around the model tool, summaries only.
3. Calibration on NH3 synthesis and methanol. 4. Five reactions. 5. Multi-budget and scaling experiments.
