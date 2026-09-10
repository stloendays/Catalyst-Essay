# Cross-reaction leverage normalization — provenance and revalidation status

Recorded: **2026-09-10** during the claim-to-evidence audit.  
Final repository-level CI status: **METRIC_EQUIVALENCE_NOT_ESTABLISHED**.

## Current manuscript status

The numerical cross-reaction ratio previously reported as:

- NH3 TOF normalized leverage: approximately **0.000916–0.001374**;
- MeOH CH4-suppression leverage: **0.37579**;
- MeOH CH4-suppression / NH3 TOF normalized-leverage ratio: **273–410**;
- 2.5% midpoint: approximately **328**;

is **excluded from the current NH3-FINAL-1.1 manuscript claim set**.

The MeOH numerator remains current and directly traceable. The unresolved item is the NH3 denominator-side metric lineage.

## Why the second-pass audit changed the status

The denominator-normalization record in Notion page `09｜Cross-Reaction Catalyst-Economic Leverage：统一成本分母后的比较` predates promotion of NH3-FINAL-1.1. Its own text identifies the NH3 reduced-cost baseline as approximately **10.2 USD/t**, which corresponds to the archived NH3-FINAL-1.0 regime rather than the current FINAL-1.1 Fe cost of **15.292 USD/t**.

The same 273–410 / ~328 ratio is preserved in older project/GIST records alongside superseded NH3-FINAL-1.0 values such as Fe/Ru/Os = **10.199 / 17.592 / 21.321 USD/t**, Fe feasibility = **73.6%**, and Ru activity parity = **2171.56x**. This indicates that the numerical cross-reaction normalization originated before FINAL-1.1.

By contrast, the NH3-FINAL-1.1 promotion record states that NH3 ground-truth quantities were reclosed from canonical run `outputs/nh3_final_20260905T134204Z` and that Layer-B lever/reach quantities were recomputed rather than inherited. The promotion record does not document a recomputation of the cross-reaction TOF-normalized leverage ratio.

## GitHub Actions revalidation attempt

After GitHub-hosted runner access was restored, workflow `F9A revalidation and Figure 8 closure` completed successfully at run **34449914480**. The conservative provenance probe searched the full repository history while explicitly excluding the audit scripts and generated audit artifacts from serving as historical evidence.

The result was:

- classification: **METRIC_EQUIVALENCE_NOT_ESTABLISHED**;
- pre-audit code-level implementation candidates recovered: **0**;
- conservatively verified historical metric implementations: **0**;
- `configs/nh3_final.yaml`: **not present in this repository**;
- `outputs/nh3_final_20260905T134204Z`: **not present in this repository**.

Machine-readable record: `artifacts/f9a_ci/f9a_ci_revalidation.json`.  
Human-readable record: `artifacts/f9a_ci/CROSS_REACTION_FINAL1_1_CI_ATTEMPT.md`.

The workflow deliberately did **not** infer a new ratio by scaling the historical 273–410 range with the change in NH3 cost.

## Scientific decision

The exact historical NH3 TOF-economic-leverage definition cannot be established from the material currently retained in `Catalyst-Essay`. Therefore no new FINAL-1.1 quantitative cross-reaction ratio is promoted.

This does **not** invalidate the reaction-specific pathway comparison. The following qualitative mechanistic statements remain supported:

- NH3 activity primarily propagates through **catalyst inventory / reactor-demand / process-severity** pathways;
- MeOH selectivity, particularly methane suppression, propagates through **feed loss / gas accumulation / purge / recycle / compression** pathways.

The MeOH CH4-suppression leverage remains directly traceable to:

- `data/meoh/meoh_candidate_ranking_D01v3.csv`;
- `data/meoh/MeOH_D01_ExplicitRecycleSeparationEconomics_v3.0.xlsx`;
- the frozen MeOH extraction and robustness scripts.

## Figure and writing boundary

**F9A status = METRIC_EQUIVALENCE_NOT_ESTABLISHED / QUALITATIVE-ONLY.**

For the current manuscript:

- do not present **273–410** or **~328** as a current FINAL-1.1 result;
- historical documents may retain those numbers only when clearly labeled as archived pre-FINAL-1.1 normalization;
- Figure 9A may be retained only as a qualitative pathway comparison unless the original pre-audit metric implementation and the frozen FINAL-1.1 harness are later imported;
- no new proxy metric should be substituted merely to recover a numerical cross-reaction ratio.

This closes the current repository-level F9A audit without reopening the broader scientific model.
