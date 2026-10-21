# Source-type ledger of the 100 sampled extracted values (P2, 2026-10-21)

Supervisor item P2 of 2026-10-20: classify the 100 sampled extracted methanol values by source type and report each
type with its own denominator and accuracy, without pooling plot readings with printed values.

`build_ledger.py` reads the row-level source evidence of the sample
(`analysis/verify_2026_10_08/gold_standard_human_review_2026_10_12/methanol_gold_standard_100_source_evidence.csv`;
10 papers × 10 values, seed 20261008) and writes `ledger_100.csv` (one row per value: source type, location, correct,
note) and `summary.json`.

| Source type | Main text | Supporting Information | Correct |
|---|---:|---:|---:|
| printed, table | 20 | 38 | 58 / 58 |
| printed, text or caption | 30 | 6 | 35 / 36 |
| derived (H₂/CO₂ from a printed feed composition) | 4 | 2 | 6 / 6 |
| plot-read | 0 | 0 | – |
| **total** | 54 | 46 | **99 / 100** |

A value is correct when its number and qualifier agree with the paper and it is attached to an entry for which the
paper reports it.

**The one error (#40, Frei et al. 2019, doi 10.1038/s41467-019-11349-9).** The CO₂ conversion of 9.7% is printed in the text on
the 500 h stability test (Fig. 6). The extraction also attached it to the Table 2 entry of the same catalyst, and Table
2 has no conversion column. The author's review reports one error in the sample (2026-10-21); in the row-level
evidence #40 is the only value attached to an entry for which the paper does not report it (addendum in
`analysis/verify_2026_10_08/gold_standard_human_review_2026_10_12/AUTHOR_REVIEW_ADDENDUM_2026-10-21.md`).

**Effect.** The record sits in a single-catalyst group (Pd–In₂O₃ CP, 50 bar, H₂/CO₂ 4, 48 NL g⁻¹ h⁻¹), so no
catalyst-level comparison (21 of 63, 26 of 63) changes. In the point-level count of the inlet-limited loop the group
becomes a disagreement once the record is removed (50 → 51 of 81, 42 → 43 above 5%; regret 8.4%). Without the limit
nothing changes (25 of 81). The reported counts use the records as extracted, so the point-level count is the lower
of the two.

Two values carry a note but are correct: #93 (Ota 2012) keeps its upper-bound qualifier '<0.1%' as extracted, and
#99 (Ota 2012) is printed as a methanol rate in µmol per gram of catalyst per minute, kept in the printed unit.

**Plot-read values.** None of the 100 sampled values is read off a plot. Their accuracy comes from the comparison with
the curated datasets at strict tolerance (`agent/extraction/eval/field_accuracy_by_source.csv`, main-text and SI
plots): CO₂ conversion 185 of 229, methanol selectivity 73 of 207, STY 18 of 151. Plot readings enter only the
sensitivity analyses, never the primary comparisons.
