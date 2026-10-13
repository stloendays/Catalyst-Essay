# `nh3_printed.py` on NH3-FINAL-1.2 (2026-10-13)

`../nh3_printed.py` run on the NH3-FINAL-1.2 field chain (`analysis/nh3_field_2026_10_06/nh3_1_2/`; run
`nh3_final_1_2_20261013`, Fe benchmark 11.52 USD/t). Same printed-entry definition and groups as the 1.1 files in the
parent folder; it checks that the rebuilt all-entries result equals the 1.2 `summary.json` (40 / 124) before it scores
the printed set. Details and the group-level changes: `analysis/nh3_field_2026_10_06/nh3_1_2/README.md`.

    set NH3_MODEL=1.2
    set NH3_HARNESS_1_2=D:\论文-AI4S\wt-nh3-12\provenance\nh3_final_1_2\source_harness
    python analysis/nh3_field_2026_10_06/run_field_chain.py      # writes the 1.2 field run read here
    python analysis/verify_2026_10_08/nh3_printed.py

| `nh3_printed_summary.json` | NH3-FINAL-1.1 | **NH3-FINAL-1.2** |
|---|---:|---:|
| printed: groups / papers / entries | 33 / 23 / 139 | **33 / 23 / 139** |
| printed: paper leader ≠ plant leader | 7 / 33 (21.2 %) | **7 / 33 (21.2 %)** |
| printed: 95 % CI (paper bootstrap) | 7.1–36.7 % | **6.9–37.5 %** |
| printed: papers with a mismatch | 6 / 23 | **6 / 23** |
| printed: regret median of mismatched / max | 10.0 % / 31.5 % | **13.8 % / 37.3 %** |
| printed: mismatches with regret > 5 % / > 10 % | 4 / 4 | **4 / 4** |
| rate not plot-read | 7 / 34 (CI 7.1–35.1 %) | **7 / 34 (CI 6.7–35.5 %)** |
| primary, all entries | 44 / 124 (CI 18.4–52.4 %), 13 / 28 papers, > 5 %: 29, > 10 %: 25 | **40 / 124 (CI 14.3–50.4 %), 11 / 28 papers, > 5 %: 28, > 10 %: 26** |
| entries: primary / printed / T printed | 623 / 182 / 487 | **625 / 182 / 489** |
