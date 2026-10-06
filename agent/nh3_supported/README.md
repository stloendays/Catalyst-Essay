# ACSA: experimental ammonia catalysts from the Humphreys 2021 review

| File | What it does |
|---|---|
| `extract_tables.py` | gpt-5.5 (API-YES first, advisor key once API-YES is used up), one strict-JSON call per table page with the page text and a 2.2× page image; every cell copied as printed plus its number in the column unit. Two independent passes (`--pass a`, `--pass b`). |
| `adjudicate.py` | Pairs the two passes row by row, checks every number against the page text, applies `out/manual_adjudication.csv` (decisions taken from the page images) and writes `out/records.csv`, `out/review.csv`, `out/adjudication_summary.json`. |
| `pdf/`, `text/` | Review PDF and page text/images (git-ignored). |

Source: K. Humphreys, R. Lan, S. Tao, *Adv. Energy Sustain. Res.* **2**, 2000043 (2021), doi:10.1002/aesr.202000043,
Tables 1–6 on PDF pages 6, 10, 11, 13, 16, 17 and 19.

## Result (2026-10-06)

- 164 table rows, the same count in both passes on every page; 14 calls, 138,727 tokens, 20 min.
- 706 numeric fields: the passes agree on 697; 675 values appear in the page text. The 31 values not found in the text
  (thousands separators the text layer prints differently, pages 10, 16, 17) and the 9 disagreements were checked on
  the page images. The 9 disagreements are Table 1 metal contents: Table 1 has no content column, pass a took the
  percentage printed in the catalyst name (“7% Fe/CeO₂”) and pass b left it empty as instructed; the name value is
  used and flagged. After adjudication pass a equals the adjudicated value in all 706 fields.
- Normalization: rates in µmol g⁻¹ h⁻¹ as printed, mL h⁻¹ g⁻¹ converted with 22,414 mL mol⁻¹, or derived from the
  printed outlet NH₃ fraction and WHSV (flagged); fused-iron rows (Fe₃O₄, Fe₁₋ₓO, wüstite) take the benchmark metal
  content.

## Primary-source errata (2026-10-06)

The PR #27 field analysis (`agent/nh3_field/eval/humphreys_adjudication.csv`) checked these rows against the cited
papers and found ten review errors in nine rows. `out/primary_errata.csv` lists them, one row per corrected field
(14 fields: the two ref. 104 rows are Ru-free, so their name, active metal and metal content change). `adjudicate.py`
applies them after the manual adjudication; the paper value supersedes the review value, the record's column
`erratum` names each correction, and the script stops if an erratum's review value no longer matches the extraction.
The pass outputs (`out/pass_a`, `out/pass_b`) and `out/manual_adjudication.csv` are unchanged.

The chain that uses these records is `analysis/nh3_supported_2026_10_06/`.
