# Claim-to-evidence audit — Addendum A1 (2026-09-10)

Status: **TARGETED REVALIDATION REQUIRED FOR F9A ONLY**

This addendum supersedes the first-pass statement that no scientific recalculation was required. The first-pass audit correctly identified a provenance gap for the cross-reaction leverage ratio, but a second-pass temporal/data-lineage check showed that the gap is substantive enough to require one narrow deterministic revalidation.

## Finding

The previously reported cross-reaction result:

- NH3 TOF normalized leverage = **0.000916–0.001374**;
- MeOH CH4-suppression / NH3 TOF leverage ratio = **273–410**;
- midpoint ~= **328** at a 2.5% reduced/full-cost fraction;

traces to a normalization record created before NH3-FINAL-1.1 was promoted.

The source normalization page explicitly describes the NH3 reduced-cost baseline as approximately **10.2 USD/t**, matching the archived NH3-FINAL-1.0 Fe cost (**10.199 USD/t**), not the current FINAL-1.1 Fe cost (**15.292 USD/t**). Older project exports preserve the same 273–410 ratio alongside other FINAL-1.0 values, including Fe/Ru/Os = 10.199/17.592/21.321 USD/t and Ru parity = 2171.56x.

NH3-FINAL-1.1 subsequently changed the pressure-CAPEX/economic closure and explicitly recomputed its NH3 ground-truth and Layer-B lever/reach quantities. No source currently available to this audit demonstrates that the cross-reaction TOF-normalized leverage was recomputed after that promotion.

## Decision

The values **273–410** and **~328** are reclassified as:

`LEGACY_PRE_FINAL_1.1_NORMALIZATION — HOLD`

They must not be presented as current FINAL-1.1 manuscript results until the same leverage calculation is repeated with the frozen FINAL-1.1 harness.

**Figure 9A status:** `REVALIDATION_REQUIRED_AFTER_NH3_FINAL_1.1`.

## Scope of the research-freeze exception

The research freeze remains in force. The only authorized scientific computation is a deterministic revalidation of the existing cross-reaction leverage definition using the already frozen NH3-FINAL-1.1 model.

No changes are authorized to:

- NH3-FINAL-1.1 model equations or parameters;
- candidate set;
- process optimization rules;
- MeOH D01 v3 data;
- MeOH CH4-suppression leverage;
- 2–3% denominator-alignment band;
- the leverage metric/finite-difference definition;
- Agent/DISCOVER experiments.

If the old leverage definition cannot be reproduced exactly from the archived implementation, the correct outcome is to report the missing equivalence and keep F9A quantitative comparison out of the manuscript.

## Claims unaffected by this exception

The following remain valid:

- NH3 atomic-to-economic ranking inversion under FINAL-1.1;
- NH3 uncertainty/backward-design/scaling results already promoted under FINAL-1.1;
- MeOH D01 v3 ranking reshuffle and selectivity–recycle mechanism;
- Au/TiO2 rank-preservation control;
- DISCOVER V1 / C1 Agent results;
- the qualitative pathway contrast: **NH3 activity -> inventory/reactor demand**, **MeOH selectivity -> feed loss/purge/recycle**.

## Required closure artifact

Execute `docs/F9A_FINAL_1_1_REVALIDATION_TASK.md` in the local source harness. The closure must produce machine-readable input/result/provenance files and either:

1. promote a new FINAL-1.1-consistent F9A quantitative result; or
2. retain F9A as qualitative-only if exact metric equivalence cannot be established.
