# Addendum to the human review of the 100-value sample (2026-10-21)

Additive record; `HUMAN_REVIEW_CONFIRMATION.md` and the evidence files of 2026-10-12 are unchanged.

On 2026-10-21 the author stated about the review of the 100 sampled values: "我审核的时候只有看到有一个错误"
(in the review there was exactly one error), and asked for it to be carried into the source-type ledger.

In the row-level evidence (`methanol_gold_standard_100_source_evidence.csv`) the one value that is attached to an entry
for which the paper does not report it is **#40** (Frei et al. 2019, doi 10.1038/s41467-019-11349-9): the CO₂
conversion of 9.7% is printed in the text on the 500 h stability test (Fig. 6), while the extraction attached it to the
Table 2 entry, and Table 2 has no conversion column. The ledger counts #40 as the sample's one error: 99 of 100 values
correct. Its effect on the comparisons is computed in `analysis/extraction_ledger_2026_10_21/` (no catalyst-level
comparison changes; the point-level count of the inlet-limited loop would rise from 50 to 51 of 81).
