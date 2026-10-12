# Methanol gold-standard audit | 100 sampled fields

**Human review: COMPLETED (author-confirmed, 2026-10-12).** See [HUMAN_REVIEW_CONFIRMATION.md](HUMAN_REVIEW_CONFIRMATION.md) for the exact author attestation and its scope.

The **final** independent source-evidence review is [the 100-row Excel workbook](methanol_gold_standard_100_primary_source_review_2026-10-12.xlsx), [the Chinese audit report](methanol_gold_standard_100_primary_source_review_2026-10-12.md), and [the machine-readable row evidence](methanol_gold_standard_100_source_evidence.csv). Source PDF identities and SHA-256 values are recorded in the workbook and report. Original paper PDFs/SI are archived separately and are **not** redistributed here.

**Audit snapshot:** 100 sampled fields across 10 primary papers; 91 source-printed/unit equivalent, 6 derived from printed components or inverted ratios, 1 paper-locator correction, 1 upper-limit qualifier, and 1 source-measurement terminology correction. All 100 numeric comparisons in the audit workbook have `MATCH`; the author states that the 100 items have also been manually reviewed without additional problems. This does **not** imply 100% dataset-wide accuracy or 100 identical verbatim printed values.

The report identifies the nine metadata and provenance-specific cases: **#40, #45, #79, #85, #90, #93, #95, #96 and #99**. Preserve `<0.1%` for #93, preserve the original wording for ratios derived from feed composition, and cite the correct source location for #40.

The `history/` folder preserves two earlier AI-assisted review rounds, which had lower source availability; they are included for provenance and **must not supersede** the final Google Drive paper/SI re-review. Their references to unfinished manual signoff describe the state at the time of those older drafts, before the author confirmed completion.

The original precommitted random sample, draw script and original verification sheet remain available under [`../gold_standard_sample.csv`](../gold_standard_sample.csv), [`../gold_standard_sample.py`](../gold_standard_sample.py), and [`../gold_standard_sample.xlsx`](../gold_standard_sample.xlsx). This additive audit does not change the frozen primary economic conclusions. Check [MANIFEST.json](MANIFEST.json) for the original file checksums.
