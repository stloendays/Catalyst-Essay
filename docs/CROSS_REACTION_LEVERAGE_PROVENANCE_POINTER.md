# Cross-reaction leverage normalization — provenance pointer

Recorded: **2026-09-10** during the claim-to-evidence audit.

## Frozen manuscript result

After harmonizing the cost-denominator interpretation, the current manuscript uses:

- NH3 TOF normalized leverage: approximately **0.000916–0.001374**;
- MeOH CH4-suppression leverage: **0.37579**;
- MeOH CH4-suppression / NH3 TOF normalized-leverage ratio: **273–410**;
- midpoint at the 2.5% denominator assumption: approximately **328**.

These values are mirrored in `data/canonical_results_2026-09-06.csv` and the current manuscript summaries.

## Origin of the normalization

The project normalization closure records that the earlier direct cross-reaction comparison was invalid because the two reactions used different cost boundaries:

- NH3 used a reduced catalyst/process-dependent cost;
- MeOH used a near-full-cost NPC.

The closure therefore maps the NH3 reduced-cost leverage to a common full-cost interpretation using an estimated reduced-cost/full-cost fraction of **2–3%**. Under this boundary, the NH3 TOF leverage becomes approximately **0.000916–0.001374**; with the MeOH CH4-suppression leverage of **0.37579**, the frozen headline ratio is **273–410**, with a 2.5% midpoint of approximately **328**.

The underlying project record is the Notion page `09｜Cross-Reaction Catalyst-Economic Leverage：统一成本分母后的比较`, with the corresponding technical-closure rationale recorded in `11｜2026-08-22 老师会议反馈与三项 Technical Closure`.

## Evidence status

The MeOH numerator is directly traceable in this repository to:

- `data/meoh/meoh_candidate_ranking_D01v3.csv`;
- the frozen D01 v3 workbook;
- the MeOH extraction/figure scripts.

The denominator-harmonization result is currently preserved as a frozen project-level normalization record and compact canonical snapshot. The original dedicated arithmetic/source-data file that generated the 2–3% full-cost boundary is not present in `Catalyst-Essay`.

Therefore F9A remains **HOLD** for final figure locking until one of the following is supplied:

1. the original normalization worksheet/script and its cost-boundary source; or
2. a content-addressed export of the exact inputs and calculation from the source archive.

A new scientific simulation is not required to close this item. The task is to recover and freeze the existing denominator-normalization provenance. If the recovered inputs reproduce the current bounds, the 273–410 result remains unchanged.

## Writing boundary

Every manuscript use of **273–410** or **~328** must state that the comparison is made **after cost-denominator alignment** and must not imply that the ratio is a universal reaction constant. It is a pathway-level comparison under the stated denominator harmonization.
