# Cross-reaction leverage normalization — provenance and revalidation status

Recorded: **2026-09-10** during the claim-to-evidence audit.  
Second-pass status: **REVALIDATION REQUIRED AFTER NH3-FINAL-1.1**.

## Current manuscript status

The numerical cross-reaction ratio previously reported as:

- NH3 TOF normalized leverage: approximately **0.000916–0.001374**;
- MeOH CH4-suppression leverage: **0.37579**;
- MeOH CH4-suppression / NH3 TOF normalized-leverage ratio: **273–410**;
- 2.5% midpoint: approximately **328**;

is **held out of the current manuscript until NH3-FINAL-1.1 revalidation is complete**.

The MeOH numerator remains current and directly traceable. The uncertainty is specifically the NH3 denominator-side lineage.

## Why the second-pass audit changed the status

The denominator-normalization record in Notion page `09｜Cross-Reaction Catalyst-Economic Leverage：统一成本分母后的比较` predates promotion of NH3-FINAL-1.1. Its own text identifies the NH3 reduced-cost baseline as approximately **10.2 USD/t**, which corresponds to the archived NH3-FINAL-1.0 regime rather than the current FINAL-1.1 Fe cost of **15.292 USD/t**.

The same 273–410 / ~328 ratio is also preserved in older project/GIST records alongside superseded NH3-FINAL-1.0 values such as Fe/Ru/Os = **10.199 / 17.592 / 21.321 USD/t**, Fe feasibility = **73.6%**, and Ru activity parity = **2171.56x**. This is strong evidence that the cross-reaction numerical normalization originated before FINAL-1.1.

By contrast, the NH3-FINAL-1.1 promotion record explicitly states that all NH3 ground-truth quantities were reclosed from canonical run `outputs/nh3_final_20260905T134204Z` and that Layer-B lever/reach quantities were recomputed rather than inherited. The promotion record does not document a recomputation of the cross-reaction TOF-normalized leverage ratio.

Therefore the compact snapshot entry in `data/canonical_results_2026-09-06.csv` is not sufficient evidence that 273–410 was recalculated under FINAL-1.1.

## What remains valid

The qualitative mechanistic comparison remains supported and can stay in the manuscript:

- NH3 activity primarily propagates through **catalyst inventory / reactor-demand / process-severity** pathways;
- MeOH selectivity, particularly methane suppression, propagates through **feed loss / gas accumulation / purge / recycle / compression** pathways.

The MeOH CH4-suppression leverage is directly traceable in this repository to:

- `data/meoh/meoh_candidate_ranking_D01v3.csv`;
- `data/meoh/MeOH_D01_ExplicitRecycleSeparationEconomics_v3.0.xlsx`;
- the frozen MeOH extraction and robustness scripts.

## Required targeted revalidation

This is a narrow research-freeze exception, not a reopening of the scientific model.

Using the frozen NH3-FINAL-1.1 source harness only:

1. locate canonical run `outputs/nh3_final_20260905T134204Z` and the exact TOF/economic-leverage definition used for the earlier cross-reaction comparison;
2. if possible, reproduce the archived FINAL-1.0 normalized result as a regression check using the original definition;
3. compute the same NH3 TOF economic leverage under `configs/nh3_final.yaml` = NH3-FINAL-1.1 without changing the metric, perturbation definition, process model or optimization rules;
4. apply the same reduced/full-cost fraction band **2%, 2.5%, 3%**;
5. keep the MeOH numerator fixed at **0.3757939247335326**;
6. report the resulting ratio at each denominator fraction with exact source/config/code hashes.

If the frozen FINAL-1.1 harness does not expose an equivalent TOF-perturbation pathway, stop and report that limitation. Do not invent a replacement metric.

## Figure and writing boundary

**F9A status = REVALIDATION_REQUIRED_AFTER_NH3_FINAL_1_1.**

Until the targeted calculation is closed:

- do not present **273–410** or **~328** as a current FINAL-1.1 result;
- historical documents may retain those numbers only when clearly labeled as pre-FINAL-1.1 / archived normalization;
- current manuscript text may retain the qualitative pathway contrast without the numerical ratio.

When revalidation is complete, add a dedicated machine-readable source bundle and regenerate F9A from that bundle.