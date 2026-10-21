# Addendum to the review of the 100-value sample (2026-10-21)

Additive record; `HUMAN_REVIEW_CONFIRMATION.md` and the evidence files of 2026-10-12 are unchanged.

The final review of the sample counts two of the 100 values as extraction errors (row ids of
`methanol_gold_standard_100_source_evidence.csv`):

- **#40** (Frei et al. 2019, doi 10.1038/s41467-019-11349-9): the CO₂ conversion of 9.7% is printed in the text on the
  500 h stability test (Fig. 6), while the extraction attached it to the Table 2 entry; Table 2 has no conversion
  column.
- **#99** (Ota et al. 2012, doi 10.1016/j.jcat.2012.05.020): Table 2 prints a methanol formation rate of 0.3 µmol per
  gram of catalyst per minute, which the extraction recorded as a printed STY without the paper's metric name.

The source-type ledger in `analysis/extraction_ledger_2026_10_21/` therefore reports 98 of 100 values correct and
computes the effect of each error on the comparisons.
